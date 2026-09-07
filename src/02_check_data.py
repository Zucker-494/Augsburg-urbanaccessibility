from pathlib import Path
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

OUTPUT_DIR = Path("outputs")

nodes_path = OUTPUT_DIR / "augsburg_walk_nodes.gpkg"
edges_path = OUTPUT_DIR / "augsburg_walk_edges.gpkg"
pharmacies_path = OUTPUT_DIR / "augsburg_pharmacies.gpkg"

print("Reading generated GeoPackages...")
nodes = gpd.read_file(nodes_path)
edges = gpd.read_file(edges_path)
pharmacies = gpd.read_file(pharmacies_path)

print("Creating data summary...")

# Basic validation
if nodes.empty:
    raise RuntimeError("Pedestrian-network nodes layer is empty.")
if edges.empty:
    raise RuntimeError("Pedestrian-network edges layer is empty.")
if pharmacies.empty:
    raise RuntimeError("Pharmacy layer is empty.")

# Ensure pharmacy geometries can be shown consistently on the preview map.
# Polygon/multipolygon features are represented by a point guaranteed to lie inside.
pharmacy_points = pharmacies.copy()
pharmacy_points["geometry"] = pharmacy_points.geometry.representative_point()

summary = pd.DataFrame(
    [
        ["pedestrian_nodes", len(nodes), str(nodes.crs), nodes.geometry.geom_type.value_counts().to_dict()],
        ["pedestrian_edges", len(edges), str(edges.crs), edges.geometry.geom_type.value_counts().to_dict()],
        ["pharmacies", len(pharmacies), str(pharmacies.crs), pharmacies.geometry.geom_type.value_counts().to_dict()],
    ],
    columns=["layer", "feature_count", "crs", "geometry_types"],
)

summary.to_csv(OUTPUT_DIR / "data_summary.csv", index=False)

with open(OUTPUT_DIR / "data_summary.txt", "w", encoding="utf-8") as f:
    f.write("P05 Urban Accessibility — Step 2 Data Check\n")
    f.write("=" * 48 + "\n\n")
    f.write(f"Pedestrian-network nodes: {len(nodes):,}\n")
    f.write(f"Pedestrian-network edges: {len(edges):,}\n")
    f.write(f"Pharmacy features: {len(pharmacies):,}\n\n")
    f.write(f"Nodes CRS: {nodes.crs}\n")
    f.write(f"Edges CRS: {edges.crs}\n")
    f.write(f"Pharmacies CRS: {pharmacies.crs}\n\n")
    f.write(f"Network bounds: {edges.total_bounds.tolist()}\n")
    f.write(f"Pharmacy bounds: {pharmacies.total_bounds.tolist()}\n\n")
    f.write("Geometry types:\n")
    f.write(f"  Nodes: {nodes.geometry.geom_type.value_counts().to_dict()}\n")
    f.write(f"  Edges: {edges.geometry.geom_type.value_counts().to_dict()}\n")
    f.write(f"  Pharmacies: {pharmacies.geometry.geom_type.value_counts().to_dict()}\n")

print("Creating preview map...")

# Plot in a projected CRS for a cleaner local map and metric coordinates.
target_crs = edges.estimate_utm_crs()
edges_p = edges.to_crs(target_crs)
pharmacy_points_p = pharmacy_points.to_crs(target_crs)

fig, ax = plt.subplots(figsize=(10, 10))
edges_p.plot(ax=ax, linewidth=0.35, alpha=0.65)
pharmacy_points_p.plot(ax=ax, markersize=18)

ax.set_title("Augsburg Pedestrian Network and Pharmacy POIs", fontsize=14)
ax.set_axis_off()
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "step2_data_preview.png", dpi=220, bbox_inches="tight")
plt.close(fig)

print("Step 2 data check completed successfully.")
print(summary.to_string(index=False))
