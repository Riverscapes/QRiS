
from .layer import Layer
from .db_item import DBItem


class EventLayer(DBItem):
    def __init__(self, event_id, layer: Layer) -> None:
        super().__init__('None', event_id, layer.name)
        self.layer = layer
