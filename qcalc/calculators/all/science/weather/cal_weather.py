# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty, qfunc, QGeo, QScreen, qhtml
from django.conf import settings
import math
from qutil import pretty_json
from datetime import datetime, timezone, timedelta
import requests

from calc import check_setting
from calculators.all.general.map.cal_location import geo_location


def wind_chill__info():
    return {'title': 'Wind Chill Calculator'}


# https://www.weather.gov/media/epz/wxcalc/windChill.pdf
# https://www.backpacker.com/skills/how-to-calculate-wind-chill/
def wind_chill(air_temperature='10 degF', wind_speed='15 mph'):
    temp_uom = Qty(air_temperature).uom
    temp_f = Qty(air_temperature, 'degF').val
    wind_speed = Qty(wind_speed, 'mph')

    speed = wind_speed.val
    if temp_f > 50.0 or temp_f < -50.0:
        raise Exception(f"Error (WCH): Enter a temperature between -50 and +50 degF, your entry is {temp_f} degF")
    if speed < 3.0:
        raise Exception(f"Error (WCH): Enter a windspeed >= 3.0 mph, your entry is {speed} mph")
    wp = speed ** 0.16
    chill = 35.74 + 0.6215 * temp_f - 35.75 * wp + 0.4275 * temp_f * wp
    feel_like = Qty(chill, temp_uom)

    temp_c = Qty(air_temperature, 'degC').val
    speed = wind_speed.to('m/s').val
    wpm2 = (12.1452 + 11.6222 * speed ** 0.5 - 1.16222 * speed) * (33 - temp_c)
    heat_loss = Qty(wpm2, 'W/m^2')
    return {
        'Feel Like': feel_like,
        'Heat Loss': heat_loss
    }


def visibility__info():
    return {
        'title': 'Calculate Visibility Distance using Koschmieder Law',
        'schema': {
            'humidity': {'attrs': {'min': 0.0, 'max': 100.0}},
            'pollution_level': {
                'type': 'choice',
                'choices': {
                    '1.0': 'Clear (1.0)',
                    '1.5': 'Low Pollution (1.5)',
                    '2.0': 'Moderate Pollution (2.0)',
                    '2.5': 'High Pollution (2.5)',
                    '3.0': 'Heavy Pollution (3.0)',
                    '3.5': 'Very Heavy Pollution (3.5)',
                    '4.0': 'Severe Pollution (4.0)',
                },
            }
        }
    }


def visibility(temperature='68 degF', humidity: float = 85.0, air_pressure='1013.0 hPa', pollution_level='2.0'):
    """
    Calculate visibility distance in kilometers using Koschmieder's law.
    The pollution level factor is added to account for air quality impacts.

    Parameters:
    - temperature: Temperature in degrees Celsius
    - humidity: Relative humidity as a percentage (0-100)
    - air_pressure: Air pressure in hPa (hectopascals)
    - pollution_level: Pollution factor (1 = clear, 2 = moderate pollution, 3 = heavy pollution)

    Returns:
    - visibility_distance: Estimated visibility in kilometers
    """
    # Constants
    base_extinction = 0.1  # Base atmospheric extinction coefficient (typical value)

    # Adjust base extinction for pollution level
    extinction_coefficient = base_extinction * float(pollution_level)

    # Adjust for humidity: Higher humidity increases extinction coefficient
    if humidity > 70:
        humidity_factor = 1 + (humidity - 70) / 100  # Increase extinction for high humidity
        extinction_coefficient *= humidity_factor

    # Adjust for temperature: Higher temperatures can cause heat haze, affecting visibility
    temperature_c = Qty(temperature, 'degC').val
    temp_adjustment = 1 + (
        temperature_c - 20) * 0.01  # Example adjustment; this could be refined based on specific data
    extinction_coefficient *= temp_adjustment

    # Adjust for air pressure: Lower pressure can increase atmospheric scattering
    air_pressure_hpa = Qty(air_pressure, 'hPa').val
    pressure_adjustment = (1013 / air_pressure_hpa)  # Standard pressure is 1013 hPa
    extinction_coefficient *= pressure_adjustment

    # Koschmieder equation: Visibility (km) = 3.912 / extinction_coefficient
    visibility_distance = 3.912 / extinction_coefficient

    return {'visibility_distance': Qty(visibility_distance, 'km')}


def heat_index__info():
    return {
        'title': 'Calculate the Heat Index based on Temperature and Humidity'
    }


