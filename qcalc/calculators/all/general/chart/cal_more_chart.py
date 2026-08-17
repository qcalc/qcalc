# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import numpy as np
import pandas as pd
from qutil import css2floats, css2strs, css2ints, css2values
from qcore import qtexta, qlist, qchar, qtable, QChart
from calc import QCals
import matplotlib.dates as mdates  # requires for 3D as 3D cant natively handle date axes
from datetime import date, datetime


def heatmap_chart__info():
    return {
        'title': 'Simple Heatmap Chart',
        'schema': {
            'color_scheme': {'type': 'choice', 'choices': ['viridis', 'plasma', 'inferno', 'magma', 'Use Preference']}
        },
        'outcol': ['chart__r']
    }


def heatmap_chart(
    values: qtexta = '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20',
    x_labels: qtexta = 'A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T',
    y_labels: qtexta = '1,2,3,4,5',
    title='Simple Heatmap Chart',
    color_scheme='inferno'
):
    values = css2floats(values)
    x_labels = css2strs(x_labels)
    y_labels = css2strs(y_labels)

    num_values = len(values)
    num_y_labels = len(y_labels)

    # Check if the number of values can be reshaped into a matrix with the given number of y_labels
    if num_values % num_y_labels != 0:
        raise ValueError(f"Cannot reshape {num_values} values into a matrix with {num_y_labels} rows")

    num_x_labels = num_values // num_y_labels

    # Reshape the values into a 2D array
    heatmap_data = np.reshape(values, (num_y_labels, num_x_labels))

    chart = QChart(color_scheme=color_scheme if color_scheme != 'Use Preference' else None)
    chart.render_heatmap(data=heatmap_data, x_labels=x_labels, y_labels=y_labels, title=title)
    return {'chart': chart}


def surface3d_error_chart__info():
    return {
        'title': '3D Surface Chart with Error',
        'schema': {
            'surface_type': {'type': 'radio', 'choices': ['Contour', 'Contourf', 'Wireframe', 'Surface']}
        },
        'outcol': ['chart__r']
    }


def surface3d_error_chart(
    x_values: qtexta = '10, 11, 12, 13, 14, 15, 16, 17, 18, 19',
    y_values: qtexta = '2, 1, 4, 5, 8, 12, 18, 25, 96, 48',
    z_expr: qtexta = 'x**2 + y**3',
    error_values: qtexta = '0.1, 0.2, 0.1, 0.3, 0.2, 0.2, 0.1, 0.2, 0.1, 0.3',
    x_label='x',
    y_label='y',
    z_label='z',
    title='3D Surface Chart with Error',
    surface_type='Surface'
):
    xnums, xtype = css2values(x_values, time2val='hr')
    if xtype in (date, datetime): xnums = mdates.date2num(xnums)
    ynums = css2floats(y_values)
    errors = css2floats(error_values)

    def zfunc(x, y):
        return QCals.safe_eval(z_expr, ldict={'x': x, 'y': y})

    znums = []
    for x in xnums:
        zs = []
        for y in ynums:
            zs.append(zfunc(x, y))
        znums.append(zs)

    # Create a grid with errors
    error_grid = np.array([errors] * len(ynums))

    chart = QChart(xtype=xtype)
    chart.render_surface3d_error(
        xvals=xnums, yvals=ynums, zvals2d=znums, zerror=error_grid,
        xlabel=x_label, ylabel=y_label, zlabel=z_label, title=title,
        surface_type=surface_type
    )
    return {'chart': chart}


def surface_contour3d_chart__info():
    return {
        'title': '3D Surface Contour Chart',
        'outcol': ['chart__r']
    }


