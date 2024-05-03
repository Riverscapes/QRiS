from datetime import date

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QDate

class DateRangeWidget(QtWidgets.QWidget):
    
    date_range_changed = pyqtSignal()
    
    def __init__(self, parent=None, date_min: date = None, date_max: date = None):
        super(DateRangeWidget, self).__init__(parent)

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
            self.set_initial_date_range(date_min, date_max)
        else:
            self.update_range()
    
    def set_initial_date_range(self, date_start: date, date_end: date):
        self.date_start.setDate(QDate(date_start))
        self.date_end.setDate(QDate(date_end))
        self.update_range()

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

    def setupUi(self):

        self.horiz = QtWidgets.QHBoxLayout(self)

        self.lbl_date_range = QtWidgets.QLabel('Date Range')
        font = self.lbl_date_range.font()
        font.setBold(True)
        self.lbl_date_range.setFont(font)
        self.horiz.addWidget(self.lbl_date_range)

        self.lbl_from = QtWidgets.QLabel('From')
        self.horiz.addWidget(self.lbl_from)

        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(self.last_year)
        self.date_start.dateChanged.connect(self.date_range_changed.emit)
        self.horiz.addWidget(self.date_start)

        self.lbl_to = QtWidgets.QLabel('To')
        self.horiz.addWidget(self.lbl_to)

        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(self.today)
        self.date_end.dateChanged.connect(self.date_range_changed.emit)
        self.horiz.addWidget(self.date_end)