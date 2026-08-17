# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import cartopy.crs as ccrs
import cartopy
import matplotlib.pyplot as plt
from qcore import QChart
import numpy as np


class QMap(QChart):
    def __init__(self, resolution='50m'):
        super().__init__()
        self.projection = ccrs.PlateCarree()
        self.resolution = resolution

    def coastlines(self):
        projection = ccrs.PlateCarree(central_longitude=0)
        fig, ax = self.create_figure(projection)
        ax.stock_img()
        ax.coastlines(resolution=self.resolution)
        return fig

    def draw_features(self, ax):
        ax.add_feature(cartopy.feature.BORDERS)
        ax.add_feature(cartopy.feature.COASTLINE)
        # ax.add_feature(cartopy.feature.LAKES, edgecolor='black')
        ax.add_feature(cartopy.feature.LAND, edgecolor='black')
        ax.add_feature(cartopy.feature.OCEAN)
        # ax.add_feature(cartopy.feature.RIVERS)
        ax.add_feature(cartopy.feature.STATES)
        ax.gridlines()
        ax.coastlines(resolution=self.resolution)

    def region(self, central_latitude=50.0, central_lonitude=0, extent_lat=10.0, extent_long=18.0):
        extent = [central_lonitude - extent_long, central_lonitude + extent_long,
                  central_latitude - extent_lat, central_latitude + extent_lat]
        projection = ccrs.Orthographic(central_lonitude, central_latitude)
        fig, ax = self.create_figure(projection)
        ax.set_extent(extent)
        self.draw_features(ax)
        return fig

    def mark(self, lat, long):
        plt.plot([long, long], [lat, lat],
                 color='red', linewidth=2, marker='o', transform=self.projection)

    def distance(self, lat1, long1, lat2, long2):
        fig, ax = self.create_figure(projection=ccrs.PlateCarree(central_longitude=(long1 + long2) / 2))
        offset_lat = max(abs(long1 - long2), 10) / 2
        offset_lng = max(abs(lat1 - lat2), 10) / 2
        ax.set_extent([
            max(min(long1, long2) - offset_lng, -180),
            min(max(long1, long2) + offset_lng, 180),
            max(min(lat1, lat2) - offset_lat, -90),
            min(max(lat1, lat2) + offset_lat, 90)]
        )
        # print([min(long1, long2) - offset_lng, max(long1, long2) + offset_lng,
               # min(lat1, lat2) - offset_lat, max(lat1, lat2) + offset_lat])
        self.draw_features(ax)
        plt.plot([long1, long2], [lat1, lat2],
                 color='red', linewidth=2, marker='o', transform=ccrs.Geodetic())
        plt.plot([long1, long2], [lat1, lat2],
                 color='gray', linestyle='--', transform=ccrs.PlateCarree())
        return fig

    def mark_multiple(self, coordinates):
        """Allow users to plot multiple locations at once."""
        for lat, long in coordinates:
            plt.plot([long, long], [lat, lat], color='blue', linewidth=2, marker='o', transform=self.projection)
        return plt.gcf()

    def draw_polygon(self, coordinates):
        """Allow users to display polygons, useful for visualizing zones or regions."""
        lon, lat = zip(*coordinates)
        plt.fill(lon, lat, transform=self.projection, alpha=0.4, edgecolor='blue', facecolor='lightblue')
        return plt.gcf()

    @classmethod
    def draw_path(cls, path_coords):
        """Draw paths or routes between multiple locations.
        This could be useful for users needing to visualize journeys or routes."""
        lons, lats = zip(*path_coords)
        plt.plot(lons, lats, color='green', linewidth=2, marker='o', transform=ccrs.Geodetic())
        return plt.gcf()

    def heatmap(self, data_points, intensity):
        """If you want to visualize density (such as population or temperature variations),
        a heatmap feature would be useful"""
        x, y = zip(*data_points)
        heatmap_data = np.histogram2d(x, y, bins=50, weights=intensity)[0]
        plt.imshow(heatmap_data, cmap='hot', interpolation='nearest', transform=self.projection)
        return plt.gcf()

    def zoom(self, factor=2):
        ax = plt.gca()
        ax.set_extent([ax.get_xlim()[0] / factor, ax.get_xlim()[1] * factor,
                       ax.get_ylim()[0] / factor, ax.get_ylim()[1] * factor], crs=self.projection)
        return plt.gcf()


if __name__ == '__main__':
    pass
