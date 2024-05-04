from qgis.core import QgsVectorLayer

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal

from ...model.db_item import DBItemModel, CheckableDBItemModel
from ...model.project import Project
from ...model.sample_frame import SampleFrame
from ...model.sample_frame import get_sample_frame_ids


class SampleFrameWidget(QtWidgets.QWidget):

    sample_frame_changed = pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget, qris_project: Project):
        super().__init__(parent)

        self.qris_project = qris_project

        self.setupUi()

        # Sample Frames
        self.sample_frames = {id: sample_frame for id, sample_frame in self.qris_project.sample_frames.items()}
        self.sample_frames_model = DBItemModel(self.sample_frames)
        self.cbo_sample_frame.setModel(self.sample_frames_model)
        self.cbo_sample_frame.currentIndexChanged.connect(self.load_sample_frames)
        self.load_sample_frames()

    def load_sample_frames(self):
        
        # clear the list view
        self.lst_sample_frame_features.setModel(None)
        sample_frame: SampleFrame = self.cbo_sample_frame.currentData(Qt.UserRole)
        frame_ids = get_sample_frame_ids(self.qris_project.project_file, sample_frame.id)
        self.sample_frames_model = CheckableDBItemModel(frame_ids)
        self.sample_frames_model.dataChanged.connect(self.sample_frame_changed.emit)
        self.lst_sample_frame_features.setModel(self.sample_frames_model)
        self.lst_sample_frame_features.update()

    def btn_select_all_clicked(self):
        for i in range(self.sample_frames_model.rowCount(None)):
            index = self.sample_frames_model.index(i)
            self.sample_frames_model.setData(index, Qt.Checked, Qt.CheckStateRole)

    def btn_select_none_clicked(self):
        for i in range(self.sample_frames_model.rowCount(None)):
            index = self.sample_frames_model.index(i)
            self.sample_frames_model.setData(index, Qt.Unchecked, Qt.CheckStateRole)

    def selected_sample_frame(self):
        return self.cbo_sample_frame.currentData(Qt.UserRole)
    
    def selected_features_count(self):
        return sum([1 for i in range(self.sample_frames_model.rowCount(None)) if self.sample_frames_model.data(self.sample_frames_model.index(i), Qt.CheckStateRole) == Qt.Checked])

    def get_selected_sample_frame_features(self):

        sample_frame: SampleFrame = self.cbo_sample_frame.currentData(Qt.UserRole)

        fc_path = f"{self.qris_project.project_file}|layername={sample_frame.fc_name}|subset={sample_frame.fc_id_column_name} = {sample_frame.id}"
        temp_layer = QgsVectorLayer(fc_path, 'temp', 'ogr')

        for feature in temp_layer.getFeatures():
            yield feature

    def setupUi(self):

        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.horiz_sample_frame = QtWidgets.QHBoxLayout(self)
        self.vert.addLayout(self.horiz_sample_frame)

        self.cbo_sample_frame = QtWidgets.QComboBox(self)
        self.horiz_sample_frame.addWidget(self.cbo_sample_frame)

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