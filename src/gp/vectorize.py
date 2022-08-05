import os
import sys
import tempfile

from qgis.core import (
    QgsProject,
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
from qgis import processing
# TODO figure out processing imports
from processing.core.Processing import Processing
Processing.initialize()
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

# ---- processing tool parameters ----
# simplify tolerance
# use 0.00008 for most 1m LiDAR
# try 0.0001 for 10 m elevation data
simplify_tolerance = 0.00008

# smoothing parameter
# use from 0.25 to 0.5. Use higher value for 10 m DEM
smoothing_offset = 0.25

# small polygon removal area in meters
# generally been using 9 meters as a cutoff to remove small islands
polygon_min_size = 9


def raster_to_polygon(raster_path, out_gpkg, out_layer_name, raster_value, surface_name='valley bottom'):

    # raster_layer = QgsRasterLayer(raster_path, 'in_raster')
    out_polygon_path = os.path.join(out_gpkg, out_layer_name)

    # --------- PROCESSING -------------

    # -- DEM --
    tempdir = tempfile.TemporaryDirectory()
    temp_raster = os.path.join(tempdir.name, "less_than.tif")

    gp_calc = processing.run('gdal:rastercalculator', {'INPUT_A': raster_path,
                                                       'BAND_A': 1,
                                                       'FORMULA': f'(A <= {raster_value})',
                                                       'OUTPUT': temp_raster})  # 'raster'})

    # raster_less_than = gp_calc['OUTPUT']

    raster_less_than = QgsRasterLayer(gp_calc['OUTPUT'])

    # -- DEM to VECTOR --
    gp_raw = processing.run("gdal:polygonize",
                            {'INPUT': raster_less_than,
                             'BAND': 1,
                             'FIELD': 'DN',
                             'EIGHT_CONNECTEDNESS': False,
                             'EXTRA': '',
                             'OUTPUT': 'TEMPORARY_OUTPUT'})

    raw_vector = QgsVectorLayer(
        gp_raw['OUTPUT'], "raw_vectors", "ogr")

    # TODO remove when done
    # QgsProject.instance().addMapLayer(raw_vector)

    # -- CALCULATE AREA --
    # create a provider
    pv = raw_vector.dataProvider()

    # add the attribute and update
    pv.addAttributes([QgsField('raw_area_m', QVariant.Int), QgsField(
        'max_elev_m', QVariant.Double), QgsField('surface_name', QVariant.String)])
    raw_vector.updateFields()

    # Create a context and scope
    context = QgsExpressionContext()
    context.appendScopes(
        QgsExpressionContextUtils.globalProjectLayerScopes(raw_vector))

    # Loop through and add the areas
    delete_features = []
    with edit(raw_vector):
        # loop them
        for feature in raw_vector.getFeatures():
            if feature['DN'] != 1:
                delete_features.append(feature.id())
            else:
                context.setFeature(feature)
                feature['raw_area_m'] = QgsExpression('$area').evaluate(context)
                feature['max_elev_m'] = raster_value
                feature['surface_name'] = surface_name
                raw_vector.updateFeature(feature)
        raw_vector.dataProvider().deleteFeatures(delete_features)

    # -- BUFFER POLYGONS --
    gp_buffered = processing.run("native:buffer",
                                 {'INPUT': raw_vector,
                                  'DISTANCE': 0.000001,
                                  'SEGMENTS': 5,
                                  'END_CAP_STYLE': 0,
                                  'JOIN_STYLE': 0,
                                  'MITER_LIMIT': 2,
                                  'DISSOLVE': False,
                                  'OUTPUT': 'TEMPORARY_OUTPUT'})

    buffered_vector = gp_buffered['OUTPUT']

    # TODO remove when final
    # QgsProject.instance().addMapLayer(buffered_vector)

    # -- Simplify Polygons --
    gp_simple = processing.run("native:simplifygeometries",
                               {'INPUT': buffered_vector,
                                'METHOD': 0,
                                'TOLERANCE': simplify_tolerance,
                                'OUTPUT': 'TEMPORARY_OUTPUT'})

    simple_vector = gp_simple['OUTPUT']  # QgsVectorLayer(
    # gp_simplify['OUTPUT'], "simplified_polygons", 'ogr')

    # -- Smooth the polygons --
    gp_smooth = processing.run("native:smoothgeometry",
                               {'INPUT': simple_vector,
                                'ITERATIONS': 1,
                                'OFFSET': smoothing_offset,
                                'MAX_ANGLE': 180,
                                'OUTPUT': 'TEMPORARY_OUTPUT'})

    smooth_vector = gp_smooth['OUTPUT']  # QgsVectorLayer(
    # , "smoothed_polygons", 'ogr')

    gp_multi = processing.run("native:multiparttosingleparts",
                              {'INPUT': smooth_vector,
                               'OUTPUT': 'TEMPORARY_OUTPUT'})

    multi_vector = gp_multi['OUTPUT']

    # Fix any crossed geometry as final vector
    gp_fix = processing.run("native:fixgeometries",
                            {'INPUT': multi_vector,
                             'OUTPUT': 'TEMPORARY_OUTPUT'})

    final_vector = gp_fix['OUTPUT']

    # Create a context and scope
    # Understand WTF this is??
    context = QgsExpressionContext()
    context.appendScopes(
        QgsExpressionContextUtils.globalProjectLayerScopes(final_vector))

    # add an area attribute
    # create a provider
    pv = final_vector.dataProvider()

    # add the attribute and update
    pv.addAttributes([QgsField('area_m', QVariant.Int)])
    final_vector.updateFields()

    # Loop through and add the areas
    with edit(final_vector):
        # loop them
        for feature in final_vector.getFeatures():
            context.setFeature(feature)
            feature['area_m'] = QgsExpression('$area').evaluate(context)
            final_vector.updateFeature(feature)

    # -- Delete Unneeded Fields --
    pv = final_vector.dataProvider()
    pv.deleteAttributes([1, 2])
    final_vector.updateFields()

    # -- Delete small polygons --
    # data provider capabilities
    caps = final_vector.dataProvider().capabilities()

    # features and empty list of features to delete
    features = final_vector.getFeatures()
    delete_features = []

    # if the layer can have deleted features
    if caps & QgsVectorDataProvider.DeleteFeatures:
        for feature in features:
            if feature['area_m'] <= polygon_min_size:
                delete_features.append(feature.id())
        final_vector.dataProvider().deleteFeatures(delete_features)

    # TODO fix final data export
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.layerName = out_layer_name
    options.driverName = 'GPKG'
    if os.path.exists(out_gpkg):
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    QgsVectorFileWriter.writeAsVectorFormatV2(
        final_vector, out_gpkg, options)

    # open the output layer
    QgsVectorLayer(out_polygon_path, out_layer_name, 'ogr')
