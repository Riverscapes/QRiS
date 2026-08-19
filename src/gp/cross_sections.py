import math

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsFeature, QgsGeometry, QgsLineString, QgsPointXY, QgsProject, QgsTask
from qgis.PyQt.QtCore import pyqtSignal

from ..compat import MESSAGE_LEVEL_CRITICAL, MESSAGE_LEVEL_SUCCESS, MESSAGE_LEVEL_WARNING, QGSTASK_CAN_CANCEL
from ..lib.map import get_utm_crs
from ..QRiS.settings import Settings


class CrossSectionsTask(QgsTask):
    cross_sections_complete = pyqtSignal(dict)

    def __init__(self, in_centerline: QgsLineString, offset: float, spacing: float, extension: float, source_crs: QgsCoordinateReferenceSystem = None) -> None:
        super().__init__("Generate Cross Sections Task", QGSTASK_CAN_CANCEL)

        self.source_crs = source_crs
        self.centerline = in_centerline
        self.offset = offset
        self.spacing = spacing
        self.extension = extension

        self.xsections = None

    def run(self):
        """Here you implement your heavy lifting.
        Should periodically test for isCanceled() to gracefully
        abort.
        This method MUST return True or False.
        Raising exceptions will crash QGIS, so we handle them
        internally and raise them in self.finished
        """

        self.xsections = {}

        # If source CRS is geographic (lat/lon), transform to a projected CRS (UTM)
        # so that Cartesian math (cos/sin) works correctly in meters.
        if self.source_crs and self.source_crs.isGeographic():
            utm_crs = get_utm_crs(QgsGeometry(self.centerline))
            transform = QgsCoordinateTransform(self.source_crs, utm_crs, QgsProject.instance())
            centerline_geom = QgsGeometry(self.centerline)
            centerline_geom.transform(transform)
        else:
            centerline_geom = QgsGeometry(self.centerline)
            utm_crs = None

        dist = self.spacing  # initial distance from start of line
        sequence = 0

        while dist < centerline_geom.length():
            pt = centerline_geom.interpolate(dist).asPoint()
            # interpolateAngle returns radians clockwise from north (bearing convention).
            # Negate to convert to math convention (CCW from east) for cos/sin.
            alpha = -math.degrees(centerline_geom.interpolateAngle(dist))  # perpendicular angle in degrees
            # create delta x and y via triangulating
            delX = math.cos(math.radians(alpha)) * self.extension
            delY = math.sin(math.radians(alpha)) * self.extension

            pointX = pt.x() + delX
            pointY = pt.y() + delY

            pt1 = QgsPointXY(pointX, pointY)
            geom = QgsLineString([QgsPointXY(pt.x(), pt.y()), pt1])
            geom.extend(self.extension, 0.0)

            feat = QgsFeature()
            feat.setGeometry(QgsGeometry(geom))
            self.xsections[sequence] = feat
            sequence += 1
            dist += self.spacing

        # Transform cross sections back to the source CRS if we projected them
        if utm_crs is not None:
            back_transform = QgsCoordinateTransform(utm_crs, self.source_crs, QgsProject.instance())
            for seq in self.xsections:
                geom = self.xsections[seq].geometry()
                geom.transform(back_transform)
                self.xsections[seq].setGeometry(geom)

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
            Settings.log("CrossSectionsTask completed", MESSAGE_LEVEL_SUCCESS)
        else:
            if self.exception is None:
                Settings.log("Cross Sections not successful but without exception (probably the task was manually canceled by the user)", MESSAGE_LEVEL_WARNING)
            else:
                Settings.log(f"Generate Cross Sections Exception: {self.exception}", MESSAGE_LEVEL_CRITICAL)
                raise self.exception

        self.cross_sections_complete.emit(self.xsections)

    def cancel(self):
        Settings.log("Cross Sections Tool was canceled", MESSAGE_LEVEL_WARNING)
        super().cancel()
