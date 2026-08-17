# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import QGeo, qhtml, qtexta


def geo_location__info():
    return {
        'title': 'Show a Geographic Location',
        'schema': {
            'method': {'type': 'choice', 'choices': {'1': 'Latitude-Longitude Known', '2': 'Name of Location Known'}},
            'show_map': {'type': 'radio', 'choices': ['None', 'English', 'Local']}
        },
        'showhide': {
            'method': {
                'fields': ['latitude', 'longitude', 'location'],
                'callback': "gloc_method"
            }
        },
        'script': '''
        function gloc_method(v){
            if(v=='1'){
                return [true, true, false]
            }else if(v=='2'){
                return [false, false, true]
            }
        }
        '''
    }


def geo_location(method='2', latitude=50.0, longitude=0.0, location: qtexta = 'London, England', show_map='None'):
    geo = None
    timezone = None
    if method == '1':
        geo = QGeo(latitude=latitude, longitude=longitude)
        timezone = geo.timezone()
    elif method == '2':
        geo = QGeo(address=location)
        timezone = geo.timezone()
    toret = {
        'Location': str(geo),
        'Time Zone': f'{timezone}'
    }
    if show_map != 'None':
        toret.update({'Map': qhtml(geo.display(language=show_map))})

    return toret
