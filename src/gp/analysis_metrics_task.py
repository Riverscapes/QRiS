import json
import sqlite3

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

    def run(self):
        try:
            selected_analysis_metrics = [
                am for mid, am in self.analysis.analysis_metrics.items() if mid in self.metric_ids
            ]

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
                                metric_calculation = getattr(analysis_metrics, metric.metric_function)
                                result = metric_calculation(
                                    self.qris_project.project_file,
                                    sample_frame_id,
                                    event_id,
                                    metric.metric_params,
                                    analysis_params,
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

                                if len(pending_rows) >= self.BATCH_SIZE:
                                    self._flush_pending_rows(conn, pending_rows)

                self._flush_pending_rows(conn, pending_rows)

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
