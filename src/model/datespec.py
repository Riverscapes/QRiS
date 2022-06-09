

class DateSpec:

    def __init__(self, year: int, month: int, day: int):
        self.set_year(year)
        self.set_month(month)
        self.set_day(day)

    def set_year(self, year: int):
        if year and year < 0:
            raise Exception(f'Invalid year {year}. Must be greater than zero.')
        self.year = year

    def set_month(self, month: int):
        if month and (month < 1 or month > 12):
            raise Exception(f'Invalid month {month}. Must be between 1 and 12.')
        self.month = month

    def set_day(self, day: int):
        if day and (day < 1 or day > 31):
            raise Exception(f'Invalid day of month {day}. Must be between 1 and 31.')
        self.day = day
