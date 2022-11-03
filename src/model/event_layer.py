
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
