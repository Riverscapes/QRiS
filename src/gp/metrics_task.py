import os
import json
import datetime
from qgis.core import QgsTask, QgsMessageLog, Qgis, QgsProject, QgsVectorLayer, QgsRasterLayer
from qgis.PyQt.QtCore import pyqtSignal

from ..model.project import Project
from ..model.mask import Mask, AOI_MASK_TYPE_ID
from .metrics import Metrics
from ..model.raster import SURFACES_PARENT_FOLDER
from ..QRiS.qris_map_manager import QRisMapManager

import webbrowser

MESSAGE_CATEGORY = 'QRiS Metrics Task'


class MetricsTask(QgsTask):
    """
    https://docs.qgis.org/3.22/en/docs/pyqgis_developer_cookbook/tasks.html
    """

    # Signal to notify when done and return the PourPoint and whether it should be added to the map
    on_complete = pyqtSignal(bool, Mask, dict or None, dict or None)

    def __init__(self, project: Project, mask: Mask):
        super().__init__(MESSAGE_CATEGORY, QgsTask.CanCancel)

        self.polygons = {}
        self.data = {}

        mask_guid = f'QRiS::{project.map_guid}::{mask.db_table_name}::{mask.id}'

        self.map_layers = []
        for layer in QgsProject.instance().mapLayers().values():
            layer_node = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
            if layer_node.itemVisibilityChecked():

                # Skip the mask being used to summarize layers
                prop = layer_node.customProperty('QRiS')
                if prop is not None and isinstance(mask, Mask) and prop == mask_guid:
                    continue

                layer_def = {'name': layer.name(), 'url': layer.dataProvider().dataSourceUri()}
                if isinstance(layer, QgsRasterLayer):
                    layer_def['type'] = 'raster'
                    self.map_layers.append(layer_def)
                elif isinstance(layer, QgsVectorLayer):
                    if layer.featureCount() > 0:
                        layer_def['type'] = 'vector'
                        self.map_layers.append(layer_def)

        self.project = project
        self.mask = mask
        self.config = {}
        mask_layer = 'aoi_features' if self.mask.mask_type.id == AOI_MASK_TYPE_ID else 'mask_features'
        self.metrics = Metrics(project.project_file, mask, self.map_layers, mask_layer)

    def run(self):
        """
        Originally intended to use this VectorTranslate method
        https://gdal.org/development/rfc/rfc59.1_utilities_as_a_library.html#swig-bindings-python-java-c-perl-changes

        But ended up using this ogr method
        https://subscription.packtpub.com/book/application-development/9781787124837/3/ch03lvl1sec58/exporting-a-layer-to-the-geopackage-format
        """
        try:
            self.data = self.metrics.run()
            self.polygons = self.metrics.polygons

        except Exception as ex:
            self.exception = ex
            return False

        return True

    def finished(self, result: bool):
        """
        This function is automatically called when the task has completed (successfully or not).
        You implement finished() to do whatever follow-up stuff should happen after the task is complete.
        finished is always called from the main thread, so it's safe to do GUI operations and raise Python exceptions here.
        result is the return value from self.run.
        """

        if result:
            QgsMessageLog.logMessage('Metrics Complete', MESSAGE_CATEGORY, Qgis.Success)

            # base_name = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            # output_json = os.path.join(os.path.dirname(self.project.project_file), SURFACES_PARENT_FOLDER, f'geospatial_metric_summary_{base_name}.json')
            # with open(output_json, 'w') as f:
            #     json.dump(self.data, f, indent=4)
            # webbrowser.open('file://' + output_json)

        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Geospatial Metrics unsuccessful but without exception (probably the task was canceled by the user)', MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(f'Geospatial metrics exception: {self.exception}', MESSAGE_CATEGORY, Qgis.Critical)
                # raise self.exception

        self.on_complete.emit(result, self.mask, self.polygons, self.data)

    def cancel(self):
        QgsMessageLog.logMessage(
            'Geospatial Metrics was canceled'.format(name=self.description()), MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