def surface_contour3d_chart(
    xvals: qtexta = '1, 2, 3, 4, 5',
    yvals: qtexta = '1, 2, 3, 4',
    zvals2d: qtable = pd.DataFrame([
        [1, 2, 3, 4, 5],
        [6, 7, 8, 9, 10],
        [11, 12, 13, 14, 15],
        [16, 17, 18, 19, 20]
    ]),
    xlabel='X-Axis',
    ylabel='Y-Axis',
    zlabel='Z-Axis',
    title='3D Surface Contour Chart'
):
    xvals_, xtype = css2values(xvals, time2val='hr')
    if xtype in (date, datetime): xvals_ = mdates.date2num(xvals_)
    yvals_ = css2floats(yvals)
    zvals2d_ = zvals2d.to_numpy()

    # Check if dimensions of zvals2d match the length of xvals and yvals
    row, col = zvals2d_.shape
    if len(xvals_) != col or len(yvals_) != row:
        raise ValueError("The shape of zvals2d does not match xvals and yvals dimensions")

    chart = QChart(xtype=xtype)
    chart.render_surface_contour3d(
        xvals=xvals_, yvals=yvals_, zvals2d=zvals2d_,
        xlabel=xlabel, ylabel=ylabel, zlabel=zlabel, title=title
    )

    return {'chart': chart}


def box_chart__info():
    return {
        'title': 'Simple Box Chart',
        'outcol': ['chart__r']
    }


def box_chart(
    values: qlist[qchar] = ['2,5,7,8,9,10,12,15,18,20'],
    labels: qtexta = '',
    title='Simple Box Chart'
):
    values_ = []
    for value in values:
        values_.append(css2floats(value))
    labels_ = css2strs(labels) if labels else [f'Group {i + 1}' for i in range(len(values_))]
    chart = QChart(xtype=str)
    chart.render_box(data2d=values_, labels=labels_, title=title)
    return {'chart': chart}


def violin_chart__info():
    return {
        'title': 'Simple Violin Chart',
        'outcol': ['chart__r']
    }


def violin_chart(
    values: qlist[qchar] = ['2,5,7,8,9,10,12,15,18,20'],
    labels: qtexta = '',
    title='Simple Violin Chart'
):
    values_ = []
    for value in values:
        values_.append(css2floats(value))

    # Generate default labels if none provided
    labels_ = css2strs(labels) if labels else [f'Group {i + 1}' for i in range(len(values_))]

    chart = QChart(xtype=str)
    chart.render_violinplot(data2d=values_, labels=labels_, title=title)
    return {'chart': chart}


def radar_chart__info():
    return {
        'title': 'Simple Radar Chart',
        'outcol': ['chart__r']
    }


def radar_chart(
    values: qlist[qchar] = ['2,5,7,8,9'],
    labels: qtexta = 'M1,M2,M3,M4,M5',
    title='Simple Radar Chart'
):
    values_ = css2floats(values[0])

    # Convert the labels into a list
    labels_ = css2strs(labels)

    if len(values_) != len(labels_):
        raise ValueError("Number of values must match the number of labels")

    chart = QChart(xtype=str)
    chart.render_radar(values=values_, labels=labels_, title=title)
    return {'chart': chart}


def scatter3d_chart__info():
    return {
        'title': '3D Scatter Chart',
        'outcol': ['chart__r']
    }


def scatter3d_chart(
    xvals: qtexta = '1,2,3,4,5',
    yvals: qtexta = '5,6,7,8,9',
    zvals: qtexta = '9,8,7,6,5',
    xlabel='X-Axis',
    ylabel='Y-Axis',
    zlabel='Z-Axis',
    title='3D Scatter Chart'
):
    xvals_, xtype = css2values(xvals, time2val='hr')
    if xtype in (date, datetime): xvals_ = mdates.date2num(xvals_)
    yvals_ = css2floats(yvals)
    zvals_ = css2floats(zvals)

    # Ensure all value lists are the same length
    if not (len(xvals_) == len(yvals_) == len(zvals_)):
        raise ValueError("X, Y, and Z values must have the same length")

    chart = QChart(xtype=xtype)
    chart.render_scatter3d(
        xvals=xvals_, yvals=yvals_, zvals=zvals_,
        xlabel=xlabel, ylabel=ylabel, zlabel=zlabel, title=title
    )
    return {'chart': chart}


def stack_chart__info():
    return {
        'title': 'Simple Stack Chart',
        'outcol': ['chart__r']
    }


