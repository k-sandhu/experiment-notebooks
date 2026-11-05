import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Patch

df = pd.read_csv("data.csv")

# Order departments by total forecast variance
dept_order = (
    df.groupby("department")["variance_k"]
    .sum()
    .sort_values(ascending=False)
    .index
    .tolist()
)

lines = ["Staff", "Overtime", "Contracts", "Materials", "Fleet"]
colors = {
    "Staff": "#4C72B0",
    "Overtime": "#DD8452",
    "Contracts": "#55A868",
    "Materials": "#C44E52",
    "Fleet": "#8172B3",
}

pivot = (
    df.pivot_table(
        index="department",
        columns="budget_line",
        values="variance_k",
        aggfunc="sum"
    )
    .reindex(dept_order)
)

fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(dept_order))
pos_bottom = np.zeros(len(dept_order))
neg_bottom = np.zeros(len(dept_order))

for line in lines:
    vals = pivot[line].fillna(0).values
    pos = np.where(vals > 0, vals, 0)
    neg = np.where(vals < 0, vals, 0)

    ax.bar(
        x, pos, bottom=pos_bottom, color=colors[line],
        width=0.72, edgecolor="white", linewidth=0.6
    )
    ax.bar(
        x, neg, bottom=neg_bottom, color=colors[line],
        width=0.72, edgecolor="white", linewidth=0.6
    )

    pos_bottom += pos
    neg_bottom += neg

ax.axhline(0, color="black", linewidth=0.8)
ax.set_xticks(x)
ax.set_xticklabels(dept_order)
ax.set_ylabel("Forecast variance ($ millions)")
ax.set_title(
    "Forecast Year-End Budget Variance by Department and Budget Line\n"
    f"City total: {df['variance_k'].sum() / 1000:+.1f}M forecast overspend",
    fontsize=12,
)
ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"${y / 1000:.1f}M"))
ax.grid(axis="y", linestyle="--", alpha=0.35)
ax.set_axisbelow(True)
ax.margins(y=0.16)

# Add department total labels
totals = df.groupby("department")["variance_k"].sum()
for xi, dept in zip(x, dept_order):
    total = totals.loc[dept]
    ax.annotate(
        f"{total / 1000:+.1f}M",
        (xi, total),
        xytext=(0, 6 if total >= 0 else -12),
        textcoords="offset points",
        ha="center",
        va="bottom" if total >= 0 else "top",
        fontsize=9,
        fontweight="bold",
    )

# Highlight Transit overtime
transit_x = dept_order.index("Transit")
transit_ot = df.loc[
    (df["department"] == "Transit") & (df["budget_line"] == "Overtime"),
    "variance_k",
].iloc[0]
transit_staff = df.loc[
    (df["department"] == "Transit") & (df["budget_line"] == "Staff"),
    "variance_k",
].iloc[0]
ot_mid = max(transit_staff, 0) + transit_ot / 2

ax.annotate(
    "Transit overtime\n+$2.4M",
    xy=(transit_x + 0.36, ot_mid),
    xytext=(transit_x + 0.62, ot_mid + 900),
    arrowprops=dict(arrowstyle="-", lw=0.8, color="gray"),
    fontsize=9,
    ha="left",
    va="center",
)

handles = [
    Patch(facecolor=colors[line], edgecolor="white", label=line)
    for line in lines
]
ax.legend(
    handles=handles,
    title="Budget line",
    loc="upper right",
    frameon=False,
    fontsize=9,
    title_fontsize=9,
)

plt.tight_layout()
