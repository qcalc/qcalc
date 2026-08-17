# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from math import sin, cos, acos, pi
from qcore import Qty, QMap, QGeo, qhtml, qtexta


def map_region__info():
    return {
        'title': 'Show Geographic Region',
        'schema': {
            'resolution': {'type': 'radio', 'choices': ['110m', '50m', '10m']}
        }
    }


def map_region(central_latitude=50.0, central_lonitude=0.0, resolution='50m', extent_lat=10.0, extent_lng=18.0):
    map_ = QMap(resolution=resolution)
    _fig = map_.region(central_latitude, central_lonitude, extent_lat, extent_lng)
    map_.mark(central_latitude, central_lonitude)
    map_.render_done()
    return {'Map': map_}


def map_distance__info():
    return {
        'title': 'Distance between Two Locations on Earth',
        'schema': {
            'method': {'type': 'choice', 'choices': {'1': 'Latitude-Longitude Known', '2': 'Name of Locations Known'}},
            'show_map': {'type': 'radio', 'choices': ['None', 'English', 'Local']},
        },
        'showhide': {
            'method': {
                'fields': ['from_latitude', 'from_longitude', 'to_latitude', 'to_longitude',
                           'from_location', 'to_location'],
                'callback': "fcall_method"
            }
        },
        'script': '''
        function fcall_method(v){
            if(v=='1'){
                return [true, true, true, true, false, false]
            }else if(v=='2'){
                return [false, false, false, false, true ,true]
            }
        }
        '''
    }


def map_distance(method='1', from_latitude=50.0, from_longitude=0.0,
                 to_latitude=24.0, to_longitude=90.0, from_location: qtexta = 'London, England',
                 to_location: qtexta = 'New York, USA', show_map='None'):
    dist = 0
    earth_radius = 6378.0  # km
    from_geo = None
    to_geo = None
    if method == '1':
        lat1 = from_latitude * pi / 180
        lng1 = from_longitude * pi / 180
        lat2 = to_latitude * pi / 180
        lng2 = to_longitude * pi / 180
        dist = acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lng2 - lng1)) * earth_radius
        from_geo = QGeo(address=from_location)
        to_geo = QGeo(address=to_location)
    elif method == '2':
        from_geo = QGeo(address=from_location)
        to_geo = QGeo(address=to_location)
        lat1d = from_geo.latitude
        lng1d = from_geo.longitude
        lat2d = to_geo.latitude
        lng2d = to_geo.longitude
        lat1 = lat1d * pi / 180
        lng1 = lng1d * pi / 180
        lat2 = lat2d * pi / 180
        lng2 = lng2d * pi / 180
        dist = acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lng2 - lng1)) * earth_radius

    toret = {
        'Distance': Qty(dist, 'km'),
        'From Location': str(from_geo),
        'To Location': str(to_geo),
    }
    if show_map != 'None':
        # map = QMap(resolution='50m')
        # fig = map.distance(lat1d, lng1d, lat2d, lng2d)
        # map.close(fig)
        # toret.update({'Map': map})
        toret.update({'Map': qhtml(from_geo.display(markers=[from_geo.marker(), to_geo.marker()], language=show_map))})

    return toret
