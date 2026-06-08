import json
import sqlite3
import time
from decimal import Decimal, InvalidOperation
from typing import Dict

from .db_item_spatial import DBItemSpatial
from .sample_frame import SampleFrame
from .analysis_metric import AnalysisMetric, store_analysis_metrics

ANALYSIS_MACHINE_CODE = 'ANALYSIS'
default_units = {'distance': 'meters', 'area': 'square meters', 'ratio': 'ratio', 'count': 'count'}


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


def checkpoint_wal(db_path: str) -> None:
    with sqlite3.connect(db_path, isolation_level=None) as conn:
        for _ in range(5):
            busy, _log, _checkpointed = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            if busy == 0:
                break
            time.sleep(0.15)

class Analysis(DBItemSpatial):

    def __init__(self, id: int, name: str, description: str, sample_frame: SampleFrame, metadata: dict = None):
        super().__init__('analyses', id, name, sample_frame.fc_name, 'sample_frame_id', 'Polygon', metadata=metadata)
        self.description = description
        self.icon = 'analysis'
        self.sample_frame = sample_frame
        self.analysis_metrics = None
    
    def update(self, db_path: str, name: str, description: str, analysis_metrics: dict, metadata: dict = None) -> None:

        description = description if len(description) > 0 else None
        metadata['units'] = self.units
        metadata_str = json.dumps(metadata) if metadata is not None else None

        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE analyses SET name = ?, description = ?, metadata = ? WHERE id = ?', [name, description, metadata_str, self.id])

                store_analysis_metrics(curs, self.id, analysis_metrics)
                self.create_spatial_view(curs)
                conn.commit()

                self.name = name
                self.description = description
                self.analysis_metrics = analysis_metrics
                self.set_metadata(metadata)
                checkpoint_wal(db_path)

            except Exception as ex:
                conn.rollback()
                raise Exception(f"Error updating analysis {self.id}: {ex}") from ex
            
    def set_metadata(self, metadata):
        super().set_metadata(metadata)
        self.profile = self.metadata.get('centerline', None) # really just the profile id
        self.dem = self.metadata.get('dem', None)
        self.units = self.metadata.get('units', default_units)
            

    def create_spatial_view(self, curs: sqlite3.Cursor) -> None:
        """Create a spatial view of the Analysis features."""
        
        # Filter by selected events if known
        event_filter = ""
        if self.metadata and 'selected_events' in self.metadata:
            selected_events = self.metadata['selected_events']
            if selected_events:
                 event_ids = ",".join([str(id) for id in selected_events])
                 event_filter = f" AND metric_values.event_id IN ({event_ids})"

        # prepare sql string for each metric
        sql_metric = ", ".join(
            [f'MAX(CASE WHEN metric_id = {metric_id} THEN (CASE WHEN is_manual = 1 THEN manual_value ELSE automated_value END) END) AS "{analysis_metric.metric.name}"' for metric_id, analysis_metric in self.analysis_metrics.items()])
        sql = f"""CREATE VIEW {self.view_name} AS SELECT * FROM sample_frame_features JOIN (SELECT sample_frame_feature_id, {sql_metric} FROM metric_values JOIN metrics ON metric_values.metric_id == metrics.id WHERE metric_values.analysis_id = {self.id}{event_filter} GROUP BY sample_frame_feature_id) AS x ON sample_frame_features.fid = x.sample_frame_feature_id"""  # nosec B608 - view_name is auto-generated (vw_<table>_<int_id>); all other values are integer DB IDs
        if sql_metric == '':
            sql = f"CREATE VIEW {self.view_name} AS SELECT * FROM sample_frame_features WHERE sample_frame_id == {self.sample_frame.id}"  # nosec B608 - view_name is auto-generated; sample_frame.id is an integer DB ID
        # check if the view already exists, if so, delete it
        if self.check_spatial_view_exists(curs):
            curs.execute(f"DROP VIEW {self.view_name}")  # nosec B608 - view_name is auto-generated (vw_<table>_<int_id>)
            curs.execute(f"DELETE FROM gpkg_contents WHERE table_name = '{self.view_name}'")  # nosec B608 - view_name is auto-generated
            curs.execute(f"DELETE FROM gpkg_geometry_columns WHERE table_name = '{self.view_name}'")  # nosec B608 - view_name is auto-generated
        curs.execute(sql)
        # add view to geopackage
        sql = "INSERT INTO gpkg_contents (table_name, data_type, identifier, description, srs_id) VALUES (?, ?, ?, ?, ?)"
        curs.execute(sql, [self.view_name, "features", self.view_name, "", self.epsg])
        sql = (
            "INSERT INTO gpkg_geometry_columns "
            "(table_name, column_name, geometry_type_name, srs_id, z, m) "
            "VALUES (?, ?, ?, ?, ?, ?)"
        )
        curs.execute(sql, [self.view_name, 'geom', self.geom_type.upper(), self.epsg, 0, 0])


    def check_metric_feasibility(self, metric, project, event=None) -> Dict:
        return self._check_metric_feasibility(metric, project, event, set())

    def _check_metric_feasibility(self, metric, project, event=None, visited_metrics=None) -> Dict:
        """
        Checks if the automated metric can be calculated based on:
        1. Automation definition existence
        2. Required Inputs (Analysis Metadata)
        3. Required DCE Layers (Project Configuration & Event Content)
        
        Returns:
            dict: {
                'status': str ('MANUAL_ONLY', 'FEASIBLE', 'FEASIBLE_EMPTY', 'NOT_FEASIBLE'),
                'reasons': list[str]
            }
        """
        if visited_metrics is None:
            visited_metrics = set()

        metric_identity = (
            getattr(metric, 'protocol_machine_code', None),
            getattr(metric, 'machine_name', None),
            getattr(metric, 'version', None),
        )
        # Dependency cycles are blocked at execution planning, but this guard keeps
        # feasibility checks safe if malformed definitions are loaded.
        if metric_identity in visited_metrics:
            return {
                'status': 'FEASIBLE',
                'reasons': []
            }
        visited_metrics.add(metric_identity)

        result = {
            'status': 'FEASIBLE',
            'reasons': []
        }
        
        # 1. Check Automation Definition
        if metric.metric_function == 'manual' or not metric.metric_params:
            result['status'] = 'MANUAL_ONLY'
            return result
            
        # 2. Check Inputs (Analysis Metadata)
        inputs = metric.metric_params.get('inputs', [])
        for input_item in inputs:
            ref = input_item.get('input_ref', '')
            if not ref: continue
                
            # Check if this key exists in analysis metadata (case insensitive)
            # metadata keys are usually lowercase, but let's be safe
            found = False
            for k, v in self.metadata.items():
                if k.lower() == ref.lower() and v is not None:
                    found = True
                    break
            
            if not found:
                 result['status'] = 'NOT_FEASIBLE'
                 result['reasons'].append(f"Missing Input: {ref}")

        # 2b. Check Metric Dependencies (selected analysis metrics)
        metric_dependencies = metric.metric_params.get('metric_dependencies', [])
        if metric_dependencies:
            selected_metrics = [am.metric for am in self.analysis_metrics.values()] if self.analysis_metrics else []
            selected_by_exact = {}
            for m in selected_metrics:
                raw_key = f"{m.protocol_machine_code}::{m.machine_name}::{m.version}"
                selected_by_exact[raw_key] = m
                normalized_version = _normalize_version(m.version)
                if normalized_version is not None:
                    normalized_key = f"{m.protocol_machine_code}::{m.machine_name}::{normalized_version}"
                    selected_by_exact[normalized_key] = m
            selected_by_loose = {}
            for m in selected_metrics:
                key = f"{m.protocol_machine_code}::{m.machine_name}"
                selected_by_loose.setdefault(key, []).append(m)

            for dep in metric_dependencies:
                dep_machine = dep.get('metric_id_ref')
                if not dep_machine:
                    result['status'] = 'NOT_FEASIBLE'
                    result['reasons'].append('Invalid metric dependency: missing metric_id_ref')
                    continue

                dep_protocol = dep.get('protocol_machine_code_ref', metric.protocol_machine_code)
                dep_version = dep.get('version')

                if dep_version is not None:
                    dep_key = f"{dep_protocol}::{dep_machine}::{dep_version}"
                    normalized_dep_version = _normalize_version(dep_version)
                    dep_keys = [dep_key]
                    if normalized_dep_version is not None:
                        dep_keys.append(f"{dep_protocol}::{dep_machine}::{normalized_dep_version}")
                    dep_metric = next((selected_by_exact.get(k) for k in dep_keys if k in selected_by_exact), None)
                    if dep_metric is None:
                        result['status'] = 'NOT_FEASIBLE'
                        result['reasons'].append(
                            f"Missing Metric Dependency: {dep_protocol}.{dep_machine} v{dep_version}"
                        )
                        continue
                else:
                    dep_key = f"{dep_protocol}::{dep_machine}"
                    dep_matches = selected_by_loose.get(dep_key, [])
                    if len(dep_matches) < 1:
                        result['status'] = 'NOT_FEASIBLE'
                        result['reasons'].append(
                            f"Missing Metric Dependency: {dep_protocol}.{dep_machine}"
                        )
                    elif len(dep_matches) > 1:
                        result['status'] = 'NOT_FEASIBLE'
                        result['reasons'].append(
                            f"Ambiguous Metric Dependency: {dep_protocol}.{dep_machine}"
                        )
                        continue
                    dep_metric = dep_matches[0]

                dep_feasibility = self._check_metric_feasibility(
                    dep_metric,
                    project,
                    event,
                    set(visited_metrics),
                )
                if dep_feasibility.get('status') == 'NOT_FEASIBLE':
                    result['status'] = 'NOT_FEASIBLE'
                    dep_reason = '; '.join(dep_feasibility.get('reasons', []))
                    if dep_reason:
                        result['reasons'].append(
                            f"Dependency Not Feasible: {dep_protocol}.{dep_machine} ({dep_reason})"
                        )
                    else:
                        result['reasons'].append(
                            f"Dependency Not Feasible: {dep_protocol}.{dep_machine}"
                        )

        # 3. Check DCE Layers (With Usage Grouping)
        dce_layers = metric.metric_params.get('dce_layers', [])
        
        usage_groups = {}
        required_individual = []
        
        for lyr_def in dce_layers:
            u = lyr_def.get('usage')
            if u:
                usage_groups.setdefault(u, []).append(lyr_def)
            else:
                required_individual.append(lyr_def)
                
        has_empty_required_layers = False

        def check_single_layer(layer_def):
            # Returns (is_valid_config, failure_reason, is_empty, empty_reason)
            ref = layer_def.get('layer_id_ref')
            if not ref: return False, "Invalid Layer Ref", False, None
            
            # Find Layer in Project
            # Scope to Metric Protocol if possible
            metric_protocol = next((p for p in project.protocols.values() if p.machine_code == metric.protocol_machine_code), None) if hasattr(project, 'protocols') else None
            layer = None
            if metric_protocol and hasattr(metric_protocol, 'protocol_layers'):
                 layer = next((l for l in metric_protocol.protocol_layers.values() if l.layer_id == ref), None)
            
            # Fallback
            if layer is None:
                layer = next((l for l in project.layers.values() if l.layer_id == ref), None)
            
            # Use display name if available, otherwise ref
            layer_name = layer.name if layer else ref

            if layer is None:
                return False, f"{ref}: Not Found in Project", False, None
            
            if event:
                # Check Configuration in DCE
                # We prioritize configuration check (is checked in setup)
                in_dce = False
                for el in event.event_layers:
                    if el.layer.id == layer.id:
                        in_dce = True
                        break
                if not in_dce:
                     return False, f"{layer_name}: Not added to DCE", False, None
                
                # Check Feature Counts
                is_empty = False
                empty_msg = None
                with sqlite3.connect(project.project_file) as conn:
                     curs = conn.cursor()
                     try:
                         # dce_points/lines/polys have layer_id and event_id
                         table_name = layer.DCE_LAYER_NAMES.get(layer.geom_type)
                         if table_name:
                             # Note: Column is event_layer_id, not layer_id (per schema.sql)
                             curs.execute(f"SELECT COUNT(*) FROM {table_name} WHERE event_id = ? AND event_layer_id = ?", [event.id, layer.id])  # nosec B608 - table_name is from DCE_LAYER_NAMES fixed dict
                             count = curs.fetchone()[0]
                             if count == 0:
                                 is_empty = True
                                 empty_msg = f"{layer_name}: No features"
                     except Exception:  # nosec B110 - failure means the DCE table doesn't exist; count stays 0 and is_empty remains False
                         # Table might not exist or other error
                         pass
                return True, None, is_empty, empty_msg
            
            return True, None, False, None

        # Check Individual Layers (Changed from AND to OR logic - at least one required)
        if required_individual:
            any_valid = False
            any_non_empty = False
            indiv_reasons = []
            indiv_empty_reasons = []

            for l_def in required_individual:
                is_valid, fail_reason, is_empty, empty_reason = check_single_layer(l_def)
                if is_valid:
                    any_valid = True
                    if not is_empty:
                        any_non_empty = True
                    else:
                        indiv_empty_reasons.append(empty_reason)
                else:
                    indiv_reasons.append(fail_reason)
            
            if not any_valid:
                result['status'] = 'NOT_FEASIBLE'
                unique_reasons = sorted(list(set(indiv_reasons)))
                result['reasons'].append("; ".join(unique_reasons))
            elif not any_non_empty:
                has_empty_required_layers = True
                # If we have valid layers but ALL are empty, we mark as FEASIBLE_EMPTY
                result['reasons'].append("; ".join(indiv_empty_reasons))

        # Check Usage Groups (OR Logic)
        for usage, l_defs in usage_groups.items():
            group_valid = False
            group_non_empty = False
            group_fail_reasons = []
            group_empty_reasons = []
            
            for l_def in l_defs:
                is_valid, fail_reason, is_empty, empty_reason = check_single_layer(l_def)
                if is_valid:
                    group_valid = True
                    if not is_empty:
                        group_non_empty = True
                    else:
                        group_empty_reasons.append(empty_reason)
                else:
                    group_fail_reasons.append(fail_reason)
            
            if not group_valid:
                 result['status'] = 'NOT_FEASIBLE'
                 unique_reasons = sorted(list(set(group_fail_reasons)))
                 result['reasons'].append("; ".join(unique_reasons))
            elif not group_non_empty:
                 has_empty_required_layers = True
                 result['reasons'].append("; ".join(group_empty_reasons))

        if result['status'] == 'FEASIBLE' and has_empty_required_layers:
            result['status'] = 'FEASIBLE_EMPTY'

        return result

