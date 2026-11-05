import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

df = pd.read_csv("data.csv")
q = "My manager supports my growth"
sub = df[df["question"] == q]

scores = sub.pivot_table(index="department", columns="year", values="pct_favourable")
resp = sub[sub["year"] == 2026].set_index("department")[["response_rate_pct", "n_responses", "headcount"]]
resp25 = sub[sub["year"] == 2025].set_index("department")["response_rate_pct"]

# Lowest 2026 score at the top
scores = scores.sort_values(2026)
depts = list(scores.index)
n = len(depts)
ypos = {d: n - 1 - i for i, d in enumerate(depts)}

HIGHLIGHT = "#C8102E"
BASE = "#5B6770"
LIGHT = "#B8C0C6"

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.17, right=0.84, top=0.80, bottom=0.12)

for d in depts:
    y = ypos[d]
    v25, v26 = scores.loc[d, 2025], scores.loc[d, 2026]
    is_hl = d == "Customer Support"
    col = HIGHLIGHT if is_hl else BASE
    ax.plot([v25, v26], [y, y], color=col if is_hl else LIGHT,
            lw=3 if is_hl else 2, zorder=1, solid_capstyle="round")
    ax.scatter(v25, y, s=70, facecolor="white", edgecolor=col if is_hl else LIGHT,
               linewidth=2, zorder=2)
    ax.scatter(v26, y, s=110 if is_hl else 80, color=col, zorder=3)

    # 2026 value label, placed away from the 2025 dot
    if v26 <= v25:
        ax.text(v26 - 1.3, y, f"{v26:.0f}%", ha="right", va="center",
                fontsize=12 if is_hl else 10, color=col,
                fontweight="bold" if is_hl else "normal")
    else:
        ax.text(v26 + 1.3, y, f"{v26:.0f}%", ha="left", va="center",
                fontsize=10, color=col)
    if is_hl:
        ax.text(v25 + 1.3, y, f"{v25:.0f}% in 2025", ha="left", va="center",
                fontsize=9.5, color=BASE)

    # Response-rate column on the right
    r = resp.loc[d]
    ax.text(1.03, y, f"{r['response_rate_pct']:.0f}%", transform=ax.get_yaxis_transform(),
            ha="left", va="center", fontsize=10.5 if is_hl else 10,
            color=HIGHLIGHT if is_hl else BASE, fontweight="bold" if is_hl else "normal")

ax.text(1.03, n - 0.35, "Responded\n(2026)", transform=ax.get_yaxis_transform(),
        ha="left", va="bottom", fontsize=9, color=BASE)

# Caveat annotation next to Support
y_cs = ypos["Customer Support"]
r = resp.loc["Customer Support"]
ax.text(80, y_cs - 0.45,
        f"−27 pts: largest drop on any question\n"
        f"Caution: only {r['n_responses']:.0f} of {r['headcount']:.0f} answered "
        f"({r['response_rate_pct']:.0f}%,\nvs {resp25['Customer Support']:.0f}% in 2025), "
        f"so this result is less certain",
        ha="center", va="top", fontsize=9.5, color=HIGHLIGHT, linespacing=1.35)

# Axes styling
ax.set_yticks([ypos[d] for d in depts])
ax.set_yticklabels(depts, fontsize=11)
for lab in ax.get_yticklabels():
    if lab.get_text() == "Customer Support":
        lab.set_color(HIGHLIGHT)
        lab.set_fontweight("bold")
    else:
        lab.set_color("#333333")

ax.set_xlim(35, 95)
ax.set_ylim(-0.6, n - 0.4)
ax.set_xticks(range(40, 91, 10))
ax.set_xticklabels([f"{x}%" for x in range(40, 91, 10)], fontsize=9.5, color=BASE)
ax.set_xlabel("% favourable (agree or strongly agree)", fontsize=9.5, color=BASE)
ax.grid(axis="x", color="#E6E6E6", lw=1)
ax.set_axisbelow(True)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(LIGHT)
ax.tick_params(axis="y", length=0)
ax.tick_params(axis="x", length=0)

legend_items = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor="white",
           markeredgecolor=BASE, markeredgewidth=2, markersize=8, label="Sept 2025"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor=BASE,
           markersize=9, label="Sept 2026"),
]
ax.legend(handles=legend_items, loc="lower right", frameon=False, fontsize=9.5)

fig.text(0.02, 0.94,
         "Customer Support has the weakest manager support: 44%, down from 71%",
         fontsize=15, fontweight="bold", color="#1A1A1A", ha="left")
fig.text(0.02, 0.885,
         "\u2018My manager supports my growth\u2019, % favourable by department. "
         "Every other department is at 58% or above and roughly flat.",
         fontsize=10.5, color=BASE, ha="left")

fig.text(0.02, 0.025,
         "Source: Northlight employee survey, 8\u201322 September 2026 and September 2025.",
         fontsize=8.5, color="#8A8A8A", ha="left")
