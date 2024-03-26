import numpy as np
import sqlite3
from datetime import date

from PyQt5 import QtCore, QtGui, QtWidgets
import matplotlib
from qgis import core, gui, utils
from qgis.core import QgsApplication, Qgis, QgsMessageLog
from PyQt5.QtCore import pyqtSlot

from ..QRiS.settings import CONSTANTS

# from qgis.core import QgsMapLayer
# from qgis.gui import QgsDataSourceSelectDialog
# from qgis.utils import iface

from ..model.project import Project
from ..model.stream_gage import STREAM_GAGE_MACHINE_CODE
from ..model.db_item import dict_factory
from ..model.basin_characteristics_table_view import BasinCharsTableModel
from ..gp.stream_gage_task import StreamGageTask

from ..gp.stream_gage_discharge_task import StreamGageDischargeTask

# https://stackoverflow.com/questions/31406193/matplotlib-is-not-worked-with-qgis
# https://matplotlib.org/3.1.1/gallery/user_interfaces/embedding_in_qt_sgskip.html
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
    import matplotlib.ticker as ticker
except ImportError:
    QgsMessageLog.logMessage(f"Matplotlib is not at a sufficient version: {matplotlib.__version__}", CONSTANTS['logCategory'], level=Qgis.Critical)


# Help on selection changed event
# https://stackoverflow.com/questions/10156842/howto-get-the-selectionchanged-signal

from ..QRiS.qris_map_manager import QRisMapManager


class FrmStreamGageDocWidget(QtWidgets.QDockWidget):

    def __init__(self, iface, project: Project, map_manager: QRisMapManager, parent=None):

        super(FrmStreamGageDocWidget, self).__init__(parent)
        self.iface = iface
        self.project = project
        self.map_manager = map_manager
        self.setupUi()
        self.load_stream_gages()

        self.dtStart.setDate(date(date.today().year - 1, date.today().month, date.today().day))
        self.dtEnd.setDate(date.today())

        # lets plot a few sample points
        t = np.arange(0.0, 2.0, 0.01)
        s = 1 + np.sin(2 * np.pi * t)
        self._static_ax.plot(t, s)

        # map_layer = self.map_manager.build_stream_gage_layer()
        # map_layer.selectionChanged.connect(self.on_map_selection_changed)

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

    def on_map_selection_changed(self, selected, deselected, clearAndSelect: bool):
        print('here')

    def on_site_changed(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):

        site_id = self.selected_stream_gage()
        if site_id is None:
            return

        self.load_discharge_plot()
        self.load_metadata()

        map_layer = self.map_manager.get_machine_code_layer(self.project.map_guid, STREAM_GAGE_MACHINE_CODE, None)
        if map_layer is None:
            return

        # ) .setSelectedFeatures
        self.iface.mapCanvas().setCurrentLayer(map_layer)
        map_layer.selectByIds([site_id])
        self.iface.mapCanvas().zoomToSelected()

    def selected_stream_gage(self):
        lst_item = self.stream_gage_model.itemFromIndex(self.lst_gages.currentIndex())
        if lst_item is None:
            return

        site_id, site_code = lst_item.data(QtCore.Qt.UserRole)
        return site_id

    def load_metadata(self):

        lst_item = self.stream_gage_model.itemFromIndex(self.lst_gages.currentIndex())
        if lst_item is None:
            return

        fields = {
            'site_code': 'Site Code',
            'site_name': 'Site Name',
            'site_datum': 'Site Datum',
            'huc': 'HUC',
            'agency': 'Agency',
            'latitude': 'Latitude',
            'longitude': 'Longitude'
        }

        site_id, site_code = lst_item.data(QtCore.Qt.UserRole)
        conn = sqlite3.connect(self.project.project_file)
        conn.row_factory = dict_factory
        curs = conn.cursor()
        curs.execute('SELECT {} FROM stream_gages where fid = ?'.format(','.join(fields.keys())), [site_id])
        row = curs.fetchone()
        metadata_values = [(val, row[key]) for key, val in fields.items()]
        self.metadata_model = BasinCharsTableModel(metadata_values, ['Name', 'Value'])
        self.tableMeta.setModel(self.metadata_model)

    def load_discharge_data(self):

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
        return data

    def load_discharge_plot(self):

        data = self.load_discharge_data()
        if data is None:
            return

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

    def export(self):

        data = self.load_discharge_data()
        if data is None:
            self.iface.messageBar().pushMessage('Discharge Export', f'No data to export.', level=Qgis.Info, duration=5)
            return

        dialog_return = QtWidgets.QFileDialog.getSaveFileName(self, "Export Discharge Data", None, 'CSV Files (*.csv)')
        if dialog_return is not None and dialog_return[0] != '':
            with open(dialog_return[0], 'w') as f:
                f.write('measurement_date,discharge (cfs)\n')
                [f.write(f'{row[0]},{row[1]}\n') for row in data]

        self.iface.messageBar().pushMessage('Discharge Export', 'Data successfully exported to ' + dialog_return[0], level=Qgis.Info, duration=5)

    def setupUi(self):

        minDate = QtCore.QDate(1970, 1, 1)
        maxDate = QtCore.QDate(date.today())

        self.setWindowTitle('Stream Gage Explorer')
        self.dockWidgetContents = QtWidgets.QWidget(self)

        self.main_horiz = QtWidgets.QHBoxLayout(self.dockWidgetContents)

        self.splitter = QtWidgets.QSplitter(self.dockWidgetContents)
        self.splitter.setSizes([300])
        self.main_horiz.addWidget(self.splitter)

        self.left_vert = QtWidgets.QVBoxLayout(self)

        self.left_widget = QtWidgets.QWidget(self)
        self.splitter.addWidget(self.left_widget)
        self.left_widget.setLayout(self.left_vert)

        self.cmdGage = QtWidgets.QPushButton()
        self.cmdGage.setText('Download Gages')
        self.cmdGage.setToolTip('Download Stream Gage Locations for Current Map Extent')
        self.cmdGage.setEnabled(False)
        self.cmdGage.clicked.connect(self.download_stream_gages)
        self.left_vert.addWidget(self.cmdGage)

        self.lst_gages = QtWidgets.QListView()
        # self.lst_gages.setMaximumWidth(400)
        self.left_vert.addWidget(self.lst_gages)

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

        self.cmdDischarge = QtWidgets.QPushButton()
        self.cmdDischarge.setText('Download Discharge')
        self.cmdDischarge.clicked.connect(self.download_discharges)
        self.button_horiz.addWidget(self.cmdDischarge)

        self.cmdExport = QtWidgets.QPushButton()
        self.cmdExport.setText('Export')
        self.cmdExport.clicked.connect(self.export)
        self.button_horiz.addWidget(self.cmdExport)

        self.static_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self._static_ax = self.static_canvas.figure.subplots()

        self.tableMeta = QtWidgets.QTableView(self)
        self.tableMeta.verticalHeader().hide()

        self.tabWidget = QtWidgets.QTabWidget()
        self.right_vert.addWidget(self.tabWidget)
        self.tabWidget.addTab(self.static_canvas, 'Graphical')
        self.tabWidget.addTab(self.tableMeta, 'Metadata')

        self.setWidget(self.dockWidgetContents)
