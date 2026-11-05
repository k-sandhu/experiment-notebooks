import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FuncFormatter

df = pd.read_csv("data.csv")

LIMIT = 48
df["over"] = df["actual_hours"] > LIMIT
summary = (df.groupby("courier")
             .agg(n=("delivery_id", "size"),
                  over=("over", "sum"))
             .reset_index())
summary["pct"] = summary["over"] / summary["n"] * 100
summary = summary.sort_values("pct", ascending=True)  # largest at top in barh

highlight = "#C0392B"
grey = "#B0B0B0"
colors = [highlight if c == "Swiftline" else grey for c in summary["courier"]]

fig, ax = plt.subplots(figsize=(10, 6))
y = np.arange(len(summary))
ax.barh(y, summary["pct"], color=colors, height=0.6)

ax.set_yticks(y)
ax.set_yticklabels(summary["courier"], fontsize=13)
for tick, c in zip(ax.get_yticklabels(), summary["courier"]):
    if c == "Swiftline":
        tick.set_color(highlight)
        tick.set_fontweight("bold")

# Direct labels: the share over 48 h is the message
for yi, (_, r) in zip(y, summary.iterrows()):
    is_sw = r["courier"] == "Swiftline"
    ax.text(r["pct"] + 0.3, yi,
            f"{r['pct']:.1f}%  ({int(r['over'])} of {int(r['n'])})",
            va="center", fontsize=13 if is_sw else 12,
            color=highlight if is_sw else "#555555",
            fontweight="bold" if is_sw else "normal")

# Caveat for ParcelPro: small sample
pp = summary[summary["courier"] == "ParcelPro"]
if not pp.empty:
    pp_y = y[list(summary["courier"]).index("ParcelPro")]
    n_pp = int(pp["n"].iloc[0])
    over_pp = int(pp["over"].iloc[0])
    ax.text(pp["pct"].iloc[0] + 0.3, pp_y - 0.40,
            f"Caution: only {n_pp} deliveries (started Sept). "
            f"One more late parcel would make it {(over_pp + 1) / n_pp * 100:.1f}%",
            va="center", fontsize=9.5, color="#777777", style="italic")

# Honest x-axis: starts at zero, ticks at clean 5-point steps
ax.set_xlim(0, 21)
ax.xaxis.set_major_locator(MultipleLocator(5))
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.set_xlabel("Share of deliveries taking more than 48 hours", fontsize=11, color="#444444")

for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#999999")
ax.tick_params(axis="y", length=0)
ax.tick_params(axis="x", colors="#666666")

# Title and subtitle, left-aligned together
fig.text(0.02, 0.965,
         "Swiftline let 1 in 7 parcels outlast the 48-hour cold packs;\n"
         "Northway and ParcelPro only about 1 in 40",
         ha="left", va="top", fontsize=16, fontweight="bold")
fig.text(0.02, 0.835,
         "Swiftline is fastest on a typical delivery, but its late parcels arrive very late.\n"
         "Prices ($9.28–9.73) and customer ratings (4.2–4.3) barely differ.  "
         "Medley Pharmacy deliveries, Aug–Oct 2026",
         ha="left", va="top", fontsize=10.5, color="#555555", linespacing=1.4)

fig.subplots_adjust(left=0.13, right=0.97, top=0.72, bottom=0.12)
