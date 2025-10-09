import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional, Any

from PyQt5.QtCore import QSettings

from .settings import Settings

ORGANIZATION = 'Riverscapes'
APPNAME = 'QRiS'
SHOW_EXPERIMENTAL_PROTOCOLS = 'show_experimental_protocols'
LOCAL_PROTOCOL_FOLDER = 'local_protocol_folder'

FIELD_TYPES = {
    'ListField': 'list',
    'TextField': 'text',
    'IntegerField': 'integer',
    'FloatField': 'float',
    'AttachmentField': 'attachment',
}

@dataclass
class MetadataItem:
    key: str
    value: str
    type: str

@dataclass
class FieldDefinition:
    id: str
    type: str
    label: str
    required: bool = False
    allow_custom_values: bool = False
    description: Optional[str] = None
    values: Optional[List[str]] = None
    default_value: Optional[str] = None
    visibility_field: Optional[str] = None
    visibility_values: Optional[List[str]] = None
    allow_multiple_values: Optional[bool] = None
    derived_values: Optional[List[str]] = None
    slider: Optional[dict] = None

@dataclass
class LayerDefinition:
    id: str
    version: str
    geom_type: str
    label: str
    symbology: str
    description: Optional[str] = None
    hierarchy: Optional[str] = None
    fields: List[FieldDefinition] = field(default_factory=list)
    menu_items: Optional[List[str]] = None
    protocol_definition = None

@dataclass
class MetricDefinition:
    id: str
    version: str
    calculation_machine_code: str
    label: str
    default_level: str
    description: Optional[str] = None
    definition_url: Optional[str] = None
    minimum_value: Optional[float] = None
    maximum_value: Optional[float] = None
    precision: Optional[int] = None
    parameters: List[Any] = None
    protocol_defintion = None
    status = 'active'

@dataclass
class ProtocolDefinition:
    machine_code: str
    protocol_type: str
    version: str
    status: str
    label: str
    description: str
    url: str
    citation: str
    author: str
    creation_date: str
    updated_date: str
    metadata: List[MetadataItem] = field(default_factory=list)
    layers: List[LayerDefinition] = field(default_factory=list)
    metrics: List[MetricDefinition] = field(default_factory=list)

    def unique_key(self):
        return f'{self.machine_code}::{self.version}'

def load_protocol_definitions(project_directory: str, show_experimental: bool = None) -> List[ProtocolDefinition]:
    """Load protocol from xml"""

    if show_experimental is None:
        settings = QSettings(ORGANIZATION, APPNAME)
        show_experimental = settings.value(SHOW_EXPERIMENTAL_PROTOCOLS, False, type=bool)

    directories = [project_directory]
    q_settings = QSettings(ORGANIZATION, APPNAME)
    directories.append(q_settings.value(LOCAL_PROTOCOL_FOLDER, '', type=str))
    settings = Settings()
    directories.append(settings.getValue('protocolsDir'))

    protocols = list()
    for protocol_directory in directories:
        if protocol_directory is None or not os.path.isdir(protocol_directory):
            continue
        for filename in os.listdir(protocol_directory):
            if filename.endswith('.xml'):
                protocol = load_protocool_from_xml(os.path.join(protocol_directory, filename))
                if protocol is not None:
                    if protocol.status == 'experimental' and not show_experimental:
                        continue
                    if protocol.status == 'deprecated':
                        continue
                    protocols.append(protocol)

    return protocols

