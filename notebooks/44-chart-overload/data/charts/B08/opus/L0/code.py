import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data.csv", parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)

over = df[df["actual_peak_mw"] > df["available_capacity_mw"]]
outage_start, outage_end = pd.Timestamp("2026-01-10"), pd.Timestamp("2026-01-16")
pk = df.loc[df["actual_peak_mw"].idxmax()]

fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(10, 6), sharex=True,
    gridspec_kw={"height_ratios": [3, 1.2], "hspace": 0.08}
)

c_actual, c_fcst, c_cap, c_over = "#1f4e79", "#8a8a8a", "#c0392b", "#c0392b"
half = pd.Timedelta(hours=12)

# --- Top panel: demand vs capacity ---
for ax in (ax1, ax2):
    ax.axvspan(outage_start - half, outage_end + half, color="#f2d7d5", alpha=0.5, lw=0, zorder=0)

ax1.step(df["date"], df["available_capacity_mw"], where="mid", color=c_cap, lw=1.8,
         label="Available capacity")
ax1.plot(df["date"], df["forecast_peak_mw"], color=c_fcst, lw=1.3, ls="--",
         label="Day-ahead forecast")
ax1.plot(df["date"], df["actual_peak_mw"], color=c_actual, lw=1.8, label="Actual peak demand")
ax1.scatter(over["date"], over["actual_peak_mw"], color=c_over, s=36, zorder=5,
            label="Demand above capacity")

ax1.annotate(f"Winter high: {pk['actual_peak_mw']:,.0f} MW on 14 Jan\n"
             f"forecast was {pk['forecast_peak_mw']:,.0f} MW",
             xy=(pk["date"], pk["actual_peak_mw"]),
             xytext=(pk["date"] + pd.Timedelta(days=6), 985),
             fontsize=9, color="#333333", va="center",
             arrowprops=dict(arrowstyle="-", color="#666666", lw=0.8))

ax1.text(outage_start - pd.Timedelta(days=1), 900,
         "Unit 3 out (−50 MW)\n10–16 Jan", ha="right", va="top", fontsize=8.5, color=c_cap)

ax1.set_ylabel("MW")
ax1.set_ylim(560, 1050)
ax1.legend(loc="upper left", fontsize=8.5, frameon=False, ncol=2)
ax1.set_title("Peak demand broke through capacity on 12–15 January as a deep cold snap "
              "coincided with the Unit 3 outage",
              fontsize=11.5, loc="left", pad=22)
ax1.text(0, 1.015,
         "Forecast under-shot on the coldest days: on the 7 days with lows below −15 °C, "
         "actual peak ran 5.3% (≈47 MW) above forecast",
         transform=ax1.transAxes, fontsize=9, color="#555555")

# --- Bottom panel: minimum temperature ---
cold = df["min_temp_c"] < -15
ax2.bar(df["date"], df["min_temp_c"], width=0.8,
        color=np.where(cold, "#2e86c1", "#aed6f1"))
ax2.axhline(-15, color="#2e86c1", lw=0.8, ls=":")
ax2.text(df["date"].iloc[-1] + pd.Timedelta(days=1), -15, "−15 °C",
         fontsize=8, color="#2e86c1", va="center")
ax2.axhline(0, color="#999999", lw=0.6)
ax2.set_ylabel("Daily low, °C")
ax2.set_ylim(-32, 9)

ax2.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
ax2.set_xlim(df["date"].iloc[0] - pd.Timedelta(days=1), df["date"].iloc[-1] + pd.Timedelta(days=1))

for ax in (ax1, ax2):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", lw=0.7)
    ax.set_axisbelow(True)

fig.subplots_adjust(left=0.08, right=0.95, top=0.88, bottom=0.08)
