import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data.csv", parse_dates=["date"])
d = df["date"]
actual = df["actual_peak_mw"]
fcst = df["forecast_peak_mw"]
cap = df["available_capacity_mw"]

ACC = "#c8102e"   # the one strong colour
DARK = "#4d4d4d"
GREY = "#9a9a9a"

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(top=0.84, left=0.08, right=0.97, bottom=0.08)

# Available capacity (step down to 910 MW while Unit 3 was out)
ax.step(d, cap, where="mid", color=DARK, lw=1.8, zorder=3)

# What capacity would have been with Unit 3 running
out = cap < 960
half = pd.Timedelta(hours=12)
ax.hlines(960, d[out].min() - half, d[out].max() + half,
          colors=DARK, linestyles=":", lw=1.5, zorder=3)

# The 40 MW option under consideration
ax.axhline(1000, color=GREY, ls="--", lw=1, zorder=1)

# Forecast (context) and actual demand (message)
ax.plot(d, fcst, color=GREY, lw=1.3, zorder=2)
ax.plot(d, actual, color=ACC, lw=2.3, zorder=4)

# Shade demand above capacity
ax.fill_between(d, cap, actual, where=actual > cap, interpolate=True,
                color=ACC, alpha=0.25, lw=0, zorder=2)

# Mark the forecast miss on the 7 days below -15 °C
cold = df["min_temp_c"] < -15
ax.vlines(d[cold], fcst[cold], actual[cold], color=ACC, lw=2.5, alpha=0.45, zorder=3)
ax.scatter(d[cold], fcst[cold], s=18, color=GREY, zorder=5)

# Direct labels
ax.text(pd.Timestamp("2025-12-01"), 772, "Actual peak demand",
        color=ACC, fontsize=10, fontweight="bold")
ax.text(pd.Timestamp("2026-02-13"), 955, "Available capacity: 960 MW",
        color=DARK, fontsize=9, va="top")
ax.text(pd.Timestamp("2026-02-13"), 1004, "With +40 MW: 1,000 MW",
        color=GREY, fontsize=9, va="bottom")

# Key annotations
ax.annotate("14 Jan: 1,012 MW. Even with Unit 3 running (dotted line, 960 MW)\n"
            "this day was 52 MW over capacity, more than the 40 MW on offer.",
            xy=(pd.Timestamp("2026-01-14"), 1012),
            xytext=(pd.Timestamp("2025-12-02"), 1108),
            fontsize=9.5, color="black", va="top", ha="left",
            arrowprops=dict(arrowstyle="-", color=ACC, lw=1))

ax.annotate("12–15 Jan: demand above capacity on 4 days\n"
            "while Unit 3 (50 MW) was out, cutting capacity to 910 MW.\n"
            "Gap covered by emergency imports.",
            xy=(pd.Timestamp("2026-01-15"), 925),
            xytext=(pd.Timestamp("2026-01-21"), 922),
            fontsize=9.5, color="black", va="top", ha="left",
            arrowprops=dict(arrowstyle="-", color=ACC, lw=1))

ax.text(pd.Timestamp("2025-12-02"), 510,
        "Grey line = day-ahead forecast. On the 7 days below −15 °C (marked), actual peak\n"
        "demand beat the forecast by 47 MW (5.3%) on average.",
        fontsize=9.5, color=DARK, va="bottom", ha="left")

# Axes styling
ax.set_ylim(500, 1120)
ax.set_xlim(d.min() - pd.Timedelta(days=1), d.max() + pd.Timedelta(days=1))
ax.set_ylabel("Peak demand (MW)", fontsize=10)
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.grid(axis="y", color="#e6e6e6", lw=0.8, zorder=0)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
ax.spines["left"].set_color("#bbbbbb")
ax.spines["bottom"].set_color("#bbbbbb")
ax.tick_params(colors=DARK, labelsize=9)

# Title (the message) and subtitle
fig.text(0.08, 0.95,
         "Cold snaps push demand past capacity, and forecasts miss them by ~47 MW",
         fontsize=15, fontweight="bold", ha="left", va="top")
fig.text(0.08, 0.895,
         "Brightwater Electric daily peak demand vs. available capacity, 1 Dec 2025 – 28 Feb 2026 (MW)",
         fontsize=10.5, color=DARK, ha="left", va="top")
