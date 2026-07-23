from qgis.PyQt import QtCore, QtWidgets

from ..model.db_item import DBItemModel
from ..model.profile import Profile
from ..model.project import Project
from .utilities import add_standard_form_buttons


class FrmOrderByCenterline(QtWidgets.QDialog):
    """
    Minimal dialog that lets the user choose a centerline profile before
    the calling code runs OrderByLineTask.  The dialog only handles UI;
    the task is launched by the caller after exec_() returns Accepted.
    """

    def __init__(self, parent, qris_project: Project):
        super().__init__(parent)

        self.qris_project = qris_project
        self.setWindowTitle("Set Order by Centerline")
        self.resize(350, 130)
        self.setMinimumSize(300, 110)

        self._setup_ui()
        self._load_centerlines()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def selected_profile(self) -> Profile:
        """Returns the Profile selected by the user, or None."""
        return self.cboCenterline.currentData(QtCore.Qt.UserRole)

    def update_display_label(self) -> bool:
        """Returns True if the user also wants display_label updated."""
        return self.chkUpdateDisplayLabel.isChecked()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_centerlines(self):
        centerlines = {id: profile for id, profile in self.qris_project.profiles.items() if profile.profile_type_id == Profile.ProfileTypes.CENTERLINE_PROFILE_TYPE}
        self.cboCenterline.setModel(DBItemModel(centerlines))

    def accept(self):
        if self.selected_profile() is None:
            QtWidgets.QMessageBox.warning(self, "No Centerline Selected", "Please select a centerline profile.")
            return
        super().accept()

    def _setup_ui(self):
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        grid = QtWidgets.QGridLayout()
        self.vert.addLayout(grid)

        grid.addWidget(QtWidgets.QLabel("Centerline"), 0, 0)

        self.cboCenterline = QtWidgets.QComboBox()
        self.cboCenterline.setToolTip("Select the centerline profile to use for ordering features.")
        grid.addWidget(self.cboCenterline, 0, 1)

        self.chkUpdateDisplayLabel = QtWidgets.QCheckBox("Also update Display Label")
        self.chkUpdateDisplayLabel.setToolTip("Write the sort position (1, 2, 3…) to the display_label field as well.\nUseful when display_label is null or out of date.")
        self.chkUpdateDisplayLabel.setChecked(False)
        grid.addWidget(self.chkUpdateDisplayLabel, 1, 0, 1, 2)

        self.vert.addLayout(add_standard_form_buttons(self, "inputs/sample-frames"))
