# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

# WeCase -- This model implemented a dateutil-compatible parser
#           for Sina's time format.
# Copyright (C) 2013, 2014 The WeCase Developers.
# License: GPL v3 or later.


from datetime import datetime, timedelta, tzinfo


class tzoffset(tzinfo):
    """Genenal Timezone without DST"""
    ZERO = timedelta(0)

    def __init__(self, tzname, utcoffset):
        super(tzoffset, self).__init__()

        self.utcoffset_value = timedelta(hours=utcoffset / 3600)
        self.tzname_value = tzname

    def utcoffset(self, dt):
        return self.utcoffset_value

    def tzname(self, dt):
        return self.tzname

    def dst(self, dt):
        return self.ZERO


class WTimeParser():
    MONTHS = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
              "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
              "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

    def parse(self, time_string):
        """
        Sina's time-string parser.

        >>> t.parse("Sat Apr 06 00:49:30 +0800 2013")
        datetime(2013, 4, 6, 0, 49, 30, tzinfo=tzoffset(None, 28800))
        """

        date_list = time_string.split(' ')
        year = int(date_list[5])
        month = self.MONTHS[date_list[1]]
        day = int(date_list[2])

        time = date_list[3].split(':')
        hour = int(time[0])
        minute = int(time[1])
        second = int(time[2])

        timezone_str = date_list[4]
        timezone_offset = int(timezone_str[0:3]) * 3600

        return datetime(year, month, day, hour, minute, second,
                        tzinfo=tzoffset(None, timezone_offset))
