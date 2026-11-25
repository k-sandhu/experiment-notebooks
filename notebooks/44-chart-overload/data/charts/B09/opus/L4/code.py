import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

q = "My manager supports my growth"
mgr = df[df["question"] == q]
now = mgr[mgr["year"] == 2026].set_index("department")
prev = mgr[mgr["year"] == 2025].set_index("department")

# Lowest score at the top of the chart
now = now.sort_values("pct_favourable", ascending=True)
depts = now.index.tolist()
vals = now["pct_favourable"].values

focus = "Customer Support"
accent = "#C8102E"
grey = "#C4C4C4"
colors = [accent if d == focus else grey for d in depts]

fig, ax = plt.subplots(figsize=(10, 6))
y = list(range(len(depts)))
fy = depts.index(focus)
fval = int(now.loc[focus, "pct_favourable"])
pval = int(prev.loc[focus, "pct_favourable"])

# Ghost bar: where Support was last year
ax.barh(fy, pval, height=0.65, facecolor="none", edgecolor=accent,
        linestyle=(0, (3, 2)), linewidth=1.3, zorder=2)
ax.barh(y, vals, color=colors, height=0.65, zorder=3)
ax.invert_yaxis()

# Department labels, focus highlighted (asterisk links to the caveat)
ax.set_yticks(y)
ax.set_yticklabels([d + "*" if d == focus else d for d in depts], fontsize=11)
for tick, d in zip(ax.get_yticklabels(), depts):
    if d == focus:
        tick.set_color(accent)
        tick.set_fontweight("bold")

# Only the numbers that carry the message
ax.text(fval - 1.2, fy, f"{fval}%", va="center", ha="right",
        fontsize=12, color="white", fontweight="bold", zorder=4)
ax.text(pval + 1.2, fy - 0.08, f"{pval}% in 2025", va="center", ha="left",
        fontsize=10.5, color=accent, fontweight="bold")

rr_now = int(now.loc[focus, "response_rate_pct"])
rr_prev = int(prev.loc[focus, "response_rate_pct"])
ax.text(pval + 1.2, fy + 0.28, f"*only {rr_now}% responded (vs {rr_prev}%)",
        va="center", ha="left", fontsize=9, color="#555555", style="italic")

# Honest scale
ax.set_xlim(0, 100)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=10, color="#555555")
ax.set_xlabel("% favourable (agree or strongly agree), September 2026 survey",
              fontsize=10, color="#555555")
ax.tick_params(axis="y", length=0)
ax.tick_params(axis="x", colors="#777777")
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#AAAAAA")
ax.xaxis.grid(True, color="#EEEEEE", zorder=0)
ax.set_axisbelow(True)

# Title and subtitle
fig.suptitle(f"Customer Support needs manager support most: {fval}% favourable, down from {pval}%",
             x=0.02, ha="left", fontsize=14, fontweight="bold", y=0.965)
ax.set_title("“My manager supports my growth”, by department. Every other department "
             "scores 58% or higher and changed by 3 points or less.",
             loc="left", fontsize=10.5, color="#555555", pad=12)

# Caveat that changes how the Support bar should be read
n_now = int(now.loc[focus, "n_responses"])
hc = int(now.loc[focus, "headcount"])
fig.text(0.02, 0.03,
         f"*Only {n_now} of {hc} Customer Support staff responded this year "
         f"({rr_now}%, vs {rr_prev}% in 2025; other departments 77–85%). "
         f"The drop is large but less certain.",
         ha="left", fontsize=9.5, color="#333333")

fig.subplots_adjust(left=0.18, right=0.96, top=0.86, bottom=0.17)
