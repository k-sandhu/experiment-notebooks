import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

FOCUS = "Customer Support"
RED = "#C0392B"
GREY = "#BDBDBD"
DARK = "#333333"

questions = [
    "My manager supports my growth",
    "I see myself working here in two years",
]

fig, axes = plt.subplots(1, 2, figsize=(10, 6), sharey=True)
fig.subplots_adjust(left=0.08, right=0.97, top=0.78, bottom=0.17, wspace=0.12)

for i, (ax, q) in enumerate(zip(axes, questions)):
    piv = (df[df["question"] == q]
           .pivot(index="department", columns="year", values="pct_favourable"))

    # Other departments in grey, for context
    for dept, row in piv.iterrows():
        if dept == FOCUS:
            continue
        ax.plot([0, 1], [row[2025], row[2026]], color=GREY, lw=1.3,
                marker="o", ms=4, zorder=1)

    # Customer Support highlighted
    v25, v26 = piv.loc[FOCUS, 2025], piv.loc[FOCUS, 2026]
    change = v26 - v25
    ax.plot([0, 1], [v25, v26], color=RED, lw=3.2, marker="o", ms=7, zorder=3)
    ax.text(-0.06, v25, f"{v25:.0f}%", color=RED, fontsize=12,
            fontweight="bold", ha="right", va="center")
    ax.text(1.06, v26, f"{v26:.0f}%  ({change:+.0f} pts)".replace("-", "\u2212"),
            color=RED, fontsize=12, fontweight="bold", ha="left", va="center")
    ax.text(1.0, v26 - 4.5, FOCUS, color=RED, fontsize=10.5,
            ha="center", va="top")

    # Label for the grey context lines
    others = piv.drop(index=FOCUS)
    ax.text(1.06, others[2026].max() + 1.5, "Other 8 departments",
            color="#8A8A8A", fontsize=9.5, ha="left", va="bottom")

    ax.set_title(f"\u201c{q}\u201d", fontsize=12, color=DARK, loc="left", pad=10)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Sep 2025", "Sep 2026"], fontsize=10.5, color=DARK)
    ax.set_xlim(-0.45, 1.75)
    ax.set_ylim(30, 92)
    ax.tick_params(axis="y", labelsize=10, colors="#666666")
    ax.tick_params(axis="x", length=0)
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color("#999999")
    ax.spines["bottom"].set_color("#999999")
    ax.yaxis.grid(True, color="#EEEEEE", lw=0.8)
    ax.set_axisbelow(True)

axes[0].set_ylabel("% favourable (agree or strongly agree)", fontsize=10.5,
                   color=DARK)
axes[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))

# Title and subtitle
fig.text(0.02, 0.955,
         "Customer Support's manager-support score fell 27 points, "
         "the biggest drop anywhere",
         fontsize=15.5, fontweight="bold", color=DARK, ha="left", va="top")
fig.text(0.02, 0.885,
         "Its staff are also far less likely to see themselves at Northlight "
         "in two years. Every other department held steady.",
         fontsize=11.5, color="#555555", ha="left", va="top")

# Caveat that changes how the chart is read
sup = df[(df["department"] == FOCUS)].drop_duplicates("year").set_index("year")
fig.text(0.02, 0.035,
         f"Caveat: only {sup.loc[2026, 'response_rate_pct']}% of Customer Support "
         f"staff responded in 2026 ({sup.loc[2026, 'n_responses']} of "
         f"{sup.loc[2026, 'headcount']}), down from "
         f"{sup.loc[2025, 'response_rate_pct']}% in 2025, so their 2026 scores "
         f"are less certain than other departments'.",
         fontsize=9.5, color="#555555", style="italic", ha="left", va="bottom",
         wrap=True)
