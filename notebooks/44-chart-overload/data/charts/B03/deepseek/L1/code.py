import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Load data
df = pd.read_csv("data.csv")
df["date"] = pd.to_datetime(df["date"])

# Overall daily conversion by variant
daily = (
    df.groupby(["date", "variant"], as_index=False)
      .agg(sessions=("sessions", "sum"), orders=("orders", "sum"))
)
daily["conversion_pct"] = 100 * daily["orders"] / daily["sessions"]
overall = daily.pivot(index="date", columns="variant", values="conversion_pct").sort_index()

# Mobile conversion before vs after Sep 26 fix
mobile = df[df["device"] == "mobile"].copy()
mobile["period"] = np.where(
    mobile["date"] < pd.Timestamp("2026-09-26"),
    "Sep 14-25\n(before fix)",
    "Sep 26-27\n(after fix)"
)

periods = ["Sep 14-25\n(before fix)", "Sep 26-27\n(after fix)"]
variants = ["control", "new_checkout"]

m_agg = (
    mobile.groupby(["period", "variant"], as_index=False)
          .agg(sessions=("sessions", "sum"), orders=("orders", "sum"))
)
m_agg["conversion_pct"] = 100 * m_agg["orders"] / m_agg["sessions"]
m_agg["period"] = pd.Categorical(m_agg["period"], categories=periods, ordered=True)
m_agg = m_agg.sort_values(["period", "variant"])

mobile_vals = {
    v: [
        float(m_agg[(m_agg["period"] == p) & (m_agg["variant"] == v)]["conversion_pct"].iloc[0])
        for p in periods
    ]
    for v in variants
}

# Colors / labels
colors = {"control": "#7f8c8d", "new_checkout": "#1f77b4"}
labels = {"control": "Old checkout", "new_checkout": "New checkout"}

# Figure
fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [2.1, 1]}
)

# Left panel: overall conversion over time
for variant in variants:
    ax1.plot(
        overall.index,
        overall[variant],
        marker="o",
        markersize=4,
        linewidth=2,
        color=colors[variant],
        linestyle="--" if variant == "control" else "-",
        label=labels[variant],
    )

bug_date = pd.Timestamp("2026-09-26")
outage_date = pd.Timestamp("2026-09-20")

ax1.axvline(bug_date, color="#2ca02c", linestyle="--", linewidth=2, alpha=0.8)
ax1.axvline(outage_date, color="#d62728", linestyle=":", linewidth=1.5, alpha=0.7)

ax1.set_ylim(1.2, 3.05)
ax1.set_ylabel("Overall conversion (%)")
ax1.set_title(
    "Overall conversion: new checkout only overtook old after mobile fix",
    loc="left",
    fontsize=11,
    weight="bold",
)
ax1.legend(loc="lower left", frameon=False)
ax1.xaxis.set_major_locator(mdates.DayLocator(interval=2))
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax1.grid(axis="y", alpha=0.25)

ax1.text(
    bug_date - pd.Timedelta(days=1),
    2.98,
    "Mobile bug fixed",
    color="#2ca02c",
    fontsize=9,
    ha="right",
    va="top",
)
ax1.text(
    outage_date,
    1.35,
    "Payment\noutage",
    color="#d62728",
    fontsize=8,
    ha="center",
    va="bottom",
)

# Right panel: mobile pre-fix vs post-fix
x = np.arange(len(periods))
width = 0.36

for i, variant in enumerate(variants):
    offsets = x + (i - 0.5) * width
    bars = ax2.bar(
        offsets,
        mobile_vals[variant],
        width,
        color=colors[variant],
        label=labels[variant],
    )
    for bar, val in zip(bars, mobile_vals[variant]):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.04,
            f"{val:.2f}%",
            ha="center",
            va="bottom",
            fontsize=9,
        )

ax2.set_xticks(x)
ax2.set_xticklabels(periods, fontsize=9)
ax2.set_ylabel("Mobile conversion (%)")
ax2.set_ylim(0, 2.7)
ax2.set_title(
    "Mobile: recovery after fix, but only 2 days\n(68% of sessions)",
    loc="left",
    fontsize=11,
    weight="bold",
)
ax2.grid(axis="y", alpha=0.25)
ax2.legend(loc="upper left", frameon=False)

# Full-period order impact
tot = df.groupby("variant")["orders"].sum()
pct_change = (tot["new_checkout"] / tot["control"] - 1) * 100

fig.text(
    0.08,
    0.02,
    f"Full 14 days: new checkout {tot['new_checkout']:,} orders vs {tot['control']:,} old "
    f"({pct_change:+.1f}%).",
    fontsize=9,
    color="#333333",
)

fig.suptitle(
    "Oakline checkout test: desktop gains, but mobile bug held back overall results",
    fontsize=14,
    weight="bold",
    x=0.08,
    ha="left",
    y=0.97,
)
fig.text(
    0.08,
    0.91,
    "New mobile checkout matched old after Sep 26 fix; full-period order gap reflects pre-fix mobile losses.",
    fontsize=10,
    color="#444444",
)

fig.subplots_adjust(top=0.82, bottom=0.12, left=0.08, right=0.97, wspace=0.32)
