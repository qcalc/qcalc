# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import math
from qcore import Qty, qfunc
from qutil import QDateTime, qc_datetime_to_str
from datetime import timedelta
from calculators.all.science.astronomy.cal_earth_rotation import sunrise

# CoC in mm
image_sensor_coc = {
    "APS-C": 0.018,
    "APS-C Canon": 0.018,
    "APS-C Nikon/Pentax/Sony": 0.019,
    "APS-H Canon": 0.023,
    "Four Thirds": 0.015,
    "1 inch": 0.011,
    "35 mm": 0.029,
    "645 (6x4.5)": 0.047,
    "6x6": 0.053,
    "6x7": 0.059,
    "6x9": 0.067,
    "6x12": 0.083,
    "6x17": 0.12,
    "4x5": 0.11,
    "5x7": 0.15,
    "8x10": 0.22,
}


def depth_of_field__info():
    return {
        'title': 'Depth of Field Calculator',
        'desc': 'Depth of Field (DoF) in photography refers to the range of distance '
                'within a photo that appears acceptably sharp and in focus',
        'schema': {
            'image_sensor': {'type': 'choice', 'choices': list(image_sensor_coc.keys())}
        }
    }


def depth_of_field(aperture=2.8, focal_length='50 mm', distance_to_subject='2 m', image_sensor='35 mm'):
    circle_of_confusion = float(image_sensor_coc[image_sensor])
    focal_length = Qty(focal_length, 'mm').val
    distance_to_subject = Qty(distance_to_subject, 'mm').val
    hyperfocal_distance = (focal_length ** 2) / (aperture * circle_of_confusion)
    near_point = (hyperfocal_distance * distance_to_subject) / (
        hyperfocal_distance + (distance_to_subject - focal_length))
    far_point = (hyperfocal_distance * distance_to_subject) / (
        hyperfocal_distance - (distance_to_subject - focal_length))
    depth_of_field = far_point - near_point
    return {
        'near_point': Qty(near_point, 'mm', 'm'),
        'far_point': Qty(far_point, 'mm', 'm'),
        'depth_of_field': Qty(depth_of_field, 'mm', 'm')
    }


def exposure_value__info():
    return {
        'title': 'Exposure Value Calculator',
        'desc': 'Exposure is determined by the relationship between aperture, shutter speed, and ISO.'
    }


def exposure_value(aperture=2.8, shutter_speed='1 ss60', iso=100):
    ev = (aperture ** 2) / Qty(shutter_speed, 's').val * (100 / iso)
    return ev


def field_of_view__info():
    return {
        'title': 'Calculate Field of View',
        'desc': 'Field of view (FOV) is the maximum area of a scene that can be captured by the camera sensor. '
                'Field of View is determined by the sensor size and the focal length of the lens.'
    }


def field_of_view(sensor_size='36 mm', focal_length='50 mm'):
    fov = 2 * math.atan(Qty(sensor_size, 'mm').val / (2 * Qty(focal_length, 'mm').val))
    fov_degrees = math.degrees(fov)
    return Qty(fov_degrees, 'deg')


def aspect_ratio__info():
    return {
        'title': 'Calculate Aspect Ratio',
        'desc': 'Aspect ratio is simply the ratio of the width to the height of the image.'
    }


def aspect_ratio(width: int = 1920, height: int = 1080):
    gcd = math.gcd(width, height)
    return f"{width // gcd}:{height // gcd}"


def shutter_speed__info():
    return {
        'title': 'Calculate Shutter Speed',
        'desc': 'Calculate the required shutter speed based on focal length to avoid camera shake.'
    }


def shutter_speed(focal_length='50 mm', crop_factor=1.0):
    return f"1/{int(Qty(focal_length, 'mm').val * crop_factor)} sec"


def equivalent_focal_length__info():
    return {
        'title': 'Equivalent Focal Length Calculator',
        'desc': 'Calculate the equivalent focal length for different crop factor (that depends on sensor size).'
    }


