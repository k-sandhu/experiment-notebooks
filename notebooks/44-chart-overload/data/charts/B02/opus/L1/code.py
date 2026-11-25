import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Visit-weighted share of patients who left without being seen, per hospital
df["lwbs_n"] = df["visits"] * df["left_without_being_seen_pct"] / 100
hosp = df.groupby("hospital").agg(visits=("visits", "sum"), lwbs_n=("lwbs_n", "sum"))
hosp["lwbs_pct"] = 100 * hosp["lwbs_n"] / hosp["visits"]

others = hosp.drop(index="Riverside")
others_lwbs = 100 * others["lwbs_n"].sum() / others["visits"].sum()

# Order: worst at the top
order = hosp.sort_values("lwbs_pct").index.tolist()
ypos = {h: i for i, h in enumerate(order)}

waits = df.pivot(index="hospital", columns="triage_category", values="median_wait_min")
cats = ["Urgent", "Semi-urgent", "Non-urgent"]
markers = {"Urgent": "o", "Semi-urgent": "s", "Non-urgent": "D"}

clock = df.groupby("hospital")["wait_clock_starts_at"].first()

HIGHLIGHT = "#c0392b"
GREY = "#9a9a9a"
DARK = "#333333"

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), sharey=True,
    gridspec_kw={"width_ratios": [1.7, 1], "wspace": 0.08}
)
fig.subplots_adjust(left=0.13, right=0.97, top=0.80, bottom=0.17)

# ---- Left panel: median wait to see a doctor, by triage category ----
for h in order:
    y = ypos[h]
    col = HIGHLIGHT if h == "Riverside" else GREY
    vals = waits.loc[h, cats].values
    ax1.plot([vals.min(), vals.max()], [y, y], color=col, lw=2,
             alpha=0.5, zorder=1)
    for c in cats:
        ax1.scatter(waits.loc[h, c], y, marker=markers[c], s=60,
                    color=col, edgecolor="white", linewidth=0.8, zorder=2)

# Label Riverside's values
r = ypos["Riverside"]
for c in cats:
    v = waits.loc["Riverside", c]
    ax1.annotate(f"{v:.0f}", (v, r), xytext=(0, 9), textcoords="offset points",
                 ha="center", va="bottom", fontsize=9, color=HIGHLIGHT,
                 fontweight="bold")

ax1.set_xlim(0, 225)
ax1.set_xlabel("Median minutes until first seen by a doctor")
ax1.set_title("Median wait, by triage category", loc="left",
              fontsize=11, color=DARK)

# Legend for marker shapes
for c in cats:
    ax1.scatter([], [], marker=markers[c], s=50, color=DARK, label=c)
ax1.legend(loc="lower right", frameon=False, fontsize=9,
           handletextpad=0.3, borderaxespad=0.2)

# ---- Right panel: % left without being seen ----
bar_cols = [HIGHLIGHT if h == "Riverside" else GREY for h in order]
ax2.barh(range(len(order)), hosp.loc[order, "lwbs_pct"], color=bar_cols,
         height=0.6)
for h in order:
    v = hosp.loc[h, "lwbs_pct"]
    ax2.text(v + 0.2, ypos[h], f"{v:.1f}%", va="center", fontsize=9,
             color=HIGHLIGHT if h == "Riverside" else DARK,
             fontweight="bold" if h == "Riverside" else "normal")
ax2.set_xlim(0, 11.5)
ax2.set_xlabel("% of visits")
ax2.set_title("Left without being seen", loc="left",
              fontsize=11, color=DARK)

# Y labels (flag the hospital with a different wait-clock definition)
labels = [f"{h}*" if clock[h] != "triage" else h for h in order]
ax1.set_yticks(range(len(order)))
ax1.set_yticklabels(labels, fontsize=10)
for tick, h in zip(ax1.get_yticklabels(), order):
    if h == "Riverside":
        tick.set_color(HIGHLIGHT)
        tick.set_fontweight("bold")

for ax in (ax1, ax2):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#e5e5e5", lw=0.8)
    ax.set_axisbelow(True)

# Headline
fig.text(0.02, 0.945,
         "Riverside has the longest waits and the most patients leaving unseen",
         fontsize=15, fontweight="bold", color=DARK, ha="left")
fig.text(0.02, 0.885,
         f"Riverside's waits are the longest in every triage category; "
         f"{hosp.loc['Riverside', 'lwbs_pct']:.1f}% of its visits left before "
         f"seeing a doctor vs {others_lwbs:.1f}% at the other seven EDs",
         fontsize=10.5, color="#555555", ha="left")

# Footnotes
fig.text(0.02, 0.045,
         "*Northgate starts its wait clock at registration; the other EDs start at triage, "
         "so its waits are not directly comparable.\n"
         "Emergency department visits, July to September 2026. "
         "Left-without-being-seen rate is weighted by visits across triage categories.",
         fontsize=8, color="#666666", ha="left", va="bottom")
