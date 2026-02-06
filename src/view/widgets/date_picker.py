from calendar import month
from datetime import datetime

from PyQt5 import QtCore, QtGui, QtWidgets

from ...model.datespec import DateSpec

NONE_TEXT = 'None'


class FrmDatePicker(QtWidgets.QWidget):

    def __init__(self, parent, date_spec: DateSpec = None):
        super().__init__(parent)
        self.setupUi()

        [self.cboYear.addItem(str(year), year) for year in range(1970, 2050)]
        [self.cboMonth.addItem(datetime(2000, month, 1).strftime('%b'), month) for month in range(1, 13)]
        [self.cboDay.addItem((str(day)), day) for day in range(1, 32)]

        # Add the unspecified text with a value of zero
        [widget.addItem(NONE_TEXT, 0) for widget in [self.cboYear, self.cboMonth, self.cboDay]]

        if date_spec is None:
            for widget in [self.cboYear, self.cboMonth, self.cboDay]:
                index = widget.findData(0)
                widget.setCurrentIndex(index)
        else:
            self.set_date_spec(date_spec)

    def get_date_spec(self):

        year = self.cboYear.currentData()
        month = self.cboMonth.currentData()
        day = self.cboDay.currentData()

        return DateSpec(
            year if year != 0 else None,
            month if month != 0 else None,
            day if day != 0 else None)

    def set_date_spec(self, date_spec: DateSpec):

        if date_spec.year is not None:
            index = self.cboYear.findData(date_spec.year)
            self.cboYear.setCurrentIndex(index)

        if date_spec.month is not None:
            index = self.cboMonth.findData(date_spec.month)
            self.cboMonth.setCurrentIndex(index)

        if date_spec.day is not None:
            index = self.cboDay.findData(date_spec.day)
            self.cboDay.setCurrentIndex(index)

    def validate(self) -> bool:
        event_date = self.get_date_spec()
        is_valid_date = True
        error_message = ""
        if event_date.year is None and event_date.month is not None:
            is_valid_date = False
            error_message = "A year is required if a month is present."
        elif event_date.year is None and event_date.month is None and event_date.day is not None:
            is_valid_date = False
            error_message = "A year and month are required if a day is present."
        elif event_date.year is not None and event_date.month is None and event_date.day is not None:
            is_valid_date = False
            error_message = "A month is required if a day is present."
        # Dates must be real dates (February 30th is not allowed)
        elif event_date.year is not None and event_date.month is not None and event_date.day is not None:
            try:
                datetime(event_date.year, event_date.month, event_date.day)
            except ValueError:
                is_valid_date = False
                error_message = "Not a valid calendar date."

        return is_valid_date, error_message

    def set_to_today(self):
        today = datetime.now()
        self.set_date_spec(DateSpec(today.year, today.month, today.day))

    def setupUi(self):

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.horiz = QtWidgets.QHBoxLayout(self)
        self.horiz.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.horiz)

        self.lblYear = QtWidgets.QLabel()
        self.lblYear.setText('Year')
        self.horiz.addWidget(self.lblYear)

        self.cboYear = QtWidgets.QComboBox()
        self.horiz.addWidget(self.cboYear)

        self.lblMonth = QtWidgets.QLabel()
        self.lblMonth.setText('Month')
        self.horiz.addWidget(self.lblMonth)

        self.cboMonth = QtWidgets.QComboBox()
        self.horiz.addWidget(self.cboMonth)

        self.lblDay = QtWidgets.QLabel()
        self.lblDay.setText('Day')
        self.horiz.addWidget(self.lblDay)

        self.cboDay = QtWidgets.QComboBox()
        self.horiz.addWidget(self.cboDay)
        
        self.btnToday = QtWidgets.QPushButton("Today")
        self.btnToday.setToolTip("Set to today's date")
        self.btnToday.clicked.connect(self.set_to_today)
        self.horiz.addWidget(self.btnToday)
        
        self.horiz.addStretch()
