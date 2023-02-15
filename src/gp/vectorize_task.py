import os

from qgis.core import (
    QgsApplication,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsField,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsExpression, QgsCoordinateTransformContext,
    QgsVectorFileWriter,
    QgsVectorDataProvider, QgsTask, QgsMessageLog, Qgis,
    edit)
from PyQt5.QtGui import *
from qgis.PyQt.QtCore import QVariant, pyqtSignal
from qgis.analysis import QgsNativeAlgorithms

Path = str

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
#simplify_tolerance = 0.00008

# smoothing parameter
# use from 0.25 to 0.5. Use higher value for 10 m DEM
#smoothing_offset = 0.25

# small polygon removal area in meters
# generally been using 9 meters as a cutoff to remove small islands
#polygon_min_size = 9

Path = str

MESSAGE_CATEGORY = 'QRiS_VectorizeClassTask'


class VectorizeTask(QgsTask):
    """
    https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/tasks.html
    """

    # Signal to notify when done and return the PourPoint and whether it should be added to the map
    on_complete = pyqtSignal(bool)

    def __init__(self, raster_path: Path, out_gpkg: Path, out_layer_name: str, raster_value: float, simplify_tolerance: float = 0.00008, smoothing_offset: float = 0.25, polygon_min_size: float = 9.0, inverse: bool = False):
        super().__init__(f'Vectorize Task', QgsTask.CanCancel)

        self.raster_path = raster_path
        self.out_gpkg = out_gpkg
        self.out_layer_name = out_layer_name
        self.raster_value = raster_value
        self.simplify_tolerance = simplify_tolerance
        self.smoothing_offset = smoothing_offset
        self.polygon_min_size = polygon_min_size
        self.inverse = inverse

    def run(self):
        """
        Vectorize
        """
        try:
            # --------- PROCESSING -------------
            raster_layer = QgsRasterLayer(self.raster_path)
            ref_crs = raster_layer.crs()

            surface_name = os.path.splitext(os.path.basename(self.raster_path))[0]
            threshold_type = '<=' if self.inverse is False else '>='

            gp_calc = processing.run('gdal:rastercalculator', {'INPUT_A': self.raster_path,
                                                               'BAND_A': 1,
                                                               'FORMULA': f'(A {threshold_type} {self.raster_value})',
                                                               'OUTPUT': 'TEMPORARY_OUTPUT'})

            thresholded_raster = QgsRasterLayer(gp_calc['OUTPUT'])

            # -- DEM to VECTOR --
            gp_raw = processing.run("gdal:polygonize",
                                    {'INPUT': thresholded_raster,
                                     'BAND': 1,
                                     'FIELD': 'DN',
                                     'EIGHT_CONNECTEDNESS': False,
                                     'EXTRA': '',
                                     'OUTPUT': 'TEMPORARY_OUTPUT'})

            raw_vector = QgsVectorLayer(
                gp_raw['OUTPUT'], "raw_vectors", "ogr")

            # -- CALCULATE AREA --
            # create a provider
            pv = raw_vector.dataProvider()

            # add the attribute and update
            pv.addAttributes([QgsField('raw_area_m', QVariant.Double),
                              QgsField('max_elev_m', QVariant.Double),
                              QgsField('surface_name', QVariant.String)])
            raw_vector.updateFields()

            # Create a context and scope
            context = QgsExpressionContext()
            context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(raw_vector))

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
                        feature['max_elev_m'] = self.raster_value
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

            # -- Simplify Polygons --
            gp_simple = processing.run("native:simplifygeometries",
                                       {'INPUT': buffered_vector,
                                        'METHOD': 0,
                                        'TOLERANCE': self.simplify_tolerance,
                                        'OUTPUT': 'TEMPORARY_OUTPUT'})

            simple_vector = gp_simple['OUTPUT']

            # -- Smooth the polygons --
            gp_smooth = processing.run("native:smoothgeometry",
                                       {'INPUT': simple_vector,
                                        'ITERATIONS': 1,
                                        'OFFSET': self.smoothing_offset,
                                        'MAX_ANGLE': 180,
                                        'OUTPUT': 'TEMPORARY_OUTPUT'})

            smooth_vector = gp_smooth['OUTPUT']

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
            context = QgsExpressionContext()
            context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(final_vector))

            # add an area attribute
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
                    if feature['area_m'] <= self.polygon_min_size:
                        delete_features.append(feature.id())
                final_vector.dataProvider().deleteFeatures(delete_features)

            # Export final layer
            tc = QgsCoordinateTransformContext()
            tc.addCoordinateOperation(ref_crs, ref_crs, "")

            options = QgsVectorFileWriter.SaveVectorOptions()
            options.layerName = self.out_layer_name
            options.driverName = 'GPKG'
            if os.path.exists(self.out_gpkg):
                options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
                options.EditionCapability = QgsVectorFileWriter.CanAddNewLayer
            else:
                output_dir = os.path.dirname(self.out_gpkg)
                if not os.path.isdir(output_dir):
                    os.makedirs(output_dir)
                options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
            result = QgsVectorFileWriter.writeAsVectorFormatV3(final_vector, self.out_gpkg, tc, options)

            if result[0] == QgsVectorFileWriter.NoError:
                return True
            else:
                self.exception = Exception(str(result))
                return False
        except Exception as ex:
            self.exception = ex
            return False

    def finished(self, result: bool):
        """
        This function is automatically called when the task has completed (successfully or not).
        You implement finished() to do whatever follow-up stuff should happen after the task is complete.
        finished is always called from the main thread, so it's safe to do GUI operations and raise Python exceptions here.
        result is the return value from self.run.
        """

        if result:
            QgsMessageLog.logMessage('Export Polygon from Raster Complete', MESSAGE_CATEGORY, Qgis.Success)

        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Vectorize was unsuccessful but without exception (probably the task was canceled by the user)', MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(f'Vectorize exception: {self.exception}', MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

        self.on_complete.emit(result)

    def cancel(self):
        QgsMessageLog.logMessage(
            'Vectorize polygon was canceled'.format(name=self.description()), MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
