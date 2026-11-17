import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data.csv", parse_dates=["date"])
x = mdates.date2num(df["date"])
demand = df["actual_peak_mw"].to_numpy(dtype=float)
cap = df["available_capacity_mw"].to_numpy(dtype=float)
cap40 = cap + 40

RED = "#c62828"
GREY = "#9e9e9e"
DARK = "#424242"

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(top=0.80, bottom=0.15, left=0.08, right=0.84)

# Context: daily peak demand
ax.plot(x, demand, color=GREY, lw=1.6, zorder=3)

# Capacity today, and capacity with the proposed extra 40 MW
ax.plot(x, cap, drawstyle="steps-mid", color=DARK, lw=1.8, zorder=2)
ax.plot(x, cap40, drawstyle="steps-mid", color=DARK, lw=1.3, ls="--", zorder=2)

# Shortfalls: light = covered by the extra 40 MW, dark = still short with it
ax.fill_between(x, cap, demand, where=demand > cap, interpolate=True,
                color=RED, alpha=0.25, lw=0, zorder=1)
ax.fill_between(x, cap40, demand, where=demand > cap40, interpolate=True,
                color=RED, alpha=0.95, lw=0, zorder=4)

# Highlight the worst day
i_max = int(np.argmax(demand))
ax.plot(x[i_max], demand[i_max], "o", color=RED, ms=6, zorder=5)
ax.annotate(
    "14 Jan: 1,012 MW at \u221229 \u00b0C\n"
    "62 MW above capacity even with +40 MW\n"
    "(still 12 MW short with Unit 3 back in service)",
    xy=(x[i_max], demand[i_max]), xytext=(x[i_max] + 8, 935),
    ha="left", va="top", fontsize=10, color=RED, fontweight="bold",
    arrowprops=dict(arrowstyle="-", color=RED, lw=1))

# Unit 3 outage
i_out = int(np.where(df["date"] == pd.Timestamp("2026-01-10"))[0][0])
ax.annotate("Unit 3 (50 MW) out\n10\u201316 Jan",
            xy=(x[i_out] + 0.5, 910), xytext=(x[i_out] - 16, 870),
            ha="left", va="top", fontsize=9.5, color=DARK,
            arrowprops=dict(arrowstyle="-", color=DARK, lw=0.8))

# Direct line labels at the right edge
xe = x[-1] + 1.5
ax.text(xe, cap40[-1], "Capacity + 40 MW\n(1,000 MW)", va="center", fontsize=10, color=DARK)
ax.text(xe, cap[-1] - 8, "Available capacity\n(960 MW)", va="center", fontsize=10, color=DARK)
ax.text(xe, demand[-1], "Actual daily\npeak demand", va="center", fontsize=10, color="#757575")

# Axes styling
ax.set_xlim(x[0] - 1, x[-1] + 1)
ax.set_ylim(550, 1060)
ax.set_ylabel("Daily peak demand (MW)", fontsize=10)
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="y", color="#e0e0e0", lw=0.8)
ax.set_axisbelow(True)
ax.tick_params(labelsize=9.5)

# Title (the message) and subtitle
fig.text(0.01, 0.975,
         "An extra 40 MW would not have covered last winter's worst day:\n"
         "demand hit 1,012 MW in the \u221229 \u00b0C cold snap",
         fontsize=15, fontweight="bold", va="top", ha="left")
fig.text(0.01, 0.855,
         "Daily peak demand vs available capacity, Dec 2025 \u2013 Feb 2026.  "
         "Light red: shortfall the extra 40 MW would cover.  Dark red: shortfall remaining.",
         fontsize=9.5, color="#555555", va="top", ha="left")

# Caveat that changes how to read the risk
fig.text(0.01, 0.025,
         "Caveat: the day-ahead forecast under-predicts very cold days (by ~5% below \u221215 \u00b0C; "
         "93 MW on 14 Jan), so shortfalls of this size may not be visible a day ahead.",
         fontsize=9, color="#555555", style="italic", ha="left", va="bottom")
