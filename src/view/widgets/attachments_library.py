from qgis.PyQt import QtCore, QtGui, QtWidgets

from ..frm_attachment import FrmAttachment

from ...QRiS.settings import Settings

from ...model.project import Project
from ...model.event import Event
from ...model.attachment import (
    Attachment,
    load_dce_attachments,
    associate_attachment_with_dce,
    disassociate_attachment_from_dce,
)


class AttachmentsLibraryWidget(QtWidgets.QWidget):
    """
    Lists attachments associated with an event (DCE, Design, or As-Built) and provides:
      - Associate an existing project attachment
      - Add a new file or web-link attachment (and auto-associate it)
      - Edit the purpose of an existing association
      - Disassociate an attachment (does NOT delete the attachment)

    Each association stores an optional 'purpose' in the event_attachments.metadata JSON.
    The purpose dropdown is populated at runtime from resources/lookups.json;
    users may also type a free-form value.
    """

    def __init__(self, parent: QtWidgets.QWidget, qris_project: Project, dce_event: Event):
        super().__init__(parent)

        self.qris_project = qris_project
        self.dce_event = dce_event
        self._purposes = Settings().get_lookup_values('attachments', 'purpose')
        # dict: attachment_id -> (Attachment, assoc_metadata)
        self._dce_attachments: dict = {}
        # ids that were associated when the form opened — used to diff on save()
        self._original_attachment_ids: set = set()

        self._setup_ui()
        self._load_attachments()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reload(self):
        self._load_attachments()

    def save(self):
        """Write pending association changes to the database. Call from the parent form's accept()."""
        if self.dce_event is None:
            return
        # Delete associations that were removed since the form opened
        for aid in self._original_attachment_ids - set(self._dce_attachments.keys()):
            disassociate_attachment_from_dce(self.qris_project.project_file, self.dce_event.id, aid)
        # Write all current associations (INSERT OR REPLACE handles both new and updated)
        for aid, (att, meta) in self._dce_attachments.items():
            purpose = meta.get('purpose') if meta else None
            associate_attachment_with_dce(self.qris_project.project_file, self.dce_event.id, aid, purpose)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_attachments(self):
        if self.dce_event is None:
            return
        self._dce_attachments = load_dce_attachments(
            self.qris_project.project_file, self.dce_event.id
        )
        self._original_attachment_ids = set(self._dce_attachments.keys())
        self._refresh_table()

    def _refresh_table(self):
        search = self.txt_search.text().lower().strip()

        self.table.setUpdatesEnabled(False)
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        for attachment_id, (attachment, assoc_meta) in self._dce_attachments.items():
            name = attachment.name or ''
            purpose = assoc_meta.get('purpose', '') if assoc_meta else ''
            label = attachment.attachment_type_label or ''
            date = attachment.date or ''

            if search and search not in name.lower() and search not in purpose.lower():
                continue

            row = self.table.rowCount()
            self.table.insertRow(row)

            icon_alias = 'link' if attachment.attachment_type == Attachment.TYPE_WEB_LINK else 'file'

            name_item = QtWidgets.QTableWidgetItem(name)
            name_item.setData(QtCore.Qt.UserRole, attachment_id)
            name_item.setIcon(QtGui.QIcon(f':/plugins/qris_toolbar/{icon_alias}'))
            name_item.setFlags(name_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)

            # Purpose cell — editable combobox embedded in the table
            cbo_purpose = QtWidgets.QComboBox()
            cbo_purpose.setEditable(True)
            cbo_purpose.addItem('')
            for p in self._purposes:
                cbo_purpose.addItem(p)
            # Preserve any existing value even if not in the current list
            if purpose and cbo_purpose.findText(purpose) == -1:
                cbo_purpose.addItem(purpose)
            cbo_purpose.setCurrentText(purpose)
            cbo_purpose.setProperty('attachment_id', attachment_id)
            cbo_purpose.currentTextChanged.connect(self._on_purpose_changed)
            self.table.setCellWidget(row, 1, cbo_purpose)

            type_item = QtWidgets.QTableWidgetItem(label)
            type_item.setFlags(type_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, 2, type_item)

            date_item = QtWidgets.QTableWidgetItem(date)
            date_item.setFlags(date_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, 3, date_item)

        self.table.setUpdatesEnabled(True)
        self.table.blockSignals(False)
        self._update_button_states()
        self._update_summary()

    def _update_button_states(self):
        has_selection = self.table.currentRow() >= 0
        self.btn_disassociate.setEnabled(has_selection)

    def _update_summary(self):
        total = len(self._dce_attachments)
        showing = self.table.rowCount()
        noun = 'reference' if total == 1 else 'references'
        if total == showing:
            self.lbl_summary.setText(f'{total} {noun}')
        else:
            self.lbl_summary.setText(f'Showing {showing} of {total} {noun}')

    def _attachment_id_at_row(self, row: int):
        item = self.table.item(row, 0)
        return item.data(QtCore.Qt.UserRole) if item else None

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_purpose_changed(self, text: str):
        # Update in-memory only — save() writes to DB on form accept
        cbo = self.sender()
        attachment_id = cbo.property('attachment_id')
        if attachment_id is None:
            return
        if attachment_id in self._dce_attachments:
            att, meta = self._dce_attachments[attachment_id]
            meta = meta.copy() if meta else {}
            meta['purpose'] = text.strip() or None
            self._dce_attachments[attachment_id] = (att, meta)

    def on_associate_existing(self):
        already_associated = set(self._dce_attachments.keys())
        candidates = {
            aid: att
            for aid, att in self.qris_project.attachments.items()
            if aid not in already_associated
        }

        if not candidates:
            QtWidgets.QMessageBox.information(
                self,
                'No Attachments Available',
                'All project attachments are already associated with this event, '
                'or no attachments exist yet.'
            )
            return

        dlg = _AttachmentPickerDialog(self, candidates, self._purposes)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return

        for aid, purpose in dlg.selected_with_purpose():
            att = self.qris_project.attachments[aid]
            meta = {'purpose': purpose.strip()} if purpose and purpose.strip() else {}
            self._dce_attachments[aid] = (att, meta)
        self._refresh_table()

    def on_add_new(self, attachment_type: str):
        

        frm = FrmAttachment(self, self.qris_project, attachment_type=attachment_type)
        old_ids = set(self.qris_project.attachments.keys())

        if frm.exec_() != QtWidgets.QDialog.Accepted:
            return

        new_ids = set(self.qris_project.attachments.keys()) - old_ids
        if not new_ids:
            return

        # Ask for purpose after adding
        purpose = _ask_purpose(self, self._purposes)
        for aid in new_ids:
            att = self.qris_project.attachments[aid]
            meta = {'purpose': purpose.strip()} if purpose and purpose.strip() else {}
            self._dce_attachments[aid] = (att, meta)
        self._refresh_table()

    def on_disassociate(self):
        row = self.table.currentRow()
        attachment_id = self._attachment_id_at_row(row)
        if attachment_id is None:
            return

        attachment, _ = self._dce_attachments[attachment_id]
        reply = QtWidgets.QMessageBox.question(
            self,
            'Disassociate Reference',
            f'Remove the reference to "{attachment.name}" from this event?\n\n'
            'The attachment will remain in the project.',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if reply != QtWidgets.QMessageBox.Yes:
            return

        del self._dce_attachments[attachment_id]
        self._refresh_table()

    def on_open_attachment(self, row, _col):
        attachment_id = self._attachment_id_at_row(row)
        if attachment_id is None:
            return
        attachment, _ = self._dce_attachments[attachment_id]
        if attachment.attachment_type == Attachment.TYPE_WEB_LINK:
            import webbrowser
            webbrowser.open(attachment.path)
        else:
            path = attachment.attachment_path(self.qris_project.project_file)
            if os.path.isfile(path):
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))
            else:
                QtWidgets.QMessageBox.warning(
                    self, 'File Not Found',
                    f'The attachment file could not be found:\n{path}'
                )

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        # --- Filter bar ---
        horiz_filter = QtWidgets.QHBoxLayout()
        layout.addLayout(horiz_filter)

        self.txt_search = QtWidgets.QLineEdit()
        self.txt_search.setPlaceholderText('Search references\u2026')
        self.txt_search.textChanged.connect(self._refresh_table)
        horiz_filter.addWidget(self.txt_search)

        btn_clear = QtWidgets.QPushButton()
        btn_clear.setIcon(QtGui.QIcon(':/plugins/qris_toolbar/clear_filter'))
        btn_clear.setToolTip('Clear search')
        btn_clear.clicked.connect(self.txt_search.clear)
        horiz_filter.addWidget(btn_clear)

        horiz_filter.addStretch()

        # --- Table ---
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Name', 'Purpose', 'Type', 'Date'])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._update_button_states)
        self.table.cellDoubleClicked.connect(self.on_open_attachment)
        layout.addWidget(self.table)

        # --- Bottom bar ---
        horiz_bottom = QtWidgets.QHBoxLayout()
        layout.addLayout(horiz_bottom)

        self.lbl_summary = QtWidgets.QLabel('')
        horiz_bottom.addWidget(self.lbl_summary)

        horiz_bottom.addStretch()

        self.btn_associate = QtWidgets.QPushButton('Associate Existing\u2026')
        self.btn_associate.setIcon(QtGui.QIcon(':/plugins/qris_toolbar/add_to_map'))
        self.btn_associate.setToolTip('Associate an existing project attachment with this event')
        self.btn_associate.clicked.connect(self.on_associate_existing)
        horiz_bottom.addWidget(self.btn_associate)

        self.btn_add_file = QtWidgets.QPushButton('Add New File\u2026')
        self.btn_add_file.setIcon(QtGui.QIcon(':/plugins/qris_toolbar/add_file'))
        self.btn_add_file.setToolTip('Add a new file attachment and associate it with this event')
        self.btn_add_file.clicked.connect(lambda: self.on_add_new(Attachment.TYPE_FILE))
        horiz_bottom.addWidget(self.btn_add_file)

        self.btn_add_link = QtWidgets.QPushButton('Add New Link\u2026')
        self.btn_add_link.setIcon(QtGui.QIcon(':/plugins/qris_toolbar/add_link'))
        self.btn_add_link.setToolTip('Add a new web-link attachment and associate it with this event')
        self.btn_add_link.clicked.connect(lambda: self.on_add_new(Attachment.TYPE_WEB_LINK))
        horiz_bottom.addWidget(self.btn_add_link)

        self.btn_disassociate = QtWidgets.QPushButton('Disassociate')
        self.btn_disassociate.setIcon(QtGui.QIcon(':/plugins/qris_toolbar/delete'))
        self.btn_disassociate.setToolTip(
            'Remove the reference between the selected attachment and this event '
            '(does not delete the attachment)'
        )
        self.btn_disassociate.setEnabled(False)
        self.btn_disassociate.clicked.connect(self.on_disassociate)
        horiz_bottom.addWidget(self.btn_disassociate)


