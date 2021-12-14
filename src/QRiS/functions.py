import os
# from typing_extensions import ParamSpecKwargs

from qgis.core import (
    QgsField,
    QgsVectorLayer,
    QgsVectorFileWriter
)


def create_geopackage_table(geometry_type, table_name, geopackage_path, full_path, field_tuple_list):
    """
        Creates tables in existing or new geopackages
        geometry_type (string):  NoGeometry, Polygon, Linestring, Point, etc...
        table_name (string): Name for the new table
        geopackage_path (string): full path to the geopackage i.e., dir/package.gpkg
        full_path (string): full path including the layer i.e., dir/package.gpkg|layername=layer
        field_tuple_list (list): a list of tuples as field name and QVariant field types i.e., [('my_field', QVarient.Double)]
        """
    memory_layer = QgsVectorLayer(geometry_type, "memory_layer", "memory")
    fields = []
    for field_tuple in field_tuple_list:
        field = QgsField(field_tuple[0], field_tuple[1])
        fields.append(field)
    memory_layer.dataProvider().addAttributes(fields)
    memory_layer.updateFields()
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.layerName = table_name
    options.driverName = 'GPKG'
    if os.path.exists(geopackage_path):
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    QgsVectorFileWriter.writeAsVectorFormat(memory_layer, geopackage_path, options)
