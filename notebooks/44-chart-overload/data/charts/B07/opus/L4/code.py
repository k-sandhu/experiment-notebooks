import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Defect returns as % of units sold: returns that cite a defect, per unit sold
df["defect_return_pct"] = (df["units_returned"] * df["defect_share_of_returns_pct"] / 100
                           / df["units_sold"] * 100)

quarters = sorted(df["quarter"].unique())
x_pos = {q: i for i, q in enumerate(quarters)}
pretty = [f"{q[4:]} {q[:4]}" for q in quarters]

HIGHLIGHT = "#C0392B"
GREY = "#C4C4C4"
DARK_GREY = "#6E6E6E"

fig, ax = plt.subplots(figsize=(10, 6))

# Context: every other category in grey
others = df[df["category"] != "Footwear"]
n_other = others["category"].nunique()
other_max = others["defect_return_pct"].max()
for cat, g in others.groupby("category"):
    g = g.sort_values("quarter")
    ax.plot([x_pos[q] for q in g["quarter"]], g["defect_return_pct"],
            color=GREY, lw=1.2, zorder=1)

# Focus: Footwear
fw = df[df["category"] == "Footwear"].sort_values("quarter")
fx = [x_pos[q] for q in fw["quarter"]]
fy = fw["defect_return_pct"].values
before_avg = fy[:-1].mean()
ratio = fy[-1] / before_avg

ax.plot(fx, fy, color=HIGHLIGHT, lw=3, zorder=3)
ax.scatter(fx[-1], fy[-1], color=HIGHLIGHT, s=55, zorder=4)

# Direct labels
ax.text(fx[-1] + 0.12, fy[-1], f"Footwear\n{fy[-1]:.1f}%", color=HIGHLIGHT,
        fontsize=13, fontweight="bold", va="center", ha="left", linespacing=1.2)

ax.text(fx[-1] + 0.12, 1.3, f"{n_other} other\ncategories,\nall below {other_max:.0f}%",
        color=DARK_GREY, fontsize=10, va="center", ha="left", linespacing=1.2)

# Prior baseline for footwear, pointing at the footwear line itself
ax.annotate(f"Footwear: {before_avg:.1f}% on average\nin the six prior quarters",
            xy=(fx[3], fy[3]), xytext=(fx[3], 4.6),
            ha="center", va="bottom", fontsize=10.5, color=HIGHLIGHT,
            arrowprops=dict(arrowstyle="-", color=HIGHLIGHT, lw=1,
                            shrinkA=2, shrinkB=4))

# Axes and scale
ax.set_xticks(range(len(quarters)))
ax.set_xticklabels(pretty, fontsize=10)
ax.set_xlim(-0.3, len(quarters) - 1 + 1.0)
ax.set_ylim(0, 10)
ax.set_ylabel("Returns citing a defect (% of units sold)", fontsize=11)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.grid(axis="y", color="#EEEEEE", lw=0.8)
ax.set_axisbelow(True)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
for s in ["left", "bottom"]:
    ax.spines[s].set_color("#999999")
ax.tick_params(colors="#444444")

ax.set_title(f"Footwear defect returns jumped ~{ratio:.0f}× in Q3 2026: investigate footwear first",
             fontsize=14.5, fontweight="bold", loc="left", pad=14)

fig.text(0.01, 0.015,
         "Caveat: footwear's return window doubled to 60 days in Q3 2026. Past extensions added only ~2 pts to the return rate,\n"
         "while the share of footwear returns citing a defect rose from ~9% to 46% (mostly soles coming apart).",
         fontsize=9, color="#555555", ha="left", va="bottom")

fig.tight_layout(rect=(0, 0.07, 1, 1))
