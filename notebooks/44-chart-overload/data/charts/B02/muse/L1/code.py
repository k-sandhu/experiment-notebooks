import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Put Northgate on the same basis as the others: its clock starts at
# registration, about 15 minutes before triage.
df["median_adj"] = np.where(
    df["wait_clock_starts_at"] == "registration",
    df["median_wait_min"] - 15,
    df["median_wait_min"],
)

# Order hospitals by adjusted urgent wait, worst first (Riverside at top).
urgent = (
    df[df["triage_category"] == "Urgent"]
    .set_index("hospital")["median_adj"]
    .sort_values(ascending=False)
)
hospitals = urgent.index.tolist()

totals = df.groupby("hospital")["visits"].sum().reindex(hospitals)

# Overall left-without-being-seen rate, weighted by visits in each category.
left = (
    df.assign(left_n=df["visits"] * df["left_without_being_seen_pct"] / 100.0)
    .groupby("hospital")["left_n"]
    .sum()
    .reindex(hospitals)
)
lwbs = 100.0 * left / totals
lwbs_others = 100.0 * left.drop("Riverside").sum() / totals.drop("Riverside").sum()

categories = ["Urgent", "Semi-urgent", "Non-urgent"]
cat_colors = {"Urgent": "#1B4F72", "Semi-urgent": "#5DA5DA", "Non-urgent": "#B9CDE3"}
cat_offsets = {"Urgent": -0.25, "Semi-urgent": 0.0, "Non-urgent": 0.25}

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), sharey=True,
    gridspec_kw={"width_ratios": [2.1, 1.0]},
)
fig.subplots_adjust(left=0.21, right=0.965, top=0.80, bottom=0.19, wspace=0.14)

fig.text(0.04, 0.94, "Fund the 12 extra triage nurses at Riverside",
         fontsize=19, fontweight="bold", ha="left", va="center")
fig.text(0.04, 0.885,
         "Riverside patients wait longest in every triage category — and leave unseen most often  ·  Jul–Sep 2026",
         fontsize=11, color="#444444", ha="left", va="center")

y = np.arange(len(hospitals))

# --- Left panel: median wait by triage category ---
# Shade Riverside's row so it is found first.
ax1.axhspan(-0.5, 0.5, color="#FDEDEC", zorder=0)

for cat in categories:
    vals = (
        df[df["triage_category"] == cat]
        .set_index("hospital")["median_adj"]
        .reindex(hospitals)
    )
    bars = ax1.barh(
        y + cat_offsets[cat], vals, height=0.22,
        color=cat_colors[cat], label=cat, zorder=3,
    )
    # Outline Riverside's bars and label only its values (avoids clutter).
    bars[0].set_edgecolor("black")
    bars[0].set_linewidth(1.2)
    ax1.text(vals.iloc[0] + 4, cat_offsets[cat], f"{vals.iloc[0]:.0f}",
             va="center", ha="left", fontsize=10, fontweight="bold", color="#922B21")

ax1.set_yticks(y)
ax1.set_yticklabels(
    [f"{h}{'*' if h == 'Northgate' else ''}  ({totals[h] / 1000:.1f}k visits)"
     for h in hospitals],
    fontsize=10,
)
for label in ax1.get_yticklabels():
    if label.get_text().startswith("Riverside"):
        label.set_fontweight("bold")
        label.set_color("#922B21")
        label.set_fontsize(12)

ax1.invert_yaxis()  # worst at the top
ax1.set_xlim(0, 225)
ax1.set_xlabel("Median wait to first be seen by a doctor (minutes)", fontsize=11)
ax1.set_title("Worst in every triage category", fontsize=12, fontweight="bold")
ax1.legend(title="Triage category", loc="lower right", frameon=False, fontsize=9, title_fontsize=9)
ax1.grid(axis="x", color="#DDDDDD", linewidth=0.7, zorder=0)
ax1.tick_params(axis="x", labelsize=10)

# --- Right panel: left without being seen ---
bar_colors = ["#C0392B" if h == "Riverside" else "#7A8694" for h in hospitals]
ax2.barh(y, lwbs.values, height=0.55, color=bar_colors, zorder=3)
ax2.axhspan(-0.5, 0.5, color="#FDEDEC", zorder=0)
ax2.axvline(lwbs_others, color="black", linestyle="--", linewidth=1.1, zorder=4)
ax2.text(lwbs_others, len(hospitals) - 0.25, f"  other 7 hospitals:\n  {lwbs_others:.1f}%",
         fontsize=8.5, va="bottom", ha="left", color="black")

for yi, (h, v) in enumerate(lwbs.items()):
    ax2.text(v + 0.2, yi, f"{v:.1f}%",
             va="center", ha="left", fontsize=10,
             fontweight="bold" if h == "Riverside" else "normal",
             color="#922B21" if h == "Riverside" else "#444444")

ax2.set_xlim(0, 11.5)
ax2.set_xlabel("Left without being seen", fontsize=11)
ax2.set_title("Three times more walk away unseen", fontsize=12, fontweight="bold")
ax2.grid(axis="x", color="#DDDDDD", linewidth=0.7, zorder=0)
ax2.tick_params(axis="x", labelsize=10)
ax2.tick_params(axis="y", length=0)

for ax in (ax1, ax2):
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

fig.text(
    0.04, 0.02,
    "*Northgate's clock starts at registration (all others: triage), so 15 minutes were subtracted from its waits "
    "(unadjusted urgent median: 41 min).\n"
    "Left-without-being-seen is visit-weighted across triage categories; the same ordering holds for 90th-percentile waits.\n"
    "Riverside is mid-sized (34 staffed beds) and not the busiest (Central: 14.8k visits), so volume alone does not explain its waits.",
    fontsize=8, color="#555555", ha="left", va="bottom",
)
