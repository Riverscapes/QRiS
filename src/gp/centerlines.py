
from shapely.geometry import Point, MultiPoint, LineString, MultiLineString, Polygon, MultiPolygon, GeometryCollection
from shapely.ops import voronoi_diagram, split, linemerge
from shapely.wkt import loads

from qgis.core import QgsApplication, QgsTask, QgsMessageLog, Qgis
from qgis.PyQt.QtCore import pyqtSignal


MESSAGE_CATEGORY = 'CenterlineTask'


class CenterlineTask(QgsTask):

    centerline_complete = pyqtSignal(str)

    def __init__(self, in_polygon: Polygon, start_clipline: LineString, end_clipline: LineString) -> None:
        super().__init__('Generate Centerline Task', QgsTask.CanCancel)

        self.in_polygon = loads(in_polygon)
        self.start_clipline = loads(start_clipline)
        self.end_clipline = loads(end_clipline)
        self.clipline = MultiLineString([self.start_clipline, self.end_clipline])
        self.centerline = None

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

        # TODO Densify vertex option
        polygon_dense = self.in_polygon
        # Find the central polygon by clipping the start and end lines
        inter_polygons = split(polygon_dense, start_clipline)
        inter_polygon = MultiPolygon([poly for poly in inter_polygons if poly.intersects(end_clipline.buffer(.00001))])  # max(inter_polygons, key=lambda a: a.area)
        inter_polygons = split(inter_polygon, end_clipline)

        # inter_polygons = split(polygon_dense, self.clipline)
        central_polygon = MultiPolygon([poly for poly in inter_polygons if poly.intersects(end_clipline.buffer(.00001)) and poly.intersects(start_clipline.buffer(.00001))])[0]  # max(inter_polygons, key=lambda a: a.area)

        # build voronoi polygons
        coords_polygon = central_polygon.exterior.coords
        polygon_verts = MultiPoint(coords_polygon)
        voronoi = voronoi_diagram(polygon_verts)  # GeometryCollection

        # Split to L and R

        # Splitting method below is unreliable
        # exter_central = split(central_polygon.boundary, MultiLineString([start_clipline, end_clipline]))
        # m_side_lines_segments = central_polygon.boundary.intersection(exter_central)
        # m_side_lines_segments_clean = GeometryCollection([geom for geom in m_side_lines_segments.geoms if geom.geom_type == 'LineString'])  # remove any pts

        # Split by selecting line segments of polygon not touching midpoint of split lines
        midpoints = [line.interpolate(0.5, normalized=True) for line in [start_clipline, end_clipline]]
        midpoints_buffer = MultiPolygon([pt.buffer(0.00001) for pt in midpoints])
        segments = list(map(LineString, zip(central_polygon.boundary.coords[:-1], central_polygon.boundary.coords[1:])))
        m_side_lines_segments_clean = MultiLineString([segment for segment in segments if midpoints_buffer.disjoint(segment)])
        m_side_lines = MultiLineString(linemerge(m_side_lines_segments_clean))

        side_pts = []
        side_polys = []
        for side_line in list(m_side_lines.geoms):
            mpnts = MultiPoint([Point(pt) for pt in side_line.coords])
            mpolys = MultiPolygon([poly for poly in list(voronoi.geoms) if poly.intersects(mpnts)])
            side_pts.append(mpnts)
            side_polys.append(mpolys)

        m_centerline_raw = side_polys[0].intersection(side_polys[1])
        centerline_raw = linemerge(m_centerline_raw)
        centerline_out = centerline_raw.intersection(self.in_polygon)

        self.centerline = centerline_out
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

        self.centerline_complete.emit(self.centerline)

    def cancel(self):
        QgsMessageLog.logMessage(
            f'Centerline Tool was canceled',
            MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
