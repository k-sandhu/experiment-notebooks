import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Read data
df = pd.read_csv("data.csv")

# Prepare triage-category wait data
cat_order = ["Urgent", "Semi-urgent", "Non-urgent"]
waits = (
    df.pivot(index="hospital", columns="triage_category", values="median_wait_min")
    .reindex(columns=cat_order)
)

# Prepare weighted left-without-being-seen percentage by hospital
df["lwbs_num"] = df["left_without_being_seen_pct"] * df["visits"]
lwbs = (
    df.groupby("hospital", as_index=False)
    .agg(lwbs_num=("lwbs_num", "sum"), visits=("visits", "sum"))
)
lwbs["lwbs_pct"] = lwbs["lwbs_num"] / lwbs["visits"]
lwbs_sorted = lwbs.sort_values("lwbs_pct", ascending=True).reset_index(drop=True)

other_avg = (
    lwbs.loc[lwbs["hospital"] != "Riverside", "lwbs_num"].sum()
    / lwbs.loc[lwbs["hospital"] != "Riverside", "visits"].sum()
)

# Figure
fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [2.3, 1]}
)
fig.subplots_adjust(top=0.80, bottom=0.18, left=0.07, right=0.96, wspace=0.55)

# Left panel: median waits by triage category
x = np.arange(len(cat_order))

for hospital in waits.index:
    if hospital == "Riverside":
        continue
    ax1.plot(
        x,
        waits.loc[hospital, cat_order].values,
        color="#b8b8b8",
        lw=1.2,
        marker="o",
        markersize=3,
        alpha=0.85,
        zorder=1,
    )

riverside_vals = waits.loc["Riverside", cat_order].values
ax1.plot(
    x,
    riverside_vals,
    color="#c62828",
    lw=3,
    marker="o",
    markersize=7,
    zorder=5,
)

for xi, val in zip(x, riverside_vals):
    ax1.annotate(
        f"{val:.0f} min",
        xy=(xi, val),
        xytext=(0, 10),
        textcoords="offset points",
        ha="center",
        va="bottom",
        color="#c62828",
        fontsize=10,
        fontweight="bold",
    )

ax1.text(
    2.08,
    riverside_vals[-1],
    "Riverside",
    color="#c62828",
    fontsize=11,
    fontweight="bold",
    va="center",
)

ax1.set_xticks(x)
ax1.set_xticklabels(cat_order)
ax1.set_ylabel("Median wait (minutes)")
ax1.set_ylim(0, 215)
ax1.set_xlim(-0.2, 2.55)
ax1.grid(axis="y", color="#e5e5e5", lw=0.8)
ax1.set_axisbelow(True)
ax1.tick_params(axis="both", labelsize=10)
for spine in ["top", "right"]:
    ax1.spines[spine].set_visible(False)

# Right panel: left without being seen
y = np.arange(len(lwbs_sorted))
colors = [
    "#c62828" if hospital == "Riverside" else "#b8b8b8"
    for hospital in lwbs_sorted["hospital"]
]

ax2.barh(y, lwbs_sorted["lwbs_pct"], color=colors, height=0.7)
ax2.set_yticks(y)
ax2.set_yticklabels(lwbs_sorted["hospital"], fontsize=10)
ax2.set_xlabel("Left without being seen (%)", fontsize=10)
ax2.set_xlim(0, 10.5)

ax2.axvline(other_avg, color="#777777", lw=1, linestyle="--", zorder=0)
ax2.text(
    other_avg + 0.15,
    len(lwbs_sorted) - 0.5,
    f"Other EDs avg.\n{other_avg:.1f}%",
    color="#555555",
    fontsize=8,
    va="top",
)

riverside_lwbs = lwbs_sorted.loc[lwbs_sorted["hospital"] == "Riverside", "lwbs_pct"].values[0]
riverside_y = lwbs_sorted.index[lwbs_sorted["hospital"] == "Riverside"][0]
ax2.text(
    riverside_lwbs + 0.2,
    riverside_y,
    f"{riverside_lwbs:.1f}%",
    color="#c62828",
    fontsize=10,
    fontweight="bold",
    va="center",
)

ax2.set_title("Patients leaving without being seen", fontsize=10, loc="left", pad=8)
ax2.grid(axis="x", color="#e5e5e5", lw=0.8)
ax2.set_axisbelow(True)
ax2.tick_params(axis="x", labelsize=9)
for spine in ["top", "right"]:
    ax2.spines[spine].set_visible(False)

# Titles and note
fig.text(
    0.02,
    0.965,
    "Riverside should receive the 12 triage nurses:",
    fontsize=15,
    fontweight="bold",
    ha="left",
    va="top",
)
fig.text(
    0.02,
    0.915,
    "longest waits in every triage category and the most patients leaving unseen",
    fontsize=12,
    ha="left",
    va="top",
)
fig.text(
    0.02,
    0.855,
    "Median minutes from arrival to first seen; July–September 2026",
    fontsize=9,
    color="#555555",
    ha="left",
)
fig.text(
    0.02,
    0.02,
    "Note: Northgate's wait clock starts at registration rather than triage "
    "(adds about 15 min), so its waits are not directly comparable.",
    fontsize=8,
    color="#555555",
    ha="left",
)
