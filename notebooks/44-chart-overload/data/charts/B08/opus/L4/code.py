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
MUTED = "#555555"

# Worst day and its shortfall in three cases
i_max = int(np.argmax(demand))
d_max = demand[i_max]
full_cap = cap.max()                           # 960 MW with Unit 3 running
short_actual = d_max - cap[i_max]              # Unit 3 out, no extra capacity
short_plus40 = d_max - (cap[i_max] + 40)       # Unit 3 out, +40 MW
short_plus40_full = d_max - (full_cap + 40)    # Unit 3 running, +40 MW

fig = plt.figure(figsize=(10, 6))
axL = fig.add_axes([0.07, 0.16, 0.56, 0.60])
axR = fig.add_axes([0.70, 0.16, 0.27, 0.60])

# ---------- Left panel: the season, for context ----------
axL.plot(x, demand, color=GREY, lw=1.4, zorder=3)
axL.plot(x, cap, drawstyle="steps-mid", color=DARK, lw=1.8, zorder=2)
axL.plot(x, cap40, drawstyle="steps-mid", color=DARK, lw=1.2, ls="--", zorder=2)

over = demand > cap
axL.fill_between(x, cap, demand, where=over, interpolate=True,
                 color=RED, alpha=0.85, lw=0, zorder=4)
axL.plot(x[i_max], d_max, "o", color=RED, ms=6, zorder=5)
axL.text(x[i_max] - 2.5, 1032, f"14 Jan, \u221229 \u00b0C: {d_max:,.0f} MW",
         ha="right", va="center", fontsize=9.5, color=RED, fontweight="bold")

axL.text(x[i_max] + 5, 918,
         "Demand above capacity on 4 days, 12\u201315 Jan\n"
         "(Unit 3, 50 MW, out for repair 10\u201316 Jan)",
         ha="left", va="top", fontsize=9, color=DARK)

# Direct line labels
axL.text(x[-1], 1003, "Capacity + 40 MW: 1,000 MW", ha="right", va="bottom",
         fontsize=9, color=DARK)
axL.text(x[-1], 963, "Available capacity: 960 MW", ha="right", va="bottom",
         fontsize=9, color=DARK)
axL.text(x[-1], 548, "Daily peak demand", ha="right", va="bottom",
         fontsize=9, color="#757575")

axL.set_xlim(x[0] - 1, x[-1] + 1)
axL.set_ylim(540, 1060)
axL.set_ylabel("MW", fontsize=10)
axL.xaxis.set_major_locator(mdates.MonthLocator())
axL.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
axL.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
for s in ("top", "right"):
    axL.spines[s].set_visible(False)
axL.grid(axis="y", color="#e6e6e6", lw=0.8)
axL.set_axisbelow(True)
axL.tick_params(labelsize=9)
axL.set_title("Daily peak demand vs capacity, Dec 2025 \u2013 Feb 2026",
              loc="left", fontsize=10.5, color=DARK, pad=8)

# ---------- Right panel: the decision ----------
cases = [
    ("As it happened (Unit 3 out)", short_actual, GREY),
    ("With +40 MW, Unit 3 out", short_plus40, RED),
    ("With +40 MW, Unit 3 running", short_plus40_full, RED),
]
ypos = [2, 1, 0]
for (label, val, col), y in zip(cases, ypos):
    axR.barh(y, val, height=0.42, color=col, zorder=2)
    axR.text(0, y + 0.27, label, ha="left", va="bottom", fontsize=9, color=DARK)
    axR.text(val + 2.5, y, f"{val:,.0f} MW", ha="left", va="center",
             fontsize=10, fontweight="bold", color=col if col == RED else DARK)

axR.set_xlim(0, 130)
axR.set_ylim(-0.45, 2.85)
axR.set_yticks([])
axR.set_xlabel("MW short of peak demand", fontsize=9.5)
for s in ("top", "right", "left"):
    axR.spines[s].set_visible(False)
axR.grid(axis="x", color="#e6e6e6", lw=0.8)
axR.set_axisbelow(True)
axR.tick_params(labelsize=9)
axR.set_title("Shortfall on 14 Jan", loc="left", fontsize=10.5,
              color=DARK, pad=8)

# ---------- Title and caveat ----------
fig.text(0.01, 0.975,
         "An extra 40 MW would not have covered last winter's worst day",
         fontsize=15, fontweight="bold", va="top", ha="left")
fig.text(0.01, 0.905,
         f"At \u221229 \u00b0C on 14 Jan, demand ({d_max:,.0f} MW) was still "
         f"{short_plus40_full:,.0f} MW above capacity + 40 MW, even with every unit "
         "running. Last winter the gap was met with emergency imports.",
         fontsize=10, color=MUTED, va="top", ha="left", wrap=True)

fig.text(0.01, 0.02,
         "Caveat: the day-ahead forecast under-predicts very cold days (~5% below "
         "\u221215 \u00b0C; 93 MW on 14 Jan), so a shortfall like this may not be "
         "flagged a day ahead.",
         fontsize=8.8, color=MUTED, style="italic", ha="left", va="bottom")
