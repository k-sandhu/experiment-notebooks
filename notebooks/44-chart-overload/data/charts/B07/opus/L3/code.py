import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Order the quarters and build short axis labels such as "Q1\n'25"
quarters = sorted(df["quarter"].unique())
q_idx = {q: i for i, q in enumerate(quarters)}
q_labels = [f"{q[4:]}\n'{q[2:4]}" for q in quarters]
df["x"] = df["quarter"].map(q_idx)

HIGHLIGHT = "#C0392B"
GREY = "#BDBDBD"
DARK = "#333333"

fw = df[df["category"] == "Footwear"].sort_values("x")
fw_prior = fw[fw["quarter"] != "2026Q3"]
fw_last = fw[fw["quarter"] == "2026Q3"].iloc[0]
base_rate = fw_prior["return_rate_pct"].mean()                 # about 10.8
base_defect = fw_prior["defect_share_of_returns_pct"].mean()    # about 9
jump = fw_last["return_rate_pct"] - base_rate

fig = plt.figure(figsize=(10, 6))
gs = fig.add_gridspec(1, 2, width_ratios=[1.55, 1], wspace=0.28,
                      left=0.07, right=0.97, top=0.76, bottom=0.2)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])

# Left panel: return rate by category (Footwear highlighted)
for cat, g in df.groupby("category"):
    if cat == "Footwear":
        continue
    g = g.sort_values("x")
    ax1.plot(g["x"], g["return_rate_pct"], color=GREY, lw=1.3, zorder=1)

ax1.plot(fw["x"], fw["return_rate_pct"], color=HIGHLIGHT, lw=3, zorder=3)
ax1.scatter([fw_last["x"]], [fw_last["return_rate_pct"]], color=HIGHLIGHT, s=45, zorder=4)

# Dashed line for the prior average
ax1.hlines(base_rate, 0, 5, colors=HIGHLIGHT, linestyles="--", lw=1.2, alpha=0.7, zorder=2)
ax1.text(0, base_rate + 1.0, f"Footwear: prior 6-quarter avg {base_rate:.1f}%",
         color=HIGHLIGHT, fontsize=9.5, va="bottom")

ax1.annotate(f"{fw_last['return_rate_pct']:.1f}%",
             xy=(fw_last["x"], fw_last["return_rate_pct"]),
             xytext=(-12, 8), textcoords="offset points",
             ha="right", va="bottom", color=HIGHLIGHT, fontsize=13, fontweight="bold")

ax1.text(0, 28.3, "Other 10 categories (grey): none moved more than 0.9 pts",
         color="#777777", fontsize=9, va="top")

ax1.set_ylim(0, 29)
ax1.set_xlim(-0.3, len(quarters) - 0.6)
ax1.set_xticks(range(len(quarters)))
ax1.set_xticklabels(q_labels, fontsize=9)
ax1.set_ylabel("Return rate (% of units sold)", fontsize=9.5)
ax1.set_title("Return rate by category", loc="left", fontsize=11, color=DARK)

# Right panel: share of Footwear returns that reported a defect
colors = [GREY] * (len(fw) - 1) + [HIGHLIGHT]
ax2.bar(fw["x"], fw["defect_share_of_returns_pct"], color=colors, width=0.7)
ax2.hlines(base_defect, -0.4, 5.4, colors="#777777", linestyles="--", lw=1.1)
ax2.text(-0.4, base_defect + 1.5, f"Prior avg {base_defect:.0f}%",
         color="#555555", fontsize=9.5, va="bottom")
ax2.text(fw_last["x"], fw_last["defect_share_of_returns_pct"] + 1.2,
         f"{fw_last['defect_share_of_returns_pct']:.0f}%",
         ha="center", va="bottom", color=HIGHLIGHT, fontsize=13, fontweight="bold")
ax2.text(fw_last["x"] - 0.55, 40, "Mostly soles\ncoming apart",
         ha="right", va="center", color=HIGHLIGHT, fontsize=9.5)

ax2.set_ylim(0, 55)
ax2.set_xticks(range(len(quarters)))
ax2.set_xticklabels(q_labels, fontsize=9)
ax2.set_ylabel("% of Footwear returns reporting a defect", fontsize=9.5)
ax2.set_title("Footwear returns citing a defect", loc="left", fontsize=11, color=DARK)

for ax in (ax1, ax2):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#999999")
    ax.tick_params(colors="#555555", labelsize=9)

# Title and subtitle
fig.text(0.07, 0.94, "Investigate Footwear first: returns jumped to 19.2% in Q3 2026, driven by defects",
         fontsize=14, fontweight="bold", color=DARK, ha="left")
fig.text(0.07, 0.885,
         f"Up {jump:.1f} pts from a {base_rate:.1f}% average, while no other category moved more than 0.9 pts. "
         f"Defect reports rose from ~{base_defect:.0f}% to 46% of Footwear returns.",
         fontsize=10, color="#555555", ha="left")

# Caveat
fig.text(0.07, 0.045,
         "Caveat: Footwear's return window was extended from 30 to 60 days for a Q3 2026 promotion. "
         "Past extensions added about 2 pts to the return rate,\n"
         f"so the policy explains only a small part of the {jump:.1f}-pt jump. The rest points to a product quality problem.",
         fontsize=9, color="#555555", ha="left", va="bottom", style="italic")
