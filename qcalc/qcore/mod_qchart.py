# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import matplotlib.pyplot as plt
import matplotlib as mpl
import io
import base64
import numpy as np
from statistics import fmean, stdev
import pandas as pd
import networkx as nx
from qutil import QThread, joinx
import matplotlib.dates as mdates  # requires for 3D as 3D cant natively handle date axes
from datetime import date, datetime

color_schemes = [
    'Accent', 'Accent_r', 'Blues', 'Blues_r', 'BrBG', 'BrBG_r', 'BuGn', 'BuGn_r', 'BuPu', 'BuPu_r', 'CMRmap',
    'CMRmap_r', 'Dark2', 'Dark2_r', 'GnBu', 'GnBu_r', 'Greens', 'Greens_r', 'Greys', 'Greys_r', 'OrRd', 'OrRd_r',
    'Oranges', 'Oranges_r', 'PRGn', 'PRGn_r', 'Paired', 'Paired_r', 'Pastel1', 'Pastel1_r', 'Pastel2', 'Pastel2_r',
    'PiYG', 'PiYG_r', 'PuBu', 'PuBuGn', 'PuBuGn_r', 'PuBu_r', 'PuOr', 'PuOr_r', 'PuRd', 'PuRd_r', 'Purples',
    'Purples_r', 'RdBu', 'RdBu_r', 'RdGy', 'RdGy_r', 'RdPu', 'RdPu_r', 'RdYlBu', 'RdYlBu_r', 'RdYlGn', 'RdYlGn_r',
    'Reds', 'Reds_r', 'Set1', 'Set1_r', 'Set2', 'Set2_r', 'Set3', 'Set3_r', 'Spectral', 'Spectral_r', 'Wistia',
    'Wistia_r', 'YlGn', 'YlGnBu', 'YlGnBu_r', 'YlGn_r', 'YlOrBr', 'YlOrBr_r', 'YlOrRd', 'YlOrRd_r', 'afmhot',
    'afmhot_r', 'autumn', 'autumn_r', 'binary', 'binary_r', 'bone', 'bone_r', 'brg', 'brg_r', 'bwr', 'bwr_r', 'cividis',
    'cividis_r', 'cool', 'cool_r', 'coolwarm', 'coolwarm_r', 'copper', 'copper_r', 'cubehelix', 'cubehelix_r', 'flag',
    'flag_r', 'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_heat', 'gist_heat_r', 'gist_ncar',
    'gist_ncar_r', 'gist_rainbow', 'gist_rainbow_r', 'gist_stern', 'gist_stern_r', 'gist_yarg', 'gist_yarg_r',
    'gnuplot', 'gnuplot2', 'gnuplot2_r', 'gnuplot_r', 'gray', 'gray_r', 'hot', 'hot_r', 'hsv', 'hsv_r', 'inferno',
    'inferno_r', 'jet', 'jet_r', 'magma', 'magma_r', 'nipy_spectral', 'nipy_spectral_r', 'ocean', 'ocean_r', 'pink',
    'pink_r', 'plasma', 'plasma_r', 'prism', 'prism_r', 'rainbow', 'rainbow_r', 'seismic', 'seismic_r', 'spring',
    'spring_r', 'summer', 'summer_r', 'tab10', 'tab10_r', 'tab20', 'tab20_r', 'tab20b', 'tab20b_r', 'tab20c',
    'tab20c_r', 'terrain', 'terrain_r', 'turbo', 'turbo_r', 'twilight', 'twilight_r', 'twilight_shifted',
    'twilight_shifted_r', 'viridis', 'viridis_r', 'winter', 'winter_r'
]

legend_locations = [
    'none',
    'upper left out', 'upper center out', 'upper right out',
    'lower left out', 'lower center out', 'lower right out',
    'left upper out', 'left center out', 'left lower out',
    'right upper out', 'right center out', 'right lower out',
    'upper left', 'upper center', 'upper right',
    'lower left', 'lower center', 'lower right',
    'center left', 'center', 'center right',
    'right', 'best',
]


