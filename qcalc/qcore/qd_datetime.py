# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from datetime import date, datetime, time as dt_time, timedelta, timezone, tzinfo
from dateutil import parser
import re
import pytz
from timezonefinderL import TimezoneFinder
import qconst

# QC_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S UTC%z'  # Europe/London 2026-08-09 05:36:09 UTC+0100

# UTC%z is not a valid input for django datetime field
# Europe/London 2026-08-09 05:36:09 +0100
# Following is not strictly ISO 8601 format which is '%Y-%m-%dT%H:%M:%S%z' but closer and cleaner and compatible
QC_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S %z'
ISO_8601_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'  # not used


# Kept here (not in qd_data) because qd_data imports this module; moving it there needs a circular/lazy import.
def is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


class QTimezone:
    """Find timezone information for dates, times, and locations.

    Use ``from_offset()`` for values such as ``'UTC'``, ``'+06:00'`` or
    ``'UTC-05:30'``, and ``from_name()`` for names such as ``'Asia/Dhaka'``.
    These return a timezone when the text is recognized, otherwise ``None``.
    Use ``from_latlng(latitude, longitude)`` to look up a location's timezone
    name.
    """

    @staticmethod
    def from_offset(time_zone: str) -> None | timezone:
        """Return a fixed timezone from ``UTC`` or an offset such as ``+06:00``.

        The forms ``+HHMM``, ``-HHMM``, and ``UTC+HH:MM`` are also accepted.
        Blank or unrecognized text returns ``None``.
        """
        # both 'UTC+06:00' and '+06:00' are valid
        if not time_zone:
            return None
        value = time_zone.strip()
        if value == 'UTC':
            return timezone.utc

        match = qconst.TIMEZONE_PATTERN.match(value)
        if match:
            offset_text = match.group(1)
            sign = 1 if offset_text[0] == "+" else -1

            # Remove any existing colon to standardize the string to 4 digits
            digits = offset_text[1:].replace(":", "")
            hours = int(digits[:2])
            minutes = int(digits[2:])

            return timezone(sign * timedelta(hours=hours, minutes=minutes))

        return None

    @staticmethod
    def from_latlng(latitude: float, longitude: float):
        """Return the IANA timezone name for geographic coordinates, or ``None``."""
        # returns the IANA timezone name, e.g. 'Asia/Dhaka'
        return TimezoneFinder().timezone_at(lat=latitude, lng=longitude)

    @staticmethod
    def from_name(time_zone: str) -> None | tzinfo:
        """Return the timezone for an IANA name such as ``'Asia/Dhaka'`` or ``'UTC'``.

        Unrecognized names return ``None``.
        """
        # time_zone: python timezone string e.g. 'Asia/Dhaka', 'Europe/London'
        value = time_zone.strip()
        if value.upper() == "UTC":
            return timezone.utc

        try:
            return pytz.timezone(value)  # return tzinfo
        except Exception:
            return None


