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
DARK = "#444444"
RED = "#c8102e"

fig, ax = plt.subplots(figsize=(10, 6))

# Threshold: weakest standard store (the benchmark in the title)
ax.axhline(std_min, color="#777777", linestyle=":", linewidth=1.3, zorder=1)
ax.text(15500, std_min - 8, f"Weakest standard store: ${std_min:,.0f}",
        color=DARK, fontsize=10, va="top", ha="left")

# Standard stores: context, in grey
ax.scatter(std["sq_ft"], std["sales_per_sqft_usd"], s=55, color=GREY,
           edgecolor="white", linewidth=0.6, zorder=3)

# Established large stores: the message, in strong colour
ax.scatter(large_est["sq_ft"], large_est["sales_per_sqft_usd"], s=80, color=RED,
           edgecolor="white", linewidth=0.6, zorder=4)

# New large stores: hollow, because they are still ramping up
ax.scatter(large_new["sq_ft"], large_new["sales_per_sqft_usd"], s=75,
           facecolor="white", edgecolor=RED, linewidth=1.5, zorder=4)

# Average lines, labelled directly at their right-hand end
std_x0, std_x1 = std["sq_ft"].min() - 800, std["sq_ft"].max() + 800
ax.hlines(std_mean, std_x0, std_x1, color=DARK, linestyle="--", linewidth=1.3, zorder=2)
ax.text(std_x1 + 500, std_mean,
        f"Standard stores ({len(std)})\naverage ${std_mean:,.0f}",
        color=DARK, fontsize=11, fontweight="bold", va="center", ha="left")

lg_x0, lg_x1 = large["sq_ft"].min() - 800, large["sq_ft"].max() + 800
ax.hlines(large_est_mean, lg_x0, lg_x1, color=RED, linestyle="--", linewidth=1.3, zorder=2)
ax.text(lg_x1 + 500, large_est_mean,
        f"Established large\nstores ({len(large_est)})\naverage ${large_est_mean:,.0f}",
        color=RED, fontsize=11, fontweight="bold", va="center", ha="left")

# New large stores label, beside the hollow points
ax.text(lg_x1 + 500, large_new["sales_per_sqft_usd"].mean(),
        f"Large, opened\n2025–26 ({len(large_new)}):\nstill ramping up",
        color=RED, fontsize=10, va="center", ha="left")

# Caveat that changes the reading
ax.text(0.0, -0.15,
        "Large stores already sit in bigger catchments (85k–140k people within 15 min vs 30k–90k) "
        "and still sell less per sq ft.\nEstablished = opened 2024 or earlier.",
        transform=ax.transAxes, fontsize=9, color="#555555", va="top")

# Axes and title
ax.set_xlim(15000, 64000)
ax.set_ylim(300, 760)
ax.set_xticks(np.arange(15000, 60000, 5000))
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
