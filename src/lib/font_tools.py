from qgis.PyQt.QtGui import QFont
from qgis.PyQt import QtWidgets

try:
    from matplotlib import font_manager as mpl_font_manager
except Exception:  # nosec B110 - matplotlib may not be available in limited environments
    mpl_font_manager = None


_MPL_FAMILIES_CACHE = None


def get_matplotlib_font_families(current_family: str = None):
    """Return sorted unique font families discovered by matplotlib."""
    global _MPL_FAMILIES_CACHE
    if _MPL_FAMILIES_CACHE is None:
        families = set()

        if mpl_font_manager is not None:
            for fpath in mpl_font_manager.findSystemFonts(fontext='ttf'):
                try:
                    prop = mpl_font_manager.FontProperties(fname=fpath)
                    name = prop.get_name()
                except Exception:  # nosec B110 - skip unreadable/invalid font files
                    continue
                if name:
                    families.add(name)

        if not families:
            families.update(['Sans Serif', 'DejaVu Sans'])

        _MPL_FAMILIES_CACHE = sorted(families, key=str.casefold)

    families = list(_MPL_FAMILIES_CACHE)
    if current_family and current_family not in families:
        families.append(current_family)
        families = sorted(set(families), key=str.casefold)
    return families


def sanitize_chart_font(qfont: QFont) -> QFont:
    """Return a copy with unsupported chart effects disabled."""
    if qfont is None:
        return qfont

    clean_font = QFont(qfont)
    clean_font.setUnderline(False)
    clean_font.setStrikeOut(False)
    return clean_font


class _ChartFontDialog(QtWidgets.QDialog):
    def __init__(self, parent, current_font: QFont, title: str):
        super().__init__(parent)
        self.setWindowTitle(title)

        self._current_font = sanitize_chart_font(current_font)

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        layout.addLayout(form)

        self.cmb_family = QtWidgets.QComboBox()
        self.cmb_family.setEditable(False)
        families = get_matplotlib_font_families(self._current_font.family())
        self.cmb_family.addItems(families)

        family_index = self.cmb_family.findText(self._current_font.family())
        if family_index < 0:
            family_index = self.cmb_family.findText('DejaVu Sans')
        if family_index < 0:
            family_index = self.cmb_family.findText('Sans Serif')
        if family_index < 0:
            family_index = 0
        if family_index >= 0:
            self.cmb_family.setCurrentIndex(family_index)

        form.addRow('Font Family:', self.cmb_family)

        self.spn_size = QtWidgets.QSpinBox()
        self.spn_size.setRange(6, 96)
        self.spn_size.setValue(max(6, self._current_font.pointSize() or 10))
        form.addRow('Size:', self.spn_size)

        style_row = QtWidgets.QHBoxLayout()
        self.chk_bold = QtWidgets.QCheckBox('Bold')
        self.chk_bold.setChecked(self._current_font.bold())
        style_row.addWidget(self.chk_bold)

        self.chk_italic = QtWidgets.QCheckBox('Italic')
        self.chk_italic.setChecked(self._current_font.italic())
        style_row.addWidget(self.chk_italic)
        style_row.addStretch()
        form.addRow('Style:', style_row)

        self.lbl_preview = QtWidgets.QLabel('The quick brown fox jumps over the lazy dog 123')
        self.lbl_preview.setWordWrap(True)
        layout.addWidget(self.lbl_preview)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.cmb_family.currentTextChanged.connect(self._update_preview)
        self.spn_size.valueChanged.connect(self._update_preview)
        self.chk_bold.toggled.connect(self._update_preview)
        self.chk_italic.toggled.connect(self._update_preview)
        self._update_preview()

    def selected_font(self):
        font = QFont(self.cmb_family.currentText(), self.spn_size.value())
        font.setBold(self.chk_bold.isChecked())
        font.setItalic(self.chk_italic.isChecked())
        return sanitize_chart_font(font)

    def _update_preview(self):
        self.lbl_preview.setFont(self.selected_font())


def select_chart_font(parent, current_font: QFont, title: str = 'Select Chart Font'):
    """Open a custom chart font dialog constrained to matplotlib-supported settings."""
    dialog = _ChartFontDialog(parent, current_font, title)
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        return dialog.selected_font(), True

    return sanitize_chart_font(current_font), False


def apply_qfont_to_mpl_text(text_obj, qfont: QFont):
    """Apply QFont properties to a matplotlib text object."""
    if text_obj is None or qfont is None:
        return

    text_obj.set_fontfamily(qfont.family())
    text_obj.set_fontsize(qfont.pointSize())
    text_obj.set_fontweight('bold' if qfont.bold() else 'normal')
    text_obj.set_fontstyle('italic' if qfont.italic() else 'normal')

    if hasattr(text_obj, 'set_underline'):
        text_obj.set_underline(qfont.underline())

    if hasattr(text_obj, 'set_strikethrough'):
        text_obj.set_strikethrough(qfont.strikeOut())


def apply_qfont_to_mpl_texts(text_objects, qfont: QFont):
    """Apply QFont properties across an iterable of matplotlib text objects."""
    for text_obj in text_objects:
        apply_qfont_to_mpl_text(text_obj, qfont)
