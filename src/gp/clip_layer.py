import os
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

from qgis import processing
# TODO figure out processing imports
# I would like to remove this
from processing.core.Processing import Processing
Processing.initialize()
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())


def raster_to_polygon(raw_layer):
    p_clip = processing.run("native:clip",
                            {'INPUT': raw_layer,
                             'OVERLAY': raw_layer,
                             'OUTPUT': 'TEMPORARY_OUTPUT'})

    clipped_veronis = p_clipped_veronis['OUTPUT']
    clipped_veronis.setName('clipped_veronis')
    riverscape_node.addLayer(clipped_veronis)
