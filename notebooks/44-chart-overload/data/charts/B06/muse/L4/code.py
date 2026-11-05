import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

df = pd.read_csv("data.csv")

standard = df[df["format"] == "standard"]
large_est = df[(df["format"] == "large") & (df["opened_year"] < 2025)]

mean_std = standard["sales_per_sqft_usd"].mean()
mean_large = large_est["sales_per_sqft_usd"].mean()
gap_usd = mean_std - mean_large
gap_pct = 100 * gap_usd / mean_std

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.09, right=0.96, top=0.76, bottom=0.21)

x = np.array([0, 1])
means = [mean_std, mean_large]
colors = ["#9AA0A6", "#D94F30"]

ax.bar(x, means, width=0.54, color=colors, zorder=2)

# Benchmark line at the standard-store average
ax.hlines(mean_std, x[0] - 0.27, x[1] + 0.27,
          colors="#555555", linestyles="--", linewidth=1.1, zorder=3)

# Show only the 7 established large stores: every one sits below the benchmark.
# The 35 standard-store dots added clutter, hid the $606 label and forced a tall axis.
rng = np.random.default_rng(42)
large_vals = large_est["sales_per_sqft_usd"].to_numpy()
ax.scatter(
    x[1] + rng.uniform(-0.15, 0.15, size=len(large_vals)),
    large_vals,
    s=42, color="#222222", edgecolor="white", linewidth=0.7, zorder=4,
)

# Average labels in the middle of each bar, clear of the dots
for xi, mean in zip(x, means):
    ax.text(xi, mean / 2, f"${mean:,.0f}", ha="center", va="center",
            fontsize=17, fontweight="bold", color="white", zorder=5)

# Make the gap itself readable in the white space above the large bar
ax.annotate("", xy=(1.38, mean_std), xytext=(1.38, mean_large),
            arrowprops=dict(arrowstyle="<->", color="#D94F30", linewidth=1.4),
            zorder=4)
ax.text(x[1], mean_large + gap_usd / 2 + 18, f"−${gap_usd:,.0f}",
        ha="center", va="center", fontsize=14, fontweight="bold",
        color="#D94F30", zorder=5)

ax.set_xticks(x)
ax.set_xticklabels(
    [f"Standard\n(under 33,000 sq ft)\nn = {len(standard)} stores",
     f"Large, established\n(opened before 2025)\nn = {len(large_est)} stores"],
    fontsize=11.5,
)
ax.set_xlim(-0.58, 1.62)
ax.set_ylabel("Annual sales per sq ft ($)", fontsize=12)
ax.set_ylim(0, 670)
ax.set_yticks([0, 200, 400, 600])
ax.tick_params(axis="y", labelsize=11)
ax.tick_params(axis="x", length=0)
ax.yaxis.grid(True, color="#DDDDDD", linewidth=0.7, zorder=0)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

fig.text(
    0.075, 0.97,
    f"Established large stores earn {gap_pct:.0f}% less per square foot\nthan standard stores",
    fontsize=20, fontweight="bold", color="#111111", va="top", linespacing=1.15,
)
fig.text(
    0.075, 0.815,
    "Bars = format average   ·   dots = the 7 established large stores",
    fontsize=11.5, color="#555555", va="top",
)
fig.text(
    0.075, 0.035,
    f"Excludes 4 large stores opened 2025–26, still building trade. "
    f"Large stores sit in bigger catchments "
    f"({large_est['catchment_pop_k'].min():.0f}k–{large_est['catchment_pop_k'].max():.0f}k within 15 minutes "
    f"vs {standard['catchment_pop_k'].min():.0f}k–{standard['catchment_pop_k'].max():.0f}k),\n"
    f"so weaker locations do not explain the gap.",
    fontsize=9.5, color="#555555", va="bottom", linespacing=1.35,
)
