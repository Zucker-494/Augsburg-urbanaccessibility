from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import osmnx as ox

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
PLACE = "Augsburg, Bavaria, Germany"

# Step 4 already computed network distance for every pedestrian-network node.
df = pd.read_csv(RESULTS_DIR / "step4_node_accessibility.csv")

# Define interpretable distance bands rather than inventing a composite score.
# These thresholds align with the descriptive statistics already reported in Step 4.
bins = [-1, 500, 1000, 1500, float("inf")]
labels = ["≤ 500 m", "500–1000 m", "1000–1500 m", "> 1500 m"]
df["accessibility_band"] = pd.cut(
    df["nearest_pharmacy_m"], bins=bins, labels=labels
)

counts = df["accessibility_band"].value_counts(sort=False)
pct = (counts / len(df) * 100).round(2)

band_summary = pd.DataFrame({
    "distance_band": labels,
    "node_count": [int(counts.get(x, 0)) for x in labels],
    "percentage": [float(pct.get(x, 0)) for x in labels],
})
band_summary.to_csv(RESULTS_DIR / "step5_accessibility_bands.csv", index=False)

gap = df[df["nearest_pharmacy_m"] > 1500].copy()
gap.to_csv(RESULTS_DIR / "step5_gap_nodes.csv", index=False)

with open(RESULTS_DIR / "step5_gap_summary.txt", "w", encoding="utf-8") as f:
    f.write("P05 Urban Accessibility — Step 5 Accessibility Gaps\n")
    f.write("=" * 57 + "\n\n")
    f.write("Operational definition:\n")
    f.write("Potential accessibility gap = pedestrian-network node more than 1500 m\n")
    f.write("from the nearest pharmacy along the walking network.\n\n")
    for _, row in band_summary.iterrows():
        f.write(
            f"{row['distance_band']}: {int(row['node_count'])} nodes "
            f"({row['percentage']:.2f}%)\n"
        )
    f.write(f"\nPotential gap nodes (>1500 m): {len(gap)}\n")
    f.write(f"Potential gap share: {len(gap) / len(df) * 100:.2f}%\n")
    f.write("\nInterpretation note:\n")
    f.write(
        "The 1500 m threshold is used here as an operational screening threshold, "
        "not as a universal standard of adequate pharmacy access.\n"
    )

# Recreate network only for spatial visualization.
G = ox.graph_from_place(PLACE, network_type="walk", simplify=True)
nodes, edges = ox.graph_to_gdfs(G)

# Join Step 4 distances back to OSM node IDs.
# The CSV index column written by Step 4 is the graph node identifier.
node_id_col = df.columns[0]
dist_lookup = df.set_index(node_id_col)["nearest_pharmacy_m"]
nodes["nearest_pharmacy_m"] = nodes.index.map(dist_lookup)

valid = nodes[nodes["nearest_pharmacy_m"].notna()].copy()
gap_nodes = valid[valid["nearest_pharmacy_m"] > 1500].copy()

utm = valid.estimate_utm_crs()
edges_p = edges.to_crs(utm)
valid_p = valid.to_crs(utm)
gap_p = gap_nodes.to_crs(utm)

# Gap-focused map: background network is deliberately subdued.
fig, ax = plt.subplots(figsize=(9, 10))
edges_p.plot(ax=ax, linewidth=0.25, alpha=0.20)
valid_p.plot(ax=ax, markersize=1.5, alpha=0.20)
gap_p.plot(ax=ax, markersize=5.0, label="> 1500 m from nearest pharmacy")
ax.set_title("Potential Pharmacy Accessibility Gaps", fontsize=14)
ax.set_axis_off()
ax.legend(loc="upper right")
fig.tight_layout()
fig.savefig(RESULTS_DIR / "step5_accessibility_gaps.png", dpi=220, bbox_inches="tight")
plt.close(fig)

# Distance-band distribution.
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(band_summary["distance_band"], band_summary["percentage"])
ax.set_ylabel("Share of pedestrian-network nodes (%)")
ax.set_xlabel("Network distance to nearest pharmacy")
ax.set_title("Pedestrian-Network Nodes by Pharmacy Accessibility Band")
ax.tick_params(axis="x", rotation=15)
fig.tight_layout()
fig.savefig(RESULTS_DIR / "step5_accessibility_bands.png", dpi=220, bbox_inches="tight")
plt.close(fig)

print(band_summary.to_string(index=False))
print(f"Potential gap nodes (>1500 m): {len(gap)}")
print("Step 5 completed successfully.")
