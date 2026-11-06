import pandas as pd
import matplotlib.pyplot as plt

# Read data
df = pd.read_csv("data.csv")
question = "My manager supports my growth"

# Current year and previous year for the manager-support question
current = df[(df["question"] == question) & (df["year"] == 2026)].copy()
previous = (
    df[(df["question"] == question) & (df["year"] == 2025)][["department", "pct_favourable"]]
    .rename(columns={"pct_favourable": "prev_pct"})
)

current = current.merge(previous, on="department", how="left")
current = current.sort_values("pct_favourable", ascending=True).reset_index(drop=True)

# Key numbers
support_row = current.index[current["department"] == "Customer Support"][0]
support_val = current.loc[support_row, "pct_favourable"]
support_prev = current.loc[support_row, "prev_pct"]
drop = support_prev - support_val

sales_row = current.index[current["department"] == "Sales"][0]
sales_val = current.loc[sales_row, "pct_favourable"]

# Chart
fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

colors = [
    "#C8102E" if dept == "Customer Support" else "#BDBDBD"
    for dept in current["department"]
]

y = list(range(len(current)))
ax.barh(y, current["pct_favourable"], color=colors, height=0.64, edgecolor="none", zorder=3)

ax.set_yticks(y)
ax.set_yticklabels(current["department"], fontsize=11)

for label, dept in zip(ax.get_yticklabels(), current["department"]):
    if dept == "Customer Support":
        label.set_color("#C8102E")
        label.set_fontweight("bold")
    else:
        label.set_color("#333333")

ax.invert_yaxis()

ax.set_xlim(0, 100)
ax.set_xlabel("% favourable (2026)", fontsize=11, color="#333333")
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, pos: f"{int(x)}%"))
ax.grid(axis="x", color="#D0D0D0", linewidth=0.8, alpha=0.8, zorder=0)
ax.set_axisbelow(True)
ax.tick_params(axis="x", colors="#555555", labelsize=10)
ax.tick_params(axis="y", length=0)

for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color("#BBBBBB")

# Direct labels: highlight Support and give next-lowest context
ax.text(
    support_val + 2,
    support_row,
    f"{support_val:.0f}%  (was {support_prev:.0f}%)",
    va="center",
    ha="left",
    fontsize=12,
    fontweight="bold",
    color="#C8102E",
)

ax.text(
    sales_val + 2,
    sales_row,
    f"{sales_val:.0f}%",
    va="center",
    ha="left",
    fontsize=10,
    color="#666666",
)

ax.set_title(
    "Customer Support is the clear priority for manager support:\n"
    f"just {support_val:.0f}% favourable in 2026, down {drop:.0f} points from 2025",
    fontsize=15,
    fontweight="bold",
    loc="left",
    pad=16,
    color="#111111",
)

fig.text(
    0.02,
    0.035,
    "Q: “My manager supports my growth.” Caveat: Support 2026 response rate is 38% (n=53) vs 81% in 2025.",
    fontsize=9,
    color="#555555",
    ha="left",
)

fig.subplots_adjust(left=0.18, right=0.95, top=0.82, bottom=0.16)