def heat_index(temperature='90 degF', humidity: float = 60.0):  # result 100 degF
    """
    Calculate the Heat Index based on temperature and relative humidity.

    Parameters:
    - temperature: Air temperature in degrees Celsius
    - humidity: Relative humidity as a percentage (0-100)

    Returns:
    - heat_index: Calculated heat index in degrees Celsius
    """
    # Convert temperature to Fahrenheit for calculation
    temp_uom = Qty(temperature).uom
    temperature_f = Qty(temperature, 'degF').val

    # Heat index formula (Fahrenheit)
    heat_index_f = (
        -42.379 + 2.04901523 * temperature_f + 10.14333127 * humidity -
        0.22475541 * temperature_f * humidity - 0.00683783 * temperature_f ** 2 -
        0.05481717 * humidity ** 2 + 0.00122874 * temperature_f ** 2 * humidity +
        0.00085282 * temperature_f * humidity ** 2 - 0.00000199 * temperature_f ** 2 * humidity ** 2
    )

    heat_index = Qty(heat_index_f, temp_uom)
    return {'heat_index': heat_index}


def dew_point__info():
    return {
        'title': 'Calculate the Dew Point based on Temperature and Humidity'
    }


def dew_point(temperature='68 degF', humidity: float = 85.0):
    """
    Calculate the Dew Point based on temperature and relative humidity.

    Parameters:
    - temperature: Air temperature in degrees Celsius
    - humidity: Relative humidity as a percentage (0-100)

    Returns:
    - dew_point: Calculated dew point in degrees Celsius
    """
    # Constants for the dew point calculation
    a = 17.27
    b = 237.7

    # Calculate alpha
    temperature_c = Qty(temperature, 'degC').val
    alpha = ((a * temperature_c) / (b + temperature_c)) + math.log(humidity / 100.0)

    # Calculate dew point
    dew_point = (b * alpha) / (a - alpha)

    return {'dew_point': dew_point}


def weather__info():
    return {
        'title': 'Get Weather Information of a Location',
        'fargs': {
            'location--show_map': 'Local',
        }
    }


def weather(location: qfunc = geo_location, show_data=False):
    def get_weather_data(lat, lng):
        api_key = check_setting(settings.OPENW_API_KEY, "OPENW_API_KEY", optional=False)
        api_url = check_setting(settings.OPENW_API_URL, "OPENW_API_URL", optional=False)
        params = {
            "lat": lat,
            "lon": lng,
            "units": "metric",
            "appid": api_key
        }
        response = requests.get(api_url, params=params, timeout=(3, 15))
        data = response.json()
        return data

    def format_weather_data(data):
        weather_main = data['weather'][0]['main']
        weather_desc = data['weather'][0]['description']

        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        temp_min = data['main']['temp_min']
        temp_max = data['main']['temp_max']

        humidity = data['main']['humidity']
        pressure = data['main']['pressure']

        wind_speed = data['wind']['speed']
        wind_deg = data['wind']['deg']

        visibility = data['visibility']

        timezone_offset = data['timezone'] // 3600  # Convert seconds to hours
        timezone_ = timezone(timedelta(hours=timezone_offset))
        sunrise = datetime.fromtimestamp(data['sys']['sunrise'], tz=timezone.utc).astimezone(timezone_).strftime(
            '%Y-%m-%d %H:%M:%S')
        sunset = datetime.fromtimestamp(data['sys']['sunset'], tz=timezone.utc).astimezone(timezone_).strftime(
            '%Y-%m-%d %H:%M:%S')

        return (
            f"<pre>"
            f"Weather: {weather_main} ({weather_desc})<br>"
            f"Temperature: {temp}°C (feels like {feels_like}°C)<br>"
            f"Min/Max Temperature: {temp_min}°C / {temp_max}°C<br>"
            f"Humidity: {humidity}%<br>"
            f"Pressure: {pressure} hPa<br>"
            f"Wind: {wind_speed} m/s, {wind_deg}°<br>"
            f"Visibility: {visibility} meters<br>"
            f"Timezone: UTC{timezone_offset:+}<br>"
            f"Sunrise: {sunrise} UTC{timezone_offset:+}<br>"
            f"Sunset: {sunset} UTC{timezone_offset:+}<br>"
            f"</pre>"
        )

    location_str = location['Location']
    geo = QGeo.from_str(location_str)
    json_data = get_weather_data(geo.latitude, geo.longitude)
    weather_report = format_weather_data(json_data)

    toret = {
        'Location': location_str,
        'Weather Report': qhtml(weather_report),
    }

    if show_data:
        out = QScreen()
        out.write(pretty_json(json_data))
        toret.update({'Weather Data': out.flush()})

    if 'Map' in location:
        toret.update({'Map': location['Map']})
    return toret


# if __name__ == '__main__':
#     import sett
#
#     # weather()
#
#     # Example usage
#     humidity = 85  # Relative humidity in %
#     temperature = '20 degC'  # Temperature in Celsius
#     air_pressure = '1013 hPa'  # Standard air pressure in hPa
#     pollution_level = '2.0'  # Moderate pollution level
#
#     visi = visibility(temperature, humidity, air_pressure, pollution_level)
#     print(f"Estimated visibility distance: {visi:.2f} km")
