from datetime import datetime
from psycopg2 import Date
from qgis.PyQt.QtWidgets import QWidget, QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox

from .ui.date_picker import Ui_DatePicker
from ..model.datespec import DateSpec
from ..model.db_item import DBItem, DBItemModel

NONE_TEXT = 'None'


class FrmDatePicker(QWidget, Ui_DatePicker):

    def __init__(self, date_spec: DateSpec = None):
        super().__init__()
        self.setupUi(self)

        [self.cboYear.addItem(str(year), year) for year in range(1970, 2050)]
        [self.cboMonth.addItem(datetime(2000, month, 1).strftime('%b'), month) for month in range(1, 13)]
        [self.cboDay.addItem((str(day)), day) for day in range(1, 31)]

        # Add the unspecified text with a value of zero
        [widget.addItem(NONE_TEXT, 0) for widget in [self.cboYear, self.cboMonth, self.cboDay]]

        if date_spec is None:
            for widget in [self.cboYear, self.cboMonth, self.cboDay]:
                index = widget.findData(0)
                widget.setCurrentIndex(index)
        else:
            if date_spec.year is not None:
                index = self.cboYear.findData(date_spec.year)
                self.cboYear.setCurrentIndex(index)

            if date_spec.month is not None:
                index = self.cboMonth.findData(date_spec.month)
                self.cboMonth.setCurrentIndex(index)

            if date_spec.day is not None:
                index = self.cboDay.findDate(date_spec.day)
                self.cboDay.setCurrentIndex(index)

    def get_date_spec(self):

        year = self.cboYear.currentData()
        month = self.cboYear.currentData()
        day = self.cboDay.currentData()

        return DateSpec(
            year if year != 0 else None,
            month if month != 0 else None,
            day if day != 0 else None)
