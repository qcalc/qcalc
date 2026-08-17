# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from datetime import date, datetime, time as dt_time, timedelta, timezone, tzinfo
from dateutil import parser
import re
import pytz
from timezonefinderL import TimezoneFinder

QC_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S UTC%z'  # Europe/London 2026-08-09 05:36:09 UTC+0100


class QDateTime:
    dt_value: date | datetime | dt_time | None

    @staticmethod
    def _looks_like_time_only(value: str) -> bool:
        # Examples: 18:06, 18:06:30, 18:06:30.123456, 6:30 PM
        return bool(re.fullmatch(r"\s*\d{1,2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?\s*(?:[AaPp][Mm])?\s*", value))

    @staticmethod
    def _has_explicit_time(value: str) -> bool:
        # Time may be represented as HH:MM, HHMM with AM/PM, or ISO T separator.
        return bool(
            re.search(r"\d{1,2}:\d{2}", value)
            or re.search(r"\b\d{1,2}\s*(?:[AaPp][Mm])\b", value)
            or re.search(r"T\d{1,2}", value)
        )

    @classmethod
    def _has_explicit_date_only(cls, value: str) -> bool:
        # A date-only string has no explicit time and is not a time-only token.
        return (not cls._looks_like_time_only(value)) and (not cls._has_explicit_time(value))

    def __init__(self, sdatetime_iso_qc: str | date | datetime | dt_time):
        try:
            if isinstance(sdatetime_iso_qc, str):
                # Normalize custom " UTC..." tokens to ISO-style offsets for dateutil.
                cleaned = re.sub(r'\sUTC([+-]\d{2}:?\d{2})\b', r' \1', sdatetime_iso_qc)
                cleaned = re.sub(r'\sUTC\b', ' +0000', cleaned)
                parsed = parser.parse(cleaned)

                if self._looks_like_time_only(sdatetime_iso_qc):
                    self.dt_value = parsed.timetz() if parsed.tzinfo else parsed.time()
                elif self._has_explicit_date_only(sdatetime_iso_qc):
                    self.dt_value = parsed.date()
                else:
                    self.dt_value = parsed
            elif isinstance(sdatetime_iso_qc, date) and not isinstance(sdatetime_iso_qc, datetime):
                self.dt_value = sdatetime_iso_qc
            elif isinstance(sdatetime_iso_qc, datetime):
                self.dt_value = sdatetime_iso_qc
            elif isinstance(sdatetime_iso_qc, dt_time):
                self.dt_value = sdatetime_iso_qc
            else:
                self.dt_value = None
        except ValueError:
            self.dt_value = None

    def __str__(self):
        return qc_datetime_to_str(self.dt_value)

    @property
    def val(self) -> None | date | datetime | dt_time:
        return self.dt_value  # DateTime or None

    def date_time(self) -> datetime | None:
        if self.dt_value is None:
            return None
        if self.is_datetime:
            return self.dt_value
        if self.is_date:
            return datetime.combine(self.dt_value, dt_time.min)
        if self.is_time:
            return datetime.combine(date.today(), self.dt_value)
        return None

    @property
    def is_date(self) -> bool:
        # datetime is a subclass of date.
        return isinstance(self.dt_value, date) and not isinstance(self.dt_value, datetime)

    @property
    def is_datetime(self) -> bool:
        return isinstance(self.dt_value, datetime)

    @property
    def is_time(self) -> bool:
        return isinstance(self.dt_value, dt_time)


# -------------------------------------

def qc_datetime_to_str(dtime: datetime | date | dt_time | None):  # qc date/time format
    if dtime is None:
        return "Invalid date"

    if not isinstance(dtime, datetime):
        return dtime.isoformat()

    if dtime.tzinfo is None or dtime.utcoffset() is None:
        return dtime.strftime('%Y-%m-%d %H:%M:%S')
    return dtime.strftime(QC_DATETIME_FORMAT)


def qc_str_to_datetime(sdatetime_iso_qc: str):
    return QDateTime(sdatetime_iso_qc).val

def qc_str_to_date_and_time(sdatetime_iso_qc: str):
    return QDateTime(sdatetime_iso_qc).date_time()

def is_str_date(sdatetime_iso_qc: str) -> bool:
    return QDateTime(sdatetime_iso_qc).is_date


def is_obsolete(past_timestamp: float, delta_secs: float = 86400.0):
    cur_datetime = datetime.now()
    past_datetime = datetime.fromtimestamp(past_timestamp)
    return past_datetime + timedelta(seconds=delta_secs) < cur_datetime


def timestamp_to_dt(timestamp: float) -> str:
    return qc_datetime_to_str(datetime.fromtimestamp(timestamp, tz=timezone.utc))


