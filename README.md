# P05 — Urban Accessibility Analysis

## Research question

**How accessible are pharmacies across Augsburg when accessibility is measured
through the pedestrian street network rather than straight-line distance?**

This portfolio project introduces network-based accessibility analysis using
OpenStreetMap data, OSMnx, GeoPandas and NetworkX.

## Current stage

Stage 1 builds the remote data workflow:

1. Retrieve the Augsburg pedestrian network from OpenStreetMap.
2. Retrieve pharmacy POIs.
3. Convert the network to node and edge layers.
4. Export the results as GeoPackages.
5. Store generated files as a GitHub Actions artifact.

The analysis deliberately uses pedestrian network distance rather than
Euclidean distance because geometric proximity does not necessarily represent
actual pedestrian accessibility.

## Workflow

Run the workflow manually from:

`Actions → Run P05 Accessibility Analysis → Run workflow`

The first workflow produces three GeoPackages:

- `augsburg_walk_nodes.gpkg`
- `augsburg_walk_edges.gpkg`
- `augsburg_pharmacies.gpkg`

## Planned next stage

The next stage will snap pharmacy locations to the pedestrian network and
calculate network-based accessibility.
