from pathlib import Path
import pandas as pd
import geopandas as gpd
import osmnx as ox
import matplotlib.pyplot as plt

OUTPUT_DIR = Path("outputs")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

nodes = gpd.read_file(OUTPUT_DIR / "augsburg_walk_nodes.gpkg")
edges = gpd.read_file(OUTPUT_DIR / "augsburg_walk_edges.gpkg")
pharmacies = gpd.read_file(OUTPUT_DIR / "augsburg_pharmacies.gpkg")

if pharmacies.empty:
    raise RuntimeError("No pharmacy features were found.")

# OSM POIs are points in the current dataset, but this keeps the script robust.
pharmacy_points = pharmacies.copy()
pharmacy_points["geometry"] = pharmacy_points.geometry.representative_point()

# OSMnx nearest_nodes expects x = longitude, y = latitude for EPSG:4326.
# Rebuild the graph from the edge/node GeoDataFrames by redownloading is unnecessary.
# Instead, create a fresh walk graph for reliable snapping.
PLACE = "Augsburg, Bavaria, Germany"
G = ox.graph_from_place(PLACE, network_type="walk", simplify=True)

x = pharmacy_points.geometry.x.to_numpy()
y = pharmacy_points.geometry.y.to_numpy()

nearest_nodes = ox.distance.nearest_nodes(G, X=x, Y=y)

pharmacy_points["nearest_node"] = nearest_nodes

# Get snapped node coordinates.
node_lookup = {
    node_id: (data["x"], data["y"])
    for node_id, data in G.nodes(data=True)
}

pharmacy_points["snap_lon"] = pharmacy_points["nearest_node"].map(lambda n: node_lookup[n][0])
pharmacy_points["snap_lat"] = pharmacy_points["nearest_node"].map(lambda n: node_lookup[n][1])

snapped = gpd.GeoDataFrame(
    pharmacy_points.drop(columns="geometry"),
    geometry=gpd.points_from_xy(pharmacy_points["snap_lon"], pharmacy_points["snap_lat"]),
    crs="EPSG:4326"
)

# Distance from original pharmacy point to snapped network node.
# Project both layers to local UTM before measuring metres.
utm_crs = pharmacy_points.estimate_utm_crs()
orig_p = pharmacy_points.to_crs(utm_crs)
snap_p = snapped.to_crs(utm_crs)

snap_dist_m = orig_p.geometry.distance(snap_p.geometry)
pharmacy_points["snap_distance_m"] = snap_dist_m

# Summary
summary = pd.DataFrame({
    "metric": [
        "pharmacy_count",
        "unique_nearest_nodes",
        "mean_snap_distance_m",
        "median_snap_distance_m",
        "max_snap_distance_m"
    ],
    "value": [
        len(pharmacy_points),
        pharmacy_points["nearest_node"].nunique(),
        round(float(snap_dist_m.mean()), 2),
        round(float(snap_dist_m.median()), 2),
        round(float(snap_dist_m.max()), 2),
    ]
})
summary.to_csv(RESULTS_DIR / "step3_snapping_summary.csv", index=False)

with open(RESULTS_DIR / "step3_snapping_summary.txt", "w", encoding="utf-8") as f:
    f.write("P05 Urban Accessibility — Step 3 Network Snapping\n")
    f.write("=" * 52 + "\n\n")
    for _, row in summary.iterrows():
        f.write(f"{row['metric']}: {row['value']}\n")

# Lightweight table for later analysis
cols = [c for c in ["name", "amenity", "nearest_node", "snap_distance_m"] if c in pharmacy_points.columns]
pharmacy_points[cols].to_csv(RESULTS_DIR / "step3_pharmacy_node_matches.csv", index=False)

# Preview map
edges_p = edges.to_crs(utm_crs)
orig_p = pharmacy_points.to_crs(utm_crs)
snap_p = snapped.to_crs(utm_crs)

fig, ax = plt.subplots(figsize=(10, 10))
edges_p.plot(ax=ax, linewidth=0.3, alpha=0.55)
orig_p.plot(ax=ax, markersize=20, label="Pharmacy")
snap_p.plot(ax=ax, markersize=10, label="Nearest network node")

# Draw connector lines so snapping can be visually inspected.
for p1, p2 in zip(orig_p.geometry, snap_p.geometry):
    ax.plot([p1.x, p2.x], [p1.y, p2.y], linewidth=0.6, alpha=0.6)

ax.set_title("Pharmacy POIs Snapped to Pedestrian Network", fontsize=14)
ax.set_axis_off()
ax.legend()
fig.tight_layout()
fig.savefig(RESULTS_DIR / "step3_snapping_preview.png", dpi=220, bbox_inches="tight")
plt.close(fig)

print(summary.to_string(index=False))
print("Step 3 snapping completed successfully.")
