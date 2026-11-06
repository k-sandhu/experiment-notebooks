import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

df = pd.read_csv("data.csv", parse_dates=["date"])
dates = df["date"]
act = df["actual_peak_mw"]
cap = df["available_capacity_mw"]
opt = cap + 40  # capacity with the proposed extra 40 MW

C_DEMAND = "#1f4e79"
C_CAP = "#444444"
C_OPT = "#2a9d4b"
C_SHORT = "#c0392b"

fig, ax = plt.subplots(figsize=(10, 6))

# Unit 3 outage window
ax.axvspan(pd.Timestamp("2026-01-09 12:00"), pd.Timestamp("2026-01-16 12:00"),
           color="grey", alpha=0.12, lw=0)
ax.text(pd.Timestamp("2026-01-13"), 1050, "Unit 3 out\n(−50 MW)", ha="center",
        va="top", fontsize=9, color="#555")

# Lines
ax.plot(dates, act, color=C_DEMAND, lw=1.6, zorder=3)
ax.step(dates, cap, where="mid", color=C_CAP, lw=2, zorder=2)
ax.step(dates, opt, where="mid", color=C_OPT, lw=2, ls="--", zorder=2)

# Shortfall days
short = act > cap
ax.vlines(dates[short], cap[short], act[short], color=C_SHORT, lw=5, zorder=4)
ax.scatter(dates[short], act[short], color=C_SHORT, s=28, zorder=5)

# Direct labels on the right
x_end = dates.iloc[-1] + pd.Timedelta(days=1.5)
ax.text(x_end, 960, "Available capacity: 960 MW", va="center", fontsize=9.5,
        color=C_CAP, fontweight="bold")
ax.text(x_end, 1003, "With +40 MW: 1,000 MW", va="center", fontsize=9.5,
        color=C_OPT, fontweight="bold")
ax.text(x_end, act.iloc[-1], "Daily peak demand", va="center", fontsize=9.5,
        color=C_DEMAND, fontweight="bold")

# Key annotation: 14 Jan peak
pk = df.loc[act.idxmax()]
ax.annotate("14 Jan: 1,012 MW\nexceeds +40 MW option by 62 MW\n(by 12 MW even with Unit 3 running)",
            xy=(pk["date"], pk["actual_peak_mw"]),
            xytext=(pd.Timestamp("2025-12-03"), 1015),
            fontsize=10, color=C_SHORT, va="center",
            arrowprops=dict(arrowstyle="->", color=C_SHORT, lw=1.2,
                            connectionstyle="arc3,rad=-0.15"))

ax.text(pd.Timestamp("2026-01-22"), 905,
        "Red = demand above capacity, 12–15 Jan\n(covered by emergency imports, up to 126 MW)\n"
        "With +40 MW: 4 shortfall days → 2",
        fontsize=9, color=C_SHORT, va="center")

# Axes styling
ax.set_ylim(560, 1060)
ax.set_xlim(dates.iloc[0] - pd.Timedelta(days=1), dates.iloc[-1] + pd.Timedelta(days=22))
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.set_ylabel("Peak demand / capacity (MW)")
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="y", color="#e5e5e5", lw=0.8)
ax.set_axisbelow(True)

# Title and footnote
fig.text(0.01, 0.97, "An extra 40 MW would have shrunk, not removed, January's capacity shortfall",
         fontsize=14, fontweight="bold", ha="left", va="top")
fig.text(0.01, 0.925, "Brightwater Electric daily peak demand vs. available capacity, 1 Dec 2025 – 28 Feb 2026",
         fontsize=10.5, color="#555", ha="left", va="top")
fig.text(0.01, 0.015,
         "Forecast risk: on the 7 days below −15 °C, actual peak beat the day-ahead forecast by ~47 MW (5.3%) "
         "on average; on 14 Jan the forecast was 919 MW.",
         fontsize=8.5, color="#555", ha="left", va="bottom")

fig.tight_layout(rect=(0, 0.04, 1, 0.9))