def format_feasibility_text(f_status: str, f_reasons: list = None) -> str:
    """Helper to generate consistent tooltip text from feasibility status and reasons."""
    if f_reasons is None:
        f_reasons = []
    
    msg = ""
    if f_status == 'NOT_FEASIBLE':
        msg = "Automation Not Feasible:"
    elif f_status == 'FEASIBLE_EMPTY':
        msg = "Automation Feasible (Input Data Empty):"
    elif f_status == 'MANUAL_ONLY':
        return "Manual Entry Only"
    else: # FEASIBLE
        return "Automation Feasible"

    if f_reasons:
        msg += "\n" + "\n".join([f" - {r}" for r in f_reasons])
        
    return msg


def load_analyses(curs: sqlite3.Cursor, sample_frames: dict, metrics: dict) -> Dict[int, Analysis] :

    curs.execute('SELECT * FROM analyses')
    analyses = {row['id']: Analysis(
        row['id'],
        row['name'],
        row['description'],
        sample_frames[row['sample_frame_id']],
        json.loads(row['metadata']) if row['metadata'] is not None else None
    ) for row in curs.fetchall()}

    for analysis_id, analysis in analyses.items():
        curs.execute('SELECT * FROM analysis_metrics WHERE analysis_id = ?', [analysis_id])
        analysis.analysis_metrics = {row['metric_id']: AnalysisMetric(metrics[row['metric_id']], row['level_id']) for row in curs.fetchall() if row['metric_id'] in metrics}

    return analyses


def insert_analysis(db_path: str, name: str, description: str, sample_frame: SampleFrame, analysis_metrics: dict, metadata: dict=None) -> Analysis:
    """
    active metrics is a dictionary with metric_id keyed to metric_level_id
    """

    metadata_str = json.dumps(metadata) if metadata is not None else None

    analysis = None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO analyses (name, description, sample_frame_id, metadata) VALUES (?, ?, ?, ?)', [
                name, description if description is not None and len(description) > 0 else None, sample_frame.id, metadata_str])
            analysis_id = curs.lastrowid
            analysis = Analysis(analysis_id, name, description, sample_frame, metadata=metadata)
            store_analysis_metrics(curs, analysis_id, analysis_metrics)
            analysis.analysis_metrics = analysis_metrics
            analysis.create_spatial_view(curs)
            conn.commit()
            checkpoint_wal(db_path)
        except Exception as ex:
            conn.rollback()
            raise Exception(f"Error inserting analysis {name}: {ex}") from ex

    return analysis
