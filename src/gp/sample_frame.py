from PyQt5.QtGui import *
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import QgsApplication, QgsTask, QgsMessageLog, Qgis, QgsVectorLayer, QgsFeature, QgsProject, QgsCoordinateTransform
from qgis.analysis import QgsNativeAlgorithms

# Initialize QGIS Application
from qgis import processing
# TODO figure out processing imports
from processing.core.Processing import Processing
Processing.initialize()
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())


MESSAGE_CATEGORY = 'SampleFrameTask'


class SampleFrameTask(QgsTask):

    sample_frame_complete = pyqtSignal(bool)

    def __init__(self, polygon: QgsVectorLayer, cross_sections: QgsVectorLayer, out_path: str, id: int) -> None:
        super().__init__('Generate Sample Frames Task', QgsTask.CanCancel)

        self.polygon_layer = polygon
        self.cross_sections_layer = cross_sections
        self.id = id
        self.sample_frame = out_path

    def run(self):
        """Here you implement your heavy lifting.
        Should periodically test for isCanceled() to gracefully
        abort.
        This method MUST return True or False.
        Raising exceptions will crash QGIS, so we handle them
        internally and raise them in self.finished
        """

        extend_params = {
            'INPUT': self.cross_sections_layer,
            'START_DISTANCE': 0.000001,
            'END_DISTANCE': 0.000001,
            'OUTPUT': "TEMPORARY_OUTPUT"
        }
        gp_extend = processing.run('native:extendlines', extend_params)

        split_params = {
            'INPUT': self.polygon_layer,
            'LINES': gp_extend['OUTPUT'],
            'OUTPUT': "TEMPORARY_OUTPUT"
        }
        gp_split = processing.run('qgis:splitwithlines', split_params)

        out_layer = QgsVectorLayer(self.sample_frame)
        transform = QgsCoordinateTransform(self.polygon_layer.crs(), out_layer.crs(), QgsProject.instance())

        for i, feat in enumerate(gp_split['OUTPUT'].getFeatures(), 1):
            geom = feat.geometry()
            geom.transform(transform)
            out_feature = QgsFeature()
            out_feature.setFields(out_layer.fields())
            out_feature.setGeometry(geom)
            out_feature['mask_id'] = self.id
            out_feature['display_label'] = str(i)
            out_layer.dataProvider().addFeature(out_feature)
        out_layer.commitChanges()

        return True

    def finished(self, result):
        """
        This function is automatically called when the task has
        completed (successfully or not).
        You implement finished() to do whatever follow-up stuff
        should happen after the task is complete.
        finished is always called from the main thread, so it's safe
        to do GUI operations and raise Python exceptions here.
        result is the return value from self.run.
        """

        if result:
            QgsMessageLog.logMessage(
                'Sample Frame completed',
                MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Sample Frame not successful but without '
                    'exception (probably the task was manually '
                    'canceled by the user)'.format(
                        name=self.description()),
                    MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(
                    f'Generate Sample Frame Exception: {self.exception}',
                    MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

        self.sample_frame_complete.emit(result)
        self.cancel()

    def cancel(self):
        QgsMessageLog.logMessage(
            f'Sample Frame Tool was canceled',
            MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
