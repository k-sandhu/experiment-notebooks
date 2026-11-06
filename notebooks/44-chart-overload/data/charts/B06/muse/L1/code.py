import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

df["sq_ft_k"] = df["sq_ft"] / 1000
standard = df[df["format"] == "standard"]
large_new = df[(df["format"] == "large") & (df["opened_year"] >= 2025)]
large_mature = df[(df["format"] == "large") & (df["opened_year"] < 2025)]
large_all = df[df["format"] == "large"]

# Fair comparison: exclude 2025-26 large stores that are still ramping up.
std_sq = standard["sq_ft"].mean()
std_sales = standard["annual_sales_musd"].mean()
std_prod = standard["sales_per_sqft_usd"].mean()

mat_sq = large_mature["sq_ft"].mean()
mat_sales = large_mature["annual_sales_musd"].mean()
mat_prod = large_mature["sales_per_sqft_usd"].mean()

space_gain = mat_sq / std_sq - 1
sales_gain = mat_sales / std_sales - 1
prod_change = mat_prod / std_prod - 1

TEAL = "#147A6E"
ORANGE = "#D95F02"
GREY = "#555555"

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.65, 1.0], "wspace": 0.28}
)

fig.suptitle(
    f"Build standard by default: mature large stores add {space_gain:.0%} space\n"
    f"for only {sales_gain:.0%} more sales",
    fontsize=17,
    fontweight="bold",
    x=0.015,
    ha="left",
)
fig.text(
    0.015,
    0.905,
    "FreshWay property committee — next five stores  |  Reserve large for exceptionally large catchments",
    fontsize=11,
    color=GREY,
)

# ----- Left: every store -----
ax1.axvspan(33, 38, color="#EEEEEE", zorder=0)
ax1.text(35.5, 725, "no stores\n33–38k", ha="center", va="top", fontsize=8, color=GREY)

ax1.scatter(
    standard["sq_ft_k"], standard["sales_per_sqft_usd"],
    s=72, color=TEAL, alpha=0.85, edgecolor="white", linewidth=0.7, zorder=3,
    label=f"Standard (n={len(standard)})",
)
ax1.scatter(
    large_mature["sq_ft_k"], large_mature["sales_per_sqft_usd"],
    s=92, color=ORANGE, alpha=0.95, edgecolor="white", linewidth=0.7, zorder=3,
    label=f"Large, mature (n={len(large_mature)})",
)
ax1.scatter(
    large_new["sq_ft_k"], large_new["sales_per_sqft_usd"],
    s=105, facecolor="white", edgecolor=ORANGE, linewidth=2.0, zorder=4,
    label=f"Large, opened 2025–26 (n={len(large_new)})",
)

# Group averages, drawn only over each group's own size range
ax1.hlines(std_prod, 17, 33, color=TEAL, linewidth=3.5, zorder=4)
ax1.hlines(mat_prod, 38, 56, color=ORANGE, linewidth=3.5, zorder=4)
ax1.text(17, std_prod + 20, f"Standard avg  ${std_prod:.0f}/sq ft",
         fontsize=11, fontweight="bold", color=TEAL)
ax1.text(38, mat_prod + 20, f"Mature large avg  ${mat_prod:.0f}/sq ft",
         fontsize=11, fontweight="bold", color=ORANGE)
ax1.annotate(
    f"${std_prod - mat_prod:.0f} less\nper sq ft",
    xy=(44, (std_prod + mat_prod) / 2), xytext=(46, 625),
    fontsize=10, fontweight="bold", color="#222222",
    arrowprops=dict(arrowstyle="->", color="#222222", lw=1.4),
)

if len(large_new):
    ax1.annotate(
        "2025–26 large:\nstill ramping up\n(excluded from avg)",
        xy=(large_new["sq_ft_k"].median(), large_new["sales_per_sqft_usd"].median()),
        xytext=(37, 338),
        fontsize=9, color=ORANGE,
        arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.3),
    )

ax1.set_title("Bigger stores sell less per square foot", fontsize=13, fontweight="bold", loc="left", pad=10)
ax1.set_xlabel("Selling floor area (000 sq ft)", fontsize=11)
ax1.set_ylabel("Annual sales per sq ft ($)", fontsize=11)
ax1.set_xlim(16, 57)
ax1.set_ylim(320, 750)
ax1.grid(axis="y", color="#DDDDDD", linewidth=0.8)
ax1.set_axisbelow(True)
ax1.tick_params(labelsize=10)
for spine in ["top", "right"]:
    ax1.spines[spine].set_visible(False)
ax1.legend(frameon=False, fontsize=9, loc="lower left", handlelength=1.2)

# ----- Right: mature large indexed to standard = 100 -----
labels = [
    f"Sales / sq ft\n${mat_prod:.0f} vs ${std_prod:.0f}",
    f"Annual sales\n${mat_sales:.1f}m vs ${std_sales:.1f}m",
    f"Floor space\n{mat_sq/1000:.0f}k vs {std_sq/1000:.0f}k sq ft",
]
index_values = [mat_prod / std_prod * 100, mat_sales / std_sales * 100, mat_sq / std_sq * 100]
changes = [prod_change, sales_gain, space_gain]
ypos = np.arange(3)

ax2.barh(ypos, index_values, height=0.55, color=ORANGE, alpha=0.92, zorder=3)
ax2.axvline(100, color=TEAL, linewidth=2.5, linestyle="--", zorder=4)
ax2.text(100, 2.62, "Standard = 100", ha="center", fontsize=9, fontweight="bold", color=TEAL)

for y, val, chg in zip(ypos, index_values, changes):
    ax2.text(val + 4, y, f"{chg:+.0%}", va="center", fontsize=12, fontweight="bold", color="#222222")

ax2.set_yticks(ypos)
ax2.set_yticklabels(labels, fontsize=9.5)
ax2.set_xlim(0, max(215, max(index_values) * 1.22))
ax2.set_ylim(-1.25, 2.85)
ax2.set_xlabel("Mature large, indexed (standard = 100)", fontsize=10)
ax2.set_title("Space grows faster\nthan sales", fontsize=13, fontweight="bold", loc="left", pad=10)
ax2.grid(axis="x", color="#DDDDDD", linewidth=0.8)
ax2.set_axisbelow(True)
ax2.tick_params(labelsize=10)
for spine in ["top", "right"]:
    ax2.spines[spine].set_visible(False)

ax2.text(
    3, -0.92,
    "Catchment hurdle is higher too\n"
    f"Large: {large_all['catchment_pop_k'].min():.0f}–{large_all['catchment_pop_k'].max():.0f}k people within 15 min\n"
    f"Standard: {standard['catchment_pop_k'].min():.0f}–{standard['catchment_pop_k'].max():.0f}k",
    fontsize=9, va="center",
    bbox=dict(boxstyle="round,pad=0.45", facecolor="#FFF1E6", edgecolor=ORANGE, linewidth=1.2),
)

fig.text(
    0.015, 0.012,
    f"Each dot = 1 store (n={len(df)}). Large averages exclude the {len(large_new)} stores opened in 2025–26. "
    "Two renovated stores are annualised.",
    fontsize=8, color=GREY,
)

fig.tight_layout(rect=[0, 0.035, 1, 0.88])
