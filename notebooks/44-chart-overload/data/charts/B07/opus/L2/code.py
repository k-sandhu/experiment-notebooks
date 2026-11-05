import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Returns that cite a defect, as % of units sold (the quality signal)
df["defect_return_pct"] = df["units_returned"] * df["defect_share_of_returns_pct"] / 100 / df["units_sold"] * 100

quarters = sorted(df["quarter"].unique())
x_pos = {q: i for i, q in enumerate(quarters)}
pretty = [f"{q[4:]} {q[:4]}" for q in quarters]

HIGHLIGHT = "#C0392B"
GREY = "#BBBBBB"

fig, ax = plt.subplots(figsize=(10, 6))

# Context: all other categories in grey
for cat, g in df[df["category"] != "Footwear"].groupby("category"):
    g = g.sort_values("quarter")
    ax.plot([x_pos[q] for q in g["quarter"]], g["defect_return_pct"],
            color=GREY, lw=1.3, zorder=1)

# Focus: Footwear
fw = df[df["category"] == "Footwear"].sort_values("quarter")
fx = [x_pos[q] for q in fw["quarter"]]
fy = fw["defect_return_pct"].values
ax.plot(fx, fy, color=HIGHLIGHT, lw=3, marker="o", ms=6, zorder=3)

# Labels only where the number is the message
before_avg = fy[:-1].mean()
ax.annotate(f"{fy[-1]:.1f}%", xy=(fx[-1], fy[-1]), xytext=(10, 0),
            textcoords="offset points", va="center", ha="left",
            fontsize=13, fontweight="bold", color=HIGHLIGHT)
ax.text(fx[-1] + 0.15, fy[-1] - 0.9, "Footwear", color=HIGHLIGHT,
        fontsize=12, fontweight="bold", va="center", ha="left")
ax.annotate(f"Footwear averaged {before_avg:.1f}%\nin the six prior quarters",
            xy=(2.5, before_avg), xytext=(2.5, 4.3),
            textcoords="data", ha="center", fontsize=10, color=HIGHLIGHT,
            arrowprops=dict(arrowstyle="-", color=HIGHLIGHT, lw=1))
ax.text(0.05, 3.25, "All other categories (grey) stay below 3%",
        color="#777777", fontsize=10, va="bottom")

# Axes and scale
ax.set_xticks(range(len(quarters)))
ax.set_xticklabels(pretty, fontsize=10)
ax.set_xlim(-0.3, len(quarters) - 1 + 1.1)
ax.set_ylim(0, 10)
ax.set_ylabel("Returns citing a defect (% of units sold)", fontsize=11)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.grid(axis="y", color="#EEEEEE", lw=0.8)
ax.set_axisbelow(True)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
ax.spines["left"].set_color("#999999")
ax.spines["bottom"].set_color("#999999")

ax.set_title("Footwear defect returns jumped about ninefold in Q3 2026: investigate footwear first",
             fontsize=14, fontweight="bold", loc="left", pad=14)

fig.text(0.01, 0.015,
         "Note: Footwear's return window was extended from 30 to 60 days for a Q3 2026 promotion. Past extensions added only ~2 pts "
         "to the return rate,\nwhile the defect share of footwear returns rose from ~9% to 46%. "
         "Defect returns estimated as units returned × share reporting a defect.",
         fontsize=8.5, color="#555555", ha="left", va="bottom")

fig.tight_layout(rect=(0, 0.07, 1, 1))
