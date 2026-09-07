# Source Transit Destination Mesh

## Purpose

This calculator draws a two-stage network diagram connecting **sources** to
**destinations** through an intermediate layer of **transits**, showing
which source-transit and transit-destination pairs are linked. It is useful
for visualizing any network with a routing or hub layer in between — such
as plants, distribution centers, and customers — and, optionally, for
labeling each connection with a value (for example, a shipped quantity or a
cost) to review alongside the network.

## Background

### How the mesh is built

The network has two stages of candidate connections: every possible
source-transit pair, and every possible transit-destination pair. The
**Links** input selects which of those candidate connections are actually
drawn. Leaving **Links** blank draws every possible pair in both stages.
**Custom Labels** can attach a value to each candidate connection, whether
or not it is drawn — see below for how they are matched.

## Inputs

### Sources

A comma-separated list of source names (for example, `S1, S2, S3`).

### Transits

A comma-separated list of transit names (for example, `T1,T2`).

### Destinations

A comma-separated list of destination names (for example, `D1,D2,D3`).

### Links

A comma-separated list of `Source-Transit` and `Transit-Destination` pairs
to draw as edges (for example, `S1-T1,T1-D1`). Leave this blank to draw
every possible source-to-transit and transit-to-destination combination.

### Edge Label

When checked, each edge on the diagram is labeled — with its **Custom
Labels** value if one was supplied for that pair, or otherwise with its
position number (see **Custom Labels** below). When unchecked, edges are
drawn without a visible label.

### Circular

When checked, sources, transits, and destinations are arranged along
curved arcs. When unchecked, they are arranged in straight vertical lines.
This only affects the layout, not which connections are drawn.

### Custom Labels

An optional comma-separated list of values used to label the edges. Values
are matched to pairs **by position across every possible combination**,
listed first for every source-transit pair (source by source, and within
each source, transit by transit), followed by every transit-destination
pair (transit by transit, and within each transit, destination by
destination) — including pairs not selected in **Links**. If fewer labels
are supplied than there are combinations, the remaining pairs are left
unlabeled.

## Results

### Chart

The network diagram, showing every drawn source-transit and
transit-destination connection as a line between the two nodes, arranged
according to **Circular**, and labeled according to **Edge Label** and
**Custom Labels**.

### Nodes

A table with one row per source, transit, and destination, giving its name
and the X, Y position used to place it on the chart.

### Edges

A table with one row per drawn connection, giving its **From** node, its
**To** node, and its **Edge** label (a position number by default, or the
matched **Custom Labels** value).

## Example

With the default inputs — sources `S1, S2, S3`, transits `T1,T2`,
destinations `D1,D2,D3`, and every source-transit and transit-destination
pair included by default — the chart draws all 6 source-transit
connections (S1-T1, S1-T2, S2-T1, S2-T2, S3-T1, S3-T2) followed by all 9
transit-destination connections (T1-D1, T1-D2, T1-D3, T2-D1, T2-D2, T2-D3).
Without **Custom Labels**, the edges are numbered sequentially 0 through
14 in that same order, since every candidate pair is drawn and none are
skipped.

## Important Assumptions and Interpretation

-   **Custom Labels** are matched purely by position across the full list
    of source-transit pairs followed by the full list of
    transit-destination pairs, not by the order connections appear in
    **Links** or on the chart — supply enough values, in the right order,
    to label every intended connection.
-   This calculator only draws the network and reports label/position
    values; it does not calculate flows, costs, or optimal routes. Use the
    supply-chain optimization calculators (for example, `transship_opt`)
    when you need the connections and quantities calculated for you.
