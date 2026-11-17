import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

RED = "#C1272D"
GREY = "#8A8A8A"
DARK = "#333333"

df = pd.read_csv("data.csv", parse_dates=["date"])
df = df.sort_values("date")

full_capacity = df["available_capacity_mw"].max()   # 960 MW
proposed_capacity = full_capacity + 40              # 1,000 MW

exceeded = df["actual_peak_mw"] > df["available_capacity_mw"]
peak_row = df.loc[df["actual_peak_mw"].idxmax()]
outage = df[df["available_capacity_mw"] < full_capacity]
outage_start = outage["date"].min()
outage_end = outage["date"].max()

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.08, right=0.98, top=0.82, bottom=0.18)

# Unit 3 outage period (context)
ax.axvspan(
    outage_start - pd.Timedelta(hours=12),
    outage_end + pd.Timedelta(hours=12),
    color=DARK, alpha=0.07, zorder=0,
)
ax.text(
    outage_start + (outage_end - outage_start) / 2, 55,
    "Unit 3 out\n10–16 Jan",
    ha="center", va="bottom", fontsize=8.5, color=DARK,
)

# Daily actual peak demand (context, grey)
ax.plot(
    df["date"], df["actual_peak_mw"],
    color=GREY, linewidth=1.5, marker="o", markersize=2.8, zorder=2,
)
ax.text(
    pd.Timestamp("2025-12-04"), 585, "Daily actual peak",
    fontsize=9, color=DARK,
)

# Capacity available that day (960 MW, dipping to 910 MW during the outage)
ax.step(
    df["date"], df["available_capacity_mw"], where="mid",
    color=DARK, linewidth=1.8, zorder=3,
)
ax.text(
    pd.Timestamp("2025-12-02"), 930,
    f"Capacity available that day ({full_capacity:,.0f} MW; 910 MW during outage)",
    fontsize=9, color=DARK,
)

# Proposed capacity: full fleet + 40 MW
ax.axhline(proposed_capacity, color=DARK, linewidth=1.5, linestyle="--", zorder=3)
ax.text(
    pd.Timestamp("2025-12-02"), proposed_capacity + 15,
    f"Full capacity + 40 MW ({proposed_capacity:,.0f} MW)",
    fontsize=9, color=DARK,
)

# Days that exceeded the capacity available that day (the message, red)
ax.scatter(
    df.loc[exceeded, "date"], df.loc[exceeded, "actual_peak_mw"],
    s=75, color=RED, edgecolor="white", linewidth=1.0, zorder=4,
)

# The one number that carries the decision
ax.annotate(
    f"{peak_row['date']:%d %b}: {peak_row['actual_peak_mw']:,.0f} MW\n"
    f"{peak_row['actual_peak_mw'] - proposed_capacity:,.0f} MW above full capacity + 40 MW",
    xy=(peak_row["date"], peak_row["actual_peak_mw"]),
    xytext=(peak_row["date"] + pd.Timedelta(days=13), 1055),
    fontsize=10, color=RED, fontweight="bold", va="center",
    arrowprops=dict(arrowstyle="-", color=RED, linewidth=1.2),
)

# Title states the decision-relevant message
ax.set_title(
    "40 MW extra would still have left the highest winter peak short",
    loc="left", fontsize=16, fontweight="bold", color=DARK, pad=38,
)
ax.text(
    0, 1.045,
    "Daily peak demand, 1 Dec 2025–28 Feb 2026. "
    "Red days exceeded the capacity available that day.",
    transform=ax.transAxes, fontsize=10, color="#555555", va="bottom",
)

# Caveat that changes how the chart should be read
fig.text(
    0.08, 0.025,
    "Caveat: Unit 3 (50 MW) was out 10–16 Jan, so capacity was 910 MW, not 960 MW. "
    "At full 960 MW, only 14 Jan would have exceeded capacity.\n"
    "Buying 40 MW would cut the worst shortfall, but not remove the need for "
    "emergency imports on a day like 14 Jan.",
    fontsize=8.5, color="#555555", va="bottom",
)

ax.set_ylabel("Peak demand (MW)", fontsize=10, color=DARK)
ax.set_xlim(df["date"].min() - pd.Timedelta(days=1),
            df["date"].max() + pd.Timedelta(days=1))
ax.set_ylim(0, 1100)
ax.set_yticks(np.arange(0, 1101, 200))
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
ax.tick_params(labelsize=9, colors=DARK)
ax.grid(axis="y", color="#E5E5E5", linewidth=0.8)
ax.set_axisbelow(True)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color("#B0B0B0")
