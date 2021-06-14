import os
import sys
import tempfile

from qgis.core import (
    QgsApplication,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsField,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsExpression,
    QgsVectorFileWriter,
    QgsVectorDataProvider,
    edit)
from PyQt5.QtGui import *
from qgis.PyQt.QtCore import QVariant
from qgis.analysis import QgsNativeAlgorithms

# Initialize QGIS Application
import processing
from processing.core.Processing import Processing
Processing.initialize()
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

# ---- processing tool parameters ----
# simplify tolerance
# use 0.00008 for most 1m LiDAR
# try 0.0001 for 10 m elevation data
simplify_tolerance = 0.00005

# smoothing parameter
# use from 0.25 to 0.5. Use higher value for 10 m DEM
smoothing_offset = 0.1

# small polygon removal area in meters
# generally been using 9 meters as a cutoff to remove small islands
polygon_min_size = 9


def raster_to_polygon(raster_path, out_gpkg, out_layer_name, raster_value, surface_name='valley bottom'):

    #raster_layer = QgsRasterLayer(raster_path, 'in_raster')
    out_polygon_path = os.path.join(out_gpkg, out_layer_name)

    # --------- PROCESSING -------------

    # -- DEM --
    tempdir = tempfile.TemporaryDirectory()
    temp_raster = os.path.join(tempdir.name, "less_than.tif")

    gp_calc = processing.run('gdal:rastercalculator', {'INPUT_A': raster_path,
                                                       'BAND_A': 1,
                                                       'FORMULA': f'(A <= {raster_value})',
                                                       'OUTPUT': temp_raster})  # 'raster'})

    #raster_lessthan = gp_calc['OUTPUT']

    raster_lessthan = QgsRasterLayer(gp_calc['OUTPUT'])
    # -- DEM to VECTOR --

    gp_polygonize = processing.run("gdal:polygonize",
                                   {'INPUT': raster_lessthan,
                                    'BAND': 1,
                                    'FIELD': 'DN',
                                    'EIGHT_CONNECTEDNESS': False,
                                    'EXTRA': '',
                                    'OUTPUT': 'TEMPORARY_OUTPUT'})

    raw_vector_layer = QgsVectorLayer(
        gp_polygonize['OUTPUT'], "raw_polygons", "ogr")
    # -- CALCULATE AREA --

    # create a provider
    pv = raw_vector_layer.dataProvider()

    # add the attribute and update
    pv.addAttributes([QgsField('raw_area_m', QVariant.Int), QgsField(
        'max_elev_m', QVariant.Double), QgsField('surface_name', QVariant.String)])
    raw_vector_layer.updateFields()

    # Create a context and scope
    context = QgsExpressionContext()
    context.appendScopes(
        QgsExpressionContextUtils.globalProjectLayerScopes(raw_vector_layer))

    # Loop through and add the areas
    delete_features = []
    with edit(raw_vector_layer):
        # loop them
        for feature in raw_vector_layer.getFeatures():
            if feature['DN'] != 1:
                delete_features.append(feature.id())
            else:
                context.setFeature(feature)
                feature['raw_area_m'] = QgsExpression('$area').evaluate(context)
                feature['max_elev_m'] = raster_value
                feature['surface_name'] = surface_name
                raw_vector_layer.updateFeature(feature)
        result = raw_vector_layer.dataProvider().deleteFeatures(delete_features)

    # -- Simplify Polygons --
    gp_simplify = processing.run("native:simplifygeometries",
                                 {'INPUT': raw_vector_layer,
                                  'METHOD': 0,
                                  'TOLERANCE': simplify_tolerance,
                                  'OUTPUT': 'TEMPORARY_OUTPUT'})

    simp_vector_layer = gp_simplify['OUTPUT']  # QgsVectorLayer(
    # gp_simplify['OUTPUT'], "simplified_polygons", 'ogr')

    # -- Smooth the polygons --
    gp_smooth = processing.run("native:smoothgeometry",
                               {'INPUT': simp_vector_layer,
                                'ITERATIONS': 1,
                                'OFFSET': smoothing_offset,
                                'MAX_ANGLE': 180,
                                'OUTPUT': 'TEMPORARY_OUTPUT'})

    smooth_vector_layer = gp_smooth['OUTPUT']  # QgsVectorLayer(
    # , "smoothed_polygons", 'ogr')

    # Create a context and scope
    # Understand WTF this is??
    context = QgsExpressionContext()
    context.appendScopes(
        QgsExpressionContextUtils.globalProjectLayerScopes(smooth_vector_layer))

    # add an area attribute
    # create a provider
    pv = smooth_vector_layer.dataProvider()

    # add the attribute and update
    pv.addAttributes([QgsField('area_m', QVariant.Int)])
    smooth_vector_layer.updateFields()

    # Loop through and add the areas
    with edit(smooth_vector_layer):
        # loop them
        for feature in smooth_vector_layer.getFeatures():
            context.setFeature(feature)
            feature['area_m'] = QgsExpression('$area').evaluate(context)
            smooth_vector_layer.updateFeature(feature)

    # -- Do a quick geometry fix for twisted polygons --

    gp_fix = processing.run("native:fixgeometries",
                            {'INPUT': smooth_vector_layer,
                             'OUTPUT': 'TEMPORARY_OUTPUT'})

    fixed_vector_layer = gp_fix['OUTPUT']  # QgsVectorLayer(
    # gp_fix['OUTPUT'], "fixed_polygons", 'ogr')

    # Open the fixed vector

    # -- Copy the vector to outputs directory
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.layerName = out_layer_name
    options.driverName = 'GPKG'
    if os.path.exists(out_gpkg):
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    QgsVectorFileWriter.writeAsVectorFormat(
        fixed_vector_layer, out_gpkg, options)

    # open the output layer
    output_vector_layer = QgsVectorLayer(
        out_polygon_path, out_layer_name, 'ogr')

    # -- Delete Unneeded Fields --
    pv = output_vector_layer.dataProvider()
    pv.deleteAttributes([1, 2])
    output_vector_layer.updateFields()

    # -- Delete small polygons --
    # data provider capabilities
    caps = output_vector_layer.dataProvider().capabilities()

    # features and empty list of features to delete
    features = output_vector_layer.getFeatures()
    delete_features = []

    # if the layer can have deleted features
    if caps & QgsVectorDataProvider.DeleteFeatures:
        for feature in features:
            if feature['area_m'] <= polygon_min_size:
                delete_features.append(feature.id())
        result = output_vector_layer.dataProvider().deleteFeatures(delete_features)
        # output_vector_layer.triggerRepaint()
