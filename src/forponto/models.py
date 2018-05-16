# -*- coding: utf-8 -*-
from datetime import datetime, date, time as _time, timedelta


class Mark:
    def __init__(self, date, marks, justification=None, is_holiday=False, holiday_name=None):
        self.date = date
        self.marks = marks
        self._justification = justification
        self.synced = True
        self.is_holiday = is_holiday
        self.holiday_name = holiday_name
        self.business, self.day_extras, self.night_extras,\
            self.credit, self.debt, self.working_hours,\
            self.breaks = self.read_journey()

    @classmethod
    def holiday(cls, date, holiday_name):
        return cls(date=date, marks=[], is_holiday=True, holiday_name=holiday_name)

    @property
    def justification(self):
        return self._justification

    @justification.setter
    def justification(self, value):
        self._justification = value
        self.synced = False

    @property
    def is_empty(self):
        return not self.marks

    @property
    def has_missing(self):
        return len(self.marks) % 2 != 0

    @property
    def has_day_extras(self):
        return self.day_extras.hour or self.day_extras.minute

    @property
    def has_night_extras(self):
        return self.night_extras.hour or self.night_extras.minute

    @property
    def has_debt(self):
        return self.debt.hour or self.debt.minute

    @property
    def has_credit(self):
        return self.credit.hour or self.credit.minute

    @property
    def expected_journey_end(self):
        projection = 29700 - ((self.working_hours.hour * 60 + self.working_hours.minute) * 60)
        last_mark = self.marks[-1]

        if projection <= 0:
            return None

        return (last_mark + timedelta(seconds=projection)).time()

    def _get_extras(self):
        if self.is_empty or self.has_missing:
            return (0, 0,)

        day_extras = 0
        night_extras = 0

        if self.marks[0].time() < _time(hour=7):
            day_extras += (datetime.combine(self.marks[0].date(), _time(hour=7)) - self.marks[0]).seconds

        if self.marks[-1].time() > _time(hour=19):
            day_extras += (self.marks[-1] - datetime.combine(self.marks[0].date(), _time(hour=19))).seconds

        if self.marks[-1].time() > _time(hour=22):
            night_extras += (self.marks[-1] - datetime.combine(self.marks[0].date(), _time(hour=22))).seconds
            day_extras -= night_extras

        return (day_extras, night_extras, )

    def seconds_to_time(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes = remainder // 60
        return _time(hour=hours, minute=minutes)

    def read_journey(self):
        fulltime = 0
        breaks = 0
        hour_breaks = dict()

        # here we grab intervals between marks,
        # so we start from the second mark of the day.
        for i, m in enumerate(self.marks, 1):
            if i >= 2:
                interval = (m - self.marks[i-2]).seconds

                # even marks are exits, so the interval is considered as working hours.
                if not i % 2:
                    fulltime += interval
                # odd marks are breaks, and if smaller than 10 minutes have
                # to be grouped by hour.
                elif interval <= 600:
                    hour_breaks[m.hour] = hour_breaks.get(m.hour, 0) + interval
                # otherwise it is a normal break in the journey.
                else:
                    breaks += interval

        # here we check if the sum of all breaks per hour exceeds 10 minutes.
        for _break in hour_breaks.values():
            if _break <= 600:
                fulltime += _break
            else:
                breaks += _break

        # if there are only two marks and journey is bigger than 6 hours,
        # we have to remove 60 minutes for lunch.
        # if len(self.marks) == 2 and fulltime >= 21600:
        if breaks < 3600 and fulltime >= 21600:
            fulltime -= 3600
            breaks = 3600

        day_extras, night_extras = self._get_extras()
        business = fulltime - day_extras - night_extras
        debt = 0
        credt = 0

        # 08:10h in seconds
        if business > 29400:
            if business >= 29700:  # 08:15h in seconds
                credt = business - 29700
            business = 29700
        else:
            debt = 29700 - business

        return (self.seconds_to_time(v) for v in (
            business,
            day_extras,
            night_extras,
            credt,
            debt,
            business + day_extras + night_extras + credt,
            breaks,
        ))


