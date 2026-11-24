import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")
df["month"] = df["month"].astype(str)

before = df[df["month"].isin(["2026-04", "2026-05"])]
after = df[df["month"].isin(["2026-06", "2026-07", "2026-08", "2026-09"])].copy()

base = before.groupby("district")["litres_per_household_day"].mean()
post = after.groupby("district")["litres_per_household_day"].mean()
cut = (1 - post / base) * 100

# Hillcrest: new meters fitted in July read about 8% high, so scale Jul-Sep down
hc = after[after["district"] == "Hillcrest"].copy()
hc_adj = np.where(hc["month"] >= "2026-07",
                  hc["litres_per_household_day"] / 1.08,
                  hc["litres_per_household_day"])
hc_cut_adj = (1 - hc_adj.mean() / base["Hillcrest"]) * 100

order = cut.sort_values().index.tolist()
vals = cut[order].values
y = np.arange(len(order))

fig, ax = plt.subplots(figsize=(10, 6))

grey = "#9aa5b1"
red = "#c0392b"
colors = [red if d == "Hillcrest" else grey for d in order]

# Adjusted Hillcrest bar behind the recorded value
hi = order.index("Hillcrest")
ax.barh(hi, hc_cut_adj, color="none", edgecolor=red, hatch="///",
        linewidth=1.2, height=0.6, zorder=2)
ax.barh(y, vals, color=colors, height=0.6, zorder=3)

# 20% target line
ax.axvline(20, color="#333333", linestyle="--", linewidth=1.3, zorder=4)
ax.text(20.3, len(order) - 0.45, "20% reduction target", va="bottom",
        ha="left", fontsize=10, color="#333333")

# Value labels
for yi, d, v in zip(y, order, vals):
    if d == "Hillcrest":
        ax.text(v + 0.3, yi, f"{v:.0f}% recorded", va="center",
                fontsize=10, color=red, fontweight="bold", zorder=5)
        ax.text(hc_cut_adj + 0.4, yi,
                f"{hc_cut_adj:.0f}% allowing for new meters\n(fitted July, read ~8% high)",
                va="center", fontsize=9, color=red)
    else:
        ax.text(v + 0.3, yi, f"{v:.0f}%", va="center", fontsize=10,
                color="#333333")

ax.set_yticks(y)
ax.set_yticklabels(order, fontsize=11)
for lbl in ax.get_yticklabels():
    if lbl.get_text() == "Hillcrest":
        lbl.set_color(red)
        lbl.set_fontweight("bold")

ax.set_xlim(0, 32)
ax.set_xlabel("Reduction in litres per household per day, Jun–Sep vs Apr–May (%)",
              fontsize=10)
ax.set_title("Hillcrest cut water use far less than other districts after restrictions",
             fontsize=14, loc="left", pad=22)
ax.text(0, 1.02,
        "Change in average daily use per household after restrictions began on 1 June 2026",
        transform=ax.transAxes, fontsize=10, color="#555555")

ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", color="#e5e5e5", zorder=0)
ax.set_axisbelow(True)

fig.tight_layout()
