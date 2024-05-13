import numpy as np
import sqlite3
from datetime import date, datetime

from PyQt5 import QtCore, QtGui, QtWidgets
import matplotlib

from qgis.core import QgsApplication, Qgis, QgsMessageLog, QgsVectorLayer, QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsRectangle
from PyQt5.QtCore import pyqtSlot

from ..QRiS.settings import CONSTANTS
from ..QRiS.qris_map_manager import QRisMapManager

from .utilities import add_help_button

from ..model.project import Project
from ..model.stream_gage import STREAM_GAGE_MACHINE_CODE
from ..model.db_item import dict_factory
from ..model.basin_characteristics_table_view import BasinCharsTableModel

from ..gp.stream_gage_task import StreamGageTask
from ..gp.stream_gage_discharge_task import StreamGageDischargeTask

# https://stackoverflow.com/questions/31406193/matplotlib-is-not-worked-with-qgis
# https://matplotlib.org/3.1.1/gallery/user_interfaces/embedding_in_qt_sgskip.html
try:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import matplotlib.ticker as ticker
except ImportError:
    QgsMessageLog.logMessage(f"Matplotlib is not at a sufficient version: {matplotlib.__version__}", CONSTANTS['logCategory'], level=Qgis.Critical)


# Help on selection changed event
# https://stackoverflow.com/questions/10156842/howto-get-the-selectionchanged-signal


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

        map_layer = self.map_manager.build_stream_gage_layer()
        # map_layer.selectionChanged.connect(self.on_map_selection_changed)

    def load_stream_gages(self):

        # clear the list view
        self.lst_gages.setModel(None)

        with sqlite3.connect(self.project.project_file) as conn:
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

        map_layer_tree = self.map_manager.get_machine_code_layer(self.project.map_guid, STREAM_GAGE_MACHINE_CODE, None)
        if map_layer_tree is None:
            return
        map_layer: QgsVectorLayer = map_layer_tree.layer()
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

        dates = [datetime.strptime(item[0], '%Y-%m-%d') for item in data]
        disch = [item[1] for item in data]
        # remove empty string values
        disch = [item if item != '' else None for item in disch]
        self._static_ax.plot(dates, disch, ".")
        self._static_ax.set_ylabel('Discharge (CFS)')
        self._static_ax.set_xlabel('Date')

        self._static_ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%b'))
        self._static_ax.xaxis.set_major_locator(ticker.MultipleLocator(30))
        self._static_ax.tick_params(axis='x', rotation=45)
        
        # Adjust the bottom margin
        plt.subplots_adjust(bottom=0.75)
        
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

        extent: QgsRectangle = self.iface.mapCanvas().extent()
        source_crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        target_crs = QgsCoordinateReferenceSystem('EPSG:4326')
        transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())
        extent = transform.transform(extent)

        task = StreamGageTask(self.project.project_file, extent.yMinimum(), extent.yMaximum(), extent.xMinimum(), extent.xMaximum())
        task.on_task_complete.connect(self.on_download_gages_complete)
        # task.run()
        QgsApplication.taskManager().addTask(task)

    @pyqtSlot(bool, int, int)
    def on_download_gages_complete(self, success: bool, rowsDownloaded:int, rowsSaved: int):

        if success:
            if rowsDownloaded == 0:
                self.iface.messageBar().pushMessage('Stream Gages', 'No stream gage locations were found in the current map extent.', level=Qgis.Info, duration=5)
            elif rowsSaved == 0:
                self.iface.messageBar().pushMessage('Stream Gages Downloaded', f'{rowsDownloaded} stream gage locations found, however none were new.', level=Qgis.Info, duration=5)
            else:
                self.iface.messageBar().pushMessage('Stream Gages Downloaded', f'{rowsSaved} new stream gage locations were downloaded and saved to the project.', level=Qgis.Success, duration=5)
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

    def delete_gage(self):
        
        # Confirm deletion
        result = QtWidgets.QMessageBox.question(self, 'Delete Stream Gage', 'Are you sure you want to delete this stream gage and all associated discharge data?', QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if result == QtWidgets.QMessageBox.No:
            return
        
        lst_item = self.stream_gage_model.itemFromIndex(self.lst_gages.currentIndex())
        if lst_item is None:
            return
        
        site_id, site_code = lst_item.data(QtCore.Qt.UserRole)
        with sqlite3.connect(self.project.project_file) as conn:
            try:
                curs = conn.cursor()
                curs.execute('DELETE FROM stream_gage_discharges WHERE stream_gage_id = ?', [site_id])
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                self.iface.messageBar().pushMessage('Error Deleting Discharge Data', str(e), level=Qgis.Critical, duration=5)
                return
        # now use ogr to delete the feature
        fc_path = f"{self.project.project_file}|layername=stream_gages|subset=fid = {site_id}"
        temp_layer = QgsVectorLayer(fc_path, 'temp', 'ogr')
        temp_layer.startEditing()
        for feature in temp_layer.getFeatures():
            temp_layer.deleteFeature(feature.id())
        temp_layer.commitChanges()
        temp_layer.updateExtents()
        self.iface.mapCanvas().refresh()
        self.iface.mapCanvas().refreshAllLayers()
        
        # let the user know
        self.iface.messageBar().pushMessage('Stream Gage Deleted', f'Stream Gage {site_code} and associated discharge data deleted.', level=Qgis.Info, duration=5)
        
        self.load_stream_gages()
        # clear the plot and metadata
        self._static_ax.cla()
        self.static_canvas.draw()
        self.tableMeta.setModel(None)
        
        self.load_discharge_plot()
        self.load_metadata()

    def on_gage_context_menu(self, point):
        index = self.lst_gages.indexAt(point)
        if not index.isValid():
            return

        menu = QtWidgets.QMenu()
        delete_action = QtWidgets.QAction(QtGui.QIcon(f':/plugins/qris_toolbar/delete'), 'Delete Stream Gage', self)
        delete_action.triggered.connect(self.delete_gage)
        menu.addAction(delete_action)
        menu.exec_(QtGui.QCursor.pos())

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
        self.cmdGage.clicked.connect(self.download_stream_gages)
        self.left_vert.addWidget(self.cmdGage)

        self.lst_gages = QtWidgets.QListView()
        # self.lst_gages.setMaximumWidth(400)
        self.lst_gages.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.lst_gages.customContextMenuRequested.connect(self.on_gage_context_menu)
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

        self.cmdHelp = add_help_button(self, 'context/stream-gage-explorer')
        self.button_horiz.addWidget(self.cmdHelp)

        self.static_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self._static_ax = self.static_canvas.figure.subplots()

        self.tableMeta = QtWidgets.QTableView(self)
        self.tableMeta.verticalHeader().hide()

        self.tabWidget = QtWidgets.QTabWidget()
        self.right_vert.addWidget(self.tabWidget)
        self.tabWidget.addTab(self.static_canvas, 'Graphical')
        self.tabWidget.addTab(self.tableMeta, 'Metadata')

        self.setWidget(self.dockWidgetContents)