class QChart:

    def __init__(self, width: int = None, aspect: float = 0.0,
                 color_scheme=None, xtype=float):
        # | width in pixel, aspect is the ratio of height and width (h=a*w)
        # | both the width and aspect are optional

        self.color_scheme = color_scheme or QThread.get_pref('chart_color_scheme', 'tab20')

        # | Handle width and height
        self.width = width or QThread.get_pref('chart_width', 620)
        self.height = int(self.width * aspect) if aspect > 0.0 else QThread.get_pref('chart_height', 620)
        self.figsize = (self.width / 100, self.height / 100)
        self.aspect = self.height / self.width

        # | Backend for rendering without GUI
        # https://stackoverflow.com/questions/52839758/matplotlib-and-runtimeerror-main-thread-is-not-in-main-loop
        plt.switch_backend('agg')
        plt.set_loglevel('WARNING')

        self.b64 = None
        self.fig, self.ax = None, None  # | Placeholder for figure and axis objects
        self.projection = None

        # | optional saved data
        self.data = None
        self.chtype = None
        self.dtype_x = xtype
        self.legend_loc = QThread.get_pref('chart_legend', 'lower center out')
        self.legend_loc_best = None
        self.legend_labels = None

    def __str__(self):
        return f'Chart image base64 size {len(self.b64)} bytes'

    def set_labels(self, xlabel=None, ylabel=None, zlabel=None, title=None, grid=False):
        if xlabel: self.ax.set_xlabel(xlabel)
        if ylabel: self.ax.set_ylabel(ylabel)
        if zlabel: self.ax.set_zlabel(zlabel)
        if title: self.ax.set_title(title, pad=20)
        if grid: self.ax.grid()
        # if aspect > 0.0: self.ax.set_aspect(aspect)

    def set_legend(self, labels, loc=None):
        self.legend_labels = labels
        self.legend_loc = loc or self.legend_loc
        if self.legend_loc == 'best':
            self.legend_loc = self.legend_loc_best or 'best'

    def show_legend(self):
        outside = {
            'upper left out': (0, 1.01), 'upper center out': (.5, 1.01), 'upper right out': (1, 1.01),
            'lower left out': (0, -0.25 / self.aspect), 'lower center out': (0.5, -0.25 / self.aspect),
            'lower right out': (1, -0.25 / self.aspect),
            'left upper out': (-0.2, 1), 'left center out': (-0.2, 0.5), 'left lower out': (-0.2, 0),
            'right upper out': (1.05, 1), 'right center out': (1.05, 0.5), 'right lower out': (1.05, 0)
        }
        inside = [
            'upper left', 'upper center', 'upper right',
            'lower left', 'lower center', 'lower right',
            'center left', 'center', 'center right',
            'right', 'best',
        ]

        loc = self.legend_loc
        labels = self.legend_labels
        if loc == 'none':
            return
        elif loc == 'upper left out':
            self.ax.legend(loc='lower left', bbox_to_anchor=outside[loc], borderaxespad=0., labels=labels)
        elif loc == 'upper center out':
            ncol = 2 if len(labels) > 4 else 1
            self.ax.legend(loc='lower center', bbox_to_anchor=outside[loc], borderaxespad=0., labels=labels, ncol=ncol)
        elif loc == 'upper right out':
            self.ax.legend(loc='lower right', bbox_to_anchor=outside[loc], borderaxespad=0., labels=labels)
        elif loc == 'lower left out':
            self.ax.legend(loc='upper left', bbox_to_anchor=outside[loc], borderaxespad=1, labels=labels)
        elif loc == 'lower center out':
            ncol = 2 if len(labels) > 4 else 1
            self.ax.legend(loc='upper center', bbox_to_anchor=outside[loc], borderaxespad=1, labels=labels, ncol=ncol)
        elif loc == 'lower right out':
            self.ax.legend(loc='upper right', bbox_to_anchor=outside[loc], borderaxespad=1, labels=labels)
        elif loc == 'left upper out':
            self.ax.legend(loc='upper right', bbox_to_anchor=outside[loc], borderaxespad=0., labels=labels)
        elif loc == 'left center out':
            self.ax.legend(loc='center right', bbox_to_anchor=outside[loc], borderaxespad=0., labels=labels)
        elif loc == 'left lower out':
            self.ax.legend(loc='lower right', bbox_to_anchor=outside[loc], borderaxespad=0., labels=labels)
        elif loc == 'right upper out':
            self.ax.legend(loc='upper left', bbox_to_anchor=outside[loc], borderaxespad=0., labels=labels)
        elif loc == 'right center out':
            self.ax.legend(loc='center left', bbox_to_anchor=outside[loc], borderaxespad=0., labels=labels)
        elif loc == 'right lower out':
            self.ax.legend(loc='lower left', bbox_to_anchor=outside[loc], borderaxespad=0., labels=labels)
        elif loc in inside:
            self.ax.legend(loc=loc, borderaxespad=0., labels=labels)

        self.fig.tight_layout()
        # self.fig.tight_layout(rect=[0, 0.1, 1, 1])  # Adjust the rect to give more space at the bottom

    def save_data(self, data, chtype):
        self.data = data
        self.chtype = chtype

    def fig2b64(self):
        buf = io.BytesIO()
        self.fig.savefig(buf)
        # self.fig.savefig(buf, format='png', bbox_inches='tight')
        self.b64 = base64.b64encode(buf.getvalue()).decode()
        buf.close()
        plt.close(self.fig)

    def chart(self):
        return self.b64

    def create_figure(self, projection=None):
        """Create a 2D or 3D figure and axis."""
        self.projection = projection
        if self.projection is None:
            subplot_kw = {}
        else:
            subplot_kw = {"projection": self.projection}

        self.fig, self.ax = plt.subplots(figsize=self.figsize, subplot_kw=subplot_kw)
        return self.fig, self.ax

    def render_done(self):
        if self.projection == '3d':
            # for 2d native support available for dates
            # Set padding for the X-axis ticks and labels
            if self.dtype_x == date:
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            elif self.dtype_x == datetime:
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))

        # x_ticks = [label.get_text() for label in self.ax.get_xticklabels()]
        if self.ax is not None:
            x_ticks = [label.get_text() for label in self.ax.get_xticklabels()]
        else:
            # Handle the case where self.ax is None e.g. word_cloud chart
            x_ticks = []

        if x_ticks:
            count_label = len(x_ticks)
            max_label_length = max(len(label) for label in x_ticks)
            rotate_x = (count_label * max_label_length) > int((self.width - 120) / 12)
            if rotate_x:
                labelpad = max_label_length * 3
                self.ax.set_xlabel(self.ax.get_xlabel(), labelpad=labelpad)
                plt.gcf().autofmt_xdate()

        if self.legend_labels and self.legend_loc != 'none': self.show_legend()
        self.fig2b64()

    def render_surface3d(self, xvals: list | None = None, yvals: list | None = None, zvals2d: list | None = None,
                         xlabel='x', ylabel='y', zlabel='z', title='z vs x,y', surface_type='Surface'):
        """Render a 3D surface plot."""
        if xvals is None: xvals = []
        if yvals is None: yvals = []

        zvals2d = zvals2d or []

        X, Y = np.meshgrid(np.array(xvals), np.array(yvals))
        Z = np.array(zvals2d)

        fig, ax = self.create_figure("3d")

        if surface_type == 'Contour':
            ax.contour(X, Y, Z, cmap=self.color_scheme, antialiased=False)
        elif surface_type == 'Contourf':
            ax.contourf(X, Y, Z, cmap=self.color_scheme, antialiased=False)
        elif surface_type == 'Wireframe':
            ax.plot_wireframe(X, Y, Z, rstride=10, cstride=10)
        # elif surface_type == 'Surface':
        else:  # Default to Surface plot type 'Surface'
            ax.plot_surface(X, Y, Z, cmap=self.color_scheme, antialiased=False)
        self.set_labels(xlabel, ylabel, zlabel, title, grid=True)
        self.render_done()

    def render_line3d(self, xvals: list | None = None, yvals: list | None = None, zvals: list | None = None,
                      xlabel='x', ylabel='y', zlabel='z', title='z vs x,y'):
        """Render a 3D line plot."""
        if xvals is None: xvals = []
        if yvals is None: yvals = []
        if zvals is None: zvals = []

        fig, ax = self.create_figure("3d")
        ax.plot3D(xvals, yvals, zvals, 'red', linewidth=1)
        self.set_labels(xlabel, ylabel, zlabel, title, grid=True)
        self.render_done()

    def render_lines(self, xvals: list | None = None, yvalsm: list | None = None,
                     xlabel='x', ylabels: list | None = None, ylabel='y', title='y vs x'):
        """Render line chart(s)."""
        if xvals is None: xvals = []
        if yvalsm is None: yvalsm = []
        if ylabels is None: ylabels = ['y']

        fig, ax = self.create_figure()
        i = 0
        for yvals in yvalsm:
            ax.plot(xvals, yvals, label=ylabels[i])
            i += 1

        self.set_labels(xlabel=xlabel, ylabel=ylabel, title=title, grid=True)
        if ylabels: self.set_legend(ylabels)
        self.render_done()

    def render_stack(self, xvals: list | None = None, yvalsm: list | None = None,
                     xlabel='x', ylabels: list | None = None, ylabel='y', title='Stack Plot'):
        """Render a stack plot."""
        if xvals is None: xvals = []
        if yvalsm is None: yvalsm = []

        fig, ax = self.create_figure()
        ax.stackplot(xvals, yvalsm, labels=ylabels, colors=self.get_colors(len(yvalsm)))
        self.set_labels(xlabel=xlabel, ylabel=ylabel, title=title)
        if ylabels: self.set_legend(ylabels)
        self.render_done()

    def render_bars(self, xvals: list | None = None, yvalsm: list | None = None,
                    xlabel='x', ylabels: list | None = None, ylabel='y', title='Bar Chart', vertical=True):
        """Render a bar chart."""
        if xvals is None: xvals = []
        if yvalsm is None: yvalsm = []

        fig, ax = self.create_figure()
        n_series = len(yvalsm)
        width = 0.8 / n_series
        colors = self.get_colors(n_series)

        if vertical:
            x = np.arange(len(xvals))
            for i, values in enumerate(yvalsm):
                offset = (i - (n_series - 1) / 2) * width
                ax.bar(x + offset, values, width=width, color=colors[i],
                       label=ylabels[i] if ylabels else None)

            ax.set_xticks(x)
            ax.set_xticklabels(xvals)
            self.set_labels(xlabel=xlabel, ylabel=ylabel, title=title)

        else:
            y = np.arange(len(xvals))
            for i, values in enumerate(yvalsm):
                offset = (i - (n_series - 1) / 2) * width
                ax.barh(y + offset, values, height=width, color=colors[i],
                        label=ylabels[i] if ylabels else None)

            ax.set_yticks(y)
            ax.set_yticklabels(xvals)
            self.set_labels(xlabel=ylabel, ylabel=xlabel, title=title)

        if ylabels: ax.legend()
        self.render_done()

    def render_bar(self, labels, vals, label='y', title='Bar Chart', vertical=True):
        """Render a bar chart."""
        fig, ax = self.create_figure()
        colors = self.get_colors(len(labels))
        if vertical:
            ax.bar(labels, vals, color=colors)
            self.set_labels(ylabel=label, title=title)
        else:
            ax.barh(labels, vals, color=colors)
            self.set_labels(xlabel=label, title=title)

        self.render_done()

    def render_scatter(self, xvals, yvals, names, xlabel='x', ylabel='y', title='y vs x'):
        """Render a scatter plot."""
        fig, ax = self.create_figure()
        ax.scatter(xvals, yvals, color='red')
        for i, name in enumerate(names):
            ax.text(xvals[i], yvals[i], name, fontsize=10, ha='left', va='top', color='black')
        self.set_labels(xlabel=xlabel, ylabel=ylabel, title=title, grid=True)
        self.render_done()

    def render_pie(self, labels, vals, title='Pie Chart', show_pct=True, shadow=False, radius=1.0,
                   show_labels=True, legend='none', labels_include=None):
        """Render a pie chart."""
        if labels_include is None:
            labels_include = ['label']
        fig, ax = self.create_figure()
        colors = self.get_colors(len(labels))
        autopct = '%1.2f%%' if show_pct else ''
        composed_labels = []
        for i in range(len(labels)):
            composed_labels.append(
                joinx((labels[i] if 'label' in labels_include else '',
                       '{:.2f}'.format(vals[i]) if 'value' in labels_include else ''), ', '))

        wedges, _, _ = ax.pie(vals, labels=composed_labels, autopct=autopct, colors=colors, shadow=shadow,
                              radius=radius, labeldistance=1.1 if show_labels else None)
        self.set_labels(title=title)
        self.set_legend(labels=labels, loc=legend)
        self.render_done()

    def render_pareto(self, x, y, ylabel='Count', title='Pareto Chart'):
        """Render a Pareto chart."""
        # | https://tylermarrs.com/posts/pareto-plot-with-matplotlib/
        fig, ax = self.create_figure()
        colors = self.get_colors(len(x))
        df = pd.DataFrame({'x': x, 'y': y}).sort_values(by='y', ascending=False)
        x = df["x"].values
        y = df["y"].values
        ax.bar(df["x"], df['y'], color=colors)
        self.set_labels(ylabel=ylabel, title=title)

        # Overlay cumulative percentage line
        ax2 = ax.twinx()
        weights = y / y.sum()
        cumsum = weights.cumsum() * 100
        ax2.plot(x, cumsum, '-ro', alpha=0.5)
        ax2.set_ylabel('', color='r')
        ax2.tick_params('y', colors='r')
        self.render_done()

    def render_histogram(self, values, bin_count, density=True, xlabel='Values', ylabel='Frequeency',
                         title='Histogram'):
        """Render a Histogram."""
        fig, ax = self.create_figure()
        mu = fmean(values)
        sigma = stdev(values)
        n, bins, patches = ax.hist(values, bin_count, density=density)  # , color='green'
        if density:
            y = ((1 / (np.sqrt(2 * np.pi) * sigma)) *
                 np.exp(-0.5 * (1 / sigma * (bins - mu)) ** 2))
            ax.plot(bins, y, '--')

        self.set_labels(xlabel=xlabel, ylabel=ylabel, title=title + fr', $\mu={mu:.2f}$, $\sigma={sigma:.2f}$')
        self.render_done()

    def render_network(self, node_df: pd.DataFrame, edge_df: pd.DataFrame,
                       title: str = 'Network Diagram', edge_label=True):
        """Render a network diagram."""
        _, _ = self.create_figure()
        G = nx.Graph()

        node_cols = node_df.columns
        for index, row in node_df.iterrows():
            G.add_node(row[node_cols[0]], pos=(float(row[node_cols[1]]), float(row[node_cols[2]])))

        edge_cols = edge_df.columns
        for index, row in edge_df.iterrows():
            G.add_edge(row[edge_cols[1]], row[edge_cols[2]], edge_id=row[edge_cols[0]])

        # Get node positions from the graph
        node_positions = {node: pos['pos'] for node, pos in G.nodes(data=True)}

        # Draw nodes and edges
        nx.draw(G, pos=node_positions, with_labels=True, font_size=8, font_color='white', font_weight='bold')
        nx.draw_networkx_nodes(G, pos=node_positions, node_size=500)
        nx.draw_networkx_edges(G, pos=node_positions, arrowsize=16, arrows=True, arrowstyle='->')

        # Draw edge labels
        if edge_label:
            edge_labels = {(node1, node2): edge_id for (node1, node2, edge_id) in G.edges(data='edge_id')}
            nx.draw_networkx_edge_labels(G, pos=node_positions, edge_labels=edge_labels)

        self.set_labels(title=title)
        self.render_done()

    def get_colors(self, n):
        """Get a list of colors from the current color scheme."""
        cmap = mpl.colormaps[self.color_scheme]
        colors = cmap(np.linspace(0, 1, n))
        return colors

    def render_heatmap(self, data, x_labels=None, y_labels=None, title='Heatmap'):
        """Render a heatmap."""
        fig, ax = self.create_figure()
        cax = ax.imshow(data, cmap=self.color_scheme, interpolation='nearest')

        # Add color bar
        fig.colorbar(cax)

        # Set labels and title
        ax.set_xlabel('X-axis' if x_labels is None else x_labels)
        ax.set_ylabel('Y-axis' if y_labels is None else y_labels)
        self.set_labels(title=title)
        return self.render_done()

    def render_box(self, data2d, labels=None, title='Boxplot'):
        """Render a boxplot."""
        fig, ax = self.create_figure()
        ax.boxplot(data2d, labels=labels)
        self.set_labels(title=title)
        self.render_done()

    def render_violinplot(self, data2d, labels=None, title='Violin Plot'):
        """Render a violin plot."""
        fig, ax = self.create_figure()
        ax.violinplot(data2d, showmeans=False, showmedians=True)
        if labels:
            ax.set_xticks(range(1, len(labels) + 1))
            ax.set_xticklabels(labels)
        self.set_labels(title=title)
        self.render_done()

    def render_scatter3d(self, xvals, yvals, zvals, xlabel='x', ylabel='y', zlabel='z', title='3D Scatter'):
        """Render a 3D scatter plot."""
        fig, ax = self.create_figure('3d')
        ax.scatter(xvals, yvals, zvals, c='r', marker='o')
        self.set_labels(xlabel, ylabel, zlabel, title)
        self.render_done()

    def render_radar(self, values, labels, title='Radar Chart'):
        """Render a radar chart."""
        fig, ax = self.create_figure()
        num_vars = len(labels)

        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]

        ax.fill(angles, values, color='red', alpha=0.25)
        ax.plot(angles, values, color='red', linewidth=2)
        ax.set_yticklabels([])
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels)

        self.set_labels(title=title)
        self.render_done()

    def render_contour3d(self, xvals, yvals, zvals, xlabel='x', ylabel='y', zlabel='z', title='3D Contour'):
        """Render a 3D contour plot."""
        xvals_ = np.array(xvals, dtype=self.dtype_x)
        yvals_ = np.array(yvals, dtype=float)
        zvals_ = np.array(zvals, dtype=float)
        fig, ax = self.create_figure('3d')
        X, Y = np.meshgrid(xvals_, yvals_)
        ax.contour3D(X, Y, zvals_, 50, cmap=self.color_scheme)
        self.set_labels(xlabel, ylabel, zlabel, title)
        self.render_done()

    def render_errorbar(self, xvals, yvals, yerr, xlabel='x', ylabel='y', title='Error Bar Chart'):
        """Render a line chart with error bars."""
        fig, ax = self.create_figure()
        ax.errorbar(xvals, yvals, yerr=yerr, fmt='-o', color='blue')
        self.set_labels(xlabel=xlabel, ylabel=ylabel, title=title, grid=True)
        self.render_done()

    def render_qqplot(self, data, title='QQ Plot'):
        """Render a QQ plot."""
        fig, ax = self.create_figure()
        from scipy import stats
        stats.probplot(data, dist="norm", plot=ax)
        self.set_labels(title=title)
        self.render_done()

    def render_gantt(self, tasks, start_dates, end_dates, title='Gantt Chart'):
        """Render a Gantt chart."""
        fig, ax = self.create_figure()
        for task, start, end in zip(tasks, start_dates, end_dates):
            ax.barh(task, end - start, left=start)
        self.set_labels(title=title, grid=True)
        self.render_done()

    def render_surface_contour3d(self, xvals, yvals, zvals2d, xlabel='x', ylabel='y', zlabel='z',
                                 title='3D Surface Contour'):
        """Render a 3D surface plot with contour projections."""
        X, Y = np.meshgrid(np.array(xvals, dtype=self.dtype_x), np.array(yvals, dtype=float))
        Z = np.array(zvals2d, dtype=float)

        fig, ax = self.create_figure('3d')
        surf = ax.plot_surface(X, Y, Z, cmap=self.color_scheme, alpha=0.6)
        _ = ax.contour3D(X, Y, Z, 50, cmap=self.color_scheme, linewidths=0.5)
        fig.colorbar(surf, ax=ax)
        self.set_labels(xlabel=xlabel, ylabel=ylabel, zlabel=zlabel, title=title)
        self.render_done()

    def render_mesh3d(self, xvals, yvals, zvals2d, xlabel='x', ylabel='y', zlabel='z', title='3D Mesh Plot'):
        """Render a 3D mesh plot."""
        X, Y = np.meshgrid(np.array(xvals, dtype=self.dtype_x), np.array(yvals, dtype=float))
        Z = np.array(zvals2d, dtype=float)

        fig, ax = self.create_figure('3d')
        ax.plot_wireframe(X, Y, Z, cmap=self.color_scheme)
        self.set_labels(xlabel=xlabel, ylabel=ylabel, zlabel=zlabel, title=title)
        self.render_done()

    def render_sankey(self, flows, labels, orientations=None, title='Sankey Diagram'):
        """Render a Sankey diagram."""
        fig, ax = self.create_figure()
        from matplotlib.sankey import Sankey
        if orientations is None:
            orientations = [0] * len(labels)
        sankey = Sankey(ax=ax, unit=None)
        sankey.add(flows=flows, labels=labels, orientations=orientations)
        sankey.finish()
        self.set_labels(title=title)
        self.render_done()

    def render_dendrogram(self, linkage_matrix, xlabel, ylabel, title='Dendrogram'):
        """Render a dendrogram."""
        from scipy.cluster.hierarchy import dendrogram
        fig, ax = self.create_figure()
        dendrogram(np.array(linkage_matrix, dtype=float), ax=ax)
        self.set_labels(xlabel=xlabel, ylabel=ylabel, title=title)
        self.render_done()

    def render_surface3d_error(self, xvals, yvals, zvals2d, zerror, xlabel='x', ylabel='y', zlabel='z',
                               title='3D Surface with Error', surface_type='Surface'):
        """Render a 3D surface plot with error bars."""
        X, Y = np.meshgrid(np.array(xvals), np.array(yvals))
        Z = np.array(zvals2d)
        Z_error = np.array(zerror)

        fig, ax = self.create_figure(projection='3d')

        if surface_type == 'Contour':
            ax.contour(X, Y, Z, cmap=self.color_scheme, antialiased=False)
        elif surface_type == 'Contourf':
            ax.contourf(X, Y, Z, cmap=self.color_scheme, antialiased=False)
        elif surface_type == 'Wireframe':
            ax.plot_wireframe(X, Y, Z, rstride=10, cstride=10)
        # elif surface_type == 'Surface':
        else:  # Default to Surface plot type 'Surface'
            ax.plot_surface(X, Y, Z, cmap=self.color_scheme, antialiased=False)
            # _ = ax.plot_surface(X, Y, Z, cmap=self.color_scheme, alpha=0.7)

        ax.errorbar(X.ravel(), Y.ravel(), Z.ravel(), zerr=Z_error.ravel(), fmt='o', color='black', alpha=0.3)
        self.set_labels(xlabel=xlabel, ylabel=ylabel, zlabel=zlabel, title=title)
        self.render_done()

    def render_bubble_chart(self, xvals, yvals, sizes, xlabel='x', ylabel='y', title='Bubble Chart'):
        """Render a bubble chart."""
        fig, ax = self.create_figure()
        scatter = ax.scatter(xvals, yvals, s=sizes, alpha=0.5, c=sizes, cmap='viridis', edgecolors='w')
        self.set_labels(xlabel=xlabel, ylabel=ylabel, title=title)
        fig.colorbar(scatter, ax=ax, label='Bubble Size')
        self.render_done()

    def render_polar_chart(self, radii, theta, xlabel='Theta', ylabel='Radius', title='Polar Chart'):
        """Render a polar chart."""
        fig, ax = self.create_figure()
        ax = fig.add_subplot(111, polar=True)
        ax.plot(theta, radii, marker='o')
        self.set_labels(xlabel=xlabel, ylabel=ylabel, title=title)
        self.render_done()

    def render_area_chart(self, xvals, yvals, xlabel='x', ylabel='y', title='Area Chart'):
        """Render an area chart."""
        fig, ax = self.create_figure()
        ax.fill_between(xvals, yvals, color='blue', alpha=0.5)
        ax.plot(xvals, yvals, color='blue', linewidth=2)
        self.set_labels(xlabel=xlabel, ylabel=ylabel, title=title)
        self.render_done()

    def render_waterfall_chart(self, xvals, yvals, labels=None, xlabel='x', ylabel='y', title='Waterfall Chart'):
        """Render a waterfall chart."""
        fig, ax = self.create_figure()

        # Ensure yvals is a numeric list
        yvals = np.array(yvals, dtype=float)

        # Calculate cumulative values for the waterfall effect
        cumulative = np.cumsum(yvals)
        starts = np.hstack(([0], cumulative[:-1]))  # Previous cumulative values
        changes = yvals

        ax.bar(xvals, changes, bottom=starts, color=['green' if change >= 0 else 'red' for change in changes])
        self.set_labels(xlabel=xlabel, ylabel=ylabel, title=title, grid=True)

        if labels:
            for i, label in enumerate(labels):
                ax.text(xvals[i], starts[i] + changes[i] / 2, label, ha='center', va='center')

        self.render_done()

    def render_chord_diagram(self, matrix, labels, title='Chord Diagram'):
        """Render a chord diagram based on the matrix of connections."""
        from matplotlib.patches import FancyArrowPatch
        from math import sin, cos

        fig, ax = self.create_figure()

        # Normalize matrix and labels
        matrix = np.array(matrix, dtype=float)
        n = len(labels)

        # Create angles for labels around a circle
        angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
        angles += angles[:1]

        # Draw labels around the circle
        radius = 1.5
        for i, (angle, label) in enumerate(zip(angles[:-1], labels)):
            x = radius * cos(angle)
            y = radius * sin(angle)
            ax.text(x, y, label, ha='center', va='center', fontsize=12)

        # Draw arcs representing the connections based on the matrix
        for i in range(n):
            for j in range(i + 1, n):
                if matrix[i, j] > 0:
                    # Draw an arrow for each connection in the matrix
                    start_angle = angles[i]
                    end_angle = angles[j]
                    start = (radius * cos(start_angle), radius * sin(start_angle))
                    end = (radius * cos(end_angle), radius * sin(end_angle))
                    arrow = FancyArrowPatch(start, end, connectionstyle="arc3,rad=.5", color='blue', lw=matrix[i, j])
                    ax.add_patch(arrow)

        self.set_labels(title=title)
        ax.set_xlim([-2, 2])
        ax.set_ylim([-2, 2])
        ax.set_axis_off()
        self.render_done()

    def render_streamgraph(self, xvals, yvalsm, labels=None, xlabel='x', ylabel='y', title='Streamgraph'):
        """Render a streamgraph."""
        fig, ax = self.create_figure()
        ax.stackplot(xvals, yvalsm, labels=labels, baseline='wiggle', colors=self.get_colors(len(yvalsm)))
        self.set_labels(xlabel=xlabel, ylabel=ylabel, title=title)
        if labels: self.set_legend(labels)
        self.render_done()
