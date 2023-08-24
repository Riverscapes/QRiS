"""
Centerline geoprocessing task using QgsGeometry
"""

from qgis.core import QgsApplication, QgsWkbTypes, QgsTask, QgsMessageLog, Qgis, QgsGeometry, QgsLineString, QgsPointXY
from qgis.PyQt.QtCore import pyqtSignal


MESSAGE_CATEGORY = 'CenterlineTask'


class CenterlineTask(QgsTask):

    centerline_complete = pyqtSignal(QgsGeometry)

    def __init__(self, in_polygon: QgsGeometry, start_clipline: QgsLineString, end_clipline: QgsLineString, densify_distance=None, islands: QgsGeometry = None) -> None:
        super().__init__('Generate Centerline Task', QgsTask.CanCancel)

        # Try to make deep copies of geometries so gui/parent changes don't cause issues?
        self.in_polygon = QgsGeometry(in_polygon)
        self.start_clipline = start_clipline.clone()
        self.end_clipline = end_clipline.clone()
        self.densify_distance = densify_distance
        self.islands = islands.clone() if islands is not None else None
        self.centerline = None

        self.exception = None

    def run(self):
        """Here you implement your heavy lifting.
        Should periodically test for isCanceled() to gracefully
        abort.
        This method MUST return True or False.
        Raising exceptions will crash QGIS, so we handle them
        internally and raise them in self.finished
        """

        start_clipline = self.start_clipline
        end_clipline = self.end_clipline

        g_startline = QgsGeometry(start_clipline.clone())
        g_endline = QgsGeometry(end_clipline.clone())

        try:
            # Get one and only one polygon if multipolygon.
            if self.in_polygon.get().wkbType() == QgsWkbTypes.MultiPolygon:
                for part in self.in_polygon.get().parts():  # what if more than one part intersects both cliplines??
                    g_part = QgsGeometry(part.clone())
                    if g_part.intersects(g_endline) and g_part.intersects(g_startline):
                        g_single_main_poly = g_part
                        break
            else:
                g_single_main_poly = QgsGeometry(self.in_polygon)

            # Get perimeter only
            g_single_main_poly = g_single_main_poly.removeInteriorRings()

            g_inner_startline = QgsGeometry(g_startline.intersection(g_single_main_poly))
            g_inner_endline = QgsGeometry(g_endline.intersection(g_single_main_poly))

            if any(geom.isMultipart() for geom in [g_inner_endline, g_inner_startline]):
                raise Exception('Unable to find one central polygon between the clip lines. Make sure clip lines are clean across the polygon.')

            midpoint_start = QgsGeometry(g_inner_startline.get().interpolatePoint(g_inner_startline.get().length() / 2))
            midpoint_end = QgsGeometry(g_inner_endline.get().interpolatePoint(g_inner_endline.get().length() / 2))
            midpoint_start_buffer = QgsGeometry(midpoint_start.buffer(0.00001, 4))
            midpoint_end_buffer = QgsGeometry(midpoint_end.buffer(0.00001, 4))

            g_inner_startline = None
            g_inner_endline = None

            # TODO Donut Routing
            if self.densify_distance is not None:
                g_clipping_poly = QgsGeometry(g_single_main_poly.densifyByDistance(self.densify_distance))
            else:
                g_clipping_poly = QgsGeometry(g_single_main_poly)

            # Find the central polygon by clipping the start and end lines
            _result0, l_clippedpolys0, _l_test0 = g_clipping_poly.splitGeometry([QgsPointXY(start_clipline.startPoint()), QgsPointXY(start_clipline.endPoint())], True)
            g_clipped_poly0 = QgsGeometry(l_clippedpolys0[0])
            if g_clipping_poly.intersects(g_endline):
                _result1, l_clippedpolys1, _l_test1 = g_clipping_poly.splitGeometry([QgsPointXY(end_clipline.startPoint()), QgsPointXY(end_clipline.endPoint())], True)
                g_clipped_poly1 = QgsGeometry(l_clippedpolys1[0])
            else:
                _result1, l_clippedpolys1, _l_test1 = g_clipped_poly0.splitGeometry([QgsPointXY(end_clipline.startPoint()), QgsPointXY(end_clipline.endPoint())], True)
                g_clipped_poly1 = QgsGeometry(l_clippedpolys1[0])

            test_polygons = [g_clipped_poly0, g_clipped_poly1, g_clipping_poly]
            l_tested_polygons = list(geom_polygon for geom_polygon in test_polygons if geom_polygon.intersects(midpoint_start_buffer) and geom_polygon.intersects(midpoint_end_buffer))
            if len(l_tested_polygons) != 1:
                raise Exception('Unable to find one central polygon between the clip lines. Make sure clip lines are clean across the polygon.')

            g_central_polygon = QgsGeometry(l_tested_polygons[0])
            g_clipped_poly0 = None
            g_clipped_poly1 = None
            g_clipping_poly = None
            test_polygons = None

            # Build Voronoi from clipped polygon
            voronoi = QgsGeometry(g_central_polygon.voronoiDiagram())
            l_vor_polys = [QgsGeometry(poly.clone()) for poly in voronoi.parts()]
            voronoi = None

            # Split to L and R by selecting line segments of polygon not touching midpoint of split lines
            coords = g_central_polygon.asPolygon()[0]
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

            clean = None

            # Intersect to find the centerline
            m_centerline_raw = side_polys[0].intersection(side_polys[1])
            centerline_raw = QgsGeometry.mergeLines(m_centerline_raw)
            g_centerline_intersected = centerline_raw.intersection(g_single_main_poly)

            # Find the main centerline after clipping the boundary
            g_centerline_out = None
            if g_centerline_intersected.isMultipart():
                for line in g_centerline_intersected.parts():
                    g_line = QgsGeometry(line.clone())
                    if g_line.intersects(g_startline) and g_line.intersects(g_endline):
                        g_centerline_out = QgsGeometry(g_line)
                        break
            else:
                g_centerline_out = QgsGeometry(g_centerline_intersected)

            if g_centerline_out is None or g_centerline_out.isEmpty():
                raise Exception('Centerline task has produced empty centerline polygon.')

            self.centerline = QgsGeometry(g_centerline_out)

            return True
        except Exception as e:
            self.exception = e
            return False

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
                'Centerline Task completed',
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

        self.centerline_complete.emit(self.centerline)

    def cancel(self):
        QgsMessageLog.logMessage(
            f'Centerline Tool was canceled',
            MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
