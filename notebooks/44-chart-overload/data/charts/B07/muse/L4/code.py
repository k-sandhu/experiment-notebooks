import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Quality metric: defective returns per 100 units sold
df["defect_rate"] = df["return_rate_pct"] * df["defect_share_of_returns_pct"] / 100

quarters = sorted(df["quarter"].unique())
pivot = df.pivot(index="quarter", columns="category", values="defect_rate").reindex(quarters)
x = list(range(len(quarters)))

footwear = df[df["category"] == "Footwear"].sort_values("quarter")
last_rate = footwear.iloc[-1]["defect_rate"]
prior_rate = footwear.iloc[:-1]["defect_rate"].mean()
ratio = last_rate / prior_rate
last_defect_share = footwear.iloc[-1]["defect_share_of_returns_pct"]
prior_defect_share = footwear.iloc[:-1]["defect_share_of_returns_pct"].mean()

RED = "#C1272D"
GREY = "#C8C8C8"
DARK = "#595959"

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.085, right=0.97, top=0.80, bottom=0.20)

# Context: all other categories, thin and light
for category in pivot.columns:
    if category == "Footwear":
        continue
    s = pivot[category].dropna()
    xs = [quarters.index(q) for q in s.index]
    ax.plot(xs, s.values, color=GREY, linewidth=1.1, zorder=1)

# Focus: Footwear — flat, then a spike; only the final point gets a marker
ax.plot(x, pivot["Footwear"], color=RED, linewidth=4, zorder=3,
        solid_capstyle="round")
ax.plot([x[-1]], [last_rate], color=RED, marker="o", markersize=10,
        markeredgecolor="white", markeredgewidth=1.5, zorder=4)

# Title states the decision
fig.text(0.085, 0.96, "Investigate Footwear first: defect returns spiked in Q3 2026",
         fontsize=17, fontweight="bold", ha="left", va="top")
fig.text(0.085, 0.905, "Defect returns per 100 units sold, by category — no other category moved",
         fontsize=11, color=DARK, ha="left", va="top")

# The one number that carries the message, set in the empty space by the spike
ax.annotate(
    f"Footwear: {last_rate:.1f} per 100 sold\n"
    f"about {ratio:.0f}\u00d7 its previous level (~{prior_rate:.1f})\n"
    f"{last_defect_share:.0f}% of its returns cited a defect (was ~{prior_defect_share:.0f}%)",
    xy=(x[-1], last_rate), xycoords="data",
    xytext=(2.15, 7.1), textcoords="data",
    fontsize=11.5, color=RED, fontweight="bold", va="center",
    arrowprops=dict(arrowstyle="->", color=RED, lw=1.6,
                    shrinkA=2, shrinkB=8),
)

# Direct label for the grey context, placed just above its highest line
ax.text(3.05, 3.05, "All other categories", fontsize=10, color=DARK, va="bottom")

ax.set_xticks(x)
ax.set_xticklabels(quarters, fontsize=10)
ax.set_yticks([0, 2, 4, 6, 8, 10])
ax.tick_params(axis="y", labelsize=10, length=0)
ax.tick_params(axis="x", length=4)
ax.set_xlim(0, x[-1])
ax.set_ylim(0, 10)
ax.set_ylabel("Defect returns\n(per 100 units sold)", fontsize=10)
ax.grid(axis="y", color="#E6E6E6", linewidth=0.8)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

fig.text(
    0.085, 0.02,
    "Defect returns = units returned \u00d7 defect share of returns, as a share of units sold. "
    "Caveat: Footwear's return window rose from 30 to 60 days in\n"
    "2026Q3; past extensions added only about 2 points to the total return rate — far smaller than this defect spike.",
    fontsize=8.5, color=DARK, ha="left", va="bottom",
)
