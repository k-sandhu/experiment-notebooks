import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

df = pd.read_csv("data.csv")

questions = [
    "I would recommend Northlight as a place to work",
    "My manager supports my growth",
    "I have the tools I need to do my job",
    "My workload is manageable",
    "I see myself working here in two years",
    "I understand the company's strategy",
]
short_q = {
    "I would recommend Northlight as a place to work": "Recommend as place to work",
    "My manager supports my growth": "Manager supports growth",
    "I have the tools I need to do my job": "Have tools to do job",
    "My workload is manageable": "Workload manageable",
    "I see myself working here in two years": "See myself here in 2 years",
    "I understand the company's strategy": "Understand strategy",
}

# Customer Support question-level changes
cs = df[df["department"] == "Customer Support"]
cs_pivot = cs.pivot(index="question", columns="year", values="pct_favourable").reindex(questions)
change = cs_pivot[2026] - cs_pivot[2025]
order = change.sort_values().index
cs_pivot = cs_pivot.loc[order]
y = np.arange(len(order))

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.45, 1]}
)

for yi, q in zip(y, order):
    v25 = cs_pivot.loc[q, 2025]
    v26 = cs_pivot.loc[q, 2026]
    color = "#d62728" if v26 < v25 else "#2ca02c"

    ax1.plot([v25, v26], [yi, yi], color=color, lw=3, alpha=0.85, zorder=1)
    ax1.scatter(v25, yi, color="#7f7f7f", s=55, zorder=2)
    ax1.scatter(v26, yi, color=color, s=65, zorder=3)

    ax1.text(
        102, yi,
        f"{v25:.0f} → {v26:.0f} ({v26 - v25:+.0f})",
        va="center", ha="left", fontsize=8.5, color=color
    )

ax1.set_yticks(y)
ax1.set_yticklabels([short_q[q] for q in order])
ax1.invert_yaxis()
ax1.set_xlim(0, 130)
ax1.set_xlabel("Percentage favourable")
ax1.set_title(
    "Customer Support: favourable scores fell sharply in 2026\n"
    "Response: 81% (n=113) → 38% (n=53)",
    loc="left", fontsize=10.5, fontweight="bold"
)
ax1.grid(axis="x", color="#dddddd", lw=0.6)
ax1.set_axisbelow(True)

legend1 = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#7f7f7f",
           markersize=8, label="2025"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#d62728",
           markersize=8, label="2026 decline"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#2ca02c",
           markersize=8, label="2026 improvement"),
]
ax1.legend(handles=legend1, loc="upper left", frameon=True,
           facecolor="white", framealpha=0.9, fontsize=8)

# Response rates by department
dept_order = df["department"].drop_duplicates().tolist()
resp = df.pivot_table(
    index="department", columns="year", values="response_rate_pct", aggfunc="first"
).reindex(dept_order)

y2 = np.arange(len(dept_order))

for yi, dept in zip(y2, dept_order):
    v25 = resp.loc[dept, 2025]
    v26 = resp.loc[dept, 2026]
    color = "#d62728" if dept == "Customer Support" else "#1f77b4"

    ax2.plot([v25, v26], [yi, yi], color="#bbbbbb", lw=1.2, zorder=1)
    ax2.scatter(v25, yi, color="#7f7f7f", s=35, zorder=2)
    ax2.scatter(v26, yi, color=color, s=45, zorder=3)

    if dept == "Customer Support":
        ax2.text(v26 + 2, yi, f"{v26:.0f}%", va="center", ha="left",
                 fontsize=9, color=color, fontweight="bold")
        ax2.text(v25 + 2, yi, f"{v25:.0f}%", va="center", ha="left",
                 fontsize=8, color="#555555")

ax2.set_yticks(y2)
ax2.set_yticklabels(dept_order)
ax2.invert_yaxis()
ax2.set_xlim(0, 100)
ax2.set_xlabel("Response rate (%)")
ax2.set_title("Response rates by department", loc="left",
              fontsize=12, fontweight="bold")
ax2.grid(axis="x", color="#dddddd", lw=0.6)
ax2.set_axisbelow(True)

legend2 = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#7f7f7f",
           markersize=7, label="2025"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#1f77b4",
           markersize=7, label="2026"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor="#d62728",
           markersize=7, label="Customer Support 2026"),
]
ax2.legend(handles=legend2, loc="upper left", frameon=False, fontsize=8)

plt.tight_layout()
