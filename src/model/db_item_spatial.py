import sqlite3

from qgis.core import QgsVectorLayer

from .db_item import DBItem


class DBItemSpatial(DBItem):
    """
    Represents a spatial database item with support for spatial views in a GeoPackage.
    """

    def __init__(self, db_table_name: str, id: int, name: str, fc_name: str, fc_id_column_name: str, geom_type: str, epsg: int = 4326, metadata: dict = None):
        """
        Initialize a spatial DB item.

        Args:
            db_table_name: Name of the database table.
            id: Unique identifier for the item.
            name: Display name.
            fc_name: Feature class name.
            fc_id_column_name: ID column name in the feature class.
            geom_type: Geometry type (e.g., 'Polygon').
            epsg: EPSG code for the spatial reference system.
            metadata: Optional metadata dictionary.
        """
        super().__init__(db_table_name, id, name, metadata)

        self.fc_name: str = fc_name
        self.fc_id_column_name: str = fc_id_column_name
        self.epsg: int = epsg
        self.geom_type: str = geom_type

        self.view_name: str = f'vw_{self.db_table_name}_{self.id}'

    def get_layer_path(self, db_path: str) -> str:
        """Get the data source path for the spatial layer."""
        return f'{db_path}|layername={self.fc_name}'

    def get_temp_layer(self, db_path: str) -> QgsVectorLayer:
        """Get a temporary layer for the spatial item."""
        return QgsVectorLayer(f'{db_path}|layername={self.fc_name}|subset={self.fc_id_column_name} = {self.id}', 'temp', 'ogr')

    def feature_count(self, db_path: str) -> int:
        """Get the feature count for the spatial item."""
        temp_layer = self.get_temp_layer(db_path)
        return temp_layer.featureCount()

    def check_spatial_view_exists(self, curs: sqlite3.Cursor) -> bool:
        """Check if the spatial view exists."""
        curs.execute(f"SELECT name FROM sqlite_master WHERE type='view' AND name='{self.view_name}'")
        return curs.fetchone() is not None

    def create_spatial_view(self, curs: sqlite3.Cursor) -> None:
        """Create a spatial view of the DB item features."""
        sql = f"CREATE VIEW {self.view_name} AS SELECT * FROM {self.fc_name} WHERE {self.fc_id_column_name} == {self.id}"
            # check if the view already exists, if so, delete it
        if self.check_spatial_view_exists(curs):
            curs.execute(f"DROP VIEW {self.view_name}")
            curs.execute(f"DELETE FROM gpkg_contents WHERE table_name = '{self.view_name}'")
            curs.execute(f"DELETE FROM gpkg_geometry_columns WHERE table_name = '{self.view_name}'")
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
    
    def drop_spatial_view(self, curs: sqlite3.Cursor) -> None:
        """Drop the spatial view of the DB item features."""
        curs.execute(f"DROP VIEW IF EXISTS {self.view_name}")
        curs.execute(f"DELETE FROM gpkg_contents WHERE table_name = ?", (self.view_name,))
        curs.execute(f"DELETE FROM gpkg_geometry_columns WHERE table_name = ?", (self.view_name,))