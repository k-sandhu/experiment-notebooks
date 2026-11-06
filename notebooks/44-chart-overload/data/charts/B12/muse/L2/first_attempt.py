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
hill_adj_reduction = (hill_base - hill_post_adj) / hill_base * 100
hill_raw_reduction = reduction.loc["Hillcrest"]

fig, ax = plt.subplots(figsize=(10, 6))

y = np.arange(len(reduction))
colours = ["#C1272D" if d == "Hillcrest" else "#B8B8B8" for d in reduction.index]
ax.barh(y, reduction.values, color=colours, height=0.62)

ax.set_yticks(y)
ax.set_yticklabels(reduction.index, fontsize=11)
ax.invert_yaxis()  # smallest cut (Hillcrest) at the top
for label in ax.get_yticklabels():
    if label.get_text() == "Hillcrest":
        label.set_color("#C1272D")
        label.set_weight("bold")

ax.set_xlim(0, 32)
ax.set_xticks([0, 10, 20, 30])
ax.set_xticklabels(["0%", "10%", "20%", "30%"], fontsize=10)
ax.set_xlabel("Cut in litres per household per day, Jun–Sep vs Apr–May", fontsize=11)
ax.xaxis.grid(True, colour="#E5E5E5", linewidth=0.8)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_colour("#999999")
ax.tick_params(left=False)

# Target
ax.axvline(20, color="#333333", linestyle="--", linewidth=1.4)
ax.text(20.4, len(reduction) - 0.55, "Target\n20% cut", fontsize=10,
        color="#333333", va="center", weight="bold")

# Hillcrest: adjusted marker and the only bar labels
y_hill = list(reduction.index).index("Hillcrest")
ax.plot(hill_adj_reduction, y_hill, marker="D", color="#7A0E14",
        markersize=7, clip_on=False, zorder=5)
ax.text(hill_adj_reduction + 0.7, y_hill,
        f"{hill_raw_reduction:.0f}% recorded  ·  ≈{hill_adj_reduction:.0f}% allowing for new meters",
        fontsize=11, color="#C1272D", weight="bold", va="center")

ax.set_title("Hillcrest alone missed the saving target by a wide margin —\nfocus enforcement there",
             loc="left", fontsize=17, weight="bold", pad=16)

fig.text(0.07, 0.02,
         "Note: Hillcrest meters replaced in July read ~8% higher; adjusted cut (◆) is still far short of 20%.",
         fontsize=9, color="#555555")

plt.tight_layout(rect=[0, 0.05, 1, 1])