def qc_timezone_ll(latitude: float, longitude: float):
    tf = TimezoneFinder()
    return tf.timezone_at(lat=latitude, lng=longitude)


def qc_timezone(time_zone: str) -> None | timezone:
    if not time_zone:
        return None
    value = time_zone.strip()
    if value == 'UTC':
        return timezone.utc

    # match = re.match(r"^(UTC[+-]\d{2}:?\d{2})\s*(.+)$", value)
    match = re.match(r"^(UTC[+-]\d{2}:?\d{2})(?:\s*(.+))?$", value) # 'UTC+6:00' is valid

    if match:
        # Slice from index 3 to skip "UTC" and get "+0530" or "+05:30"
        offset_text = match.group(1)[3:]
        sign = 1 if offset_text[0] == "+" else -1

        # Remove any existing colon to standardize the string to 4 digits
        digits = offset_text[1:].replace(":", "")
        hours = int(digits[:2])
        minutes = int(digits[2:])

        return timezone(sign * timedelta(hours=hours, minutes=minutes))

    return None


def qc_tzinfo(time_zone: str) -> None | tzinfo:
    # time_zone: python timezone string e.g. 'Asia/Dhaka', 'Europe/London'
    value = time_zone.strip()
    if value.upper() == "UTC":
        return timezone.utc

    try:
        return pytz.timezone(value)  # return tzinfo
    except Exception:
        pass


def julian_date(local_date: date):
    """ Julian day numbers are a system of counting days since a specific day (January 1, 4713, BC) """
    time_stamp = datetime.timestamp(datetime(local_date.year, local_date.month, local_date.day))
    jdate = time_stamp / 86400 + 2440587.5  # (based on 01.01.1970 unix time)
    # lprint(f'julian_date={jdate}')
    return jdate


def j2ts(jdy: float):
    # julian date/day to timestamp
    return (jdy - 2440587.5) * 86400


def ts2iso(time_stamp, tz: tzinfo):
    dt = datetime.fromtimestamp(time_stamp, tz)
    return qc_datetime_to_str(dt)  # | time upto sec


def j2iso(jdy: float, tz: tzinfo):
    time_stamp = j2ts(jdy)
    return ts2iso(time_stamp, tz)


if __name__ == '__main__':
    x = [QDateTime('1.07.1967').dt_value,
         QDateTime('07.21.2023').dt_value,
         QDateTime('21.07.2023').dt_value,
         QDateTime('2023.07.21').dt_value,
         QDateTime('21-jul-23').dt_value,
         QDateTime('xx.05.2023').dt_value,
         QDateTime('2023-07-21').dt_value,  # iso
         QDateTime('20230721').dt_value,  # iso
         QDateTime('230721').dt_value]
    for i in range(len(x)):
        print(i, x[i])
    print(qc_str_to_datetime('2023-01-01'), is_str_date('2023-01-01'))

    # Example usage:
    qdate = QDateTime("2024-09-23")
    assert qdate.is_date
    assert (not qdate.is_datetime)
    assert (not qdate.is_time)

    qdatetime = QDateTime("2024-09-23T10:30:00")
    assert (not qdatetime.is_date)
    assert qdatetime.is_datetime
    assert (not qdatetime.is_time)

    qtime = QDateTime("10:30:01")
    assert (not qtime.is_date)
    # assert (not qtime.is_datetime)
    assert qtime.is_time

    a = QDateTime('2024-09-23')
    b = QDateTime('18:06')
    c = QDateTime('18:06:30')
    d = QDateTime('2024-09-23 18:06:30+06:00')
    e = QDateTime('2024-09-23 18:06:30.123456+06:00')
    qc = QDateTime('2024-09-23 18:06:30 UTC+06:00')
    assert a.is_date
    assert b.is_time
    assert c.is_time
    assert d.is_datetime
    assert e.is_datetime
    assert qc.is_datetime
    print('a', str(a))
    print('b', str(b))
    print('c', str(c))
    print('d', str(d))
    print('e', str(e))
    print('qc', str(qc))
    a = QDateTime(a.val)
    b = QDateTime(b.val)
    c = QDateTime(c.val)
    d = QDateTime(d.val)
    e = QDateTime(e.val)
    qc = QDateTime(qc.val)
    assert a.is_date
    assert b.is_time
    assert c.is_time
    assert d.is_datetime
    assert e.is_datetime
    assert qc.is_datetime
    print('1', str(a))
    print('2', str(b))
    print('3', str(c))
    print('4', str(d))
    print('5', str(e))
    print('qc', str(qc))
