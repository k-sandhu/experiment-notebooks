import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Forecast variance (forecast minus budget) by department, in $ millions
dept = (df.groupby("department", as_index=False)[["annual_budget_k", "variance_k"]]
          .sum())
dept["var_m"] = dept["variance_k"] / 1000
dept = dept.sort_values("var_m").reset_index(drop=True)   # largest overspend at the top

total_var_m = dept["var_m"].sum()
transit_m = dept.loc[dept["department"] == "Transit", "var_m"].iloc[0]
roads_m = dept.loc[dept["department"] == "Roads", "var_m"].iloc[0]
transit_ot_m = df.loc[(df["department"] == "Transit") & (df["budget_line"] == "Overtime"),
                      "variance_k"].iloc[0] / 1000
share = transit_m / total_var_m

HIGHLIGHT = "#C0392B"
GREY = "#BDBDBD"
colors = [HIGHLIGHT if d == "Transit" else GREY for d in dept["department"]]

fig, ax = plt.subplots(figsize=(10, 6))
n = len(dept)
y = range(n)
ax.barh(y, dept["var_m"], color=colors, height=0.65, zorder=2)

# Zero line
ax.axvline(0, color="#555555", linewidth=1, zorder=3)

# Department labels
ax.set_yticks(list(y))
ax.set_yticklabels(dept["department"], fontsize=11)
for lbl in ax.get_yticklabels():
    if lbl.get_text() == "Transit":
        lbl.set_color(HIGHLIGHT)
        lbl.set_fontweight("bold")

# Transit label: the number that matters
t_idx = dept.index[dept["department"] == "Transit"][0]
ax.text(transit_m + 0.06, t_idx,
        f"+\\${transit_m:.1f}M  (\\${transit_ot_m:.1f}M is driver overtime)",
        va="center", ha="left", fontsize=11, color=HIGHLIGHT, fontweight="bold")

# Roads caveat: a harsh winter could add up to $1.5M (still below Transit)
r_idx = dept.index[dept["department"] == "Roads"][0]
winter_extra = 1.5
ax.barh(r_idx, winter_extra, left=roads_m, height=0.65, fill=False,
        edgecolor="#888888", linestyle="--", linewidth=1, zorder=2)
ax.text(roads_m + winter_extra + 0.06, r_idx,
        f"+\\${roads_m:.1f}M; up to +\\${roads_m + winter_extra:.1f}M in a harsh winter",
        va="center", ha="left", fontsize=9.5, color="#666666")

# Direction hints above the bars, either side of zero
top_y = n - 0.35
ax.text(-0.06, top_y, "← under budget", fontsize=9, color="#888888", ha="right", va="center")
ax.text(0.06, top_y, "over budget →", fontsize=9, color="#888888", ha="left", va="center")

# Axes styling
ax.set_xlim(-0.95, 5.6)
ax.set_ylim(-0.6, n + 0.1)
ax.set_xticks([0, 1, 2, 3, 4, 5])
ax.set_xlabel("Forecast year-end spending minus approved budget (\\$ millions)", fontsize=10)
ax.xaxis.grid(True, color="#EEEEEE", zorder=0)
for side in ["top", "right", "left"]:
    ax.spines[side].set_visible(False)
ax.tick_params(axis="y", length=0)

# Title states the message and the decision
fig.suptitle(f"Review Transit: it drives {share:.0%} of the city's "
             f"\\${total_var_m:.1f}M forecast overspend",
             x=0.02, ha="left", fontsize=16, fontweight="bold")
ax.set_title("Forecast full-year overspend by department, City of Marlow "
             "(based on January–July spending)",
             loc="left", fontsize=10.5, color="#555555", pad=10)

fig.tight_layout(rect=[0, 0, 1, 0.95])
