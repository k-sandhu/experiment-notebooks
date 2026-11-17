import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

df = pd.read_csv("data.csv", parse_dates=["month"])
df = df.sort_values(["plan", "month"])

april = pd.Timestamp("2026-04-01")
sep = pd.Timestamp("2026-09-01")

plans = ["Couple", "Family", "Single", "Vegetarian"]
colors = {
    "Couple": "#4C78A8",
    "Family": "#C1272D",
    "Single": "#E69F00",
    "Vegetarian": "#59A14F",
}

fig, axes = plt.subplots(
    2, 1, figsize=(10, 6), sharex=True,
    gridspec_kw={"height_ratios": [1.25, 1], "hspace": 0.12},
)
ax_top, ax_bot = axes

# Panel 1: active subscribers at start of month (September value is valid)
for plan in plans:
    d = df[df["plan"] == plan]
    lw = 3.2 if plan == "Family" else 2.2
    ax_top.plot(
        d["month"], d["active_subscribers"],
        color=colors[plan], linewidth=lw, marker="o", markersize=3.5,
        label=plan,
    )

# Panel 2: cancellation rate, excluding partial September (1-14 Sep only)
for plan in plans:
    d = df[(df["plan"] == plan) & (df["month"] < sep)]
    lw = 3.2 if plan == "Family" else 2.2
    ax_bot.plot(
        d["month"], d["cancellation_rate_pct"],
        color=colors[plan], linewidth=lw, marker="o", markersize=3.5,
        label=plan,
    )

# Price-rise marker on both panels
for ax in axes:
    ax.axvline(april, color="#C1272D", linestyle="--", linewidth=1.4, alpha=0.85)
    ax.grid(axis="y", alpha=0.25, linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)

ax_top.text(
    april + pd.Timedelta(days=6), 19500,
    "1 Apr 2026\nFamily price\n$79 → $89/week",
    color="#C1272D", fontsize=9, va="top", fontweight="bold",
)

# Key changes calculated from the data
fam = df[df["plan"] == "Family"].set_index("month")
veg = df[df["plan"] == "Vegetarian"].set_index("month")

fam_apr = fam.loc[april, "active_subscribers"]
fam_sep = fam.loc[sep, "active_subscribers"]
fam_change = 100 * (fam_sep - fam_apr) / fam_apr
veg_change = 100 * (
    veg.loc[sep, "active_subscribers"] - veg.iloc[0]["active_subscribers"]
) / veg.iloc[0]["active_subscribers"]

ax_top.annotate(
    f"Family: {fam_apr:,.0f} (Apr) → {fam_sep:,.0f} (Sep)\n{fam_change:.0f}%",
    xy=(sep, fam_sep),
    xytext=(pd.Timestamp("2026-05-20"), 8500),
    color="#C1272D", fontsize=9, fontweight="bold",
    arrowprops={"arrowstyle": "->", "color": "#C1272D", "linewidth": 1.2},
)
ax_top.annotate(
    f"Vegetarian +{veg_change:.0f}% Oct→Sep\n(fastest-growing)",
    xy=(pd.Timestamp("2026-02-01"), veg.loc[pd.Timestamp("2026-02-01"), "active_subscribers"]),
    xytext=(pd.Timestamp("2025-10-05"), 8500),
    color="#59A14F", fontsize=9,
    arrowprops={"arrowstyle": "->", "color": "#59A14F", "linewidth": 1.1},
)

# Family average cancellation rates before/after the price rise
pre = fam.loc[fam.index < april, "cancellation_rate_pct"].mean()
post = fam.loc[(fam.index >= april) & (fam.index < sep), "cancellation_rate_pct"].mean()
ax_bot.hlines(pre, df["month"].min(), april, color="#C1272D", linestyle=":", linewidth=1.6)
ax_bot.hlines(post, april, pd.Timestamp("2026-08-01"), color="#C1272D", linestyle=":", linewidth=1.6)
ax_bot.text(pd.Timestamp("2025-11-15"), pre + 0.35,
            f"Family avg Oct–Mar: {pre:.1f}%", color="#C1272D", fontsize=9, fontweight="bold")
ax_bot.text(pd.Timestamp("2026-04-12"), post + 0.35,
            f"Family avg Apr–Aug: {post:.1f}%", color="#C1272D", fontsize=9, fontweight="bold")

ax_top.set_ylabel("Active subscribers\n(start of month)")
ax_top.set_ylim(3000, 23500)
ax_top.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))

ax_bot.set_ylabel("Cancellation rate\n(% of active subscribers)")
ax_bot.set_ylim(0, 7.8)
ax_bot.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0f}%"))

months = sorted(df["month"].unique())
ax_bot.set_xticks(months)
ax_bot.set_xticklabels([pd.Timestamp(m).strftime("%b %y") for m in months], rotation=35, ha="right")
ax_bot.set_xlim(df["month"].min() - pd.Timedelta(days=5),
                sep + pd.Timedelta(days=12))
ax_bot.set_xlabel("Month")

handles, labels = ax_top.get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=4, frameon=False,
           bbox_to_anchor=(0.5, 0.94), fontsize=10)

fig.suptitle(
    "Family plan lost subscribers after its April price rise — other plans kept growing",
    fontsize=14, fontweight="bold", y=0.985,
)
fig.text(
    0.01, 0.01,
    "Note: September 2026 covers 1–14 Sep only, so it is excluded from the cancellation panel; "
    "its start-of-month subscriber count (top) is unaffected.\n"
    "Excludes gift subscriptions (~3% of orders).",
    fontsize=8, color="#555555", va="bottom",
)

fig.tight_layout(rect=[0, 0.05, 1, 0.91])
