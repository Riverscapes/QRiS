import sqlite3
import json

from .db_item import DBItem
from ..gp.analysis_metrics import analysis_metric_unit_type


METRIC_SCHEMA = './qris_metrics.schema.json'

default_units = {'distance': 'meters', 'area': 'square meters', 'ratio': 'ratio', 'count': 'count'}

class Metric(DBItem):

    def __init__(self, id: int, name: str, machine_name:str, protocol_machine_code:str, description: str, default_level_id: int, metric_function: str, metric_params: str, default_unit_id: int = None, definition_url: str = None, metadata: dict = None, version: int = 1):
        super().__init__('metrics', id, name)
        self.machine_name = machine_name
        self.description = description
        self.protocol_machine_code = protocol_machine_code
        self.default_level_id = default_level_id
        self.default_unit_id = default_unit_id
        self.metric_function = metric_function
        self.metric_params: dict = metric_params
        self.icon = 'calculate'
        self.definition_url = definition_url
        self.metadata = metadata
        self.version = version
        # This is the base unit as defined in the metric calculation function
        self.unit_type = analysis_metric_unit_type.get(self.metric_function, None)
        self.base_unit = default_units.get(self.unit_type, None)
        self.normalized = True if any(metric_layer.get('usage', None) == 'normalization' for metric_layer in metric_params.get('dce_layers', []) + metric_params.get('inputs', [])) else False
        if self.normalized:
            self.base_unit = 'meters'
            if self.unit_type == 'distance':
                self.unit_type = 'ratio'
        self.tolerance = self.metadata.get('tolerance', None) if self.metadata else None  # no tolerance = no testing for tolerance
        self.min_value = self.metadata.get('minimum_value', None) if self.metadata else None
        self.max_value = self.metadata.get('maximum_value', None) if self.metadata else None
        self.precision = self.metadata.get('precision', None) if self.metadata else None  # No precision = full float value
        self.status = self.metadata.get('status', 'active') if self.metadata else 'active'  # active, deprecated

    def can_calculate_automated(self, qris_project, event_id, analysis_id) -> bool: 

        # check if the metric can be calulated automatically
        dce = qris_project.events.get(event_id, None)
        if dce is None:
            return False 
        # check if the metric is in the dce layers
        metric_layers = self.metric_params.get('dce_layers', [])
        # we need to be a bit more detailed here. 
        # 1) Sort the layers by the 'usage', including None.
        # 2) iterate through the various usages. If more than one layer per usage, we only need to make sure one exists in the dce

        usage_layers = {}
        for metric_layer in metric_layers:
            usage = metric_layer.get('usage', None)
            if usage not in usage_layers:
                usage_layers[usage] = []
            usage_layers[usage].append(metric_layer)
        
        for usage, layers in usage_layers.items():
            layer_ids = [layer.get('layer_id_ref', None) for layer in layers]
            if not any(event_layer.layer.layer_id in layer_ids for event_layer in dce.event_layers):
                return False
            
        analysis = qris_project.analyses.get(analysis_id, None)
        inputs = self.metric_params.get('inputs', None)
        if inputs is not None:
            for analysis_input in inputs:
                input_id = analysis_input.get('input_ref', None)
                if input_id is not None:
                    if analysis.metadata.get(input_id, None) is None:
                        return False
        return True

    def get_metric_protocol(self, protocols: dict):
        for protocol in protocols.values():
            if protocol.machine_code == self.protocol_machine_code:
                return protocol
        return None