class QDateTime:
    """Read and work with a date, time, or combined date and time.

    Pass text such as ``'2026-11-18'``, ``'18:30'`` or
    ``'2026-11-18 18:30 UTC+06:00'``, or a Python date/time value. The parsed
    value is available as ``dt_value``; invalid input sets it to ``None``.
    ``str(value)`` gives a display-friendly result and ``spell()`` gives a
    longer description. This class is also available as ``qdt``.

    Existing timezone information is preserved. Values without timezone
    information stay without it, while values with ``UTC`` or an explicit
    offset keep that information. Adding or subtracting a number changes a
    date or datetime by that many days.
    """
    dt_value: date | datetime | dt_time | None

    @staticmethod
    def _has_sub_day_precision(delta: timedelta) -> bool:
        return delta.seconds != 0 or delta.microseconds != 0

    @staticmethod
    def _delta_from_operand(other: int | float | timedelta) -> timedelta:
        if isinstance(other, timedelta):
            return other
        if isinstance(other, bool):
            raise TypeError("Boolean values are not valid day offsets")
        if isinstance(other, (int, float)):
            return timedelta(days=other)
        raise TypeError(
            f"Unsupported operand type: {type(other).__name__}. "
            "Use a day number or timedelta."
        )

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
        self.dt_value = None

        try:
            if isinstance(sdatetime_iso_qc, str):
                value = sdatetime_iso_qc.strip()

                # Do not allow numeric strings to be interpreted as dates
                # by dateutil.parser.
                #
                # Examples:
                #   "1"        -> invalid
                #   "2024"     -> invalid
                #   "230721"   -> invalid
                #   "30.0"     -> invalid
                #   "12.65"    -> invalid
                if is_number(value):
                    return

                # Normalize custom UTC notation to an offset understood
                # by dateutil:
                #
                #   UTC       -> +0000
                #   UTC+06:00 -> +06:00
                #   UTC-05:30 -> -05:30
                cleaned = re.sub(r'\sUTC([+-]\d{2}:?\d{2})\b', r' \1', value)
                cleaned = re.sub(r'\sUTC\b', ' +0000', cleaned)
                parsed = parser.parse(cleaned)

                if self._looks_like_time_only(value):
                    self.dt_value = parsed.timetz() if parsed.tzinfo else parsed.time()
                elif self._has_explicit_date_only(sdatetime_iso_qc):
                    self.dt_value = parsed.date()
                else:
                    self.dt_value = parsed
            elif isinstance(sdatetime_iso_qc, (date, dt_time)):
                self.dt_value = sdatetime_iso_qc

        except (ValueError, OverflowError, TypeError):
            self.dt_value = None

    @staticmethod
    def to_str(dtime: datetime | date | dt_time | None) -> str:  # qc date/time format
        """Format a Python date, datetime, or time as qcalc display text.

        ``None`` returns ``'Invalid date'``. Aware datetimes include their offset.
        """
        if dtime is None:
            return "Invalid date"

        if not isinstance(dtime, datetime):
            return dtime.isoformat()

        if dtime.tzinfo is None or dtime.utcoffset() is None:
            return dtime.strftime('%Y-%m-%d %H:%M:%S')
        return dtime.strftime(QC_DATETIME_FORMAT)

    def __str__(self):
        return self.to_str(self.dt_value)

    def spell(self) -> str:
        """Return the value as a readable date and time sentence.

        Invalid or missing values return ``'Invalid date'``.
        """
        dt = self.date_time
        if dt is None:
            return "Invalid date"
        base = f"{dt.strftime('%A, %B')} {dt.day}, {dt.strftime('%Y, %I:%M %p')}"
        return f"{base} UTC{dt.strftime('%z')}" if dt.tzinfo and dt.utcoffset() is not None else f"{base} local time"

    def __add__(self, other: int | float | timedelta):
        if self.dt_value is None:
            raise TypeError("Cannot apply arithmetic on an invalid QDateTime value")
        if isinstance(self.dt_value, dt_time):
            raise TypeError("Arithmetic is not supported for time-only QDateTime values")
        delta = self._delta_from_operand(other)
        if self.is_date and self._has_sub_day_precision(delta):
            base_datetime = datetime.combine(self.dt_value, dt_time.min)
            return QDateTime(base_datetime + delta)
        return QDateTime(self.dt_value + delta)

    def __sub__(self, other):
        if self.dt_value is None:
            raise TypeError("Cannot apply arithmetic on an invalid QDateTime value")
        if isinstance(self.dt_value, dt_time):
            raise TypeError("Arithmetic is not supported for time-only QDateTime values")
        if isinstance(other, QDateTime):
            if other.dt_value is None:
                raise TypeError("Cannot subtract an invalid QDateTime value")
            if isinstance(other.dt_value, dt_time):
                raise TypeError("Arithmetic is not supported for time-only QDateTime values")
            delta = self.dt_value - other.dt_value
            return delta.total_seconds() / 86400.0
        delta = self._delta_from_operand(other)
        if self.is_date and self._has_sub_day_precision(delta):
            base_datetime = datetime.combine(self.dt_value, dt_time.min)
            return QDateTime(base_datetime - delta)
        return QDateTime(self.dt_value - delta)

    def _comparison_value(self):
        if self.dt_value is None:
            raise TypeError("Cannot compare invalid QDateTime values")
        if self.is_time:
            return "time", self.dt_value
        return "datetime", self.date_time

    def _compare_qdatetime(self, other, op):
        if not isinstance(other, QDateTime):
            return NotImplemented

        left_kind, left_value = self._comparison_value()
        right_kind, right_value = other._comparison_value()
        if left_kind != right_kind:
            raise TypeError("Cannot compare time-only values with date/datetime values")
        return op(left_value, right_value)

    def __eq__(self, other):
        return self._compare_qdatetime(other, lambda a, b: a == b)

    def __lt__(self, other):
        return self._compare_qdatetime(other, lambda a, b: a < b)

    def __le__(self, other):
        return self._compare_qdatetime(other, lambda a, b: a <= b)

    def __gt__(self, other):
        return self._compare_qdatetime(other, lambda a, b: a > b)

    def __ge__(self, other):
        return self._compare_qdatetime(other, lambda a, b: a >= b)

    def day_name(self, short: bool = False) -> str | None:
        """Return the weekday name for a date or datetime.

        Use ``short=True`` for an abbreviation such as ``'Mon'``. Time-only and
        invalid values return ``None``.
        """
        if isinstance(self.dt_value, (date, datetime)):
            return self.dt_value.strftime('%a' if short else '%A')
        return None

    @classmethod
    def qc_str_to_datetime(cls, sdatetime_iso_qc: str):  # risk
        """Parse text and return its date, datetime, or time value; invalid text returns ``None``."""
        return cls(sdatetime_iso_qc).val

    @classmethod
    def qc_str_to_date_and_time(cls, sdatetime_iso_qc: str):  # risk
        """Parse text and return a ``datetime`` where possible.

        Dates use midnight, and time-only values use today's date. Invalid text
        returns ``None``.
        """
        return cls(sdatetime_iso_qc).date_time

    @classmethod
    def is_str_date(cls, sdatetime_iso_qc: str) -> bool:  # risk
        """Return ``True`` when text represents a date without a time component."""
        return cls(sdatetime_iso_qc).is_date

    @staticmethod
    def timestamp_to_dt(timestamp: float) -> str:
        """Convert a timestamp to a datetime string in YYYY-MM-DD HH:MM:SS UTC+0000 format."""
        return QDateTime.to_str(datetime.fromtimestamp(timestamp, tz=timezone.utc))

    @staticmethod
    def timestamp_to_date(timestamp: float) -> str:
        """Convert a timestamp to a date string in YYYY-MM-DD."""
        return QDateTime.to_str(datetime.fromtimestamp(timestamp, tz=timezone.utc))[:10]

    @staticmethod
    def is_obsolete(past_timestamp: float, delta_secs: float = 86400.0):
        """Check if a past timestamp is obsolete based on the current time and a delta in seconds."""
        cur_datetime = datetime.now()
        past_datetime = datetime.fromtimestamp(past_timestamp)
        return past_datetime + timedelta(seconds=delta_secs) < cur_datetime

    @staticmethod
    def j2ts(jdy: float):
        """Convert a Julian day number to a Unix timestamp in seconds."""
        # julian date/day to timestamp
        return (jdy - 2440587.5) * 86400

    @staticmethod
    def julian_date(local_date: date):
        """ Julian day numbers are a system of counting days since a specific day (January 1, 4713, BC) """
        if isinstance(local_date, datetime):
            local_date = local_date.date()

        # Use an epoch-independent conversion so dates before 1970 work on every platform.
        return local_date.toordinal() + 1721424.5

    @staticmethod
    def ts2iso(time_stamp, tz: tzinfo):
        """Convert a Unix timestamp to qcalc datetime text in timezone ``tz``."""
        dt = datetime.fromtimestamp(time_stamp, tz)
        return QDateTime.to_str(dt)  # | time upto sec

    @classmethod
    def j2iso(cls, jdy: float, tz: tzinfo):
        """Convert a Julian day number to qcalc datetime text in timezone ``tz``."""
        return cls.ts2iso(cls.j2ts(jdy), tz)

    @property
    def val(self) -> None | date | datetime | dt_time:
        """The parsed Python date, datetime, or time, or ``None`` for invalid input."""
        return self.dt_value  # DateTime or None

    @property
    def date_time(self) -> datetime | None:
        """The value as a ``datetime`` where possible.

        Dates use midnight, time-only values use today's date, and invalid input
        returns ``None``.
        """
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
        """``True`` when this is a date without a time component."""
        # datetime is a subclass of date.
        return isinstance(self.dt_value, date) and not isinstance(self.dt_value, datetime)

    @property
    def is_datetime(self) -> bool:
        """``True`` when this value contains both a date and a time."""
        return isinstance(self.dt_value, datetime)

    @property
    def is_time(self) -> bool:
        """``True`` when this is a time without a date."""
        return isinstance(self.dt_value, dt_time)




