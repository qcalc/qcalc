# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty, qtable, qformat_q, quom2, qhtml, qfunc
import pandas as pd
from qcore import QChart, QTable
from calculators.all.mathematics.geometry.cal_triangle import triangle
import numpy as np
from calculators.all.image_processing.cal_image import image_reader
from PIL import Image
from qutil import demo_url


def irg_landimg__input(_kwargs):
    return {
        'land_image--image_url': demo_url('irg_land.jpg')
    }


def irg_landimg__info():
    return {
        'title': 'Irregular Land Area from Image',
    }


def irg_landimg(land_image: qfunc = image_reader):
    qimg = land_image['image']
    with Image.open(qimg.bio) as img_arr:
        # Convert the image to black and white
        bw_img_arr = img_arr.convert("1")
        # Calculate the area of the land
        area_white = np.sum(bw_img_arr)
        pltarea = img_arr.width * img_arr.height
        area_black = (1 - (area_white / pltarea)) * 100
    return {
        "Image Size": qhtml(f'{img_arr.width}x{img_arr.height} pixel'),
        "Land Area": Qty(area_black, 'pct'),
        "Land Image": qimg,
    }


def irg_land__info():
    return {
        'title': 'Irregular Land Area, Coordinates Known'
    }


def irg_land(coordinates: qtable = pd.DataFrame(
    {
        'Point': ['A', 'B', 'C', 'D', 'E'],
        'X': ['1 ft', '30 ft', '30 ft', '20 ft', '10 ft'],
        'Y': ['0 ft', '0 ft', '40 ft', '50 ft', '20 ft']
    }), result_area_unit: quom2 = 'decimal', result_length_unit: quom2 = 'ft'):
    p = 'Point'
    x = 'X'
    y = 'Y'
    coords = pd.DataFrame({p: coordinates[p], x: coordinates[x].apply(lambda lx: Qty(lx, result_length_unit).val),
                           y: coordinates[y].apply(lambda ly: Qty(ly, result_length_unit).val)})
    n1 = coords[p].tolist()
    n2 = coords[p][1:].tolist() + coords[p][0:1].tolist()
    edges = pd.DataFrame({'Edge': [p1 + p2 for p1, p2 in zip(n1, n2)], 'N1': n1, 'N2': n2})
    chart = QChart()
    chart.render_network(
        coords,
        edges,
        title='Land Shape',
        edge_label=True
    )
    asum = 0.0
    psum = 0.0
    arms = []
    for i in range(len(n1)):
        j = 0 if i == len(n1) - 1 else i + 1
        x1 = coords[x][i]
        y1 = coords[y][i]
        x2 = coords[x][j]
        y2 = coords[y][j]
        asum += x1 * y2 - x2 * y1
        arm = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        psum += arm
        arms.append(arm)

    area = Qty(0.5 * abs(asum), result_length_unit + '^2', result_area_unit)
    perimeter = Qty(psum, result_length_unit)
    edges['Length'] = [Qty(a, result_length_unit) for a in arms]
    edges['Length'] = edges['Length'].apply(qformat_q)
    return {
        'Area': area,
        'Coordinate unit': qhtml(f'{result_length_unit}'),
        'Coordinates': coords,
        'Perimeter': perimeter,
        'Chart': chart,
        'Edges': edges
    }


def irg_land2__info():
    return {
        'title': 'Irregular Land Area by Triangulation'
    }


def irg_land2(triangles: qtable = pd.DataFrame(
    {
        "Triangle": ['ABE', 'BED', 'BDC'],
        "Method": ['2', '1', '3'],
        "Param1": ['70 ft', '62.5 ft', '90 ft'],
        "Param2": ['81 ft', '20 ft', '75 ft'],
        "Param3": ['76 deg', '', '65 ft']
    }), result_area_unit: quom2 = 'decimal', result_length_unit: quom2 = 'ft'):
    # def length_or_angle(la):
    #     if la=='':
    #         return ''
    #     laq = Qty(la)
    #     if laq.unit.dimension=='L':
    #         laq.to(length_unit)
    #     elif laq.unit.dimension=='P':
    #         laq.to('rad')
    #     return laq

    t = 'Triangle'
    m = 'Method'
    p1 = 'Param1'
    p2 = 'Param2'
    p3 = 'Param3'

    def cal_tri(row):
        if row[m] == '2':
            res = triangle(method=row[m], side_a=row[p1], side_b=row[p2], angle=row[p3],
                           result_area_unit=result_area_unit, result_length_unit=result_length_unit)
        elif row[m] == '1':
            ang = row[p3]
            if ang == '':
                ang = '@rad'
            res = triangle(method=row[m], base=row[p1], height=row[p2], angle=ang,
                           result_area_unit=result_area_unit, result_length_unit=result_length_unit)
        elif row[m] == '3':
            res = triangle(method=row[m], side_a=row[p1], side_b=row[p2], side_c=row[p3],
                           result_area_unit=result_area_unit, result_length_unit=result_length_unit)
        else:
            res = {}
        x = row.to_dict()
        x.update(res)
        return x

    arr = []
    for index, row in triangles.iterrows():
        tri = cal_tri(row)
        # print(tri)
        arr.append(tri)

    df = pd.DataFrame(arr)
    area = QTable(df)
    area.format()

    # return {'Area': areaq,
    #         'Side a': aq, 'Side b': bq, 'Side c': cq,
    #         'Angle ab': ang_abq, 'Angle bc': ang_bcq, 'Angle ca': ang_caq}
    return area.df
