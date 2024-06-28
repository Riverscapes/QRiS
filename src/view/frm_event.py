
import json

from PyQt5 import QtCore, QtGui, QtWidgets

from ..model.event import Event, PLANNING_EVENT_TYPE_ID, PLANNING_MACHINE_CODE, AS_BUILT_EVENT_TYPE_ID, AS_BUILT_MACHINE_CODE, DESIGN_EVENT_TYPE_ID, DESIGN_MACHINE_CODE, insert as insert_event
from ..model.db_item import DBItem, DBItemModel
from ..model.datespec import DateSpec
from ..model.project import Project
from ..model.layer import Layer

from .frm_date_picker import FrmDatePicker
from .frm_event_picker import FrmEventPicker
from .metadata import MetadataWidget
from .widgets.surface_library import SurfaceLibraryWidget

from datetime import date, datetime
from .utilities import validate_name, add_standard_form_buttons


DATA_CAPTURE_EVENT_TYPE_ID = 1


class FrmEvent(QtWidgets.QDialog):

    def __init__(self, parent, qris_project: Project, event_type_id: int = DATA_CAPTURE_EVENT_TYPE_ID, event: Event = None):
        super().__init__(parent)

        self.qris_project = qris_project
        self.protocols = []
        self.event_type_id = event_type_id
        # Note that "event" is already a method from QDialog(), hence the weird name
        self.the_event = event
        self.mandatory_layers = None

        init_metadata = None
        if event is not None and event.metadata is not None:
            # move any keys that are not 'metadata', 'system' or 'attributes' to 'system'
            init_metadata = event.metadata
            if 'system' not in init_metadata:
                init_metadata['system'] = dict()
            for key in list(init_metadata.keys()):
                if key not in ['metadata', 'system', 'attributes']:
                    init_metadata['system'][key] = init_metadata[key]
                    del init_metadata[key]
        self.metadata_widget = MetadataWidget(self, json.dumps(init_metadata))
        self.surface_library = SurfaceLibraryWidget(self, qris_project)

        self.setupUi()
        dce_type = 'Data Capture' if event_type_id == DATA_CAPTURE_EVENT_TYPE_ID else 'Planning'
        self.setWindowTitle(f'Create New {dce_type} Event' if event is None else f'Edit {dce_type} Event')

        self.tree_model = None
        self.load_layer_tree()

        self.layers_model = QtGui.QStandardItemModel()
        self.layer_list.setModel(self.layers_model)

        # Surface Rasters
        # self.surface_raster_model = QtGui.QStandardItemModel()
        # rtypes = self.qris_project.lookup_tables['lkp_raster_types']
        # for surface in qris_project.surface_rasters().values():
        #     item = QtGui.QStandardItem(f'{surface.name} ({rtypes[surface.raster_type_id].name})')
        #     item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        #     item.setData(surface, QtCore.Qt.UserRole)
        #     self.surface_raster_model.appendRow(item)

        #     checked_state = QtCore.Qt.Checked if event is not None and surface in event.rasters else QtCore.Qt.Unchecked
        #     item.setData(QtCore.QVariant(checked_state), QtCore.Qt.CheckStateRole)

        # self.vwRasterSurfaces.setModel(self.surface_raster_model)
        # self.vwRasterSurfaces.setModelColumn(1)

        self.platform_model = DBItemModel(qris_project.lookup_tables['lkp_platform'])
        self.representation_model = DBItemModel(qris_project.lookup_tables['lkp_representation'])
        self.representation_model._data.sort(key=lambda a: a[0])
        self.cboPlatform.setModel(self.platform_model)
        self.cboRepresentation.setModel(self.representation_model)

        self.optSingleDate.toggled.connect(self.on_opt_date_change)

        valley_bottoms: dict = qris_project.valley_bottoms.copy()
        valley_bottoms[0] = DBItem('', 0, 'None')
        self.valley_bottom_model = DBItemModel(valley_bottoms)
        self.valley_bottom_model.sort_data_by_key()
        self.cboValleyBottom.setModel(self.valley_bottom_model)
        self.cboValleyBottom.setCurrentIndex(0)

        if event is not None:
            self.txtName.setText(event.name)
            self.txtDescription.setPlainText(event.description)
            self.cboPlatform.setCurrentIndex(event.platform.id - 1)
            self.cboRepresentation.setCurrentIndex(event.representation.id - 1)

            self.uc_start.set_date_spec(event.start)
            self.uc_end.set_date_spec(event.end)
            if any(date is not None for date in [event.end.day, event.end.year, event.end.month]):
                self.optDateRange.setChecked(True)

            if self.metadata_widget.metadata is not None and 'system' in self.metadata_widget.metadata:
                if 'valley_bottom_id' in self.metadata_widget.metadata['system']:
                    self.cboValleyBottom.setCurrentIndex(self.valley_bottom_model.getItemIndexById(self.metadata_widget.metadata['system']['valley_bottom_id']))
                if 'phase' in self.metadata_widget.metadata['system']:
                    self.txtPhase.setText(self.metadata_widget.metadata['system']['phase'])

            for event_layer in event.event_layers:
                item = QtGui.QStandardItem(event_layer.layer.name)
                item.setData(event_layer.layer, QtCore.Qt.UserRole)
                item.setEditable(False)
                self.layers_model.appendRow(item)

            self.surface_library.set_selected_surface_ids([r.id for r in event.rasters])

        self.txtName.setFocus()

    def load_layer_tree(self):

        # if self.rdoAlphabetical.isChecked():
        #     self.load_alphabetical_tree()
        # else:
        self.load_hierarchical_tree()

    def load_hierarchical_tree(self):

        layer_names = [layer.name for protocol in self.qris_project.protocols.values() for method in protocol.methods for layer in method.layers]
        layer_names += [layer.name for layer in self.qris_project.non_method_layers.values()]
        duplicate_layers = [item for item in set(layer_names) if layer_names.count(item) > 1]

        # Rebuild the tree
        self.tree_model = QtGui.QStandardItemModel(self)
        for protocol in self.qris_project.protocols.values():
            protocol_si = QtGui.QStandardItem(protocol.name)
            if self.event_type_id == DATA_CAPTURE_EVENT_TYPE_ID:
                if protocol.has_custom_ui == 1:
                    continue
            if self.event_type_id == PLANNING_EVENT_TYPE_ID:
                if protocol.machine_code.lower() != PLANNING_MACHINE_CODE.lower():
                    continue
            if self.event_type_id == AS_BUILT_EVENT_TYPE_ID:
                if protocol.machine_code.lower() != AS_BUILT_MACHINE_CODE.lower():
                    continue
            if self.event_type_id == DESIGN_EVENT_TYPE_ID:
                if protocol.machine_code.lower() != DESIGN_MACHINE_CODE.lower():
                    continue

            protocol_si.setData(protocol, QtCore.Qt.UserRole)
            protocol_si.setEditable(False)
            # protocol_si.setCheckable(True)

            for method in protocol.methods:
                # method_si = QtGui.QStandardItem(method.name)
                # method_si.setEditable(False)
                # method_si.setData(method, QtCore.Qt.UserRole)
                # method_si.setCheckable(True)

                for layer in method.layers:
                    layer_name = layer.name if layer.name not in duplicate_layers else f'{layer.name} ({layer.geom_type})'
                    layer_si = QtGui.QStandardItem(layer_name)
                    layer_si.setEditable(False)
                    layer_si.setData(layer, QtCore.Qt.UserRole)
                    # layer_si.setCheckable(True)

                    # if layer in checked_layers:
                    #     layer_si.setCheckState(QtCore.Qt.Checked)

                    # if self.chkActiveLayers.checkState() == QtCore.Qt.Unchecked or layer_si.checkState() == QtCore.Qt.Checked:
                    # method_si.appendRow(layer_si)
                    protocol_si.appendRow(layer_si)

                # if method_si.hasChildren():
                #     # if self.chkActiveLayers.checkState() == QtCore.Qt.Unchecked or method_si.hasChildren():
                #     protocol_si.appendRow(method_si)

            if protocol_si.hasChildren():
                # if self.chkActiveLayers.checkState() == QtCore.Qt.Unchecked or protocol_si.hasChildren():
                self.tree_model.appendRow(protocol_si)

        # non_method_si = QtGui.QStandardItem('Layers without a method')
        # non_method_si.setEditable(False)
        # non_method_si.setData(None, QtCore.Qt.UserRole)
        # for non_method_layer in self.qris_project.non_method_layers.values():
        #     layer_name = non_method_layer.name if non_method_layer.name not in duplicate_layers else f'{non_method_layer.name} ({non_method_layer.geom_type})'
        #     layer_si = QtGui.QStandardItem(layer_name)
        #     layer_si.setEditable(False)
        #     layer_si.setData(non_method_layer, QtCore.Qt.UserRole)
        #     non_method_si.appendRow(layer_si)
        # self.tree_model.appendRow(non_method_si)

        self.layer_tree.setModel(self.tree_model)
        self.layer_tree.expandAll()
        # self.layer_tree.setExpanded(self.tree_model.indexFromItem(non_method_si), False)

        self.layer_tree.doubleClicked.connect(self.on_double_click_tree)


    # def load_alphabetical_tree(self):

    #     # Retain a list of any checked layers so they can be checked again once the three is loaded
    #     checked_layers = []
    #     self.get_checked_layers(None, checked_layers)

    #     # Rebuild the tree
    #     sorted_layers = sorted(self.qris_project.layers.values(), key=lambda x: x.name)
    #     self.tree_model = QtGui.QStandardItemModel(self)
    #     for layer in sorted_layers:
    #         item = QtGui.QStandardItem(layer.name)
    #         item.setData(layer, QtCore.Qt.UserRole)
    #         item.setCheckable(True)

    #         if layer in checked_layers:
    #             item.setCheckState(QtCore.Qt.Checked)

    #         if self.chkActiveLayers.checkState() == QtCore.Qt.Unchecked or item.checkState() == QtCore.Qt.Checked:
    #             self.tree_model.appendRow(item)

    #     self.layer_tree.setModel(self.tree_model)
    #     self.layer_tree.expandAll()

    # def on_check_children(self, index: QtCore.QModelIndex) -> None:
    #     modelItem = self.tree_model.itemFromIndex(index)
    #     self.check_children(modelItem)

    #     data = modelItem.data(QtCore.Qt.UserRole)
    #     self.check_all_layers_of_type(None, data, modelItem.checkState())

    # def check_all_layers_of_type(self, modelItem: QtGui.QStandardItem, layer, state: QtCore.Qt.CheckState) -> None:
    #     """ Ensures that if the user checks a particular layer then all instances of that layer type
    #     become checked in the tree."""

    #     if not self.tree_model:
    #         return

    #     if modelItem is None:
    #         modelItem = self.tree_model.invisibleRootItem()

    #     if modelItem.hasChildren():
    #         for i in range(modelItem.rowCount()):
    #             self.check_all_layers_of_type(modelItem.child(i), layer, state)
    #     else:
    #         data = modelItem.data(QtCore.Qt.UserRole)
    #         if data == layer and modelItem.checkState() != state:
    #             modelItem.setCheckState(state)

    # def get_checked_layers(self, modelItem: QtGui.QStandardItem, checked_layers: list) -> None:
    #     """return a list of the layers that are currently checked.
    #     This is used to get the state of checked items before rebuilding the tree"""

    #     if not self.tree_model:
    #         return

    #     if modelItem is None:
    #         modelItem = self.tree_model.invisibleRootItem()

    #     if modelItem.hasChildren():
    #         for i in range(modelItem.rowCount()):
    #             self.get_checked_layers(modelItem.child(i), checked_layers)
    #     else:
    #         if modelItem.checkState() == QtCore.Qt.Checked:
    #             checked_layers.append(modelItem.data(QtCore.Qt.UserRole))

    # def get_checked_layer_tree(self) -> list:
    #     """ Return a dictionary of the IDs of protocols, methods and layer IDs.
    #     This is stored in the database to be able to recrete the tree on edit."""

    #     layer_list = []
    #     modelItem = self.tree_model.invisibleRootItem()
    #     for p in range(modelItem.rowCount()):
    #         protocol_item = modelItem.child(p)
    #         protocol = protocol_item.data(QtCore.Qt.UserRole)
    #         for m in range(protocol_item.rowCount()):
    #             method_item = protocol_item.child(m)
    #             method = method_item.data(QtCore.Qt.UserRole)
    #             for li in range(method_item.rowCount()):
    #                 layer_item = method_item.child(li)
    #                 layer = layer_item.data(QtCore.Qt.UserRole)
    #                 if layer_item.checkState() == QtCore.Qt.Checked:
    #                     layer_list.append((protocol, method, layer))

    #     return layer_list

    # def check_children(self, item: QtGui.QStandardItem) -> None:
    #     itemCheckState = item.checkState()
    #     for i in range(item.rowCount()):
    #         child = item.child(i)
    #         child.setCheckState(itemCheckState)
    #         self.check_children(child)

    def on_double_click_tree(self, index):

        item = self.layer_tree.model().itemFromIndex(index)
        layer = item.data(QtCore.Qt.UserRole)
        if isinstance(layer, Layer):
            self.add_selected_layers(item)

    def on_add_layer_clicked(self):

        for index in self.layer_tree.selectedIndexes():
            modelItem = self.tree_model.itemFromIndex(index)
            self.add_selected_layers(modelItem)

    def on_add_from_dce_clicked(self):

        frm = FrmEventPicker(self, self.qris_project, self.event_type_id)
        frm.exec_()
        if frm.result() == QtWidgets.QDialog.Accepted:
            for layer in frm.layers:
                layer_item = QtGui.QStandardItem(layer.name)
                layer_item.setData(layer, QtCore.Qt.UserRole)
                self.add_selected_layers(layer_item)

    def add_selected_layers(self, item: QtGui.QStandardItem) -> None:

        if item is None:
            item = self.tree_model.invisibleRootItem()

        if item.hasChildren():
            for i in range(item.rowCount()):
                self.add_selected_layers(item.child(i))
        else:
            tree_layer = item.data(QtCore.Qt.UserRole)
            tree_name = item.text()
            # check if in list already
            for i in range(self.layers_model.rowCount()):
                list_layer = self.layers_model.item(i).data(QtCore.Qt.UserRole)

                if tree_layer == list_layer:
                    return
            # If got to here then the layer selected in the tree is not in use
            layer_item = QtGui.QStandardItem(tree_name)
            layer_item.setData(tree_layer, QtCore.Qt.UserRole)
            layer_item.setEditable(False)
            self.layers_model.appendRow(layer_item)

    def on_remove_layer(self):
        for index in self.layer_list.selectedIndexes():
            if self.mandatory_layers is not None:
                layer = self.layers_model.itemFromIndex(index).data(QtCore.Qt.UserRole)
                if layer.fc_name in self.mandatory_layers:
                    continue
            self.layers_model.removeRow(index.row())

    def on_opt_date_change(self):
        if self.optSingleDate.isChecked():
            self.lblEndDate.setVisible(False)
            self.uc_end.setVisible(False)
            self.lblStartDate.setText('Date')
        else:
            self.lblEndDate.setVisible(True)
            self.uc_end.setVisible(True)
            self.lblStartDate.setText('Start Date')

    def check_surface_types(self):
        """check that only one surface type of id == 4 is checked"""

        checked_dems = 0
        for raster in self.surface_library.get_selected_surfaces():
        # for i in range(self.surface_raster_model.rowCount()):
        #     item = self.surface_raster_model.item(i)
        #     if item.checkState() == QtCore.Qt.Checked:
        #         raster = item.data(QtCore.Qt.UserRole)
            if raster.raster_type_id == 4:
                checked_dems += 1
        return False if checked_dems > 1 else True

    def accept(self):

        selected_layers = []
        for index in range(self.layers_model.rowCount()):
            item = self.layers_model.item(index)
            selected_layers.append(item.data(QtCore.Qt.UserRole).fc_name)
        # make sure all mandatory layers are present
        if self.mandatory_layers is not None:
            if any(layer not in selected_layers for layer in self.mandatory_layers):
                QtWidgets.QMessageBox.warning(self, 'Error', f'All mandatory layers ({",".join(self.mandatory_layers)}) must be selected.')
                return

        if not self.check_surface_types():
            QtWidgets.QMessageBox.warning(self, 'Invalid Surface Types', 'Only one DEM can be selected')
            return

        start_date_valid, start_date_error_msg = self.uc_start.validate()
        if not start_date_valid:
            QtWidgets.QMessageBox.warning(self, 'Invalid Start Date', start_date_error_msg)
            self.uc_start.setFocus()
            return

        end_date_valid, end_date_error_msg = self.uc_end.validate()
        if not end_date_valid:
            QtWidgets.QMessageBox.warning(self, 'Invalid End Date', end_date_error_msg)
            self.uc_end.setFocus()
            return

        start_date = self.uc_start.get_date_spec()
        end_date = self.uc_end.get_date_spec()

        date_order_valid = check_if_date_order_valid(start_date, end_date)
        if not date_order_valid:
            QtWidgets.QMessageBox.warning(self, 'Invalid Date Order', "Start date must be before the end date.")
            self.uc_end.setFocus()
            return

        if not validate_name(self, self.txtName):
            return

        # There must be at least one layer!
        layers_in_use = [self.layers_model.item(i).data(QtCore.Qt.UserRole) for i in range(self.layers_model.rowCount())]
        if len(layers_in_use) < 1:
            QtWidgets.QMessageBox.warning(self, 'No Layers Selected', 'You must select at least one layer to continue.')
            return

        surface_rasters = self.surface_library.get_selected_surfaces()
        # for row in range(self.surface_raster_model.rowCount()):
        #     index = self.surface_raster_model.index(row, 0)
        #     check = self.surface_raster_model.data(index, QtCore.Qt.CheckStateRole)
        #     if check == QtCore.Qt.Checked:
        #         for raster in self.qris_project.surface_rasters().values():
        #             if raster == self.surface_raster_model.data(index, QtCore.Qt.UserRole):
        #                 surface_rasters.append(raster)
        #                 break
        
        if self.cboValleyBottom.currentText() != 'None':
            self.metadata_widget.add_system_metadata('valley_bottom_id', self.cboValleyBottom.currentData(QtCore.Qt.UserRole).id)
        else:
            self.metadata_widget.delete_item('system', 'valley_bottom_id')

        if self.txtPhase.text() != '':
            self.metadata_widget.add_system_metadata('phase', self.txtPhase.text())
        else:
            self.metadata_widget.delete_item('system', 'phase')

        if not self.metadata_widget.validate():
            return

        try:
            if self.the_event is not None:
                # Check if any GIS data might be lost
                for event_layer in self.the_event.event_layers:
                    if event_layer.layer not in layers_in_use:
                        response = QtWidgets.QMessageBox.question(self, 'Possible Data Loss',
                                                                  """One or more layers that were part of this data capture event are no longer associated with the event.
                            Continuing might lead to the loss of geospatial data. Do you want to continue?
                            "Click Yes to proceed and delete all data associated with layers that are no longer used by the
                            current data capture event protocols. Click No to stop and avoid any data loss.""")
                        if response == QtWidgets.QMessageBox.No:
                            return

                self.the_event.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), layers_in_use, surface_rasters, start_date, end_date, self.cboPlatform.currentData(QtCore.Qt.UserRole), self.cboRepresentation.currentData(QtCore.Qt.UserRole), self.metadata_widget.get_data())
                super().accept()
            else:
                self.the_event = insert_event(
                    self.qris_project.project_file,
                    self.txtName.text(),
                    self.txtDescription.toPlainText(),
                    self.uc_start.get_date_spec(),
                    self.uc_end.get_date_spec(),
                    '',
                    self.qris_project.lookup_tables['lkp_event_types'][self.event_type_id],
                    self.cboPlatform.currentData(QtCore.Qt.UserRole),
                    self.cboRepresentation.currentData(QtCore.Qt.UserRole),
                    layers_in_use,
                    surface_rasters,
                    self.metadata_widget.get_data()
                )

                self.qris_project.events[self.the_event.id] = self.the_event
                super().accept()

        except Exception as ex:
            if 'unique' in str(ex).lower():
                QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A data capture event with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                self.txtName.setFocus()
            else:
                QtWidgets.QMessageBox.warning(self, 'Error Saving Data Capture Event', str(ex))

    def setupUi(self):

        self.resize(575, 550)
        self.setMinimumSize(500, 400)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblName = QtWidgets.QLabel()
        self.lblName.setText('Name')
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.tab = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tab)
        self.horiz_layer_widget = QtWidgets.QWidget(self)
        self.horiz_layers = QtWidgets.QHBoxLayout(self.horiz_layer_widget)
        self.tab.addTab(self.horiz_layer_widget, 'Layers')

        # self.horiz_layer_buttons = QtWidgets.QHBoxLayout(self)
        # self.vert_layers.addLayout(self.horiz_layer_buttons)

        # self.rdoAlphabetical = QtWidgets.QRadioButton('Alphatetical', self)
        # self.horiz_layer_buttons.addWidget(self.rdoAlphabetical)

        # self.rdoHierarchical = QtWidgets.QRadioButton('Hierarchical', self)
        # self.rdoHierarchical.setChecked(True)
        # self.rdoHierarchical.toggled.connect(self.load_layer_tree)
        # self.horiz_layer_buttons.addWidget(self.rdoHierarchical)

        # self.chkActiveLayers = QtWidgets.QCheckBox('Show Only Active Layers', self)
        # self.chkActiveLayers.toggled.connect(self.load_layer_tree)
        # self.horiz_layer_buttons.addWidget(self.chkActiveLayers)

        # layer tree
        self.vert_layer_tree = QtWidgets.QVBoxLayout(self)
        self.horiz_layers.addLayout(self.vert_layer_tree)
        self.lblAllLayers = QtWidgets.QLabel('Available Layers')
        self.vert_layer_tree.addWidget(self.lblAllLayers)

        self.layer_tree = QtWidgets.QTreeView(self)
        self.layer_tree.setHeaderHidden(True)
        # self.layer_tree.clicked.connect(self.on_check_children)
        self.vert_layer_tree.addWidget(self.layer_tree)

        # Add Remove Buttons
        self.vert_buttons = QtWidgets.QVBoxLayout(self)
        self.horiz_layers.addLayout(self.vert_buttons)
        self.vert_add = QtWidgets.QVBoxLayout(self)
        self.vert_buttons.addLayout(self.vert_add)
        self.cmdAddLayer = QtWidgets.QPushButton('Add >>', self)
        self.cmdAddLayer.clicked.connect(self.on_add_layer_clicked)
        self.vert_add.addWidget(self.cmdAddLayer)
        self.cmdAddFromDCE = QtWidgets.QPushButton('Add From DCE >>', self)
        self.cmdAddFromDCE.clicked.connect(self.on_add_from_dce_clicked)
        self.vert_add.addWidget(self.cmdAddFromDCE)
        self.vert_remove = QtWidgets.QVBoxLayout(self)
        self.vert_buttons.addLayout(self.vert_remove)
        self.cmdRemoveLayer = QtWidgets.QPushButton('<< Remove', self)
        self.cmdRemoveLayer.clicked.connect(self.on_remove_layer)
        self.vert_remove.addWidget(self.cmdRemoveLayer)
        self.cmdRemoveAllLayers = QtWidgets.QPushButton('<< Remove All', self)
        self.cmdRemoveAllLayers.clicked.connect(lambda: self.layers_model.removeRows(0, self.layers_model.rowCount()))
        self.vert_remove.addWidget(self.cmdRemoveAllLayers)

        # Layers list
        self.vert_layers = QtWidgets.QVBoxLayout(self)
        self.horiz_layers.addLayout(self.vert_layers)
        # self.grpLayersInUse = QtWidgets.QGroupBox('Layers In Use')
        # self.vert_layers.addWidget(self.grpLayersInUse)
        # self.grpLayersInUse.setLayout(self.vert_layers)

        self.lblLayersInUse = QtWidgets.QLabel('Layers In Use')
        self.vert_layers.addWidget(self.lblLayersInUse)

        self.layer_list = QtWidgets.QListView(self)
        self.vert_layers.addWidget(self.layer_list)

        # Basic Properties Tab
        self.tabGridWidget = QtWidgets.QWidget()
        self.tabGrid = QtWidgets.QGridLayout(self.tabGridWidget)
        self.tab.addTab(self.tabGridWidget, 'Basic Properties')

        self.lblValleyBottom = QtWidgets.QLabel('Associated Valley Bottom')
        self.tabGrid.addWidget(self.lblValleyBottom, 0, 0, 1, 1)

        self.cboValleyBottom = QtWidgets.QComboBox()
        self.tabGrid.addWidget(self.cboValleyBottom, 0, 1, 1, 1)

        # row 2: as-built associated design

        self.lblPhase = QtWidgets.QLabel('Phase', self)
        self.tabGrid.addWidget(self.lblPhase, 2, 0, 1, 1)
        self.lblPhase.setVisible(False)

        self.txtPhase = QtWidgets.QLineEdit(self)
        self.txtPhase.setPlaceholderText('Phase 1, Phase 2, Pilot, Demo, Maintenance of Phase 1 etc.')
        self.tabGrid.addWidget(self.txtPhase, 2, 1, 1, 1)
        self.txtPhase.setVisible(False)

        self.optSingleDate = QtWidgets.QRadioButton('Single Point in Time')
        self.optSingleDate.setChecked(True)
        self.tabGrid.addWidget(self.optSingleDate, 3, 0, 1, 1)

        self.optDateRange = QtWidgets.QRadioButton('Date Range')
        self.tabGrid.addWidget(self.optDateRange, 4, 0, 1, 1)

        self.lblStartDate = QtWidgets.QLabel()
        self.lblStartDate.setText('Date')
        self.tabGrid.addWidget(self.lblStartDate, 5, 0, 1, 1)

        self.uc_start = FrmDatePicker(self)
        self.tabGrid.addWidget(self.uc_start, 5, 1, 1, 1)

        self.lblEndDate = QtWidgets.QLabel()
        self.lblEndDate.setText('End Date')
        self.lblEndDate.setVisible(False)
        self.tabGrid.addWidget(self.lblEndDate, 6, 0, 1, 1)

        self.uc_end = FrmDatePicker(self)
        self.uc_end.setVisible(False)
        self.tabGrid.addWidget(self.uc_end, 6, 1, 1, 1)

        self.lblPlatform = QtWidgets.QLabel()
        self.lblPlatform.setText('Event completed at')
        self.tabGrid.addWidget(self.lblPlatform, 7, 0, 1, 1)

        self.cboPlatform = QtWidgets.QComboBox()
        self.tabGrid.addWidget(self.cboPlatform, 7, 1, 1, 1)

        self.lblRepresentation = QtWidgets.QLabel("Representation")
        self.tabGrid.addWidget(self.lblRepresentation, 8, 0, 1, 1)

        self.cboRepresentation = QtWidgets.QComboBox()
        self.tabGrid.addWidget(self.cboRepresentation, 8, 1, 1, 1)

        verticalSpacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.tabGrid.addItem(verticalSpacer)

        # self.lblProtocols = QtWidgets.QLabel()
        # self.lblProtocols.setText('Protocols')
        # self.tabGrid.addWidget(self.lblProtocols, 3, 0, 1, 1)

        # self.vwProtocols = QtWidgets.QListView()
        # self.tabGrid.addWidget(self.vwProtocols)

        self.chkAddToMap = QtWidgets.QCheckBox()
        self.chkAddToMap.setChecked(False)
        self.chkAddToMap.setText('Add New Layers to Map')
        self.vert.addWidget(self.chkAddToMap)

        # Surface Rasters
        self.vert_surfaces = QtWidgets.QVBoxLayout(self)
        self.surfaces_widget = QtWidgets.QWidget(self)
        self.surfaces_widget.setLayout(self.vert_surfaces)
        self.vert_surfaces.addWidget(self.surface_library)
        self.tab.addTab(self.surfaces_widget, 'Surfaces')
        # self.tab.addTab(self.surface_library, 'Surfaces')

        # Description
        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.tab.addTab(self.txtDescription, 'Description')

        # Metadata
        self.tab.addTab(self.metadata_widget, 'Metadata')

        help_text = 'events' if self.event_type_id == DATA_CAPTURE_EVENT_TYPE_ID else 'designs'
        self.vert.addLayout(add_standard_form_buttons(self, help_text))


def check_if_date_order_valid(start_date: DateSpec, end_date: DateSpec):
    if start_date.year is None or end_date.month is None:
        return True
    elif start_date.month is None or end_date.month is None:
        if start_date.year <= end_date.year:
            return True
        else:
            return False
    elif start_date.day is None or end_date.day is None:
        start_dt = datetime(start_date.year, start_date.month, 1)
        end_dt = datetime(end_date.year, end_date.month, 1)
    else:
        start_dt = datetime(start_date.year, start_date.month, start_date.day)
        end_dt = datetime(end_date.year, end_date.month, end_date.day)

    if start_dt > end_dt:
        return False
    else:
        return True
