import re
import json
import sqlite3
import xml.etree.ElementTree as ET

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from qgis.PyQt import QtWidgets, QtCore, QtGui
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsVectorLayer, 
    QgsProject, 
    QgsCoordinateTransform, 
    Qgis, 
    QgsMessageLog, 
    QgsDistanceArea, 
    QgsGeometry, 
    QgsFeatureRequest
)

from ...model.project import Project
from ...model.event import DCE_EVENT_TYPE_ID, DESIGN_EVENT_TYPE_ID, AS_BUILT_EVENT_TYPE_ID
from ...model.sample_frame import SampleFrame
from .chart_export_widget import ChartExportWidget

class DistributionAnalysisWidget(QtWidgets.QWidget):
    """
    Shared widget for Distribution Analysis (used in DockWidget and Dialog).
    Layout: Horizontal Split (Left=Inputs, Right=Chart)
    """

    def __init__(self, iface, qris_project: Project, map_manager, parent=None, orientation=QtCore.Qt.Horizontal):
        super().__init__(parent)
        self.setObjectName("DistributionAnalysisWidget")
        self.iface = iface
        self.qris_project = qris_project
        self.map_manager = map_manager
        self.orientation = orientation
        
        self.unit_factor = 1.0
        self.unit_label = ""
        self.active_scope_layer = None
        self.active_event_layer = None
        self.current_distribution_data = None
        self.current_attribute_feature_counts = {}
        self.attribute_sort_mode = "alpha"
        
        # Chart Settings
        self.chart_font_family = "Sans Serif"
        self.chart_font_size = 10
        self.chart_font = QtGui.QFont(self.chart_font_family, self.chart_font_size)
        
        self.chart_show_pct = False
        self.chart_pct_basis = 'mapped'

        self.setupUi()
        
        # Initial Population must happen after UI setup
        if self.qris_project:
            self.populate_scope()
            self.populate_dce()

    def setupUi(self):
        # Main Layout
        self.splitter = None
        if self.orientation == QtCore.Qt.Horizontal:
            self.main_layout = QtWidgets.QHBoxLayout(self)
            self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
            self.main_layout.addWidget(self.splitter)
        else:
            self.main_layout = QtWidgets.QVBoxLayout(self)
        
        # --- Left Side: Inputs ---
        self.input_container = QtWidgets.QWidget()
        if self.orientation == QtCore.Qt.Horizontal:
            self.input_container.setMinimumWidth(300)
            
        # Use a QVBox for the left side to allow pushing items to top
        self.left_layout = QtWidgets.QVBoxLayout(self.input_container)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabs
        self.tabs = QtWidgets.QTabWidget()
        self.left_layout.addWidget(self.tabs)

        # Tab 1: Chart Inputs
        self.tab_inputs = QtWidgets.QWidget()
        self.layout_inputs = QtWidgets.QVBoxLayout(self.tab_inputs)
        self.layout_inputs.setContentsMargins(5, 5, 5, 5)

        # Tab 2: Attributes
        self.tab_attributes = QtWidgets.QWidget()
        self.layout_attributes = QtWidgets.QVBoxLayout(self.tab_attributes)
        self.layout_attributes.setContentsMargins(5, 5, 5, 5)
        
        self.lstAttributes = QtWidgets.QListWidget()
        self.lstAttributes.itemChanged.connect(self.on_attributes_changed)
        self.layout_attributes.addWidget(self.lstAttributes)

        # Attribute Selection Buttons
        self.hbox_attr_buttons = QtWidgets.QHBoxLayout()
        self.hbox_attr_buttons.setSpacing(6)

        self.btnSortAlpha = QtWidgets.QPushButton("Sort Alphabetical (A-Z)")
        self.btnSortAlpha.clicked.connect(self.sort_attributes_alphabetical)
        self.btnSortByCount = QtWidgets.QPushButton("Sort By Feature Count (Desc.)")
        self.btnSortByCount.clicked.connect(self.sort_attributes_by_count_desc)
        self.hbox_attr_buttons.addWidget(self.btnSortAlpha)
        self.hbox_attr_buttons.addWidget(self.btnSortByCount)

        self.hbox_attr_buttons.addStretch() # Keep sort buttons left and select buttons right
        
        self.btnSelectNonEmpty = QtWidgets.QPushButton("Select Non-Empty")
        self.btnSelectNonEmpty.clicked.connect(self.select_non_empty_attributes)
        self.btnSelectAll = QtWidgets.QPushButton("Select All")
        self.btnSelectAll.clicked.connect(self.select_all_attributes)
        self.btnSelectNone = QtWidgets.QPushButton("Select None")
        self.btnSelectNone.clicked.connect(self.select_none_attributes)
        self.hbox_attr_buttons.addWidget(self.btnSelectNonEmpty)
        self.hbox_attr_buttons.addWidget(self.btnSelectAll)
        self.hbox_attr_buttons.addWidget(self.btnSelectNone)
        self.layout_attributes.addLayout(self.hbox_attr_buttons)
        
        self.tabs.addTab(self.tab_inputs, "Chart Inputs")
        self.tabs.addTab(self.tab_attributes, "Attributes")

        # Form Layout for fields
        self.form_layout = QtWidgets.QFormLayout()
        
        # Line 1: Scope (Sample Frame, AOI, or Riverscape)
        self.scope_label = QtWidgets.QLabel("Analysis Mask:")
        self.cmbScope = QtWidgets.QComboBox()
        self.cmbScope.currentIndexChanged.connect(self.on_scope_changed)
        self.form_layout.addRow(self.scope_label, self.cmbScope)
        
        # Line 2: Scope Features
        self.scope_features_label = QtWidgets.QLabel("Mask Feature:")
        self.cmbScopeFeatures = QtWidgets.QComboBox()
        self.cmbScopeFeatures.currentIndexChanged.connect(self.calculate_distribution)
        self.cmbScopeFeatures.currentIndexChanged.connect(self.update_map)
        self.form_layout.addRow(self.scope_features_label, self.cmbScopeFeatures)
        
        # Line 3: DCE/Design/As-Built
        self.dce_label = QtWidgets.QLabel("Event:")
        self.cmbDCE = QtWidgets.QComboBox()
        self.cmbDCE.currentIndexChanged.connect(self.on_dce_changed)
        self.form_layout.addRow(self.dce_label, self.cmbDCE)
        
        # Line 4: Layer
        self.layer_label = QtWidgets.QLabel("Event Layer:")
        self.cmbLayer = QtWidgets.QComboBox()
        self.cmbLayer.currentIndexChanged.connect(self.on_layer_changed)
        self.form_layout.addRow(self.layer_label, self.cmbLayer)
        
        # Line 5: Measure
        self.measure_label = QtWidgets.QLabel("Measure:")
        self.cmbMeasure = QtWidgets.QComboBox()
        self.cmbMeasure.addItem("Geometry (Area/Length)", "geometry")
        self.cmbMeasure.addItem("Feature Count", "count")
        self.cmbMeasure.addItem("Percent of Sample Frame", "percent_scope")
        self.cmbMeasure.addItem("Percent of Total Mapped", "percent_total")
        self.cmbMeasure.currentIndexChanged.connect(self.calculate_distribution)
        self.form_layout.addRow(self.measure_label, self.cmbMeasure)

        # Line 6: Metric (Categorical Attributes)
        self.metric_label = QtWidgets.QLabel("Attribute/Metric:")
        self.cmbMetric = QtWidgets.QComboBox()
        self.cmbMetric.currentIndexChanged.connect(self.calculate_distribution)
        self.form_layout.addRow(self.metric_label, self.cmbMetric)
        
        # Interactive Map Checkbox
        self.chkInteractive = QtWidgets.QCheckBox("Interactive Map")
        # Checked by default only for horizontal (dock) layout
        self.chkInteractive.setChecked(self.orientation == QtCore.Qt.Horizontal)
        self.chkInteractive.stateChanged.connect(self.toggle_interactive)
        
        # Hide for Vertical layout (Dialog)
        if self.orientation != QtCore.Qt.Horizontal:
            self.chkInteractive.setVisible(False)
            
        self.form_layout.addRow("", self.chkInteractive)
        
        self.layout_inputs.addLayout(self.form_layout)
        if self.orientation == QtCore.Qt.Horizontal:
            self.layout_inputs.addStretch() # Push inputs to top
        
        if self.splitter:
            self.splitter.addWidget(self.input_container)
        else:
            self.main_layout.addWidget(self.input_container)

        # --- Right Side: Chart ---
        self.chart_container = QtWidgets.QWidget()
        self.chart_layout = QtWidgets.QVBoxLayout(self.chart_container)
        self.chart_layout.setContentsMargins(0, 0, 0, 0)
        
        self.chart_label = QtWidgets.QLabel("Distribution Summary:")
        self.chart_layout.addWidget(self.chart_label)
        
        # Matplotlib Figure and Canvas
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(200)
        self.chart_layout.addWidget(self.canvas)

        # Chart Controls
        self.hbox_bottom = QtWidgets.QHBoxLayout()
        
        self.chart_type_label = QtWidgets.QLabel("Chart Type:")
        self.hbox_bottom.addWidget(self.chart_type_label)
        
        self.cmbChartType = QtWidgets.QComboBox()
        self.cmbChartType.addItem("Horizontal Bar", "horizontal")
        self.cmbChartType.addItem("Stacked Bar", "stacked")
        self.cmbChartType.currentIndexChanged.connect(self.draw_chart)
        self.hbox_bottom.addWidget(self.cmbChartType)
        
        # Chart Options Button
        self.btnChartOptions = QtWidgets.QToolButton()
        self.btnChartOptions.setText("Settings")
        self.btnChartOptions.setToolTip("Customize Chart Font")
        self.btnChartOptions.clicked.connect(self.show_chart_options)
        self.hbox_bottom.addWidget(self.btnChartOptions)
        
        self.hbox_bottom.addSpacing(10)
        
        self.btnUnits = QtWidgets.QToolButton()
        self.btnUnits.setText("Units")
        self.btnUnits.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.hbox_bottom.addWidget(self.btnUnits)
        
        self.hbox_bottom.addItem(QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        
        # Add Export Widget
        self.export_widget = ChartExportWidget(
            self,
            base_name="DistributionAnalysis",
            get_data_callback=self.get_export_data,
            get_figure_callback=lambda: self.figure,
            project_path=self.qris_project.project_file if self.qris_project else None
        )
        self.hbox_bottom.addWidget(self.export_widget)
        
        self.chart_layout.addLayout(self.hbox_bottom)
        
        if self.splitter:
            self.splitter.addWidget(self.chart_container)
            self.splitter.setStretchFactor(1, 1) # Give chart all remaining space
        else:
            self.main_layout.addWidget(self.chart_container, 1) # Give chart all remaining space
        
        self.main_layout.addWidget(self.chart_container, 1) # Give chart all remaining space
    
    def populate_scope(self):
        self.cmbScope.clear()
        
        # Add Valley Bottoms
        for vb in self.qris_project.valley_bottoms.values():
            self.cmbScope.addItem(f"Valley Bottom: {vb.name}", vb)
            
        # Add AOIs
        for aoi in self.qris_project.aois.values():
             self.cmbScope.addItem(f"AOI: {aoi.name}", aoi)
             
        # Add Sample Frames
        for sf in self.qris_project.sample_frames.values():
            self.cmbScope.addItem(f"Sample Frame: {sf.name}", sf)
            
        if self.cmbScope.count() > 0:
            self.on_scope_changed()

    def on_scope_changed(self):
        self.cmbScopeFeatures.blockSignals(True)
        self.cmbScopeFeatures.clear()
        selected_scope = self.cmbScope.currentData()
        
        self.cmbScopeFeatures.addItem("All Features", None)
        
        if selected_scope:
            features = self.get_scope_features(selected_scope)
            for name, fid in features:
                self.cmbScopeFeatures.addItem(str(name), fid)
        
        self.cmbScopeFeatures.blockSignals(False)
        self.calculate_distribution()
        self.update_map()
    
    def get_scope_features(self, scope_item):
        features = []
        if isinstance(scope_item, SampleFrame):
            
            try:
                # All scopes (VB, AOI, SF) are SampleFrame instances in QRiS model
                # and share sample_frame_features table
                with sqlite3.connect(self.qris_project.project_file) as conn:
                    # Enable row factory to access columns by name
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    table_name = 'sample_frame_features'
                    fk_col = 'sample_frame_id'
                    
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    # Determine Name Column
                    if 'display_label' in columns:
                        name_col = 'display_label'
                    elif 'name' in columns:
                        name_col = 'name'
                    else:
                        name_col = 'fid' # Fallback
                        
                    # Determine ID Column
                    id_col = 'fid' if 'fid' in columns else 'id'
                    
                    query = f"SELECT {name_col}, {id_col} FROM {table_name} WHERE {fk_col} = ?"
                    cursor.execute(query, (scope_item.id,))
                    
                    # Fetch and process
                    rows = cursor.fetchall()
                    for row in rows:
                        features.append((row[0], row[1]))
                    
            except Exception as e:
                QgsMessageLog.logMessage(f"Error loading scope features: {e}", 'QRiS', Qgis.Warning)
                
        return features

    def populate_dce(self):
        self.cmbDCE.clear()
        
        # Events to include: DCE (1), Design, As-Built
        # Using constants from imports
        event_types = [DCE_EVENT_TYPE_ID, DESIGN_EVENT_TYPE_ID, AS_BUILT_EVENT_TYPE_ID]
        
        sorted_events = sorted(self.qris_project.events.values(), key=lambda x: x.name)
        
        for event in sorted_events:
            if event.event_type.id in event_types:
                type_name = event.event_type.name if event.event_type else "Unknown"
                self.cmbDCE.addItem(f"{event.name} ({type_name})", event)
                
        if self.cmbDCE.count() > 0:
            self.on_dce_changed()

    def on_dce_changed(self):
        self.cmbLayer.clear()
        selected_event = self.cmbDCE.currentData()
        
        if not selected_event:
            return
            
        # event.event_layers is a list of EventLayer objects
        for evt_layer in selected_event.event_layers:
            # Maybe filter out lookup tables?
            if not evt_layer.layer.is_lookup:
               self.cmbLayer.addItem(evt_layer.name, evt_layer)
               
        if self.cmbLayer.count() > 0:
            self.on_layer_changed()

    def on_layer_changed(self):
        self.cmbMetric.clear()
        selected_layer = self.cmbLayer.currentData()
        
        if not selected_layer:
            return
            
        # Update Calculate Option Label based on Geometry
        geom_type = selected_layer.layer.geom_type
        idx = self.cmbMeasure.findData("geometry")
        if idx >= 0:
            if geom_type == 'Linestring':
                self.cmbMeasure.setItemText(idx, "Geometry (Length)")
            elif geom_type == 'Point':
                self.cmbMeasure.setItemText(idx, "Geometry (Count)")
            else:
                self.cmbMeasure.setItemText(idx, "Geometry (Area)")

        # populate categorical attributes from metadata
        # layer.metadata['fields'] contains field definitions
        # Look for fields that are strings or have lookups
        
        fields = selected_layer.layer.metadata.get('fields', [])
        for field in fields:
            # Field ID can be 'id' or 'machine_code' depending on data version
            f_id = field.get('id', field.get('machine_code'))
            if not f_id:
                continue
                
            f_type = field.get('type', '').lower()
            f_label = field.get('label', f_id)
            
            # Heuristic for categorical attributes:
            # 1. Type contains 'text' or 'string'
            # 2. Type is 'list' (e.g. drop down)
            # 3. Has 'lookup' or 'values' defined
            # 4. Explicit widget definition
            is_categorical = (
                'text' in f_type or 
                'string' in f_type or
                f_type == 'list' or
                'lookup' in field or 
                'values' in field or
                field.get('widget') == 'value_map'
            )
            
            if is_categorical:
                self.cmbMetric.addItem(f_label, f_id)
                
        self.update_units_menu()

        if self.cmbMetric.count() > 0:
            self.calculate_distribution()
            
        self.update_map()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_distribution_data:
            self.draw_chart()

    def show_chart_options(self):
        # Determine if current layer allows scope basis (Polygon)
        is_polygon = False
        if self.current_distribution_data:
            # distribution, total, event_layer, metric, scope_measure
            event_layer = self.current_distribution_data[2]
            if hasattr(event_layer.layer, 'geom_type'):
                g_type = event_layer.layer.geom_type
                is_polygon = 'Polygon' in g_type
            
        dlg = ChartSettingsDialog(self, self.chart_font, self.chart_show_pct, self.chart_pct_basis, is_polygon)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            settings = dlg.get_settings()
            self.chart_font = settings['font']
            self.chart_font_family = self.chart_font.family()
            self.chart_font_size = self.chart_font.pointSize()
            self.chart_show_pct = settings['show_pct']
            self.chart_pct_basis = settings['pct_basis']
            
            self.draw_chart()

    def update_units_menu(self):
        selected_layer = self.cmbLayer.currentData()
        if not selected_layer:
            return
            
        geom_type = selected_layer.layer.geom_type
        
        menu = QtWidgets.QMenu(self.btnUnits)
        
        # Define factor relative to base unit (Meters or Sq Meters)
        units = []
        if geom_type == 'Linestring':
            units = [
                ("Meters (m)", 1.0, "m"),
                ("Kilometers (km)", 0.001, "km"),
                ("Feet (ft)", 3.28084, "ft"),
                ("Miles (mi)", 0.000621371, "mi")
            ]
        elif geom_type == 'Polygon':
            units = [
                ("Sq Meters (m²)", 1.0, "m²"),
                ("Sq Kilometers (km²)", 1e-6, "km²"),
                ("Hectares (ha)", 0.0001, "ha"),
                ("Sq Feet (ft²)", 10.7639, "ft²"),
                ("Acres (ac)", 0.000247105, "ac"),
                ("Sq Miles (mi²)", 3.861e-7, "mi²")
            ]
        else:
             units = [("Count", 1.0, "")]
             
        for name, factor, label in units:
            action = menu.addAction(name)
            action.triggered.connect(lambda checked, f=factor, l=label: self.set_unit(f, l))
            
        self.btnUnits.setMenu(menu)
        
        # Set default
        if units:
            self.unit_factor = units[0][1]
            self.unit_label = units[0][2]
            
    def set_unit(self, factor, label):
        self.unit_factor = factor
        self.unit_label = label
        self.btnUnits.setText(f"Units: {label}")
        self.draw_chart()

    def toggle_interactive(self):
        # If interactive mode is turned off, remove active layers and clean empty groups.
        if not self.chkInteractive.isChecked():
            self.cleanup_interactive_layers()

        self.update_map()

    def cleanup_interactive_layers(self):
        project = QgsProject.instance()

        for layer in [self.active_scope_layer, self.active_event_layer]:
            if layer and layer.id() in project.mapLayers():
                node = project.layerTreeRoot().findLayer(layer.id())
                parent_grp = node.parent() if node else None
                project.removeMapLayer(layer.id())
                if parent_grp and self.map_manager and hasattr(self.map_manager, 'remove_empty_groups'):
                    self.map_manager.remove_empty_groups(parent_grp)

        self.active_scope_layer = None
        self.active_event_layer = None

    def hideEvent(self, event):
        # Ensure transient interactive map layers/groups are removed when widget is hidden.
        self.cleanup_interactive_layers()
        super().hideEvent(event)

    def closeEvent(self, event):
        # Ensure transient interactive map layers/groups are removed when widget is closed.
        self.cleanup_interactive_layers()
        super().closeEvent(event)

    def update_map(self):
        # Allow enabling/disabling via checkbox
        if not self.chkInteractive.isChecked():
            return

        if not self.iface:
            return

        project = QgsProject.instance()

        # Helper method for layer cleanup
        def remove_layer_and_clean(layer):
            if layer and layer.id() in project.mapLayers():
                node = project.layerTreeRoot().findLayer(layer.id())
                parent_grp = None
                if node:
                    parent_grp = node.parent()
                
                project.removeMapLayer(layer.id())
                
                if parent_grp:
                    # Remove any now-empty parent/ancestor groups for layers added by map_manager.
                    if self.map_manager and hasattr(self.map_manager, 'remove_empty_groups'):
                        self.map_manager.remove_empty_groups(parent_grp)
        
        # Handle Scope Layer
        scope_item = self.cmbScope.currentData()
        if scope_item:
            # Determine appropriate build method
            layer = None
            if isinstance(scope_item, SampleFrame):
                if scope_item.sample_frame_type == SampleFrame.AOI_SAMPLE_FRAME_TYPE:
                    layer = self.map_manager.build_aoi_layer(scope_item)
                elif scope_item.sample_frame_type == SampleFrame.VALLEY_BOTTOM_SAMPLE_FRAME_TYPE:
                    # Assuming there's a valley bottom builder or we use the sample frame one
                    # Usually just sample frame layer but with VB filter?
                     # Map manager logic not fully visible but assuming build_sample_frame_layer exists or similar
                     layer = self.map_manager.build_sample_frame_layer(scope_item)
                else:
                    layer = self.map_manager.build_sample_frame_layer(scope_item)
            
            # If we switched scopes, remove the old one IF it's different and exists
            if self.active_scope_layer and layer and self.active_scope_layer.id() != layer.id():
                remove_layer_and_clean(self.active_scope_layer)
            
            self.active_scope_layer = layer
            
            # Zoom to Mask (Scope) Feature Extent
            scope_feature_id = self.cmbScopeFeatures.currentData()
            extent = None
            
            if self.active_scope_layer:
                if scope_feature_id:
                    # Zoom to specific feature
                    feat = self.active_scope_layer.getFeature(scope_feature_id)
                    if feat.isValid():
                        extent = feat.geometry().boundingBox()
                else:
                    # Zoom to layer
                    extent = self.active_scope_layer.extent()
            
            if extent and not extent.isEmpty():
                canvas = self.iface.mapCanvas()
                
                # Check for CRS mismatch
                if self.active_scope_layer.crs() != canvas.mapSettings().destinationCrs():
                     xform = QgsCoordinateTransform(self.active_scope_layer.crs(), canvas.mapSettings().destinationCrs(), QgsProject.instance())
                     extent = xform.transformBoundingBox(extent)

                # Expand slightly to prevent tight fit
                extent.scale(1.1)
                canvas.setExtent(extent)
                canvas.refresh()
        
        # Handle Event Layer
        event_layer_item = self.cmbLayer.currentData() # EventLayer
        event = self.cmbDCE.currentData() # Event
        
        if event and event_layer_item:
             layer = self.map_manager.build_event_single_layer(event, event_layer_item)
             
             if self.active_event_layer and layer and self.active_event_layer.id() != layer.id():
                 remove_layer_and_clean(self.active_event_layer)
                 
             self.active_event_layer = layer

    def get_export_data(self):
        if not self.current_distribution_data:
             return None

        # Unpack with backward compatibility
        data = self.current_distribution_data
        
        distribution = {}
        total_mapped = 0
        event_layer = None
        metric_field = None
        scope_measure = 0
        measure_type = 'count'
        
        if len(data) >= 6:
            distribution, total_mapped, event_layer, metric_field, scope_measure, measure_type = data[:6]
        elif len(data) == 5:
            distribution, total_mapped, event_layer, metric_field, scope_measure = data[:5]
            measure_type = 'geometry'
        else:
             if len(data) > 0: distribution = data[0]
             if len(data) > 1: total_mapped = data[1]
             scope_measure = 0
             measure_type = 'geometry'
        
        # Determine units
        unit = self.unit_label
        factor = self.unit_factor
        
        if measure_type == 'count':
            unit = "Features"
            factor = 1.0
        elif 'percent' in measure_type:
            unit = "%"
            factor = 1.0
            
        sorted_keys = sorted(distribution.keys())
        
        export_list = []
        for k in sorted_keys:
            raw_val = distribution[k]
            
            val = 0.0
            if measure_type == 'percent_scope' and scope_measure > 0:
                 val = (raw_val / scope_measure) * 100
            elif measure_type == 'percent_total' and total_mapped > 0:
                 val = (raw_val / total_mapped) * 100
            else:
                 val = raw_val * factor

            pct = (raw_val / total_mapped * 100) if total_mapped > 0 else 0.0
            
            export_list.append({
                "Category": k,
                "Value": float(val),
                "Unit": unit,
                "Percentage": float(pct)
            })
            
        return export_list

    def get_layer_colors(self, event_layer_item, attribute_name):
        colors = {}

        if not self.map_manager:
            return colors

        qml_path = self.map_manager.get_symbology_qml(event_layer_item.layer.qml)
        if not qml_path or not QtCore.QFile.exists(qml_path):
            return colors

        def parse_qgis_color(value_str):
            """Parse a QGIS color string to QColor. Handles three formats:
              - "R,G,B,A"  (QGIS 3 mid-era, e.g. "43,131,186,255")
              - "R,G,B,A,rgb:r,g,b,a"  (QGIS 3 newer, extended form)
              - legacy prop format "R,G,B,A" from <prop k="color"> elements
            Returns QColor or None if not parseable or fully transparent."""
            # Strip any trailing rgb:/hsv: extended portion (starts after the 4th comma)
            raw = value_str.split('rgb:')[0].split('hsv:')[0].split('hsl:')[0].rstrip(',')
            parts = raw.split(',')
            if len(parts) >= 4:
                try:
                    r, g, b, a = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
                    if a > 0:
                        return QtGui.QColor(r, g, b, a)
                except (ValueError, IndexError):
                    pass
            return None

        try:
            tree = ET.parse(qml_path)
            qml_root = tree.getroot()

            renderer_el = qml_root.find('.//renderer-v2')
            if renderer_el is None:
                return colors

            renderer_type = renderer_el.get('type')

            # Build symbol id -> QColor map from the <symbols> block.
            # Each symbol has stacked marker/line/fill layers; layers may be transparent
            # placeholders. We search only within the direct <Option type="Map"> properties
            # block of each layer — NOT recursively — to avoid picking up colors from effects
            # or data_defined_properties sub-elements.
            # Two sub-formats exist across QGIS versions:
            #   Modern:  layer > <Option type="Map"> > <Option name="color" value="R,G,B,A[,rgb:...]"/>
            #   Legacy:  layer > <prop k="color" v="R,G,B,A"/>

            def layer_prop_color(layer_el, key):
                """Return parse_qgis_color for `key` from a layer's direct property Map.
                Checks modern <Option type="Map"> children first, then legacy <prop> elements.
                Returns None if not found or fully transparent."""
                opt_map = layer_el.find('Option[@type="Map"]')
                if opt_map is not None:
                    opt = opt_map.find(f'Option[@name="{key}"]')
                    if opt is not None:
                        return parse_qgis_color(opt.get('value', ''))
                for prop in layer_el.findall('prop'):
                    if prop.get('k') == key:
                        return parse_qgis_color(prop.get('v', ''))
                return None

            symbol_colors = {}
            for sym_el in renderer_el.findall('.//symbols/symbol'):
                sym_name = sym_el.get('name')
                sym_type = (sym_el.get('type') or '').lower()
                color = None

                if sym_type == 'line':
                    # Line symbols often have a wide casing layer plus a thinner colored
                    # core layer. Pick line_color from the thinnest layer so the category
                    # hue is used rather than the white/neutral casing.
                    thinnest_width = None
                    thinnest_color = None
                    for layer_el in sym_el.findall('layer'):
                        lc = layer_prop_color(layer_el, 'line_color')
                        lw_str = None
                        opt_map = layer_el.find('Option[@type="Map"]')
                        if opt_map is not None:
                            lw_opt = opt_map.find('Option[@name="line_width"]')
                            if lw_opt is not None:
                                lw_str = lw_opt.get('value')
                        if lw_str is None:
                            for prop in layer_el.findall('prop'):
                                if prop.get('k') == 'line_width':
                                    lw_str = prop.get('v')
                        if lc is not None:
                            try:
                                lw = float(lw_str) if lw_str is not None else 999999.0
                            except (TypeError, ValueError):
                                lw = 999999.0
                            if thinnest_width is None or lw < thinnest_width:
                                thinnest_width = lw
                                thinnest_color = lc
                    color = thinnest_color or layer_prop_color(sym_el.find('layer') or sym_el, 'color')

                else:
                    # Marker symbols can be composites where the first SimpleMarker color is a
                    # scaffold/stroke and the actual category color is in a later FontMarker.
                    # Prefer FontMarker color first, then fall back to first opaque layer color.
                    if sym_type == 'marker':
                        for layer_el in sym_el.findall('layer'):
                            if (layer_el.get('class') or '') == 'FontMarker':
                                color = layer_prop_color(layer_el, 'color')
                                if color:
                                    break
                    if color is None:
                        # Marker/fill fallback: first layer with opaque main color.
                        for layer_el in sym_el.findall('layer'):
                            color = layer_prop_color(layer_el, 'color')
                            if color:
                                break

                if color and sym_name is not None:
                    symbol_colors[sym_name] = color

            if renderer_type == 'categorizedSymbol':
                for cat_el in renderer_el.findall('.//categories/category'):
                    val = cat_el.get('value', '')
                    lbl = cat_el.get('label', '')
                    sym_ref = cat_el.get('symbol')
                    color = symbol_colors.get(sym_ref)
                    if color:
                        colors[val] = color
                        if lbl:
                            colors[lbl] = color

            elif renderer_type == 'singleSymbol':
                if symbol_colors:
                    colors['__default__'] = next(iter(symbol_colors.values()))

            elif renderer_type == 'RuleRenderer':
                def parse_rules(rules_el):
                    for rule_el in rules_el:
                        if rule_el.tag != 'rule':
                            continue
                        sym_ref = rule_el.get('symbol')
                        label = rule_el.get('label', '')
                        filter_expr = rule_el.get('filter', '')
                        color = symbol_colors.get(sym_ref) if sym_ref is not None else None

                        if color:
                            # Store by label (works for geomorphic-style rules where label == data value)
                            if label:
                                colors[label] = color
                            # Also extract individual string literals from the filter expression.
                            # This handles grouped rules like structure points/lines where the label
                            # is a category name (e.g. "BDA") but the filter lists all member values
                            # (e.g. "Structure Type" = 'Primary BDA' OR ... = 'Secondary BDA' OR ...)
                            for match in re.findall(r"=\s*'([^']*)'", filter_expr):
                                colors[match] = color

                        # Recurse into child rules (nested rule groups)
                        parse_rules(rule_el)

                rules_el = renderer_el.find('rules')
                if rules_el is not None:
                    parse_rules(rules_el)

        except Exception as e:
            QgsMessageLog.logMessage(f"Error parsing QML style '{qml_path}': {e}", "QRiS", Qgis.Warning)

        return colors

    def on_attributes_changed(self, item=None):
        # item parameter is passed by itemChanged signal
        self.draw_chart()

    def select_all_attributes(self):
        self.set_attributes_check_state(QtCore.Qt.Checked)

    def select_none_attributes(self):
        self.set_attributes_check_state(QtCore.Qt.Unchecked)

    def select_non_empty_attributes(self):
        self.lstAttributes.blockSignals(True)
        for i in range(self.lstAttributes.count()):
            item = self.lstAttributes.item(i)
            key = item.data(QtCore.Qt.UserRole)
            if key is None:
                key = item.text()
            feature_count = self.current_attribute_feature_counts.get(str(key), 0)
            state = QtCore.Qt.Checked if feature_count > 0 else QtCore.Qt.Unchecked
            item.setCheckState(state)
        self.lstAttributes.blockSignals(False)
        self.draw_chart()

    def set_attributes_check_state(self, state):
        self.lstAttributes.blockSignals(True)
        for i in range(self.lstAttributes.count()):
            item = self.lstAttributes.item(i)
            item.setCheckState(state)
        self.lstAttributes.blockSignals(False)
        self.draw_chart()

    def get_sorted_attribute_keys(self, keys):
        key_texts = [str(k) for k in keys]

        if self.attribute_sort_mode == "count_desc":
            return sorted(
                key_texts,
                key=lambda k: (-self.current_attribute_feature_counts.get(k, 0), k.lower())
            )

        return sorted(key_texts, key=lambda k: k.lower())

    def sort_attributes_alphabetical(self):
        self.attribute_sort_mode = "alpha"
        self.populate_attributes_list(self.current_attribute_feature_counts.keys())
        self.draw_chart()

    def sort_attributes_by_count_desc(self):
        self.attribute_sort_mode = "count_desc"
        self.populate_attributes_list(self.current_attribute_feature_counts.keys())
        self.draw_chart()

    def populate_attributes_list(self, keys):
        # Preserve unchecked state if keys persist (e.g. changing measure type)
        current_unchecked = set()
        if self.lstAttributes.count() > 0:
            for i in range(self.lstAttributes.count()):
                item = self.lstAttributes.item(i)
                if item.checkState() == QtCore.Qt.Unchecked:
                    key = item.data(QtCore.Qt.UserRole)
                    if key is None:
                        key = item.text()
                    current_unchecked.add(str(key))
        
        self.lstAttributes.blockSignals(True)
        self.lstAttributes.clear()
        
        sorted_keys = self.get_sorted_attribute_keys(keys)
        for key in sorted_keys:
            # Create Checkbox Item
            key_text = str(key)
            feature_count = self.current_attribute_feature_counts.get(key_text, 0)
            item = QtWidgets.QListWidgetItem(f"{key_text} ({feature_count})")
            item.setData(QtCore.Qt.UserRole, key_text)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            
            if key_text in current_unchecked:
                item.setCheckState(QtCore.Qt.Unchecked)
            else:
                item.setCheckState(QtCore.Qt.Checked)
            
            self.lstAttributes.addItem(item)
            
        self.lstAttributes.blockSignals(False)

    def calculate_distribution(self):
        self.figure.clear()
        
        if not self.qris_project:
             return
             
        project_path = self.qris_project.project_file

        scope = self.cmbScope.currentData()
        scope_feature_id = self.cmbScopeFeatures.currentData()
        event = self.cmbDCE.currentData()
        event_layer = self.cmbLayer.currentData()
        metric_field = self.cmbMetric.currentData()
        measure_type = self.cmbMeasure.currentData()
        
        # Log input params
        s_id = scope.id if scope else 'None'
        e_id = event.id if event else 'None'
        l_id = event_layer.layer.id if event_layer else 'None'
        m_f = metric_field if metric_field else 'None'
        QgsMessageLog.logMessage(f"Calculating Distribution: Scope={s_id}, Feature={scope_feature_id}, Event={e_id}, Layer={l_id}, Metric={m_f}", 'QRiS', Qgis.Info)

        if not (scope and event and event_layer and metric_field):
            QgsMessageLog.logMessage("Missing required inputs.", 'QRiS', Qgis.Warning)
            return
            
        # Initialize distribution with known categories (values/lookup)
        distribution = {}
        feature_counts = {}
        lookup_map = {} # ID (str) -> Label
        
        # Find field definition
        field_def = None
        for f in event_layer.layer.metadata.get('fields', []):
            f_id = f.get('id', f.get('machine_code'))
            if f_id == metric_field:
                field_def = f
                break
                
        if field_def:
            # 1. Check 'values' list (e.g. for simple dropdowns)
            if 'values' in field_def:
                for val in field_def['values']:
                    distribution[str(val)] = 0
                    feature_counts[str(val)] = 0
            
            # 2. Check 'lookup' table
            elif 'lookup' in field_def:
                lookup_name = field_def['lookup']
                if lookup_name in self.qris_project.lookup_tables:
                    # lookup_tables is dict of tables -> dict of id:DBItem
                    # We usually want the names/labels as keys
                    lkp = self.qris_project.lookup_tables[lookup_name]
                    for item in lkp.values():
                        distribution[item.name] = 0
                        feature_counts[item.name] = 0
                        # Store lookup map for value resolution
                        lookup_map[str(item.id)] = item.name
        
        # Load Scope Layer
        scope_uri = f"{project_path}|layername=sample_frame_features"
        scope_layer = QgsVectorLayer(scope_uri, "scope", "ogr")
        
        if not scope_layer.isValid():
             QgsMessageLog.logMessage("Scope layer invalid.", 'QRiS', Qgis.Critical)
             return

        scope_geom = None
        
        if scope_feature_id:
            feat = scope_layer.getFeature(scope_feature_id)
            if feat.isValid():
                scope_geom = feat.geometry()
        else:
            req = QgsFeatureRequest().setFilterExpression(f'"sample_frame_id" = {scope.id}')
            geoms = []
            try:
                for f in scope_layer.getFeatures(req):
                    if f.hasGeometry():
                        geoms.append(f.geometry())
                if geoms:
                    scope_geom = QgsGeometry.unaryUnion(geoms)
            except Exception as e:
                QgsMessageLog.logMessage(f"Error merging scope geometries: {e}", 'QRiS', Qgis.Warning)
        
        if not scope_geom or scope_geom.isEmpty():
            QgsMessageLog.logMessage("No scope geometry found.", 'QRiS', Qgis.Warning)
            self.figure.text(0.5, 0.5, "No geometric scope found (Sample Frame/AOI empty).", ha='center', va='center')
            self.canvas.draw()
            return
            
        # 2. Load Data Layer
        table_name = "dce_lines" if event_layer.layer.geom_type == 'Linestring' else "dce_polygons"
        if event_layer.layer.geom_type == 'Point':
             table_name = "dce_points"
             
        data_uri = f"{project_path}|layername={table_name}"
        data_layer = QgsVectorLayer(data_uri, "data", "ogr")
        
        if not data_layer.isValid():
            QgsMessageLog.logMessage(f"Data layer invalid: {table_name}", 'QRiS', Qgis.Critical)
            return

        subset_string = f"event_id = {event.id} AND event_layer_id = {event_layer.layer.id}"
        data_layer.setSubsetString(subset_string)
        
        # distribution dict already initialized with 0 for expected categories
        total_amount = 0
        
        # Transform scope geometry to data layer CRS if needed
        if scope_layer.crs() != data_layer.crs():
            xform = QgsCoordinateTransform(scope_layer.crs(), data_layer.crs(), QgsProject.instance())
            scope_geom.transform(xform)

        # Initialize DistanceArea for accurate metric calculations in meters/sq meters
        da = QgsDistanceArea()
        da.setSourceCrs(data_layer.crs(), QgsProject.instance().transformContext())
        da.setEllipsoid(QgsProject.instance().ellipsoid())
        
        # Calculate Scope Measure (Area) for Percentage Basis
        scope_measure = 0
        try:
            # Only relevant if data layer is Polygon (Area)
            # If Line, we can measure Length but usually "Percent of Sample Frame" implies Area
            # We measure Area of Scope regardless, usage depends on chart setting validation
            if scope_geom and not scope_geom.isEmpty():
                 scope_measure = da.measureArea(scope_geom)
        except Exception as e:
            QgsMessageLog.logMessage(f"Error measuring scope area: {e}", 'QRiS', Qgis.Warning)

        req = QgsFeatureRequest().setFilterRect(scope_geom.boundingBox())
        
        features_scanned = 0
        features_intersected = 0

        for feat in data_layer.getFeatures(req):
            features_scanned += 1
            if not feat.geometry().intersects(scope_geom):
                continue
            
            features_intersected += 1
            intersection = feat.geometry().intersection(scope_geom)
            if intersection.isEmpty():
                continue
                
            # Attribute retrieval depends on storage: direct column vs JSON metadata
            val = None
            try:
                # 1. Try direct column access
                idx = feat.fieldNameIndex(metric_field)
                if idx != -1:
                    val = feat[idx]
                else:
                    # 2. Try parsing from metadata JSON column
                    metadata_idx = feat.fieldNameIndex('metadata')
                    if metadata_idx != -1:
                        md_str = feat[metadata_idx]
                        if md_str:
                            md_json = json.loads(md_str)
                            # Attributes stored in 'attributes' key
                            val = md_json.get('attributes', {}).get(metric_field)
            except Exception as e:
                # QgsMessageLog.logMessage(f"Error retrieving attribute: {e}", 'QRiS', Qgis.Warning)
                pass
                
            if val is None:
                val = "Null"
            else:
                val = str(val)
                # Resolve lookup value relative to label
                if val in lookup_map:
                    val = lookup_map[val]
                
                if val == "": val = "Null"
            
            amount = 0
            is_count = measure_type == 'count'
            
            if data_layer.geometryType() == 0: # Point
                amount = 1
            elif data_layer.geometryType() == 1: # Line
                if is_count:
                    amount = 1
                else:
                    amount = da.measureLength(intersection)
            else: # Polygon
                if is_count:
                     amount = 1
                else:
                     amount = da.measureArea(intersection)
                
            distribution[val] = distribution.get(val, 0) + amount
            feature_counts[val] = feature_counts.get(val, 0) + 1
            total_amount += amount

        self.current_attribute_feature_counts = feature_counts
        self.current_distribution_data = (
            distribution, total_amount, event_layer, 
            metric_field, scope_measure, measure_type
        )
        self.populate_attributes_list(distribution.keys())
        self.draw_chart()

    def format_value(self, value):
        if value >= 1000:
            return f"{value:,.1f}"
        return f"{value:.1f}"

    def draw_chart(self):
        if not self.current_distribution_data:
            return

        # Unpack with backward compatibility
        data = self.current_distribution_data
        if len(data) >= 6:
            distribution, total, event_layer, metric_field, scope_measure, measure_type = data[:6]
        elif len(data) == 5:
            distribution, total, event_layer, metric_field, scope_measure = data[:5]
            measure_type = 'geometry'
        else:
             distribution, total, event_layer, metric_field = data[:4]
             scope_measure = 0
             measure_type = 'geometry'
             
        colors = self.get_layer_colors(event_layer, metric_field)
        
        # Determine Unit and Factor
        unit = self.unit_label
        factor = self.unit_factor
        
        if measure_type == 'count':
            unit = " Features"
            factor = 1.0
        elif 'percent' in measure_type:
            unit = "%"
            factor = 1.0

        self.figure.clear()
        chart_type = self.cmbChartType.currentData()
        ax = self.figure.add_subplot(111)
        
        # Apply font settings
        font_settings = {'family': self.chart_font_family, 'size': self.chart_font_size}
        
        # Filter Keys based on Attributes List
        if self.lstAttributes.count() > 0:
            checked_keys = set()
            for i in range(self.lstAttributes.count()):
                item = self.lstAttributes.item(i)
                if item.checkState() == QtCore.Qt.Checked:
                    key = item.data(QtCore.Qt.UserRole)
                    if key is None:
                        key = item.text()
                    checked_keys.add(str(key))
            sorted_keys = sorted([k for k in distribution.keys() if k in checked_keys])
        else:
            sorted_keys = sorted(distribution.keys())
        
        # Determine colors
        mpl_colors = []
        for key in sorted_keys:
            if key in colors:
                c = colors[key]
            elif '__default__' in colors:
                c = colors['__default__']
            else:
                # Use a consistent hashing for fallback color
                fallback_h = (hash(key) % 360) / 360.0
                c = QtGui.QColor.fromHsvF(fallback_h, 0.7, 0.9)
            mpl_colors.append(c.name())

        # Calculate Values
        values = []
        for key in sorted_keys:
             raw_val = distribution[key]
             val = 0
             if measure_type == 'percent_scope':
                  if scope_measure > 0:
                       val = (raw_val / scope_measure) * 100
             elif measure_type == 'percent_total':
                  if total > 0:
                       val = (raw_val / total) * 100
             else:
                  val = raw_val * factor
             values.append(val)
        
        # Determine Total for Display
        display_total = total * factor
        if measure_type == 'percent_total':
             display_total = 100
        elif measure_type == 'percent_scope':
             display_total = sum(values)

        if chart_type == "stacked":
            # Single horizontal stacked bar
            left = 0
            for k, v, c in zip(sorted_keys, values, mpl_colors):
                pct = v / display_total if display_total > 0 else 0
                label = f"{k}: {self.format_value(v)} {unit} ({pct*100:.1f}%)"
                ax.barh(0, v, left=left, color=c, label=label, height=0.6)
                left += v
            
            ax.set_yticks([])
            ax.set_xlabel(f"Total: {self.format_value(display_total)} {unit}", **font_settings) # Use display_total
            
            # Legend below x-axis label. x-label is roughly at y=-0.1 relative to axes.
            # Move legend further down.
            ax.legend(
                loc='upper center', 
                bbox_to_anchor=(0.5, -0.25), 
                ncol=2, 
                frameon=False, 
                prop=font_settings
            )
            
        elif chart_type == "horizontal":
            # Multi-bar horizontal chart
            y_pos = range(len(sorted_keys))
            ax.barh(y_pos, values, color=mpl_colors, align='center')
            ax.set_yticks(y_pos)
            
            ax.set_yticklabels(sorted_keys, **font_settings)
            ax.invert_yaxis()  # labels read top-to-bottom
            ax.set_xlabel(unit, **font_settings)
            
            # Value labels on bars
            max_val = max(values) if values else 1
            
            # Add padding to x-axis so labels fit (extra space for text)
            if max_val > 0:
                ax.set_xlim(0, max_val * 1.35)
                
            for i, v in enumerate(values):
                 label = f" {self.format_value(v)} {unit}"
                 ax.text(v, i, label, va='center', rotation=0, **font_settings)

            # Second Axis (Percent) - Only if not already percent
            if self.chart_show_pct and 'percent' not in measure_type:
                ax2 = ax.twiny()
                x1_min, x1_max = ax.get_xlim()
                
                # Determine Basis (scaled by factor)
                basis = 0
                if self.chart_pct_basis == 'scope' and scope_measure > 0:
                    basis = scope_measure * factor
                elif total > 0 and self.chart_pct_basis == 'mapped':
                    basis = total * factor
                
                if basis > 0:
                    x2_min = (x1_min / basis) * 100
                    x2_max = (x1_max / basis) * 100
                    
                    ax2.set_xlim(x2_min, x2_max)
                    # Label
                    lbl = "Percent of Total Mapped (%)" if self.chart_pct_basis == 'mapped' else "Percent of Sample Frame Area (%)"
                    ax2.set_xlabel(lbl, **font_settings)
                    
                    # Ensure font settings apply to ticks as well
                    for tick in ax2.get_xticklabels():
                         tick.set_fontname(self.chart_font_family)
                         tick.set_fontsize(self.chart_font_size)

        # Set also tick labels font
        for tick in ax.get_xticklabels():
            tick.set_fontname(self.chart_font_family)
            tick.set_fontsize(self.chart_font_size)
            
        for tick in ax.get_yticklabels():
            tick.set_fontname(self.chart_font_family)
            tick.set_fontsize(self.chart_font_size)

        self.figure.tight_layout()
        self.canvas.draw()

class ChartSettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent, current_font, show_pct, pct_basis, is_polygon):
        super().__init__(parent)
        self.setWindowTitle('Chart Settings')
        self.font = current_font
        self.show_pct = show_pct
        self.pct_basis = pct_basis
        self.is_polygon = is_polygon
        self.setupUi()
        
    def setupUi(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Font
        self.btnFont = QtWidgets.QPushButton(f'Change Font ({self.font.family()} {self.font.pointSize()}pt)')
        self.btnFont.clicked.connect(self.choose_font)
        layout.addWidget(self.btnFont)
        
        # Percent Axis Group
        grp = QtWidgets.QGroupBox('Top Axis (Percent)')
        gl = QtWidgets.QVBoxLayout(grp)
        
        self.chkShowPct = QtWidgets.QCheckBox('Show Percent Axis (Horizontal Chart)')
        self.chkShowPct.setChecked(self.show_pct)
        self.chkShowPct.toggled.connect(self.update_state)
        gl.addWidget(self.chkShowPct)
        
        self.cmbBasis = QtWidgets.QComboBox()
        self.cmbBasis.addItem('Percent of Total Mapped Features', 'mapped')
        if self.is_polygon:
            self.cmbBasis.addItem('Percent of Sample Frame Area', 'scope')
        
        # Set current index
        idx = self.cmbBasis.findData(self.pct_basis)
        if idx >= 0:
             self.cmbBasis.setCurrentIndex(idx)
        else:
             self.cmbBasis.setCurrentIndex(0)
             
        # Enable/Disable combo based on check
        self.cmbBasis.setEnabled(self.show_pct)
        
        gl.addWidget(self.cmbBasis)
        layout.addWidget(grp)
        
        # Buttons
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def update_state(self):
        self.cmbBasis.setEnabled(self.chkShowPct.isChecked())

    def choose_font(self):
        font, ok = QtWidgets.QFontDialog.getFont(self.font, self, 'Select Chart Font')
        if ok:
            self.font = font
            self.btnFont.setText(f'Change Font ({self.font.family()} {self.font.pointSize()}pt)')
            
    def get_settings(self):
        return {
            'font': self.font,
            'show_pct': self.chkShowPct.isChecked(),
            'pct_basis': self.cmbBasis.currentData()
        }

