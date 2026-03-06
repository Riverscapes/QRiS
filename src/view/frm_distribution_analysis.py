import sqlite3
import xml.etree.ElementTree as ET
from PyQt5 import QtWidgets, QtCore, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from qgis.core import QgsVectorLayer, QgsProject, QgsField, QgsRectangle, QgsFeatureRequest, QgsGeometry, QgsCoordinateTransform, Qgis, QgsMessageLog, QgsDistanceArea

from ..model.project import Project
from ..model.event import Event, DESIGN_EVENT_TYPE_ID, AS_BUILT_EVENT_TYPE_ID, DCE_EVENT_TYPE_ID
from ..model.sample_frame import SampleFrame
from ..model.event_layer import EventLayer
from .utilities import add_standard_form_buttons

class FrmDistributionAnalysis(QtWidgets.QDialog):

    def __init__(self, parent, qris_project: Project, map_manager):
        super().__init__(parent)
        self.qris_project = qris_project
        self.map_manager = map_manager
        self.setWindowTitle("Distribution Analysis")
        self.resize(600, 500)
        
        self.unit_factor = 1.0
        self.unit_label = ""
        
        self.setupUi()
        
    def setupUi(self):
        self.vert = QtWidgets.QVBoxLayout(self)
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
        
        # Line 5: Metric (Categorical Attributes)
        self.metric_label = QtWidgets.QLabel("Metric:")
        self.cmbMetric = QtWidgets.QComboBox()
        self.cmbMetric.currentIndexChanged.connect(self.calculate_distribution)
        self.form_layout.addRow(self.metric_label, self.cmbMetric)

        self.vert.addLayout(self.form_layout)

        # Result: Horizontal Bar Chart
        self.chart_label = QtWidgets.QLabel("Distribution Summary:")
        self.vert.addWidget(self.chart_label)
        
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(200)
        self.vert.addWidget(self.canvas)

        # Line 6: Chart Controls
        self.hbox_bottom = QtWidgets.QHBoxLayout()
        
        self.chart_type_label = QtWidgets.QLabel("Chart Type:")
        self.hbox_bottom.addWidget(self.chart_type_label)
        
        self.cmbChartType = QtWidgets.QComboBox()
        self.cmbChartType.addItem("Horizontal Bar", "horizontal")
        self.cmbChartType.addItem("Stacked Bar", "stacked")
        self.cmbChartType.currentIndexChanged.connect(self.draw_chart)
        self.hbox_bottom.addWidget(self.cmbChartType)
        
        self.hbox_bottom.addSpacing(10)
        
        self.btnUnits = QtWidgets.QToolButton()
        self.btnUnits.setText("Units")
        self.btnUnits.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.hbox_bottom.addWidget(self.btnUnits)
        
        self.hbox_bottom.addItem(QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        
        self.btnSaveChart = QtWidgets.QPushButton("Save Chart")
        self.btnSaveChart.clicked.connect(self.save_chart)
        self.hbox_bottom.addWidget(self.btnSaveChart)
        
        self.vert.addLayout(self.hbox_bottom)
        
        self.vert.addLayout(add_standard_form_buttons(self, 'distribution-analysis'))
        
        # Initial Population
        self.current_distribution_data = None
        self.populate_scope()
        self.populate_dce()

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

    def get_scope_features(self, scope_item):
        features = []
        if isinstance(scope_item, SampleFrame):
            import sqlite3
            try:
                # All scopes (VB, AOI, SF) are SampleFrame instances in QRiS model
                # and share sample_frame_features table
                with sqlite3.connect(self.qris_project.project_file) as conn:
                    cursor = conn.cursor()
                    
                    table_name = 'sample_frame_features'
                    fk_col = 'sample_frame_id'
                    
                    # Identify name column - usually 'name' but fallback to 'id'
                    # We can check schema but for speed just look for columns
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    name_col = 'name' if 'name' in columns else 'id'
                    
                    query = f"SELECT {name_col}, id FROM {table_name} WHERE {fk_col} = ?"
                    cursor.execute(query, (scope_item.id,))
                    features = cursor.fetchall() # list of tuples (name, id)
                    
            except Exception as e:
                # Log or print error
                print(f"Error loading scope features: {e}")
                
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_distribution_data:
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

    def save_chart(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Chart", "", "PNG Image (*.png);;JPEG Image (*.jpg)")
        if filename:
            self.figure.savefig(filename)

    def get_layer_colors(self, event_layer_item, attribute_name):
        colors = {}
        
        # User requested QML as source of truth
        if not self.map_manager:
             return colors

        qml_path = self.map_manager.get_symbology_qml(event_layer_item.layer.qml)
        if not qml_path or not QtCore.QFile.exists(qml_path):
             return colors

        try:
             # Load QML into a temporary memory layer to parse style safely
            geom_type = event_layer_item.layer.geom_type
            if geom_type == 'Linestring': geom_type = 'LineString'
            
            temp_layer = QgsVectorLayer(f"{geom_type}?crs=epsg:4326", "temp_loader", "memory")
            if not temp_layer.isValid():
                return colors
                
            # Load style (only renderer needed)
            temp_layer.loadNamedStyle(qml_path)
            
            renderer = temp_layer.renderer()
            if not renderer:
                return colors
                
            # Handle Categorized
            if renderer.type() == 'categorizedSymbol':
                # Check attribute match (case insensitive, strip quotes)
                r_attr = renderer.classAttribute().replace('"', '').replace("'", "")
                
                # Check if attributes match OR if we should just trust the categories if the attribute is empty 
                # (sometimes happens with expressions)
                if r_attr.lower() != attribute_name.lower():
                    QgsMessageLog.logMessage(f"Symbology attribute '{r_attr}' does not match metric '{attribute_name}' - attempting to use colors anyway.", "QRiS", Qgis.Info)

                for cat in renderer.categories():
                    val = str(cat.value())
                    lbl = cat.label()
                    
                    # Store color by Value AND Label to catch all cases
                    colors[val] = cat.symbol().color()
                    if lbl:
                        colors[lbl] = cat.symbol().color()

            # Handle Single Symbol (apply to all)
            elif renderer.type() == 'singleSymbol':
                color = renderer.symbol().color()
                colors['__default__'] = color

            # Handle RuleBased - Try to match labels to values
            elif renderer.type() == 'RuleRenderer':
                root = renderer.rootRule()
                # Recursively get rules from groups
                def get_rules(parent_rule):
                    rules = []
                    for child in parent_rule.children():
                         if child.symbol(): # It's a drawing rule
                             rules.append(child)
                         # Recurse for groups
                         rules.extend(get_rules(child))
                    return rules

                for rule in get_rules(root):
                     colors[rule.label()] = rule.symbol().color()

        except Exception as e:
            QgsMessageLog.logMessage(f"Error loading QML style: {e}", "QRiS", Qgis.Warning)

        return colors

    def calculate_distribution(self):
        self.figure.clear()
        
        scope = self.cmbScope.currentData()
        scope_feature_id = self.cmbScopeFeatures.currentData()
        event = self.cmbDCE.currentData()
        event_layer = self.cmbLayer.currentData()
        metric_field = self.cmbMetric.currentData()
        
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
            
            # 2. Check 'lookup' table
            elif 'lookup' in field_def:
                lookup_name = field_def['lookup']
                if lookup_name in self.qris_project.lookup_tables:
                    # lookup_tables is dict of tables -> dict of id:DBItem
                    # We usually want the names/labels as keys
                    lkp = self.qris_project.lookup_tables[lookup_name]
                    for item in lkp.values():
                        distribution[item.name] = 0
                        # Store lookup map for value resolution
                        lookup_map[str(item.id)] = item.name

        project_path = self.qris_project.project_file
        
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
            geoms = [f.geometry() for f in scope_layer.getFeatures(req)]
            if geoms:
                scope_geom = QgsGeometry.unaryUnion(geoms)
        
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
                            import json
                            md_json = json.loads(md_str)
                            # Attributes stored in 'attributes' key
                            val = md_json.get('attributes', {}).get(metric_field)
            except Exception as e:
                print(f"Error retrieving attribute {metric_field}: {e}")
                
            if val is None:
                val = "Null"
            else:
                val = str(val)
                # Resolve lookup value relative to label
                if val in lookup_map:
                    val = lookup_map[val]
                    
                if val == "": val = "Null"
            
            amount = 0
            if data_layer.geometryType() == 0: # Point
                amount = 1
            elif data_layer.geometryType() == 1: # Line
                amount = da.measureLength(intersection)
            else: # Polygon
                amount = da.measureArea(intersection)
                
            distribution[val] = distribution.get(val, 0) + amount
            total_amount += amount
            
        QgsMessageLog.logMessage(f"Distribution: Scanned={features_scanned}, Intersected={features_intersected}, Total={total_amount}, Dict={list(distribution.keys())}", 'QRiS', Qgis.Info)

        self.current_distribution_data = (distribution, total_amount, event_layer, metric_field)

        if total_amount > 0:
            self.draw_chart()
        else:
            self.figure.text(0.5, 0.5, "No matching features found within scope.", ha='center', va='center')
            self.canvas.draw()

    def format_value(self, value):
        if value is None:
            return "0"
        if value < 0.01 and value > 0:
            return f"{value:.4e}"
        elif value >= 1000:
            return f"{value:,.0f}"
        else:
            return f"{value:.2f}"

    def draw_chart(self):
        if not self.current_distribution_data:
            return

        distribution, total, event_layer, metric_field = self.current_distribution_data
        colors = self.get_layer_colors(event_layer, metric_field)
        
        # Use selected unit
        unit = self.unit_label
        factor = self.unit_factor

        self.figure.clear()
        chart_type = self.cmbChartType.currentData()
        ax = self.figure.add_subplot(111)
        
        sorted_keys = sorted(distribution.keys())
        
        # Determine colors for all keys
        mpl_colors = []
        for key in sorted_keys:
            if key in colors:
                c = colors[key]
            elif '__default__' in colors:
                c = colors['__default__']
            else:
                fallback_h = (hash(key) % 360) / 360.0
                c = QtGui.QColor.fromHsvF(fallback_h, 0.7, 0.9)
            mpl_colors.append(c.name())

        values = [distribution[key] * factor for key in sorted_keys]

        if chart_type == "stacked":
            left = 0
            for k, v, c in zip(sorted_keys, values, mpl_colors):
                pct = v / (total * factor) if total > 0 else 0
                label = f"{k}: {self.format_value(v)} {unit} ({pct*100:.1f}%)"
                ax.barh(0, v, left=left, color=c, label=label, height=0.6)
                left += v
            
            ax.set_yticks([])
            ax.set_xlabel(f"Total: {self.format_value(total*factor)} {unit}")
            # Legend
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.25), ncol=2, frameon=False)
            
        elif chart_type == "horizontal":
            y_pos = range(len(sorted_keys))
            ax.barh(y_pos, values, color=mpl_colors, align='center')
            ax.set_yticks(y_pos)
            ax.set_yticklabels(sorted_keys)
            ax.invert_yaxis()
            ax.set_xlabel(unit)
            
            # Label
            for i, v in enumerate(values):
                 label = f" {self.format_value(v)} {unit}"
                 ax.text(v, i, label, va='center')
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()
