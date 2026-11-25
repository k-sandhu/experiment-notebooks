import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.transforms import blended_transform_factory

df = pd.read_csv("data.csv")

# Urgent patients only. Northgate's clock starts at registration (~+15 min),
# so put it on the same triage basis as the other hospitals.
urgent = df[df["triage_category"] == "Urgent"].copy()
urgent["median_wait_adj"] = (
    urgent["median_wait_min"]
    - urgent["wait_clock_starts_at"].eq("registration") * 15
)
urgent = urgent.sort_values("median_wait_adj")  # longest wait on top

riverside_val = float(
    urgent.loc[urgent["hospital"] == "Riverside", "median_wait_adj"].iloc[0]
)
other_avg = float(
    urgent.loc[urgent["hospital"] != "Riverside", "median_wait_adj"].mean()
)
riverside_y = len(urgent) - 1

strong = "#C62828"
grey = "#AFAFAF"
colors = [strong if h == "Riverside" else grey for h in urgent["hospital"]]

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.15, right=0.96, top=0.79, bottom=0.16)

# Title aligned with the left edge of the chart, not the axes.
fig.text(
    0.015,
    0.97,
    "Riverside should get the extra triage nurses:\n"
    f"urgent patients wait {riverside_val:.0f} min — more than twice "
    f"the {other_avg:.0f}-min average elsewhere",
    fontsize=17,
    fontweight="bold",
    ha="left",
    va="top",
    linespacing=1.2,
)

ax.barh(
    urgent["hospital"],
    urgent["median_wait_adj"],
    color=colors,
    height=0.62,
    zorder=3,
)

ax.set_xlim(0, 66)
ax.set_ylim(-0.6, 7.6)
ax.set_xticks([0, 20, 40, 60])
ax.set_xlabel(
    "Median wait to first be seen by a doctor (minutes)", fontsize=11
)

# Only number labelled on a bar: the one in the title.
ax.text(
    riverside_val + 1.2,
    riverside_y,
    f"{riverside_val:.0f} min",
    va="center",
    ha="left",
    fontsize=13,
    fontweight="bold",
    color=strong,
    zorder=6,
)

# Average-elsewhere reference, labelled at the top of the line
# where the eye is already comparing it with Riverside.
ax.axvline(
    other_avg,
    ymin=0,
    ymax=0.97,
    color="#555555",
    linestyle="--",
    linewidth=1.3,
    zorder=5,
)
top_of_line = blended_transform_factory(ax.transData, ax.transAxes)
ax.text(
    other_avg,
    1.005,
    f"Average elsewhere: {other_avg:.0f} min",
    transform=top_of_line,
    va="bottom",
    ha="center",
    fontsize=10,
    color="#444444",
    clip_on=False,
)

for label in ax.get_yticklabels():
    label.set_fontsize(12)
    if label.get_text() == "Riverside":
        label.set_fontweight("bold")
        label.set_color(strong)

ax.tick_params(axis="x", labelsize=11)
ax.tick_params(axis="y", length=0)
ax.xaxis.grid(True, color="#E6E6E6", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

fig.text(
    0.015,
    0.015,
    "Urgent patients only, July–September 2026  •  "
    "Northgate adjusted down 15 min: its clock starts at registration, not triage.",
    fontsize=9,
    color="#555555",
    ha="left",
    va="bottom",
)