def equivalent_focal_length(focal_length='50 mm', crop_factor=1.0):
    return Qty(int(Qty(focal_length, 'mm').val * crop_factor), 'mm')


def hyperfocal_distance__info():
    return {
        'title': 'Hyperfocal Distance Calculator',
        'desc': 'The hyperfocal distance is the closest distance at which a lens can be focused '
                'while keeping objects at infinity acceptably sharp.',
        'schema': {
            'image_sensor': {'type': 'choice', 'choices': list(image_sensor_coc.keys())}
        }
    }


def hyperfocal_distance(focal_length='50 mm', aperture=8.0, image_sensor='35 mm'):
    circle_of_confusion = float(image_sensor_coc[image_sensor])
    focal_length = Qty(focal_length, 'mm').val
    return Qty((focal_length ** 2) / (aperture * circle_of_confusion), 'mm', 'm')


def image_resolution__info():
    return {
        'title': 'Image Resolution Calculator',
        'desc': 'Calculate the number of megapixels of an image based on its dimensions.'
    }


def image_resolution(width=6000, height=4000):
    return (width * height) / 1_000_000  # in megapixels


def image_storage_required__info():
    return {
        'title': 'Image Storage Requirement Calculator',
        'desc': 'Calculate the storage required for a given number of images based on their resolution and bit depth.'
    }


def image_storage_required(image_count=100, width=6000, height=4000, bit_depth=24):
    bytes_per_pixel = bit_depth / 8
    bytes_per_image = width * height * bytes_per_pixel
    total_bytes = image_count * bytes_per_image
    total_gb = total_bytes / (1024 ** 3)  # Convert to GB
    return Qty(total_gb, 'gb')


def image_print_size__info():
    return {
        'title': 'Image Print Size Calculator',
        'desc': 'Calculate the maximum print size based on image resolution and desired DPI.'
    }


def image_print_size(image_width=6000, image_height=4000, dpi=300):
    width_in_inches = image_width / dpi
    height_in_inches = image_height / dpi
    return {"Print Width": Qty(width_in_inches, 'inch'),
            "Print Height": Qty(height_in_inches, 'inch')}


def golden_hours__info():
    return {
        'title': "Golden and Magic Hours of Photography",
        'desc': 'Golden and Magic Hours are the best time of day to photograph. '
                'The golden hour typically lasts about one hour after sunrise and one hour before sunset, '
                'and the magic hour is roughly one hour before sunrise and one hour after sunset. '

    }


def golden_hours(sun_rise: qfunc = sunrise):
    sunrise_dt = QDateTime(sun_rise['sunrise']).val
    sunset_dt = QDateTime(sun_rise['sunset']).val
    golden_hour_start_morning = sunrise_dt
    golden_hour_end_morning = sunrise_dt + timedelta(hours=1)
    golden_hour_start_evening = sunset_dt - timedelta(hours=1)
    golden_hour_end_evening = sunset_dt

    magic_hour_start_morning = sunrise_dt - timedelta(hours=1)
    magic_hour_end_morning = sunrise_dt
    magic_hour_start_evening = sunset_dt
    magic_hour_end_evening = sunset_dt + timedelta(hours=1)

    return {
        "location": sun_rise['location'], "time_zone": sun_rise['time_zone'],
        "sunrise": sun_rise['sunrise'], "sunset": sun_rise['sunset'],
        "day_length": sun_rise['day_length'], "night_length": sun_rise['night_length'],
        "magic_hour_morning": f'{qc_datetime_to_str(magic_hour_start_morning)} - {qc_datetime_to_str(magic_hour_end_morning)}',
        "golden_hour_morning": f'{qc_datetime_to_str(golden_hour_start_morning)} - {qc_datetime_to_str(golden_hour_end_morning)}',
        "golden_hour_evening": f'{qc_datetime_to_str(golden_hour_start_evening)} - {qc_datetime_to_str(golden_hour_end_evening)}',
        "magic_hour_evening": f'{qc_datetime_to_str(magic_hour_start_evening)} - {qc_datetime_to_str(magic_hour_end_evening)}'
    }
