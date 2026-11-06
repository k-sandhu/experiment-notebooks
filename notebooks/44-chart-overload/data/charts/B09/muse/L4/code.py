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

second_dept = pivot.index[1]
second_2026 = int(pivot.loc[second_dept, 2026])
second_2025 = int(pivot.loc[second_dept, 2025])
gap = second_2026 - support_2026

s26 = d[(d["department"] == support) & (d["year"] == 2026)].iloc[0]
s25 = d[(d["department"] == support) & (d["year"] == 2025)].iloc[0]

HIGHLIGHT = "#C1272D"
GREY = "#B8B8B8"
DARK = "#404040"

fig, ax = plt.subplots(figsize=(10, 6))

departments = list(pivot.index)
y = list(range(len(departments)))
colors = [HIGHLIGHT if dep == support else GREY for dep in departments]
bar_h = 0.56

ax.barh(y, pivot[2026], color=colors, height=bar_h, edgecolor="none", zorder=3)

# 2025 scores as short ticks contained within the bar height,
# so they do not protrude or collide with text
for yi, x25 in zip(y, pivot[2025]):
    ax.plot(
        [x25, x25],
        [yi - bar_h / 2, yi + bar_h / 2],
        color=DARK,
        linewidth=2.4,
        zorder=5,
        solid_capstyle="butt",
    )

ax.set_yticks(y)
ax.set_yticklabels(departments, fontsize=12)
ax.invert_yaxis()  # Lowest (Customer Support) at the top
for label in ax.get_yticklabels():
    if label.get_text() == support:
        label.set_fontweight("bold")
        label.set_color(HIGHLIGHT)

# Honest scale: bars start at zero, full 0-100% range
ax.set_xlim(0, 100)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0", "25", "50", "75", "100%"], fontsize=10)
ax.set_xlabel(
    "% favourable \u2014 \u201cMy manager supports my growth\u201d"
    "   (bars = 2026, dark ticks = 2025)",
    fontsize=11,
)
ax.grid(axis="x", color="#E0E0E0", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for spine in ("top", "right", "left"):
    ax.spines[spine].set_visible(False)
ax.tick_params(left=False)

# Title states the decision; subtitle gives the evidence in one line
fig.text(
    0.07,
    0.94,
    "Give the manager-support programme to Customer Support",
    fontsize=17,
    fontweight="bold",
    va="top",
)
fig.text(
    0.07,
    0.885,
    f"Its manager-support score fell {drop} points to {support_2026}% \u2014 "
    f"{gap} points below the next-lowest department",
    fontsize=12,
    color="#333333",
    va="top",
)

y_support = departments.index(support)
y_second = departments.index(second_dept)

# 2026 value sits immediately after the highlighted bar
ax.text(
    support_2026 + 1.5,
    y_support,
    f"{support_2026}%",
    va="center",
    fontsize=13,
    fontweight="bold",
    color=HIGHLIGHT,
)

# 2025 value sits after its tick, so text never crosses the tick;
# labelling this one tick also teaches what every tick means
ax.text(
    support_2025 + 1.5,
    y_support,
    f"was {support_2025}% in 2025\n\u2212{drop} pts",
    va="center",
    fontsize=10.5,
    color=DARK,
    linespacing=1.25,
)

# Next-lowest label placed beyond both its bar end and its 2025 tick
ax.text(
    max(second_2026, second_2025) + 1.5,
    y_second,
    f"{second_2026}% \u2014 next lowest",
    va="center",
    fontsize=10.5,
    color=DARK,
)

# Caveat that changes how the highlighted bar should be read
fig.text(
    0.07,
    0.025,
    f"Caution: only {int(s26['response_rate_pct'])}% of Customer Support responded in 2026 "
    f"({int(s26['n_responses'])} of {int(s26['headcount'])}, vs {int(s25['response_rate_pct'])}% in 2025), "
    "so its score is less certain than other departments'.",
    fontsize=9.5,
    color="#555555",
)

fig.subplots_adjust(left=0.20, right=0.97, top=0.81, bottom=0.17)
