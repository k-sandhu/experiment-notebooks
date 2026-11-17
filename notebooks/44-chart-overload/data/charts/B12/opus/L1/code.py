import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Hillcrest's new meters (fitted July) read ~8% high, so correct July onward
df["lphd_adj"] = df["litres_per_household_day"].astype(float)
mask = (df["district"] == "Hillcrest") & (df["month"] >= "2026-07")
df.loc[mask, "lphd_adj"] = df.loc[mask, "litres_per_household_day"] / 1.08

pre = df[df["month"].isin(["2026-04", "2026-05"])].groupby("district")["litres_per_household_day"].mean()
post_raw = df[df["month"] >= "2026-06"].groupby("district")["litres_per_household_day"].mean()
post_adj = df[df["month"] >= "2026-06"].groupby("district")["lphd_adj"].mean()

cut = ((pre - post_adj) / pre * 100).sort_values(ascending=False)  # largest cut at bottom
cut_raw_hill = (pre["Hillcrest"] - post_raw["Hillcrest"]) / pre["Hillcrest"] * 100

fig, ax = plt.subplots(figsize=(10, 6))

colors = ["#d62728" if d == "Hillcrest" else "#b0b0b0" for d in cut.index]
y = np.arange(len(cut))
ax.barh(y, cut.values, color=colors, height=0.65)

# 20% target line
ax.axvline(20, color="#333333", linestyle="--", linewidth=1.5)
ax.text(20.3, len(cut) - 0.35, "Target: 20% cut", fontsize=11, color="#333333",
        va="bottom", ha="left")

# Value labels
for yi, (d, v) in zip(y, cut.items()):
    weight = "bold" if d == "Hillcrest" else "normal"
    col = "#d62728" if d == "Hillcrest" else "#444444"
    ax.text(v + 0.4, yi, f"{v:.0f}%", va="center", fontsize=12, fontweight=weight, color=col)

# Hillcrest note
hy = list(cut.index).index("Hillcrest")
ax.text(cut["Hillcrest"] + 3.5, hy,
        f"Only {cut_raw_hill:.0f}% as metered; ~{cut['Hillcrest']:.0f}% after allowing for\n"
        "new meters (fitted July) reading ~8% high",
        va="center", fontsize=10, color="#d62728")

ax.set_yticks(y)
ax.set_yticklabels(cut.index, fontsize=12)
for lbl in ax.get_yticklabels():
    if lbl.get_text() == "Hillcrest":
        lbl.set_color("#d62728")
        lbl.set_fontweight("bold")

ax.set_xlim(0, 32)
ax.set_xlabel("Cut in average daily water use per household, Jun–Sep vs Apr–May (%)", fontsize=11)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))

ax.set_title("Hillcrest is the only district far short of the 20% target —\n"
             "focus enforcement there if restrictions are extended",
             fontsize=15, fontweight="bold", loc="left")

for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0)

fig.text(0.01, 0.01,
         "Other districts cut use by 17–27%. Restrictions began 1 June 2026. "
         "Source: Clearwater Valley district water data, Apr–Sep 2026.",
         fontsize=9, color="#666666")

fig.tight_layout(rect=[0, 0.03, 1, 1])
