import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Forecast variance by department, $ million (positive = overspend)
dept = (df.groupby("department")["variance_k"].sum() / 1000).sort_values()
departments = dept.index.tolist()
values = dept.values
y = np.arange(len(departments))

city_total = dept.sum()
transit_total = dept["Transit"]
transit_share = transit_total / city_total * 100
roads_total = dept["Roads"]
police_total = dept["Police"]

transit_ot = df[(df["department"] == "Transit") &
                (df["budget_line"] == "Overtime")].iloc[0]
ot_var_m = transit_ot["variance_k"] / 1000
ot_budget_m = transit_ot["annual_budget_k"] / 1000
ot_pct = transit_ot["variance_pct"]
transit_other_m = transit_total - ot_var_m

STRONG = "#B2182B"   # the one message: Transit
LIGHT_RED = "#F4A582"  # remainder of the Transit bar, same hue
GREY = "#B8B8B8"    # context
DARK_GREY = "#666666"

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.11, right=0.97, top=0.84, bottom=0.17)

# Context bars
ax.barh(y, values, height=0.58, color=GREY, zorder=2)

# Transit bar: overtime in the strong colour, the rest in a pale tint of it
y_transit = departments.index("Transit")
ax.barh(y_transit, ot_var_m, height=0.58, color=STRONG, zorder=3)
ax.barh(y_transit, transit_other_m, left=ot_var_m, height=0.58,
        color=LIGHT_RED, zorder=3)
ax.text(ot_var_m / 2, y_transit, "Overtime", ha="center", va="center",
        color="white", fontsize=10, fontweight="bold", zorder=4)

# Roads downside risk: hatched, not part of the forecast
y_roads = departments.index("Roads")
roads_risk_m = 1.5
ax.barh(y_roads, roads_risk_m, left=roads_total, height=0.58,
        facecolor="none", edgecolor=DARK_GREY, hatch="///", linewidth=0.9,
        zorder=3)

# Number labels only where they carry the message
ax.text(transit_total + 0.07, y_transit, f"${transit_total:.1f}M",
        ha="left", va="center", color=STRONG, fontsize=13,
        fontweight="bold")
ax.text(roads_total / 2, y_roads, f"${roads_total:.1f}M",
        ha="center", va="center", color="white", fontsize=10,
        fontweight="bold", zorder=4)
ax.text(roads_total + roads_risk_m + 0.07, y_roads,
        "up to +$1.5M more\nin a harsh winter",
        ha="left", va="center", color=DARK_GREY, fontsize=9)

y_police = departments.index("Police")
ax.text(police_total + 0.07, y_police, f"${police_total:.1f}M",
        ha="left", va="center", color=DARK_GREY, fontsize=10)

# Why Transit: direct annotation into the empty space, no legend
ax.annotate(
    f"Overtime is ${ot_var_m:.1f}M over a ${ot_budget_m:.1f}M budget "
    f"(+{ot_pct:.0f}%)\nDriver vacancies covered by extra shifts",
    xy=(1.55, y_transit - 0.32), xytext=(1.5, 5.1),
    fontsize=10, color="#222222",
    arrowprops=dict(arrowstyle="->", color=STRONG, lw=1.2),
    bbox=dict(boxstyle="round,pad=0.45", facecolor="#FDECEC",
              edgecolor=STRONG, linewidth=0.9),
)

ax.axvline(0, color="#222222", linewidth=1.0, zorder=4)
ax.set_yticks(y)
ax.set_yticklabels(departments, fontsize=11)
for label in ax.get_yticklabels():
    if label.get_text() == "Transit":
        label.set_fontweight("bold")
        label.set_color(STRONG)

ax.set_xlim(-0.6, 3.7)
ax.set_xticks(np.arange(-0.5, 3.51, 0.5))
ax.tick_params(axis="x", labelsize=10)
ax.set_xlabel("Forecast variance vs annual budget ($ million) "
              "— right of zero is an overspend", fontsize=10)
ax.xaxis.grid(True, color="#E6E6E6", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

fig.text(0.02, 0.955,
         f"Transit accounts for ${transit_total:.1f}M of the city's "
         f"${city_total:.1f}M forecast overspend",
         fontsize=16, fontweight="bold", color="#111111")
fig.text(0.02, 0.91,
         f"Put Transit under mid-year review first — {transit_share:.0f}% "
         f"of the overspend, ahead of Roads (${roads_total:.1f}M) and "
         f"Police (${police_total:.1f}M)",
         fontsize=10.5, color=DARK_GREY)

fig.text(0.02, 0.02,
         "Note: Roads forecast assumes snow clearing at the five-year "
         "average; the hatched bar shows up to $1.5M more in a harsh winter.   "
         "Forecast year-end spending minus annual budget.",
         fontsize=8.5, color=DARK_GREY)
