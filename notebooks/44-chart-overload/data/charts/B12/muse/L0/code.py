import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

df = pd.read_csv("data.csv", parse_dates=["month"])
df = df.sort_values(["district", "month"])

restriction_start = pd.Timestamp("2026-06-01")
meter_change = pd.Timestamp("2026-07-01")

# Baseline (Apr-May) and restriction period (Jun-Sep)
baseline = (
    df[df["month"] < restriction_start]
    .groupby("district")["litres_per_household_day"]
    .mean()
)
post = (
    df[df["month"] >= restriction_start]
    .groupby("district")["litres_per_household_day"]
    .mean()
)

summary = pd.DataFrame({"baseline": baseline, "post": post})
summary["pct_cut"] = (1 - summary["post"] / summary["baseline"]) * 100

# Hillcrest adjustment: meters replaced in July read ~8% higher
adj = df.copy()
mask = (adj["district"] == "Hillcrest") & (adj["month"] >= meter_change)
adj.loc[mask, "litres_per_household_day"] /= 1.08
hill_adj_post = adj[
    (adj["district"] == "Hillcrest") & (adj["month"] >= restriction_start)
]["litres_per_household_day"].mean()
hill_adj_cut = (1 - hill_adj_post / summary.loc["Hillcrest", "baseline"]) * 100

hill_target = df.loc[df["district"] == "Hillcrest", "target_lphd"].iloc[0]
hill_post = summary.loc["Hillcrest", "post"]

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.35, 1.0], "wspace": 0.32}
)

# ---- Panel 1: trend over time ----
for district, g in df.groupby("district"):
    if district == "Hillcrest":
        ax1.plot(
            g["month"], g["litres_per_household_day"],
            color="#C1272D", lw=3, marker="o", ms=4, zorder=5,
        )
    else:
        ax1.plot(
            g["month"], g["litres_per_household_day"],
            color="#8A97A8", lw=1.3, marker="o", ms=3, alpha=0.85, zorder=2,
        )

ax1.axvline(restriction_start, color="black", lw=1, ls="--")
ax1.text(
    restriction_start + pd.Timedelta(days=2), 455,
    "Restrictions\nbegin 1 June", fontsize=8, va="top",
)

# Direct labels for the extremes only (other lines are a bundle)
hill = df[df["district"] == "Hillcrest"]
ax1.annotate(
    f"Hillcrest\n{hill_post:.0f} L/day Jun–Sep\n(target {hill_target:.0f})",
    xy=(hill["month"].iloc[-1], hill["litres_per_household_day"].iloc[-1]),
    xytext=(8, 6), textcoords="offset points",
    color="#C1272D", fontsize=8, fontweight="bold", va="center",
)

orch = df[df["district"] == "Orchard"]
ax1.annotate(
    f"Orchard (lowest)\n{summary.loc['Orchard', 'post']:.0f} L/day Jun–Sep",
    xy=(orch["month"].iloc[-1], orch["litres_per_household_day"].iloc[-1]),
    xytext=(8, -4), textcoords="offset points",
    color="#44546A", fontsize=8, va="center",
)

ax1.set_xlim(pd.Timestamp("2026-03-25"), pd.Timestamp("2026-10-20"))
ax1.set_ylim(180, 470)
ax1.set_ylabel("Litres per household per day")
ax1.set_title("Use dropped in June — except in Hillcrest", fontsize=11, fontweight="bold", loc="left")
ax1.xaxis.set_major_locator(mdates.MonthLocator())
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
ax1.grid(axis="y", alpha=0.25)
ax1.spines[["top", "right"]].set_visible(False)
ax1.legend(
    handles=[
        Line2D([0], [0], color="#C1272D", lw=3, label="Hillcrest"),
        Line2D([0], [0], color="#8A97A8", lw=1.3, label="Other 7 districts"),
    ],
    frameon=False, fontsize=8, loc="lower left",
)

# ---- Panel 2: % cut vs 20% target ----
plot_data = summary.sort_values("pct_cut", ascending=True)
colors = ["#C1272D" if d == "Hillcrest" else "#2E6F8E" for d in plot_data.index]

bars = ax2.barh(plot_data.index, plot_data["pct_cut"], color=colors, height=0.62)
ax2.axvline(20, color="black", lw=1.2, ls="--")
ax2.text(20.4, len(plot_data) - 0.4, "20% target", fontsize=8, va="center")

for bar, val in zip(bars, plot_data["pct_cut"]):
    ax2.text(val + 0.5, bar.get_y() + bar.get_height() / 2,
             f"{val:.0f}%", va="center", fontsize=8)

# Meter-adjusted Hillcrest marker
hill_y = list(plot_data.index).index("Hillcrest")
ax2.scatter(
    [hill_adj_cut], [hill_y], marker="D", s=55,
    facecolor="white", edgecolor="#C1272D", lw=1.5, zorder=5,
)
ax2.annotate(
    f"{hill_adj_cut:.0f}% after meter\nadjustment",
    xy=(hill_adj_cut, hill_y), xytext=(hill_adj_cut + 2, hill_y - 0.75),
    fontsize=7.5, color="#C1272D",
    arrowprops=dict(arrowstyle="-", color="#C1272D", lw=0.8),
)

ax2.set_xlim(0, 33)
ax2.set_xlabel("Reduction, Jun–Sep vs Apr–May (%)")
ax2.set_title("Cut achieved under restrictions", fontsize=11, fontweight="bold", loc="left")
ax2.grid(axis="x", alpha=0.25)
ax2.set_axisbelow(True)
ax2.spines[["top", "right"]].set_visible(False)

fig.suptitle(
    "Restrictions worked almost everywhere — Hillcrest barely cut use",
    fontsize=15, fontweight="bold", x=0.01, ha="left",
)
fig.text(
    0.01, 0.03,
    "Hillcrest meters were replaced in July and read ~8% higher; the diamond divides Jul–Sep readings by 1.08. "
    "Even adjusted, Hillcrest is well short of the 20% target.",
    fontsize=8, color="#444444",
)

plt.tight_layout(rect=[0, 0.06, 1, 0.93])
