import copy
import csv
import json
import os
import pandas as pd

from qgis.PyQt import QtWidgets, QtCore, QtGui

from ..model.pour_point import PourPoint
from ..model.project import Project
from ..model.basin_characteristics_table_view import BasinCharsTableModel
from ..gp.stream_stats import delineate_watershed, get_state_from_coordinates, retrieve_basin_characteristics, calculate_flow_statistics, retrieve_flow_scenarios
from .utilities import validate_name, add_standard_form_buttons, format_superscript
from .widgets.metadata import MetadataWidget


class FrmPourPoint(QtWidgets.QDialog):

    def __init__(self, parent, qris_project: Project, latitude: float, longitude: float, pour_point: PourPoint):
        super().__init__(parent)
        
        metadata_json = json.dumps(pour_point.metadata) if pour_point is not None and pour_point.metadata else None
        self.metadata_widget = MetadataWidget(self, metadata_json)
        
        self.setupUi()

        self.pour_point = pour_point
        self.qris_project = qris_project

        if self.pour_point is None:
            self.setWindowTitle('Create New Pour Point with Catchment')

            self.txtLatitude.setText(f"{latitude:.6f}")
            self.txtLongitude.setText(f"{longitude:.6f}")

            # Remove Basin and Flow Tabs for new creation
            self.tabWidget.removeTab(0)
            self.tabWidget.removeTab(0)
        else:
            self.setWindowTitle('Pour Point Details')
            
            self.groupAnalysis.setVisible(False)
            self.chkAddToMap.setVisible(False)

            self.txtName.setText(pour_point.name)
            self.txtDescription.setPlainText(pour_point.description)

            self.txtLatitude.setText(f"{pour_point.latitude:.6f}")
            self.txtLongitude.setText(f"{pour_point.longitude:.6f}")

            # Load the basin characteristics
            self.load_basin_characteristics()

            # Load flow statistics into the table view
            self.load_flow_statistics()

    def load_basin_characteristics(self):
        if self.pour_point.basin_chars is not None and 'parameters' in self.pour_point.basin_chars:
            # Find required codes first so we can filter unneeded -999 noise
            required_codes = set()
            if self.pour_point.flow_scenarios:
                scenario_list = []
                if isinstance(self.pour_point.flow_scenarios, dict):
                    scenario_list = self.pour_point.flow_scenarios.get('scenarios', [])
                elif isinstance(self.pour_point.flow_scenarios, list):
                    scenario_list = self.pour_point.flow_scenarios
                    
                for scenario in scenario_list:
                    if isinstance(scenario, dict):
                        for rr in scenario.get('regressionRegions', []):
                            for param in rr.get('parameters', []):
                                required_codes.add(param.get('code', '').upper())

            basin_data = []
            for param in self.pour_point.basin_chars['parameters']:
                code = param.get('code', '')
                val = param.get('value', 'N/A')

                # Filter out API artifacts (-999 values) unless they are strictly required by Flow Statistics
                if (val == -999 or val == -999.0) and code.upper() not in required_codes:
                    continue

                basin_data.append([
                    param.get('name', ''),
                    code,
                    format_superscript(param.get('unit', '')),
                    val,
                    param.get('override_value', '')
                ])

            self.basin_model = BasinCharsTableModel(basin_data, ['Name', 'Code', 'Units', 'USGS Value', 'User Override'], required_codes=list(required_codes))
            self.basinTable.setModel(self.basin_model)
            self.basinTable.verticalHeader().setVisible(False)
            
            # Expand headers
            header = self.basinTable.horizontalHeader()
            header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
            self.basinTable.resizeColumnToContents(0)
            if self.basinTable.columnWidth(0) > 275:
                self.basinTable.setColumnWidth(0, 275)

    def show_flow_context_menu(self, position):
        item = self.tabFlow.itemAt(position)
        if not item:
            return
        
        menu = QtWidgets.QMenu()
        details_action = menu.addAction(QtGui.QIcon(':/plugins/qris_toolbar/details'),"Details")
        
        # Get the item in column 1 (Value) for the clicked row
        val_item = self.tabFlow.item(item.row(), 1)
        if val_item:
            raw_val = val_item.data(QtCore.Qt.UserRole)
            full_text = val_item.text()
            
            if raw_val:
                menu.addSeparator()
                
                menu.addAction(QtGui.QIcon(':/plugins/qris_toolbar/copy_content'), "Copy Value", 
                    lambda: QtWidgets.QApplication.clipboard().setText(str(raw_val)))
                
                menu.addAction(QtGui.QIcon(':/plugins/qris_toolbar/copy_content_units'), "Copy Value with Units", 
                    lambda: QtWidgets.QApplication.clipboard().setText(full_text))

        action = menu.exec_(self.tabFlow.viewport().mapToGlobal(position))
        if action == details_action:
            self.show_flow_stat_details(item)

    def show_basin_context_menu(self, position):
        index = self.basinTable.indexAt(position)
        if not index.isValid():
            return

        menu = QtWidgets.QMenu()
        details_action = menu.addAction(QtGui.QIcon(':/plugins/qris_toolbar/details'),"Details")
        
        # Get the row index
        row = index.row()
        
        # Get Value (col 3) and Units (col 2)
        val_idx = self.basin_model.index(row, 3)
        unit_idx = self.basin_model.index(row, 2)
        
        val_str = str(self.basin_model.data(val_idx, QtCore.Qt.DisplayRole))
        unit_str = str(self.basin_model.data(unit_idx, QtCore.Qt.DisplayRole))
        
        full_text = f"{val_str} {unit_str}".strip()
        
        if val_str and val_str != 'N/A':
            menu.addSeparator()
            menu.addAction(QtGui.QIcon(':/plugins/qris_toolbar/copy_content'), "Copy Value", 
                lambda: QtWidgets.QApplication.clipboard().setText(val_str))
            
            menu.addAction(QtGui.QIcon(':/plugins/qris_toolbar/copy_content_units'), "Copy Value with Units", 
                lambda: QtWidgets.QApplication.clipboard().setText(full_text))

        action = menu.exec_(self.basinTable.viewport().mapToGlobal(position))
        if action == details_action:
            self.show_basin_details(index)

    def show_basin_details(self, index):
        if not index.isValid():
            return
            
        row = index.row()
        code_idx = self.basin_model.index(row, 1) # Code is column 1
        code = self.basin_model.data(code_idx, QtCore.Qt.DisplayRole)
        
        # Find the parameter usage
        param_obj = None
        if self.pour_point.basin_chars and 'parameters' in self.pour_point.basin_chars:
            for p in self.pour_point.basin_chars['parameters']:
                if p.get('code', '') == code:
                    param_obj = p
                    break
        
        if not param_obj:
            return

        name = param_obj.get('name', 'Unknown')
        desc = param_obj.get('description', 'No description provided.')
        val = param_obj.get('value', 'N/A')
        unit = format_superscript(param_obj.get('unit', ''))
        
        details = f"Parameter: {name} ({code})\n"
        details += f"Value: {val} {unit}\n"
        details += f"Description: {desc}\n\n"
        
        override = param_obj.get('override_value', '')
        if str(override).strip():
            details += f"User Override: {override}\n\n"

        # Find Usage in Flow Statistics
        usage = []
        
        # 1. Try to list from calculated Flow Statistics results first (most accurate)
        if self.pour_point.flow_stats:
            for entry in self.pour_point.flow_stats:
                # Handle error entries
                if 'error' in entry:
                    continue

                scenario = entry.get('scenario', {})
                s_name = scenario.get('statisticGroupName', scenario.get('name', 'Unknown Scenario'))
                
                estimate = entry.get('estimate', {})
                if not isinstance(estimate, dict):
                    continue

                for region in estimate.get('regressionRegions', []):
                    r_name = region.get('name', 'Unknown Region')
                    
                    # Check if this parameter is required for this region
                    has_param = False
                    param_limit_str = ""
                    for p in region.get('parameters', []):
                        if p.get('code', '').upper() == code.upper():
                            has_param = True
                            # Extract limits
                            limits = p.get('limits', {})
                            min_lim = limits.get('min', 'none')
                            max_lim = limits.get('max', 'none')
                            if min_lim != 'none' or max_lim != 'none':
                                param_limit_str = f"Limits:   [{min_lim} to {max_lim}]"
                            break
                    
                    if has_param:
                        # List all statistics generated by this region
                        stat_names = []
                        for res in region.get('results', []):
                            s_code = res.get('code', '')
                            s_n = res.get('name', s_code)
                            stat_names.append(s_n)
                        
                        usage.append(f"Scenario: {s_name}\nRegion:   {r_name}")
                        if param_limit_str:
                            usage.append(param_limit_str)
                        if stat_names:
                            usage.append(f"Stats:    {', '.join(stat_names)}")
                        else:
                            usage.append(f"Stats:    (All statistics in this region)")
                        usage.append("-" * 30)

        # 2. If no stats calculated, fallback to Flow Scenarios definitions
        elif self.pour_point.flow_scenarios:
            scenarios = []
            if isinstance(self.pour_point.flow_scenarios, dict):
                scenarios = self.pour_point.flow_scenarios.get('scenarios', [])
            elif isinstance(self.pour_point.flow_scenarios, list):
                scenarios = self.pour_point.flow_scenarios
            
            for scenario in scenarios:
                if not isinstance(scenario, dict):
                    continue
                    
                s_name = scenario.get('statisticGroupName', scenario.get('name', 'Unknown Scenario'))
                
                for region in scenario.get('regressionRegions', []):
                    r_name = region.get('name', 'Unknown Region')
                    
                    # Check if this parameter is required for this region
                    has_param = False
                    param_limit_str = ""
                    for p in region.get('parameters', []):
                        if p.get('code', '').upper() == code.upper():
                            has_param = True
                            # Extract limits
                            limits = p.get('limits', {})
                            min_lim = limits.get('min', 'none')
                            max_lim = limits.get('max', 'none')
                            if min_lim != 'none' or max_lim != 'none':
                                param_limit_str = f"Limits:   [{min_lim} to {max_lim}]"
                            break
                    
                    if has_param:
                        usage.append(f"Scenario: {s_name}\nRegion:   {r_name}")
                        if param_limit_str:
                            usage.append(param_limit_str)
                        usage.append("-" * 30)
        
        if usage:
            details += "This parameter is required for the following Flow Statistics calculations:\n"
            details += "-" * 30 + "\n"
            details += "\n".join(usage)
        else:
            details += "This parameter is not strictly required for the current Flow Statistics scenarios."

        # Show in a dialog similar to Flow Stats
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Basin Characteristic Details")
        dlg.resize(600, 400)
        layout = QtWidgets.QVBoxLayout(dlg)
        
        lbl = QtWidgets.QLabel(f"Details for {name}:")
        lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl)
        
        txt = QtWidgets.QPlainTextEdit()
        txt.setReadOnly(True)
        txt.setPlainText(details)
        # Set font to monospace
        font = QtGui.QFont("Courier")
        font.setStyleHint(QtGui.QFont.Monospace)
        font.setPointSize(10)
        txt.setFont(font)
        
        layout.addWidget(txt)
        
        btnbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        btnbox.accepted.connect(dlg.accept)
        layout.addWidget(btnbox)
        
        dlg.exec_()

    def show_flow_stat_details(self, item):
        row = item.row()
        stat_name = self.tabFlow.item(row, 0).text()
        val_str = self.tabFlow.item(row, 1).text()
        scenario_name = self.tabFlow.item(row, 2).text()
        region_name = self.tabFlow.item(row, 3).text()

        if not self.pour_point.flow_stats:
            return

        # Find the scenario and region data
        scenario_data = None
        estimate_region_data = None

        for entry in self.pour_point.flow_stats:
            scenario = entry.get('scenario', {})
            s_name = scenario.get('statisticGroupName', scenario.get('name', 'Unknown Scenario')) if isinstance(scenario, dict) else str(scenario)
            
            # If the scenario names don't match, we keep searching
            # Be mindful that exceptions create 'Error' stat_names inside a matching scenario name
            if s_name == scenario_name:
                if isinstance(scenario, dict):
                    for rr in scenario.get('regressionRegions', []):
                        if rr.get('name') == region_name or region_name == '':
                            scenario_data = rr
                            break
                
                estimate = entry.get('estimate', {})
                if isinstance(estimate, dict):
                    for rr in estimate.get('regressionRegions', []):
                        if rr.get('name') == region_name or region_name == '':
                            estimate_region_data = rr
                            break
                # Only break if we successfully matched a region, or if no region name was present
                if scenario_data or estimate_region_data or region_name == '':
                    break

        if not scenario_data and not estimate_region_data:
            QtWidgets.QMessageBox.information(self, "Details", "Could not find underlying API details for this region.")
            return

        details = f"Statistic: {stat_name}\n"
        details += f"Scenario: {scenario_name}\n"
        if region_name:
            details += f"Region: {region_name}\n"
        details += "\n"

        # Look for specific result limits/equations
        result_obj = None
        if estimate_region_data:
            for res in estimate_region_data.get('results', []):
                r_name = res.get('name', res.get('code', 'Unknown'))
                if r_name == stat_name:
                    result_obj = res
                    break

        if result_obj:
            val = result_obj.get('value', 'N/A')
            unit = format_superscript(result_obj.get('unit', {}).get('abbr', ''))
            details += f"Result Value: {val} {unit}\n"
            
            if 'equation' in result_obj:
                details += f"Equation: {result_obj.get('equation')}\n"
            
            error_val = result_obj.get('errors')
            if error_val:
                details += f"Calculation Errors/Warnings: {error_val}\n"
        else:
             details += f"Table Value: {val_str}\n"

        details += "\nRequired Basin Characteristics for this API calculation:\n"
        details += "-"*75 + "\n"

        if scenario_data and 'parameters' in scenario_data:
            # Build a text table
            details += f"{'Name':<35} | {'Code':<10} | {'Value':<10} | {'Limits'}\n"
            details += "-"*75 + "\n"
            for p in scenario_data['parameters']:
                limits = p.get('limits', {})
                min_lim = limits.get('min', 'none')
                max_lim = limits.get('max', 'none')
                lim_str = f"[{min_lim} to {max_lim}]"
                details += f"{p.get('name', '')[:33]:<35} | {p.get('code', ''):<10} | {str(p.get('value', 'N/A')):<10} | {lim_str}\n"
        else:
            details += "No required parameters mapped or provided by API.\n"

        # Check for overriding errors in the main container
        error_msg = None
        for entry in self.pour_point.flow_stats:
             if entry.get('error') and scenario_name in str(entry):
                  error_msg = entry.get('error')
        if error_msg:
             details += f"\nAPI Level Error:\n{error_msg}\n"
             
        # Show simple dialog
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Flow Statistic Details")
        dlg.resize(750, 450)
        
        layout = QtWidgets.QVBoxLayout(dlg)
        
        lbl = QtWidgets.QLabel("The logic limits, equations, and values returned natively by the StreamStats API before parsing:")
        lbl.setStyleSheet("font-style: italic; color: #777777;")
        layout.addWidget(lbl)
        
        txt = QtWidgets.QPlainTextEdit()
        txt.setReadOnly(True)
        txt.setPlainText(details)
        # Set font to monospace
        font = QtGui.QFont("Courier")
        font.setStyleHint(QtGui.QFont.Monospace)
        font.setPointSize(10)
        txt.setFont(font)
        
        layout.addWidget(txt)
        
        btnbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        btnbox.accepted.connect(dlg.accept)
        layout.addWidget(btnbox)
        
        dlg.exec_()
        
    def load_flow_statistics(self):
        flow_stats = self.pour_point.flow_stats
        self.tabFlow.setColumnCount(4)
        self.tabFlow.setHorizontalHeaderLabels(['Statistic', 'Value', 'Scenario', 'Region'])
        self.tabFlow.verticalHeader().setVisible(False)
        if flow_stats:
            rows = []
            for entry in flow_stats:
                scenario = entry.get('scenario', {})
                scenario_name = scenario.get('statisticGroupName', scenario.get('name', 'Unknown Scenario')) if isinstance(scenario, dict) else str(scenario)

                if 'error' in entry:
                    # In case of error, we try to preserve the scenario name and region if possible, though the API might have failed before the region was clear.
                    rows.append([scenario_name, 'Error', scenario_name, ''])
                else:
                    estimate = entry.get('estimate', {})
                    if isinstance(estimate, dict):
                        # The API returns results inside regressionRegions
                        regions = estimate.get('regressionRegions', [])
                        if not regions:
                            rows.append(['No calculations', 'N/A', scenario_name, ''])
                        for region in regions:
                            region_name = region.get('name', 'Unknown Region')
                            group_prefix = f"{scenario_name} ({region_name})"
                            results = region.get('results', [])
                            if not results:
                                rows.append(['No results', '', scenario_name, region_name])
                            for res in results:
                                stat_name = res.get('name', res.get('code', 'Unknown'))
                                stat_value = str(res.get('value', 'N/A'))
                                stat_unit = res.get('unit', {}).get('abbr', '')
                                
                                # Nice unit formatting
                                stat_unit = format_superscript(stat_unit)
                                    
                                val_str = f"{stat_value} {stat_unit}".strip()
                                rows.append([stat_name, (val_str, stat_value), scenario_name, region_name])
                    else:
                        rows.append(['Invalid Estimate format', '', scenario_name, ''])

            # Update columns to match new format
            self.tabFlow.setRowCount(len(rows))
            for row_idx, row_data in enumerate(rows):
                for col_idx, value in enumerate(row_data):
                    if col_idx == 1 and isinstance(value, tuple):
                        text, raw = value
                        item = QtWidgets.QTableWidgetItem(str(text))
                        item.setData(QtCore.Qt.UserRole, raw)
                        self.tabFlow.setItem(row_idx, col_idx, item)
                    else:
                        self.tabFlow.setItem(row_idx, col_idx, QtWidgets.QTableWidgetItem(str(value)))

            # Enable sorting
            self.tabFlow.setSortingEnabled(True)

            # Expand columns
            header = self.tabFlow.horizontalHeader()
            header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
            
            # Stretch the last two columns so they fill the remaining space
            header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
            header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)

            self.tabFlow.resizeColumnToContents(0)
            if self.tabFlow.columnWidth(0) > 300:
                self.tabFlow.setColumnWidth(0, 300)
                
            self.tabFlow.resizeColumnToContents(1)
        else:
            self.tabFlow.setRowCount(1)
            self.tabFlow.setItem(0, 0, QtWidgets.QTableWidgetItem('No flow statistics available'))
            self.tabFlow.setItem(0, 1, QtWidgets.QTableWidgetItem(''))
            self.tabFlow.setItem(0, 2, QtWidgets.QTableWidgetItem(''))

    def download_basin_characteristics(self):
        self.lblBasinStatus.setText(' Starting Basin Characteristics download...')
        QtWidgets.QApplication.processEvents()

        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.btnDownloadBasinChars.setEnabled(False)
        try:
            # The basin endpoints generally require the original delineation SSHydroRequest payload as input
            state_code = self.pour_point.state_code
            if not state_code:
                self.lblBasinStatus.setText(' Determining US State from coordinates...')
                QtWidgets.QApplication.processEvents()

                state_code, status = get_state_from_coordinates(self.pour_point.latitude, self.pour_point.longitude)
                if state_code is None:
                    raise Exception("Failed to determine US State of the point.")

            self.lblBasinStatus.setText(' Delineating watershed (this may take a moment)...')
            QtWidgets.QApplication.processEvents()

            watershed_data = delineate_watershed(self.pour_point.latitude, self.pour_point.longitude, state_code)

            self.lblBasinStatus.setText(' Retrieving basin characteristics...')
            QtWidgets.QApplication.processEvents()

            new_basin_chars = retrieve_basin_characteristics(watershed_data)

            # Fetch scenarios to ensure we know which parameters are required right away
            self.lblBasinStatus.setText(' Retrieving flow analysis scenarios...')
            QtWidgets.QApplication.processEvents()
            
            # Prepare metadata update, respecting current widget state
            metadata = self.metadata_widget.get_data()
            if 'system' not in metadata: metadata['system'] = {}
            metadata['system']['state_code'] = state_code

            try:
                new_flow_scenarios = retrieve_flow_scenarios(watershed_data, new_basin_chars)
                self.pour_point.flow_scenarios = new_flow_scenarios
                metadata['system']['flow_scenarios'] = new_flow_scenarios
            except Exception:
                # If scenarios fail, just keep the state code and basin chars
                pass

            # Update pour point and database
            self.lblBasinStatus.setText(' Updating pour point database...')
            QtWidgets.QApplication.processEvents()
            self.pour_point.update_stats(self.qris_project.project_file, new_basin_chars, self.pour_point.flow_stats, metadata)
            self.qris_project.project_changed.emit()

            self.load_basin_characteristics()
            self.lblBasinStatus.setText(' Basin characteristics successfully downloaded and refreshed.')

        except Exception as e:
            self.lblBasinStatus.setText(' Error downloading basin characteristics.')
            QtWidgets.QMessageBox.critical(self, 'Error', f'Error downloading basin characteristics:\n{str(e)}')
        finally:
            self.btnDownloadBasinChars.setEnabled(True)
            QtWidgets.QApplication.restoreOverrideCursor()

    def recalculate_flow_stats(self):
        # Update basin chars dictionary with user input
        if getattr(self, 'basin_model', None) and self.pour_point.basin_chars and 'parameters' in self.pour_point.basin_chars:
            for i, row in enumerate(self.basin_model._data): # row is [name, code, units, value, override_value]
                code = row[1]
                override_val = row[4]
                for param in self.pour_point.basin_chars['parameters']:
                    if param.get('code') == code:
                        if str(override_val).strip() != '':
                            try:
                                param['override_value'] = float(override_val)
                            except ValueError:
                                param['override_value'] = override_val
                        else:
                            # Clear the override if the user deletes their text
                            param.pop('override_value', None)
        
        self.lblFlowStatus.setText(' Starting Flow Statistics recalculation...')
        QtWidgets.QApplication.processEvents()
        
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.btnRecalculate.setEnabled(False)
        try:
            # Create a deep copy of basin_chars specifically for calculation
            # so we inject the overrides into 'value' exactly how StreamStats expects it
            calc_basin_chars = copy.deepcopy(self.pour_point.basin_chars) if self.pour_point.basin_chars else {'parameters': []}
            for param in calc_basin_chars.get('parameters', []):
                if 'override_value' in param and str(param['override_value']).strip() != '':
                    param['value'] = param['override_value']

            metadata_to_save = None
            if not self.pour_point.flow_scenarios:
                self.lblFlowStatus.setText(' Fetching missing flow scenarios transparently (may take a moment)...')
                QtWidgets.QApplication.processEvents()

                # Fallback for old projects: download missing flow scenarios transparently
                state_code, status = get_state_from_coordinates(self.pour_point.latitude, self.pour_point.longitude)
                if state_code is None:
                    raise Exception("Failed to determine US State to fetch missing flow scenarios.")
                
                watershed_data = delineate_watershed(self.pour_point.latitude, self.pour_point.longitude, state_code)
                new_scenarios = retrieve_flow_scenarios(watershed_data, calc_basin_chars)
                self.pour_point.flow_scenarios = new_scenarios
                
                # Setup metadata block to persist the newly downloaded scenarios
                if 'system' not in self.pour_point.metadata:
                    self.pour_point.metadata['system'] = {}
                self.pour_point.metadata['system']['flow_scenarios'] = self.pour_point.flow_scenarios
                metadata_to_save = self.pour_point.metadata

            self.lblFlowStatus.setText(' Calculating flow statistics via API...')
            QtWidgets.QApplication.processEvents()

            # Recalculate using the overridden parameters
            new_flow_stats = calculate_flow_statistics(self.pour_point.flow_scenarios, calc_basin_chars)
            
            # Update the pour point database record. Save the original basin_chars dictionary 
            # (which contains 'override_value') so overrides persist accurately between reloads.
            self.pour_point.update_stats(self.qris_project.project_file, self.pour_point.basin_chars, new_flow_stats, metadata=metadata_to_save)
            self.qris_project.project_changed.emit()
            
            # Refresh standard views
            self.load_flow_statistics()
            self.load_basin_characteristics()
            self.lblFlowStatus.setText(' Flow statistics recalculated successfully.')

            # switch to flow stats tab
            self.tabWidget.setCurrentWidget(self.tabFlowPage)
        except Exception as e:
            self.lblFlowStatus.setText(' Error recalculating flow statistics.')
            QtWidgets.QMessageBox.critical(self, 'Error', f'Error recalculating flow statistics:\n{str(e)}')
        finally:
            self.btnRecalculate.setEnabled(True)
            QtWidgets.QApplication.restoreOverrideCursor()

    def accept(self):

        if not validate_name(self, self.txtName):
            return
            
        metadata = self.metadata_widget.get_data()

        if self.pour_point is not None:
            try:
                self.pour_point.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), metadata)
                self.qris_project.project_changed.emit()
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A pour point with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Pour Point', str(ex))
                return

        super().accept()

    def _export_data(self, path, headers, data, table_name):
        if path.endswith('.json'):
            result = []
            for row in data:
                result.append(dict(zip(headers, row)))
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=4)
        elif path.endswith('.xlsx') or path.endswith('.xls'):
            try:
                df = pd.DataFrame(data, columns=headers)
                df.to_excel(path, index=False)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Excel Export Failed", f"Could not export to Excel, saving as CSV instead.\nError: {e}")
                path = os.path.splitext(path)[0] + '.csv'
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(data)
        else:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(data)

        QtWidgets.QMessageBox.information(self, "Success", f"{table_name} exported successfully.")

    def export_basin_table(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Basin Characteristics", "basin_characteristics.csv", "CSV Files (*.csv);;JSON Files (*.json);;Excel Files (*.xlsx *.xls)")
        if not path:
            return
        try:
            model = self.basinTable.model()
            if not model:
                return
            
            # Headers
            headers = []
            for c in range(model.columnCount(QtCore.QModelIndex())):
                header_data = model.headerData(c, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole)
                headers.append(str(header_data) if header_data else "")
            
            # Data
            data = []
            for r in range(model.rowCount(QtCore.QModelIndex())):
                row_data = []
                for c in range(model.columnCount(QtCore.QModelIndex())):
                    val = model.data(model.index(r, c), QtCore.Qt.DisplayRole)
                    row_data.append(str(val) if val is not None else "")
                data.append(row_data)

            self._export_data(path, headers, data, "Basin characteristics")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to export table:\n{e}")

    def export_flow_table(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Flow Statistics", "flow_statistics.csv", "CSV Files (*.csv);;JSON Files (*.json);;Excel Files (*.xlsx *.xls)")
        if not path:
            return
        try:
            # Headers
            headers = []
            for c in range(self.tabFlow.columnCount()):
                header_item = self.tabFlow.horizontalHeaderItem(c)
                headers.append(header_item.text() if header_item else "")
            
            # Data
            data = []
            for r in range(self.tabFlow.rowCount()):
                row_data = []
                for c in range(self.tabFlow.columnCount()):
                    item = self.tabFlow.item(r, c)
                    row_data.append(item.text() if item is not None else "")
                data.append(row_data)

            self._export_data(path, headers, data, "Flow statistics")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to export table:\n{e}")

    def setupUi(self):
        # self.setObjectName("PoutPoint")
        self.resize(800, 500)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblName = QtWidgets.QLabel()
        self.lblName.setText('Name')
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setToolTip('The name of the catchment')
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.horiz = QtWidgets.QHBoxLayout()
        self.vert.addLayout(self.horiz)

        self.lblLatitude = QtWidgets.QLabel()
        self.lblLatitude.setText('Latitude')
        self.horiz.addWidget(self.lblLatitude)

        self.txtLatitude = QtWidgets.QLineEdit()
        self.txtLatitude.setReadOnly(True)
        self.horiz.addWidget(self.txtLatitude)

        self.lblLongitude = QtWidgets.QLabel()
        self.lblLongitude.setText('Longitude')
        self.horiz.addWidget(self.lblLongitude)

        self.txtLongitude = QtWidgets.QLineEdit()
        self.txtLongitude.setReadOnly(True)
        self.horiz.addWidget(self.txtLongitude)

        # Create GroupBox for Analysis Options
        self.groupAnalysis = QtWidgets.QGroupBox('Initial Download Options')
        self.layoutAnalysis = QtWidgets.QVBoxLayout()
        self.groupAnalysis.setLayout(self.layoutAnalysis)
        self.vert.addWidget(self.groupAnalysis)

        self.grpOptions = QtWidgets.QButtonGroup(self)

        self.radDelineate = QtWidgets.QRadioButton()
        self.radDelineate.setText('Delineate Catchment Only')
        self.radDelineate.setChecked(True)
        self.layoutAnalysis.addWidget(self.radDelineate)
        self.grpOptions.addButton(self.radDelineate)

        self.radBasin = QtWidgets.QRadioButton()
        self.radBasin.setText('Include Basin Characteristics (additional 60 seconds)')
        self.layoutAnalysis.addWidget(self.radBasin)
        self.grpOptions.addButton(self.radBasin)

        self.radFlowStats = QtWidgets.QRadioButton()
        self.radFlowStats.setText('Include Flow Statistics (additional 60 seconds)')
        self.layoutAnalysis.addWidget(self.radFlowStats)
        self.grpOptions.addButton(self.radFlowStats)
        
        self.tabWidget = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tabWidget)

        # Basin Characteristics Tab
        self.tabBasinPage = QtWidgets.QWidget()
        layoutBasin = QtWidgets.QVBoxLayout(self.tabBasinPage)
        self.basinTable = QtWidgets.QTableView()
        self.basinTable.verticalHeader().hide()
        self.basinTable.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.basinTable.customContextMenuRequested.connect(self.show_basin_context_menu)
        self.basinTable.doubleClicked.connect(self.show_basin_details)
        layoutBasin.addWidget(self.basinTable)

        # Basin characteristics buttons
        buttonLayoutBasin = QtWidgets.QHBoxLayout()
        
        self.btnDownloadBasinChars = QtWidgets.QPushButton()
        self.btnDownloadBasinChars.setText("Download Basin Characteristics")
        self.btnDownloadBasinChars.clicked.connect(self.download_basin_characteristics)
        buttonLayoutBasin.addWidget(self.btnDownloadBasinChars)

        self.lblBasinStatus = QtWidgets.QLabel("")
        self.lblBasinStatus.setStyleSheet("font-style: italic;")
        buttonLayoutBasin.addWidget(self.lblBasinStatus)

        buttonLayoutBasin.addStretch()

        self.btnExportBasinTable = QtWidgets.QPushButton()
        self.btnExportBasinTable.setText("Export Table")
        self.btnExportBasinTable.clicked.connect(self.export_basin_table)
        buttonLayoutBasin.addWidget(self.btnExportBasinTable)

        layoutBasin.addLayout(buttonLayoutBasin)

        self.tabWidget.addTab(self.tabBasinPage, 'Basin Characteristics')

        # Flow Statistics Tab
        self.tabFlowPage = QtWidgets.QWidget()
        layoutFlow = QtWidgets.QVBoxLayout(self.tabFlowPage)
        
        self.tabFlow = QtWidgets.QTableWidget()
        self.tabFlow.itemDoubleClicked.connect(self.show_flow_stat_details)
        self.tabFlow.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tabFlow.customContextMenuRequested.connect(self.show_flow_context_menu)
        layoutFlow.addWidget(self.tabFlow)
        
        # Flow statistics buttons
        buttonLayoutFlow = QtWidgets.QHBoxLayout()

        self.btnRecalculate = QtWidgets.QPushButton()
        self.btnRecalculate.setText("Recalculate Flow Statistics")
        self.btnRecalculate.clicked.connect(self.recalculate_flow_stats)
        buttonLayoutFlow.addWidget(self.btnRecalculate)

        self.lblFlowStatus = QtWidgets.QLabel("")
        self.lblFlowStatus.setStyleSheet("font-style: italic;")
        buttonLayoutFlow.addWidget(self.lblFlowStatus)

        buttonLayoutFlow.addStretch()

        self.btnExportFlowTable = QtWidgets.QPushButton()
        self.btnExportFlowTable.setText("Export Table")
        self.btnExportFlowTable.clicked.connect(self.export_flow_table)
        buttonLayoutFlow.addWidget(self.btnExportFlowTable)

        layoutFlow.addLayout(buttonLayoutFlow)
        self.tabWidget.addTab(self.tabFlowPage, 'Flow Statistics')

        # Description Tab
        self.tabDescriptionPage = QtWidgets.QWidget()
        layoutDescription = QtWidgets.QVBoxLayout(self.tabDescriptionPage)
        self.txtDescription = QtWidgets.QPlainTextEdit()
        layoutDescription.addWidget(self.txtDescription)
        self.tabWidget.addTab(self.tabDescriptionPage, 'Description')

        # Metadata Tab
        self.tabWidget.addTab(self.metadata_widget, 'Metadata')
        
        # Add to Map checkbox
        self.chkAddToMap = QtWidgets.QCheckBox()
        self.chkAddToMap.setText('Add to Map')
        self.chkAddToMap.setChecked(True)
        self.vert.addWidget(self.chkAddToMap)

        # Add buttons
        self.vert.addLayout(add_standard_form_buttons(self, 'context/watershed-catchments'))


if __name__ == "__main__":

    app = QtWidgets.QApplication([])
    window = FrmPourPoint(None, 123, 123)
    window.show()
    app.exec_()




