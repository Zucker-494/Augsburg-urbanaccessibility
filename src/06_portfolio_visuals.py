from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

summary = pd.read_csv(RESULTS_DIR / "step5_accessibility_bands.csv")

# Create a cleaner portfolio-oriented summary graphic.
labels = summary["distance_band"].tolist()
values = summary["percentage"].tolist()

fig, ax = plt.subplots(figsize=(9, 5.5))

bars = ax.barh(labels, values)

ax.set_xlabel("Share of pedestrian-network nodes (%)")
ax.set_ylabel("")
ax.set_title("Pharmacy Accessibility Across Augsburg's Pedestrian Network", fontsize=15)

# Put the largest accessibility band at the top.
ax.invert_yaxis()

# Add values at the end of each bar.
for bar, value in zip(bars, values):
    ax.text(
        value + 0.6,
        bar.get_y() + bar.get_height() / 2,
        f"{value:.1f}%",
        va="center",
        fontsize=11
    )

ax.set_xlim(0, max(values) * 1.18)
ax.grid(axis="x", alpha=0.2)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
fig.savefig(RESULTS_DIR / "step6_portfolio_summary.png", dpi=240, bbox_inches="tight")
plt.close(fig)

# Create a concise interpretation text for README use.
within_1000 = summary.loc[
    summary["distance_band"].isin(["≤ 500 m", "500–1000 m"]),
    "percentage"
].sum()

gap_share = summary.loc[
    summary["distance_band"] == "> 1500 m",
    "percentage"
].sum()

with open(RESULTS_DIR / "step6_interpretation.txt", "w", encoding="utf-8") as f:
    f.write("P05 Urban Accessibility — Step 6 Interpretation\n")
    f.write("=" * 50 + "\n\n")
    f.write(
        f"{within_1000:.2f}% of pedestrian-network nodes are within 1000 m "
        "network distance of a pharmacy.\n"
    )
    f.write(
        f"{gap_share:.2f}% of pedestrian-network nodes fall beyond the 1500 m "
        "screening threshold used to identify potential accessibility gaps.\n"
    )
    f.write(
        "The mapped pattern shows that low-accessibility nodes are concentrated "
        "mainly at the urban periphery and network edges, while the inner urban "
        "area generally exhibits shorter walking-network distances to pharmacies.\n"
    )
    f.write(
        "These results describe network-based spatial accessibility rather than "
        "population accessibility, because the analysis is based on pedestrian-network "
        "nodes rather than residential population or demand-weighted locations.\n"
    )

print("Step 6 portfolio visualization and interpretation created.")
