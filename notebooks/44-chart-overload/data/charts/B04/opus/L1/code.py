import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Department totals ($ millions)
dept = (df.groupby("department")
          .agg(budget=("annual_budget_k", "sum"),
               var=("variance_k", "sum"))
          .reset_index())
dept["var_m"] = dept["var"] / 1000
dept = dept.sort_values("var_m").reset_index(drop=True)  # largest overspend ends up at top
total_m = dept["var"].sum() / 1000

transit_ot_m = df.loc[(df.department == "Transit") & (df.budget_line == "Overtime"),
                      "variance_k"].sum() / 1000
transit_ot_budget = df.loc[(df.department == "Transit") & (df.budget_line == "Overtime"),
                           "annual_budget_k"].sum()
transit_ot_fc = df.loc[(df.department == "Transit") & (df.budget_line == "Overtime"),
                       "forecast_year_end_k"].sum()
transit_m = dept.loc[dept.department == "Transit", "var_m"].iloc[0]
transit_share = transit_m / total_m
roads_risk_m = 1.5  # harsh-winter snow clearing risk (analyst note)

fig, ax = plt.subplots(figsize=(10, 6))

RED_DARK = "#b2182b"
RED_LIGHT = "#ef8a62"
GREY = "#9e9e9e"
GREY_LIGHT = "#cfcfcf"

y = np.arange(len(dept))
for i, row in dept.iterrows():
    d, v = row["department"], row["var_m"]
    if d == "Transit":
        ax.barh(i, transit_ot_m, color=RED_DARK, height=0.7)
        ax.barh(i, v - transit_ot_m, left=transit_ot_m, color=RED_LIGHT, height=0.7)
        ax.text(transit_ot_m / 2, i, f"Overtime +${transit_ot_m:.1f}M",
                ha="center", va="center", color="white", fontsize=10, fontweight="bold")
        ax.text(v + 0.06, i + 0.12,
                f"+${v:.1f}M  ·  {transit_share:.0%} of city overspend",
                ha="left", va="center", fontsize=11, fontweight="bold", color=RED_DARK)
        ax.text(v + 0.06, i - 0.25,
                f"Overtime forecast {transit_ot_fc/transit_ot_budget:.1f}× its budget (driver vacancies)",
                ha="left", va="center", fontsize=9, color="#444444")
    elif d == "Roads":
        ax.barh(i, v, color=GREY, height=0.7)
        ax.barh(i, roads_risk_m, left=v, color="none", edgecolor=GREY,
                hatch="///", height=0.7, linewidth=0.8)
        ax.text(v + roads_risk_m + 0.06, i,
                f"+${v:.1f}M  (up to +${v + roads_risk_m:.1f}M if harsh winter)",
                ha="left", va="center", fontsize=9.5, color="#333333")
    else:
        color = GREY if v > 0 else GREY_LIGHT
        ax.barh(i, v, color=color, height=0.7)
        if v > 0:
            ax.text(v + 0.06, i, f"+${v:.1f}M", ha="left", va="center",
                    fontsize=9.5, color="#333333")
        elif v < 0:
            ax.text(v - 0.06, i, f"−${abs(v):.1f}M", ha="right", va="center",
                    fontsize=9.5, color="#666666")
        else:
            ax.text(0.06, i, "on budget", ha="left", va="center",
                    fontsize=9.5, color="#666666")

ax.set_yticks(y)
ax.set_yticklabels(dept["department"], fontsize=11)
for lbl in ax.get_yticklabels():
    if lbl.get_text() == "Transit":
        lbl.set_fontweight("bold")
        lbl.set_color(RED_DARK)

ax.axvline(0, color="#333333", linewidth=1)
ax.set_xlim(-1.0, 6.2)
ax.set_xlabel("Forecast year-end variance vs. budget ($ millions)   ← underspend | overspend →",
              fontsize=10, color="#444444")
ax.tick_params(axis="x", colors="#666666")
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#999999")
ax.tick_params(axis="y", length=0)
ax.grid(axis="x", color="#eeeeee", zorder=0)
ax.set_axisbelow(True)

fig.suptitle("Review Transit: it drives most of the city's forecast overspend",
             x=0.02, ha="left", fontsize=16, fontweight="bold", y=0.97)
ax.set_title(f"Forecast overspend by department, full year. City total: +${total_m:.1f}M. "
             f"Even with a harsh winter, Roads stays below Transit.",
             loc="left", fontsize=10.5, color="#444444", pad=10)

fig.text(0.02, 0.015,
         "Source: City of Marlow budget monitoring, January–July (7 of 12 months). "
         "Positive = forecast above approved budget.",
         fontsize=8.5, color="#777777", ha="left")

fig.tight_layout(rect=[0, 0.03, 1, 0.93])
