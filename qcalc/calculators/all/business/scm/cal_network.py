# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import qtable, qtexta, QScreen, QChart
from qutil import css2strs
import pandas as pd
import pulp
import math


def transport_opt__info():
    return {
        'title': 'Transportation Optimization - Plant to Customer'
    }


def transport_opt(
    supply: qtable = pd.DataFrame({'Plant': ['P1', 'P2'], 'Capacity': [100, 125]}),
    demand: qtable = pd.DataFrame({'Customer': ['C1', 'C2', 'C3'], 'Demand': [25, 95, 80]}),
    cost: qtable = pd.DataFrame({
        'Plant': ['P1', 'P1', 'P1', 'P2', 'P2', 'P2'],
        'Customer': ['C1', 'C2', 'C3', 'C1', 'C2', 'C3'],
        'Cost': [250, 325, 445, 275, 260, 460]}),
):
    plants = supply['Plant']
    customers = demand['Customer']
    links = [f"{row['Plant']}-{row['Customer']}" for index, row in cost.iterrows()]
    solution, x = solve_transport_network(supply, demand, cost)
    labels = [x[p, c].value() for p in plants for c in customers]
    chart = sd_mesh(','.join(plants), ','.join(customers), ','.join(links),
                    edge_label=True, custom_labels=labels)
    return {'Network': chart['chart'], 'Solution': solution}


def transship_opt__info():
    return {
        'title': 'Transshipment Optimization - Plant -> Distribution Center -> Customer'
    }


def transship_opt(
    supply: qtable = pd.DataFrame({'Plant': ['P1', 'P2'], 'Capacity': [100, 125]}),
    distribution: qtable = pd.DataFrame({'DC': ['D1', 'D2']}),  # , 'Capacity': [0, 0]}),
    demand: qtable = pd.DataFrame({'Customer': ['C1', 'C2', 'C3'], 'Demand': [25, 95, 80]}),
    cost: qtable = pd.DataFrame({
        'From': ['P1', 'P1', 'P2', 'P2', 'D1', 'D1', 'D1', 'D2', 'D2', 'D2'],
        'To': ['D1', 'D2', 'D1', 'D2', 'C1', 'C2', 'C3', 'C1', 'C2', 'C3'],
        'Cost': [190, 210, 185, 205, 175, 180, 165, 235, 130, 145]}),
):
    plants = supply['Plant']
    dcs = distribution['DC']
    customers = demand['Customer']
    links = [f"{row['From']}-{row['To']}" for index, row in cost.iterrows()]
    solution, x1, x2 = solve_transshipment_network(supply, distribution, demand, cost)
    labels = [x1[p, d].value() for p in plants for d in dcs] + [x2[d, c].value() for d in dcs for c in customers]
    chart = std_mesh(','.join(plants), ','.join(dcs), ','.join(customers), ','.join(links),
                     edge_label=True, custom_labels=labels)
    return {'Network': chart['chart'], 'Solution': solution}


def solve_transport_network(supply, demand, cost):
    # Extract data from DataFrames
    plants = supply['Plant'].tolist()
    customers = demand['Customer'].tolist()
    capacity = dict(zip(supply['Plant'], supply['Capacity'].astype(float)))
    demand = dict(zip(demand['Customer'], demand['Demand'].astype(float)))
    cost_matrix = {(row['Plant'], row['Customer']): float(row['Cost']) for _, row in cost.iterrows()}

    # Create the LP problem
    prob = pulp.LpProblem("SupplyChainProblem", pulp.LpMinimize)

    # Define decision variables
    x = pulp.LpVariable.dicts("Transport", ((plant, customer) for plant in plants for customer in customers), 0, None,
                              pulp.LpInteger)

    # Objective function: minimize the total transportation cost
    prob += pulp.lpSum(cost_matrix[plant, customer] * x[plant, customer] for plant in plants for customer in customers)

    # Constraints: supply from each plant should not exceed its capacity
    for plant in plants:
        prob += pulp.lpSum(x[plant, customer] for customer in customers) <= capacity[plant]

    # Constraints: meet the demand of each customer
    for customer in customers:
        prob += pulp.lpSum(x[plant, customer] for plant in plants) == demand[customer]

    # Solve the problem
    prob.solve()

    # Display the results
    out = QScreen()
    out.write("Status:", pulp.LpStatus[prob.status])
    out.write("Total Cost:", round(prob.objective.value(), 2))

    for plant in plants:
        for customer in customers:
            if x[plant, customer].value() > 0:
                out.write(f"Transport {x[plant, customer].value()} units from {plant} to {customer}")
    return out.flush(), x


