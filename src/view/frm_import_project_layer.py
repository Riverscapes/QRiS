import os

from qgis.PyQt import QtCore, QtGui, QtWidgets
from qgis.core import QgsVectorLayer, QgsWkbTypes

from ..model.project import Project
from ..model.event_layer import EventLayer
from ..model.db_item_spatial import DBItemSpatial
from ..model.scratch_vector import ScratchVector

_GEOM_TYPE_MAP = {
    'point': QgsWkbTypes.PointGeometry,
    'linestring': QgsWkbTypes.LineGeometry,
    'polygon': QgsWkbTypes.PolygonGeometry,
}


class FrmImportProjectLayer(QtWidgets.QDialog):
    """
    Picker dialog for importing features from an existing project layer into a
    DCE event layer.  Three vertically-stacked sections, each with its own
    radio button and dedicated combo box:

      1. Project Inputs  – sample frames, profiles, cross sections, pour points,
                           and context (scratch) vectors matching geometry type.
      2. DCE Same Type   – DCE event layers with the same protocol layer
                           definition; features are copied directly (no field
                           mapping needed).
      3. DCE Diff Type   – DCE event layers with a different protocol layer
                           definition but the same geometry type; opens the
                           attribute-mapping import form.
    """

    def __init__(self, parent, project: Project, db_item: EventLayer):
        super().__init__(parent)
        self.qris_project = project
        self.db_item = db_item
        self.geom_type = db_item.layer.geom_type  # 'Point' | 'Linestring' | 'Polygon'
        self.source_layer: QgsVectorLayer = None
        self.use_direct_copy: bool = False

        self.setupUi()
        self.setWindowTitle('Import from Existing Project Layer')

        self._populate_all_combos()

        self.rdoProject.toggled.connect(self._on_radio_changed)
        self.rdoDceSame.toggled.connect(self._on_radio_changed)
        self.rdoDceDiff.toggled.connect(self._on_radio_changed)

        self.rdoProject.setChecked(True)
        self._on_radio_changed()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _geom_matches(self, geom_type_str: str) -> bool:
        return geom_type_str.lower() == self.geom_type.lower()

    def _target_qgs_geom(self) -> QgsWkbTypes.GeometryType:
        return _GEOM_TYPE_MAP.get(self.geom_type.lower())

    def _make_model(self) -> QtGui.QStandardItemModel:
        return QtGui.QStandardItemModel()

    def _add_item(self, model: QtGui.QStandardItemModel, label: str, data):
        item = QtGui.QStandardItem(label)
        item.setData(data, QtCore.Qt.UserRole)
        model.appendRow(item)

    def _apply_model(self, combo: QtWidgets.QComboBox, model: QtGui.QStandardItemModel):
        if model.rowCount() == 0:
            placeholder = QtGui.QStandardItem('— No layers available —')
            placeholder.setData(None, QtCore.Qt.UserRole)
            model.appendRow(placeholder)
        combo.setModel(model)

    # ------------------------------------------------------------------
    # Population
    # ------------------------------------------------------------------

    def _populate_all_combos(self):
        project_file = self.qris_project.project_file
        geom = self.geom_type.lower()
        target_qgs_geom = self._target_qgs_geom()

        # --- Project Inputs ---
        project_model = self._make_model()

        if geom == 'polygon':
            for sf in self.qris_project.sample_frames.values():
                if sf.feature_count(project_file) > 0:
                    self._add_item(project_model, f'Sample Frame: {sf.name}', ('project', sf))
        elif geom == 'linestring':
            for p in self.qris_project.profiles.values():
                if p.feature_count(project_file) > 0:
                    self._add_item(project_model, f'Profile: {p.name}', ('project', p))
            for cs in self.qris_project.cross_sections.values():
                if cs.feature_count(project_file) > 0:
                    self._add_item(project_model, f'Cross Section: {cs.name}', ('project', cs))
        elif geom == 'point':
            for pp in self.qris_project.pour_points.values():
                if pp.feature_count(project_file) > 0:
                    self._add_item(project_model, f'Pour Point: {pp.name}', ('project', pp))

        # Scratch / context vectors (any geometry — check at runtime)
        for sv in self.qris_project.scratch_vectors.values():
            if os.path.exists(sv.gpkg_path):
                temp = QgsVectorLayer(
                    f'{sv.gpkg_path}|layername={sv.fc_name}', 'tmp', 'ogr')
                if (temp.isValid()
                        and temp.geometryType() == target_qgs_geom
                        and temp.featureCount() > 0):
                    self._add_item(project_model, f'Context Layer: {sv.name}', ('scratch', sv))

        self._apply_model(self.cboProject, project_model)

        # --- DCE Same Type ---
        same_model = self._make_model()
        for event in self.qris_project.events.values():
            for el in event.event_layers:
                if el.layer.id == self.db_item.layer.id and el.event_id != self.db_item.event_id:
                    if el.feature_count(project_file) > 0:
                        self._add_item(same_model,
                                       f'{event.name} — {el.layer.name}', ('dce', el))
        self._apply_model(self.cboDceSame, same_model)

        # --- DCE Different Type ---
        diff_model = self._make_model()
        for event in self.qris_project.events.values():
            for el in event.event_layers:
                if (self._geom_matches(el.layer.geom_type)
                        and el.layer.id != self.db_item.layer.id):
                    if el.feature_count(project_file) > 0:
                        self._add_item(diff_model,
                                       f'{event.name} — {el.layer.name}', ('dce', el))
        self._apply_model(self.cboDceDiff, diff_model)

    # ------------------------------------------------------------------
    # Radio toggle
    # ------------------------------------------------------------------

    def _on_radio_changed(self):
        project_on = self.rdoProject.isChecked()
        same_on = self.rdoDceSame.isChecked()
        diff_on = self.rdoDceDiff.isChecked()

        self.cboProject.setEnabled(project_on)
        self.cboDceSame.setEnabled(same_on)
        self.cboDceDiff.setEnabled(diff_on)

        active_combo = (
            self.cboProject if project_on
            else self.cboDceSame if same_on
            else self.cboDceDiff
        )
        has_data = active_combo.currentData(QtCore.Qt.UserRole) is not None
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(has_data)

    # ------------------------------------------------------------------
    # Accept
    # ------------------------------------------------------------------

    def accept(self):
        if self.rdoProject.isChecked():
            combo = self.cboProject
            self.use_direct_copy = False
        elif self.rdoDceSame.isChecked():
            combo = self.cboDceSame
            self.use_direct_copy = True
        else:
            combo = self.cboDceDiff
            self.use_direct_copy = False

        data = combo.currentData(QtCore.Qt.UserRole)
        if data is None:
            return

        kind, item = data
        label = combo.currentText()
        project_file = self.qris_project.project_file

        if kind == 'project':
            spatial_item: DBItemSpatial = item
            self.source_layer = spatial_item.get_temp_layer(project_file)
            self.source_layer.setName(label)
        elif kind == 'scratch':
            sv: ScratchVector = item
            self.source_layer = QgsVectorLayer(
                f'{sv.gpkg_path}|layername={sv.fc_name}', label, 'ogr')
        else:  # 'dce'
            el: EventLayer = item
            self.source_layer = QgsVectorLayer(
                f'{project_file}|layername={el.fc_name}', label, 'ogr')
            self.source_layer.setSubsetString(
                f'event_id = {el.event_id} AND event_layer_id = {el.layer.id}')

        super().accept()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def setupUi(self):
        self.resize(500, 260)
        self.setMinimumWidth(400)

        self.vert = QtWidgets.QVBoxLayout(self)

        # Section 1: Project Inputs
        self.rdoProject = QtWidgets.QRadioButton('Project Inputs')
        self.vert.addWidget(self.rdoProject)
        self.cboProject = QtWidgets.QComboBox()
        self.vert.addWidget(self.cboProject)

        self.vert.addSpacing(8)

        # Section 2: DCE Same Type
        self.rdoDceSame = QtWidgets.QRadioButton('DCE Layers (Same Layer Type)')
        self.vert.addWidget(self.rdoDceSame)
        self.cboDceSame = QtWidgets.QComboBox()
        self.vert.addWidget(self.cboDceSame)

        self.vert.addSpacing(8)

        # Section 3: DCE Different Type
        self.rdoDceDiff = QtWidgets.QRadioButton('DCE Layers (Different Layer Type)')
        self.vert.addWidget(self.rdoDceDiff)
        self.cboDceDiff = QtWidgets.QComboBox()
        self.vert.addWidget(self.cboDceDiff)

        self.vert.addStretch(1)

        self.buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.vert.addWidget(self.buttonBox)
