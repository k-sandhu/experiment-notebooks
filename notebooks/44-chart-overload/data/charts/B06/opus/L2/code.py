import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

df = pd.read_csv("data.csv")

std = df[df["format"] == "standard"]
large = df[df["format"] == "large"]
large_est = large[large["opened_year"] <= 2024]   # trading for at least a full year
large_new = large[large["opened_year"] >= 2025]   # still building up trade

std_mean = std["sales_per_sqft_usd"].mean()
large_est_mean = large_est["sales_per_sqft_usd"].mean()
std_min = std["sales_per_sqft_usd"].min()

GREY = "#9a9a9a"
RED = "#c8102e"

fig, ax = plt.subplots(figsize=(10, 6))

# Standard stores: context, in grey
ax.scatter(std["sq_ft"], std["sales_per_sqft_usd"], s=55, color=GREY,
           edgecolor="white", linewidth=0.6, zorder=3)

# Established large stores: the message, in strong colour
ax.scatter(large_est["sq_ft"], large_est["sales_per_sqft_usd"], s=75, color=RED,
           edgecolor="white", linewidth=0.6, zorder=4)

# New large stores: same colour, hollow, because they are still ramping up
ax.scatter(large_new["sq_ft"], large_new["sales_per_sqft_usd"], s=75,
           facecolor="white", edgecolor=RED, linewidth=1.5, zorder=4)

# Average lines, labelled directly
ax.hlines(std_mean, std["sq_ft"].min() - 800, std["sq_ft"].max() + 800,
          color="#555555", linestyle="--", linewidth=1.2, zorder=2)
ax.text(std["sq_ft"].min() - 800, std_mean + 12,
        f"Standard stores average ${std_mean:,.0f}", color="#444444",
        fontsize=11, fontweight="bold", va="bottom")

ax.hlines(large_est_mean, large["sq_ft"].min() - 800, large["sq_ft"].max() + 800,
          color=RED, linestyle="--", linewidth=1.2, zorder=2)
ax.text(large["sq_ft"].max() + 800, large_est_mean + 12,
        f"Established large stores\naverage ${large_est_mean:,.0f}",
        color=RED, fontsize=11, fontweight="bold", ha="right", va="bottom")

# Group labels
ax.text(std["sq_ft"].mean(), 455, f"Standard\n({len(std)} stores)",
        color="#555555", fontsize=10.5, ha="center", va="top")
ax.annotate(f"Large, opened 2025–26 ({len(large_new)} stores)\nstill building up trade",
            xy=(large_new["sq_ft"].iloc[0], large_new["sales_per_sqft_usd"].iloc[0]),
            xytext=(33500, 345), color=RED, fontsize=10, va="center",
            arrowprops=dict(arrowstyle="-", color=RED, linewidth=0.8))

# Caveat that changes the reading
ax.text(0.0, -0.16,
        f"Large stores already sit in bigger catchments (85k–140k people within 15 min vs 30k–90k) "
        f"and still sell less per sq ft.\nEstablished = opened 2024 or earlier. "
        f"Weakest standard store: ${std_min:,.0f}/sq ft.",
        transform=ax.transAxes, fontsize=9, color="#555555", va="top")

# Axes and title
ax.set_xlim(15000, 57500)
ax.set_ylim(300, 760)
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"${y:,.0f}"))
ax.set_xlabel("Selling floor area (sq ft)", fontsize=10.5, color="#333333")
ax.set_ylabel("Annual sales per sq ft (US$)", fontsize=10.5, color="#333333")
ax.tick_params(colors="#555555", labelsize=10)
for side in ["top", "right"]:
    ax.spines[side].set_visible(False)
for side in ["left", "bottom"]:
    ax.spines[side].set_color("#bbbbbb")
ax.grid(axis="y", color="#eeeeee", zorder=0)

fig.suptitle("Every established large store sells less per sq ft than our weakest standard store",
             x=0.06, ha="left", fontsize=14, fontweight="bold", y=0.97)
ax.set_title("Annual sales per square foot, by store, last 12 months",
             loc="left", fontsize=10.5, color="#555555", pad=10)

fig.subplots_adjust(left=0.1, right=0.97, top=0.86, bottom=0.2)
