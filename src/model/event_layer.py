
from .layer import Layer
from .db_item import DBItem


class EventLayer(DBItem):
    """
    Simply class that represents a layer used within a data capture event.
    Note the absence of protocol! This class is intended to be used for each
    unique layer within an event (across multiple protocols if needed).

    Note the ID passed in is the EVENT ID!!!!!! that can be used to retrieve
    the event to which this event layer belongs. The layer property can be
    used to get all the information needed to add this even layer to the map."""

    def __init__(self, event_id, layer: Layer) -> None:
        super().__init__('None', event_id, layer.name)
        self.layer = layer
        self.icon = 'layer'
