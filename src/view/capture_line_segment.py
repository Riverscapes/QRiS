"""
"""
from PyQt5.QtCore import Qt

from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import Qgis, QgsWkbTypes, QgsPoint, QgsLineString
from qgis.gui import QgsMapToolEmitPoint, QgsMapTool, QgsRubberBand


class LineSegmentMapTool(QgsMapToolEmitPoint):

    line_captured = pyqtSignal(QgsLineString)

    def __init__(self, canvas):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.rubberBand = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.rubberBand.setColor(Qt.red)
        self.rubberBand.setWidth(1)
        self.reset()
        self.line = None

    def reset(self):
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.rubberBand.reset(QgsWkbTypes.LineGeometry)

    def canvasPressEvent(self, e):
        self.startPoint = self.toMapCoordinates(e.pos())
        self.endPoint = self.startPoint
        self.isEmittingPoint = True
        self.showLine(self.startPoint, self.endPoint)

    def canvasReleaseEvent(self, e):
        self.isEmittingPoint = False
        r = self.linestring()
        if r is not None:
            self.line_captured.emit(r)
            self.deactivate()

    def canvasMoveEvent(self, e):
        if not self.isEmittingPoint:
            return

        self.endPoint = self.toMapCoordinates(e.pos())
        self.showLine(self.startPoint, self.endPoint)

    def showLine(self, startPoint, endPoint):
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        if startPoint.x() == endPoint.x() or startPoint.y() == endPoint.y():
            return

        # point1 = QgsPoint(startPoint.x(), startPoint.y())
        # point2 = QgsPoint(startPoint.x(), endPoint.y())
        # point3 = QgsPoint(endPoint.x(), endPoint.y())
        # point4 = QgsPoint(endPoint.x(), startPoint.y())
        self.rubberBand.addPoint(startPoint, False)
        self.rubberBand.addPoint(endPoint, True)
        # self.rubberBand.addPoint(point1, False)
        # self.rubberBand.addPoint(point2, False)
        # self.rubberBand.addPoint(point3, False)
        # self.rubberBand.addPoint(point4, True)    # true to update canvas
        self.rubberBand.show()

    def linestring(self):
        if self.startPoint is None or self.endPoint is None:
            return None
        elif (self.startPoint.x() == self.endPoint.x() or
              self.startPoint.y() == self.endPoint.y()):
            return None

        return QgsLineString([self.startPoint, self.endPoint])

    def deactivate(self):
        self.rubberBand.reset()
        QgsMapTool.deactivate(self)
        self.deactivated.emit()
