import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

# Read and prepare data
df = pd.read_csv("data.csv")
question = "My manager supports my growth"

current = (
    df[(df["question"] == question) & (df["year"] == 2026)]
    [["department", "pct_favourable", "n_responses", "headcount", "response_rate_pct"]]
    .rename(columns={"pct_favourable": "fav_2026"})
)

previous = (
    df[(df["question"] == question) & (df["year"] == 2025)]
    [["department", "pct_favourable", "response_rate_pct"]]
    .rename(columns={"pct_favourable": "fav_2025", "response_rate_pct": "rr_2025"})
)

plot = (
    current.merge(previous, on="department", how="left")
    .sort_values("fav_2026", ascending=True)
    .reset_index(drop=True)
)

support_idx = plot.index[plot["department"] == "Customer Support"][0]
support = plot.loc[support_idx]

# The next-lowest department gives useful context for the size of the gap
next_idx = support_idx + 1
next_row = plot.loc[next_idx]

gap = next_row["fav_2026"] - support["fav_2026"]
drop = support["fav_2025"] - support["fav_2026"]

# Chart
fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

y = np.arange(len(plot))
colors = [
    "#C8102E" if dept == "Customer Support" else "#C9C9C9"
    for dept in plot["department"]
]

ax.barh(y, plot["fav_2026"], color=colors, height=0.62, edgecolor="none", zorder=3)

ax.set_yticks(y)
ax.set_yticklabels(plot["department"], fontsize=11)

for label, dept in zip(ax.get_yticklabels(), plot["department"]):
    if dept == "Customer Support":
        label.set_color("#C8102E")
        label.set_fontweight("bold")
    else:
        label.set_color("#444444")

ax.invert_yaxis()

ax.set_xlim(0, 100)
ax.set_xticks([0, 20, 40, 60, 80, 100])
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{int(x)}%"))
ax.set_xlabel("% favourable, 2026", fontsize=11, color="#333333")

ax.grid(axis="x", color="#D9D9D9", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
ax.tick_params(axis="x", colors="#555555", labelsize=10)
ax.tick_params(axis="y", length=0)

for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color("#BBBBBB")

# Direct labels only where they support the decision
ax.text(
    support["fav_2026"] + 2,
    support_idx,
    f"{support['fav_2026']:.0f}%  (was {support['fav_2025']:.0f}%)",
    va="center",
    ha="left",
    fontsize=12,
    fontweight="bold",
    color="#C8102E",
)

ax.text(
    next_row["fav_2026"] + 2,
    next_idx,
    f"{next_row['fav_2026']:.0f}%",
    va="center",
    ha="left",
    fontsize=10,
    color="#666666",
)

ax.set_title(
    "Customer Support needs the manager-support programme most:\n"
    f"{support['fav_2026']:.0f}% favourable — {gap:.0f} points below any other department "
    f"and down {drop:.0f} points from 2025",
    fontsize=15,
    fontweight="bold",
    loc="left",
    pad=18,
    color="#111111",
)

fig.text(
    0.02,
    0.035,
    "Question: “My manager supports my growth.”  "
    f"Caveat: Customer Support’s 2026 response rate was {support['response_rate_pct']:.0f}% "
    f"(n={support['n_responses']:.0f}) vs {support['rr_2025']:.0f}% in 2025.",
    fontsize=9,
    color="#555555",
    ha="left",
)

fig.subplots_adjust(left=0.19, right=0.96, top=0.80, bottom=0.17)
