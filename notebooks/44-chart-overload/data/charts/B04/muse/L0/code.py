import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Department totals, ordered by net forecast variance (largest overspend first)
dept = (
    df.groupby("department")
      .agg(budget_k=("annual_budget_k", "sum"), variance_k=("variance_k", "sum"))
      .sort_values("variance_k", ascending=False)
)
dept["variance_pct_total"] = 100 * dept["variance_k"] / dept["budget_k"]
order = list(dept.index)

# Variance by budget line, in $ million
lines = ["Staff", "Overtime", "Contracts", "Materials", "Fleet"]
pivot = (
    df.pivot_table(index="department", columns="budget_line",
                   values="variance_k", aggfunc="sum")
      .reindex(index=order, columns=lines)
      .fillna(0) / 1000.0
)

city_budget_m = dept["budget_k"].sum() / 1000.0
city_var_m = dept["variance_k"].sum() / 1000.0
city_pct = 100 * city_var_m / city_budget_m
transit_var_m = dept.loc["Transit", "variance_k"] / 1000.0
transit_share = 100 * transit_var_m / city_var_m
transit_ot = df.loc[
    (df["department"] == "Transit") & (df["budget_line"] == "Overtime")
].iloc[0]
transit_ot_var_m = transit_ot["variance_k"] / 1000.0
transit_ot_budget_m = transit_ot["annual_budget_k"] / 1000.0
transit_ot_pct = transit_ot["variance_pct"]

colors = {
    "Staff": "#4C78A8",
    "Overtime": "#E45756",
    "Contracts": "#54A24B",
    "Materials": "#F58518",
    "Fleet": "#B279A2",
}

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), sharey=True,
    gridspec_kw={"width_ratios": [3.0, 1.3], "wspace": 0.08},
)

y = np.arange(len(order))
pos_end = {}
net_m = dept["variance_k"].values / 1000.0

# Left panel: diverging stacked variance in $m
for i, dept_name in enumerate(order):
    pos, neg = 0.0, 0.0
    for line in lines:
        val = pivot.loc[dept_name, line]
        label = line if i == 0 else None
        if val >= 0:
            ax1.barh(i, val, left=pos, height=0.62,
                     color=colors[line], label=label)
            pos += val
        else:
            ax1.barh(i, abs(val), left=neg + val, height=0.62,
                     color=colors[line], label=label)
            neg += val
    pos_end[dept_name] = pos

# Roads harsh-winter scenario: not part of the forecast variance
roads_y = order.index("Roads")
ax1.barh(roads_y, 1.5, left=pos_end["Roads"], height=0.62,
         facecolor="none", edgecolor="#666666", hatch="///", linewidth=1.0)
ax1.annotate(
    "Roads: harsh winter could add\nup to +$1.5m (not in forecast)",
    xy=(pos_end["Roads"] + 1.5, roads_y),
    xytext=(2.55, roads_y + 0.55),
    fontsize=8, color="#444444",
    arrowprops=dict(arrowstyle="->", color="#666666", lw=0.9),
)

# Net department variance markers and labels
ax1.plot(net_m, y, marker="D", color="black", markersize=5,
         linestyle="none", zorder=5, label="Department net")
for i, val in enumerate(net_m):
    offset = 0.10 if val >= 0 else -0.10
    ha = "left" if val >= 0 else "right"
    # Keep the Transit label clear of its long bar
    x_text = val + offset
    ax1.text(x_text, i - 0.32, f"{val:+.1f}", fontsize=8,
             ha=ha, va="center", fontweight="bold")

# Key annotation for the main driver
transit_y = order.index("Transit")
ax1.annotate(
    f"Transit overtime +${transit_ot_var_m:.1f}m\n"
    f"({transit_ot_pct:+.0f}% of its ${transit_ot_budget_m:.1f}m budget)",
    xy=(1.45, transit_y), xytext=(1.05, transit_y + 1.35),
    fontsize=8.5, fontweight="bold", color="#A52A2A",
    arrowprops=dict(arrowstyle="->", color="#A52A2A", lw=1.1),
)

ax1.axvline(0, color="black", linewidth=0.9)
ax1.set_xlim(-0.95, 4.15)
ax1.set_xlabel("Forecast variance, $ million\n(left = underspend, right = overspend)")
ax1.set_title("Where the overspend sits, by spending type ($m)", fontsize=11)
ax1.set_yticks(y)
ax1.set_yticklabels(
    [f"{d} (${dept.loc[d, 'budget_k'] / 1000:.1f}m budget)" for d in order],
    fontsize=9,
)
ax1.invert_yaxis()
ax1.grid(axis="x", alpha=0.25)
ax1.set_axisbelow(True)
ax1.legend(loc="lower right", fontsize=8, framealpha=0.9, ncol=2)

# Right panel: variance relative to each department's own budget
pct = dept["variance_pct_total"].values
bar_colors = ["#C0392B" if v > 0 else "#2471A3" if v < 0 else "#7F8C8D"
              for v in pct]
ax2.barh(y, pct, height=0.62, color=bar_colors)
ax2.axvline(0, color="black", linewidth=0.9)
for i, val in enumerate(pct):
    ax2.text(val + (0.25 if val >= 0 else -0.25), i, f"{val:+.1f}%",
             fontsize=8, ha="left" if val >= 0 else "right", va="center")
ax2.set_xlim(-5.5, 12.5)
ax2.set_xlabel("% of department budget")
ax2.set_title("Overspend in context", fontsize=11)
ax2.grid(axis="x", alpha=0.25)
ax2.set_axisbelow(True)
ax2.tick_params(labelleft=False)

fig.suptitle(
    f"City forecast: ${city_var_m:.1f}m overspend on a ${city_budget_m:.1f}m budget "
    f"({city_pct:+.1f}%)",
    fontsize=14, fontweight="bold",
)
fig.text(
    0.5, 0.93,
    f"Transit alone is ${transit_var_m:.1f}m of the net overspend "
    f"({transit_share:.0f}%), driven mainly by overtime.",
    ha="center", fontsize=10,
)
fig.text(
    0.01, 0.01,
    "Diamonds = department net forecast variance ($m). Departments sorted by net variance. "
    "Hatched Roads bar is a scenario excluded from the forecast.",
    fontsize=8, color="#444444",
)

plt.tight_layout(rect=[0, 0.04, 1, 0.90])
