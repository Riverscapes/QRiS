import sqlite3


from qgis.core import QgsVectorLayer

from .layer import Layer
from .db_item import DBItem
from .db_item_spatial import DBItemSpatial


class EventLayer(DBItemSpatial):
    """
    Simple class that represents a layer used within a data capture event.
    Note the absence of protocol or method! This class is intended to be
    used for each unique layer within an event (across multiple protocols
    and methods if needed)."""

    def __init__(self, id, event_id, layer: Layer) -> None:
        super().__init__('event_layers', id, layer.name, layer.DCE_LAYER_NAMES[layer.geom_type], 'event_layer_id', layer.geom_type)
        self.event_id = event_id
        self.layer = layer
        self.icon = 'layer'

        self.view_name = f'vw_{self.layer.layer_id}_{self.event_id}'

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
        temp_layer = QgsVectorLayer(f'{db_path}|layername={self.fc_name}|subset=event_layer_id = {self.layer.id} AND event_id = {self.event_id}', 'temp', 'ogr')
        return temp_layer.featureCount()

    def create_spatial_view(self, db_path: str):
        
        try:
            layer_fields: list = self.layer.metadata.get('fields', None)
            out_fields = '*'
            if layer_fields is not None and len(layer_fields) > 0:
                out_fields = ", ".join([f"json_extract(metadata, '$.attributes.{field['id']}') AS \"{field['label']}\"" for field in layer_fields])
            
            sql = f"CREATE VIEW {self.view_name} AS SELECT fid, geom, event_id, event_layer_id, {out_fields}, metadata FROM {self.fc_name} WHERE event_id == {self.event_id} AND event_layer_id == {self.layer.id}"
            with sqlite3.connect(db_path) as conn:
                curs = conn.cursor()
                # check if the view already exists, if so, delete it
                if self.check_spatial_view_exists(db_path):
                    curs.execute(f"DROP VIEW {self.view_name}")
                    curs.execute(f"DELETE FROM gpkg_contents WHERE table_name = '{self.view_name}'")
                    curs.execute(f"DELETE FROM gpkg_geometry_columns WHERE table_name = '{self.view_name}'")

                curs.execute(sql)
                # add view to geopackage
                sql = "INSERT INTO gpkg_contents (table_name, data_type, identifier, description, srs_id) VALUES (?, ?, ?, ?, ?)"
                curs.execute(sql, [self.view_name, "features", self.view_name, "", self.epsg])
                sql = "INSERT INTO gpkg_geometry_columns (table_name, column_name, geometry_type_name, srs_id, z, m) VALUES (?, ?, ?, ?, ?, ?)"
                curs.execute(sql, [self.view_name, 'geom', self.geom_type.upper(), self.epsg, 0, 0])
                conn.commit()
        
        except Exception as ex:
            conn.rollback()
            raise ex

    def delete_event_layer_features(self, db_path: str) -> None:
        """
        Deletes all features in the event layer.
        """
        fc_name = Layer.DCE_LAYER_NAMES[self.layer.geom_type]
        temp_layer = QgsVectorLayer(f'{db_path}|layername={fc_name}|subset=event_layer_id = {self.layer.id} AND event_id = {self.event_id}', 'temp', 'ogr')
        temp_layer.startEditing()
        for feat in temp_layer.getFeatures():
            temp_layer.deleteFeature(feat.id())
        temp_layer.commitChanges()