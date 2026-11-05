import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

categories = ["Urgent", "Semi-urgent", "Non-urgent"]
colors = {
    "Urgent": "#B2182B",
    "Semi-urgent": "#E08214",
    "Non-urgent": "#4A6FA5",
}

# Order hospitals by urgent median wait, longest first
urgent = (
    df[df["triage_category"] == "Urgent"]
    .sort_values("median_wait_min", ascending=False)
)
hospitals = urgent["hospital"].tolist()

totals = df.groupby("hospital")["visits"].sum()
labels = [f"{h}\n({totals[h]:,} visits)" for h in hospitals]

median_pivot = (
    df.pivot(index="hospital", columns="triage_category", values="median_wait_min")
    .reindex(index=hospitals, columns=categories)
)

# Visit-weighted overall left-without-being-seen rate per hospital.
# (Medians are NOT averaged across triage categories.)
lwbs = (
    df.assign(lwbs_visits=df["visits"] * df["left_without_being_seen_pct"] / 100)
      .groupby("hospital")
      .apply(lambda g: 100 * g["lwbs_visits"].sum() / g["visits"].sum(), include_groups=False)
      .reindex(hospitals)
)

other = df[df["hospital"] != "Riverside"]
others_lwbs = 100 * (other["visits"] * other["left_without_being_seen_pct"] / 100).sum() / other["visits"].sum()

fig, (ax0, ax1) = plt.subplots(
    1, 2, figsize=(10, 6), sharey=True,
    gridspec_kw={"width_ratios": [2.3, 1.0], "wspace": 0.08},
)

y = np.arange(len(hospitals))
height = 0.22
offsets = {"Urgent": -height, "Semi-urgent": 0.0, "Non-urgent": height}
northgate_idx = hospitals.index("Northgate")

for cat in categories:
    values = median_pivot[cat].to_numpy()
    bars = ax0.barh(
        y + offsets[cat], values, height=height,
        color=colors[cat], label=cat, edgecolor="white", linewidth=0.5,
    )
    # Northgate uses a different wait-clock start; hatch to flag non-comparability
    bars[northgate_idx].set_hatch("///")
    bars[northgate_idx].set_edgecolor("black")
    bars[northgate_idx].set_linewidth(0.6)

    for yi, v in zip(y + offsets[cat], values):
        ax0.text(v + 3, yi, f"{v:.0f}", va="center", ha="left", fontsize=7)

# Approximate like-for-like Northgate values: registration clock adds ~15 min
for i, cat in enumerate(categories):
    ax0.plot(
        median_pivot.loc["Northgate", cat] - 15,
        northgate_idx + offsets[cat],
        marker="D", color="black", markersize=4,
        label="Northgate adjusted (≈ −15 min)" if i == 0 else None,
    )

ax0.set_yticks(y)
ax0.set_yticklabels(labels, fontsize=8)
ax0.invert_yaxis()
ax0.set_xlim(0, 228)
ax0.set_xlabel("Median wait, arrival to first seen by a doctor (minutes)")
ax0.set_title("Median wait by triage category", loc="left", fontsize=11, fontweight="bold")
ax0.legend(frameon=False, fontsize=8, loc="lower right")
ax0.grid(axis="x", color="#CCCCCC", linewidth=0.6, alpha=0.6)
ax0.set_axisbelow(True)
ax0.annotate(
    "Lakeview: shortest\nin every category",
    xy=(median_pivot.loc["Lakeview", "Non-urgent"], len(hospitals) - 1 + height),
    xytext=(105, len(hospitals) - 1.55),
    fontsize=8,
    arrowprops=dict(arrowstyle="->", color="black", lw=0.8),
)

bar_colors = ["#B2182B" if h == "Riverside" else "#4A6FA5" for h in hospitals]
ax1.barh(y, lwbs.to_numpy(), height=0.55, color=bar_colors, edgecolor="white")
for yi, v in zip(y, lwbs.to_numpy()):
    ax1.text(v + 0.18, yi, f"{v:.1f}%", va="center", ha="left", fontsize=8)

ax1.axvline(others_lwbs, color="black", linestyle="--", linewidth=1)
ax1.text(
    others_lwbs + 0.15, -0.65,
    f"Other hospitals: {others_lwbs:.1f}%",
    fontsize=8, va="bottom",
)
ax1.set_xlim(0, max(lwbs) * 1.28)
ax1.set_xlabel("Left without being seen\n(% of visits, visit-weighted)")
ax1.set_title("Left without being seen", loc="left", fontsize=11, fontweight="bold")
ax1.grid(axis="x", color="#CCCCCC", linewidth=0.6, alpha=0.6)
ax1.set_axisbelow(True)

for ax in (ax0, ax1):
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(labelsize=8)

fig.suptitle(
    "Riverside has the longest waits — and by far the most patients leaving unseen",
    x=0.015, ha="left", fontsize=13.5, fontweight="bold",
)
fig.text(0.015, 0.935, "Emergency departments, July–September 2026  •  Hospitals ordered by urgent median wait",
         ha="left", fontsize=9, color="#444444")
fig.text(
    0.015, 0.015,
    "Note: Northgate (hatched) starts its wait clock at registration, not triage like the other hospitals, inflating waits by about 15 minutes;\n"
    "black diamonds show the approximate like-for-like values. Median waits are shown separately by triage and are not averaged across categories.",
    ha="left", va="bottom", fontsize=7.5, color="#444444",
)

fig.tight_layout(rect=[0, 0.055, 1, 0.92])
