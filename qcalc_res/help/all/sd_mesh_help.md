# Source Destination Mesh

## Purpose

This calculator draws a network diagram connecting a set of **sources** to a
set of **destinations**, showing which source-destination pairs are linked.
It is useful for visualizing any two-sided relationship — such as plants
and customers, warehouses and stores, or suppliers and buyers — and,
optionally, for labeling each connection with a value (for example, a
shipped quantity or a cost) to review alongside the network.

## Background

### How the mesh is built

Every possible pair formed by taking one source and one destination is a
candidate connection. The **Links** input selects which of those candidate
connections are actually drawn. Leaving **Links** blank draws every
possible source-destination pair. **Custom Labels** can attach a value to
each candidate connection, whether or not it is drawn — see below for how
they are matched.

## Inputs

### Sources

A comma-separated list of source names (for example, `S1, S2`).

### Destinations

A comma-separated list of destination names (for example, `D1,D2,D3`).

### Links

A comma-separated list of `Source-Destination` pairs to draw as edges (for
example, `S1-D1,S1-D2`). Leave this blank to draw every possible
combination of a source and a destination.

### Edge Label

When checked, each edge on the diagram is labeled — with its **Custom
Labels** value if one was supplied for that pair, or otherwise with its
position number (see **Custom Labels** below). When unchecked, edges are
drawn without a visible label.

### Circular

When checked, sources and destinations are arranged along curved arcs.
When unchecked, they are arranged in straight vertical lines. This only
affects the layout, not which connections are drawn.

### Custom Labels

An optional comma-separated list of values used to label the edges. Values
are matched to source-destination pairs **by position across every
possible combination**, taken source by source and, within each source,
destination by destination — including pairs not selected in **Links**. For
example, with sources `S1, S2` and destinations `D1, D2, D3`, the positions
are S1-D1, S1-D2, S1-D3, S2-D1, S2-D2, S2-D3 in that order, and the first
value in **Custom Labels** applies to S1-D1, the second to S1-D2, and so on
— even if some of those pairs are excluded by **Links**. If fewer labels
are supplied than there are combinations, the remaining pairs are left
unlabeled.

## Results

### Chart

The network diagram, showing every drawn source-destination connection as a
line between the two nodes, arranged according to **Circular**, and labeled
according to **Edge Label** and **Custom Labels**.

### Nodes

A table with one row per source and destination, giving its name and the X,
Y position used to place it on the chart.

### Edges

A table with one row per drawn connection, giving its **From** source, its
**To** destination, and its **Edge** label (a position number by default,
or the matched **Custom Labels** value).

## Example

With the default inputs — sources `S1, S2`, destinations `D1,D2,D3`, and
links `S1-D1,S1-D2,S1-D3,S2-D1,S2-D3` (note that `S2-D2` is not listed) —
the chart draws 5 connections: S1 to each of D1, D2, D3, and S2 to D1 and
D3, but not S2 to D2. Without **Custom Labels**, the drawn edges are
numbered by their position in the full 6-combination list (S1-D1=0,
S1-D2=1, S1-D3=2, S2-D1=3, S2-D3=5) — position 4 (S2-D2) is skipped because
that pair is not drawn, so the visible numbering has a gap. If
`custom_labels='100,200,300,400,500'` is supplied instead, S1-D1 through
S2-D1 are labeled 100, 200, 300, 400, and S2-D3 is left unlabeled, because
its position (5) falls beyond the 5 supplied values.

## Important Assumptions and Interpretation

-   **Custom Labels** are matched purely by position in the full
    source-by-destination combination list, not by the order connections
    appear in **Links** or on the chart — supply enough values, in the
    right order, to label every intended connection.
-   This calculator only draws the network and reports label/position
    values; it does not calculate flows, costs, or optimal routes. Use the
    supply-chain optimization calculators (for example, `transport_opt`)
    when you need the connections and quantities calculated for you.
