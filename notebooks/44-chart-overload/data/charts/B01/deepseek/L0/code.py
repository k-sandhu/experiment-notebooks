import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Load data
df = pd.read_csv("data.csv")
df["month"] = pd.to_datetime(df["month"], format="%Y-%m")
df = df.sort_values(["plan", "month"])

plans = ["Single", "Couple", "Family", "Vegetarian"]
colors = {
    "Single": "#1f77b4",
    "Couple": "#ff7f0e",
    "Family": "#d62728",
    "Vegetarian": "#2ca02c",
}

fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(10, 6), sharex=True, gridspec_kw={"height_ratios": [1.1, 1]}
)

for plan in plans:
    d = df[df["plan"] == plan]
    lw = 2.4 if plan == "Family" else 1.6
    ax1.plot(
        d["month"],
        d["active_subscribers"],
        marker="o",
        markersize=3.5,
        linewidth=lw,
        color=colors[plan],
        label=plan,
    )
    ax2.plot(
        d["month"],
        d["cancellation_rate_pct"],
        marker="o",
        markersize=3.5,
        linewidth=lw,
        color=colors[plan],
        label=plan,
    )

price_change = pd.Timestamp("2026-04-01")
sep_start = pd.Timestamp("2026-09-01")
oct_start = pd.Timestamp("2026-10-01")

for ax in (ax1, ax2):
    ax.axvline(price_change, color="0.35", linestyle="--", linewidth=1)
    ax.axvspan(sep_start, oct_start, color="0.85", alpha=0.35, zorder=0)
    ax.grid(axis="y", alpha=0.25)

ax1.set_ylabel("Active subscribers")
ax1.set_title("Active subscribers and cancellation rates by plan")
ax1.legend(loc="upper left", ncol=4, fontsize=8, frameon=False)
ax1.text(
    price_change,
    ax1.get_ylim()[1] * 0.96,
    " Family price\n $79→$89",
    va="top",
    ha="left",
    fontsize=8,
)

ax2.set_ylabel("Cancellation rate (%)")
ax2.set_xlabel("Month")
ax2.legend(loc="upper left", ncol=4, fontsize=8, frameon=False)
ax2.text(
    sep_start,
    ax2.get_ylim()[1] * 0.96,
    " Sep 2026\n partial",
    va="top",
    ha="left",
    fontsize=8,
    color="0.35",
)

ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
plt.setp(ax2.get_xticklabels(), rotation=45, ha="right")

fig.tight_layout()
