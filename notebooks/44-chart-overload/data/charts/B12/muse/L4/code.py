import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

baseline = (
    df[df["month"].isin(["2026-04", "2026-05"])]
    .groupby("district")["litres_per_household_day"].mean()
)
post = (
    df[df["month"] >= "2026-06"]
    .groupby("district")["litres_per_household_day"].mean()
)
reduction = ((baseline - post) / baseline * 100).sort_values()

# Hillcrest adjusted for meters replaced in July reading ~8% higher
hill = df[df["district"] == "Hillcrest"].copy()
hill["adj_lphd"] = np.where(
    hill["month"] >= "2026-07",
    hill["litres_per_household_day"] / 1.08,
    hill["litres_per_household_day"],
)
hill_base = hill[hill["month"].isin(["2026-04", "2026-05"])]["adj_lphd"].mean()
hill_post_adj = hill[hill["month"] >= "2026-06"]["adj_lphd"].mean()
hill_adj = (hill_base - hill_post_adj) / hill_base * 100
hill_raw = reduction.loc["Hillcrest"]

others = reduction.drop("Hillcrest")

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.15, right=0.97, top=0.81, bottom=0.14)

# Hillcrest at the top, visually separated from the other districts
districts = list(reduction.index)
y = np.array([0.0] + [1.35 + i for i in range(len(districts) - 1)])
colours = ["#C1272D" if d == "Hillcrest" else "#B8B8B8" for d in districts]
ax.barh(y, reduction.values, color=colours, height=0.62)

# Pale extension from recorded to meter-adjusted Hillcrest cut
y_hill = y[districts.index("Hillcrest")]
ax.barh(y_hill, hill_adj - hill_raw, left=hill_raw,
        color="#E8AFAF", height=0.62)
ax.plot(hill_adj, y_hill, marker="D", color="#7A0E14",
        markersize=7, clip_on=False, zorder=5)

ax.set_yticks(y)
ax.set_yticklabels(districts, fontsize=12)
for label in ax.get_yticklabels():
    if label.get_text() == "Hillcrest":
        label.set_color("#C1272D")
        label.set_weight("bold")

ax.set_ylim(y[-1] + 0.65, -1.15)  # Hillcrest at top; headroom for target label
ax.set_xlim(0, 30)
ax.set_xticks([0, 10, 20, 30])
ax.set_xticklabels(["0%", "10%", "20%", "30%"], fontsize=11)
ax.set_xlabel("Cut in litres per household per day, Jun–Sep vs Apr–May", fontsize=11)
ax.xaxis.grid(True, color="#E5E5E5", linewidth=0.8)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color("#999999")
ax.tick_params(left=False)

# Target: label sits in the empty headroom, never over a bar
ax.axvline(20, color="#333333", linestyle="--", linewidth=1.4, zorder=4)
ax.text(20, -0.88, "Target  20% cut", fontsize=11, color="#333333",
        weight="bold", ha="center", va="center",
        bbox=dict(facecolor="white", edgecolor="none", pad=2.5), zorder=6)

# The only numbers on the bars: Hillcrest, kept clear of the target line
ax.text(hill_adj + 0.8, y_hill,
        f"{hill_raw:.0f}% recorded\n"
        f"≈{hill_adj:.0f}% adjusted — still far short",
        fontsize=11.5, color="#C1272D", weight="bold", va="center", linespacing=1.35)

fig.text(0.15, 0.97,
         "Hillcrest is far behind every other district —\nfocus enforcement there",
         fontsize=18, weight="bold", va="top", ha="left")
fig.text(0.15, 0.855,
         f"Other districts cut use by {others.min():.0f}–{others.max():.0f}% under restrictions.",
         fontsize=12, color="#444444", va="top", ha="left")

fig.text(0.15, 0.02,
         "Note: Hillcrest meters replaced in July read ~8% higher. Pale segment and ◆ show the cut after allowing for this.",
         fontsize=9, color="#555555")
