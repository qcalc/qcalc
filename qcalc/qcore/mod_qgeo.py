# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from geopy.geocoders import Nominatim
from django.template.loader import render_to_string
import json
from qutil import format_address, makeid, qc_timezone_ll
import math
import requests


class QGeo:
    def __init__(self, address='', latitude=None, longitude=None):
        self.geolocator = Nominatim(user_agent='qcalc')
        self.id = f'map-{makeid()}'
        if address and latitude is not None and longitude is not None:
            self.latitude, self.longitude, self.address = latitude, longitude, address
        elif address:
            self.latitude, self.longitude, self.address = self._geocode(format_address(address))
        elif latitude is not None and longitude is not None:
            self.latitude, self.longitude = latitude, longitude
            self.address = self.reverse_geocode() or 'Unnamed Location'
        else:
            raise ValueError("Either address or both latitude and longitude must be provided")

    def __str__(self):
        return f'{self.address}: {round(self.latitude, 3)}, {round(self.longitude, 3)}'

    def timezone(self):
        return qc_timezone_ll(self.latitude, self.longitude)

    @classmethod
    def from_str(cls, s):
        address, coords = s.split(': ')
        latitude, longitude = map(float, coords.split(', '))
        geo = cls(address, latitude, longitude)
        return geo

    def to_geojson(self):
        """
        Convert the location data to GeoJSON format.
        """
        geojson = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": {
                "name": self.address
            }
        }
        return geojson

    def _geocode(self, address):
        location = self.geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude, location.address
        return None, None, 'Location not found'

    def elevation(self):
        # elevation in meters
        elevation_url = f"https://api.open-elevation.com/api/v1/lookup?locations={self.latitude},{self.longitude}"
        try:
            response = requests.get(elevation_url)
            response.raise_for_status()
            altitude = response.json().get('results', [{}])[0].get('elevation')
        except (requests.RequestException, IndexError, KeyError):
            altitude = None
        return altitude

    def reverse_geocode(self):
        location = self.geolocator.reverse((self.latitude, self.longitude), exactly_one=True)
        if location:
            return location.address
        return None

    def marker(self):
        return {"location": [self.latitude, self.longitude], "popup": self.__str__()}

    @classmethod
    def calculate_zoom(cls, lat_diff, lng_diff, min_zoom=0.0, max_zoom=15.0):
        """
        Calculate an appropriate zoom level based on the latitude and longitude differences.
        The smaller the difference, the higher the zoom level.

        min_zoom and max_zoom are optional arguments to control the zoom range.
        """
        # Handle edge cases where lat/lng difference is too small
        if lat_diff == 0: lat_diff = 0.0001  # Avoid division by zero or log of zero
        if lng_diff == 0: lng_diff = 0.0001

        # Convert lat/lng difference into a rough distance in meters (approximation)
        lat_distance = lat_diff * 111_000  # meters (1 degree latitude ~ 111 km)
        lng_distance = lng_diff * 111_000 * math.cos(math.radians(lat_diff / 2))  # meters, adjust by latitude

        # Use the larger distance as the reference for zooming
        max_distance = max(lat_distance, lng_distance)

        # Formula to determine zoom level from the distance in meters
        if max_distance <= 0: return max_zoom  # Default to the highest zoom level if something goes wrong

        # Improved log-based zoom calculation with fine-tuning
        zoom = max_zoom - math.log(max_distance / 1_000) / math.log(2)

        # Ensure the zoom level stays within configurable bounds
        zoom = max(min_zoom, min(zoom, max_zoom))

        return round(zoom)

    def center(self, markers=None):
        if markers:
            # Step 1: Calculate bounds from markers
            latitudes = [marker['location'][0] for marker in markers]
            longitudes = [marker['location'][1] for marker in markers]

            min_lat, max_lat = min(latitudes), max(latitudes)
            min_lng, max_lng = min(longitudes), max(longitudes)

            # Calculate center based on bounds
            center_lat = (min_lat + max_lat) / 2
            center_lng = (min_lng + max_lng) / 2

            # Step 2: Calculate the zoom level based on lat/lng range
            lat_diff = max_lat - min_lat
            lng_diff = max_lng - min_lng
            zoom = self.calculate_zoom(lat_diff, lng_diff)
            return {'center': [center_lat, center_lng], 'zoom': zoom}
        else:
            return {'center': [self.latitude, self.longitude], 'zoom': 8}

    def display(self, zoom=None, markers=None, language='English'):
        center = self.center(markers)
        zoom = zoom or center['zoom']
        map_data = {
            "center": center['center'],
            "zoom": zoom,
            "markers": markers or [self.marker()],
        }
        return render_to_string('map.html',
                                {'map_data': json.dumps(map_data),  # | simple json dumps
                                 'map_id': self.id, 'language': language})


if __name__ == '__main__':
    # Example usage:
    lat_diff = 0.1
    lng_diff = 0.1
    zoom = QGeo.calculate_zoom(lat_diff, lng_diff)
    print(f'Calculated Zoom Level: {zoom}')
    zoom = QGeo.calculate_zoom(0, 0)
    print(f'Calculated Zoom Level: {zoom}')
