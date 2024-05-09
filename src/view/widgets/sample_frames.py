from qgis.core import QgsVectorLayer
from qgis.utils import iface

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal

from ...model.db_item import DBItem, DBItemModel, CheckableDBItemModel
from ...model.project import Project
from ...model.sample_frame import SampleFrame
from ...model.sample_frame import get_sample_frame_ids

from ...QRiS.qris_map_manager import QRisMapManager

class SampleFrameWidget(QtWidgets.QWidget):

    sample_frame_changed = pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget, qris_project: Project, qris_map_manager: QRisMapManager = None, first_index_empty: bool = False):
        super().__init__(parent)

        self.qris_project = qris_project
        self.qris_map_manager = qris_map_manager

        self.setupUi()

        # Sample Frames
        self.sample_frames = {id: sample_frame for id, sample_frame in self.qris_project.sample_frames.items()}
        if first_index_empty:
            choose_sample_frame = DBItem('None', 0, 'Choose Sample Frame...')
        else:
            choose_sample_frame = None
        self.sample_frames_model = DBItemModel(self.sample_frames, choose_sample_frame)
        self.cbo_sample_frame.setModel(self.sample_frames_model)
        if first_index_empty:
            self.cbo_sample_frame.setCurrentIndex(0)
        self.cbo_sample_frame.currentIndexChanged.connect(self.on_sample_frame_changed)
        self.load_sample_frame_features()

    def on_sample_frame_changed(self):

        if self.qris_map_manager is not None:
            sample_frame: SampleFrame = self.cbo_sample_frame.currentData(Qt.UserRole)
            sample_frame_layer = self.qris_map_manager.build_sample_frame_layer(sample_frame)

        self.load_sample_frame_features()

    def load_sample_frame_features(self):
        
        # clear the list view
        self.lst_sample_frame_features.setModel(None)
        sample_frame: SampleFrame = self.cbo_sample_frame.currentData(Qt.UserRole)
        if sample_frame is None:
            return
        frame_ids = get_sample_frame_ids(self.qris_project.project_file, sample_frame.id)
        self.sample_frame_features_model = CheckableDBItemModel(frame_ids)
        self.sample_frame_features_model.dataChanged.connect(self.on_sample_frame_features_changed)
        self.lst_sample_frame_features.setModel(self.sample_frame_features_model)
        self.lst_sample_frame_features.update()

    def on_sample_frame_features_changed(self):

        if self.qris_map_manager is not None:
            sample_frame: SampleFrame = self.cbo_sample_frame.currentData(Qt.UserRole)
            sample_frame_layer_tree = self.qris_map_manager.build_sample_frame_layer(sample_frame)
            sample_frame_layer: QgsVectorLayer = sample_frame_layer_tree.layer()
            iface.setActiveLayer(sample_frame_layer)
            sample_frame_feature_ids = self.get_selected_sample_frame_feature_ids()
            sample_frame_layer.removeSelection()
            sample_frame_layer.selectByIds(sample_frame_feature_ids)

        self.sample_frame_changed.emit()

    def btn_select_all_clicked(self):
        for i in range(self.sample_frame_features_model.rowCount(None)):
            index = self.sample_frame_features_model.index(i)
            self.sample_frame_features_model.setData(index, Qt.Checked, Qt.CheckStateRole)

    def btn_select_none_clicked(self):
        for i in range(self.sample_frame_features_model.rowCount(None)):
            index = self.sample_frame_features_model.index(i)
            self.sample_frame_features_model.setData(index, Qt.Unchecked, Qt.CheckStateRole)

    def selected_sample_frame(self):
        return self.cbo_sample_frame.currentData(Qt.UserRole)
    
    def selected_features_count(self):
        return sum([1 for i in range(self.sample_frame_features_model.rowCount(None)) if self.sample_frame_features_model.data(self.sample_frame_features_model.index(i), Qt.CheckStateRole) == Qt.Checked])

    def get_selected_sample_frame_feature_ids(self):
        return [self.sample_frame_features_model.data(self.sample_frame_features_model.index(i), Qt.UserRole).id for i in range(self.sample_frame_features_model.rowCount(None)) if self.sample_frame_features_model.data(self.sample_frame_features_model.index(i), Qt.CheckStateRole) == Qt.Checked]

    def get_selected_sample_frame_features(self):

        sample_frame: SampleFrame = self.cbo_sample_frame.currentData(Qt.UserRole)
        sample_frame_feature_ids = self.get_selected_sample_frame_feature_ids()

        fc_path = f"{self.qris_project.project_file}|layername={sample_frame.fc_name}|subset={sample_frame.fc_id_column_name} = {sample_frame.id}"
        temp_layer = QgsVectorLayer(fc_path, 'temp', 'ogr')

        for feature in temp_layer.getFeatures():
            if feature.id() in sample_frame_feature_ids:
                yield feature

    def setupUi(self):

        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.cbo_sample_frame = QtWidgets.QComboBox(self)
        self.vert.addWidget(self.cbo_sample_frame)

        self.lst_sample_frame_features = QtWidgets.QListView(self)
        self.lst_sample_frame_features.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.lst_sample_frame_features.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.vert.addWidget(self.lst_sample_frame_features)

        self.horiz_sample_frame_buttons = QtWidgets.QHBoxLayout(self)
        self.vert.addLayout(self.horiz_sample_frame_buttons)

        self.btn_select_all = QtWidgets.QPushButton('Select All')
        self.btn_select_all.clicked.connect(self.btn_select_all_clicked)
        self.horiz_sample_frame_buttons.addWidget(self.btn_select_all)

        self.btn_select_none = QtWidgets.QPushButton('Select None')
        self.btn_select_none.clicked.connect(self.btn_select_none_clicked)
        self.horiz_sample_frame_buttons.addWidget(self.btn_select_none)

        self.horiz_sample_frame_buttons.addStretch()