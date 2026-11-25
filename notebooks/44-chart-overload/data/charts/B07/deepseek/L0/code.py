import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

quarters = sorted(
    df["quarter"].unique(),
    key=lambda q: (int(q[:4]), int(q[-1]))
)
q_to_pos = {q: i for i, q in enumerate(quarters)}
x = np.arange(len(quarters))

pivot_return = (
    df.pivot_table(
        index="quarter",
        columns="category",
        values="return_rate_pct",
        aggfunc="mean"
    )
    .reindex(quarters)
)

fig, (ax1, ax2) = plt.subplots(
    2, 1,
    figsize=(10, 6),
    sharex=True,
    gridspec_kw={"height_ratios": [2, 1]}
)

highlight = {
    "Footwear": "#d62728",
    "Swimwear": "#1f77b4",
    "Accessories": "#2ca02c"
}

other_label_used = False
for category in pivot_return.columns:
    if category in highlight:
        continue
    ax1.plot(
        x,
        pivot_return[category].values,
        color="0.8",
        linewidth=1,
        alpha=0.8,
        label="Other categories" if not other_label_used else None
    )
    other_label_used = True

for category, color in highlight.items():
    if category in pivot_return.columns:
        ax1.plot(
            x,
            pivot_return[category].values,
            color=color,
            linewidth=2,
            marker="o",
            markersize=3,
            label=category
        )

footwear_q3 = pivot_return.loc["2026Q3", "Footwear"]
ax1.annotate(
    f"Footwear Q3 2026\n{footwear_q3:.1f}% return rate",
    xy=(q_to_pos["2026Q3"], footwear_q3),
    xytext=(q_to_pos["2026Q3"] - 2.6, 21.5),
    textcoords="data",
    arrowprops=dict(arrowstyle="->", color="#d62728"),
    color="#d62728",
    fontsize=9
)

ax1.set_ylabel("Return rate (%)")
ax1.set_title("Return rates by category: Footwear surge in Q3 2026")
ax1.set_ylim(0, 26)
ax1.grid(True, axis="y", alpha=0.3)
ax1.legend(loc="upper left", ncol=2, fontsize=8, frameon=False)

footwear = (
    df[df["category"].eq("Footwear")]
    .set_index("quarter")
    .reindex(quarters)
    .reset_index()
)
footwear["pos"] = footwear["quarter"].map(q_to_pos)

bar_colors = [
    "#d62728" if q == "2026Q3" else "#8da0cb"
    for q in footwear["quarter"]
]
ax2.bar(
    footwear["pos"],
    footwear["defect_share_of_returns_pct"],
    color=bar_colors,
    width=0.7
)

q3_defect = footwear.loc[
    footwear["quarter"].eq("2026Q3"), "defect_share_of_returns_pct"
].iloc[0]
ax2.text(
    q_to_pos["2026Q3"],
    q3_defect + 1.5,
    f"{q3_defect:.1f}%",
    ha="center",
    va="bottom",
    color="#d62728",
    fontweight="bold"
)

ax2.set_ylabel("Defect share (%)")
ax2.set_title("Why: share of Footwear returns reporting a defect")
ax2.set_ylim(0, 52)
ax2.grid(True, axis="y", alpha=0.3)
ax2.set_xticks(x)
ax2.set_xticklabels(quarters, rotation=45, ha="right")

fig.tight_layout()
