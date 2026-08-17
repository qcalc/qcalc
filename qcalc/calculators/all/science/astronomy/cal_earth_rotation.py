# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from datetime import datetime, date
from calculators.all.general.map.cal_location import geo_location
from qcore import Qty, qfunc, QGeo
from math import fmod, radians, degrees, sqrt, ceil, acos
from .cal_coord import *
from qutil import nzv, qc_tzinfo, julian_date, j2iso


class EarthRotation:
    # Reference: https://en.wikipedia.org/wiki/Sunrise_equation
    latitude_deg: float  # north positive, south negative
    longitude_deg: float
    elevation_ft: float
    local_date: date
    time_zone: str

    def __init__(self, latitude='24.0 deg', longitude='90.0 deg', elevation='0.0 ft',
                 on_date=date.today(), time_zone='UTC'):
        self.latitude_deg = Qty(latitude, 'deg').val
        self.longitude_deg = Qty(longitude, 'deg').val
        self.elevation_ft = Qty(elevation, 'ft').val
        self.local_date = on_date
        self.tz_info = qc_tzinfo(time_zone)
        self.jul_date = julian_date(self.local_date)
        self.m_solar_time = self.mean_solar_time()
        self.solar_m_anomaly = self.solar_mean_anomaly()

    def mean_solar_time(self):
        n = ceil(self.jul_date - 2451545.0 + 0.0008)
        mst = n - self.longitude_deg / 360.0
        return mst

    def solar_mean_anomaly(self):
        M_deg = fmod(357.5291 + 0.98560028 * self.m_solar_time, 360)
        return M_deg

    def equation_of_center(self):
        M_deg = self.solar_m_anomaly
        M_radians = radians(M_deg)
        C_deg = 1.9148 * sin(M_radians) + 0.02 * sin(2 * M_radians) + 0.0003 * sin(3 * M_radians)
        return C_deg

    def ecliptic_longitude(self):
        M_deg = self.solar_m_anomaly
        C_deg = self.equation_of_center()
        lambda_deg = fmod(M_deg + C_deg + 180 + 102.9372, 360)
        # lprint(f'ecliptic_longitude={lambda_deg}')
        return lambda_deg

    def solar_transit(self):
        M_deg = self.solar_m_anomaly
        M_radians = radians(M_deg)
        lambda_deg = self.ecliptic_longitude()
        lambda_radians = radians(lambda_deg)
        J_transit = 2451545.0 + self.m_solar_time + 0.0053 * sin(M_radians) - 0.0069 * sin(2 * lambda_radians)
        return J_transit

    def sun_declination(self):
        lambda_deg = self.ecliptic_longitude()
        lambda_radians = radians(lambda_deg)
        sun_dec_deg = degrees(asin_chk(sin(lambda_radians) * sin(radians(23.4397))))
        return sun_dec_deg

    def hour_angle(self):
        sun_dec_radians = radians(self.sun_declination())
        latitude_radians = radians(self.latitude_deg)

        divisor = cos(latitude_radians) * cos(sun_dec_radians)
        dividend = (sin(radians(-0.833 - 1.15 * sqrt(self.elevation_ft) / 60.0)) - sin(latitude_radians) *
                    sin(sun_dec_radians))
        if abs(divisor) > 1e-10:
            cos_omega0 = dividend / divisor
            cos_omega0 = max(min(cos_omega0, 1.0), -1.0)
        else:
            cos_omega0 = 1.0 if dividend > 0 else -1.0
        omega0_deg = degrees(acos(cos_omega0))
        return omega0_deg

    def sunrise_and_sunset(self):
        J_transit = self.solar_transit()
        omega0_deg = self.hour_angle()
        jrise = J_transit - omega0_deg / 360.0
        jset = J_transit + omega0_deg / 360.0
        sunrise = j2iso(jrise, self.tz_info)
        sunset = j2iso(jset, self.tz_info)
        day_length_hr = omega0_deg * 24.0 / 180.0
        night_length_hr = 24 - day_length_hr
        return sunrise, sunset, day_length_hr, night_length_hr


def sunrise__info():
    return {
        'title': 'Calculate Sunrise and Sunset Time',
        'showhide': {'__': {'fields': ['location--show_map']}},
    }