def solve_transshipment_network(supply, distribution, demand, cost):
    # Extract data from DataFrames
    plants = supply['Plant'].tolist()
    dcs = distribution['DC'].tolist()
    customers = demand['Customer'].tolist()
    pl_capacity = dict(zip(supply['Plant'], supply['Capacity'].astype(float)))
    # dc_capacity = dict(zip(distribution['DC'], distribution['Capacity'].astype(float)))
    demand = dict(zip(demand['Customer'], demand['Demand'].astype(float)))
    cost_matrix = {(row['From'], row['To']): float(row['Cost']) for _, row in cost.iterrows()}

    # Create the LP problem
    prob = pulp.LpProblem("SupplyChainProblem", pulp.LpMinimize)
    # Define decision variables
    x1 = pulp.LpVariable.dicts("Transport",
                               ((plant, dc) for plant in plants for dc in dcs), 0, None, pulp.LpInteger)
    x2 = pulp.LpVariable.dicts("Transport",
                               ((dc, customer) for dc in dcs for customer in customers), 0, None, pulp.LpInteger)

    # Objective function: minimize the total transportation cost
    prob += (pulp.lpSum(cost_matrix[plant, dc] * x1[plant, dc]
                        for plant in plants for dc in dcs) +
             pulp.lpSum(cost_matrix[dc, customer] * x2[dc, customer]
                        for dc in dcs for customer in customers))

    # Constraints: supply from each plant should not exceed its capacity
    for plant in plants:
        prob += pulp.lpSum(x1[plant, dc] for dc in dcs) <= pl_capacity[plant]

    for dc in dcs:
        prob += (pulp.lpSum(x1[plant, dc] for plant in plants) - pulp.lpSum(x2[dc, customer] for customer in customers)
                 == 0)

    # Constraints: meet the demand of each customer
    for customer in customers:
        prob += pulp.lpSum(x2[dc, customer] for dc in dcs) == demand[customer]

    # print(prob)
    # Solve the problem
    prob.solve()

    # Display the results
    out = QScreen()
    out.write("Status:", pulp.LpStatus[prob.status])
    out.write("Total Cost:", round(prob.objective.value(), 2))

    for plant in plants:
        for dc in dcs:
            if x1[plant, dc].value() > 0:
                out.write(f"Transport {x1[plant, dc].value()} units from {plant} to {dc}")
    for dc in dcs:
        for customer in customers:
            if x2[dc, customer].value() > 0:
                out.write(f"Transport {x2[dc, customer].value()} units from {dc} to {customer}")
    return out.flush(), x1, x2


def sd_mesh__info():
    return {
        'title': 'Source Destination Mesh'
    }


def create_y(n, h, mode):
    if mode == 'c':  # circular
        return [h / 2 * math.sin(i * 2 / (n - 1) - 1) for i in range(n)] if n > 1 else [0]
    elif mode == 'l':  # linear
        return [h * i / (n - 1) - h / 2 for i in range(n)] if n > 1 else [0]


def create_x(n, w, mode):
    if mode == 'c':  # circular
        return [w * math.cos(i * 2 / (n - 1) - 1) for i in range(n)] if n > 1 else [0]
    elif mode == 'l':  # linear
        return [w] * n


def sd_mesh(sources: qtexta = 'S1, S2', destinations: qtexta = 'D1,D2,D3',
            links: qtexta = 'S1-D1,S1-D2,S1-D3,S2-D1,S2-D3',
            edge_label=False, circular=True, custom_labels: qtexta = ''):
    source_list = css2strs(sources)
    dest_list = css2strs(destinations)
    link_list = css2strs(links)
    labels = css2strs(custom_labels)
    len_s = len(source_list)
    len_d = len(dest_list)
    l_max = max(len_s, len_d)
    mode = 'c' if circular else 'l'
    nodes_y = create_y(len_s, 100 * len_s / l_max, mode) + create_y(len_d, 100 * len_d / l_max, mode)
    nodes_x = create_x(len_s, -50, mode) + create_x(len_d, 50, mode)
    nodes = pd.DataFrame({"Node": source_list + dest_list, "X": nodes_x, "Y": nodes_y})
    edges = []
    edge_from = []
    edge_to = []
    i = 0
    lbl = len(labels)
    for s in source_list:
        for d in dest_list:
            link = f"{s}-{d}"
            if link_list == [''] or link in link_list:
                edges.append(i if lbl == 0 else labels[i] if i < lbl else '')
                edge_from.append(s)
                edge_to.append(d)
            i = i + 1
    edges = pd.DataFrame({"Edge": edges, "From": edge_from, "To": edge_to})
    chart = QChart()
    chart.render_network(
        nodes,
        edges,
        title='Source Destination Mesh',
        edge_label=edge_label
    )
    return {'chart': chart, 'nodes': nodes, 'edges': edges}


