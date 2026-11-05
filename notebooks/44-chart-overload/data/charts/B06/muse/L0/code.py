import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

df = pd.read_csv("data.csv")

is_large = df["format"] == "large"
is_new_large = is_large & (df["opened_year"] >= 2025)
is_mature_large = is_large & (df["opened_year"] < 2025)
is_standard = df["format"] == "standard"

standard = df[is_standard]
mature_large = df[is_mature_large]
new_large = df[is_new_large]
all_large = df[is_large]

std_psf = standard["sales_per_sqft_usd"].mean()
mature_psf = mature_large["sales_per_sqft_usd"].mean()
new_psf = new_large["sales_per_sqft_usd"].mean()

std_mean_sq = standard["sq_ft"].mean()
std_mean_sales = standard["annual_sales_musd"].mean()
large_mean_sq = all_large["sq_ft"].mean()
large_mean_sales = all_large["annual_sales_musd"].mean()
space_gain = (large_mean_sq / std_mean_sq - 1) * 100
sales_gain = (large_mean_sales / std_mean_sales - 1) * 100

blue = "#2E6FBB"
orange = "#D95D26"

fig, axes = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.55, 1.0]}
)
ax, ax2 = axes

# --- Left panel: floor area vs total sales ---
x_line = np.linspace(0, 58000, 100)
ax.plot(
    x_line,
    std_psf * x_line / 1e6,
    color=blue,
    linestyle="--",
    linewidth=1.2,
    alpha=0.8,
    label=f"${std_psf:,.0f}/sq ft benchmark (standard mean)",
)
ax.plot(
    x_line,
    mature_psf * x_line / 1e6,
    color=orange,
    linestyle="--",
    linewidth=1.2,
    alpha=0.9,
    label=f"${mature_psf:,.0f}/sq ft benchmark (large, pre-2025)",
)

ax.scatter(
    standard["sq_ft"],
    standard["annual_sales_musd"],
    s=55,
    color=blue,
    alpha=0.85,
    edgecolors="white",
    linewidths=0.5,
    label=f"Standard (n={len(standard)})",
    zorder=3,
)
ax.scatter(
    mature_large["sq_ft"],
    mature_large["annual_sales_musd"],
    s=75,
    marker="s",
    color=orange,
    alpha=0.95,
    edgecolors="white",
    linewidths=0.5,
    label=f"Large, opened before 2025 (n={len(mature_large)})",
    zorder=3,
)
ax.scatter(
    new_large["sq_ft"],
    new_large["annual_sales_musd"],
    s=85,
    marker="s",
    facecolors="white",
    edgecolors=orange,
    linewidths=1.6,
    label=f"Large, opened 2025-26 (n={len(new_large)})",
    zorder=4,
)

# Format means and the 88% space vs 46% sales contrast
ax.scatter(
    [std_mean_sq, large_mean_sq],
    [std_mean_sales, large_mean_sales],
    s=190,
    marker="X",
    color="black",
    edgecolors="white",
    linewidths=0.8,
    label="Format mean",
    zorder=5,
)
ax.annotate(
    "",
    xy=(large_mean_sq, large_mean_sales),
    xytext=(std_mean_sq, std_mean_sales),
    arrowprops=dict(arrowstyle="->", color="black", linewidth=1.3,
                    shrinkA=8, shrinkB=8),
    zorder=4,
)
ax.text(
    (std_mean_sq + large_mean_sq) / 2,
    (std_mean_sales + large_mean_sales) / 2 - 3.4,
    f"+{space_gain:.0f}% floor space\n+{sales_gain:.0f}% sales\n(standard mean to large mean)",
    ha="center",
    va="top",
    fontsize=8,
    bbox=dict(boxstyle="round,pad=0.35", facecolor="white", alpha=0.85,
              edgecolor="none"),
)

# Top seller
s39 = df.loc[df["store_id"] == "S39"].iloc[0]
ax.annotate(
    f"S39 Radley\ntop seller: ${s39['annual_sales_musd']:.1f}m",
    xy=(s39["sq_ft"], s39["annual_sales_musd"]),
    xytext=(36500, 28.6),
    fontsize=8,
    arrowprops=dict(arrowstyle="->", color="#333333", linewidth=1.0),
    ha="center",
)

ax.set_xlim(0, 58000)
ax.set_ylim(0, 32)
ax.set_xlabel("Selling floor area (sq ft)")
ax.set_ylabel("Annual sales, last 12 months ($m)")
ax.set_title("Sales rise with size, but with\ndiminishing returns", fontsize=11)
ax.xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda v, _: f"{v:,.0f}")
)
ax.grid(True, alpha=0.25)
ax.legend(loc="upper left", fontsize=7.5, framealpha=0.95)

# --- Right panel: sales per square foot by group ---
ax2.axhline(std_psf, color=blue, linestyle="--", linewidth=1.1, alpha=0.7)

groups = [
    (f"Standard\n(n={len(standard)})", standard, blue, "o", blue),
    (f"Large,\nopened before 2025\n(n={len(mature_large)})",
     mature_large, orange, "s", orange),
    (f"Large,\nopened 2025-26\n(n={len(new_large)})",
     new_large, orange, "s", "white"),
]
rng = np.random.default_rng(42)

for i, (label, sub, color, marker, face) in enumerate(groups):
    jitter = rng.normal(i, 0.07, size=len(sub))
    ax2.scatter(
        jitter,
        sub["sales_per_sqft_usd"],
        s=60,
        marker=marker,
        facecolors=face,
        edgecolors=color,
        linewidths=1.1 if face == "white" else 0.5,
        alpha=0.9,
        zorder=3,
    )
    mean = sub["sales_per_sqft_usd"].mean()
    ax2.plot([i - 0.27, i + 0.27], [mean, mean],
             color="black", linewidth=2.2, zorder=4)
    ax2.text(i, mean + 24, f"mean ${mean:,.0f}",
             ha="center", va="bottom", fontsize=8, fontweight="bold")

gap = mature_psf - std_psf
ax2.annotate(
    f"${abs(gap):,.0f} below\nstandard mean",
    xy=(1, mature_psf),
    xytext=(1.55, 565),
    fontsize=8,
    ha="center",
    arrowprops=dict(arrowstyle="->", color="#333333", linewidth=1.0),
)

ax2.set_xticks(range(len(groups)))
ax2.set_xticklabels([g[0] for g in groups], fontsize=8)
ax2.set_xlim(-0.55, 2.55)
ax2.set_ylim(300, 760)
ax2.set_ylabel("Annual sales per sq ft ($)")
ax2.set_title("The gap remains even after\nremoving new large stores", fontsize=11)
ax2.grid(axis="y", alpha=0.25)

for a in axes:
    a.spines["top"].set_visible(False)
    a.spines["right"].set_visible(False)

fig.suptitle(
    "Large stores sell more overall, but far less per square foot",
    fontsize=14,
    fontweight="bold",
    y=0.98,
)
fig.text(
    0.01,
    0.01,
    "Each point is a store (n=46). Dashed lines are constant sales-per-sq-ft benchmarks through the origin; black marks are means.\n"
    "Large stores sit in larger catchments (85-140k within 15 minutes vs 30-90k for standard), yet still trade less intensively.\n"
    "Large stores opened in 2025-26 are still building trade and are shown separately. Two stores' sales are annualised after renovation.",
    fontsize=8,
    color="#333333",
    ha="left",
    va="bottom",
)

fig.tight_layout(rect=[0, 0.09, 1, 0.93])