def sunrise(location: qfunc = geo_location, on_date=date.today(), consider_elevation=False):
    location_str = location['Location']
    time_zone = location['Time Zone']
    geo = QGeo.from_str(location_str)
    elevation_str = '0.0 m'
    if consider_elevation:
        elevation = geo.elevation()
        if elevation: elevation_str = f'{elevation} m'
    rtn = EarthRotation(geo.latitude, geo.longitude, elevation_str, on_date, time_zone.replace(':', '/'))
    srs = rtn.sunrise_and_sunset()
    toret = {"location": location_str, "time_zone": time_zone, "sunrise": srs[0], "sunset": srs[1],
             "day_length": Qty(srs[2], 'h'), "night_length": Qty(srs[3], 'h')}
    if consider_elevation: toret.update({'elevation': Qty(elevation_str)})
    return toret


def jday__info(): return {'title': 'Calculate Julian Day Number'}


def jday(on_date=date.today()):
    jday = julian_date(on_date)
    return {"Julian Day Number": jday}


def moonphase__info(): return {'title': 'Calculate Moonphase on a Date'}


def moonphase(on_date=date.today()):
    """
    Assumptions: The New Moon (when the sun does not illuminate moon’s surface
    we see from Earth, i.e. night is dark) repeats every 29.53058770576 days (Mean Synodic Month).
    The calculation is based on the reference New Moon date of 06 January 2000 AD.
    """
    # https://www.subsystems.us/uploads/9/8/9/4/98948044/moonphase.pdf
    # https://minkukel.com/en/various/calculating-moon-phase/
    # http://individual.utoronto.ca/kalendis/lunar/#FALC
    jday_20000106 = 2451549.5
    lunar_cycle_length = 29.53058770576
    julian_day_dict = jday(on_date)
    julian_day = list(julian_day_dict.values())[0]
    # lprint('Julian day number', julian_day)
    day_since_new = julian_day - jday_20000106
    moon_age = day_since_new % lunar_cycle_length
    # this take into account of -ve automatically e.g. -1%5=4
    phases = ['New', 'Waning Crescent',
              'Third Qtr', 'Waning Gibbous', 'Full',
              'Waxing Gibbous', 'First Qtr',
              'Waxing Crescent', 'New'
              ]
    ph_interval = lunar_cycle_length / 8
    ph_num = int(round(moon_age / ph_interval, 0))
    moon_phase = phases[ph_num]
    return {"Moon Age": Qty(moon_age, 'd'), "Moon Phase": moon_phase}


def coord__info():
    return {
        'title': 'Coversion of Coordinates',
        'schema': {
            'convert': {
                'type': 'choice',
                'choices':
                    {
                        'eq2ec': 'Equatorial to Ecliptic',
                        'eq2ga': 'Equatorial to Galactic',
                        'eq2lo': 'Equatorial to Local',
                        'ec2eq': 'Ecliptic to Equatorial',
                        'ec2ga': 'Ecliptic to Galactic',
                        'ec2lo': 'Ecliptic to Local',
                        'ga2eq': 'Galactic to Equatorial',
                        'ga2ec': 'Galactic to Ecliptic',
                        'ga2lo': 'Galactic to Local',
                        'lo2eq': 'Local to Equatorial',
                        'lo2ec': 'Local to Ecliptic',
                        'lo2ga': 'Local to Galactic',
                    }
            }
        },
        # 'min_height': '300px',
        'showhide': {
            'convert': {
                'fields': [
                    'right_ascension', 'declination', 'celestial_longitude', 'celestial_latitude',
                    'galactic_longitude', 'galactic_latitude', 'azimuth', 'altitude',
                    'observer_latitude', 'local_siderial_time'
                ],
                'callback': {
                    'eq2ec': '[1,1,0,0,0,0,0,0,0,0]',
                    'eq2ga': '[1,1,0,0,0,0,0,0,0,0]',
                    'eq2lo': '[1,1,0,0,0,0,0,0,1,1]',
                    'ec2eq': '[0,0,1,1,0,0,0,0,0,0]',
                    'ec2ga': '[0,0,1,1,0,0,0,0,0,0]',
                    'ec2lo': '[0,0,1,1,0,0,0,0,1,1]',
                    'ga2eq': '[0,0,0,0,1,1,0,0,0,0]',
                    'ga2ec': '[0,0,0,0,1,1,0,0,0,0]',
                    'ga2lo': '[0,0,0,0,1,1,0,0,1,1]',
                    'lo2eq': '[0,0,0,0,0,0,1,1,1,1]',
                    'lo2ec': '[0,0,0,0,0,0,1,1,1,1]',
                    'lo2ga': '[0,0,0,0,0,0,1,1,1,1]'
                }
            }
        }
    }


