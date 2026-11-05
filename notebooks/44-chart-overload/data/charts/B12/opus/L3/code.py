import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")
df["month"] = df["month"].astype(str)

pre_months = ["2026-04", "2026-05"]
post_months = ["2026-06", "2026-07", "2026-08", "2026-09"]

pre = df[df["month"].isin(pre_months)].groupby("district")["litres_per_household_day"].mean()
post = df[df["month"].isin(post_months)].groupby("district")["litres_per_household_day"].mean()
cut = ((1 - post / pre) * 100).sort_values()

# Hillcrest adjusted for new meters (from July) reading ~8% high
h = df[(df["district"] == "Hillcrest") & df["month"].isin(post_months)].copy()
h.loc[h["month"] >= "2026-07", "litres_per_household_day"] /= 1.08
h_adj_cut = (1 - h["litres_per_household_day"].mean() / pre["Hillcrest"]) * 100
h_post = post["Hillcrest"]
h_target = df.loc[df["district"] == "Hillcrest", "target_lphd"].iloc[0]

HIGHLIGHT = "#c0392b"
GREY = "#b8b8b8"

fig, ax = plt.subplots(figsize=(10, 6))

districts = list(cut.index)
y = range(len(districts))
colors = [HIGHLIGHT if d == "Hillcrest" else GREY for d in districts]
ax.barh(y, cut.values, color=colors, height=0.65, zorder=2)

# Adjusted Hillcrest cut shown as an outlined extension
hi = districts.index("Hillcrest")
ax.barh(hi, h_adj_cut, height=0.65, facecolor="none", edgecolor=HIGHLIGHT,
        linestyle="--", linewidth=1.5, zorder=3)

# Target line
ax.axvline(20, color="#333333", linestyle=":", linewidth=1.5, zorder=4)
ax.text(20.3, len(districts) - 0.45, "Target: 20% cut", fontsize=10,
        color="#333333", va="bottom", ha="left")

# Hillcrest labels
ax.text(cut["Hillcrest"] - 0.3, hi, f"{cut['Hillcrest']:.0f}%", va="center", ha="right",
        color="white", fontsize=11, fontweight="bold", zorder=5)
ax.text(h_adj_cut + 0.4, hi,
        f"~{h_adj_cut:.0f}% allowing for new meters\n"
        f"{h_post:.0f} L/day vs target {h_target} L/day",
        va="center", ha="left", color=HIGHLIGHT, fontsize=10.5, zorder=5)

ax.set_yticks(list(y))
ax.set_yticklabels(districts, fontsize=11)
for lbl in ax.get_yticklabels():
    if lbl.get_text() == "Hillcrest":
        lbl.set_color(HIGHLIGHT)
        lbl.set_fontweight("bold")

ax.set_xlim(0, 30)
ax.set_xlabel("Cut in litres per household per day, Jun–Sep vs Apr–May (%)", fontsize=10.5)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.grid(axis="x", color="#eeeeee", zorder=0)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0)

fig.suptitle("Hillcrest is the outlier: it cut water use by only 4%,\n"
             "while the other seven districts cut 17–27%",
             x=0.02, ha="left", fontsize=15, fontweight="bold", y=0.97)

fig.text(0.02, 0.025,
         "Note: Hillcrest's meters were replaced in July and read ~8% higher than the old ones. "
         "Even allowing for this, its cut is ~9%, well short of 20%.",
         fontsize=9, color="#555555", ha="left")

fig.subplots_adjust(left=0.13, right=0.97, top=0.84, bottom=0.17)
