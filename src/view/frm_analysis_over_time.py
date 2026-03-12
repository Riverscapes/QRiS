import textwrap
import numpy as np

from qgis.PyQt import QtCore, QtWidgets, QtGui
from qgis.gui import QgisInterface
from qgis.core import Qgis,  QgsProject, QgsCoordinateTransform, QgsMessageLog, QgsVectorLayer, QgsField, QgsVectorFileWriter, QgsFeature
from qgis.PyQt.QtCore import QVariant

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from ..model.project import Project
from ..model.analysis import Analysis
from ..model.sample_frame import SampleFrame, get_sample_frame_sequence
from ..model.metric_value import load_metric_values
from ..lib.unit_conversion import short_unit_name, distance_units, area_units, ratio_units
from ..model.event import DCE_EVENT_TYPE_ID

from .widgets.event_library import EventLibraryWidget
from .utilities import add_help_button
from .frm_metric_value import FrmMetricValue

class FrmAnalysisOverTime(QtWidgets.QDockWidget):
    """
    Dockable widget for performing analysis over time. Allows users to select a sample frame and pour point, and then runs the analysis.
    """

    def __init__(self, iface: QgisInterface, project: Project, map_manager, analysis: Analysis):
        super().__init__("Analysis Over Time", iface.mainWindow())
        self.setObjectName("AnalysisOverTimeDock")
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.TopDockWidgetArea)
        
        self.iface = iface
        self.project = project
        self.map_manager = map_manager
        self.analysis = analysis
        
        self.active_scope_layer = None

        self.setup_ui()
        self.populate_analyses()
        self.populate_data()

        # Connections for interactive map
        self.chk_interactive_map.toggled.connect(self.update_map)
        self.sample_frame_combo.currentIndexChanged.connect(self.update_map)
        
        # Enable by default and trigger initial map update
        self.chk_interactive_map.setChecked(True)
        self.analysis_combo.currentIndexChanged.connect(self.on_analysis_changed)
        self.metric_combo.currentIndexChanged.connect(self.redraw_chart)
        self.sample_frame_combo.currentIndexChanged.connect(self.redraw_chart)
        self.event_library.event_checked.connect(self.redraw_chart)
        self.sample_frame_combo.currentIndexChanged.connect(self.redraw_chart)
        self.event_library.event_checked.connect(self.redraw_chart)
        # Trigger redraw when events are reordered
        if hasattr(self.event_library, 'table') and hasattr(self.event_library.table, 'orderChanged'):
            self.event_library.table.orderChanged.connect(self.redraw_chart)

        # Chart UI triggers
        self.chart.cbo_value_type.currentIndexChanged.connect(self.redraw_chart)
        self.chart.action_chk_uncertainty.triggered.connect(self.redraw_chart)
        self.chart.chart_needs_update.connect(self.redraw_chart)
        self.chart.metric_data_clicked.connect(self.edit_metric_value)
        self.update_map()
        self.redraw_chart()

    def populate_analyses(self):
        self.analysis_combo.blockSignals(True)
        self.analysis_combo.clear()
        
        if self.project and self.project.analyses:
            sorted_analyses = sorted(self.project.analyses.values(), key=lambda a: a.name)
            for a in sorted_analyses:
                self.analysis_combo.addItem(a.name, a.id)
            
            # Select current analysis
            if self.analysis:
                idx = self.analysis_combo.findData(self.analysis.id)
                if idx >= 0:
                    self.analysis_combo.setCurrentIndex(idx)
        
        self.analysis_combo.blockSignals(False)

    def on_analysis_changed(self):
        analysis_id = self.analysis_combo.currentData()
        if analysis_id:
             self.analysis = self.project.analyses.get(analysis_id)
             self.chart.analysis = self.analysis
             self.chart.setup_units_menu()
             self.populate_data()
             self.update_map()

    def update_map(self):
        if not self.chk_interactive_map.isChecked():
            return
            
        if not self.iface or not self.analysis or not self.analysis.sample_frame:
            return

        project = QgsProject.instance()
        scope_item = self.analysis.sample_frame

        layer = None
        if scope_item.sample_frame_type == SampleFrame.AOI_SAMPLE_FRAME_TYPE:
            layer = self.map_manager.build_aoi_layer(scope_item)
        else:
            layer = self.map_manager.build_sample_frame_layer(scope_item)

        if self.active_scope_layer and layer and self.active_scope_layer.id() != layer.id():
            if self.active_scope_layer.id() in project.mapLayers():
                project.removeMapLayer(self.active_scope_layer.id())

        self.active_scope_layer = layer

        # Zoom to selected feature
        scope_feature_id = self.sample_frame_combo.currentData()
        extent = None

        if self.active_scope_layer:
            if scope_feature_id:
                feat = self.active_scope_layer.getFeature(scope_feature_id)
                if feat.isValid():
                    extent = feat.geometry().boundingBox()
            else:
                extent = self.active_scope_layer.extent()

        if extent and not extent.isEmpty():
            canvas = self.iface.mapCanvas()
            if self.active_scope_layer.crs() != canvas.mapSettings().destinationCrs():
                 xform = QgsCoordinateTransform(self.active_scope_layer.crs(), canvas.mapSettings().destinationCrs(), QgsProject.instance())
                 extent = xform.transformBoundingBox(extent)

            extent.scale(1.1)
            canvas.setExtent(extent)
            canvas.refresh()

    def populate_data(self):
        # 1. Populate Metrics Combo (Use analysis metrics mapping)
        self.metric_combo.clear()
        if self.analysis and self.analysis.analysis_metrics:
            for metric_id, am in self.analysis.analysis_metrics.items():
                self.metric_combo.addItem(am.metric.name, metric_id)
                
        # 2. Populate Sample Frame Features Combo
        self.sample_frame_combo.blockSignals(True)
        self.sample_frame_combo.clear()
        
        if self.analysis and self.analysis.sample_frame:
            try:
                scope_item = self.analysis.sample_frame
                features_sequence = get_sample_frame_sequence(self.project.project_file, scope_item.id)
                for feature in features_sequence:
                    display_name = str(feature.name) if feature.name is not None else str(feature.id)
                    self.sample_frame_combo.addItem(display_name, feature.id)
            except Exception as e:
                QgsMessageLog.logMessage(f"Error loading sample frame features: {e}", 'QRiS', Qgis.Warning)
                
        self.sample_frame_combo.blockSignals(False)
            
        # 3. Populate DCE Event Library Widget and Select Settings
        # Enable dragging/reordering and filter on existing events
        self.event_library.allow_reorder = True

        # Load in the previously selected DCEs from the analysis metadata if present
        if self.analysis and self.analysis.metadata and 'selected_events' in self.analysis.metadata:
            selected_event_ids = self.analysis.metadata.get('selected_events', [])
            
            # Create ordered list of events
            all_events = [e for e in self.project.events.values() if e.event_type.id == DCE_EVENT_TYPE_ID]
            event_map = {e.id: e for e in all_events}

            ordered_events = []
            # Add selected events in order
            for eid in selected_event_ids:
                if eid in event_map:
                    ordered_events.append(event_map[eid])

            # Add remaining events (unselected)
            for e in all_events:
                if e.id not in selected_event_ids:
                    ordered_events.append(e)

            self.event_library.load_events(ordered_events)
            self.event_library.set_selected_event_ids(selected_event_ids)
        else:
            all_events = [e for e in self.project.events.values() if e.event_type.id == DCE_EVENT_TYPE_ID]
            self.event_library.load_events(all_events)
            self.event_library.select_all()

    def setup_ui(self):
        self.main_widget = QtWidgets.QWidget()
        self.setWidget(self.main_widget)
        
        # Splitter to separate left/right
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addWidget(self.splitter)
        self.main_widget.setLayout(main_layout)

        # ========== LEFT SIDE (Tabs) ==========
        self.left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(self.left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QtWidgets.QTabWidget()
        left_layout.addWidget(self.tabs)
        
        # --- TAB A: Basic Properties ---
        self.tab_basic = QtWidgets.QWidget()
        basic_layout = QtWidgets.QVBoxLayout(self.tab_basic)
        
        grid_layout = QtWidgets.QGridLayout()
        # Analysis Selection
        lbl_analysis = QtWidgets.QLabel("Analysis:")
        grid_layout.addWidget(lbl_analysis, 0, 0)
        self.analysis_combo = QtWidgets.QComboBox()
        grid_layout.addWidget(self.analysis_combo, 0, 1)

        # Metric Selection
        lbl_metric = QtWidgets.QLabel("Metric:")
        grid_layout.addWidget(lbl_metric, 1, 0)
        self.metric_combo = QtWidgets.QComboBox()
        grid_layout.addWidget(self.metric_combo, 1, 1)

        # Sample Frame Selection
        lbl_sample_frame = QtWidgets.QLabel("Mask Polygon:")
        grid_layout.addWidget(lbl_sample_frame, 2, 0)
        self.sample_frame_combo = QtWidgets.QComboBox()
        grid_layout.addWidget(self.sample_frame_combo, 2, 1)

        self.chk_interactive_map = QtWidgets.QCheckBox("Interactive Map")
        grid_layout.addWidget(self.chk_interactive_map, 3, 0, 1, 2)
        
        # Push the grid to the top
        basic_layout.addLayout(grid_layout)
        basic_layout.addStretch()

        self.tabs.addTab(self.tab_basic, "Chart Inputs")

        # --- TAB B: Data Capture Events ---
        self.tab_dces = QtWidgets.QWidget()
        dces_layout = QtWidgets.QVBoxLayout(self.tab_dces)
        
        self.event_library = EventLibraryWidget(self.tab_dces, self.project, allow_reorder=True)
        dces_layout.addWidget(self.event_library)
        
        self.tabs.addTab(self.tab_dces, "Data Capture Events")

        # Add Help Button
        self.help_layout = QtWidgets.QHBoxLayout()
        self.btn_help = QtWidgets.QPushButton("Help")
        # Assuming utilities.py is in scope or we import add_help_button
        # But wait, utilities.add_help_button returns a button and adds connection
        # Let's use the helper if possible, or just reimplement for dock widget context
        # Since add_help_button is designed for a form/dialog, let's manually add it here using same logic
        
        self.btn_help = QtWidgets.QPushButton("Help")
        # We need to import CONSTANTS from somewhere to get the URL, usually from ..QRiS.settings
        from ..QRiS.settings import CONSTANTS
        help_url = CONSTANTS['webUrl'].rstrip('/') + '/software-help/technical-reference/analysis/analysis-over-time'
        self.btn_help.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(help_url)))
        
        self.help_layout.addWidget(self.btn_help)
        self.help_layout.addStretch()
        
        left_layout.addLayout(self.help_layout)

        # Add left widget to splitter
        self.splitter.addWidget(self.left_widget)
        
        # Give the left panel a minimum width of 500
        self.left_widget.setMinimumWidth(500)

        # ========== RIGHT SIDE (Chart) ==========
        self.right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(self.right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.chart = AnalysisOverTimeChart(parent=self.right_widget, project=self.project, analysis=self.analysis)
        right_layout.addWidget(self.chart)
        
        self.splitter.addWidget(self.right_widget)
        
        # Stretch the right side panel to use the available width
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

    def redraw_chart(self, *args):
        metric_id = self.metric_combo.currentData()
        scope_feature_id = self.sample_frame_combo.currentData()
        if not metric_id or not scope_feature_id or not self.analysis or not self.project:
            return

        # Fetch visually reordered events from the list
        selected_events = []
        table = self.event_library.table
        for row in range(table.rowCount()):
            if table.item(row, 0).checkState() == QtCore.Qt.Checked:
                event = table.item(row, 1).data(QtCore.Qt.UserRole)
                if event is not None:
                    selected_events.append(event)

        if not selected_events:
            self.chart.render_plot([], [], None, "No events selected", self.chart.cbo_value_type.currentText())
            return
            
        metric = self.project.metrics.get(metric_id)
        
        x_labels = []
        y_values = []
        y_err = []
        metric_details = []
        
        for event in selected_events:
            x_labels.append(event.name)
            
            try:
                values_dict = load_metric_values(self.project.project_file, self.analysis, event, scope_feature_id, self.project.metrics)
                if metric_id in values_dict:
                    mv = values_dict[metric_id]
                    metric_details.append((mv, event, scope_feature_id))
                    
                    display_unit = None
                    if metric and hasattr(self.analysis, 'units'):
                        if metric.normalized:
                            if hasattr(metric, 'normalization_unit_type') and metric.normalization_unit_type == 'area':
                                display_unit = self.analysis.units.get('area', None)
                            elif hasattr(metric, 'normalization_unit_type') and metric.normalization_unit_type == 'distance':
                                display_unit = self.analysis.units.get('distance', None)
                            elif metric.unit_type != 'ratio':
                                display_unit = self.analysis.units.get('distance', None)
                        else:
                            display_unit = self.analysis.units.get(metric.unit_type, None)

                        if display_unit in ['count', 'ratio']:
                            display_unit = None
                            
                    val = mv.current_value(display_unit)
                    y_values.append(val)
                    
                    err_val = 0.0
                    if mv.uncertainty and 'Plus/Minus' in mv.uncertainty:
                        err_val = mv.uncertainty['Plus/Minus']
                    elif mv.uncertainty and 'Percent' in mv.uncertainty and val is not None:
                        err_val = abs(val * (mv.uncertainty['Percent'] / 100.0))
                    
                    y_err.append(err_val)
                else:
                    y_values.append(None)
                    y_err.append(0.0)
                    metric_details.append(None)
            except Exception as e:
                y_values.append(None)
                y_err.append(0.0)
                metric_details.append(None)

        val_type = self.chart.cbo_value_type.currentText()
        show_err = self.chart.action_chk_uncertainty.isChecked()
        
        ylabel = metric.name if metric else "Value"
        if metric and hasattr(self.analysis, 'units'):
            du = short_unit_name(self.analysis.units.get(metric.unit_type, None))
            if metric.normalized:
                if du != 'ratio':
                    norm_key = 'distance'
                    if hasattr(metric, 'normalization_unit_type') and metric.normalization_unit_type == 'area':
                        norm_key = 'area'
                    
                    norm_u = short_unit_name(self.analysis.units.get(norm_key, None))
                    du = f'{du}/{norm_u}'
            if du and du not in ['count', 'ratio']:
                ylabel += f" ({du})"
                
        self.chart.render_plot(x_labels, y_values, y_err if show_err else None, ylabel, val_type, metric.name if metric else None, metric_details)
    def edit_metric_value(self, details_tuple):
        if not details_tuple:
            return
            
        mv, event, feature_id = details_tuple
        
        # Open the metric value form
        # We need to map the parent to mainWindow or self
        frm = FrmMetricValue(self.iface.mainWindow(), self.project, self.analysis, event, feature_id, mv)
        
        # If the user saves, the form returns Accepted (1)
        if frm.exec_():
            # Refresh the chart to show new values
            self.redraw_chart()


class AnalysisOverTimeChart(QtWidgets.QWidget):
    chart_needs_update = QtCore.pyqtSignal()
    metric_data_clicked = QtCore.pyqtSignal(object)

    def __init__(self, parent=None, project=None, analysis=None):
        super().__init__(parent)
        self.project = project
        self.analysis = analysis
        self.chart_font = QtGui.QFont("Sans Serif", 10)
        self.setup_ui()
        if self.analysis:
            self.setup_units_menu()
        
        self.canvas.mpl_connect('button_press_event', self.on_click)

    def setup_ui(self):
        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        # 1. Chart (Top)
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.canvas.updateGeometry()
        vbox.addWidget(self.canvas)

        # 2. Controls (Bottom)
        hbox_controls = QtWidgets.QHBoxLayout()
        vbox.addLayout(hbox_controls)

        hbox_controls.addWidget(QtWidgets.QLabel("Display values as:"))

        self.cbo_value_type = QtWidgets.QComboBox()
        self.cbo_value_type.addItems([
            "Absolute",
            "Relative to Minimum",
            "Relative to Maximum",
            "Relative to Mean"
        ])
        hbox_controls.addWidget(self.cbo_value_type)

        self.btn_units = QtWidgets.QPushButton("Units")
        hbox_controls.addWidget(self.btn_units)

        hbox_controls.addItem(QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))

        self.btn_chart_options = QtWidgets.QPushButton("Chart Options")
        self.btn_chart_options.setToolTip("Chart Options")
        hbox_controls.addWidget(self.btn_chart_options)
        self.setup_chart_options_menu()
        
        hbox_controls.addSpacing(10)

        self.btn_export = QtWidgets.QPushButton("Export")
        hbox_controls.addWidget(self.btn_export)
        self.setup_export_menu()
        
    def setup_chart_options_menu(self):
        self.chart_options_menu = QtWidgets.QMenu(self)

        self.action_set_font = QtWidgets.QAction("Set Chart Font", self)
        self.action_set_font.triggered.connect(self.set_chart_font)
        self.chart_options_menu.addAction(self.action_set_font)
        
        self.chart_options_menu.addSeparator()

        self.action_chk_uncertainty = QtWidgets.QAction("Show Uncertainty", self)
        self.action_chk_uncertainty.setCheckable(True)
        self.action_chk_uncertainty.setChecked(False)
        self.action_chk_uncertainty.triggered.connect(self.chart_needs_update.emit)
        self.chart_options_menu.addAction(self.action_chk_uncertainty)

        self.action_chk_trendline = QtWidgets.QAction("Show Trendline", self)
        self.action_chk_trendline.setCheckable(True)
        self.action_chk_trendline.setChecked(False)
        self.action_chk_trendline.triggered.connect(self.chart_needs_update.emit)
        self.chart_options_menu.addAction(self.action_chk_trendline)

        self.btn_chart_options.setMenu(self.chart_options_menu)

    def setup_export_menu(self):
        self.export_menu = QtWidgets.QMenu(self)

        self.action_export_values = QtWidgets.QAction("Export Values...", self)
        self.action_export_values.triggered.connect(self.export_values)
        self.export_menu.addAction(self.action_export_values)

        self.action_export_chart = QtWidgets.QAction("Export Chart Image...", self)
        self.action_export_chart.triggered.connect(self.export_chart)
        self.export_menu.addAction(self.action_export_chart)

        self.btn_export.setMenu(self.export_menu)

    def export_values(self):
        # We need the current data points displayed on the chart
        # We can reconstruct them from self.last_plot_data if we store it in render_plot
        # Or we can just access them from the current plot if possible, but safer to store
        if not hasattr(self, 'last_plot_data') or not self.last_plot_data:
            QtWidgets.QMessageBox.information(self, "Export", "No data to export.")
            return

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Values", "", 
            "CSV Files (*.csv);;Excel Files (*.xlsx);;JSON Files (*.json)"
        )
        
        if not filename:
            return
            
        x_labels = self.last_plot_data['x']
        y_values = self.last_plot_data['y']
        y_err = self.last_plot_data['err']
        ylabel = self.last_plot_data['ylabel']
        
        # Create a memory layer for export (no geometry)
        vl = QgsVectorLayer("None", "AnalysisData", "memory")
        pr = vl.dataProvider()
        
        # Add attributes
        pr.addAttributes([
            QgsField("Event", QVariant.String),
            QgsField("Value", QVariant.Double),
            QgsField("Unit", QVariant.String),
            QgsField("Uncertainty", QVariant.Double)
        ])
        vl.updateFields()
        
        feats = []
        for i, label in enumerate(x_labels):
            val = y_values[i]
            if val is None: continue
            
            err = y_err[i] if y_err and i < len(y_err) else 0.0
            
            fet = QgsFeature()
            fet.setAttributes([label, float(val), ylabel, float(err)])
            feats.append(fet)
            
        pr.addFeatures(feats)
        vl.updateExtents()
        
        # Determine format/driver based on extension
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.fileEncoding = "UTF-8"
        options.driverName = "CSV" 
        if filename.lower().endswith(".xlsx"):
            options.driverName = "XLSX"
        elif filename.lower().endswith(".json"):
            options.driverName = "GeoJSON" # Or just JSON? GeoJSON handles attributes too

        error = QgsVectorFileWriter.writeAsVectorFormat(
            vl,
            filename,
            options
        )
        
        if error[0] == QgsVectorFileWriter.NoError:
             QtWidgets.QMessageBox.information(self, "Export Success", "Data exported successfully.")
        else:
             QtWidgets.QMessageBox.warning(self, "Export Error", f"Error exporting data: {error}")

    def export_chart(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Chart", "", 
            "PNG Image (*.png);;JPEG Image (*.jpg);;SVG Image (*.svg);;PDF Document (*.pdf)"
        )
        if filename:
            try:
                self.fig.savefig(filename)
                QtWidgets.QMessageBox.information(self, "Export Success", "Chart exported successfully.")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Export Error", f"Error exporting chart: {e}")

    def set_chart_font(self):
        font, ok = QtWidgets.QFontDialog.getFont(self.chart_font, self, 'Select Chart Font')
        if ok:
            self.chart_font = font
            self.chart_needs_update.emit()

    def setup_units_menu(self):
        self.units_menu = QtWidgets.QMenu(self)

        dist_menu = self.units_menu.addMenu('Distance')
        self.dist_actions = {}
        ag_dist = QtWidgets.QActionGroup(self)
        for unit_name in distance_units.keys():
            action = QtWidgets.QAction(unit_name, self)
            action.setCheckable(True)
            action.setData(unit_name)
            action.triggered.connect(lambda checked, t='distance', u=unit_name: self.update_unit(t, u))
            dist_menu.addAction(action)
            ag_dist.addAction(action)
            self.dist_actions[unit_name] = action

        area_menu = self.units_menu.addMenu('Area')
        self.area_actions = {}
        ag_area = QtWidgets.QActionGroup(self)
        for unit_name in area_units.keys():
            action = QtWidgets.QAction(unit_name, self)
            action.setCheckable(True)
            action.setData(unit_name)
            action.triggered.connect(lambda checked, t='area', u=unit_name: self.update_unit(t, u))
            area_menu.addAction(action)
            ag_area.addAction(action)
            self.area_actions[unit_name] = action

        ratio_menu = self.units_menu.addMenu('Ratio')
        self.ratio_actions = {}
        ag_ratio = QtWidgets.QActionGroup(self)
        for unit_name in ratio_units.keys():
            action = QtWidgets.QAction(unit_name, self)
            action.setCheckable(True)
            action.setData(unit_name)
            action.triggered.connect(lambda checked, t='ratio', u=unit_name: self.update_unit(t, u))
            ratio_menu.addAction(action)
            ag_ratio.addAction(action)
            self.ratio_actions[unit_name] = action

        self.btn_units.setMenu(self.units_menu)
        self.units_menu.aboutToShow.connect(self.update_menu_state)

    def update_menu_state(self):
        if not self.analysis or not hasattr(self.analysis, 'units'):
            return

        current_dist = self.analysis.units.get('distance')
        if current_dist in self.dist_actions:
            self.dist_actions[current_dist].setChecked(True)

        current_area = self.analysis.units.get('area')
        if current_area in self.area_actions:
            self.area_actions[current_area].setChecked(True)

        current_ratio = self.analysis.units.get('ratio')
        if current_ratio in self.ratio_actions:
            self.ratio_actions[current_ratio].setChecked(True)

    def update_unit(self, unit_type, unit_name):
        if self.analysis and hasattr(self.analysis, 'units'):
            self.analysis.units[unit_type] = unit_name
            self.chart_needs_update.emit()
            
    def render_plot(self, x_labels, y_values, y_err, ylabel, val_type, metric_name=None, metric_values=None):
        self.ax.clear()

        # Set font properties
        font_family = self.chart_font.family() if self.chart_font else "Sans Serif"
        font_size = self.chart_font.pointSize() if self.chart_font else 10

        if metric_name:
            if val_type == "Absolute":
                self.ax.set_title(metric_name, fontsize=font_size, fontname=font_family)
            else:
                self.ax.set_title(f"{metric_name}\n{val_type}", fontsize=font_size, fontname=font_family)
        else:
            self.ax.set_title(val_type, fontsize=font_size, fontname=font_family)
        
        # Determine baseline for relative calculations before filtering None values, 
        # but only if absolute values are present. 
        # Actually, relative calculations depend on displayed points mostly, 
        # but if we want to show gaps, we need to handle None.
        # For simplicity, let's keep None as None in y_values and filter during plotting but keep indices logic consistent.
        
        # BUT the requirement is "DCE's ... displayed ... even if no value".
        # So we should NOT filter out indices from x_labels.
        # Matplotlib plot() handles NaNs by breaking the line, or not plotting the point.
        # We need to convert None to np.nan for matplotlib.
        
        y_float = [float(v) if v is not None else np.nan for v in y_values]
        
        # Calculate baseline from VALID values
        valid_values = [v for v in y_float if not np.isnan(v)]
        x_indices = range(len(x_labels))

        if not valid_values:
            # Even if no data, we want to show axis labels
            self.ax.text(0.5, 0.5, "No data available", ha='center', va='center', fontsize=font_size, fontname=font_family)
            self.ax.set_xticks(x_indices)
            wrapped_labels = [textwrap.fill(lbl, width=15) for lbl in x_labels]
            self.ax.set_xticklabels(wrapped_labels, rotation=45, ha='right', fontsize=font_size*0.8, fontname=font_family)
            self.canvas.draw()
            return
            
        # Apply normalization
        y_plot = []
        if val_type == "Relative to Minimum":
            baseline = min(valid_values)
            y_plot = [v - baseline if not np.isnan(v) else np.nan for v in y_float]
        elif val_type == "Relative to Maximum":
            baseline = max(valid_values)
            y_plot = [v - baseline if not np.isnan(v) else np.nan for v in y_float]
        elif val_type == "Relative to Mean":
            baseline = sum(valid_values) / len(valid_values)
            y_plot = [v - baseline if not np.isnan(v) else np.nan for v in y_float]
        else: # Absolute
            y_plot = y_float

        # Handle errors
        y_err_plot = [e if e is not None else 0.0 for e in y_err] if y_err else [0.0]*len(y_plot)

        x_indices = range(len(x_labels))
        
        # Store data for export (all items)
        self.last_plot_data = {
            'x': x_labels,
            'y': y_plot,
            'err': y_err,
            'ylabel': ylabel
        }
        
        # Store for picking
        self.metric_points = [] # Store tuples of (x_idx, y_val, metric_data)
        if metric_values and len(metric_values) == len(y_plot):
             for i, y in enumerate(y_plot):
                 if np.isfinite(y) and metric_values[i]:
                      self.metric_points.append({
                          'x': i,
                          'y': y,
                          'data': metric_values[i]
                      })

           
        mask = np.isfinite(y_plot)
        if np.any(mask):
            self.ax.errorbar(np.array(x_indices)[mask], np.array(y_plot)[mask], 
                            yerr=np.array(y_err_plot)[mask] if y_err else None, 
                            fmt='o', capsize=5, ecolor='red')

        # Trendline - only use valid points
        if getattr(self, "action_chk_trendline", None) and self.action_chk_trendline.isChecked():
            mask = np.isfinite(y_plot)
            if np.sum(mask) > 1:
                x_valid = np.array(x_indices)[mask]
                y_valid = np.array(y_plot)[mask]
                
                # Plot connected line instead of regression
                self.ax.plot(x_valid, y_valid, "b--", alpha=0.8, linewidth=0.8)
            
        self.ax.set_xticks(x_indices)
        
        # Use wrap formatting logic to ensure long DCE names don't overlap heavily
        wrapped_labels = [textwrap.fill(lbl, width=15) for lbl in x_labels]
        
        self.ax.set_xticklabels(wrapped_labels, rotation=45, ha='right', fontsize=font_size*0.8, fontname=font_family)
        self.ax.set_ylabel(ylabel, fontsize=font_size, fontname=font_family)
        
        # Set tick label font
        for tick in self.ax.get_xticklabels() + self.ax.get_yticklabels():
            tick.set_fontname(font_family)
            if tick in self.ax.get_yticklabels():
                tick.set_fontsize(font_size)

        self.fig.tight_layout(pad=2.0)
        
        self.canvas.draw()

    def on_click(self, event):
        if not event.dblclick or event.inaxes != self.ax:
            return

        if not hasattr(self, 'metric_points') or not self.metric_points:
            return
            
        click_x, click_y = event.x, event.y
        closest_dist = float('inf')
        closest_point = None
        
        # Transform points to display coordinates for distance check
        for pt in self.metric_points:
            try:
                # transData takes (x, y) in data coordinates and returns (x, y) in display coordinates
                display_pt = self.ax.transData.transform((pt['x'], pt['y']))
                dist = np.hypot(click_x - display_pt[0], click_y - display_pt[1])
                
                if dist < closest_dist:
                    closest_dist = dist
                    closest_point = pt
            except:
                continue
                
        # Threshold in pixels (e.g. 10 pixels radius)
        if closest_point and closest_dist < 10:
            self.metric_data_clicked.emit(closest_point['data'])

