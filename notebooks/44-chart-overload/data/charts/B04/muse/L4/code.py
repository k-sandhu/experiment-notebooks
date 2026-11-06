import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Department totals only — the decision is which department to review.
dept_m = (df.groupby("department")["variance_k"].sum() / 1000).sort_values()
city_total_m = dept_m.sum()
transit_total_m = dept_m["Transit"]
transit_share = transit_total_m / city_total_m * 100

ot = df[(df["department"] == "Transit") & (df["budget_line"] == "Overtime")].iloc[0]
transit_ot_m = ot["variance_k"] / 1000
transit_ot_pct = ot["variance_pct"]
transit_rest_m = transit_total_m - transit_ot_m

GREY = "#B8B8B8"
RED = "#C1272D"
LIGHT_RED = "#E8A9AB"

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.115, right=0.94, top=0.79, bottom=0.17)

y = range(len(dept_m))
ax.barh(y, dept_m.values, color=GREY, height=0.58)

# Transit: split the total bar to show its overtime driver (no legend needed).
ti = list(dept_m.index).index("Transit")
ax.barh(ti, transit_ot_m, color=RED, height=0.58)
ax.barh(ti, transit_rest_m, left=transit_ot_m, color=LIGHT_RED, height=0.58)

ax.set_yticks(list(y))
ax.set_yticklabels(dept_m.index, fontsize=12)
for label in ax.get_yticklabels():
    if label.get_text() == "Transit":
        label.set_fontweight("bold")
        label.set_color(RED)

ax.tick_params(axis="y", length=0)
ax.tick_params(axis="x", labelsize=11)
ax.set_ylim(-0.65, len(dept_m) - 0.25)
ax.axvline(0, color="black", linewidth=1.2)
ax.set_xlim(-0.65, 3.85)
ax.set_xticks([-0.5, 0, 1, 2, 3])
ax.set_xlabel(
    "Forecast variance vs budget ($ million)  —  positive = overspend",
    fontsize=11,
)

ax.xaxis.grid(True, color="#E5E5E5", linewidth=0.8)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

# The one message, as the title — placed at figure level so it is not
# squeezed against the top bar.
fig.text(
    0.07, 0.97,
    f"Put Transit under review: it accounts for ${transit_total_m:.1f}m of the\n"
    f"city's ${city_total_m:.1f}m forecast overspend ({transit_share:.0f}%)",
    ha="left", va="top", fontsize=16, fontweight="bold",
)
fig.text(
    0.07, 0.855,
    "Driver vacancies are being covered by extra shifts.",
    ha="left", va="top", fontsize=11.5, color="#444444",
)

# Number labels only where they carry the message. Single lines, sized
# to fit inside their bar segments.
ax.text(
    transit_ot_m / 2, ti,
    f"Overtime +${transit_ot_m:.1f}m (+{transit_ot_pct:.0f}%)",
    va="center", ha="center", fontsize=10.5,
    fontweight="bold", color="white",
)
ax.text(
    transit_ot_m + transit_rest_m / 2, ti,
    f"other +${transit_rest_m:.1f}m",
    va="center", ha="center", fontsize=9, color="#7A1F22",
)
ax.text(
    transit_total_m + 0.07, ti, f"${transit_total_m:.1f}m",
    va="center", ha="left", fontsize=13, fontweight="bold", color=RED,
)

fig.text(
    0.07, 0.045,
    "Department forecast year-end spending minus annual budget. Roads assumes average snow clearing; "
    "a harsh winter (+up to $1.5m)\nwould still leave Roads below Transit.",
    ha="left", va="bottom", fontsize=8.5, color="#555555",
)
