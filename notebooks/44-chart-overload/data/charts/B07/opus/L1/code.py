import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Defect-related returns as a share of units sold: the direct measure of a quality problem
df["defect_returns"] = df["units_returned"] * df["defect_share_of_returns_pct"] / 100
df["defect_return_rate"] = df["defect_returns"] / df["units_sold"] * 100

quarters = sorted(df["quarter"].unique())
xpos = {q: i for i, q in enumerate(quarters)}
xlabels = [f"{q[-2:]}\n{q[:4]}" for q in quarters]

fig, ax = plt.subplots(figsize=(10, 6))

grey = "#b8b8b8"
red = "#c62828"

for cat, g in df.groupby("category"):
    g = g.sort_values("quarter")
    x = [xpos[q] for q in g["quarter"]]
    y = g["defect_return_rate"].values
    if cat == "Footwear":
        continue
    ax.plot(x, y, color=grey, lw=1.4, zorder=1)

# Label Swimwear as context (highest overall returns, but driven by fit, not defects)
sw = df[df["category"] == "Swimwear"].sort_values("quarter")
ax.text(xpos[sw["quarter"].iloc[-1]] + 0.12, sw["defect_return_rate"].iloc[-1],
        "Swimwear\n(highest total returns,\nmostly fit)", color="#777777",
        fontsize=9, va="center", ha="left")
ax.text(xpos[quarters[-1]] + 0.12, 0.55, "All other\ncategories", color="#777777",
        fontsize=9, va="center", ha="left")

# Footwear highlighted
fw = df[df["category"] == "Footwear"].sort_values("quarter")
fx = [xpos[q] for q in fw["quarter"]]
fy = fw["defect_return_rate"].values
ax.plot(fx, fy, color=red, lw=3, marker="o", ms=6, zorder=3)
ax.text(fx[-1] + 0.12, fy[-1], f"Footwear\n{fy[-1]:.1f}%", color=red,
        fontsize=12, fontweight="bold", va="center", ha="left")

prior_avg = fy[:-1].mean()
ax.annotate(f"Footwear avg. before: {prior_avg:.1f}%",
            xy=(2.5, prior_avg), xytext=(1.6, 4.2),
            color=red, fontsize=10,
            arrowprops=dict(arrowstyle="-", color=red, lw=0.8))

ax.set_xticks(range(len(quarters)))
ax.set_xticklabels(xlabels, fontsize=10)
ax.set_xlim(-0.3, len(quarters) - 1 + 1.6)
ax.set_ylim(0, 10)
ax.set_ylabel("Returns reporting a defect, % of units sold", fontsize=10)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))

for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
ax.grid(axis="y", color="#eeeeee", zorder=0)

fig.suptitle("Investigate Footwear first: defect returns jumped about 9x in Q3 2026",
             x=0.06, ha="left", fontsize=15, fontweight="bold")
ax.set_title("46% of footwear returns reported a defect (mostly soles coming apart), vs ~9% before. "
             "The 60-day return\nwindow promotion explains only ~2 pts of the 8-pt jump in footwear's return rate. "
             "No other category moved.",
             loc="left", fontsize=9.5, color="#555555")

fig.tight_layout()
fig.subplots_adjust(top=0.84)
