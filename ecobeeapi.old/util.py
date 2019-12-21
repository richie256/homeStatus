from datetime import datetime
import pytz
import calendar

@staticmethod
def toFarenheit(celsius):
    return (9.0/5.0) * celsius + 32

@staticmethod
def toCelsius(farenheit):
    return (farenheit - 32) * (5.0 / 9.0)

@staticmethod
def ts_utc_from_datestr(utc_date_str):
    utc = datetime.strptime(utc_date_str, '%Y-%m-%d %H:%M:%S')

    pst = pytz.timezone('Etc/UTC')
    utc = pst.localize(utc)

    # return calendar.timegm(dt.utctimetuple())
    return utc.timestamp()
