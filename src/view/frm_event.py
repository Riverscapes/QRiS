
from PyQt5 import QtCore, QtGui, QtWidgets

from ..model.event import Event, insert as insert_event
from ..model.db_item import DBItem, DBItemModel
from ..model.datespec import DateSpec
from ..model.project import Project

from .frm_date_picker import FrmDatePicker

from datetime import date, datetime
from .utilities import validate_name, add_standard_form_buttons


DATA_CAPTURE_EVENT_TYPE_ID = 1


class FrmEvent(QtWidgets.QDialog):

    def __init__(self, parent, qris_project: Project, event_type_id: int = DATA_CAPTURE_EVENT_TYPE_ID, event: Event = None):
        super().__init__(parent)

        self.qris_project = qris_project
        self.protocols = []
        self.metadata = None
        self.event_type_id = event_type_id
        # Note that "event" is already a method from QDialog(), hence the weird name
        self.the_event = event

        self.setupUi()
        self.setWindowTitle('Create New Data Capture Event' if event is None else 'Edit Data Capture Event')

        self.tree_model = None
        self.load_layer_tree()

        self.layers_model = QtGui.QStandardItemModel()
        self.layer_list.setModel(self.layers_model)

        # Basemaps
        self.basemap_model = QtGui.QStandardItemModel()
        for basemap in qris_project.basemaps().values():
            item = QtGui.QStandardItem(basemap.name)
            item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            item.setData(basemap, QtCore.Qt.UserRole)
            self.basemap_model.appendRow(item)

            checked_state = QtCore.Qt.Checked if event is not None and basemap in event.basemaps else QtCore.Qt.Unchecked
            item.setData(QtCore.QVariant(checked_state), QtCore.Qt.CheckStateRole)

        self.vwBasemaps.setModel(self.basemap_model)
        self.vwBasemaps.setModelColumn(1)

        self.platform_model = DBItemModel(qris_project.lookup_tables['lkp_platform'])
        self.cboPlatform.setModel(self.platform_model)

        if event is not None:
            self.txtName.setText(event.name)
            self.txtDescription.setPlainText(event.description)
            self.cboPlatform.setCurrentIndex(event.platform.id - 1)

            self.uc_start.set_date_spec(event.start)
            self.uc_end.set_date_spec(event.end)

            self.chkAddToMap.setCheckState(QtCore.Qt.Unchecked)
            self.chkAddToMap.setVisible(False)

            for event_layer in event.event_layers:
                item = QtGui.QStandardItem(event_layer.layer.name)
                item.setData(event_layer.layer, QtCore.Qt.UserRole)
                item.setEditable(False)
                self.layers_model.appendRow(item)

        self.txtName.setFocus()

    def load_layer_tree(self):

        # if self.rdoAlphabetical.isChecked():
        #     self.load_alphabetical_tree()
        # else:
        self.load_hierarchical_tree()

    def load_hierarchical_tree(self):

        # Rebuild the tree
        self.tree_model = QtGui.QStandardItemModel(self)
        for protocol in self.qris_project.protocols.values():
            protocol_si = QtGui.QStandardItem(protocol.name)
            protocol_si.setData(protocol, QtCore.Qt.UserRole)
            protocol_si.setEditable(False)
            # protocol_si.setCheckable(True)

            for method in protocol.methods:
                method_si = QtGui.QStandardItem(method.name)
                method_si.setEditable(False)
                method_si.setData(method, QtCore.Qt.UserRole)
                # method_si.setCheckable(True)

                for layer in method.layers:
                    layer_si = QtGui.QStandardItem(layer.name)
                    layer_si.setEditable(False)
                    layer_si.setData(layer, QtCore.Qt.UserRole)
                    # layer_si.setCheckable(True)

                    # if layer in checked_layers:
                    #     layer_si.setCheckState(QtCore.Qt.Checked)

                    # if self.chkActiveLayers.checkState() == QtCore.Qt.Unchecked or layer_si.checkState() == QtCore.Qt.Checked:
                    method_si.appendRow(layer_si)

                if method_si.hasChildren():
                    # if self.chkActiveLayers.checkState() == QtCore.Qt.Unchecked or method_si.hasChildren():
                    protocol_si.appendRow(method_si)

            if protocol_si.hasChildren():
                # if self.chkActiveLayers.checkState() == QtCore.Qt.Unchecked or protocol_si.hasChildren():
                self.tree_model.appendRow(protocol_si)

        self.layer_tree.setModel(self.tree_model)
        self.layer_tree.expandAll()

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

    def on_add_layer_clicked(self):

        for index in self.layer_tree.selectedIndexes():
            modelItem = self.tree_model.itemFromIndex(index)
            self.add_selected_layers(modelItem)

    def add_selected_layers(self, item: QtGui.QStandardItem) -> None:

        if item is None:
            item = self.tree_model.invisibleRootItem()

        if item.hasChildren():
            for i in range(item.rowCount()):
                self.add_selected_layers(item.child(i))
        else:
            tree_layer = item.data(QtCore.Qt.UserRole)
            # check if in list already
            for i in range(self.layers_model.rowCount()):
                list_layer = self.layers_model.item(i).data(QtCore.Qt.UserRole)

                if tree_layer == list_layer:
                    return
            # If got to here then the layer selected in the tree is not in use
            layer_item = QtGui.QStandardItem(tree_layer.name)
            layer_item.setData(tree_layer, QtCore.Qt.UserRole)
            layer_item.setEditable(False)
            self.layers_model.appendRow(layer_item)

    def on_remove_layer(self):
        for index in self.layer_list.selectedIndexes():
            self.layers_model.removeRow(index.row())

    def accept(self):
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
            QtWidgets.QMessageBox.warning(self, 'Invalid Date Order', "")
            self.uc_end.setFocus()
            return

        if not validate_name(self, self.txtName):
            return

        # There must be at least one layer!
        layers_in_use = [self.layers_model.item(i).data(QtCore.Qt.UserRole) for i in range(self.layers_model.rowCount())]
        if len(layers_in_use) < 1:
            QtWidgets.QMessageBox.warning(self, 'No Layers Selected', 'You must select at least one layer to continue.')
            return

        basemaps = []
        for row in range(self.basemap_model.rowCount()):
            index = self.basemap_model.index(row, 0)
            check = self.basemap_model.data(index, QtCore.Qt.CheckStateRole)
            if check == QtCore.Qt.Checked:
                for basemap in self.qris_project.basemaps().values():
                    if basemap == self.basemap_model.data(index, QtCore.Qt.UserRole):
                        basemaps.append(basemap)
                        break

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

            self.the_event.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), layers_in_use, basemaps, start_date, end_date, self.cboPlatform.currentData(QtCore.Qt.UserRole), self.metadata)
            super().accept()
        else:
            try:
                self.the_event = insert_event(
                    self.qris_project.project_file,
                    self.txtName.text(),
                    self.txtDescription.toPlainText(),
                    self.uc_start.get_date_spec(),
                    self.uc_end.get_date_spec(),
                    '',
                    self.qris_project.lookup_tables['lkp_event_types'][self.event_type_id],
                    self.cboPlatform.currentData(QtCore.Qt.UserRole),
                    layers_in_use,
                    basemaps,
                    self.metadata
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

        self.resize(500, 500)
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
        self.vert_buttpns = QtWidgets.QVBoxLayout(self)
        self.horiz_layers.addLayout(self.vert_buttpns)
        self.cmdAddLayer = QtWidgets.QPushButton('Add >>', self)
        self.cmdAddLayer.clicked.connect(self.on_add_layer_clicked)
        self.vert_buttpns.addWidget(self.cmdAddLayer)
        self.cmdRemoveLayer = QtWidgets.QPushButton('<< Remove', self)
        self.cmdRemoveLayer.clicked.connect(self.on_remove_layer)
        self.vert_buttpns.addWidget(self.cmdRemoveLayer)

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

        self.lblStartDate = QtWidgets.QLabel()
        self.lblStartDate.setText('Start Date')
        self.tabGrid.addWidget(self.lblStartDate, 0, 0, 1, 1)

        self.uc_start = FrmDatePicker(self)
        self.tabGrid.addWidget(self.uc_start, 0, 1, 1, 1)

        self.lblEndDate = QtWidgets.QLabel()
        self.lblEndDate.setText('End Date')
        self.tabGrid.addWidget(self.lblEndDate, 1, 0, 1, 1)

        self.uc_end = FrmDatePicker(self)
        self.tabGrid.addWidget(self.uc_end, 1, 1, 1, 1)

        self.lblPlatform = QtWidgets.QLabel()
        self.lblPlatform.setText('Event completed at')
        self.tabGrid.addWidget(self.lblPlatform, 2, 0, 1, 1)

        self.cboPlatform = QtWidgets.QComboBox()
        self.tabGrid.addWidget(self.cboPlatform, 2, 1, 1, 1)

        # self.lblProtocols = QtWidgets.QLabel()
        # self.lblProtocols.setText('Protocols')
        # self.tabGrid.addWidget(self.lblProtocols, 3, 0, 1, 1)

        # self.vwProtocols = QtWidgets.QListView()
        # self.tabGrid.addWidget(self.vwProtocols)

        self.chkAddToMap = QtWidgets.QCheckBox()
        self.chkAddToMap.setChecked(True)
        self.chkAddToMap.setText('Add to Map')
        self.vert.addWidget(self.chkAddToMap)

        # Basemaps
        self.vwBasemaps = QtWidgets.QListView()
        self.tab.addTab(self.vwBasemaps, 'Basemaps')

        # Description
        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.tab.addTab(self.txtDescription, 'Description')

        self.vert.addLayout(add_standard_form_buttons(self, 'events'))


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
