import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

df = pd.read_csv("data.csv")

cats = ["Urgent", "Semi-urgent", "Non-urgent"]
colors = {"Urgent": "#c0392b", "Semi-urgent": "#e67e22", "Non-urgent": "#f1c40f"}

# Median wait by hospital x category
wait = df.pivot(index="hospital", columns="triage_category", values="median_wait_min")[cats]

# Visit-weighted % leaving without being seen, per hospital
df["lwbs_n"] = df["visits"] * df["left_without_being_seen_pct"] / 100
lwbs = df.groupby("hospital").apply(lambda g: 100 * g["lwbs_n"].sum() / g["visits"].sum())

clock = df.groupby("hospital")["wait_clock_starts_at"].first()

# Order hospitals: longest urgent wait at top
order = wait["Urgent"].sort_values(ascending=True).index.tolist()
wait = wait.loc[order]
lwbs = lwbs.loc[order]

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), sharey=True, gridspec_kw={"width_ratios": [2.4, 1]}
)

y = np.arange(len(order))
h = 0.26
for i, c in enumerate(cats):
    offs = (1 - i) * h  # Urgent on top within each group
    for j, hosp in enumerate(order):
        diff_clock = clock[hosp] != "triage"
        ax1.barh(
            y[j] + offs, wait.loc[hosp, c], height=h,
            color=colors[c], edgecolor="#555" if diff_clock else "none",
            hatch="///" if diff_clock else None, linewidth=0.6,
        )
        ax1.text(wait.loc[hosp, c] + 2, y[j] + offs, f"{wait.loc[hosp, c]:.0f}",
                 va="center", fontsize=7, color="#333")

ax1.set_yticks(y)
ax1.set_yticklabels([f"{h_}*" if clock[h_] != "triage" else h_ for h_ in order])
ax1.set_xlabel("Median wait to first seen by a doctor (minutes)")
ax1.set_title("Median wait by triage category", fontsize=11, loc="left")
ax1.set_xlim(0, wait.values.max() * 1.12)
ax1.spines[["top", "right"]].set_visible(False)
ax1.grid(axis="x", alpha=0.3)
ax1.set_axisbelow(True)

legend_items = [Patch(color=colors[c], label=c) for c in cats]
ax1.legend(handles=legend_items, loc="lower right", frameon=False, fontsize=9)

# LWBS panel
other_avg = 100 * df.loc[df.hospital != "Riverside", "lwbs_n"].sum() / \
            df.loc[df.hospital != "Riverside", "visits"].sum()
bar_cols = ["#c0392b" if hsp == "Riverside" else "#7f8c8d" for hsp in order]
ax2.barh(y, lwbs.values, color=bar_cols, height=0.6)
for j, v in enumerate(lwbs.values):
    ax2.text(v + 0.15, y[j], f"{v:.1f}%", va="center", fontsize=8)
ax2.axvline(other_avg, color="#333", ls="--", lw=0.8)
ax2.text(other_avg + 0.15, len(order) - 0.45, f"other 7: {other_avg:.1f}%",
         fontsize=8, color="#333", va="bottom")
ax2.set_xlabel("% of visits")
ax2.set_title("Left without being seen", fontsize=11, loc="left")
ax2.set_xlim(0, lwbs.max() * 1.3)
ax2.set_ylim(-0.6, len(order) - 0.1)
ax2.spines[["top", "right"]].set_visible(False)
ax2.grid(axis="x", alpha=0.3)
ax2.set_axisbelow(True)

fig.suptitle("Riverside has the longest emergency waits and the most patients leaving unseen",
             fontsize=13, fontweight="bold", x=0.01, ha="left")
fig.text(0.01, 0.905, "Emergency departments, July–September 2026. Hospitals ordered by urgent median wait.",
         fontsize=9, color="#555", ha="left")
fig.text(0.01, 0.015,
         "* Northgate (hatched) starts its wait clock at registration; all others start at triage, "
         "so Northgate's waits are not directly comparable.\n"
         "Left-without-being-seen rates are weighted by visits across triage categories.",
         fontsize=8, color="#555", ha="left")

fig.tight_layout(rect=[0, 0.06, 1, 0.89])
