import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Quality metric: defective returns as a percentage of all units sold
df["defect_rate_pct_of_sold"] = (
    df["units_returned"] * (df["defect_share_of_returns_pct"] / 100)
    / df["units_sold"] * 100
)

quarters = sorted(df["quarter"].unique())
pivot = df.pivot(index="quarter", columns="category",
                 values="defect_rate_pct_of_sold").reindex(quarters)
x = range(len(quarters))

footwear = df[df["category"] == "Footwear"].sort_values("quarter")
last = footwear.iloc[-1]
last_rate = last["defect_rate_pct_of_sold"]
last_defect_share = last["defect_share_of_returns_pct"]
prior_defect_share = footwear.iloc[:-1]["defect_share_of_returns_pct"].mean()

RED = "#C1272D"
GREY = "#B5B5B5"
DARK_GREY = "#595959"

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.08, right=0.97, top=0.82, bottom=0.18)

# Context: every other category in grey
for category in pivot.columns:
    if category != "Footwear":
        ax.plot(x, pivot[category], color=GREY, linewidth=1.2, alpha=0.8, zorder=1)

# Focus: Footwear
ax.plot(x, pivot["Footwear"], color=RED, linewidth=3.5,
        marker="o", markersize=6, zorder=3)

# Title states the decision
fig.text(0.08, 0.96, "Investigate Footwear first: defect returns spiked in Q3 2026",
         fontsize=17, fontweight="bold", ha="left", va="top")
fig.text(0.08, 0.915, "Defect returns as a share of units sold, by category — no other category moved",
         fontsize=11, color=DARK_GREY, ha="left", va="top")

# Direct labels, no legend
ax.text(3.0, 3.4, "All other categories", fontsize=10, color=DARK_GREY)

ax.annotate(
    f"Footwear: {last_rate:.1f} defect returns per 100 sold\n"
    f"{last_defect_share:.0f}% of its returns reported a defect\n"
    f"(was ~{prior_defect_share:.0f}% in previous quarters)",
    xy=(len(quarters) - 1, last_rate),
    xytext=(2.6, 6.8),
    fontsize=11, color=RED, fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=RED, lw=1.5),
)

ax.set_xticks(list(x))
ax.set_xticklabels(quarters)
ax.set_xlim(0, len(quarters) - 1)
ax.set_ylim(0, max(10, last_rate * 1.15))
ax.set_ylabel("Defect returns (% of units sold)", fontsize=10)
ax.grid(axis="y", color="#E5E5E5", linewidth=0.8)
ax.set_axisbelow(True)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

fig.text(
    0.08, 0.02,
    "Defect returns = units returned x defect share of returns. Caveat: Footwear's return window was extended from 30 to 60 days in 2026Q3;\n"
    "past extensions added about 2 points to the total return rate, far smaller than this spike.",
    fontsize=8.5, color=DARK_GREY, ha="left", va="bottom",
)
