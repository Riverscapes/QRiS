"""
Centerline geoprocessing task using QgsGeometry
"""

from qgis.core import QgsApplication, QgsTask, QgsMessageLog, Qgis, QgsGeometry, QgsMultiPoint, QgsLineString, QgsMultiLineString, QgsPolygon, QgsMultiPolygon, QgsPointXY, QgsPoint
from qgis.PyQt.QtCore import pyqtSignal


MESSAGE_CATEGORY = 'CenterlineTask'


class CenterlineTask(QgsTask):

    centerline_complete = pyqtSignal(str)

    def __init__(self, in_polygon: QgsGeometry, start_clipline: QgsLineString, end_clipline: QgsLineString) -> None:
        super().__init__('Generate Centerline Task', QgsTask.CanCancel)

        self.in_polygon = in_polygon
        self.start_clipline = start_clipline
        self.end_clipline = end_clipline
        self.centerline = None

    def run(self):
        """Here you implement your heavy lifting.
        Should periodically test for isCanceled() to gracefully
        abort.
        This method MUST return True or False.
        Raising exceptions will crash QGIS, so we handle them
        internally and raise them in self.finished
        """

        # TODO Densify vertex option
        polygon_dense = QgsGeometry(self.in_polygon)  # Deep copy of polygon
        start_clipline = self.start_clipline
        end_clipline = self.end_clipline

        # geom_lines = [QgsGeometry(line) for line in [start_clipline, end_clipline]]
        # inside_lines = [line.intersection(self.in_polygon) for line in geom_lines]
        midpoint_start = QgsGeometry(start_clipline.interpolatePoint(start_clipline.length() / 2))
        midpoint_end = QgsGeometry(end_clipline.interpolatePoint(end_clipline.length() / 2))
        midpoint_start_buffer = midpoint_start.buffer(0.00001, 4)
        midpoint_end_buffer = midpoint_end.buffer(0.00001, 4)

        # Find the central polygon by clipping the start and end lines
        result0 = polygon_dense.splitGeometry([QgsPointXY(start_clipline.startPoint()), QgsPointXY(start_clipline.endPoint())], True)
        result1 = polygon_dense.splitGeometry([QgsPointXY(end_clipline.startPoint()), QgsPointXY(end_clipline.endPoint())], True)

        test_polygons = [result0[1][0], result1[1][0], polygon_dense]

        central_polygon = QgsGeometry(list(geom_polygon for geom_polygon in test_polygons if geom_polygon.intersects(midpoint_start_buffer) and geom_polygon.intersects(midpoint_end_buffer))[0])

        # Build Voronoi from clipped polygon
        voronoi = central_polygon.voronoiDiagram()
        l_vor_polys = [QgsGeometry(poly) for poly in voronoi.parts()]

        # Split to L and R by selecting line segments of polygon not touching midpoint of split lines
        coords = central_polygon.asPolygon()[0]
        segments = list(QgsGeometry(line) for line in list(map(QgsLineString, zip(coords[:-1], coords[1:]))))
        segments0 = [segment for segment in segments if midpoint_start_buffer.disjoint(segment)]
        segments1 = [segment for segment in segments0 if midpoint_end_buffer.disjoint(segment)]
        m_segments = QgsGeometry.fromMultiPolylineXY([segment.asPolyline() for segment in segments1])
        clean = m_segments.mergeLines()

        # Select Voronoi Polygons by Side
        side_polys = []
        for side_line in clean.parts():
            mpnts = QgsGeometry.fromMultiPointXY(QgsPointXY(pnt) for pnt in side_line.points())
            intersected_polys = [poly for poly in l_vor_polys if poly.intersects(mpnts)]
            mpolys = QgsGeometry.unaryUnion(intersected_polys)
            side_polys.append(mpolys)

        # Intersect to find the centerline
        m_centerline_raw = side_polys[0].intersection(side_polys[1])
        centerline_raw = QgsGeometry.mergeLines(m_centerline_raw)
        centerline_out = centerline_raw.intersection(self.in_polygon)
        self.centerline = QgsGeometry(centerline_out)

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
                'CenterlineTask completed\n',
                MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Centerline not successful but without '
                    'exception (probably the task was manually '
                    'canceled by the user)'.format(
                        name=self.description()),
                    MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(
                    f'Generate Centerline Exception: {self.exception}',
                    MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

        self.centerline_complete.emit(QgsGeometry(self.centerline))

    def cancel(self):
        QgsMessageLog.logMessage(
            f'Centerline Tool was canceled',
            MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