def coord(convert='eq2ec',
          right_ascension='6hr,@min,@sec',
          declination='23.45 deg',
          celestial_longitude='90.0 deg',
          celestial_latitude='23.45 deg',
          galactic_longitude='90.0 deg',
          galactic_latitude='23.45 deg',
          azimuth='6hr,@min,@sec',
          altitude='23.45 deg',
          # observer_longitude='@deg',
          observer_latitude='23.45 deg',
          # local_hour_angle='@hr,@min,@sec',
          local_siderial_time='6hr,@min,@sec'
          ):
    alpha = nzv(Qty(right_ascension, 'hr').val) * pi / 12
    delta = Qty(declination, 'rad').val
    lambda_ = Qty(celestial_longitude, 'rad').val
    beta = Qty(celestial_latitude, 'rad').val
    l = Qty(galactic_longitude, 'rad').val
    b = Qty(galactic_latitude, 'rad').val
    A = nzv(Qty(azimuth, 'hr').val) * pi / 12
    h = Qty(altitude, 'rad').val
    phi = Qty(observer_latitude, 'rad').val
    theta = nzv(Qty(local_siderial_time, 'hr').val) * pi / 12
    if convert == 'eq2ec':
        lambda_, beta = equa2eclip(alpha, delta)
        return {'celestial_longitude': Qty(lambda_, 'rad', 'deg'), 'celestial_latitude': Qty(beta, 'rad', 'deg')}
    elif convert == 'eq2ga':
        l, b = equa2galac(alpha, delta)
        return {'galactic_longitude': Qty(l, 'rad', 'deg'), 'galactic_latitude': Qty(b, 'rad', 'deg')}
    elif convert == 'eq2lo':
        A, h = equa2local(alpha, delta, phi, theta)
        return {'azimuth': Qty(A * 12 / pi, 'hr'), 'altitude': Qty(h, 'rad', 'deg')}
    elif convert == 'ec2eq':
        alpha, delta = eclip2equa(lambda_, beta)
        return {'right_ascension': Qty(alpha * 12 / pi, 'hr'), 'declination': Qty(delta, 'rad', 'deg')}
    elif convert == 'ec2ga':
        l, b = eclip2galac(lambda_, beta)
        return {'galactic_longitude': Qty(l, 'rad', 'deg'), 'galactic_latitude': Qty(b, 'rad', 'deg')}
    elif convert == 'ec2lo':
        A, h = eclip2local(lambda_, beta, phi, theta)
        return {'azimuth': Qty(A * 12 / pi, 'hr'), 'altitude': Qty(h, 'rad', 'deg')}
    elif convert == 'ga2eq':
        alpha, delta = galac2equa(l, b)
        return {'right_ascension': Qty(alpha * 12 / pi, 'hr'), 'declination': Qty(delta, 'rad', 'deg')}
    elif convert == 'ga2ec':
        lambda_, beta = galac2eclip(l, b)
        return {'celestial_longitude': Qty(lambda_, 'rad', 'deg'), 'celestial_latitude': Qty(beta, 'rad', 'deg')}
    elif convert == 'ga2lo':
        A, h = galac2local(l, b, phi, theta)
        return {'azimuth': Qty(A * 12 / pi, 'hr'), 'altitude': Qty(h, 'rad', 'deg')}
    elif convert == 'lo2eq':
        alpha, delta = local2equa(A, h, phi, theta)
        return {'right_ascension': Qty(alpha * 12 / pi, 'hr'), 'declination': Qty(delta, 'rad', 'deg')}
    elif convert == 'lo2ec':
        lambda_, beta = local2eclip(A, h, phi, theta)
        return {'celestial_longitude': Qty(lambda_, 'rad', 'deg'), 'celestial_latitude': Qty(beta, 'rad', 'deg')}
    elif convert == 'lo2ga':
        l, b = local2galac(A, h, phi, theta)
        return {'galactic_longitude': Qty(l, 'rad', 'deg'), 'galactic_latitude': Qty(b, 'rad', 'deg')}


if __name__ == '__main__':
    pass
    #
    # r = EarthRotation('0 deg','90 deg', '0 ft', '1977.04.26', 'UTC')
    # print(r.jul_date)
