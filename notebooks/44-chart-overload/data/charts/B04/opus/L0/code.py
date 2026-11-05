import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Department-level net forecast variance ($M)
dept = (df.groupby("department")[["annual_budget_k", "variance_k"]]
          .sum()
          .sort_values("variance_k"))
var_m = dept["variance_k"] / 1000
total_m = var_m.sum()

transit_m = var_m["Transit"]
transit_share = transit_m / total_m
transit_ot_m = df.query("department == 'Transit' and budget_line == 'Overtime'")["variance_k"].sum() / 1000
transit_ot_budget_m = df.query("department == 'Transit' and budget_line == 'Overtime'")["annual_budget_k"].sum() / 1000

# Colors: Transit highlighted, other overspends muted, underspends a separate muted tone
colors = []
for d, v in var_m.items():
    if d == "Transit":
        colors.append("#c0392b")
    elif v > 0:
        colors.append("#e6a59c")
    elif v < 0:
        colors.append("#8fb3d1")
    else:
        colors.append("#bbbbbb")

fig, ax = plt.subplots(figsize=(10, 6))
y = np.arange(len(var_m))
bars = ax.barh(y, var_m.values, color=colors, height=0.65, zorder=2)

# Roads winter risk: possible additional overspend (dashed outline)
roads_idx = list(var_m.index).index("Roads")
ax.barh(roads_idx, 1.5, left=var_m["Roads"], height=0.65, fill=False,
        edgecolor="#7f8c8d", linestyle="--", linewidth=1.2, zorder=2)
ax.text(var_m["Roads"] + 1.5 + 0.05, roads_idx,
        "harsh winter could add up to $1.5M",
        va="center", ha="left", fontsize=9, color="#555555")

# Value labels
for yi, v, d in zip(y, var_m.values, var_m.index):
    if d == "Roads":
        continue  # label placed inside to avoid clashing with risk note
    label = f"{v:+.1f}" if v != 0 else "0.0"
    if v >= 0:
        ax.text(v + 0.05, yi, label, va="center", ha="left", fontsize=10,
                fontweight="bold" if d == "Transit" else "normal")
    else:
        ax.text(v - 0.05, yi, label, va="center", ha="right", fontsize=10)
ax.text(var_m["Roads"] / 2, roads_idx, f"{var_m['Roads']:+.1f}",
        va="center", ha="center", fontsize=10, color="#333333")

# Transit annotation
t_idx = list(var_m.index).index("Transit")
ax.annotate(f"${transit_ot_m:.1f}M of this is overtime:\n"
            f"+{transit_ot_m / transit_ot_budget_m:.0%} over a ${transit_ot_budget_m:.1f}M budget,\n"
            "extra shifts covering driver vacancies",
            xy=(transit_m, t_idx), xytext=(transit_m - 0.2, t_idx - 2.6),
            ha="right", va="center", fontsize=9, color="#7b241c",
            arrowprops=dict(arrowstyle="-", color="#7b241c", lw=0.8))

ax.axvline(0, color="#333333", linewidth=0.8, zorder=3)
ax.set_yticks(y)
ax.set_yticklabels(var_m.index, fontsize=10)
ax.set_xlabel("Forecast year-end variance vs. budget ($ millions; positive = overspend)")
ax.set_xlim(-1.0, 4.0)
ax.grid(axis="x", color="#e5e5e5", zorder=0)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)

ax.set_title(f"Transit accounts for {transit_share:.0%} of the city's "
             f"${total_m:.1f}M forecast overspend",
             fontsize=14, fontweight="bold", loc="left")
ax.text(0, 1.02,
        "Forecast year-end spending minus approved budget, by department",
        transform=ax.transAxes, fontsize=10, color="#555555")

fig.text(0.01, 0.01,
         "Variance = forecast year-end spending − approved annual budget, summed across budget lines. "
         "Roads forecast assumes snow clearing at the 5-year average.",
         fontsize=8, color="#777777")

fig.tight_layout(rect=(0, 0.03, 1, 1))
