import os

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSettings

from ...model.project import Project
from ...model.event import PLANNING_EVENT_TYPE_ID, AS_BUILT_EVENT_TYPE_ID, DESIGN_EVENT_TYPE_ID, PLANNING_MACHINE_CODE, AS_BUILT_MACHINE_CODE, DESIGN_MACHINE_CODE
from ...model.layer import Layer

from ...QRiS.settings import Settings
from ...QRiS.protocol_parser import ProtocolDefinition, LayerDefinition, load_protocol_definitions

from ..frm_event_picker import FrmEventPicker
from ..frm_layer_metric_details import FrmLayerMetricDetails

DATA_CAPTURE_EVENT_TYPE_ID = 1

ORGANIZATION = 'Riverscapes'
APPNAME = 'QRiS'
SHOW_EXPERIMENTAL_PROTOCOLS = 'show_experimental_protocols'

class LayerTreeWidget(QtWidgets.QWidget):
    def __init__(self, parent, qris_project:Project, event_type_id: int, mandatory_layers=None):
        super(LayerTreeWidget, self).__init__(parent)
        
        self.qris_project = qris_project
        self.event_type_id = event_type_id
        self.mandatory_layers = mandatory_layers
        self.tree_model = QtGui.QStandardItemModel(self)

        settings = QSettings(ORGANIZATION, APPNAME)
        self.show_experimental = settings.value(SHOW_EXPERIMENTAL_PROTOCOLS, False, bool)

        self.setupUi()

        self.load_protocol_layer_tree()

        self.layers_model = QtGui.QStandardItemModel()
        self.layers_in_use_list.setModel(self.layers_model)


    def add_selected_layers(self, item: QtGui.QStandardItem) -> None:

        if item is None:
            item = self.tree_model.invisibleRootItem()

        if item.hasChildren():
            for i in range(item.rowCount()):
                self.add_selected_layers(item.child(i))
        else:
            tree_layer: LayerDefinition = item.data(QtCore.Qt.UserRole)
            tree_name = item.text()
            tree_protocol: ProtocolDefinition = item.parent().data(QtCore.Qt.UserRole)
            # check if in list already
            for i in range(self.layers_model.rowCount()):
                data = self.layers_model.item(i).data(QtCore.Qt.UserRole)
                if isinstance(data, Layer):
                    # Get the protocol of the layer
                    list_protocol = data.get_layer_protocol(self.qris_project.protocols)
                    if list_protocol is None:
                        continue
                    if list_protocol.unique_key() == f'{tree_protocol.machine_code}::{tree_protocol.version}':
                        if data.unique_key() == f'{tree_layer.id}::{tree_layer.version}':
                            return
                else:
                    list_protocol, list_layer = data
                    if tree_layer == list_layer:
                        return
                
            # If got to here then the layer selected in the tree is not in use
            # need the protocol name as well. should be the parent
            layer_item = QtGui.QStandardItem(tree_name)
            data_item = (tree_protocol, tree_layer)
            layer_item.setData(data_item, QtCore.Qt.UserRole)
            layer_item.setEditable(False)
            layer_item.setToolTip(f'{tree_protocol.label} ({tree_protocol.version}): {tree_layer.id} - Version {tree_layer.version}')
            self.layers_model.appendRow(layer_item)


    def load_protocol_layer_tree(self):

        # Load the protocols from the local project directory, user defined directory, and the resources protocol directory
        protocols = load_protocol_definitions(os.path.dirname(self.qris_project.project_file), self.show_experimental)

        layer_names = [layer.label for protocol in protocols for layer in protocol.layers]
        duplicate_layers = [item for item in set(layer_names) if layer_names.count(item) > 1]

        # Rebuild the tree
        self.tree_model.clear()
        for protocol in protocols:
            label = protocol.label
            if protocol.status == 'experimental':
                label += ' (Experimental)'
            protocol_si = QtGui.QStandardItem(label)
            if self.event_type_id == DATA_CAPTURE_EVENT_TYPE_ID:
                if protocol.protocol_type.lower() != 'dce':
                    continue
            # I don't think we need to add planning layers to the tree, I don't think they have any?
            # if self.event_type_id == PLANNING_EVENT_TYPE_ID:
            #     if protocol.machine_code.lower() != PLANNING_MACHINE_CODE.lower():
            #         continue
            if self.event_type_id == AS_BUILT_EVENT_TYPE_ID:
                if protocol.protocol_type.lower() != 'asbuilt':
                    continue
            if self.event_type_id == DESIGN_EVENT_TYPE_ID:
                if protocol.protocol_type.lower() != 'design':
                    continue

            protocol_si.setData(protocol, QtCore.Qt.UserRole)
            protocol_si.setEditable(False)

            for layer in protocol.layers:
                layer_name = layer.label if layer.label not in duplicate_layers else f'{layer.label} ({layer.geom_type})'
                layer_si = QtGui.QStandardItem(layer_name)
                layer_si.setEditable(False)
                layer_si.setToolTip(f'{layer.id} - Version {layer.version}')
                layer_si.setData(layer, QtCore.Qt.UserRole)
                protocol_si.appendRow(layer_si)

            if protocol_si.hasChildren():
                self.tree_model.appendRow(protocol_si)

        self.available_layers_tree.setModel(self.tree_model)
        self.available_layers_tree.expandAll()

        self.available_layers_tree.doubleClicked.connect(self.on_double_click_tree)
        self.available_layers_tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.available_layers_tree.customContextMenuRequested.connect(self.on_right_click_tree)

    def on_double_click_tree(self, index):

        item = self.available_layers_tree.model().itemFromIndex(index)
        layer = item.data(QtCore.Qt.UserRole)
        if isinstance(layer, Layer):
            self.add_selected_layers(item)

    def on_right_click_tree(self, position):
        index = self.available_layers_tree.indexAt(position)
        if not index.isValid():
            return

        item = self.available_layers_tree.model().itemFromIndex(index)
        layer = item.data(QtCore.Qt.UserRole)
        if isinstance(layer, Layer) or isinstance(layer, LayerDefinition):
            if isinstance(layer, LayerDefinition):
                protocol_definition: ProtocolDefinition = item.parent().data(QtCore.Qt.UserRole)
                layer.protocol_definition = protocol_definition
            menu = QtWidgets.QMenu(self)
            action = menu.addAction("Layer Details")
            action.triggered.connect(lambda: self.show_layer_properties(layer))
            menu.exec_(self.available_layers_tree.viewport().mapToGlobal(position))
            menu.close()  # Ensure the menu is closed after execution
            return
        else:
            return

    def on_right_click_list(self, position):
        index = self.layers_in_use_list.indexAt(position)
        if not index.isValid():
            return

        item = self.layers_in_use_list.model().itemFromIndex(index)
        layer = item.data(QtCore.Qt.UserRole)
        if isinstance(layer, tuple):
            layer_query: LayerDefinition = layer[1]
            protocol_definition: ProtocolDefinition = layer[0]
            layer_query.protocol_definition = protocol_definition
        elif isinstance(layer, Layer):
            layer_query = layer
        menu = QtWidgets.QMenu(self)
        action = menu.addAction("Layer Details")
        action.triggered.connect(lambda: self.show_layer_properties(layer_query))
        menu.exec_(self.layers_in_use_list.viewport().mapToGlobal(position))
        menu.close()

    def on_add_layer_clicked(self):

        for index in self.available_layers_tree.selectedIndexes():
            modelItem = self.tree_model.itemFromIndex(index)
            self.add_selected_layers(modelItem)

    def on_add_from_dce_clicked(self):

        frm = FrmEventPicker(self, self.qris_project, self.event_type_id)
        frm.exec_()
        if frm.result() == QtWidgets.QDialog.Accepted:
            for layer in frm.layers:
                layer: Layer
                # Traverse the tree and find the layer that matches the protocol and layer
                for i in range(self.tree_model.rowCount()):
                    protocol_item = self.tree_model.item(i)
                    protocol_definition: ProtocolDefinition = protocol_item.data(QtCore.Qt.UserRole)
                    for j in range(protocol_item.rowCount()):
                        layer_item = protocol_item.child(j)
                        layer_definition: LayerDefinition = layer_item.data(QtCore.Qt.UserRole)
                        layer_protocol = layer.get_layer_protocol(self.qris_project.protocols)
                        if f'{layer_definition.id}::{layer_definition.version}' == layer.unique_key():
                            if f'{protocol_definition.machine_code}::{protocol_definition.version}' == layer_protocol.unique_key():
                                self.add_selected_layers(layer_item)
                                break

    def on_remove_layer(self):
        for index in self.layers_in_use_list.selectedIndexes():
            if self.mandatory_layers is not None:
                layer = self.layers_model.itemFromIndex(index).data(QtCore.Qt.UserRole)
                if layer.fc_name in self.mandatory_layers:
                    continue
            self.layers_model.removeRow(index.row())

    def show_layer_properties(self, layer: Layer):

        frm = FrmLayerMetricDetails(self, self.qris_project, layer)
        frm.exec_()
        if frm.result() == QtWidgets.QDialog.Accepted:
            return
        else:
            return

    def on_show_experimental_changed(self, state):
        self.show_experimental = state == QtCore.Qt.Checked
        if self.show_experimental:
            QtWidgets.QMessageBox.warning(self, "Experimental Protocols", "Experimental protocols are protocols that are still under development and testing. They may not be fully functional and can change without notice. Please backup your project before using and proceed with caution.")
        self.load_protocol_layer_tree()

    def setupUi(self):
        
        self.horiz_layers = QtWidgets.QHBoxLayout(self)
        self.setLayout(self.horiz_layers)

        # layer tree
        self.vert_layer_tree = QtWidgets.QVBoxLayout(self)
        self.horiz_layers.addLayout(self.vert_layer_tree)
        self.lblAllLayers = QtWidgets.QLabel('Available Layers')
        self.vert_layer_tree.addWidget(self.lblAllLayers)

        self.available_layers_tree = QtWidgets.QTreeView(self)
        self.available_layers_tree.setHeaderHidden(True)
        self.available_layers_tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.available_layers_tree.customContextMenuRequested.connect(self.on_right_click_tree)
        self.vert_layer_tree.addWidget(self.available_layers_tree)

        chk_show_experimental = QtWidgets.QCheckBox('Show Experimental Protocols', self)
        chk_show_experimental.setChecked(self.show_experimental)
        chk_show_experimental.stateChanged.connect(self.on_show_experimental_changed)
        self.vert_layer_tree.addWidget(chk_show_experimental)

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

        self.lblLayersInUse = QtWidgets.QLabel('Layers In Use')
        self.vert_layers.addWidget(self.lblLayersInUse)

        self.layers_in_use_list = QtWidgets.QListView(self)
        # set right click menu
        self.layers_in_use_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.layers_in_use_list.customContextMenuRequested.connect(self.on_right_click_list)
        self.vert_layers.addWidget(self.layers_in_use_list)

        # dummy label to take up space so the list view matches the protocol tree height
        lbl_empty = QtWidgets.QLabel('')
        self.vert_layers.addWidget(lbl_empty)
