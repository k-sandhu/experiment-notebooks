import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Only the question relevant to the manager-support programme decision
question = "My manager supports my growth"
d = df[df["question"] == question].copy()

pivot = (
    d.pivot(index="department", columns="year", values="pct_favourable")
    .sort_values(2026, ascending=True)
)

support = "Customer Support"
support_2026 = int(pivot.loc[support, 2026])
support_2025 = int(pivot.loc[support, 2025])
drop = support_2025 - support_2026

# Second-lowest department in 2026, to show how far Support is adrift
second_dept = pivot.index[1]
second_2026 = int(pivot[2026].iloc[1])

# Caveat figures for Customer Support, taken from the data
s26 = d[(d["department"] == support) & (d["year"] == 2026)].iloc[0]
s25 = d[(d["department"] == support) & (d["year"] == 2025)].iloc[0]

HIGHLIGHT = "#C1272D"
GREY = "#BDBDBD"
DARK = "#404040"

fig, ax = plt.subplots(figsize=(10, 6))

departments = list(pivot.index)
y = range(len(departments))
colors = [HIGHLIGHT if dep == support else GREY for dep in departments]

ax.barh(y, pivot[2026], color=colors, height=0.58, edgecolor="none", zorder=3)

# 2025 scores as dark ticks on the same scale (labelled in the axis title, no legend)
ax.scatter(
    pivot[2025],
    list(y),
    marker="|",
    s=300,
    linewidths=2.4,
    color=DARK,
    zorder=5,
)

ax.set_yticks(list(y))
ax.set_yticklabels(departments, fontsize=11)
ax.invert_yaxis()  # Lowest (Customer Support) at the top
for label in ax.get_yticklabels():
    if label.get_text() == support:
        label.set_fontweight("bold")
        label.set_color(HIGHLIGHT)

# Honest scale: bars start at zero, full 0-100% range for a percentage
ax.set_xlim(0, 100)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0", "25", "50", "75", "100%"], fontsize=10)
ax.set_xlabel(
    "% favourable — \u201cMy manager supports my growth\u201d"
    "   (bars = 2026, dark ticks = 2025)",
    fontsize=11,
)
ax.grid(axis="x", color="#DDDDDD", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for spine in ("top", "right", "left"):
    ax.spines[spine].set_visible(False)
ax.tick_params(left=False)

# Title states the decision message as a sentence
ax.set_title(
    f"Give the manager-support programme to Customer Support:\n"
    f"its score fell {drop} points to {support_2026}%, far below every other department",
    loc="left",
    fontsize=16,
    fontweight="bold",
    pad=16,
)

# Number labels only where they carry the message
y_support = departments.index(support)
ax.text(
    support_2026 + 2,
    y_support,
    f"{support_2026}%   (was {support_2025}% in 2025, \u2212{drop} pts)",
    va="center",
    fontsize=11.5,
    fontweight="bold",
    color=HIGHLIGHT,
)

y_second = departments.index(second_dept)
ax.text(
    second_2026 + 2,
    y_second,
    f"{second_2026}% \u2014 next lowest",
    va="center",
    fontsize=10,
    color=DARK,
)

# Caveat that changes how the highlighted bar should be read
fig.text(
    0.07,
    0.015,
    f"Caution: only {int(s26['response_rate_pct'])}% of Customer Support responded in 2026 "
    f"({int(s26['n_responses'])} of {int(s26['headcount'])}, vs {int(s25['response_rate_pct'])}% in 2025), "
    "so its score is less certain than other departments'.",
    fontsize=9,
    color="#555555",
)

fig.subplots_adjust(left=0.20, right=0.97, top=0.83, bottom=0.16)
