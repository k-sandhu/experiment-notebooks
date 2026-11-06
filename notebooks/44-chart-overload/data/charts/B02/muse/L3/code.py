import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Urgent median waits (reported), with Northgate adjusted for its earlier clock start
urgent = df[df["triage_category"] == "Urgent"].copy()
urgent["wait_like_for_like"] = urgent["median_wait_min"]
northgate_mask = urgent["hospital"] == "Northgate"
urgent.loc[northgate_mask, "wait_like_for_like"] -= 15  # registration adds ~15 min

# Left without being seen: visit-weighted rate across all triage categories, per hospital
lwbs = (
    df.assign(left=df["visits"] * df["left_without_being_seen_pct"] / 100)
    .groupby("hospital")
    .apply(lambda g: 100 * g["left"].sum() / g["visits"].sum(), include_groups=False)
    .rename("lwbs_pct")
)

data = urgent.set_index("hospital").join(lwbs)
data = data.sort_values("wait_like_for_like", ascending=True)  # ascending for barh (largest on top)

riverside_wait = data.loc["Riverside", "median_wait_min"]
avg_other_wait = data.loc[data.index != "Riverside", "median_wait_min"].mean()
riverside_lwbs = data.loc["Riverside", "lwbs_pct"]
avg_other_lwbs = data.loc[data.index != "Riverside", "lwbs_pct"].mean()
northgate_reported = data.loc["Northgate", "median_wait_min"]
northgate_adjusted = data.loc["Northgate", "wait_like_for_like"]

STRONG = "#C1272D"
GREY = "#B8B8B8"
DARK = "#333333"

colours = [STRONG if h == "Riverside" else GREY for h in data.index]
y_pos = range(len(data))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6), sharey=True,
                               gridspec_kw={"width_ratios": [1.35, 1], "wspace": 0.08})

fig.suptitle("Riverside needs the extra triage nurses: urgent waits are twice\n"
             "the network average and most patients leave unseen",
             fontsize=15, fontweight="bold", color=DARK, x=0.07, ha="left")

# --- Left panel: median wait, urgent patients ---
ax1.barh(y_pos, data["wait_like_for_like"], color=colours, height=0.62)
# Northgate: hatched segment = extra ~15 min from starting the clock at registration
ng_y = list(data.index).index("Northgate")
ax1.barh(ng_y, northgate_reported - northgate_adjusted, left=northgate_adjusted,
         color="white", edgecolor="#888888", hatch="///", height=0.62)
ax1.annotate(f"Northgate: {northgate_reported:.0f} min reported,\n"
             f"~{northgate_adjusted:.0f} min like-for-like (see note)",
             xy=(northgate_reported + 1, ng_y), va="center", fontsize=8, color=DARK)

ax1.axvline(avg_other_wait, color=DARK, linestyle="--", linewidth=1.2)
ax1.text(avg_other_wait, len(data) - 0.25, f"  Other 7 average: {avg_other_wait:.0f} min",
         fontsize=8.5, color=DARK, va="bottom")

rv_y = list(data.index).index("Riverside")
ax1.text(riverside_wait + 1.5, rv_y, f"{riverside_wait:.0f} min",
         fontsize=11, fontweight="bold", color=STRONG, va="center")

ax1.set_yticks(list(y_pos))
ax1.set_yticklabels(data.index, fontsize=10)
for label in ax1.get_yticklabels():
    if label.get_text() == "Riverside":
        label.set_fontweight("bold")
        label.set_color(STRONG)
ax1.set_xlabel("Median wait, urgent patients (minutes)", fontsize=10)
ax1.set_title("Median wait — urgent patients", fontsize=11, fontweight="bold", loc="left", color=DARK)
ax1.set_xlim(0, 72)
ax1.xaxis.grid(True, color="#E5E5E5", linewidth=0.7)
ax1.set_axisbelow(True)

# --- Right panel: left without being seen ---
ax2.barh(y_pos, data["lwbs_pct"], color=colours, height=0.62)
ax2.axvline(avg_other_lwbs, color=DARK, linestyle="--", linewidth=1.2)
ax2.text(avg_other_lwbs, len(data) - 0.25, f"  Other 7 average: {avg_other_lwbs:.1f}%",
         fontsize=8.5, color=DARK, va="bottom")
ax2.text(riverside_lwbs + 0.2, rv_y, f"{riverside_lwbs:.1f}%",
         fontsize=11, fontweight="bold", color=STRONG, va="center")

ax2.set_xlabel("Left without being seen (% of visits)", fontsize=10)
ax2.set_title("Left without being seen — all visits", fontsize=11, fontweight="bold", loc="left", color=DARK)
ax2.set_xlim(0, 11.5)
ax2.xaxis.grid(True, color="#E5E5E5", linewidth=0.7)
ax2.set_axisbelow(True)
ax2.tick_params(labelleft=False)

for ax in (ax1, ax2):
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#888888")
    ax.tick_params(axis="x", labelsize=9)

fig.text(0.07, 0.015,
         "Urgent patients, July–September 2026. Northgate starts its wait clock at registration, not triage, "
         "adding ~15 minutes;\nthe hatched segment is that add-on, so Northgate is not really the second-slowest.",
         fontsize=8, color="#555555", ha="left")

plt.tight_layout(rect=[0, 0.06, 1, 0.88])
