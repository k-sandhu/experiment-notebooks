import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Read data
df = pd.read_csv("data.csv")

# Adjust Northgate waits to be comparable with triage-based wait clocks
df["median_wait_adj"] = df["median_wait_min"]
registration_mask = (
    (df["hospital"] == "Northgate") & 
    (df["wait_clock_starts_at"] == "registration")
)
df.loc[registration_mask, "median_wait_adj"] = (
    df.loc[registration_mask, "median_wait_min"] - 15
)

categories = ["Urgent", "Semi-urgent", "Non-urgent"]
colors = {
    "Urgent": "#d62728",
    "Semi-urgent": "#1f77b4",
    "Non-urgent": "#2ca02c",
}

# Order hospitals by adjusted urgent wait
urgent_order = (
    df[df["triage_category"] == "Urgent"]
    .set_index("hospital")["median_wait_adj"]
    .sort_values()
    .index
    .tolist()
)

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [2.2, 1]}
)

# Panel 1: median wait by triage category
x = np.arange(len(urgent_order))
width = 0.26

for i, cat in enumerate(categories):
    vals = (
        df[df["triage_category"] == cat]
        .set_index("hospital")
        .loc[urgent_order, "median_wait_adj"]
    )
    ax1.bar(
        x + (i - 1) * width,
        vals,
        width,
        label=cat,
        color=colors[cat],
        edgecolor="white",
        linewidth=0.6,
    )

ax1.set_xticks(x)
ax1.set_xticklabels(urgent_order, rotation=45, ha="right")
ax1.set_ylabel("Median wait to first seen (minutes)")
ax1.set_title("Median ED wait by triage category")
ax1.legend(title="Triage category", frameon=False, ncol=3, loc="upper left")
ax1.grid(axis="y", alpha=0.25)
ax1.set_axisbelow(True)
ax1.set_ylim(0, df["median_wait_adj"].max() * 1.16)

# Note Northgate adjustment
ng_idx = urgent_order.index("Northgate")
ng_ymax = df[df["hospital"] == "Northgate"]["median_wait_adj"].max()
ax1.annotate(
    "*",
    xy=(ng_idx, ng_ymax),
    xytext=(0, 7),
    textcoords="offset points",
    ha="center",
    fontsize=13,
)
ax1.text(
    0.01,
    0.98,
    "* Northgate adjusted by −15 min: its wait clock starts at registration.",
    transform=ax1.transAxes,
    fontsize=8,
    va="top",
    color="0.35",
)

# Panel 2: weighted left-without-being-seen percentage
df["weighted_lwbs"] = df["left_without_being_seen_pct"] * df["visits"]
lwbs = (
    df.groupby("hospital")
    .agg(total_visits=("visits", "sum"), weighted_lwbs=("weighted_lwbs", "sum"))
)
lwbs["lwbs_pct"] = lwbs["weighted_lwbs"] / lwbs["total_visits"]
lwbs = lwbs.sort_values("lwbs_pct", ascending=True)

bar_colors = [
    "#d62728" if hospital == "Riverside" else "#9e9e9e"
    for hospital in lwbs.index
]
ax2.barh(
    lwbs.index,
    lwbs["lwbs_pct"],
    color=bar_colors,
    edgecolor="white",
    linewidth=0.6,
)
ax2.set_xlabel("Left without being seen (%)")
ax2.set_title("Patients leaving without being seen")
ax2.grid(axis="x", alpha=0.25)
ax2.set_axisbelow(True)
ax2.set_xlim(0, lwbs["lwbs_pct"].max() * 1.32)

for i, (hospital, row) in enumerate(lwbs.iterrows()):
    ax2.text(
        row["lwbs_pct"] + 0.15,
        i,
        f'{row["lwbs_pct"]:.1f}%',
        va="center",
        fontsize=8,
        color="0.25",
    )

fig.suptitle(
    "Emergency Department Performance, July–September 2026",
    fontsize=12,
    weight="bold",
)
fig.tight_layout(rect=[0, 0, 1, 0.95])
