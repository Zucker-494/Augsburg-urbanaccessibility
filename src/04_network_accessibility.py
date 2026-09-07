from pathlib import Path
import osmnx as ox
import networkx as nx
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

PLACE = "Augsburg, Bavaria, Germany"
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

print("Downloading pedestrian network for accessibility calculation...")
G = ox.graph_from_place(PLACE, network_type="walk", simplify=True)

print("Downloading pharmacy POIs...")
pharmacies = ox.features_from_place(PLACE, tags={"amenity": "pharmacy"}).reset_index()
pharmacy_points = pharmacies.copy()
pharmacy_points["geometry"] = pharmacy_points.geometry.representative_point()

# Snap pharmacies to the walking network.
pharmacy_nodes = ox.distance.nearest_nodes(
    G,
    X=pharmacy_points.geometry.x.to_numpy(),
    Y=pharmacy_points.geometry.y.to_numpy(),
)
pharmacy_nodes = list(set(pharmacy_nodes))

print(f"Using {len(pharmacy_nodes)} unique pharmacy network nodes.")

# Multi-source Dijkstra:
# for every reachable pedestrian-network node, compute the shortest network
# distance to the nearest pharmacy node.
distances = nx.multi_source_dijkstra_path_length(
    G,
    sources=pharmacy_nodes,
    weight="length",
)

nodes, edges = ox.graph_to_gdfs(G)
nodes["nearest_pharmacy_m"] = nodes.index.map(distances)

reachable = nodes["nearest_pharmacy_m"].notna()
nodes_valid = nodes.loc[reachable].copy()

if nodes_valid.empty:
    raise RuntimeError("No network nodes could be connected to a pharmacy.")

# Summary statistics.
s = nodes_valid["nearest_pharmacy_m"]
summary = pd.DataFrame(
    {
        "metric": [
            "network_nodes_total",
            "network_nodes_reachable",
            "pharmacy_features",
            "unique_pharmacy_nodes",
            "mean_nearest_pharmacy_m",
            "median_nearest_pharmacy_m",
            "p90_nearest_pharmacy_m",
            "max_nearest_pharmacy_m",
            "nodes_within_500m_pct",
            "nodes_within_1000m_pct",
            "nodes_within_1500m_pct",
        ],
        "value": [
            len(nodes),
            len(nodes_valid),
            len(pharmacy_points),
            len(pharmacy_nodes),
            round(float(s.mean()), 2),
            round(float(s.median()), 2),
            round(float(s.quantile(0.90)), 2),
            round(float(s.max()), 2),
            round(float((s <= 500).mean() * 100), 2),
            round(float((s <= 1000).mean() * 100), 2),
            round(float((s <= 1500).mean() * 100), 2),
        ],
    }
)
summary.to_csv(RESULTS_DIR / "step4_accessibility_summary.csv", index=False)

with open(RESULTS_DIR / "step4_accessibility_summary.txt", "w", encoding="utf-8") as f:
    f.write("P05 Urban Accessibility — Step 4 Network Accessibility\n")
    f.write("=" * 57 + "\n\n")
    for _, row in summary.iterrows():
        f.write(f"{row['metric']}: {row['value']}\n")

# Lightweight node result table.
node_table = nodes_valid[["x", "y", "nearest_pharmacy_m"]].copy()
node_table.to_csv(RESULTS_DIR / "step4_node_accessibility.csv", index=True)

# Map: distance at every pedestrian-network node.
utm = nodes_valid.estimate_utm_crs()
nodes_p = nodes_valid.to_crs(utm)
edges_p = edges.to_crs(utm)
pharm_p = pharmacy_points.to_crs(utm)

fig, ax = plt.subplots(figsize=(9, 10))
edges_p.plot(ax=ax, linewidth=0.25, alpha=0.25)
nodes_p.plot(
    ax=ax,
    column="nearest_pharmacy_m",
    markersize=3.2,
    legend=True,
    legend_kwds={"label": "Network distance to nearest pharmacy (m)", "shrink": 0.65},
)
pharm_p.plot(ax=ax, markersize=18, marker="x", label="Pharmacy")
ax.set_title("Pedestrian Network Distance to the Nearest Pharmacy", fontsize=14)
ax.set_axis_off()
ax.legend(loc="upper right")
fig.tight_layout()
fig.savefig(RESULTS_DIR / "step4_accessibility_map.png", dpi=220, bbox_inches="tight")
plt.close(fig)

# Distribution plot.
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(s, bins=30)
ax.set_xlabel("Network distance to nearest pharmacy (m)")
ax.set_ylabel("Number of pedestrian-network nodes")
ax.set_title("Distribution of Nearest-Pharmacy Network Distance")
fig.tight_layout()
fig.savefig(RESULTS_DIR / "step4_distance_distribution.png", dpi=220, bbox_inches="tight")
plt.close(fig)

print(summary.to_string(index=False))
print("Step 4 network accessibility completed successfully.")