# ---------------------------------------------------------------------------
# Helper: standalone "pick a purpose" dialog
# ---------------------------------------------------------------------------

def _ask_purpose(parent, purposes: list) -> str:
    """Show a small dialog asking the user to pick or type a purpose. Returns '' if cancelled."""
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle('Reference Purpose')
    dlg.setMinimumWidth(300)
    layout = QtWidgets.QVBoxLayout(dlg)

    layout.addWidget(QtWidgets.QLabel('Purpose (optional):'))
    cbo = QtWidgets.QComboBox()
    cbo.setEditable(True)
    cbo.addItem('')
    for p in purposes:
        cbo.addItem(p)
    layout.addWidget(cbo)

    btn_box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    btn_box.accepted.connect(dlg.accept)
    btn_box.rejected.connect(dlg.reject)
    layout.addWidget(btn_box)

    if dlg.exec_() == QtWidgets.QDialog.Accepted:
        return cbo.currentText().strip()
    return ''


# ---------------------------------------------------------------------------
# Picker dialog: choose existing project attachments + assign purposes
# ---------------------------------------------------------------------------

class _AttachmentPickerDialog(QtWidgets.QDialog):
    """Pick one or more existing project attachments and assign a purpose to each."""

    def __init__(self, parent, attachments: dict, purposes: list):
        super().__init__(parent)
        self.setWindowTitle('Associate Existing Attachments')
        self.setMinimumWidth(560)
        self.setMinimumHeight(380)
        self._purposes = purposes

        layout = QtWidgets.QVBoxLayout(self)

        lbl = QtWidgets.QLabel(
            'Check the attachments to associate, then set a purpose for each:'
        )
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['', 'Name', 'Purpose'])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.table)

        for attachment in attachments.values():
            row = self.table.rowCount()
            self.table.insertRow(row)

            chk_item = QtWidgets.QTableWidgetItem()
            chk_item.setCheckState(QtCore.Qt.Unchecked)
            chk_item.setData(QtCore.Qt.UserRole, attachment.id)
            chk_item.setFlags(chk_item.flags() | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            self.table.setItem(row, 0, chk_item)

            icon_alias = 'link' if attachment.attachment_type == Attachment.TYPE_WEB_LINK else 'file'
            name_item = QtWidgets.QTableWidgetItem(attachment.name)
            name_item.setIcon(QtGui.QIcon(f':/plugins/qris_toolbar/{icon_alias}'))
            self.table.setItem(row, 1, name_item)

            cbo = QtWidgets.QComboBox()
            cbo.setEditable(True)
            cbo.addItem('')
            for p in purposes:
                cbo.addItem(p)
            self.table.setCellWidget(row, 2, cbo)

        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def selected_with_purpose(self) -> list:
        """Returns list of (attachment_id, purpose_str) for checked rows."""
        result = []
        for row in range(self.table.rowCount()):
            chk = self.table.item(row, 0)
            if chk and chk.checkState() == QtCore.Qt.Checked:
                aid = chk.data(QtCore.Qt.UserRole)
                cbo = self.table.cellWidget(row, 2)
                purpose = cbo.currentText().strip() if cbo else ''
                result.append((aid, purpose))
        return result
