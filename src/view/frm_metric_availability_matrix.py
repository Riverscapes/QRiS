from typing import List, Dict
from qgis.PyQt import QtWidgets, QtCore, QtGui

from ..model.metric import Metric
from ..model.project import Project

class FrmMetricAvailabilityMatrix(QtWidgets.QDialog):
    def __init__(self, parent, project: Project, metric: Metric, analysis_metadata: dict = None, highlight_dce_id: int = None, limit_dces: List = None):
        super().__init__(parent)
        self.project = project
        self.metric = metric
        self.analysis_metadata = analysis_metadata or {}
        self.highlight_dce_id = highlight_dce_id
        self.limit_dces = limit_dces
        
        # DEBUG
        # from qgis.core import QgsMessageLog, Qgis
        # QgsMessageLog.logMessage(f"Matrix Init - Metadata: {self.analysis_metadata}", "QRiS", Qgis.Warning)
        
        self.setWindowTitle(f"Availability Matrix - {self.metric.name}")
        self.resize(800, 500)
        
        self.v_layout = QtWidgets.QVBoxLayout(self)
        
        # Label
        self.lbl_info = QtWidgets.QLabel(f"Availability for: {self.metric.name}")
        font = self.lbl_info.font()
        font.setBold(True)
        self.lbl_info.setFont(font)
        self.v_layout.addWidget(self.lbl_info)
        
        self.lbl_desc = QtWidgets.QLabel(self.metric.description if self.metric.description else "")
        self.lbl_desc.setWordWrap(True)
        self.v_layout.addWidget(self.lbl_desc)

        # Table
        self.table = QtWidgets.QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.v_layout.addWidget(self.table)
        
        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addStretch()
        self.btn_close = QtWidgets.QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        h_layout.addWidget(self.btn_close)
        self.v_layout.addLayout(h_layout)   
        
        self.load_data()

    def load_data(self):
        # 1. Determine Columns (Required Inputs and DCE Layers)
        if not self.metric.metric_params:
             self.table.setColumnCount(1)
             self.table.setHorizontalHeaderLabels(["Status"])
             self.table.setRowCount(1)
             self.table.setItem(0, 0, QtWidgets.QTableWidgetItem("Manual Metric Only - No Automation Available"))
             return

        dce_layers = self.metric.metric_params.get('dce_layers', [])
        inputs = self.metric.metric_params.get('inputs', [])
        
        if not dce_layers and not inputs:
            self.table.setColumnCount(1)
            self.table.setHorizontalHeaderLabels(["Status"])
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QtWidgets.QTableWidgetItem("This metric does not require any specific layers."))
            return

        # Prepare Column Info
        # List of (type, ref, display_text)
        columns_info = []

        # Find the Protocol for this Metric to look up clean layer names
        metric_protocol = None
        for p in self.project.protocols.values():
            if p.machine_code == self.metric.protocol_machine_code:
                metric_protocol = p
                break

        # 1. Inputs
        for input_item in inputs:
            ref = input_item.get('input_ref', 'Unknown Input')
            # For inputs, we usually capitalize the ref as the display
            display_text = ref.replace('_', ' ').title()
            tooltip_text = f"Project Input: {ref}"
            columns_info.append(('input', ref, f"{display_text} (Input)", tooltip_text))
            
        # 2. DCE Layers
        for layer_def in dce_layers:
            ref = layer_def.get('layer_id_ref', 'Unknown Layer')
            usage = layer_def.get('usage', 'Required')
            
            # Lookup clean name from Protocol
            display_text = ref
            if metric_protocol:
                 # Protocol.protocol_layers is a dict keyed by layer ID? 
                 # Let's check src/model/protocol.py or protocol_parser.py
                 # Based on protocol_parser it seems to parse into ProtocolDefinition object lists
                 # But Protocol class has protocol_layers = {} in init.
                 # We need to see how that dict is populated. 
                 # Assuming it's a dict {layer.id: LayerDefinition} or similar.
                 # Let's try standard lookup.
                 
                 # If protocol_layers is a dict:
                 if ref in metric_protocol.protocol_layers:
                     display_text = metric_protocol.protocol_layers[ref].label
                 else:
                     # If it's a list or not populated as expected, try fallback logic
                     # or maybe it's populated differently.
                     pass
            
            # If usage is present and not 'Required', we might want to append it?
            # User request: Get rid of "Required" in title, use "DCE Layer" instead? 
            # Or assume they mean replace the generic notion.
            # If usage is specialized (like 'normalization'), indicate it?
            # Current request: "Get rid of 'Required' ... use 'DCE Layer' instead"
            # AND "use the display label of the layer"
            
            # So: "Layer Label" or "Layer Label (Usage)"?
            # Just "Layer Label" is probably cleanest unless ambiguous.
            
            final_header = display_text
            if usage and usage.lower() != 'required' and usage.lower() != 'metric_layer':
                 final_header = f"{display_text} ({usage})"
            
            tooltip_text = f"DCE Layer: {ref}\nUsage: {usage}"
            
            attr_filter = layer_def.get('attribute_filter')
            if attr_filter:
                tooltip_text += f"\nRequired Filter: {attr_filter.get('field_id_ref')} IN {attr_filter.get('values')}"
            
            columns_info.append(('dce_layer', ref, final_header, tooltip_text))

        # Determine Rows (DCEs)
        if self.limit_dces:
            events = self.limit_dces
            if hasattr(events[0], 'id'): # Check if objects or IDs
                pass
            elif isinstance(events[0], int): # Convert IDs to objects
                events = [e for e in self.project.events.values() if e.id in events]
        else:
            events = list(self.project.events.values())

        if not events:
            self.table.setRowCount(1)
            self.table.setColumnCount(1)
            self.table.setItem(0, 0, QtWidgets.QTableWidgetItem("No Data Collection Events (DCEs) found in project."))
            return
            
        # Setup Table
        # Cols: Event Name, then each Layer Column, then Available?
        headers = ["DCE"]
        tooltips = ["Data Collection Event Name"]
        
        for info in columns_info:
            # c_type, ref, display_header, tooltip
            headers.append(info[2])
            tooltips.append(info[3])
        
        headers.append("Calculation Available?")
        tooltips.append("Indicates if all required inputs and layers are present for this metric.")
        
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        # Set Header Tooltips
        for i, tip in enumerate(tooltips):
            item = self.table.horizontalHeaderItem(i)
            if item:
                item.setToolTip(tip)

        self.table.setRowCount(len(events))
        
        # Populate
        for row_idx, event in enumerate(events):
            is_highlighted = self.highlight_dce_id and event.id == self.highlight_dce_id

            # 1. DCE Name
            item_name = QtWidgets.QTableWidgetItem(event.name)
            
            # Highlight DCE if requested
            if is_highlighted:
                font = item_name.font()
                font.setBold(True)
                item_name.setFont(font)
                item_name.setBackground(QtGui.QColor("#cce5ff"))
                
            self.table.setItem(row_idx, 0, item_name)
            
            # Track overall availability for this row
            # For dce_layers, we need to respect the OR logic for Usages if we are calculating "Available?".
            # However, the table columns are specific layers. 
            # So a column might be "Missing", but the metric is still "Available" because another column for same Usage is "Yes".
            # We need to compute 'Available?' column separately using standard logic.
            
            # 2. Check each column
            for col_idx, (c_type, ref, display_header, _) in enumerate(columns_info):
                
                status_item = QtWidgets.QTableWidgetItem()
                if is_highlighted:
                    font = status_item.font()
                    font.setBold(True)
                    status_item.setFont(font)
                
                if c_type == 'input':
                    # Check analysis metadata (Case Insensitive)
                    found_id = None
                    for key, val in self.analysis_metadata.items():
                        if key.strip().lower() == str(ref).strip().lower():
                            found_id = val
                            break
                            
                    if found_id is not None:
                         # Try to find the name of the input item for better feedback
                         input_name = "Present"
                         found_obj = None
                         
                         # Heuristic lookup based on ref string
                         if 'centerline' in str(ref).lower():
                             found_obj = self.project.profiles.get(found_id)
                         elif 'dem' in str(ref).lower():
                             found_obj = self.project.rasters.get(found_id)
                         elif 'valley' in str(ref).lower():
                             found_obj = self.project.valley_bottoms.get(found_id)
                         
                         if found_obj:
                             input_name = found_obj.name
                             
                         status_item.setText("Present")
                         status_item.setBackground(QtGui.QColor("#d4edda"))
                         status_item.setToolTip(f"Input ID: {found_id}\nName: {input_name}")
                         
                         if found_obj and hasattr(found_obj, 'feature_count'):
                             try:
                                 f_count = found_obj.feature_count(self.project.project_file)
                                 if f_count == 0:
                                     status_item.setText("No Features in Layer")
                                     status_item.setBackground(QtGui.QColor("#fff3cd"))
                                     status_item.setToolTip(f"Input '{input_name}' exists but has 0 features.")
                                 else:
                                     status_item.setToolTip(f"Input ID: {found_id}\nName: {input_name}\nFeatures: {f_count}")
                             except Exception as e:
                                 status_item.setToolTip(f"Error checking features: {str(e)}")
                    else:
                         status_item.setText("Input Not Selected for Analysis")
                         status_item.setBackground(QtGui.QColor("#f8d7da"))
                         
                
                elif c_type == 'dce_layer':
                     # Check if specific layer exists in DCE
                     found_layer = None
                     for event_layer in event.event_layers:
                         if event_layer.layer.layer_id == ref:
                             found_layer = event_layer
                             break
                     
                     if found_layer:
                         try:
                             f_count = found_layer.feature_count(self.project.project_file)
                             if f_count > 0:
                                 status_item.setText("Present")
                                 status_item.setBackground(QtGui.QColor("#d4edda"))
                                 status_item.setToolTip(f"Found: {found_layer.layer.name}\nFeatures: {f_count}")
                             else:
                                 status_item.setText("No Features in Layer")
                                 status_item.setBackground(QtGui.QColor("#fff3cd"))
                                 status_item.setToolTip(f"Found: {found_layer.layer.name}\nWarning: Layer exists but has 0 features.")
                         except Exception as e:
                             status_item.setText("Present")
                             status_item.setBackground(QtGui.QColor("#d4edda"))
                             status_item.setToolTip(f"Found: {found_layer.layer.name}\nError checking features: {str(e)}")
                     else:
                         status_item.setText("Layer Not Added to DCE")
                         status_item.setBackground(QtGui.QColor("#f8d7da"))
                
                self.table.setItem(row_idx, col_idx + 1, status_item)
            
            # Match named usage groups (OR logic within group)
            # Find which usage group this ref belongs to
            # We already have usage from columns_info... wait, columns_info has display_header not usage now.
            # We need to re-derive usage or just check the metric params directly which is safer.
            pass # The Summary Logic below relies on the metric logic itself, not the columns. 
                 # The columns just display status.
            
            # 3. Summary (Using strict Metric Logic)
            # Inputs must be present
            inputs_ok = True
            missing_inputs = []
            if inputs:
                for input_item in inputs:
                     input_ref = input_item.get('input_ref')
                     # Case-insensitive check against metadata keys
                     found = False
                     if input_ref:
                         s_ref = str(input_ref).strip().lower()
                         for key in self.analysis_metadata.keys():
                             if str(key).strip().lower() == s_ref:
                                 if self.analysis_metadata[key] is not None:
                                     found = True
                                 break
                     
                     if not found:
                         inputs_ok = False
                         missing_inputs.append(str(input_ref))
            
            # DCE Layers logic (handled by metric object)
            dce_ok = self.metric.can_calculate_for_dce(event)
            
            is_fully_available = inputs_ok and dce_ok

            summary_item = QtWidgets.QTableWidgetItem()
            tool_tip_lines = []
            if is_fully_available:
                summary_item.setText("YES")
                summary_item.setBackground(QtGui.QColor("#28a745")) # Green
                summary_item.setForeground(QtGui.QColor("white"))
                tool_tip_lines.append("Metric can be calculated for this DCE.")
            else:
                summary_item.setText("NO")
                summary_item.setBackground(QtGui.QColor("#dc3545")) # Red
                summary_item.setForeground(QtGui.QColor("white"))
                if not inputs_ok:
                    tool_tip_lines.append(f"Missing Inputs: {', '.join(missing_inputs)}")
                if not dce_ok:
                    tool_tip_lines.append("One or more required DCE layers (or usage groups) are missing or incomplete.")
            
            summary_item.setToolTip("\n".join(tool_tip_lines))
            summary_item.setTextAlignment(QtCore.Qt.AlignCenter)

            if is_highlighted:
                font = summary_item.font()
                font.setBold(True)
                summary_item.setFont(font)

            self.table.setItem(row_idx, len(columns_info) + 1, summary_item)
            
        self.table.resizeColumnsToContents()
