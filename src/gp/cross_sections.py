
import math

from qgis.core import QgsTask, QgsMessageLog, Qgis, QgsFields, QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsLineString
from qgis.PyQt.QtCore import pyqtSignal, QVariant


MESSAGE_CATEGORY = 'CrossSectionsTask'


class CrossSectionsTask(QgsTask):

    cross_sections_complete = pyqtSignal(dict)

    def __init__(self, in_centerline: QgsLineString, offset: float, spacing: float, extension: float, in_polygon: QgsGeometry = None) -> None:
        super().__init__('Generate Cross Sections Task', QgsTask.CanCancel)

        self.polygon = in_polygon
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

        # Lay out points along line
        # methodology based on https://gis.stackexchange.com/questions/302802/create-points-along-line-and-apply-a-90-offset-to-them-pyqgis

        self.xsections = {}
        dist = self.spacing  # intial distance from start of line
        sequence = 0

        while dist < self.centerline.length():

            pt = self.centerline.interpolate(dist).asPoint()
            alpha = (math.degrees(self.centerline.interpolateAngle(dist)) - 90)  # return in degree
            # create delta x and y via triangulating
            delY = math.cos(math.radians(alpha)) * self.extension
            delX = math.sin(math.radians(alpha)) * self.extension

            pointX = pt[0] + delX
            pointY = pt[1] + delY

            pt1 = QgsPointXY(pointX, pointY)
            feat = QgsFeature()
            geom = QgsLineString([pt, pt1])

            geom.extend(self.extension, 0.0)
            #clipped_geom = self.polygon.intersection(geom)

            feat.setGeometry(geom)
            self.xsections[sequence] = feat
            sequence += 1
            dist += self.spacing

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
                'CrossSectionsTask completed\n',
                MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Cross Sections not successful but without '
                    'exception (probably the task was manually '
                    'canceled by the user)'.format(
                        name=self.description()),
                    MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(
                    f'Generate Cross Sections Exception: {self.exception}',
                    MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

        self.cross_sections_complete.emit(self.xsections)

    def cancel(self):
        QgsMessageLog.logMessage(
            f'Cross Sections Tool was canceled',
            MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
