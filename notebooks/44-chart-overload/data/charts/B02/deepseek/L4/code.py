import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv("data.csv")

# Triage-category median waits
cat_order = ["Urgent", "Semi-urgent", "Non-urgent"]
waits = (
    df.pivot(index="hospital", columns="triage_category", values="median_wait_min")
    .reindex(columns=cat_order)
)

# Overall left-without-being-seen, weighted by visits
df["lwbs_num"] = df["left_without_being_seen_pct"] * df["visits"]
lwbs = (
    df.groupby("hospital", as_index=False)
    .agg(lwbs_num=("lwbs_num", "sum"), visits=("visits", "sum"))
)
lwbs["lwbs_pct"] = lwbs["lwbs_num"] / lwbs["visits"]
lwbs_sorted = lwbs.sort_values("lwbs_pct", ascending=True).reset_index(drop=True)

other = lwbs[lwbs["hospital"] != "Riverside"]
other_avg = other["lwbs_num"].sum() / other["visits"].sum()

# Figure
fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [2.25, 1]}
)
fig.subplots_adjust(top=0.80, bottom=0.19, left=0.07, right=0.96, wspace=0.55)

# Left panel: median wait by triage category
x = np.arange(len(cat_order))

for hospital in waits.index:
    if hospital == "Riverside":
        continue
    ax1.plot(
        x,
        waits.loc[hospital, cat_order].values,
        color="#bdbdbd",
        lw=1.0,
        marker="o",
        markersize=2.5,
        alpha=0.8,
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
        f"{val:.0f}",
        xy=(xi, val),
        xytext=(0, 10),
        textcoords="offset points",
        ha="center",
        va="bottom",
        color="#c62828",
        fontsize=10,
        fontweight="bold",
    )

ax1.annotate(
    "Riverside",
    xy=(2, riverside_vals[-1]),
    xytext=(8, 0),
    textcoords="offset points",
    color="#c62828",
    fontsize=11,
    fontweight="bold",
    va="center",
    ha="left",
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
    "#c62828" if hospital == "Riverside" else "#bdbdbd"
    for hospital in lwbs_sorted["hospital"]
]

ax2.barh(y, lwbs_sorted["lwbs_pct"], color=colors, height=0.7)
ax2.set_yticks(y)
ax2.set_yticklabels(lwbs_sorted["hospital"], fontsize=10)
ax2.set_xlabel("Overall left without being seen (%)", fontsize=10)
ax2.set_xlim(0, 10.5)
ax2.set_ylim(-0.6, 8.3)

ax2.axvline(other_avg, color="#666666", lw=1, linestyle="--", zorder=0)
ax2.text(
    other_avg + 0.18,
    len(lwbs_sorted) - 0.4,
    f"Other EDs avg {other_avg:.1f}%",
    color="#555555",
    fontsize=8,
    va="bottom",
    ha="left",
)

riverside_lwbs = lwbs_sorted.loc[
    lwbs_sorted["hospital"] == "Riverside", "lwbs_pct"
].iloc[0]
riverside_y = lwbs_sorted.index[lwbs_sorted["hospital"] == "Riverside"][0]
ax2.text(
    riverside_lwbs + 0.18,
    riverside_y,
    f"{riverside_lwbs:.1f}%",
    color="#c62828",
    fontsize=10,
    fontweight="bold",
    va="center",
    ha="left",
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
    "Riverside should get the 12 extra triage nurses —\n"
    "it has the longest waits and the most patients leaving unseen",
    fontsize=15,
    fontweight="bold",
    ha="left",
    va="top",
    linespacing=1.15,
)
fig.text(
    0.02,
    0.855,
    "Median minutes from arrival to first seen by a doctor; July–September 2026",
    fontsize=9,
    color="#555555",
    ha="left",
    va="top",
)
fig.text(
    0.02,
    0.02,
    "Note: Northgate's wait clock starts at registration, not triage, adding about 15 min to its recorded waits.",
    fontsize=8,
    color="#555555",
    ha="left",
    va="bottom",
)
