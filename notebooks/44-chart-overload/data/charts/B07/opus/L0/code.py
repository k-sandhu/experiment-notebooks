import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

quarters = sorted(df["quarter"].unique())
qpos = {q: i for i, q in enumerate(quarters)}
qlabels = [f"{q[4:]}\n{q[:4]}" for q in quarters]
df["x"] = df["quarter"].map(qpos)

HILITE = "#c0392b"
GREY = "#b8b8b8"

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.15, 1]}
)

# Left panel: return rate by category, Footwear highlighted
for cat, g in df.groupby("category"):
    g = g.sort_values("x")
    if cat == "Footwear":
        continue
    ax1.plot(g["x"], g["return_rate_pct"], color=GREY, lw=1.3, zorder=1)

fw = df[df["category"] == "Footwear"].sort_values("x")
ax1.plot(fw["x"], fw["return_rate_pct"], color=HILITE, lw=2.6,
         marker="o", ms=4, zorder=3)
last = fw.iloc[-1]
ax1.annotate(f"Footwear\n{last['return_rate_pct']:.1f}%",
             xy=(last["x"], last["return_rate_pct"]),
             xytext=(-12, 8), textcoords="offset points",
             ha="right", va="bottom", color=HILITE, fontsize=10, fontweight="bold")

for cat in ["Swimwear", "Accessories"]:
    g = df[df["category"] == cat].sort_values("x")
    ax1.text(g["x"].iloc[0], g["return_rate_pct"].iloc[0] + 0.6, cat,
             color="#808080", fontsize=8.5, ha="left", va="bottom")
ax1.text(0, 14.6, "Other categories (grey)", color="#808080", fontsize=8.5)

ax1.set_xticks(range(len(quarters)))
ax1.set_xticklabels(qlabels, fontsize=9)
ax1.set_ylabel("Return rate (% of units sold)")
ax1.set_ylim(0, 27)
ax1.set_title("Return rate by category", loc="left", fontsize=11)
ax1.grid(axis="y", color="#eeeeee")
ax1.set_axisbelow(True)

# Right panel: Footwear return rate split into defect vs other returns
defect_pts = fw["return_rate_pct"] * fw["defect_share_of_returns_pct"] / 100
other_pts = fw["return_rate_pct"] - defect_pts
x = np.arange(len(fw))
ax2.bar(x, other_pts, color=GREY, width=0.65, label="Other reasons (mostly size/fit)")
ax2.bar(x, defect_pts, bottom=other_pts, color=HILITE, width=0.65,
        label="Customer reported a defect")

for xi, tot, d in zip(x, fw["return_rate_pct"], defect_pts):
    ax2.text(xi, tot + 0.3, f"{tot:.1f}%", ha="center", va="bottom", fontsize=8.5)

ax2.annotate("46% of Q3 2026 returns\nreported a defect,\nmostly soles coming apart",
             xy=(x[-1] - 0.33, other_pts.iloc[-1] + defect_pts.iloc[-1] / 2),
             xytext=(x[-1] - 1.5, 15.5), ha="right", va="center",
             fontsize=8.5, color=HILITE,
             arrowprops=dict(arrowstyle="-", color=HILITE, lw=0.8))

ax2.set_xticks(x)
ax2.set_xticklabels([qlabels[i] for i in fw["x"]], fontsize=9)
ax2.set_ylim(0, 27)
ax2.set_ylabel("Footwear return rate (percentage points)")
ax2.set_title("Footwear: what drove the jump", loc="left", fontsize=11)
ax2.legend(loc="upper left", frameon=False, fontsize=8.5)
ax2.grid(axis="y", color="#eeeeee")
ax2.set_axisbelow(True)

for ax in (ax1, ax2):
    ax.spines[["top", "right"]].set_visible(False)

fig.suptitle("Footwear returns nearly doubled in Q3 2026, driven by defects",
             x=0.02, ha="left", fontsize=14, fontweight="bold")
fig.text(0.02, 0.905,
         "Footwear rose from a 10.8% average to 19.2%; no other category moved more than 0.9 points. "
         "A 60-day return window\nwas also in effect, but past extensions added only about 2 points.",
         ha="left", va="top", fontsize=9, color="#555555")

fig.tight_layout(rect=[0, 0, 1, 0.85])
