import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

standard = df[df["format"] == "standard"]
large = df[df["format"] == "large"]
large_established = large[large["opened_year"] < 2025]

std_ps = standard["sales_per_sqft_usd"].mean()
lrg_ps = large["sales_per_sqft_usd"].mean()
lrg_est_ps = large_established["sales_per_sqft_usd"].mean()

space_gain = (large["sq_ft"].mean() / standard["sq_ft"].mean() - 1) * 100
sales_gain = (
    large["annual_sales_musd"].mean() / standard["annual_sales_musd"].mean() - 1
) * 100

GREY = "#9E9E9E"
STRONG = "#C0392B"
DARK = "#333333"

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.15, 1], "wspace": 0.28}
)
fig.patch.set_facecolor("white")

fig.suptitle(
    "Large stores sell far less per square foot than standard stores",
    x=0.07, y=0.97, ha="left", va="top",
    fontsize=17, fontweight="bold", color=DARK,
)
fig.text(
    0.07, 0.905,
    "Large stores take more in total, but not enough to justify their extra space.",
    ha="left", va="top", fontsize=11.5, color="#555555",
)

# --- Left panel: sales per sq ft ---
x = [0, 1]
vals = [std_ps, lrg_ps]
ax1.bar(x, vals, width=0.55, color=[GREY, STRONG], edgecolor="none")

ax1.set_title("Annual sales per sq ft", loc="left", fontsize=12,
              fontweight="bold", color=DARK, pad=10)
ax1.set_ylabel("$ per sq ft per year", fontsize=10.5, color=DARK)
ax1.set_xticks(x)
ax1.set_xticklabels(
    [f"Standard\n({len(standard)} stores)", f"Large\n({len(large)} stores)"],
    fontsize=11, color=DARK,
)
ax1.set_ylim(0, 720)
ax1.set_yticks([0, 200, 400, 600])
ax1.tick_params(axis="y", labelsize=9.5, length=0)
ax1.tick_params(axis="x", length=0)
ax1.yaxis.grid(True, color="#E6E6E6", linewidth=0.8)
ax1.set_axisbelow(True)
for s in ["top", "right", "left"]:
    ax1.spines[s].set_visible(False)
ax1.spines["bottom"].set_color("#CCCCCC")

ax1.text(0, std_ps + 18, f"${std_ps:,.0f}", ha="center", va="bottom",
         fontsize=15, fontweight="bold", color=DARK)
ax1.text(1, lrg_ps + 18, f"${lrg_ps:,.0f}", ha="center", va="bottom",
         fontsize=15, fontweight="bold", color=STRONG)

# Caveat marker: large stores excluding 2025-26 openings
ax1.hlines(lrg_est_ps, xmin=0.62, xmax=1.38, color=DARK,
           linestyles="--", linewidth=1.6)
ax1.text(
    1, lrg_est_ps + 52,
    f"Large, pre-2025 only:\n${lrg_est_ps:,.0f}",
    ha="center", va="bottom", fontsize=9.5, color=DARK, linespacing=1.25,
)

# --- Right panel: more sales, but far more space ---
cats = ["Floor space", "Annual sales"]
gains = [space_gain, sales_gain]
ypos = [1, 0]
ax2.barh(ypos, gains, height=0.45, color=[GREY, STRONG], edgecolor="none")

ax2.set_title("Large vs. standard store", loc="left", fontsize=12,
              fontweight="bold", color=DARK, pad=10)
ax2.set_xlabel("% more than a standard store", fontsize=10.5, color=DARK)
ax2.set_yticks(ypos)
ax2.set_yticklabels(cats, fontsize=11, color=DARK)
ax2.set_xlim(0, 108)
ax2.set_xticks([0, 50, 100])
ax2.tick_params(axis="x", labelsize=9.5, length=0)
ax2.tick_params(axis="y", length=0)
ax2.xaxis.grid(True, color="#E6E6E6", linewidth=0.8)
ax2.set_axisbelow(True)
for s in ["top", "right", "left"]:
    ax2.spines[s].set_visible(False)
ax2.spines["bottom"].set_color("#CCCCCC")

for y, v, c in zip(ypos, gains, [DARK, STRONG]):
    ax2.text(v + 3, y, f"+{v:.0f}%", ha="left", va="center",
             fontsize=14, fontweight="bold", color=c)

ax2.text(
    0.98, 0.06,
    f"${large['annual_sales_musd'].mean():.1f}m vs "
    f"${standard['annual_sales_musd'].mean():.1f}m\naverage annual sales",
    transform=ax2.transAxes, ha="right", va="bottom",
    fontsize=9.5, color="#555555", linespacing=1.3,
)

fig.text(
    0.07, 0.02,
    "Caveat: 4 of the 11 large stores opened in 2025–26 and are still building trade.\n"
    "Excluding them (dashed line) does not close the gap. Averages across stores in each format.",
    ha="left", va="bottom", fontsize=8.5, color="#777777", linespacing=1.35,
)

fig.subplots_adjust(left=0.07, right=0.97, top=0.83, bottom=0.13)
