import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional, Any


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

@dataclass
class ProtocolDefinition:
    machine_code: str
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

def load_protocols(protocol_directory: str) -> List[ProtocolDefinition]:
    """Load protocol from xml"""

    protocols = list()
    if protocol_directory is None or not os.path.isdir(protocol_directory):
        return protocols

    for filename in os.listdir(protocol_directory):
        if filename.endswith('.xml'):
            protocol = load_protocool_from_xml(os.path.join(protocol_directory, filename))
            if protocol is not None:
                protocols.append(protocol)

    return protocols

def load_protocool_from_xml(file_path: str) -> ProtocolDefinition:
    """Load protocol from xml"""

    tree = ET.parse(file_path)
    root = tree.getroot()
    if root.tag != 'Protocol':
        return None
    
    protocol = ProtocolDefinition(
        machine_code=root.attrib.get('machine_code'),
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
                    allow_multiple_values=field_elem.find('Values').attrib.get('allow_multiple_values') == 'true' if field_elem.find('Values') is not None else None
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
            count_field_elem = dce_elem.find('CountField')
            if count_field_elem is not None:
                count_field = {
                    'field_id_ref': count_field_elem.attrib.get('field_id_ref')
                }
                dce_layer['count_field'] = count_field
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
            parameters=parameters if len(parameters) > 0 else None
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