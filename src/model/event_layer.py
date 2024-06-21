
from qgis.core import QgsVectorLayer

from .layer import Layer
from .db_item import DBItem


class EventLayer(DBItem):
    """
    Simple class that represents a layer used within a data capture event.
    Note the absence of protocol or method! This class is intended to be
    used for each unique layer within an event (across multiple protocols
    and methods if needed)."""

    def __init__(self, id, event_id, layer: Layer) -> None:
        super().__init__('event_layers', id, layer.name)
        self.event_id = event_id
        self.layer = layer
        self.icon = 'layer'

        if self.layer.geom_type == 'Point':
            self.icon = 'point'
        elif self.layer.geom_type == 'Linestring':
            self.icon = 'line'
        elif self.layer.geom_type == 'Polygon':
            self.icon = 'polygon'
        
        self.menu_items = None
        if self.layer.metadata is not None:
            if 'menu_items' in self.layer.metadata:
                self.menu_items = self.layer.metadata['menu_items']

    def feature_count(self, db_path: str) -> int:
        fc_name = Layer.DCE_LAYER_NAMES[self.layer.geom_type]
        temp_layer = QgsVectorLayer(f'{db_path}|layername={fc_name}|subset=event_layer_id = {self.layer.id} AND event_id = {self.event_id}', 'temp', 'ogr')
        return temp_layer.featureCount()