def load_metrics(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT * FROM calculations')
    metric_functions = {row['id']: row['metric_function'] for row in curs.fetchall()}

    curs.execute('SELECT * FROM protocols')
    protocols = {row['id']: row['machine_code'] for row in curs.fetchall()}

    curs.execute('SELECT * FROM metrics')
    return {row['id']: Metric(
        row['id'],
        row['name'],
        row['machine_name'],
        protocols[int(row['protocol_id'])],
        row['description'],
        row['default_level_id'],
        metric_functions.get(row['calculation_id'], None),
        json.loads(row['metric_params']) if row['metric_params'] else None,
        row['unit_id'],
        row['definition_url'],
        json.loads(row['metadata']) if row['metadata'] else None,
        row['version']
    ) for row in curs.fetchall()}

def insert_metric(db_path: str, name: str, machine_name: str, protocol_machine_name: str, description: str, metric_level, metric_function, metric_params, default_unit, definition_url, metadata=None, version=1) -> Metric:

    metric = None
    if description is not None:
        description = description if len(description) > 0 else None
    metadata_str = json.dumps(metadata) if metadata is not None else None
    metric_params_str = json.dumps(metric_params) if metric_params is not None else None

    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            # Get the protocol id
            curs.execute('SELECT id FROM protocols WHERE machine_code = ?', [protocol_machine_name])
            protocol_id = curs.fetchone()[0]
            # make sure the metric_name and version are unique
            curs.execute('SELECT id FROM metrics WHERE name = ? AND version = ? AND protocol_id = ?', [name, version, protocol_id])
            metric_ids = curs.fetchone()
            if metric_ids is not None:
                raise ValueError(f"Metric '{name}' version '{version}' already exists in database.")
            # get the metric level id
            curs.execute('SELECT id FROM metric_levels WHERE name = ?', [metric_level])
            metric_level_ids = curs.fetchone()
            if metric_level_ids is None:
                raise ValueError(f"Metric Level type '{metric_level}' not found in database.")
            metric_level_id = metric_level_ids[0]
            # get the calculation id
            curs.execute('SELECT id FROM calculations WHERE metric_function = ?', [metric_function])
            calculation_ids = curs.fetchone()
            if calculation_ids is None:
                raise ValueError(f"Calculation '{metric_function}' not found in database.")
            calculation_id = calculation_ids[0]
            # get the unit id
            if default_unit is not None and default_unit != '':
                curs.execute('SELECT id FROM lkp_units WHERE name = ?', [default_unit])
                unit_ids = curs.fetchone()
                if unit_ids is None:
                    raise ValueError(f"Unit '{default_unit}' not found in database.")
                unit_id = unit_ids[0]
            else:
                unit_id = None

            curs.execute('INSERT INTO metrics (name, machine_name, protocol_id, description, default_level_id, calculation_id, metric_params, unit_id, definition_url, metadata, version) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [name, machine_name, protocol_id, description, metric_level_id, calculation_id, metric_params_str, unit_id, definition_url, metadata_str, version])
            id = curs.lastrowid
            metric = Metric(id, name, machine_name, protocol_machine_name, description, metric_level_id, metric_function, metric_params, unit_id, definition_url, metadata, version)
            conn.commit()

        except Exception as ex:
            metric = None
            conn.rollback()
            raise ex

    return id, metric

def update_metric(db_path: str, id: int, name: str, machine_name: str, protocol_machine_code: str, description: str, metric_level, metric_function, metric_params, default_unit, definition_url, metadata=None, version=1) -> Metric:
    
        metric = None
        description = description if len(description) > 0 else None
        metadata_str = json.dumps(metadata) if metadata is not None else None
        metric_params_str = json.dumps(metric_params) if metric_params is not None else None
    
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                # get the metric level id
                curs.execute('SELECT id FROM metric_levels WHERE name = ?', [metric_level])
                metric_level_ids = curs.fetchone()
                if metric_level_ids is None:
                    raise ValueError(f"Metric Level type '{metric_level}' not found in database.")
                metric_level_id = metric_level_ids[0]
                # get the calculation id
                curs.execute('SELECT id FROM calculations WHERE metric_function = ?', [metric_function])
                calculation_ids = curs.fetchone()
                if calculation_ids is None:
                    raise ValueError(f"Calculation '{metric_function}' not found in database.")
                calculation_id = calculation_ids[0]
                # get the unit id
                if default_unit is not None and default_unit != '':
                    curs.execute('SELECT id FROM lkp_units WHERE name = ?', [default_unit])
                    unit_ids = curs.fetchone()
                    if unit_ids is None:
                        raise ValueError(f"Unit '{default_unit}' not found in database.")
                    unit_id = unit_ids[0]
                else:
                    unit_id = None
    
                curs.execute('UPDATE metrics SET name = ?, description = ?, default_level_id = ?, calculation_id = ?, metric_params = ?, unit_id = ?, definition_url = ?, metadata = ? WHERE machine_name = ? and version = ?', [name, description, metric_level_id, calculation_id, metric_params_str, unit_id, definition_url, metadata_str, machine_name, version])
                metric = Metric(id, name, machine_name, description, metric_level_id, metric_function, metric_params, unit_id, definition_url, metadata, version)
                conn.commit()
    
            except Exception as ex:
                metric = None
                conn.rollback()
                raise ex
    
        return metric

def verify_metric(db_path: str, id: int, name: str, machine_name: str, description: str, metric_level, metric_function, metric_params, default_unit, definition_url, metadata=None, version=1) -> bool:

    description = description if len(description) > 0 else None

    with sqlite3.connect(db_path) as conn:
        try:
            conn.row_factory = sqlite3.Row
            curs = conn.cursor()
            # get the metric for the machine_name and version
            curs.execute('SELECT * FROM metrics WHERE name = ? AND version = ?', [name, version])
            metric = curs.fetchone()

            if name != metric['name'] or definition_url != metric['definition_url']:
                return False
            if description is not None:
                if description != metric['description']:
                    return False
            else:
                if metric['description'] is not None:
                    return False
            # get the metric level id
            curs.execute('SELECT id FROM metric_levels WHERE name = ?', [metric_level])
            metric_level_ids = curs.fetchone()
            if metric_level_ids is None:
                raise ValueError(f"Metric Level type '{metric_level}' not found in database.")
            if metric_level_ids[0] != metric['default_level_id']:
                return False
            # get the calculation id
            curs.execute('SELECT id FROM calculations WHERE metric_function = ?', [metric_function])
            calculation_ids = curs.fetchone()
            if calculation_ids is None:
                raise ValueError(f"Calculation '{metric_function}' not found in database.")
            if calculation_ids[0] != metric['calculation_id']:
                return False
            # get the unit id
            if default_unit != metric['unit_id']:
                return False
            if metric_params is not None:
                if metric_params != json.loads(metric['metric_params']):
                    return False
            else:
                if metric['metric_params'] is not None:
                    return False
            if metadata is not None:
                if metadata != json.loads(metric['metadata']):
                    return False
            else:
                if metric['metadata'] is not None:
                    return False

        except Exception as ex:
            raise ex
        
    return True