def load_protocool_from_xml(file_path: str) -> ProtocolDefinition:
    """Load protocol from xml"""

    tree = ET.parse(file_path)
    root = tree.getroot()
    if root.tag != 'Protocol':
        return None

    machine_code = root.attrib.get('machine_code')
    protocol_type = root.attrib.get('protocol_type', None)
    if machine_code == 'ASBUILT':
        protocol_type = 'asbuilt'
    elif machine_code == 'DESIGN':
        protocol_type = 'design'
    elif protocol_type is None:
        protocol_type = 'dce'

    protocol = ProtocolDefinition(
        machine_code=machine_code,
        protocol_type=protocol_type,
        version=root.attrib.get('version'),
        status=root.attrib.get('status'),
        label=root.find('Label').text,
        description=root.find('Description').text,
        url=root.find('URL').text,
        citation=root.find('Citation').text,
        author=root.find('Author').text,
        creation_date=root.find('CreationDate').text,
        updated_date=root.find('UpdatedDate').text,
    )

    for layer_elem in root.findall('Layers/Layer'):
        
        fields = []
        for field_elem in layer_elem.findall('Fields/'):
            derived_values = None
            if field_elem.find('DerivedValues') is not None:
                derived_values = [
                    {
                        'output': dv.attrib.get('output'),
                        'inputs': [{input_elem.attrib.get('field_id_ref'): input_elem.text} for input_elem in dv.findall('InputValue')]
                    }
                    for dv in field_elem.find('DerivedValues').findall('DerivedValue')
                ]
            slider = None
            if field_elem.find('Slider') is not None:
                if FIELD_TYPES[field_elem.tag] == 'integer':
                    slider = {
                        'min': int(field_elem.find('Slider').attrib.get('min')),
                        'max': int(field_elem.find('Slider').attrib.get('max')),
                        'step': int(field_elem.find('Slider').attrib.get('step')),
                    }
                else:
                    slider = {
                        'min': float(field_elem.find('Slider').attrib.get('min')),
                        'max': float(field_elem.find('Slider').attrib.get('max')),
                        'step': float(field_elem.find('Slider').attrib.get('step')),
                    }

            field = FieldDefinition(
                    id=field_elem.attrib.get('id'),
                    type=FIELD_TYPES[field_elem.tag],
                    label=field_elem.find('Label').text,
                    required=field_elem.attrib.get('required') == 'true',
                    allow_custom_values=field_elem.find('Values').attrib.get('allow_custom_values') == 'true' if field_elem.find('Values') is not None else False,
                    description=field_elem.find('Description').text if field_elem.find('Description') is not None else None,
                    values=[v.text for v in field_elem.find('Values').findall('Value')] if field_elem.find('Values') is not None else None,
                    default_value=str(field_elem.find('DefaultValue').text) if field_elem.find('DefaultValue') is not None else None,
                    visibility_field=field_elem.find('Visibility').attrib.get('field_id_ref') if field_elem.find('Visibility') is not None else None,
                    visibility_values=[v.text for v in field_elem.find('Visibility').find('Values').findall('Value')] if field_elem.find('Visibility') is not None else None,
                    allow_multiple_values=field_elem.find('Values').attrib.get('allow_multiple_values') == 'true' if field_elem.find('Values') is not None else None,
                    derived_values=derived_values,
                    slider=slider
                )
            fields.append(field)

        # hierarchy is a list of the text of HeirarchyItem elements
        hierarchy = [h.text for h in layer_elem.findall('Hierarchy/HierarchyItem')]

        layer = LayerDefinition(
            id=layer_elem.attrib.get('id'),
            version=layer_elem.attrib.get('version'),
            geom_type=layer_elem.attrib.get('geom_type'),
            label=layer_elem.find('Label').text,
            symbology=layer_elem.find('Symbology').text,
            description=layer_elem.find('Description').text if layer_elem.find('Description') is not None else None,
            hierarchy=hierarchy,
            fields=fields,
            menu_items=[m.text for m in layer_elem.find('MenuItems').findall('MenuItem')] if layer_elem.find('MenuItems') is not None else None
        )
        protocol.layers.append(layer)

    for metric_elem in root.findall('Metrics/Metric'):

        parameters = {}
        inputs = []
        for input_elem in metric_elem.findall('Parameters/InputLayer'):
            input = {
                'input_ref': input_elem.attrib.get('input_ref'),
                'usage': input_elem.attrib.get('usage')
            }
            inputs.append(input)
        if len(inputs) > 0:
            parameters['inputs'] = inputs

        dce_layers = []
        for dce_elem in metric_elem.findall('Parameters/DCELayer'):
            dce_layer = {
                'layer_id_ref': dce_elem.attrib.get('layer_id_ref')
            }
            attribute_filter_elem = dce_elem.find('AttributeFilter')
            if attribute_filter_elem is not None:
                attribute_filter = {
                    'field_id_ref': attribute_filter_elem.attrib.get('field_id_ref'),
                    'values': [v.text for v in attribute_filter_elem.findall('Value')]
                }
                dce_layer['attribute_filter'] = attribute_filter
            count_fields_elem = dce_elem.find('CountFields')
            if count_fields_elem is not None:
                count_fields = []
                for count_field_elem in count_fields_elem.findall('CountField'):
                    count_field = {
                        'field_id_ref': count_field_elem.attrib.get('field_id_ref')
                    }
                    count_fields.append(count_field)
                dce_layer['count_fields'] = count_fields
            usage_elem = dce_elem.find('Usage')
            if usage_elem is not None:
                dce_layer['usage'] = usage_elem.text
            dce_layers.append(dce_layer)
        if len(dce_layers) > 0:
            parameters['dce_layers'] = dce_layers
        
        metric = MetricDefinition(
            id=metric_elem.attrib.get('id'),
            version=metric_elem.attrib.get('version'),
            calculation_machine_code=metric_elem.attrib.get('calculation_machine_code'),
            label=metric_elem.find('Label').text,
            default_level=metric_elem.find('DefaultLevel').text,
            description=metric_elem.find('Description').text if metric_elem.find('Description') is not None else None,
            definition_url=metric_elem.find('DefinitionURL').text if metric_elem.find('DefinitionURL') is not None else None,
            minimum_value=float(metric_elem.find('MinimumValue').text) if metric_elem.find('MinimumValue') is not None else None,
            maximum_value=float(metric_elem.find('MaximumValue').text) if metric_elem.find('MaximumValue') is not None else None,
            precision=int(metric_elem.find('Precision').text) if metric_elem.find('Precision') is not None else None,
            parameters=parameters if len(parameters) > 0 else None,
            status=metric_elem.attrib.get('status', 'active')
        )
        protocol.metrics.append(metric)

    for metadata_elem in root.findall('Metadata/MetadataItem'):
        metadata = MetadataItem(
            key=metadata_elem.attrib.get('key'),
            value=metadata_elem.text,
            type=metadata_elem.attrib.get('type')
        )
        protocol.metadata.append(metadata)

    return protocol