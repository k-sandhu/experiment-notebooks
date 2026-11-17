import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

df = pd.read_csv("data.csv")

quarter_order = sorted(df["quarter"].unique())
quarter_to_idx = {q: i for i, q in enumerate(quarter_order)}
df["q_idx"] = df["quarter"].map(quarter_to_idx)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6))

# Left panel: return rate over time, highlighting Footwear
for cat in df["category"].unique():
    if cat == "Footwear":
        continue
    sub = df[df["category"] == cat].sort_values("q_idx")
    ax1.plot(
        sub["q_idx"],
        sub["return_rate_pct"],
        color="lightgray",
        linewidth=1,
        alpha=0.75,
        zorder=1,
    )

foot = df[df["category"] == "Footwear"].sort_values("q_idx")
ax1.plot(
    foot["q_idx"],
    foot["return_rate_pct"],
    color="#c0392b",
    linewidth=2.5,
    marker="o",
    markersize=5,
    label="Footwear",
    zorder=3,
)

last = foot.iloc[-1]
ax1.annotate(
    f"Q3'26: {last['return_rate_pct']:.1f}% return rate\n"
    f"({last['defect_share_of_returns_pct']:.0f}% of returns defective)",
    xy=(last["q_idx"], last["return_rate_pct"]),
    xytext=(last["q_idx"] - 2.0, last["return_rate_pct"] + 3.0),
    arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.2),
    fontsize=9,
    color="#c0392b",
    fontweight="bold",
)

ax1.set_xticks(range(len(quarter_order)))
ax1.set_xticklabels([q[2:] for q in quarter_order], rotation=45, ha="right")
ax1.set_ylabel("Return rate (%)")
ax1.set_xlabel("Quarter")
ax1.set_title("Return rate by category", fontsize=11, fontweight="bold")
ax1.set_ylim(0, 28)
ax1.grid(axis="y", linestyle=":", alpha=0.5)

legend_elements = [
    Line2D([0], [0], color="#c0392b", lw=2.5, marker="o", label="Footwear"),
    Line2D([0], [0], color="lightgray", lw=1, label="Other categories"),
]
ax1.legend(handles=legend_elements, loc="upper left", frameon=False, fontsize=8)

# Right panel: latest-quarter defect share by category
latest = quarter_order[-1]
latest_df = df[df["quarter"] == latest].sort_values(
    "defect_share_of_returns_pct", ascending=True
)

colors = [
    "#c0392b" if cat == "Footwear" else "#a0a0a0"
    for cat in latest_df["category"]
]
bars = ax2.barh(
    latest_df["category"],
    latest_df["defect_share_of_returns_pct"],
    color=colors,
    edgecolor="none",
)

for bar, val in zip(bars, latest_df["defect_share_of_returns_pct"]):
    ax2.text(
        val + 0.8,
        bar.get_y() + bar.get_height() / 2,
        f"{val:.1f}%",
        va="center",
        fontsize=8,
    )

ax2.set_xlabel("Defect share of returns (%)")
ax2.set_title(f"{latest}: Defect share of returns", fontsize=11, fontweight="bold")
ax2.set_xlim(0, 52)
ax2.grid(axis="x", linestyle=":", alpha=0.5)
ax2.tick_params(axis="y", labelsize=8)

fig.suptitle(
    "Investigate Footwear first: Q3 2026 defect-driven return spike",
    fontsize=13,
    fontweight="bold",
    y=0.98,
)

plt.tight_layout(rect=[0, 0, 1, 0.95])
