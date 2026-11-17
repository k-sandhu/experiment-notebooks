import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")
df["late"] = df["late"].astype(str).str.lower() == "true"

COLD_LIMIT = 48
order = ["Swiftline", "Northway", "ParcelPro"]

g = df.groupby("courier")
n = g.size().reindex(order)
over = g["actual_hours"].apply(lambda s: (s > COLD_LIMIT).sum()).reindex(order)
pct_over = 100 * over / n
median_h = g["actual_hours"].median().reindex(order)

STRONG = "#D1452B"
GREY = "#B8B8B8"
DARK = "#333333"

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [3, 2], "wspace": 0.35}
)

y = np.arange(len(order))[::-1]  # Swiftline at top

# Left panel: share of parcels past the cold-pack limit (the decision metric)
colors1 = [STRONG if c == "Swiftline" else GREY for c in order]
ax1.barh(y, pct_over.values, color=colors1, height=0.6)
for yi, c in zip(y, order):
    label = f"{pct_over[c]:.1f}%  ({over[c]} of {n[c]})"
    ax1.text(pct_over[c] + 0.4, yi, label, va="center", fontsize=11,
             color=STRONG if c == "Swiftline" else DARK,
             fontweight="bold" if c == "Swiftline" else "normal")
ax1.set_yticks(y)
ax1.set_yticklabels(order, fontsize=12)
ax1.set_xlim(0, 22)
ax1.set_xlabel("% of parcels delivered after more than 48 hours", fontsize=10)
ax1.set_title("Parcels arriving after cold packs expire (>48 h)",
              fontsize=11, loc="left", color=DARK)

# Right panel: typical (median) delivery time, as context
ax2.barh(y, median_h.values, color=GREY, height=0.6)
for yi, c in zip(y, order):
    ax2.text(median_h[c] + 0.5, yi, f"{median_h[c]:.1f} h", va="center",
             fontsize=11, color=DARK)
ax2.set_yticks(y)
ax2.set_yticklabels(order, fontsize=12)
ax2.set_xlim(0, 30)
ax2.set_xlabel("Median delivery time, hours", fontsize=10)
ax2.set_title("Typical delivery time", fontsize=11, loc="left", color=DARK)

for ax in (ax1, ax2):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", labelsize=9, colors="#555555")

fig.suptitle(
    "Swiftline is fastest on a typical delivery, but 1 in 7 of its parcels\n"
    "arrived after the 48-hour cold packs had run out",
    fontsize=15, fontweight="bold", x=0.06, ha="left", y=0.98,
)

pp_one_more = 100 * (over["ParcelPro"] + 1) / n["ParcelPro"]
fig.text(
    0.06, 0.03,
    f"Caveat: ParcelPro started in September, so its rate rests on only {n['ParcelPro']} deliveries "
    f"(vs {n['Swiftline']} for the others).\nOne more slow parcel would raise it to {pp_one_more:.0f}%. "
    "Deliveries Aug–Oct 2026.",
    fontsize=9.5, color="#555555", ha="left", va="bottom",
)

fig.subplots_adjust(left=0.12, right=0.97, top=0.80, bottom=0.2)
