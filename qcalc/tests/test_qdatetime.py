from datetime import date, timedelta

import pytest

from qutil import QDateTime, is_str_date, is_number, julian_date, now, today


def test_qdatetime():
    assert is_number("1")
    assert is_number("33.0")
    assert is_number("-12.5")
    assert is_number("1e5")
    assert is_number("20230721")

    assert not is_number("2024-09-23")
    assert not is_number("18:30")
    assert not is_number("hello")
    assert QDateTime('1.07.1967').is_date
    assert QDateTime('07.21.2023').is_date
    assert not QDateTime('21.07.2023').is_datetime
    assert QDateTime('2023.07.21').is_date
    assert QDateTime('21-jul-23').is_date
    assert not QDateTime('xx.05.2023').is_date
    assert QDateTime('2023-07-21').is_date  # iso
    assert is_str_date('2023-01-01')

    assert not QDateTime('20230721').is_date
    assert not QDateTime('20230721').is_time

    assert not QDateTime('230721').is_date
    assert not QDateTime('230721').is_time

    assert not QDateTime('1').is_date
    assert not QDateTime('1').is_time

    assert QDateTime('2024-09-23').is_date
    assert QDateTime('2024-09-23T10:30:00').is_datetime
    assert QDateTime('10:30:01').is_time

    assert QDateTime('2024-09-23 18:06:30+06:00').is_datetime
    assert QDateTime('2024-09-23 18:06:30 UTC+06:00').is_datetime
    assert QDateTime('2024-09-23 18:06:30 UTC').is_datetime

    # assert qc_str_to_datetime('2023-01-01').dt_value.is_date
    assert is_str_date('2023-01-01')

    qnum = QDateTime('20230721')
    assert not qnum.is_date
    assert not qnum.is_time

    qnum  = QDateTime('230721')
    assert not qnum.is_date
    assert not qnum.is_time

    qnum  = QDateTime('1')
    assert not qnum.is_date
    assert not qnum.is_time
    assert QDateTime('20.0').val is None
    assert QDateTime('0.05').val is None
    assert QDateTime(20.0).val is None
    assert QDateTime(20).val is None
    assert QDateTime("").val is None
    assert QDateTime(None).val is None

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
    assert a.is_date
    assert str(a) == '2024-09-23'

    assert julian_date(date(1967, 7, 1)) == 2439672.5

    b = QDateTime('18:06')
    assert b.is_time
    assert str(b) == '18:06:00'

    c = QDateTime('18:06:30')
    assert c.is_time
    assert str(c) == '18:06:30'

    d = QDateTime('2024-09-23 18:06:30+06:00')
    assert d.is_datetime
    assert str(d) == '2024-09-23 18:06:30 +0600'

    e = QDateTime('2024-09-23 18:06:30.123456+06:00')
    assert e.is_datetime
    assert str(e) == '2024-09-23 18:06:30 +0600'

    qc0 = QDateTime('2024-09-23 18:06:30 UTC+06:00')
    assert qc0.is_datetime
    assert str(qc0) == '2024-09-23 18:06:30 +0600'

    qc1a = QDateTime('2024-09-23 18:06:30 +06:00')
    assert qc1a.is_datetime
    assert str(qc1a) == '2024-09-23 18:06:30 +0600'

    qc1b = QDateTime('2024-09-23 18:06:30+06:00')
    assert qc1b.is_datetime
    assert str(qc1b) == '2024-09-23 18:06:30 +0600'

    qc2a = QDateTime('2024-09-23 18:06:30 +0600')
    assert qc2a.is_datetime
    assert str(qc2a) == '2024-09-23 18:06:30 +0600'

    qc2b = QDateTime('2024-09-23 18:06:30+0600')
    assert qc2b.is_datetime
    assert str(qc2b) == '2024-09-23 18:06:30 +0600'

    qc3a = QDateTime('2024-09-23T18:06:30+0600')
    assert qc3a.is_datetime
    assert str(qc3a) == '2024-09-23 18:06:30 +0600'

    qc3b = QDateTime('2024-09-23T18:06:30+06:00')
    assert qc3b.is_datetime
    assert str(qc3b) == '2024-09-23 18:06:30 +0600'

    a = QDateTime(a.val)
    b = QDateTime(b.val)
    c = QDateTime(c.val)
    d = QDateTime(d.val)
    e = QDateTime(e.val)
    qc = QDateTime(qc0.val)
    assert a.is_date
    assert b.is_time
    assert c.is_time
    assert d.is_datetime
    assert e.is_datetime
    assert qc.is_datetime

    base_date = QDateTime('2024-09-23')
    assert (base_date + 2).val == date(2024, 9, 25)
    assert (base_date - 3).val == date(2024, 9, 20)
    date_plus_half = base_date + 1.5
    assert date_plus_half.is_datetime
    assert str(date_plus_half) == '2024-09-24 12:00:00'
    assert (base_date - timedelta(days=4)).val == date(2024, 9, 19)
    date_minus_half = base_date - 0.5
    assert date_minus_half.is_datetime
    assert str(date_minus_half) == '2024-09-22 12:00:00'

    base_datetime = QDateTime('2024-09-23T10:30:00')
    dt_plus = base_datetime + 0.5
    dt_minus = base_datetime - timedelta(hours=12)
    assert dt_plus.is_datetime
    assert dt_minus.is_datetime
    assert str(dt_plus) == '2024-09-23 22:30:00'
    assert str(dt_minus) == '2024-09-22 22:30:00'


