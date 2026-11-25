import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Read data
df = pd.read_csv("data.csv")
df["month"] = pd.to_datetime(df["month"]).dt.strftime("%Y-%m")

# Adjust Hillcrest July-September readings for the new meters
# (new meters read ~8% higher than old meters)
df["lphd_adj"] = df["litres_per_household_day"].copy()
hill_new_meter = (df["district"] == "Hillcrest") & (df["month"] >= "2026-07")
df.loc[hill_new_meter, "lphd_adj"] = (
    df.loc[hill_new_meter, "litres_per_household_day"] / 1.08
)

# Post-restriction period: June-September
post = df[df["month"] >= "2026-06"].copy()
post["pct_over"] = (
    (post["lphd_adj"] - post["target_lphd"]) / post["target_lphd"] * 100
)

# District summary for June-September
summary = (
    post.groupby("district")
    .agg(
        avg_use=("lphd_adj", "mean"),
        target=("target_lphd", "first"),
        pct_over=("pct_over", "mean"),
        households=("households", "first"),
        notices=("enforcement_notices", "sum"),
    )
    .reset_index()
)
summary["pct_over"] = (
    (summary["avg_use"] - summary["target"]) / summary["target"] * 100
)
summary = summary.sort_values("pct_over", ascending=True)

# Figure
fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.25, 1.0]}
)

# Left panel: average gap to target
y = np.arange(len(summary))
colors = [
    "#d62728" if d == "Hillcrest" else "#9e9e9e"
    for d in summary["district"]
]

ax1.barh(y, summary["pct_over"], color=colors, height=0.7)
ax1.set_yticks(y)
ax1.set_yticklabels(summary["district"])
ax1.axvline(0, color="black", linewidth=0.8)
ax1.set_xlabel("June–September average vs target (%)")
ax1.set_title("Average gap to target", fontsize=11, loc="left")
ax1.grid(axis="x", alpha=0.25)

for i, (_, row) in enumerate(summary.iterrows()):
    val = row["pct_over"]
    if row["district"] == "Hillcrest":
        label = f"{val:+.0f}%  ({row['avg_use']:.0f} vs {row['target']:.0f})"
        fontweight = "bold"
    else:
        label = f"{val:+.0f}%"
        fontweight = "normal"

    offset = 0.8 if val >= 0 else -0.8
    ha = "left" if val >= 0 else "right"
    ax1.text(
        val + offset,
        i,
        label,
        va="center",
        ha=ha,
        fontsize=9,
        fontweight=fontweight,
        color="#d62728" if row["district"] == "Hillcrest" else "black",
    )

xmin = min(-20, summary["pct_over"].min() - 5)
xmax = max(40, summary["pct_over"].max() + 30)
ax1.set_xlim(xmin, xmax)

# Right panel: monthly gap to target
months = ["2026-06", "2026-07", "2026-08", "2026-09"]
month_labels = ["Jun", "Jul", "Aug", "Sep"]

for district in summary["district"].sort_values():
    dat = (
        post[post["district"] == district]
        .set_index("month")
        .reindex(months)
    )
    vals = dat["pct_over"].values

    if district == "Hillcrest":
        ax2.plot(
            range(len(months)),
            vals,
            color="#d62728",
            linewidth=3,
            marker="o",
            markersize=5,
            label="Hillcrest",
            zorder=5,
        )
    else:
        ax2.plot(
            range(len(months)),
            vals,
            color="#9e9e9e",
            linewidth=1,
            alpha=0.6,
            zorder=2,
        )

other_avg = (
    post[post["district"] != "Hillcrest"]
    .groupby("month")["pct_over"]
    .mean()
    .reindex(months)
)
ax2.plot(
    range(len(months)),
    other_avg.values,
    color="#4d4d4d",
    linewidth=1.5,
    linestyle="--",
    label="Other districts (avg)",
    zorder=4,
)

ax2.axhline(0, color="black", linewidth=0.8)
ax2.set_xticks(range(len(months)))
ax2.set_xticklabels(month_labels)
ax2.set_ylabel("% above monthly target")
ax2.set_title("Monthly gap to target", fontsize=11, loc="left")
ax2.grid(axis="y", alpha=0.25)
ax2.legend(frameon=False, fontsize=8, loc="upper right")

hill_vals = (
    post[post["district"] == "Hillcrest"]
    .set_index("month")
    .reindex(months)["pct_over"]
    .values
)
ax2.text(
    len(months) - 1 + 0.1,
    hill_vals[-1],
    "Hillcrest",
    color="#d62728",
    fontsize=9,
    va="center",
    ha="left",
    fontweight="bold",
)

fig.suptitle(
    "Hillcrest is the clear enforcement priority: largest and most persistent gap to target",
    fontsize=13,
    fontweight="bold",
    x=0.02,
    ha="left",
)

fig.text(
    0.01,
    0.01,
    "Target = 20% below April–May use. Hillcrest July–September readings adjusted for new meters (÷1.08).",
    fontsize=8,
    color="#555555",
)

plt.tight_layout(rect=[0, 0.04, 1, 0.93])
