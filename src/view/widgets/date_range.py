from datetime import date

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QDate

class DateRangeWidget(QtWidgets.QWidget):
    
    date_range_changed = pyqtSignal()
    
    def __init__(self, parent=None, date_min: date = None, date_max: date = None, horizontal: bool = True):
        super(DateRangeWidget, self).__init__(parent)

        self.horizontal = horizontal

        self.today = QDate(date.today())
        self.last_year = self.today.addYears(-1)

        self.date_min = self.last_year if date_min is None else QDate(date_min)
        self.date_max = self.today if date_max is None else QDate(date_max)

        self.date_start = QtWidgets.QDateEdit(self)
        self.date_end = QtWidgets.QDateEdit(self)

        self.setupUi()

        self.set_date_range_bounds(self.date_min.toPyDate(), self.date_max.toPyDate())

    def set_date_range_bounds(self, date_min: date, date_max: date, set_as_initial: bool = True):
        self.date_min = QDate(date_min)
        self.date_max = QDate(date_max)
        if set_as_initial:
            self.set_dates(date_min, date_max)
        else:
            self.update_range()
    
    def set_dates(self, date_start: date, date_end: date):
        self.date_start.setDate(QDate(date_start))
        self.date_end.setDate(QDate(date_end))
        self.update_range()

    def set_dates_to_bounds(self):
        self.date_start.setDate(self.date_min)
        self.date_end.setDate(self.date_max)

    def update_range(self):

        self.date_start.setMinimumDate(self.date_min)
        self.date_end.setMaximumDate(self.date_max)

        if self.date_start.date() < self.date_min:
            self.date_start.setDate(self.date_min)

        if self.date_end.date() > self.date_max:
            self.date_end.setDate(self.date_max)

        self.date_start.setMaximumDate(self.date_end.date())
        self.date_end.setMinimumDate(self.date_start.date())

    def get_date_range(self):
        return self.date_start.date().toPyDate(), self.date_end.date().toPyDate()

    def setEnabled(self, enabled: bool):
        self.date_start.setEnabled(enabled)
        self.date_end.setEnabled(enabled)
        super().setEnabled(enabled)

    def setupUi(self):

        if self.horizontal:
            self.widget_layout = QtWidgets.QHBoxLayout(self)
            self.horiz_start = QtWidgets.QHBoxLayout()
            self.widget_layout.addLayout(self.horiz_start)
            self.horiz_end = QtWidgets.QHBoxLayout()
            self.widget_layout.addLayout(self.horiz_end)
        else:
            self.widget_layout = QtWidgets.QGridLayout(self)

        self.lbl_from = QtWidgets.QLabel('From')
        if self.horizontal:
            self.horiz_start.addWidget(self.lbl_from)
        else:
            self.widget_layout.addWidget(self.lbl_from, 0, 0)

        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(self.last_year)
        self.date_start.dateChanged.connect(self.date_range_changed.emit)
        if self.horizontal:
            self.horiz_start.addWidget(self.date_start)
            self.horiz_start.addStretch()
        else:
            self.widget_layout.addWidget(self.date_start, 0, 1)
            self.widget_layout.setRowStretch(2, 1)

        self.lbl_to = QtWidgets.QLabel('To')
        if self.horizontal:
            self.horiz_end.addWidget(self.lbl_to)
        else:
            self.widget_layout.addWidget(self.lbl_to, 1, 0)

        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(self.today)
        self.date_end.dateChanged.connect(self.date_range_changed.emit)
        if self.horizontal:
            self.horiz_end.addWidget(self.date_end)
            self.horiz_end.addStretch()
        else:
            self.widget_layout.addWidget(self.date_end, 1, 1)
            self.widget_layout.setRowStretch(2, 1)