def test_qdatetime_arithmetic_with_negative_float_days():
    base_datetime = QDateTime('2024-09-23T10:30:00')
    shifted = base_datetime + (-0.25)
    assert shifted.is_datetime
    assert str(shifted) == '2024-09-23 04:30:00'


def test_qdatetime_arithmetic_rejects_invalid_operands():
    with pytest.raises(TypeError):
        _ = QDateTime('2024-09-23') + "1"

    with pytest.raises(TypeError):
        _ = QDateTime('10:30:01') + 1

    with pytest.raises(TypeError):
        _ = QDateTime('2024-09-23') - QDateTime(None)

    with pytest.raises(TypeError):
        _ = QDateTime('10:30:01') - QDateTime('2024-09-23')


def test_qdatetime_today_returns_qdatetime_date():
    today_qdt = today()
    assert isinstance(today_qdt, QDateTime)
    assert today_qdt.is_date
    assert today_qdt.val == date.today()


def test_qdatetime_now_returns_qdatetime_datetime():
    now_qdt = now()
    assert isinstance(now_qdt, QDateTime)
    assert now_qdt.is_datetime


def test_qdatetime_now_accepts_utc_and_offset_strings():
    utc_now = now("UTC")
    off_no_colon = now("+0600")
    off_with_colon = now("+06:00")
    utc_with_prefix = now("UTC+06:00")

    assert utc_now.is_datetime
    assert off_no_colon.is_datetime
    assert off_with_colon.is_datetime
    assert utc_with_prefix.is_datetime
    assert utc_now.val.utcoffset() == timedelta(0)
    assert off_no_colon.val.utcoffset() == timedelta(hours=6)
    assert off_with_colon.val.utcoffset() == timedelta(hours=6)
    assert utc_with_prefix.val.utcoffset() == timedelta(hours=6)


def test_qdatetime_now_rejects_invalid_timezone_strings():
    with pytest.raises(ValueError):
        now("Asia/Dhaka")

    with pytest.raises(ValueError):
        now("+25:00")


def test_qdatetime_subtract_qdatetime_returns_float_days():
    d1 = QDateTime('2024-09-23')
    d2 = QDateTime('2024-09-20')
    assert (d1 - d2) == 3.0

    dt1 = QDateTime('2024-09-23T10:30:00')
    dt2 = QDateTime('2024-09-22T22:30:00')
    assert (dt1 - dt2) == 0.5
