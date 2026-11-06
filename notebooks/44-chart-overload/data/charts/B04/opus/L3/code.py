import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Forecast variance by department, in $ millions (positive = overspend)
dept = df.groupby("department")["variance_k"].sum().div(1000).sort_values(ascending=False)
total = dept.sum()

transit_total = dept["Transit"]
transit_ot = df.query("department == 'Transit' and budget_line == 'Overtime'")["variance_k"].iloc[0] / 1000
transit_ot_pct = df.query("department == 'Transit' and budget_line == 'Overtime'")["variance_pct"].iloc[0]
transit_other = transit_total - transit_ot
roads = dept["Roads"]
roads_risk = 1.5
share = transit_total / total * 100

STRONG = "#C0392B"
STRONG_LIGHT = "#E8A79F"
GREY = "#BDBDBD"
DARK_GREY = "#7F7F7F"
TEXT = "#333333"

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.11, right=0.97, top=0.80, bottom=0.12)

names = list(dept.index)
y = range(len(names))
h = 0.68

for i, name in enumerate(names):
    v = dept[name]
    if name == "Transit":
        ax.barh(i, transit_ot, height=h, color=STRONG, zorder=3)
        ax.barh(i, transit_other, left=transit_ot, height=h, color=STRONG_LIGHT, zorder=3)
    elif name == "Roads":
        ax.barh(i, v, height=h, color=DARK_GREY, zorder=3)
    else:
        ax.barh(i, v, height=h, color=GREY, zorder=3)

ti = names.index("Transit")
ri = names.index("Roads")
pi = names.index("Police")

# Transit annotations
ax.text(transit_ot / 2, ti, f"Overtime +${transit_ot:.1f}M", ha="center", va="center",
        color="white", fontsize=10.5, fontweight="bold", zorder=4)
ax.text(transit_total + 0.08, ti - 0.13, f"+${transit_total:.1f}M  ({share:.0f}% of city total)",
        ha="left", va="center", color=STRONG, fontsize=12, fontweight="bold")
ax.text(transit_total + 0.08, ti + 0.25,
        f"Overtime is {transit_ot_pct:.0f}% over its ${2.0:.1f}M budget:\ndriver vacancies covered by extra shifts",
        ha="left", va="top", color=TEXT, fontsize=9.5)

# Roads: harsh-winter risk shown as hatched extension
ax.barh(ri, roads_risk, left=roads, height=h, facecolor="none", edgecolor=DARK_GREY,
        hatch="///", linewidth=0.8, linestyle="--", zorder=3)
ax.text(roads / 2, ri, f"+${roads:.1f}M", ha="center", va="center",
        color="white", fontsize=10, fontweight="bold", zorder=4)
ax.text(roads + roads_risk + 0.08, ri,
        f"Harsh winter could add up to ${roads_risk:.1f}M\n(forecast assumes average snow clearing)\n"
        f"→ ${roads + roads_risk:.1f}M, still below Transit",
        ha="left", va="center", color=TEXT, fontsize=9.5)

# Police label
ax.text(dept["Police"] + 0.06, pi, f"+${dept['Police']:.1f}M", ha="left", va="center",
        color=TEXT, fontsize=10)

# Axes styling
ax.set_yticks(list(y))
ax.set_yticklabels(names, fontsize=10.5, color=TEXT)
ax.get_yticklabels()[ti].set_color(STRONG)
ax.get_yticklabels()[ti].set_fontweight("bold")
ax.invert_yaxis()
ax.axvline(0, color=TEXT, linewidth=0.9, zorder=4)
ax.set_xlim(-0.6, 6.0)
ax.set_xticks([-0.5, 0, 1, 2, 3])
ax.set_xticklabels(["−$0.5M", "$0", "$1M", "$2M", "$3M"], fontsize=9.5, color=TEXT)
ax.set_xlabel("Forecast year-end spending minus approved budget ($ millions; right of zero = overspend)",
              fontsize=9.5, color=TEXT)
ax.grid(axis="x", color="#EEEEEE", zorder=0)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#999999")
ax.tick_params(axis="y", length=0)

# Title and subtitle
fig.text(0.02, 0.95, f"Transit drives {share:.0f}% of the city's ${total:.1f}M forecast overspend — review Transit",
         fontsize=15, fontweight="bold", color=TEXT, ha="left")
fig.text(0.02, 0.895,
         f"Forecast overspend by department, City of Marlow, full year. City total: +${total:.1f}M. "
         f"Next largest: Roads +${roads:.1f}M, Police +${dept['Police']:.1f}M.",
         fontsize=10.5, color="#555555", ha="left")
