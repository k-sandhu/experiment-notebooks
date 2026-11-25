import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data.csv", parse_dates=["date"]).sort_values("date")
df["error_mw"] = df["actual_peak_mw"] - df["forecast_peak_mw"]
df["error_pct"] = 100 * df["error_mw"] / df["forecast_peak_mw"]
df["exceeds"] = df["actual_peak_mw"] > df["available_capacity_mw"]

cold = df[df["min_temp_c"] < -15]
mid = df[(df["min_temp_c"] >= -15) & (df["min_temp_c"] <= -3)]
mild = df[df["min_temp_c"] > -3]
mape = df["error_pct"].abs().mean()

peak = df.loc[df["actual_peak_mw"].idxmax()]
outage_start = pd.Timestamp("2026-01-10")
outage_end = pd.Timestamp("2026-01-16")

fig = plt.figure(figsize=(10, 6))
gs = fig.add_gridspec(2, 1, height_ratios=[1.3, 1.0], hspace=0.48)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])
fig.subplots_adjust(left=0.075, right=0.975, top=0.86, bottom=0.11)

fig.suptitle(
    "Winter peaks: the forecast missed the cold snap when capacity was already down",
    x=0.075, y=0.97, ha="left", fontsize=14, fontweight="bold",
)
fig.text(
    0.075, 0.925,
    "Actual demand beat the day-ahead forecast most in extreme cold, pushing the system above available capacity on 12-15 January.",
    ha="left", fontsize=9, color="#444444",
)

# --- Panel A: demand through the winter -------------------------------------
ax1.axvspan(outage_start, outage_end + pd.Timedelta(days=1),
            color="#999999", alpha=0.18, zorder=0)
ax1.text(outage_start + pd.Timedelta(days=3.5), 585,
         "Unit 3 out\n10-16 Jan\n960 -> 910 MW",
         ha="center", va="bottom", fontsize=7.5, color="#555555")

ax1.plot(df["date"], df["actual_peak_mw"], color="#0B2C54", lw=2,
         marker="o", ms=3, label="Actual peak", zorder=3)
ax1.plot(df["date"], df["forecast_peak_mw"], color="#E67E22", lw=1.6,
         ls="--", label="Day-ahead forecast", zorder=3)
ax1.step(df["date"], df["available_capacity_mw"], where="mid",
         color="#C0392B", lw=2, label="Available capacity", zorder=4)

ax1.fill_between(df["date"], df["actual_peak_mw"], df["available_capacity_mw"],
                 where=df["exceeds"], interpolate=True,
                 color="#C0392B", alpha=0.28, zorder=2)
exc = df[df["exceeds"]]
ax1.scatter(exc["date"], exc["actual_peak_mw"], s=105, facecolor="none",
            edgecolor="#C0392B", lw=2, zorder=5,
            label=f"Above capacity ({len(exc)} days)")

ax1.annotate(
    f"Winter maximum: {peak['actual_peak_mw']:.0f} MW\n"
    f"{peak['date']:%d %b}, min {peak['min_temp_c']:.0f}\u00b0C, "
    f"imports {peak['imports_mw']:.0f} MW",
    xy=(peak["date"], peak["actual_peak_mw"]),
    xytext=(peak["date"] + pd.Timedelta(days=9), 975),
    fontsize=8.5, fontweight="bold", color="#C0392B",
    arrowprops=dict(arrowstyle="->", color="#C0392B", lw=1.4),
)

ax1.set_title("A. Peak demand against capacity, December-February",
              loc="left", fontsize=11, fontweight="bold")
ax1.set_ylabel("Peak demand (MW)")
ax1.set_ylim(550, 1060)
ax1.grid(axis="y", alpha=0.3)
ax1.set_axisbelow(True)
ax1.xaxis.set_major_locator(mdates.DayLocator(interval=14))
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
ax1.legend(loc="upper left", ncol=4, fontsize=8, frameon=False)

# --- Panel B: why it happened - temperature-dependent forecast bias ---------
groups = [
    (cold, "#C0392B", f"Very cold: below -15\u00b0C (n={len(cold)})", -30.5, -15),
    (mid, "#5D6D7E", f"Cold: -15 to -3\u00b0C (n={len(mid)})", -15, -3),
    (mild, "#148F77", f"Mild: above -3\u00b0C (n={len(mild)})", -3, 7.5),
]
for data, color, label, xmin, xmax in groups:
    ax2.scatter(data["min_temp_c"], data["error_pct"], s=48, color=color,
                edgecolor="white", linewidth=0.6, alpha=0.92,
                label=label, zorder=3)
    mean_pct = data["error_pct"].mean()
    mean_mw = data["error_mw"].mean()
    ax2.plot([xmin, xmax], [mean_pct, mean_pct], color=color, lw=3, zorder=4)
    y_text = mean_pct + (0.7 if mean_pct >= 0 else -1.15)
    ax2.text((xmin + xmax) / 2, y_text,
             f"mean {mean_pct:+.1f}%  ({mean_mw:+.0f} MW)",
             ha="center", fontsize=8.5, fontweight="bold", color=color)

ax2.axhline(0, color="black", lw=1)
ax2.axvline(-15, color="grey", ls=":", lw=1.2)
ax2.axvline(-3, color="grey", ls=":", lw=1.2)
ax2.text(0.99, 0.96,
         f"All 90 days: mean |error| = {mape:.1f}%\n"
         "Above zero = forecast too low",
         transform=ax2.transAxes, ha="right", va="top", fontsize=8.5,
         bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                   edgecolor="#BBBBBB", alpha=0.95))

ax2.set_title("B. The average hides the risk: forecasts were far too low only in extreme cold",
              loc="left", fontsize=11, fontweight="bold")
ax2.set_xlabel("Daily minimum temperature (\u00b0C)")
ax2.set_ylabel("Forecast error\n(actual - forecast, %)")
ax2.set_xlim(-31, 8)
ax2.set_ylim(-4, 11.5)
ax2.grid(axis="y", alpha=0.3)
ax2.set_axisbelow(True)
ax2.legend(loc="lower left", fontsize=8, frameon=False)

fig.text(
    0.075, 0.015,
    "Shortfalls on 12-15 Jan were covered by imports. With Unit 3 running at 960 MW, only 14 Jan would have exceeded capacity.",
    ha="left", fontsize=8, color="#555555",
)
