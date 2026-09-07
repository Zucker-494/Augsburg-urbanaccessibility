from pathlib import Path
import osmnx as ox

PLACE = "Augsburg, Bavaria, Germany"

output_dir = Path("outputs")
output_dir.mkdir(parents=True, exist_ok=True)

print("Downloading pedestrian network...")
G = ox.graph_from_place(PLACE, network_type="walk", simplify=True)

print(
    f"Pedestrian network downloaded: "
    f"{len(G.nodes):,} nodes and {len(G.edges):,} edges."
)

nodes, edges = ox.graph_to_gdfs(G)

print("Downloading pharmacy POIs...")
pharmacies = ox.features_from_place(PLACE, tags={"amenity": "pharmacy"})
pharmacies = pharmacies.reset_index()

print(f"Pharmacies downloaded: {len(pharmacies):,}")

nodes.to_file(
    output_dir / "augsburg_walk_nodes.gpkg",
    layer="nodes",
    driver="GPKG"
)

edges.to_file(
    output_dir / "augsburg_walk_edges.gpkg",
    layer="edges",
    driver="GPKG"
)

pharmacies.to_file(
    output_dir / "augsburg_pharmacies.gpkg",
    layer="pharmacies",
    driver="GPKG"
)

print("Files saved successfully.")
