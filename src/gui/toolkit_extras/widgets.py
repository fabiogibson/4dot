from datetime import datetime, date, timedelta, time as _time

from prompt_toolkit.widgets import Checkbox
from babel.dates import format_date, format_time, format_timedelta, format_datetime


class DateCheck(Checkbox):
    formatters = {
        date: lambda m: format_date(m, format='EEE, dd/MM/yy', locale='pt_BR'),
        _time: lambda m: format_time(m, format='short', locale='pt_BR'),
        datetime: lambda m: format_datetime(m, format='HH:mm', locale='pt_BR'),
        timedelta: lambda m: format_timedelta(m, locale='pt_BR'),
    }

    def format(self, value, width=0, empty=''):
        fmt = self.formatters.get(type(value))
        val = fmt(value) if value and fmt else empty
        return val.ljust(width)

    def __init__(self, mark):
        self.mark = mark
        line = (
            f'{self.format(mark.date, 20)}'
            f'Diurnas: {self.format(mark.day_extras, 14)}'
            f'Noturnas: {self.format(mark.night_extras, 14)}'
            f'Banco: {self.format(mark.credit, 14)}'
            f'{mark.justification or ""}'
        )
        super().__init__(text=line)
        self.checked = False

