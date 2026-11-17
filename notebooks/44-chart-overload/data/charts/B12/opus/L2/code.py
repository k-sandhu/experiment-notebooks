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
LIGHT = "#e8a198"
GREY = "#b5b5b5"

fig, ax = plt.subplots(figsize=(10, 6))

for i, d in enumerate(order):
    if d == "Hillcrest":
        ax.barh(i, cut[d], color=HIGHLIGHT, height=0.65)
        ax.barh(i, cut_adj[d] - cut[d], left=cut[d], color=LIGHT,
                height=0.65, hatch="///", edgecolor=HIGHLIGHT, linewidth=0)
        ax.text(cut_adj[d] + 0.6, i,
                f"{cut[d]:.0f}% as metered, about {cut_adj[d]:.0f}% after correcting for new meters",
                va="center", ha="left", fontsize=11, color=HIGHLIGHT, fontweight="bold")
    else:
        ax.barh(i, cut[d], color=GREY, height=0.65)

# Target line
ax.axvline(20, color="#333333", linestyle="--", linewidth=1.3)
ax.text(20.3, len(order) - 0.45, "20% target", fontsize=10.5, color="#333333",
        va="center", ha="left")

ax.set_yticks(y)
ax.set_yticklabels(order, fontsize=11)
for lbl in ax.get_yticklabels():
    if lbl.get_text() == "Hillcrest":
        lbl.set_color(HIGHLIGHT)
        lbl.set_fontweight("bold")

ax.set_xlim(0, 32)
ax.set_xlabel("Cut in average litres per household per day, Jun–Sep vs Apr–May (%)",
              fontsize=10.5)
ax.xaxis.grid(True, color="#e5e5e5", linewidth=0.8)
ax.set_axisbelow(True)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0)

fig.suptitle("Hillcrest is the only district far short of its 20% cut: focus enforcement there",
             fontsize=14.5, fontweight="bold", x=0.02, ha="left", y=0.97)
ax.set_title("Hillcrest households still use about 390–414 litres a day against a 342-litre target; "
             "the other seven districts are at or near 20%",
             fontsize=10.5, color="#555555", loc="left", pad=12)

fig.text(0.02, 0.02,
         "Note: Hillcrest's meters were replaced in July and the new meters read about 8% higher. "
         "Even after correcting for this, Hillcrest's cut is only about 9%.",
         fontsize=9, color="#555555", ha="left")

fig.subplots_adjust(left=0.13, right=0.97, top=0.85, bottom=0.17)
