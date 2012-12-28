from datetime import datetime, date, timedelta

class date:
    def __init__(self):
        self._today = date.today()
        self._yesterday = self._today - timedelta(1)

    def yesterday(self, fmt='%Y%m%d'):
        return self._yesterday.strftime(fmt)

    def today(self, fmt='%Y%m%d', delta=0):
        return (self._today + timedelta(delta)).strftime(fmt)

