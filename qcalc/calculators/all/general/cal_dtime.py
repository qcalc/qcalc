from datetime import datetime, timezone
from qutil import qc_datetime_to_str, qc_str_to_date_and_time, qc_timezone
from calc import StdList


def cdtime__info():
    return {
        'title': 'Convert Date Time Around the World',
        'schema': {
            'date_time': {'type': str, 'initial': qc_datetime_to_str(datetime.now(timezone.utc))},
            'time_zone': {'type': 'qsel2', 'choices': StdList.timezone_list},
        }
    }


def cdtime(date_time: str, time_zone):
    default_datetime = (date_time is None or date_time == '')
    tz = qc_timezone(time_zone)
    dtz_remark = "Time Zone OK" if tz is not None else "Unknown Time Zone"
    tz = tz or timezone.utc

    if default_datetime:
        translated_date_time_tz = datetime.now(tz)
    else:
        translated_date_time_tz = qc_str_to_date_and_time(date_time)
        if translated_date_time_tz is not None:
            # FIX: If the parsed time has no timezone, assume it's UTC (or your preferred source tz)
            if translated_date_time_tz.tzinfo is None:
                # 1. Tag it with the source timezone (e.g., UTC) without changing the clock digits
                translated_date_time_tz = translated_date_time_tz.replace(tzinfo=timezone.utc)

            # 2. Safely translate the aware datetime to your target timezone
            translated_date_time_tz = translated_date_time_tz.astimezone(tz)

    if translated_date_time_tz is None:
        dtz_remark += "; Invalid ISO Date Time format, Using Current Time instead"
        translated_date_time_tz = datetime.now(tz)
    else:
        dtz_remark += "; Date Time OK"

    result = qc_datetime_to_str(translated_date_time_tz)
    return {"Current Time": result, "Remark": dtz_remark}