def stack_chart(
    xvals: qtexta = '1,2,3,4,5',
    yvals: qlist[qchar] = ['1,2,3,4,5', '2,3,4,5,6'],
    labels: qtexta = 'Series 1,Series 2',
    xlabel='X-Axis',
    ylabel='Y-Axis',
    title='Simple Stack Chart'
):
    # xvals_ = css2floats(xvals)
    xvals_, xtype = css2values(xvals, time2val='hr')
    yvals_ = [css2floats(yval) for yval in yvals]
    labels_ = css2strs(labels) if labels else None

    # Ensure all yvals_list arrays have the same length as xvals
    for yval in yvals_:
        if len(yval) != len(xvals_):
            raise ValueError("All y-values must have the same length as x-values")

    chart = QChart(xtype=xtype)
    chart.render_stack(
        xvals=xvals_, yvals2d=yvals_, labels=labels_,
        xlabel=xlabel, ylabel=ylabel, title=title
    )
    return {'chart': chart}


def contour3d_chart__info():
    return {
        'title': '3D Contour Chart',
        'outcol': ['chart__r']
    }


def contour3d_chart(
    xvals: qtexta = '1,2,3,4,5',
    yvals: qtexta = '1,2,3,4',
    zvals: qtable = pd.DataFrame([[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12, 13, 14, 15], [16, 17, 18, 19, 20]]),
    xlabel='X-Axis',
    ylabel='Y-Axis',
    zlabel='Z-Axis',
    title='3D Contour Chart'
):
    xvals_, xtype = css2values(xvals, time2val='hr')
    if xtype in (date, datetime): xvals_ = mdates.date2num(xvals_)
    yvals_ = css2floats(yvals)
    zvals_ = zvals.to_numpy()
    row, col = zvals.shape

    # Ensure that zvals can be reshaped into a grid
    if len(xvals_) != col or len(yvals_) != row:
        raise ValueError("Length of xvals and yvals must be equal to number of columns and rows of zvals")

    chart = QChart(xtype=xtype)
    chart.render_contour3d(
        xvals=xvals_, yvals=yvals_, zvals=zvals_,
        xlabel=xlabel, ylabel=ylabel, zlabel=zlabel, title=title
    )
    return {'chart': chart}


def errorbar_chart__info():
    return {
        'title': 'Error Bar Chart',
        'outcol': ['chart__r']
    }


def errorbar_chart(
    xvals: qtexta = '1,2,3,4,5',
    yvals: qtexta = '2.1,2.5,3.2,3.8,4.0',
    yerr: qtexta = '0.1,0.2,0.1,0.3,0.2',
    xlabel='X-Axis',
    ylabel='Y-Axis',
    title='Error Bar Chart'
):
    xvals_, xtype = css2values(xvals, time2val='hr')
    yvals_ = css2floats(yvals)
    yerr_ = css2floats(yerr)

    # Ensure lengths of xvals, yvals, and yerr are consistent
    if len(xvals_) != len(yvals_) or len(yvals_) != len(yerr_):
        raise ValueError("xvals, yvals, and yerr must have the same length")

    # Render the chart
    chart = QChart(xtype=xtype)
    chart.render_errorbar(xvals=xvals_, yvals=yvals_, yerr=yerr_, xlabel=xlabel, ylabel=ylabel, title=title)

    return {'chart': chart}


def qqplot_chart__info():
    return {
        'title': 'QQ Plot',
        'outcol': ['chart__r']
    }


def qqplot_chart(
    data: qtexta = '2.1, 2.5, 3.2, 3.8, 4.0, 4.5, 5.1, 5.6, 6.0',
    title='QQ Plot'
):
    # Convert input data to floats
    data_ = css2floats(data)

    # Render the QQ plot
    chart = QChart()
    chart.render_qqplot(data=data_, title=title)

    return {'chart': chart}


def gantt_chart__info():
    return {
        'title': 'Gantt Chart',
        'outcol': ['chart__r']
    }


