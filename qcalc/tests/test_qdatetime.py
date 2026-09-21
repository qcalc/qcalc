from qutil import QDateTime, is_str_date, is_number


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
