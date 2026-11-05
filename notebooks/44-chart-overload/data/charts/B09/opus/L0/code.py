import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

df = pd.read_csv("data.csv")

# Point change in % favourable, 2025 -> 2026, for each department x question
wide = df.pivot_table(index=["department", "question"], columns="year",
                      values="pct_favourable")
change = (wide[2026] - wide[2025]).unstack("question")

questions = [
    "My manager supports my growth",
    "I see myself working here in two years",
    "I would recommend Northlight as a place to work",
    "I have the tools I need to do my job",
    "My workload is manageable",
    "I understand the company's strategy",
]
q_labels = [
    "Manager supports\nmy growth",
    "See myself here\nin two years",
    "Would recommend\nNorthlight",
    "Have the tools\nI need",
    "Workload is\nmanageable",
    "Understand company\nstrategy",
]

# Customer Support first, then the rest by headcount (largest first)
info = df.groupby(["department", "year"])[["response_rate_pct", "n_responses", "headcount"]].first()
heads = df.groupby("department")["headcount"].first().sort_values(ascending=False)
depts = ["Customer Support"] + [d for d in heads.index if d != "Customer Support"]

mat = change.loc[depts, questions].values

row_labels = []
for d in depts:
    r26 = info.loc[(d, 2026), "response_rate_pct"]
    r25 = info.loc[(d, 2025), "response_rate_pct"]
    if d == "Customer Support":
        row_labels.append(f"{d}\n{r26}% responded (was {r25}%)")
    else:
        row_labels.append(f"{d}  ({r26}% responded)")

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.27, right=0.88, top=0.74, bottom=0.09)

lim = np.ceil(np.abs(mat).max())
im = ax.imshow(mat, cmap="RdBu", vmin=-lim, vmax=lim, aspect="auto")

for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        v = mat[i, j]
        txt = f"{v:+.0f}" if v != 0 else "0"
        color = "white" if abs(v) > lim * 0.55 else "#222222"
        weight = "bold" if abs(v) >= 15 else "normal"
        ax.text(j, i, txt, ha="center", va="center", fontsize=10,
                color=color, fontweight=weight)

ax.set_xticks(range(len(questions)))
ax.set_xticklabels(q_labels, fontsize=9)
ax.xaxis.tick_top()
ax.set_yticks(range(len(depts)))
ax.set_yticklabels(row_labels, fontsize=9)
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)

# Thin white gridlines between cells
ax.set_xticks(np.arange(-0.5, len(questions), 1), minor=True)
ax.set_yticks(np.arange(-0.5, len(depts), 1), minor=True)
ax.grid(which="minor", color="white", linewidth=1.5)
ax.tick_params(which="minor", length=0)

# Outline the Customer Support row and bold its label
ax.add_patch(Rectangle((-0.5, -0.5), len(questions), 1, fill=False,
                       edgecolor="#333333", linewidth=1.6, clip_on=False))
ax.get_yticklabels()[0].set_fontweight("bold")

cax = fig.add_axes([0.905, 0.09, 0.018, 0.65])
cb = fig.colorbar(im, cax=cax)
cb.set_label("Change in % favourable, 2025 → 2026 (points)", fontsize=9)
cb.ax.tick_params(labelsize=8)
cb.outline.set_visible(False)

fig.text(0.02, 0.955,
         "Customer Support fell sharply on manager support (−27) and intent to stay (−23)",
         fontsize=13.5, fontweight="bold", ha="left")
fig.text(0.02, 0.905,
         "Elsewhere scores barely moved, except understanding of strategy, up 7–11 points in every department.\n"
         "Caution: only 38% of Customer Support answered in 2026 (53 of 140), down from 81%, so its results are less certain.",
         fontsize=9.5, color="#444444", ha="left", va="top")

fig.text(0.02, 0.025,
         "Cells show 2026 minus 2025 % favourable (agree or strongly agree). Response rate = 2026 respondents as % of headcount. "
         "Survey ran 8–22 September.",
         fontsize=8, color="#666666", ha="left")
