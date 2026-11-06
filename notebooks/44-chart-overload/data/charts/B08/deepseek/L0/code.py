import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data.csv", parse_dates=["date"])

fig, (ax1, ax2) = plt.subplots(
    2, 1,
    figsize=(10, 6),
    sharex=True,
    gridspec_kw={"height_ratios": [3, 1]}
)

# --- Top panel: peak demand, forecast, and available capacity ---
ax1.plot(
    df["date"], df["actual_peak_mw"],
    color="black", linewidth=1.5, marker="o", markersize=3,
    label="Actual peak demand"
)
ax1.plot(
    df["date"], df["forecast_peak_mw"],
    color="tab:blue", linewidth=1.3, linestyle="--", marker="o", markersize=2,
    label="Forecast peak demand"
)
ax1.step(
    df["date"], df["available_capacity_mw"],
    where="mid", color="tab:red", linewidth=1.8,
    label="Available capacity"
)

# Highlight Unit 3 outage period
outage_start = pd.Timestamp("2026-01-10")
outage_end = pd.Timestamp("2026-01-16")
ax1.axvspan(
    outage_start, outage_end,
    color="gray", alpha=0.15,
    label="Unit 3 outage"
)

# Mark days when demand exceeded available capacity
exceed = df["actual_peak_mw"] > df["available_capacity_mw"]
ax1.scatter(
    df.loc[exceed, "date"],
    df.loc[exceed, "actual_peak_mw"],
    color="red", s=60, zorder=5,
    label="Demand > available capacity"
)

# Annotate the winter peak
peak_idx = df["actual_peak_mw"].idxmax()
peak_row = df.loc[peak_idx]
ax1.annotate(
    f"Winter peak\n{peak_row['actual_peak_mw']:.0f} MW",
    xy=(peak_row["date"], peak_row["actual_peak_mw"]),
    xytext=(10, -25),
    textcoords="offset points",
    arrowprops=dict(arrowstyle="->", color="black", linewidth=0.8),
    fontsize=8
)

ax1.set_ylabel("Peak demand / capacity (MW)")
ax1.set_title("Peak electricity demand, forecast, and available capacity")
ax1.legend(loc="lower left", fontsize=8, ncol=2)
ax1.grid(True, alpha=0.25)

# --- Bottom panel: imports and residential share ---
ax2.bar(
    df["date"], df["imports_mw"],
    color="tab:orange", alpha=0.7, width=0.8,
    label="Peak imports"
)
ax2.set_ylabel("Imports (MW)")
ax2.set_xlabel("Date")
ax2.grid(True, alpha=0.25)

ax2_twin = ax2.twinx()
ax2_twin.plot(
    df["date"], df["residential_share_pct"],
    color="tab:green", linewidth=1.3,
    label="Residential share"
)
ax2_twin.set_ylabel("Residential share (%)", color="tab:green")
ax2_twin.tick_params(axis="y", labelcolor="tab:green")

lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8)

# Date formatting
ax2.xaxis.set_major_locator(mdates.MonthLocator())
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax2.xaxis.set_minor_locator(mdates.DayLocator(interval=7))
fig.autofmt_xdate(rotation=30)

plt.tight_layout()