def gantt_chart(
    project: qtable = pd.DataFrame(
        {
            'Task': ['Task 1', 'Task 2', 'Task 3', 'Task 4', 'Task 5'],
            'Start Date': ['2024-01-01', '2024-01-10', '2024-01-28', '2024-02-10', '2024-02-25'],
            'End Date': ['2024-01-12', '2024-02-05', '2024-02-20', '2024-02-19', '2024-02-28'],
        }
    ),
    title='Gantt Chart'
):
    # Extract columns from the DataFrame
    tasks_ = project['Task'].tolist()

    # Convert ISO date strings to datetime objects
    start_dates_ = pd.to_datetime(project['Start Date']).tolist()
    end_dates_ = pd.to_datetime(project['End Date']).tolist()

    # Render the Gantt chart
    chart = QChart(xtype=datetime)
    chart.render_gantt(tasks=tasks_, start_dates=start_dates_, end_dates=end_dates_, title=title)

    return {'chart': chart}


def mesh3d_chart__info():
    return {
        'title': '3D Mesh Plot',
        'outcol': ['chart__r']
    }


def mesh3d_chart(
    xvals: qtexta = '1, 2, 3, 4, 5',
    yvals: qtexta = '1, 2, 3, 4',
    zvals2d: qtable = pd.DataFrame([
        [1, 2, 3, 4, 5],
        [6, 7, 8, 9, 10],
        [11, 12, 13, 14, 15],
        [16, 17, 18, 19, 20]
    ]),
    xlabel='X-Axis',
    ylabel='Y-Axis',
    zlabel='Z-Axis',
    title='3D Mesh Plot'
):
    # xvals_ = css2floats(xvals)
    xvals_, xtype = css2values(xvals, time2val='hr')
    if xtype in (date, datetime): xvals_ = mdates.date2num(xvals_)
    yvals_ = css2floats(yvals)
    zvals2d_ = zvals2d.to_numpy()

    # Ensure the dimensions of zvals2d match the lengths of xvals and yvals
    row, col = zvals2d_.shape
    if len(xvals_) != col or len(yvals_) != row:
        raise ValueError("The shape of zvals2d does not match the dimensions of xvals and yvals")

    chart = QChart(xtype=xtype)
    chart.render_mesh3d(
        xvals=xvals_, yvals=yvals_, zvals2d=zvals2d_,
        xlabel=xlabel, ylabel=ylabel, zlabel=zlabel, title=title
    )

    return {'chart': chart}


def sankey_chart__info():
    return {
        'title': 'Sankey Diagram',
        'outcol': ['chart__r']
    }


def sankey_chart(
    flows: qtexta = '-15, 15, 10, 12, -10, 5',
    labels: qtexta = 'Input, Process 1, Process 2, Process3, Output 1, Output 2',
    orientations: qtexta = '-1, 1, 1, -1, 1, 0',
    title='Sankey Diagram'
):
    # Convert the input strings to lists
    flows_ = css2floats(flows)
    labels_ = css2strs(labels)
    orientations_ = css2ints(orientations) if orientations else [0] * len(labels_)

    # Ensure that flows and labels match in length
    if len(flows_) != len(labels_):
        raise ValueError("The number of flows must match the number of labels")

    chart = QChart()
    chart.render_sankey(
        flows=flows_,
        labels=labels_,
        orientations=orientations_,
        title=title
    )

    return {'chart': chart}


def dendrogram_chart__info():
    return {
        'title': 'Dendrogram Chart',
        'outcol': ['chart__r'],
        'schema': {
            'method':
                {
                    'type': 'choice',
                    'choices': ['single', 'complete', 'average', 'centroid', 'ward'],
                },
        }
    }


def dendrogram_chart(
    data: qtable = pd.DataFrame([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]]),
    method='ward',
    xlabel: str = 'X-Axis',
    ylabel: str = 'Y-Axis',
    title: str = 'Dendrogram Chart'
):
    from scipy.cluster.hierarchy import linkage
    # Generate the linkage matrix using the selected method
    linkage_matrix = linkage(np.array(data, dtype=float), method=method)

    # Render the dendrogram chart
    chart = QChart()
    chart.render_dendrogram(linkage_matrix=linkage_matrix, xlabel=xlabel, ylabel=ylabel, title=title)
    return {'chart': chart}


def bubble_chart__info():
    return {
        'title': 'Bubble Chart',
        'outcol': ['chart__r']
    }


