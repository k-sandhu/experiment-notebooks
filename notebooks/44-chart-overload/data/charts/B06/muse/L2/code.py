import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

df = pd.read_csv("data.csv")

def group(row):
    if row["format"] == "standard":
        return "standard"
    if row["opened_year"] >= 2025:
        return "large_new"
    return "large_est"

df["group"] = df.apply(group, axis=1)

order = ["standard", "large_est", "large_new"]
labels = {
    "standard": "Standard\n(under 33,000 sq ft)",
    "large_est": "Large, established\n(opened before 2025)",
    "large_new": "Large, opened 2025–26\n(still building trade)",
}
colors = {
    "standard": "#9AA0A6",      # grey: context / benchmark
    "large_est": "#D94F30",     # one strong colour: what matters
    "large_new": "#D9DBDD",     # pale grey: excluded from main comparison
}

means = {g: df.loc[df["group"] == g, "sales_per_sqft_usd"].mean() for g in order}
counts = {g: (df["group"] == g).sum() for g in order}
gap_pct = 100 * (means["standard"] - means["large_est"]) / means["standard"]

large_catch = df.loc[df["format"] == "large", "catchment_pop_k"]
std_catch = df.loc[df["format"] == "standard", "catchment_pop_k"]

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.09, right=0.97, top=0.80, bottom=0.22)

x = np.arange(len(order))
for xi, g in zip(x, order):
    ax.bar(
        xi, means[g], width=0.56,
        color=colors[g],
        hatch="//" if g == "large_new" else None,
        edgecolor="#6B6F76" if g == "large_new" else "none",
        zorder=2,
    )

# Individual stores as dots, so the small large-store sample is visible
rng = np.random.default_rng(42)
for xi, g in zip(x, order):
    vals = df.loc[df["group"] == g, "sales_per_sqft_usd"].to_numpy()
    ax.scatter(
        xi + rng.uniform(-0.17, 0.17, size=len(vals)), vals,
        s=38, color="#222222", edgecolor="white", linewidth=0.6, zorder=4,
    )

# Dashed reference at the standard-store average, extended over the large bar
ax.hlines(means["standard"], x[0] - 0.28, x[1] + 0.28,
          colors="#555555", linestyles="--", linewidth=1.1, zorder=3)

# Number labels only where they carry the message: the two comparable averages
for g, txt_color in [("standard", "white"), ("large_est", "white")]:
    xi = x[order.index(g)]
    ax.text(xi, means[g] - 42, f"${means[g]:,.0f}", ha="center", va="top",
            fontsize=15, fontweight="bold", color=txt_color, zorder=5)

ax.set_xticks(x)
ax.set_xticklabels([f"{labels[g]}\nn = {counts[g]} stores" for g in order], fontsize=11.5)
ax.set_ylabel("Annual sales per sq ft ($)", fontsize=12)
ax.set_ylim(0, 780)
ax.set_yticks([0, 200, 400, 600])
ax.tick_params(axis="y", labelsize=11)
ax.tick_params(axis="x", length=0)
ax.yaxis.grid(True, color="#DDDDDD", linewidth=0.7, zorder=0)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

fig.text(
    0.075, 0.94,
    f"Established large stores earn {gap_pct:.0f}% less per square foot\nthan standard stores",
    fontsize=20, fontweight="bold", color="#111111", va="top",
)
fig.text(
    0.075, 0.845,
    "Bars = format average   ·   dots = individual stores",
    fontsize=11.5, color="#555555", va="top",
)
fig.text(
    0.075, 0.035,
    f"Caveat: 2025–26 large stores are shown separately and excluded above. Large stores also sit in bigger "
    f"catchments\n({large_catch.min():.0f}k–{large_catch.max():.0f}k people within 15 minutes vs "
    f"{std_catch.min():.0f}k–{std_catch.max():.0f}k for standard), so weaker locations do not explain the gap.",
    fontsize=9.5, color="#555555", va="bottom",
)
