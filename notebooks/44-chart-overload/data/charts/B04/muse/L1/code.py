import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")
df["variance_m"] = df["variance_k"] / 1000.0

# Department totals, sorted so the largest overspend is at the top
dept = (
    df.groupby("department", as_index=False)["variance_m"]
    .sum()
    .sort_values("variance_m", ascending=True)
    .reset_index(drop=True)
)
total_m = dept["variance_m"].sum()
transit_total = dept.loc[dept["department"] == "Transit", "variance_m"].iloc[0]
transit_share = 100 * transit_total / total_m
roads_total = dept.loc[dept["department"] == "Roads", "variance_m"].iloc[0]
roads_y = dept.index[dept["department"] == "Roads"][0]
winter_extra = 1.5  # analyst note: harsh winter could add up to $1.5M

# Transit breakdown by budget line
transit = (
    df[df["department"] == "Transit"]
    .sort_values("variance_m", ascending=True)
    .reset_index(drop=True)
)
ot_row = transit[transit["budget_line"] == "Overtime"].iloc[0]

RED = "#b2182b"
LIGHT_RED = "#e08a7b"
UNDER = "#5b8ca8"
GREY = "#666666"

fig = plt.figure(figsize=(10, 6))
gs = fig.add_gridspec(1, 2, width_ratios=[1.55, 1.0], wspace=0.30)
ax = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])

# ---- Left panel: every department ----
colors = [
    RED if d == "Transit" else (LIGHT_RED if v > 0 else UNDER)
    for d, v in zip(dept["department"], dept["variance_m"])
]
ax.barh(dept["department"], dept["variance_m"], color=colors, height=0.62, zorder=3)

# Roads winter-risk extension (forecast assumes five-year-average snow)
ax.barh(
    roads_y, winter_extra, left=roads_total, height=0.62,
    facecolor="white", edgecolor=RED, hatch="///", linewidth=1.0, zorder=3,
)
ax.annotate(
    f"harsh winter:\nup to +${roads_total + winter_extra:.1f}M",
    xy=(roads_total + winter_extra, roads_y),
    xytext=(roads_total + winter_extra + 0.08, roads_y + 0.55),
    fontsize=8, color=RED, va="center",
    arrowprops=dict(arrowstyle="-", color=RED, lw=1.0),
)

for y, v in enumerate(dept["variance_m"]):
    label = f"+${v:.1f}M" if v > 0 else (f"-${abs(v):.1f}M" if v < 0 else "$0")
    if v >= 0:
        x = v + (winter_extra + 0.08 if dept.loc[y, "department"] == "Roads" else 0.08)
        # for Roads the value sits just right of its solid bar, before the hatch label
        if dept.loc[y, "department"] == "Roads":
            x = v - 0.08
            ax.text(x, y, label, va="center", ha="right", fontsize=9,
                    fontweight="bold", color="white", zorder=4)
            continue
        ax.text(x, y, label, va="center", ha="left", fontsize=9,
                fontweight="bold" if dept.loc[y, "department"] == "Transit" else "normal",
                color=RED if dept.loc[y, "department"] == "Transit" else GREY)
    else:
        ax.text(v - 0.08, y, label, va="center", ha="right", fontsize=9, color=UNDER)

for lbl in ax.get_yticklabels():
    if lbl.get_text() == "Transit":
        lbl.set_fontweight("bold")
        lbl.set_color(RED)
ax.tick_params(axis="y", labelsize=10)
ax.tick_params(axis="x", labelsize=9)
ax.axvline(0, color="black", linewidth=1.0, zorder=4)
ax.set_xlim(-0.75, 3.95)
ax.set_xticks([-0.5, 0, 1, 2, 3])
ax.set_xticklabels(["-$0.5M", "$0", "$1M", "$2M", "$3M"])
ax.set_xlabel("Forecast year-end variance vs budget  ($ million)  →  overspend", fontsize=9)
ax.set_title("Forecast overspend by department", fontsize=11, fontweight="bold", loc="left", pad=10)
ax.grid(axis="x", color="#dddddd", linewidth=0.7, zorder=0)
ax.set_axisbelow(True)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)

# ---- Right panel: why Transit ----
tcolors = [RED if b == "Overtime" else (LIGHT_RED if v > 0 else UNDER)
           for b, v in zip(transit["budget_line"], transit["variance_m"])]
ax2.barh(transit["budget_line"], transit["variance_m"], color=tcolors, height=0.58, zorder=3)
for y, v in enumerate(transit["variance_m"]):
    label = f"+${v:.1f}M" if v > 0 else f"-${abs(v):.1f}M"
    ax2.text(v + 0.07 if v >= 0 else v - 0.07, y, label, va="center",
             ha="left" if v >= 0 else "right", fontsize=9,
             fontweight="bold" if transit.loc[y, "budget_line"] == "Overtime" else "normal",
             color=RED if transit.loc[y, "budget_line"] == "Overtime" else GREY)
for lbl in ax2.get_yticklabels():
    if lbl.get_text() == "Overtime":
        lbl.set_fontweight("bold")
        lbl.set_color(RED)
ax2.tick_params(axis="y", labelsize=10)
ax2.tick_params(axis="x", labelsize=9)
ax2.axvline(0, color="black", linewidth=1.0, zorder=4)
ax2.set_xlim(-0.45, 3.05)
ax2.set_xticks([0, 1, 2])
ax2.set_xticklabels(["$0", "$1M", "$2M"])
ax2.set_xlabel("Variance vs budget  ($ million)", fontsize=9)
ax2.set_title("Inside Transit: overtime is the problem",
              fontsize=11, fontweight="bold", loc="left", pad=10)
ax2.grid(axis="x", color="#dddddd", linewidth=0.7, zorder=0)
ax2.set_axisbelow(True)
for s in ["top", "right", "left"]:
    ax2.spines[s].set_visible(False)

ot_y = transit.index[transit["budget_line"] == "Overtime"][0]
ax2.annotate(
    f"+{ot_row['variance_pct']:.0f}% over its\n${ot_row['annual_budget_k']/1000:.1f}M overtime budget\n(driver vacancies)",
    xy=(ot_row["variance_m"], ot_y),
    xytext=(1.15, ot_y - 1.55),
    fontsize=8.5, color=RED, va="center",
    arrowprops=dict(arrowstyle="->", color=RED, lw=1.2),
)

# ---- Headline: the decision, readable in seconds ----
fig.text(0.06, 0.96, "Put Transit under mid-year spending review",
         fontsize=16, fontweight="bold", ha="left", va="top")
fig.text(
    0.06, 0.905,
    f"Transit drives {transit_share:.0f}% (${transit_total:.1f}M) of the city's "
    f"${total_m:.1f}M forecast overspend — mostly overtime.  Watch Roads second (winter risk).",
    fontsize=10.5, color="#333333", ha="left", va="top",
)
fig.text(
    0.06, 0.015,
    "Positive = forecast overspend vs annual budget. Roads forecast assumes five-year-average snow clearing. Source: data.csv.",
    fontsize=7.5, color=GREY, ha="left",
)

fig.tight_layout(rect=[0, 0.035, 1, 0.875])
