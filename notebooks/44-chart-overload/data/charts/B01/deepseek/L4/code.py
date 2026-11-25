import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

# Read and prepare data
df = pd.read_csv("data.csv")
df["month"] = pd.to_datetime(df["month"], format="%Y-%m")
df = df.sort_values(["plan", "month"])

# September 2026 cancellation data covers only 1-14 Sep, so exclude it
# from the cancellation-rate chart.
cutoff = pd.Timestamp("2026-08-01")
df_rate = df[df["month"] <= cutoff].copy()

# Family monthly cancellation rate
family = (
    df_rate[df_rate["plan"] == "Family"]
    .set_index("month")["cancellation_rate_pct"]
    .sort_index()
)

# Combined cancellation rate for the other three plans, as context
other = (
    df_rate[df_rate["plan"] != "Family"]
    .groupby("month")[["cancellations", "active_subscribers"]]
    .sum()
)
other_rate = other["cancellations"] / other["active_subscribers"] * 100

# Pre- and post-price-rise averages for Family
pre_avg = family[
    (family.index >= pd.Timestamp("2025-10-01"))
    & (family.index <= pd.Timestamp("2026-03-01"))
].mean()
post_avg = family[
    (family.index >= pd.Timestamp("2026-04-01"))
    & (family.index <= pd.Timestamp("2026-08-01"))
].mean()

# Figure
fig, ax = plt.subplots(figsize=(10, 6))

# Context: other plans combined
ax.plot(
    other_rate.index,
    other_rate.values,
    color="#B0B0B0",
    linewidth=2.0,
    zorder=1,
)

# Highlight: Family plan
ax.plot(
    family.index,
    family.values,
    color="#C0392B",
    linewidth=3.0,
    marker="o",
    markersize=4,
    zorder=3,
)

# Price-rise date
price_rise = pd.Timestamp("2026-04-01")
ax.axvline(
    price_rise,
    color="#555555",
    linestyle="--",
    linewidth=1.0,
    alpha=0.75,
    zorder=0,
)
ax.text(
    price_rise - pd.Timedelta(days=10),
    7.55,
    "Family price\n$79 → $89",
    ha="right",
    va="top",
    fontsize=9.5,
    color="#333333",
)

# Pre/post average reference lines
pre_start = pd.Timestamp("2025-10-01")
pre_end = pd.Timestamp("2026-03-01")
post_end = pd.Timestamp("2026-08-01")

ax.hlines(
    pre_avg,
    pre_start,
    pre_end,
    colors="#C0392B",
    linewidth=1.0,
    linestyles="dashed",
    alpha=0.6,
    zorder=2,
)
ax.hlines(
    post_avg,
    price_rise,
    post_end,
    colors="#C0392B",
    linewidth=1.0,
    linestyles="dashed",
    alpha=0.6,
    zorder=2,
)

ax.text(
    pre_start + pd.Timedelta(days=20),
    pre_avg + 0.25,
    f"Pre-rise avg {pre_avg:.1f}%",
    color="#C0392B",
    fontsize=9.5,
    ha="left",
    va="bottom",
)
ax.text(
    price_rise + pd.Timedelta(days=10),
    post_avg + 0.25,
    f"Post-rise avg {post_avg:.1f}%",
    color="#C0392B",
    fontsize=9.5,
    ha="left",
    va="bottom",
)

# Direct labels at the right
last_date = family.index.max()
ax.text(
    last_date + pd.Timedelta(days=12),
    family.iloc[-1],
    "Family",
    color="#C0392B",
    fontsize=10.5,
    fontweight="bold",
    ha="left",
    va="center",
)
ax.text(
    last_date + pd.Timedelta(days=12),
    other_rate.iloc[-1],
    "Other plans",
    color="#777777",
    fontsize=10,
    ha="left",
    va="center",
)

# Axes and formatting
ax.set_ylim(0, 8)
ax.set_yticks([0, 2, 4, 6, 8])
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:.0f}%"))
ax.set_ylabel("Monthly cancellation rate", fontsize=11, color="#333333")
ax.set_xlabel("")
ax.grid(axis="y", color="#E8E8E8", linewidth=0.8)
ax.set_axisbelow(True)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color("#CCCCCC")
ax.spines["bottom"].set_color("#CCCCCC")
ax.tick_params(colors="#555555", labelsize=10)

ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.set_xlim(
    pre_start - pd.Timedelta(days=10),
    last_date + pd.Timedelta(days=80),
)

# Title
ax.set_title(
    "Family cancellations doubled after the April price rise, while active subscribers fell 19%",
    fontsize=14.5,
    fontweight="bold",
    loc="left",
    pad=16,
)

# Caveat
fig.text(
    0.01,
    0.015,
    "Cancellation rates exclude Sep 2026 (1–14 Sep only); active subscribers are start-of-month.",
    fontsize=8,
    color="#777777",
)

fig.tight_layout(rect=[0, 0.045, 1, 1])