def std_mesh__info():
    return {
        'title': 'Source Transit Destination Mesh'
    }


def std_mesh(sources: qtexta = 'S1, S2, S3', transits: qtexta = 'T1,T2',
             destinations: qtexta = 'D1,D2,D3',
             links: qtexta = 'S1-T1,S1-T2,S2-T1,S2-T2,S3-T1,S3-T2,T1-D1,T1-D2,T1-D3,T2-D1,T2-D2,T2-D3',
             edge_label=False, circular=True, custom_labels: qtexta = ''):
    source_list = css2strs(sources)
    transit_list = css2strs(transits)
    dest_list = css2strs(destinations)
    link_list = css2strs(links)
    if isinstance(custom_labels, list):
        labels = custom_labels
    else:
        labels = css2strs(custom_labels)
    len_s = len(source_list)
    len_t = len(transit_list)
    len_d = len(dest_list)
    l_max = max(len_s, len_t, len_d)
    mode = 'c' if circular else 'l'
    nodes_y = (create_y(len_s, 100 * len_s / l_max, mode) + create_y(len_t, 100 * len_t / l_max, mode) +
               create_y(len_d, 100 * len_d / l_max, mode))
    nodes_x = create_x(len_s, -50, mode) + create_x(len_t, 0, mode) + create_x(len_d, 50, mode)
    nodes = pd.DataFrame({"Node": source_list + transit_list + dest_list, "X": nodes_x, "Y": nodes_y})

    edges = []
    edge_from = []
    edge_to = []
    i = 0
    lbl = len(labels)
    for s in source_list:
        for t in transit_list:
            link = f"{s}-{t}"
            if link_list == [''] or link in link_list:
                edges.append(i if lbl == 0 else labels[i] if i < lbl else '')
                edge_from.append(s)
                edge_to.append(t)
            i = i + 1
    for t in transit_list:
        for d in dest_list:
            link = f"{t}-{d}"
            if link_list == [''] or link in link_list:
                edges.append(i if lbl == 0 else labels[i] if i < lbl else '')
                edge_from.append(t)
                edge_to.append(d)
            i = i + 1

    edges = pd.DataFrame({"Edge": edges, "From": edge_from, "To": edge_to})
    chart = QChart()
    chart.render_network(
        nodes,
        edges,
        title='Source Transit Destination Mesh',
        edge_label=edge_label
    )
    return {'chart': chart, 'nodes': nodes, 'edges': edges}


def facility_opt__info():
    return {
        'title': 'Facility Location Optimization - Facility to Customer'
    }


# location: qtable = pd.DataFrame({
#     'Location': ['BO', 'BR', 'CO', 'HA', 'MN', 'NA', 'NH', 'NL', 'PO', 'PR', 'SP', 'WO'],
#     'Demand': [425, 12, 43, 125, 110, 86, 129, 28, 66, 320, 220, 182],
#     'X': [100, 15, 76, 13, 80, 80, 0, 40, 120, 86, 20, 66],
#     'Y': [80, 119, 145, 33, 132, 112, 0, 6, 139, 40, 60, 73]
# }),

