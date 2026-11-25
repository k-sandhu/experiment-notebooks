import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

q_manager = "My manager supports my growth"
q_stay = "I see myself working here in two years"
questions = [q_manager, q_stay]
titles = ["\u201cMy manager supports my growth\u201d",
          "\u201cI see myself working here in two years\u201d"]

# Pivot to 2025 vs 2026 by department for the two decision-relevant questions
pivots = {}
for q in questions:
    p = (df.loc[df["question"] == q]
           .pivot(index="department", columns="year", values="pct_favourable"))
    pivots[q] = p

# Order by 2026 manager-support score (lowest first -> shown at top)
order = pivots[q_manager].sort_values(2026).index.tolist()
y = np.arange(len(order))

# Caveat figures for Customer Support, taken from the data
cs = df[(df["department"] == "Customer Support") & (df["question"] == q_manager)]
cs25 = cs.loc[cs["year"] == 2025].iloc[0]
cs26 = cs.loc[cs["year"] == 2026].iloc[0]

STRONG = "#C1272D"
GREY = "#B8B8B8"
DARK = "#333333"

fig, axes = plt.subplots(1, 2, figsize=(10, 6), sharey=True)
fig.subplots_adjust(left=0.19, right=0.97, top=0.80, bottom=0.17, wspace=0.14)

fig.text(
    0.02, 0.96,
    "Give the manager-support programme to Customer Support \u2014\n"
    "manager support and intent to stay have fallen sharply there",
    ha="left", va="top", fontsize=15.5, fontweight="bold", color=DARK,
)

for ax, q, title in zip(axes, questions, titles):
    p = pivots[q].loc[order]
    v26 = p[2026].to_numpy(dtype=float)
    v25 = p[2025].to_numpy(dtype=float)
    colours = [STRONG if d == "Customer Support" else GREY for d in order]

    ax.barh(y, v26, height=0.62, color=colours, edgecolor="none")
    # 2025 score as a dark tick on each bar (labelled directly, no legend)
    ax.scatter(v25, y, marker="|", s=260, linewidths=2.2, color=DARK, zorder=5)
    ax.text(0.98, 0.02, "|  = 2025 score", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=8.5, color=DARK)

    # Only Customer Support is number-labelled: it carries the message
    i = order.index("Customer Support")
    change = v26[i] - v25[i]
    ax.text(v26[i] + 3, y[i],
            f"{v26[i]:.0f}%  (was {v25[i]:.0f}%, {change:.0f} pts)",
            ha="left", va="center", fontsize=10.5, fontweight="bold", color=STRONG)

    ax.set_title(title, loc="left", fontsize=11, fontweight="bold", color=DARK, pad=10)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=9, color=DARK)
    ax.set_xlabel("% favourable (agree / strongly agree), Sep 2026",
                  fontsize=9, color=DARK)
    ax.xaxis.grid(True, color="#E5E5E5", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#CCCCCC")
    ax.tick_params(length=0)

axes[0].set_yticks(y)
axes[0].set_yticklabels(order, fontsize=10, color=DARK)
for label in axes[0].get_yticklabels():
    if label.get_text() == "Customer Support":
        label.set_fontweight("bold")
        label.set_color(STRONG)
axes[0].invert_yaxis()

fig.text(
    0.02, 0.025,
    f"Caution: only {cs26['response_rate_pct']:.0f}% of Customer Support responded in 2026 "
    f"({int(cs26['n_responses'])} of {int(cs26['headcount'])}; "
    f"{cs25['response_rate_pct']:.0f}% in 2025), so its 2026 scores are "
    "less certain than other departments\u2019.",
    ha="left", va="bottom", fontsize=9, color=DARK,
)
