import json
import sqlite3
from collections import deque
from decimal import Decimal, InvalidOperation

from qgis.core import QgsTask, QgsMessageLog, Qgis
from qgis.PyQt.QtCore import pyqtSignal

from ..gp import analysis_metrics
from ..gp.analysis_metrics import MetricInputMissingError
from ..model.metric_value import MetricValue, load_metric_values


MESSAGE_CATEGORY = 'QRiS Metrics Task'


class AnalysisMetricsTask(QgsTask):
    """Background task for calculating analysis metrics.

    The task accepts a list of work dimensions (sample frames, events, metrics),
    which lets the same task class support both bulk and single-metric workflows.
    """

    on_complete = pyqtSignal(dict)
    BATCH_SIZE = 250

    def __init__(
        self,
        qris_project,
        analysis,
        sample_frame_ids: list,
        event_ids: list,
        metric_ids: list,
        overwrite_existing: bool,
        force_active: bool,
    ):
        super().__init__('Calculate Analysis Metrics', QgsTask.CanCancel)

        self.qris_project = qris_project
        self.analysis = analysis
        self.sample_frame_ids = sample_frame_ids
        self.event_ids = event_ids
        self.metric_ids = metric_ids
        self.overwrite_existing = overwrite_existing
        self.force_active = force_active

        self.exception = None
        self.summary = {
            'success': 0,
            'missing_data': 0,
            'errors': 0,
            'skipped_not_feasible': 0,
            'skipped_overwrite': 0,
            'skipped_no_function': 0,
            'processed': 0,
            'total': 0,
            'messages': [],
            'canceled': False,
            'exception': None,
        }

    def _log(self, text: str, level: int = Qgis.Info):
        self.summary['messages'].append({'text': text, 'level': level})

    def _build_analysis_params(self) -> dict:
        analysis_params = {}
        centerline = self.analysis.metadata.get('centerline', None)
        if centerline is not None and centerline in self.qris_project.profiles:
            analysis_params['centerline'] = self.qris_project.profiles[centerline]

        dem = self.analysis.metadata.get('dem', None)
        if dem is not None and dem in self.qris_project.rasters:
            analysis_params['dem'] = self.qris_project.rasters[dem]

        valley_bottom = self.analysis.metadata.get('valley_bottom', None)
        if valley_bottom is not None and valley_bottom in self.qris_project.valley_bottoms:
            analysis_params['valley_bottom'] = self.qris_project.valley_bottoms[valley_bottom]

        return analysis_params

    def _flush_pending_rows(self, conn: sqlite3.Connection, pending_rows: list):
        if len(pending_rows) < 1:
            return

        curs = conn.cursor()
        curs.executemany(
            """INSERT INTO metric_values (
                    analysis_id
                    , event_id
                    , sample_frame_feature_id
                    , metric_id
                    , manual_value
                    , automated_value
                    , is_manual
                    , uncertainty
                    , unit_id
                    , metadata
                    , description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (analysis_id, event_id, sample_frame_feature_id, metric_id) DO UPDATE SET
                    manual_value = excluded.manual_value
                    , automated_value = excluded.automated_value
                    , is_manual = excluded.is_manual
                    , uncertainty = excluded.uncertainty
                    , metadata = excluded.metadata
                    , description = excluded.description""",
            pending_rows,
        )
        conn.commit()
        pending_rows.clear()

    def _queue_metric_value_row(self, pending_rows: list, event_id: int, sample_frame_id: int, metric_value: MetricValue, unit_id: int = None):
        pending_rows.append((
            self.analysis.id,
            event_id,
            sample_frame_id,
            metric_value.metric.id,
            metric_value.manual_value,
            metric_value.automated_value,
            metric_value.is_manual,
            json.dumps(metric_value.uncertainty),
            unit_id,
            json.dumps(metric_value.metadata) if metric_value.metadata is not None and len(metric_value.metadata) > 0 else None,
            metric_value.description,
        ))

    def _checkpoint_wal(self):
        with sqlite3.connect(self.qris_project.project_file, isolation_level=None) as conn:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    @staticmethod
    def _dependency_key(machine_name: str, protocol_machine_code: str, version=None) -> str:
        version_key = '' if version is None else str(version)
        return f'{protocol_machine_code}::{machine_name}::{version_key}'

    @staticmethod
    def _normalize_version(version):
        if version is None:
            return None
        version_str = str(version).strip()
        if version_str == '':
            return ''
        try:
            normalized = format(Decimal(version_str).normalize(), 'f')
            if '.' in normalized:
                normalized = normalized.rstrip('0').rstrip('.')
            return normalized
        except (InvalidOperation, ValueError):
            return version_str

    @staticmethod
    def _dependency_keys(machine_name: str, protocol_machine_code: str, version=None) -> list:
        if version is None:
            return [AnalysisMetricsTask._dependency_key(machine_name, protocol_machine_code, None)]

        raw_key = AnalysisMetricsTask._dependency_key(machine_name, protocol_machine_code, version)
        normalized_version = AnalysisMetricsTask._normalize_version(version)
        if normalized_version is None:
            return [raw_key]
        normalized_key = AnalysisMetricsTask._dependency_key(machine_name, protocol_machine_code, normalized_version)
        if normalized_key == raw_key:
            return [raw_key]
        return [raw_key, normalized_key]

    @staticmethod
    def _resolve_runtime_dependency_values(metric, metric_values: dict) -> dict:
        """Resolve dependency scalar values from current metric values in scope.

        Returns a mapping keyed by dependency usage when provided, otherwise
        by `protocol::machine::version` and `protocol::machine`.
        """
        metric_params = metric.metric_params or {}
        dependencies = metric_params.get('metric_dependencies', [])
        if len(dependencies) < 1:
            return {}

        values_by_exact = {}
        values_by_loose = {}
        for metric_id, metric_value in metric_values.items():
            if metric_value is None or metric_value.metric is None:
                continue
            current_value = metric_value.current_value()
            if current_value is None:
                continue
            metric_obj = metric_value.metric
            exact_keys = AnalysisMetricsTask._dependency_keys(
                metric_obj.machine_name,
                metric_obj.protocol_machine_code,
                metric_obj.version,
            )
            loose_key = AnalysisMetricsTask._dependency_key(
                metric_obj.machine_name,
                metric_obj.protocol_machine_code,
                None,
            )
            for exact_key in exact_keys:
                values_by_exact[exact_key] = current_value
            values_by_loose.setdefault(loose_key, []).append(current_value)

        resolved = {}
        for dep in dependencies:
            dep_machine = dep.get('metric_id_ref')
            if not dep_machine:
                raise MetricInputMissingError(
                    f"Metric '{metric.machine_name}' has dependency missing metric_id_ref"
                )

            dep_protocol = dep.get('protocol_machine_code_ref', metric.protocol_machine_code)
            dep_version = dep.get('version')

            if dep_version is not None:
                candidate_keys = AnalysisMetricsTask._dependency_keys(dep_machine, dep_protocol, dep_version)
                key = next((k for k in candidate_keys if k in values_by_exact), None)
                if key is None:
                    raise MetricInputMissingError(
                        f"Missing dependency value for '{dep_protocol}.{dep_machine}' version '{dep_version}'"
                    )
                resolved_value = values_by_exact[key]
            else:
                loose_key = AnalysisMetricsTask._dependency_key(dep_machine, dep_protocol, None)
                candidates = values_by_loose.get(loose_key, [])
                if len(candidates) < 1:
                    raise MetricInputMissingError(
                        f"Missing dependency value for '{dep_protocol}.{dep_machine}'"
                    )
                if len(candidates) > 1:
                    raise MetricInputMissingError(
                        f"Ambiguous dependency value for '{dep_protocol}.{dep_machine}', specify version"
                    )
                resolved_value = candidates[0]

            usage = dep.get('usage')
            if usage:
                resolved[usage] = resolved_value

            for exact_key in AnalysisMetricsTask._dependency_keys(dep_machine, dep_protocol, dep_version):
                resolved[exact_key] = resolved_value
            resolved[AnalysisMetricsTask._dependency_key(dep_machine, dep_protocol, None)] = resolved_value

        return resolved

    @staticmethod
    def _build_metric_index(analysis_metrics: list):
        exact_index = {}
        loose_index = {}
        for am in analysis_metrics:
            metric = am.metric
            exact_keys = AnalysisMetricsTask._dependency_keys(
                metric.machine_name,
                metric.protocol_machine_code,
                metric.version,
            )
            loose_key = AnalysisMetricsTask._dependency_key(
                metric.machine_name,
                metric.protocol_machine_code,
                None,
            )
            for exact_key in exact_keys:
                exact_index[exact_key] = am
            loose_index.setdefault(loose_key, []).append(am)
        return exact_index, loose_index

    @staticmethod
    def _resolve_dependency(dep: dict, metric, exact_index: dict, loose_index: dict):
        ref_machine = dep.get('metric_id_ref')
        if not ref_machine:
            raise ValueError(
                f"Invalid dependency definition on metric '{metric.machine_name}': missing metric_id_ref"
            )

        ref_protocol = dep.get('protocol_machine_code_ref', metric.protocol_machine_code)
        ref_version = dep.get('version')

        if ref_version is not None:
            candidate_keys = AnalysisMetricsTask._dependency_keys(ref_machine, ref_protocol, ref_version)
            resolved = next((exact_index.get(k) for k in candidate_keys if k in exact_index), None)
            if resolved is None:
                raise ValueError(
                    f"Metric '{metric.machine_name}' depends on '{ref_protocol}.{ref_machine}' version '{ref_version}' "
                    "which is not available in this analysis"
                )
            return resolved

        key = AnalysisMetricsTask._dependency_key(ref_machine, ref_protocol, None)
        candidates = loose_index.get(key, [])
        if len(candidates) < 1:
            raise ValueError(
                f"Metric '{metric.machine_name}' depends on '{ref_protocol}.{ref_machine}' which is not available in this analysis"
            )
        if len(candidates) > 1:
            raise ValueError(
                f"Metric '{metric.machine_name}' dependency '{ref_protocol}.{ref_machine}' is ambiguous; specify dependency version"
            )
        return candidates[0]

    @staticmethod
    def _find_cycle_path(adjacency: dict):
        visited = set()
        stack = []
        stack_set = set()

        def visit(node_id):
            visited.add(node_id)
            stack.append(node_id)
            stack_set.add(node_id)

            for neighbor in adjacency.get(node_id, set()):
                if neighbor not in visited:
                    cycle = visit(neighbor)
                    if cycle:
                        return cycle
                elif neighbor in stack_set:
                    idx = stack.index(neighbor)
                    return stack[idx:] + [neighbor]

            stack.pop()
            stack_set.remove(node_id)
            return None

        for node_id in adjacency:
            if node_id not in visited:
                cycle = visit(node_id)
                if cycle:
                    return cycle
        return None

    @staticmethod
    def plan_metric_execution(analysis_metrics: dict, requested_metric_ids: list) -> list:
        """Return metrics in dependency-safe execution order.

        Includes requested metrics and any transitive metric dependencies.
        Raises ValueError for missing dependencies or cycles.
        """
        available = [am for _, am in analysis_metrics.items()]
        available_by_id = {am.metric.id: am for am in available}
        exact_index, loose_index = AnalysisMetricsTask._build_metric_index(available)

        requested_ids = [mid for mid in requested_metric_ids if mid in available_by_id]
        if len(requested_ids) < 1:
            return []

        requested_set = set(requested_ids)
        included = set()
        dependencies_by_metric = {}
        pending = list(requested_ids)

        while pending:
            metric_id = pending.pop()
            if metric_id in included:
                continue

            analysis_metric = available_by_id[metric_id]
            metric = analysis_metric.metric
            included.add(metric_id)

            deps = []
            metric_params = metric.metric_params or {}
            for dep in metric_params.get('metric_dependencies', []):
                dep_metric = AnalysisMetricsTask._resolve_dependency(dep, metric, exact_index, loose_index)
                deps.append(dep_metric.metric.id)
                pending.append(dep_metric.metric.id)

            dependencies_by_metric[metric_id] = deps

        indegree = {mid: 0 for mid in included}
        dependents = {mid: set() for mid in included}
        for metric_id, deps in dependencies_by_metric.items():
            for dep_id in deps:
                if dep_id not in included:
                    continue
                dependents[dep_id].add(metric_id)
                indegree[metric_id] += 1

        order_index = {
            metric_id: idx for idx, metric_id in enumerate([am.metric.id for am in available])
        }
        queue = deque(sorted([mid for mid, deg in indegree.items() if deg == 0], key=lambda mid: order_index.get(mid, 10**9)))
        execution_order = []

        while queue:
            current = queue.popleft()
            execution_order.append(current)
            for dependent in sorted(dependents[current], key=lambda mid: order_index.get(mid, 10**9)):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    queue.append(dependent)

        if len(execution_order) != len(included):
            cycle = AnalysisMetricsTask._find_cycle_path(dependents)
            if cycle:
                cycle_text = ' -> '.join([available_by_id[mid].metric.machine_name for mid in cycle if mid in available_by_id])
                raise ValueError(f'Metric dependency cycle detected: {cycle_text}')
            raise ValueError('Metric dependency cycle detected')

        return [available_by_id[mid] for mid in execution_order if mid in requested_set or mid in dependencies_by_metric]

    def run(self):
        try:
            requested_metric_id_set = set(self.metric_ids)
            selected_analysis_metrics = self.plan_metric_execution(
                self.analysis.analysis_metrics,
                self.metric_ids,
            )

            total = len(self.sample_frame_ids) * len(self.event_ids) * len(selected_analysis_metrics)
            self.summary['total'] = total
            if total == 0:
                self.setProgress(100)
                return True

            analysis_params = self._build_analysis_params()
            processed = 0
            pending_rows = []

            with sqlite3.connect(self.qris_project.project_file, timeout=10.0) as conn:
                for sample_frame_id in self.sample_frame_ids:
                    if self.isCanceled():
                        self.summary['canceled'] = True
                        self._flush_pending_rows(conn, pending_rows)
                        return False

                    for event_id in self.event_ids:
                        if self.isCanceled():
                            self.summary['canceled'] = True
                            self._flush_pending_rows(conn, pending_rows)
                            return False

                        event = self.qris_project.events.get(event_id, None)
                        if event is None:
                            processed += len(selected_analysis_metrics)
                            continue

                        metric_values = load_metric_values(
                            self.qris_project.project_file,
                            self.analysis,
                            event,
                            sample_frame_id,
                            self.qris_project.metrics,
                        )

                        for analysis_metric in selected_analysis_metrics:
                            if self.isCanceled():
                                self.summary['canceled'] = True
                                self._flush_pending_rows(conn, pending_rows)
                                return False

                            processed += 1
                            self.summary['processed'] = processed
                            self.setProgress((processed / total) * 100)

                            metric = analysis_metric.metric
                            metric_value = metric_values.get(
                                metric.id,
                                MetricValue(metric, None, None, False, None, None, metric.default_unit_id, None),
                            )

                            # Dependencies pulled in by the DAG but not explicitly requested:
                            # skip if they already have any value (manual or automated) so we
                            # don't overwrite manual entries or waste time recalculating them.
                            is_dependency_only = metric.id not in requested_metric_id_set
                            if is_dependency_only and metric_value.current_value() is not None:
                                self.summary['skipped_overwrite'] += 1
                                continue

                            if metric_value.automated_value is not None and not self.overwrite_existing:
                                self.summary['skipped_overwrite'] += 1
                                continue

                            if metric.metric_function is None:
                                self.summary['skipped_no_function'] += 1
                                continue

                            if metric.can_calculate_automated(self.qris_project, event_id, self.analysis.id) is False:
                                self.summary['skipped_not_feasible'] += 1
                                self._log(
                                    f'Unable to calculate metric {metric.name} for {event.name} due to missing required layer in the data capture event.',
                                    Qgis.Warning,
                                )
                                continue

                            try:
                                resolved_dependencies = self._resolve_runtime_dependency_values(metric, metric_values)
                                metric_analysis_params = dict(analysis_params)
                                if resolved_dependencies:
                                    metric_analysis_params['metric_dependencies'] = resolved_dependencies

                                metric_calculation = getattr(analysis_metrics, metric.metric_function)
                                result = metric_calculation(
                                    self.qris_project.project_file,
                                    sample_frame_id,
                                    event_id,
                                    metric.metric_params,
                                    metric_analysis_params,
                                )

                                metric_value.automated_value = result
                                if self.force_active:
                                    metric_value.is_manual = False

                                if metric_value.metadata is None:
                                    metric_value.metadata = {}
                                metric_value.metadata.pop('calculation_error', None)

                                self._queue_metric_value_row(
                                    pending_rows,
                                    event_id,
                                    sample_frame_id,
                                    metric_value,
                                    metric.default_unit_id,
                                )
                                metric_values[metric.id] = metric_value

                                if len(pending_rows) >= self.BATCH_SIZE:
                                    self._flush_pending_rows(conn, pending_rows)

                                self.summary['success'] += 1

                            except MetricInputMissingError as ex:
                                self.summary['missing_data'] += 1
                                self._log(f'Error calculating metric {metric.name}: {ex}', Qgis.Warning)

                                if metric_value.metadata is None:
                                    metric_value.metadata = {}
                                metric_value.metadata['calculation_error'] = str(ex)
                                metric_value.automated_value = None

                                self._queue_metric_value_row(
                                    pending_rows,
                                    event_id,
                                    sample_frame_id,
                                    metric_value,
                                    metric.default_unit_id,
                                )
                                metric_values[metric.id] = metric_value

                                if len(pending_rows) >= self.BATCH_SIZE:
                                    self._flush_pending_rows(conn, pending_rows)

                            except Exception as ex:
                                self.summary['errors'] += 1
                                self._log(f'Error calculating metric {metric.name}: {ex}', Qgis.Warning)

                                if metric_value.metadata is None:
                                    metric_value.metadata = {}
                                metric_value.metadata['calculation_error'] = str(ex)
                                metric_value.automated_value = None

                                self._queue_metric_value_row(
                                    pending_rows,
                                    event_id,
                                    sample_frame_id,
                                    metric_value,
                                    metric.default_unit_id,
                                )
                                metric_values[metric.id] = metric_value

                                if len(pending_rows) >= self.BATCH_SIZE:
                                    self._flush_pending_rows(conn, pending_rows)

                self._flush_pending_rows(conn, pending_rows)

            self._checkpoint_wal()

            self.setProgress(100)
            return True

        except Exception as ex:
            self.exception = ex
            self.summary['exception'] = str(ex)
            return False

    def finished(self, result: bool):
        if result:
            QgsMessageLog.logMessage('Analysis metric calculation task complete.', MESSAGE_CATEGORY, Qgis.Success)
        elif self.exception is None and self.summary.get('canceled', False):
            QgsMessageLog.logMessage('Analysis metric calculation task canceled.', MESSAGE_CATEGORY, Qgis.Warning)
        elif self.exception is None:
            QgsMessageLog.logMessage('Analysis metric task ended without exception.', MESSAGE_CATEGORY, Qgis.Warning)
        else:
            QgsMessageLog.logMessage(f'Analysis metric task failed: {self.exception}', MESSAGE_CATEGORY, Qgis.Critical)

        self.on_complete.emit(self.summary)

    def cancel(self):
        QgsMessageLog.logMessage('Analysis metric task canceled by user.', MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