def bubble_chart(
    xvals: qtexta = '1,2,3,4,5',
    yvals: qtexta = '5,4,3,2,1',
    sizes: qtexta = '100,200,300,400,500',
    xlabel='X-Axis',
    ylabel='Y-Axis',
    title='Bubble Chart'
):
    # xvals_ = css2floats(xvals)
    xvals_, xtype = css2values(xvals, time2val='hr')
    yvals_ = css2floats(yvals)
    sizes_ = css2floats(sizes)

    chart = QChart(xtype=xtype)
    chart.render_bubble_chart(xvals=xvals_, yvals=yvals_, sizes=sizes_, xlabel=xlabel, ylabel=ylabel, title=title)
    return {'chart': chart}


def polar_chart__info():
    return {
        'title': 'Polar Chart',
        'outcol': ['chart__r']
    }


def polar_chart(
    radii: qtexta = '1,2,3,4,5',
    theta: qtexta = '0,0.5,1,1.5,2',
    xlabel='Theta',
    ylabel='Radius',
    title='Polar Chart'
):
    radii_ = css2floats(radii)
    theta_ = css2floats(theta)

    chart = QChart()
    chart.render_polar_chart(radii=radii_, theta=theta_, xlabel=xlabel, ylabel=ylabel, title=title)
    return {'chart': chart}


def area_chart__info():
    return {
        'title': 'Area Chart',
        'outcol': ['chart__r']
    }


def area_chart(
    xvals: qtexta = '1,2,3,4,5,6,7',
    yvals: qtexta = '2,3,4,5,6,3,4',
    xlabel='X-Axis',
    ylabel='Y-Axis',
    title='Area Chart Example'
):
    # xvals_ = css2floats(xvals)
    xvals_, xtype = css2values(xvals, time2val='hr')
    yvals_ = css2floats(yvals)
    chart = QChart(xtype=xtype)
    chart.render_area_chart(xvals=xvals_, yvals=yvals_, xlabel=xlabel, ylabel=ylabel, title=title)
    return {'chart': chart}


def waterfall_chart__info():
    return {
        'title': 'Waterfall Chart',
        'outcol': ['chart__r'],
    }


def waterfall_chart(
    xvals: qtexta = 'Q1,Q2,Q3,Q4',
    yvals: qtexta = '100,-20,30,-10',
    labels: qtexta = 'Profit,Loss,Profit,Loss',
    xlabel='Quarters',
    ylabel='Net Change',
    title='Waterfall Chart Example'
):
    # Convert comma-separated string inputs to lists
    xvals_ = css2strs(xvals)
    yvals_ = css2floats(yvals)
    labels_ = css2strs(labels)

    # Initialize chart object and render the waterfall chart
    chart = QChart(xtype=str)
    chart.render_waterfall_chart(xvals=xvals_, yvals=yvals_, labels=labels_, xlabel=xlabel, ylabel=ylabel, title=title)

    return {'chart': chart}


def chord_diagram__info():
    return {
        'title': 'Chord Diagram',
        'outcol': ['chart__r'],
    }


def chord_diagram(
    matrix: qtable = pd.DataFrame([[0, 1, 2], [1, 0, 3], [2, 3, 0]]),
    labels: qtexta = 'A,B,C',
    title='Chord Diagram Example'
):
    labels_ = css2strs(labels)
    chart = QChart()
    chart.render_chord_diagram(matrix=matrix, labels=labels_, title=title)
    return {'chart': chart}


def streamgraph__info():
    return {
        'title': 'Streamgraph',
        'outcol': ['chart__r'],
    }


def streamgraph(
    xvals: qtexta = '1,2,3,4,5',
    yvals: qtable = pd.DataFrame([[2, 3, 4, 5, 6], [1, 2, 3, 4, 5]]),
    labels: qtexta = 'Stream 1,Stream 2',
    xlabel='X-Axis',
    ylabel='Y-Axis',
    title='Streamgraph Example'
):
    xvals_, xtype = css2values(xvals, time2val='hr')
    yvals_ = yvals.to_numpy(dtype=float)
    labels_ = css2strs(labels)
    chart = QChart(xtype=xtype)
    chart.render_streamgraph(xvals=xvals_, yvals2d=yvals_, labels=labels_, xlabel=xlabel, ylabel=ylabel, title=title)
    return {'chart': chart}
