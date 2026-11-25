import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")
df["month"] = pd.to_datetime(df["month"])

before = df[df["month"].dt.month.isin([4, 5])]
after = df[df["month"].dt.month.isin([6, 7, 8, 9])].copy()

# Hillcrest's new meters (fitted in July) read about 8% high, so correct Jul-Sep readings
after["lphd_adj"] = after["litres_per_household_day"]
mask = (after["district"] == "Hillcrest") & (after["month"].dt.month >= 7)
after.loc[mask, "lphd_adj"] = after.loc[mask, "litres_per_household_day"] / 1.08

base = before.groupby("district")["litres_per_household_day"].mean()
restr = after.groupby("district")["litres_per_household_day"].mean()
restr_adj = after.groupby("district")["lphd_adj"].mean()

cut = (1 - restr / base) * 100
cut_adj = (1 - restr_adj / base) * 100

order = cut_adj.sort_values().index.tolist()  # Hillcrest ends up at the bottom
y = np.arange(len(order))

HIGHLIGHT = "#c0392b"
GREY = "#bdbdbd"

fig, ax = plt.subplots(figsize=(10, 6))

for i, d in enumerate(order):
    color = HIGHLIGHT if d == "Hillcrest" else GREY
    ax.barh(i, cut_adj[d], color=color, height=0.65, zorder=2)

# Target line
ax.axvline(20, color="#333333", linestyle="--", linewidth=1.3, zorder=3)
ax.text(20.3, len(order) - 0.45, "20% target", fontsize=10.5, color="#333333",
        va="center", ha="left")

# Direct label on Hillcrest, with the meter caveat right where it matters
hi = order.index("Hillcrest")
x0 = cut_adj["Hillcrest"] + 0.6
box = dict(facecolor="white", edgecolor="none", pad=1.5)
ax.text(x0, hi + 0.15, f"About {cut_adj['Hillcrest']:.0f}% cut, less than half the target",
        va="center", ha="left", fontsize=11.5, color=HIGHLIGHT, fontweight="bold",
        bbox=box, zorder=4)
ax.text(x0, hi - 0.22,
        f"Corrected for new meters fitted in July that read ~8% high "
        f"({cut['Hillcrest']:.0f}% as metered)",
        va="center", ha="left", fontsize=9.5, color="#555555", bbox=box, zorder=4)

ax.set_yticks(y)
ax.set_yticklabels(order, fontsize=11)
for lbl in ax.get_yticklabels():
    if lbl.get_text() == "Hillcrest":
        lbl.set_color(HIGHLIGHT)
        lbl.set_fontweight("bold")

ax.set_xlim(0, 32)
ax.set_xticks([0, 5, 10, 15, 20, 25, 30])
ax.set_xticklabels([f"{v}%" for v in [0, 5, 10, 15, 20, 25, 30]])
ax.set_xlabel("Cut in average litres per household per day (%)", fontsize=10.5)
ax.xaxis.grid(True, color="#e8e8e8", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0)

fig.suptitle("Hillcrest is the only district far short of its 20% cut: focus enforcement there",
             fontsize=14.5, fontweight="bold", x=0.02, ha="left", y=0.965)
fig.text(0.02, 0.895,
         "Change in water use per household, Jun–Sep (restrictions) vs Apr–May. "
         "Hillcrest still uses ~390 litres a day vs a 342-litre target.",
         fontsize=10.5, color="#555555", ha="left")

fig.subplots_adjust(left=0.13, right=0.97, top=0.85, bottom=0.11)
