import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

HIGHLIGHT = "#C0392B"
GREY = "#BFBFBF"
DARK = "#404040"
FOCUS = "Riverside"

# Urgent median wait, reported and on a triage-to-doctor basis
urg = df[df["triage_category"] == "Urgent"].set_index("hospital")
reported = urg["median_wait_min"].astype(float)
adjusted = reported.copy()
reg_start = urg.index[urg["wait_clock_starts_at"] == "registration"]
adjusted[reg_start] = adjusted[reg_start] - 15  # registration clock adds ~15 min

others_avg_wait = reported.drop(FOCUS).mean()  # ~28 min

# Left without being seen, weighted by visits across all triage categories
df["lwbs_n"] = df["visits"] * df["left_without_being_seen_pct"] / 100
g = df.groupby("hospital")[["lwbs_n", "visits"]].sum()
lwbs = g["lwbs_n"] / g["visits"] * 100
others = g.drop(FOCUS)
others_avg_lwbs = others["lwbs_n"].sum() / others["visits"].sum() * 100  # ~3.2%

# Same hospital order on both panels: longest like-for-like urgent wait at top
order = adjusted.sort_values().index.tolist()
y = np.arange(len(order))
colors = [HIGHLIGHT if h == FOCUS else GREY for h in order]

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), sharey=True,
    gridspec_kw={"width_ratios": [1.35, 1], "wspace": 0.12}
)

# ---- Left panel: urgent median wait ----
ax1.barh(y, adjusted[order].values, color=colors, height=0.7, zorder=2)

# Northgate: show reported value as a dashed outline behind the adjusted bar
for h in reg_start:
    yi = order.index(h)
    ax1.barh(yi, reported[h], height=0.7, facecolor="none", edgecolor="#8C8C8C",
             linestyle="--", linewidth=1, zorder=1)
    ax1.text(reported[h] + 1.2, yi,
             f"{h} reports {reported[h]:.0f} min, but its clock\n"
             f"starts at registration (~15 min earlier).\n"
             f"Like-for-like: ~{adjusted[h]:.0f} min, not 2nd-slowest",
             va="center", ha="left", fontsize=8, color=DARK)

ri = order.index(FOCUS)
ax1.text(reported[FOCUS] + 1, ri, f"{reported[FOCUS]:.0f} min",
         va="center", ha="left", fontsize=12, fontweight="bold", color=HIGHLIGHT)

ax1.axvline(others_avg_wait, color=DARK, linestyle=":", linewidth=1.2, zorder=3)
ax1.text(others_avg_wait + 0.8, -0.85, f"Other 7 avg: {others_avg_wait:.0f} min",
         fontsize=8.5, color=DARK, va="center", ha="left")

ax1.set_xlim(0, 78)
ax1.set_xlabel("Minutes from arrival to first seen by a doctor", fontsize=9, color=DARK)
ax1.set_title("Urgent patients: median wait", loc="left", fontsize=11,
              fontweight="bold", color=DARK)

# ---- Right panel: left without being seen ----
ax2.barh(y, lwbs[order].values, color=colors, height=0.7, zorder=2)
ax2.text(lwbs[FOCUS] + 0.15, ri, f"{lwbs[FOCUS]:.1f}%",
         va="center", ha="left", fontsize=12, fontweight="bold", color=HIGHLIGHT)
ax2.axvline(others_avg_lwbs, color=DARK, linestyle=":", linewidth=1.2, zorder=3)
ax2.text(others_avg_lwbs + 0.15, -0.85, f"Other 7 avg: {others_avg_lwbs:.1f}%",
         fontsize=8.5, color=DARK, va="center", ha="left")
ax2.set_xlim(0, 11.5)
ax2.set_xlabel("% of all visits", fontsize=9, color=DARK)
ax2.set_title("Patients leaving without being seen", loc="left", fontsize=11,
              fontweight="bold", color=DARK)

# ---- Shared styling ----
for ax in (ax1, ax2):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#999999")
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", colors=DARK, labelsize=9)
    ax.set_ylim(-1.3, len(order) - 0.4)

ax1.set_yticks(y)
ax1.set_yticklabels(order, fontsize=10)
for lbl in ax1.get_yticklabels():
    if lbl.get_text() == FOCUS:
        lbl.set_color(HIGHLIGHT)
        lbl.set_fontweight("bold")
    else:
        lbl.set_color(DARK)

fig.text(0.02, 0.965,
         "Riverside's urgent patients wait twice as long as elsewhere,\n"
         "and nearly 3× as many patients leave without being seen",
         fontsize=15, fontweight="bold", color="#202020", ha="left", va="top")

fig.text(0.02, 0.015,
         "Lakeshore Health emergency departments, July–September 2026. "
         "Bars for Northgate show its wait adjusted to the triage-start basis used by the other hospitals.",
         fontsize=7.5, color="#777777", ha="left", va="bottom")

fig.subplots_adjust(left=0.11, right=0.97, top=0.80, bottom=0.12)
