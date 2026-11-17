import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data.csv", parse_dates=["date"])
df = df.sort_values("date").reset_index(drop=True)

df["capacity_plus_40"] = df["available_capacity_mw"] + 40
df["excess_mw"] = df["actual_peak_mw"] - df["available_capacity_mw"]

over = df[df["excess_mw"] > 0].copy()
not_over = df[df["excess_mw"] <= 0]
worst = df.loc[df["actual_peak_mw"].idxmax()]
worst_excess = int(worst["excess_mw"])
worst_after_plus40 = int(worst["actual_peak_mw"] - worst["capacity_plus_40"])
full_capacity = int(df["available_capacity_mw"].max())
worst_after_plus40_full = int(worst["actual_peak_mw"] - (full_capacity + 40))
covered_by_40 = int((over["excess_mw"] <= 40).sum())

cold = df[df["min_temp_c"] < -15]
cold_forecast_miss = (cold["actual_peak_mw"] - cold["forecast_peak_mw"]).mean()

outage = df[df["available_capacity_mw"] < full_capacity]
outage_start = outage["date"].min()
outage_end = outage["date"].max()

plt.rcParams["font.family"] = "DejaVu Sans"

fig = plt.figure(figsize=(10, 6))
gs = fig.add_gridspec(1, 2, width_ratios=[2.65, 1.0], wspace=0.34)
ax = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
fig.subplots_adjust(left=0.07, right=0.98, top=0.80, bottom=0.23)

# ---- Headline: the conclusion, readable in a few seconds ----
fig.text(
    0.02, 0.97,
    "40 MW extra would NOT have covered last winter's worst peak",
    ha="left", va="top", fontsize=17, fontweight="bold", color="#111111",
)
fig.text(
    0.02, 0.915,
    "Brightwater Electric  |  Daily peak demand, 1 Dec 2025–28 Feb 2026 (90 days)",
    ha="left", va="top", fontsize=10.5, color="#444444",
)

# ---- Left panel: every day in context ----
ax.axvspan(
    outage_start - pd.Timedelta(hours=12),
    outage_end + pd.Timedelta(hours=12),
    color="#f4a261", alpha=0.18, lw=0, zorder=0,
)
ax.fill_between(df["date"], 550, df["actual_peak_mw"], color="#1f3a5f", alpha=0.08, lw=0)
ax.plot(df["date"], df["actual_peak_mw"], color="#1f3a5f", lw=2.2,
        label="Actual daily peak", zorder=3)
ax.step(df["date"], df["available_capacity_mw"], where="mid", color="#111111", lw=2.4,
        label="Available capacity", zorder=4)
ax.step(df["date"], df["capacity_plus_40"], where="mid", color="#2a9d8f", lw=2.0,
        linestyle="--", label="Capacity + proposed 40 MW", zorder=4)
ax.scatter(over["date"], over["actual_peak_mw"], s=78, color="#d62828",
           edgecolor="white", linewidth=1.1, zorder=5, label="Over capacity (4 days)")

ax.annotate(
    f"Worst day: {worst['date'].strftime('%d %b')} — {int(worst['actual_peak_mw']):,} MW\n"
    f"{worst_excess} MW over the {int(worst['available_capacity_mw'])} MW available",
    xy=(worst["date"], worst["actual_peak_mw"]),
    xytext=(0.40, 0.86), textcoords="axes fraction",
    fontsize=9.5, fontweight="bold", color="#8d0801", ha="left", va="center",
    bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="#d62828", alpha=0.95),
    arrowprops=dict(arrowstyle="->", color="#d62828", lw=1.6),
)

ax.text(
    outage_start + (outage_end - outage_start) / 2, 575,
    "Unit 3\noutage", ha="center", va="bottom", fontsize=8, color="#7f4f24",
)

ax.set_title("Only 4 of 90 days exceeded capacity —\nall in one cold snap during the outage",
             loc="left", fontsize=11.5, fontweight="bold", pad=10)
ax.set_ylabel("Peak demand / capacity (MW)", fontsize=10)
ax.set_ylim(550, 1070)
ax.set_xlim(df["date"].min() - pd.Timedelta(days=1), df["date"].max() + pd.Timedelta(days=1))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=14))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
ax.tick_params(axis="both", labelsize=9)
for label in ax.get_xticklabels():
    label.set_rotation(30)
    label.set_ha("right")
ax.grid(axis="y", color="#dddddd", lw=0.7)
ax.set_axisbelow(True)
ax.legend(loc="upper left", fontsize=8.5, framealpha=0.95)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

# ---- Right panel: the direct test of the 40 MW proposal ----
y = np.arange(len(over))
bar_colors = ["#2a9d8f" if e <= 40 else "#d62828" for e in over["excess_mw"]]
ax2.barh(y, over["excess_mw"], color=bar_colors, height=0.58)
ax2.axvline(40, color="#111111", lw=2.2, linestyle="--")
ax2.text(41.5, -0.72, "Proposed\n+40 MW", fontsize=9, fontweight="bold", va="center")

for yi, (_, row) in zip(y, over.iterrows()):
    ax2.text(row["excess_mw"] + 2.5, yi, f"{int(row['excess_mw'])} MW",
             va="center", fontsize=9.5, fontweight="bold",
             color="#8d0801" if row["excess_mw"] > 40 else "#146c60")

ax2.set_yticks(y)
ax2.set_yticklabels([d.strftime("%d %b") for d in over["date"]], fontsize=9.5)
ax2.invert_yaxis()
ax2.set_xlim(0, 125)
ax2.set_xlabel("MW over available capacity", fontsize=10)
ax2.set_title("Would +40 MW\nhave covered them?",
              loc="left", fontsize=11.5, fontweight="bold", pad=10)
ax2.tick_params(axis="x", labelsize=9)
ax2.grid(axis="x", color="#dddddd", lw=0.7)
ax2.set_axisbelow(True)
for spine in ["top", "right"]:
    ax2.spines[spine].set_visible(False)
ax2.text(0, 1.02, "Teal = covered by +40 MW   Red = still short",
         transform=ax2.transAxes, fontsize=8, color="#444444", ha="left", va="bottom")

# ---- Supporting context + decision takeaway ----
fig.text(
    0.02, 0.135,
    f"Context: on the other {len(not_over)} days the peak never exceeded "
    f"{int(not_over['actual_peak_mw'].max())} MW.  "
    f"On days below −15 °C the day-ahead forecast averaged {cold_forecast_miss:.0f} MW "
    f"below the actual peak, so the forecast understates cold-day risk.",
    ha="left", va="top", fontsize=8.5, color="#555555",
)

fig.text(
    0.5, 0.055,
    f"Takeaway: +40 MW would have covered {covered_by_40} of the 4 shortfalls, but left "
    f"{worst_after_plus40} MW uncovered on {worst['date'].strftime('%d %b')} during the outage\n"
    f"({worst_after_plus40_full} MW uncovered even at full {full_capacity} MW capacity). "
    f"It cuts the risk — emergency-import cover is still needed for the coldest day.",
    ha="center", va="center", fontsize=10, fontweight="bold", color="#111111",
    bbox=dict(boxstyle="round,pad=0.55", facecolor="#fff3cd", edgecolor="#b08900", lw=1.2),
)
