import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Read data
df = pd.read_csv("data.csv")
df["month"] = pd.to_datetime(df["month"], format="%Y-%m")
df = df.sort_values(["plan", "month"])

# Index each plan to its first month = 100 for comparability
first_month = df["month"].min()
base = (
    df[df["month"] == first_month]
    .set_index("plan")["active_subscribers"]
)
df["indexed_subscribers"] = df.apply(
    lambda row: row["active_subscribers"] / base[row["plan"]] * 100,
    axis=1,
)

pivot = df.pivot(
    index="month",
    columns="plan",
    values="indexed_subscribers",
).sort_index()

# Figure
fig, ax = plt.subplots(figsize=(10, 6))

context_plans = ["Single", "Couple", "Vegetarian"]
for plan in context_plans:
    ax.plot(
        pivot.index,
        pivot[plan],
        color="#B8B8B8",
        linewidth=1.6,
        alpha=0.9,
        zorder=1,
    )

# Highlight Family
ax.plot(
    pivot.index,
    pivot["Family"],
    color="#C0392B",
    linewidth=3.2,
    marker="o",
    markersize=4,
    zorder=3,
)

# Reference line at no change and price-rise date
ax.axhline(100, color="#D5D5D5", linewidth=0.9, zorder=0)
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
    price_rise + pd.Timedelta(days=8),
    143,
    "Family price\n$79 → $89",
    ha="left",
    va="top",
    fontsize=9.5,
    color="#333333",
)

# Direct labels at the right
last_date = pivot.index.max()
for plan in context_plans:
    ax.text(
        last_date + pd.Timedelta(days=10),
        pivot[plan].iloc[-1],
        plan,
        ha="left",
        va="center",
        fontsize=10,
        color="#777777",
    )

apr_value = pivot.loc[price_rise, "Family"]
last_family = pivot["Family"].iloc[-1]
change_since_apr = (last_family / apr_value - 1) * 100
ax.text(
    last_date + pd.Timedelta(days=10),
    last_family,
    f"Family ({change_since_apr:.0f}% since Apr)",
    ha="left",
    va="center",
    fontsize=10.5,
    color="#C0392B",
    fontweight="bold",
)

# Title and styling
ax.set_title(
    "Family subscribers fell 19% after the April price rise, while every other plan grew",
    fontsize=15,
    fontweight="bold",
    loc="left",
    pad=16,
)
ax.set_ylabel("Active subscribers (Oct 2025 = 100)", fontsize=11, color="#333333")
ax.set_xlabel("")
ax.set_ylim(75, 145)
ax.set_yticks([80, 100, 120, 140])
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
    pivot.index.min() - pd.Timedelta(days=12),
    pivot.index.max() + pd.Timedelta(days=115),
)

fig.text(
    0.01,
    0.015,
    "Note: Sep 2026 active subscribers are start-of-month. Sep sign-ups/cancellations cover 1–14 Sep only.",
    fontsize=8,
    color="#777777",
)

fig.tight_layout(rect=[0, 0.04, 1, 1])
