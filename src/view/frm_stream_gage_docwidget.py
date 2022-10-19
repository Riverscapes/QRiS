import sqlite3
from datetime import date
from PyQt5 import QtCore, QtGui, QtWidgets
import matplotlib
from qgis import core, gui, utils
from qgis.core import QgsApplication, Qgis
from PyQt5.QtCore import pyqtSlot

# from qgis.core import QgsMapLayer
# from qgis.gui import QgsDataSourceSelectDialog
# from qgis.utils import iface

from ..model.project import Project
from ..model.stream_gage import STREAM_GAGE_MACHINE_CODE
from ..gp.stream_gage_task import StreamGageTask

from ..gp.stream_gage_discharge_task import StreamGageDischargeTask

# https://stackoverflow.com/questions/31406193/matplotlib-is-not-worked-with-qgis
# https://matplotlib.org/3.1.1/gallery/user_interfaces/embedding_in_qt_sgskip.html
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.ticker as ticker

# Help on selection changed event
# https://stackoverflow.com/questions/10156842/howto-get-the-selectionchanged-signal

from ..QRiS.method_to_map import get_stream_gage_layer, build_stream_gage_layer


class FrmStreamGageDocWidget(QtWidgets.QDockWidget):

    def __init__(self, iface, project: Project, parent=None):

        super(FrmStreamGageDocWidget, self).__init__(parent)
        self.iface = iface
        self.project = project
        self.setupUi()
        self.load_stream_gages()

        self.dtStart.setDate(date(date.today().year - 1, date.today().month, date.today().day))
        self.dtEnd.setDate(date.today())

        map_layer = build_stream_gage_layer(self.project)
        map_layer.selectionChanged.connect(self.on_map_selection_changed)

    def load_stream_gages(self):

        conn = sqlite3.connect(self.project.project_file)
        curs = conn.cursor()
        curs.execute('SELECT fid, site_name, site_code FROM stream_gages')
        self.stream_gage_model = QtGui.QStandardItemModel()
        for row in curs.fetchall():
            item = QtGui.QStandardItem(row[1])
            item.setData((row[0], row[2]), QtCore.Qt.UserRole)
            self.stream_gage_model.appendRow(item)

        self.lst_gages.setModel(self.stream_gage_model)
        self.lst_gages.selectionModel().selectionChanged.connect(self.on_site_changed)

    def on_map_selection_changed(selected, deselected, clearAndSelect: bool):
        print('here')

    def on_site_changed(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):

        site_id = self.selected_stream_gage()
        if site_id is None:
            return

        self.load_discharge_plot()

        map_layer = get_stream_gage_layer(self.project)
        if map_layer is None:
            return

        # ) .setSelectedFeatures
        map_layer.selectByIds([site_id])
        self.iface.mapCanvas().zoomToSelected()

    def selected_stream_gage(self):
        lst_item = self.stream_gage_model.itemFromIndex(self.lst_gages.currentIndex())
        if lst_item is None:
            return

        site_id, site_code = lst_item.data(QtCore.Qt.UserRole)
        return site_id

    def load_discharge_plot(self):

        self._static_ax.cla()

        lst_item = self.stream_gage_model.itemFromIndex(self.lst_gages.currentIndex())
        if lst_item is None:
            return

        site_id, site_code = lst_item.data(QtCore.Qt.UserRole)
        start = date(self.dtStart.date().year(), self.dtStart.date().month(), self.dtStart.date().day())
        end = date(self.dtEnd.date().year(), self.dtEnd.date().month(), self.dtEnd.date().day())

        conn = sqlite3.connect(self.project.project_file)
        curs = conn.cursor()
        curs.execute('SELECT measurement_date, discharge FROM stream_gage_discharges WHERE (stream_gage_id = ?) AND (measurement_date >= ?) AND (measurement_date < ?) ORDER BY measurement_date',
                     [site_id, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')])

        data = [(row[0], row[1]) for row in curs.fetchall()]
        dates = [item[0] for item in data]
        disch = [item[1] for item in data]
        self._static_ax.plot(dates, disch, ".")
        self._static_ax.set_ylabel('Discharge (CFS)')
        self._static_ax.set_xlabel('Date')

        self._static_ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%b'))
        # self._static_ax.xaxis.set_ticks(range(start, end, 30))
        self._static_ax.xaxis.set_major_locator(ticker.MultipleLocator(30))
        self.static_canvas.draw()

    def download_discharges(self):

        lst_item = self.stream_gage_model.itemFromIndex(self.lst_gages.currentIndex())
        if lst_item is None:
            return

        site_id, site_code = lst_item.data(QtCore.Qt.UserRole)

        start = date(self.dtStart.date().year(), self.dtStart.date().month(), self.dtStart.date().day())
        end = date(self.dtEnd.date().year(), self.dtEnd.date().month(), self.dtEnd.date().day())

        task = StreamGageDischargeTask(self.project.project_file, site_code, site_id, start, end)
        task.on_task_complete.connect(self.on_download_discharges_complete)

        # self.on_download_discharges_complete(task.run(), task.inserted_discharge_records)
        QgsApplication.taskManager().addTask(task)

    @pyqtSlot(bool, int)
    def on_download_discharges_complete(self, success: bool, rowsAffected: int):

        if success:
            self.iface.messageBar().pushMessage('Stream Discharges Downloaded', f'{rowsAffected} discharge records downloaded.', level=Qgis.Info, duration=5)
        else:
            self.iface.messageBar().pushMessage('Stream Discharges Download Error', 'Check the QGIS Log for details.', level=Qgis.Warning, duration=5)

        self.load_discharge_plot()

    def download_stream_gages(self):

        extent = self.iface.mapCanvas().extent()
        task = StreamGageTask(self.project.project_file, extent.yMinimum(), extent.yMaximum(), extent.xMinimum(), extent.xMaximum())
        task.on_task_complete.connect(self.on_download_gages_complete)
        # task.run()
        QgsApplication.taskManager().addTask(task)

    @pyqtSlot(bool, int)
    def on_download_gages_complete(self, success: bool, rowsAffected: int):

        if success:
            self.iface.messageBar().pushMessage('Stream Gages Downloaded', f'{rowsAffected} gage records downloaded.', level=Qgis.Info, duration=5)
        else:
            self.iface.messageBar().pushMessage('Stream Gage Download Error', 'Check the QGIS Log for details.', level=Qgis.Warning, duration=5)

        self.load_stream_gages()

    def setupUi(self):

        minDate = QtCore.QDate(1970, 1, 1)
        maxDate = QtCore.QDate(date.today())

        self.setWindowTitle('Stream Gage Explorer')
        self.dockWidgetContents = QtWidgets.QWidget()

        self.main_horiz = QtWidgets.QHBoxLayout(self.dockWidgetContents)

        self.splitter = QtWidgets.QSplitter(self.dockWidgetContents)
        self.splitter.setSizes([300])
        self.main_horiz.addWidget(self.splitter)

        self.lst_gages = QtWidgets.QListView()
        self.lst_gages.setMaximumWidth(400)
        self.splitter.addWidget(self.lst_gages)

        self.right_widget = QtWidgets.QWidget()
        self.splitter.addWidget(self.right_widget)

        self.right_vert = QtWidgets.QVBoxLayout()

        self.right_widget.setLayout(self.right_vert)

        self.button_horiz = QtWidgets.QHBoxLayout()
        self.right_vert.addLayout(self.button_horiz)

        self.dtStart = QtWidgets.QDateEdit()
        self.dtStart.setMinimumDate(minDate)
        self.dtStart.setMaximumDate(maxDate)
        self.button_horiz.addWidget(self.dtStart)

        self.dtEnd = QtWidgets.QDateEdit()
        self.dtEnd.setMinimumDate(minDate)
        self.dtEnd.setMaximumDate(maxDate)
        self.button_horiz.addWidget(self.dtEnd)

        self.cmdGage = QtWidgets.QPushButton()
        self.cmdGage.setText('Download Gages')
        self.cmdGage.setToolTip('Download Stream Gage Locations for Current Map Extent')
        self.cmdGage.clicked.connect(self.download_stream_gages)
        self.button_horiz.addWidget(self.cmdGage)

        self.cmdDischarge = QtWidgets.QPushButton()
        self.cmdDischarge.setText('Download Discharge')
        self.cmdDischarge.clicked.connect(self.download_discharges)
        self.button_horiz.addWidget(self.cmdDischarge)

        self.cmdExport = QtWidgets.QPushButton()
        self.cmdExport.setText('Export')
        self.button_horiz.addWidget(self.cmdExport)

        self.static_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self.right_vert.addWidget(self.static_canvas)
        self._static_ax = self.static_canvas.figure.subplots()

        self.setWidget(self.dockWidgetContents)