def facility_opt(
    cost: qtable = pd.DataFrame({
        'Location': ['BO', 'BR', 'CO', 'HA', 'MN', 'NA', 'NH', 'NL', 'PO', 'PR', 'SP', 'WO'],
        'Demand': [425, 12, 43, 125, 110, 86, 129, 28, 66, 320, 220, 182],
        'BO': [0, 93, 69, 98, 55, 37, 128, 95, 62, 42, 82, 34],
        'NA': [37, 65, 33, 103, 20, 0, 137, 113, 48, 72, 79, 41],
        'PR': [42, 106, 105, 73, 92, 72, 94, 57, 104, 0, 68, 38],
        'SP': [82, 59, 101, 27, 93, 79, 63, 57, 127, 68, 0, 47],
        'WO': [34, 68, 72, 66, 60, 41, 98, 71, 85, 38, 47, 0]
    }),
    facility: qtable = pd.DataFrame({
        'Location': ['BO', 'NA', 'PR', 'SP', 'WO'],
        'Capacity': [2000, 2000, 2000, 2000, 2000],
        'Fixed Cost': [10000, 10000, 10000, 10000, 10000]
    }),
    min_number_of_facilities: int = 1,
    max_number_of_facilities: int = 5,
    max_average_customer_distance: float = None,
    max_average_demand_distance: float = 60,
    min_percent_demand: float = 80,
    demand_within_distance: float = 50
):
    # Define the problem
    prob = pulp.LpProblem("Facility_Location_Problem", pulp.LpMinimize)
    # Decision variables
    facilities = facility['Location'].tolist()
    facilities_check = cost.columns.values[2:].tolist()
    if set(facilities) != set(facilities_check):
        return f'Facility list in [cost] table are not consistent with [facility] table'

    cost_matrix = {(row['Location'], f): float(row[f]) for _, row in cost.iterrows() for f in facilities}
    locations = cost['Location'].tolist()
    possible_facilities = pulp.LpVariable.dicts("Possible_Facility", facilities, 0, 1, pulp.LpBinary)

    possible_flow = pulp.LpVariable.dicts(
        "Possible_Flow", ((l, f) for l in locations for f in facilities),
        0, None, pulp.LpInteger)

    # possible_routes = pulp.LpVariable.dicts(
    #     "Possible_Route", ((l, f) for l in locations for f in facilities),
    #     0, None, pulp.LpInteger)
    # possible_routes = {(l, f): 0 if possible_flow[(l, f)] == 0 else 1 for l in locations for f in facilities}

    # Objective function
    fixed_cost = {f: float(facility.iloc[i]['Fixed Cost']) for i, f in enumerate(facilities)}
    prob += pulp.lpSum(cost_matrix[key] * possible_flow[key] for key in cost_matrix) + pulp.lpSum(
        fixed_cost[f] * possible_facilities[f] for f in facilities)

    # Constraints
    prob += pulp.lpSum(possible_facilities[f] for f in facilities) <= max_number_of_facilities
    prob += pulp.lpSum(possible_facilities[f] for f in facilities) >= min_number_of_facilities

    for i, l in enumerate(locations):
        prob += pulp.lpSum(possible_flow[(l, f)] for f in facilities) == float(cost.iloc[i]['Demand'])

    for i, f in enumerate(facilities):
        prob += pulp.lpSum(possible_flow[(l, f)] for l in locations) <= float(facility.iloc[i]['Capacity'])

    for l in locations:
        for f in facilities:
            prob += possible_flow[(l, f)] - possible_facilities[f] * 999e9 <= 0

    if max_average_customer_distance:
        prob += (pulp.lpSum(cost_matrix[key] * (1 if possible_flow[key] > 0 else 0) for key in possible_flow)
                 <= max_average_customer_distance * pulp.lpSum(
                1 if possible_flow[key] > 0 else 0 for key in possible_flow))

    if max_average_demand_distance:
        prob += (pulp.lpSum(cost_matrix[key] * possible_flow[key] for key in possible_flow)
                 <= max_average_demand_distance * pulp.lpSum(possible_flow[key] for key in possible_flow))

    if min_percent_demand and demand_within_distance:
        total_demand = sum(cost['Demand'].astype(float))
        prob += (pulp.lpSum((1 if cost_matrix[key] <= demand_within_distance else 0) * possible_flow[key]
                            for key in possible_flow) / total_demand) >= min_percent_demand / 100

    # Solve the problem
    prob.solve()

    out = QScreen()
    # Output results
    out.write("Status:", pulp.LpStatus[prob.status])
    out.write("Total Cost:", round(prob.objective.value(), 2))
    for v in prob.variables():
        if v.varValue == 1:
            out.write(v.name, ":", v.varValue)

    # out.print(prob)
    # Get the optimal locations
    # possible_facilities = [f for f in possible_facilities if possible_facilities[f].varValue == 1]

    return out.flush()