def today() -> QDateTime:
    """Return current local date as ``QDateTime``."""
    return QDateTime(date.today())


def spellnow(tz: str | None = None) -> str:
    """Return the current date and time as a readable sentence.

    Leave ``tz`` blank for local time, or use ``'UTC'``, an offset such as
    ``'+06:00'`` or ``'UTC-05:30'``. The result includes the weekday, date,
    time, and timezone information when available.
    """
    return now(tz).spell()


def now(tz: str | None = None) -> QDateTime:
    """
    Return current time as QDateTime.

    tz behavior:
    - None or blank: local naive datetime (no tzinfo).
    - 'UTC': UTC-aware datetime.
    - '+HHMM' / '+HH:MM' (or negative forms): offset-aware datetime.
    - 'UTC+HHMM' / 'UTC+HH:MM': offset-aware datetime.
    """
    if tz is None:
        return QDateTime(datetime.now())
    if not isinstance(tz, str):
        raise TypeError("Timezone must be a string in UTC or offset format")

    value = tz.strip()
    if not value:
        return QDateTime(datetime.now())

    candidate = value
    if re.fullmatch(r"[+-]\d{2}:?\d{2}", value):
        candidate = f"UTC{value}"

    tz_value = QTimezone.from_offset(candidate)
    if tz_value is None:
        raise ValueError("Timezone must be 'UTC', '+HHMM', or '+HH:MM' format")
    return QDateTime(datetime.now(tz=tz_value))


if __name__ == '__main__':
    from tests.test_qdatetime import test_qdatetime

    test_qdatetime()
