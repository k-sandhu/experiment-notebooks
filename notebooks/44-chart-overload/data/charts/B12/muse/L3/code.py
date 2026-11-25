import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

baseline = df[df["month"].isin(["2026-04", "2026-05"])]
restricted = df[df["month"] >= "2026-06"]

summary = pd.DataFrame({
    "baseline": baseline.groupby("district")["litres_per_household_day"].mean(),
    "restricted": restricted.groupby("district")["litres_per_household_day"].mean(),
    "target": baseline.groupby("district")["target_lphd"].first(),
})
summary["cut_pct"] = (1 - summary["restricted"] / summary["baseline"]) * 100
summary = summary.sort_values("cut_pct")

# Hillcrest adjustment: Jul-Sep readings ~8% higher after meter replacement
hc = restricted[restricted["district"] == "Hillcrest"].copy()
hc["adj"] = np.where(hc["month"] >= "2026-07",
                     hc["litres_per_household_day"] / 1.08,
                     hc["litres_per_household_day"])
hc_adj_cut = (1 - hc["adj"].mean() / summary.loc["Hillcrest", "baseline"]) * 100
hc_cut = summary.loc["Hillcrest", "cut_pct"]
hc_use = summary.loc["Hillcrest", "restricted"]
hc_target = summary.loc["Hillcrest", "target"]

STRONG = "#C0272D"
GREY = "#B5B5B5"

fig, ax = plt.subplots(figsize=(10, 6))

colors = [STRONG if d == "Hillcrest" else GREY for d in summary.index]
ax.barh(summary.index, summary["cut_pct"], color=colors, height=0.62, zorder=3)

# 20% target line
ax.axvline(20, color="#222222", linewidth=1.6, linestyle="--", zorder=4)
ax.text(20, len(summary) - 0.25, "  Target: 20% cut",
        fontsize=11, fontweight="bold", va="bottom", ha="left")

# Hillcrest adjusted marker
hc_y = list(summary.index).index("Hillcrest")
ax.plot([hc_cut, hc_adj_cut], [hc_y, hc_y], color=STRONG,
        linewidth=2.5, linestyle=":", zorder=5)
ax.plot(hc_adj_cut, hc_y, marker="|", markersize=18,
        markeredgewidth=2.5, color=STRONG, zorder=5)

# Number labels only where they carry the message
ax.text(hc_adj_cut + 0.6, hc_y + 0.18,
        f"Hillcrest: only {hc_cut:.0f}% cut  (≈{hc_adj_cut:.0f}% adjusted for new meters)",
        fontsize=11.5, fontweight="bold", color=STRONG, va="bottom")
ax.text(hc_adj_cut + 0.6, hc_y - 0.22,
        f"{hc_use:.0f} litres/household/day Jun–Sep vs target {hc_target:.0f}",
        fontsize=11, color=STRONG, va="top")

ax.text(28.2, len(summary) - 3.2, "Other seven districts:\n17–27% cuts",
        fontsize=11, color="#555555", va="center", ha="left")

ax.set_xlim(0, 31)
ax.set_xlabel("Reduction in use per household, Jun–Sep vs Apr–May (%)", fontsize=11)
ax.set_ylabel("")
ax.tick_params(axis="y", labelsize=11.5, length=0)
ax.tick_params(axis="x", labelsize=10)
for label in ax.get_yticklabels():
    if label.get_text() == "Hillcrest":
        label.set_fontweight("bold")
        label.set_color(STRONG)

ax.xaxis.grid(True, color="#E5E5E5", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color("#999999")

fig.suptitle("Hillcrest is the only district far from its target — focus enforcement there",
             fontsize=16, fontweight="bold", x=0.07, ha="left")
fig.text(0.07, 0.91, "Change in litres per household per day after restrictions began on 1 June",
         fontsize=11.5, color="#444444", ha="left")
fig.text(0.07, 0.02,
         "Caveat: Hillcrest meters replaced in July read ~8% higher. Dashed marker allows for this — its cut is still well short of 20%.",
         fontsize=9, color="#666666", ha="left")

plt.tight_layout(rect=[0, 0.04, 1, 0.88])
