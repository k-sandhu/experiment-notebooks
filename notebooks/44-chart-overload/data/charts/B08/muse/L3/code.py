import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

df = pd.read_csv("data.csv", parse_dates=["date"])

# Only the very cold days relevant to the capacity decision.
cold = (
    df[df["min_temp_c"] < -15]
    .sort_values("actual_peak_mw", ascending=False)
    .reset_index(drop=True)
)

RED = "#C1272D"
GREY = "#B8B8B8"
DARK = "#333333"

fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(cold))
exceeded_available = cold["actual_peak_mw"] > cold["available_capacity_mw"]
colours = [RED if exceeded else GREY for exceeded in exceeded_available]

ax.bar(x, cold["actual_peak_mw"], color=colours, width=0.62, zorder=2)

# Day-ahead forecast shown as a short dark tick on each bar.
for xi, forecast in zip(x, cold["forecast_peak_mw"]):
    ax.plot([xi - 0.31, xi + 0.31], [forecast, forecast],
            color=DARK, linewidth=3, zorder=5)

# Capacity lines, labelled directly.
ax.plot([-0.55, 6.55], [1000, 1000], color=DARK, linewidth=1.4,
        linestyle="--", zorder=4)
ax.text(6.55, 1012, "With +40 MW on offer: 1,000 MW",
        ha="right", va="bottom", fontsize=9, color=DARK,
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1.5))

ax.plot([-0.55, 6.55], [960, 960], color=DARK, linewidth=1.6, zorder=4)
ax.text(6.55, 972, "Full capacity with Unit 3: 960 MW",
        ha="right", va="bottom", fontsize=9, color=DARK,
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1.5))

# 910 MW applied only to the four January bars at the left.
ax.plot([-0.55, 3.55], [910, 910], color=DARK, linewidth=1.4,
        linestyle=":", zorder=4)
ax.text(3.55, 895, "Capacity while Unit 3 was out: 910 MW",
        ha="right", va="top", fontsize=9, color=DARK,
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.9, pad=1.5))

# Direct label for the forecast tick.
ax.annotate(
    "Day-ahead forecast",
    xy=(0.28, cold.loc[0, "forecast_peak_mw"]),
    xytext=(1.45, 1085),
    fontsize=9, color=DARK, ha="center",
    arrowprops=dict(arrowstyle="-", color=DARK, linewidth=1),
    bbox=dict(facecolor="white", edgecolor="none", alpha=0.9, pad=1.5),
)

# The one bar value that carries the decision.
ax.text(0, cold.loc[0, "actual_peak_mw"] + 22, "1,012 MW",
        ha="center", va="bottom", fontsize=11, fontweight="bold", color=RED)

ax.set_xticks(x)
ax.set_xticklabels(
    [f"{date:%d %b}\n{temp:.0f}°C"
     for date, temp in zip(cold["date"], cold["min_temp_c"])],
    fontsize=9,
)
ax.set_xlim(-0.6, 6.6)
ax.set_ylim(0, 1150)
ax.set_yticks([0, 250, 500, 750, 1000])
ax.set_ylabel("Peak demand (MW)", fontsize=10)
ax.grid(axis="y", color="#E3E3E3", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.tick_params(left=False)

over_full_capacity = int(cold["actual_peak_mw"].max() - 960)

fig.text(
    0.07, 0.96,
    "40 MW extra would not have covered the coldest day —\n"
    f"it beat full capacity by {over_full_capacity} MW",
    ha="left", va="top", fontsize=16, fontweight="bold", color="black",
)
fig.text(
    0.07, 0.855,
    "Actual peak demand on the 7 days below −15 °C. "
    "On those days demand averaged 47 MW (5.3%) above forecast.",
    ha="left", va="top", fontsize=10, color="#555555",
)
fig.text(
    0.07, 0.025,
    "Note: the 4 red bars (12–15 Jan) exceeded the 910 MW then available and needed emergency imports. "
    "Unit 3 (50 MW) was out 10–16 Jan;\nwith it running, only 14 Jan would have exceeded capacity.",
    ha="left", va="bottom", fontsize=8.5, color="#555555",
)

fig.subplots_adjust(left=0.07, right=0.98, top=0.79, bottom=0.16)
