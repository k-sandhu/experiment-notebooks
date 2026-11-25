import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

LIMIT = 48
df["over"] = df["actual_hours"] > LIMIT
summary = (df.groupby("courier")
             .agg(n=("delivery_id", "size"),
                  over=("over", "sum"),
                  median_h=("actual_hours", "median"))
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

# Direct labels: percentage plus count (the number is the message)
for yi, (_, r) in zip(y, summary.iterrows()):
    is_sw = r["courier"] == "Swiftline"
    ax.text(r["pct"] + 0.3, yi,
            f"{r['pct']:.1f}%  ({int(r['over'])} of {int(r['n'])})",
            va="center", fontsize=13 if is_sw else 12,
            color=highlight if is_sw else "#555555",
            fontweight="bold" if is_sw else "normal")

# Caveat for ParcelPro
pp = summary[summary["courier"] == "ParcelPro"]
if not pp.empty:
    pp_y = y[list(summary["courier"]).index("ParcelPro")]
    ax.text(pp["pct"].iloc[0] + 0.3, pp_y - 0.38,
            f"Only {int(pp['n'].iloc[0])} deliveries (started Sept): one more "
            f"late parcel would add ~{100/pp['n'].iloc[0]:.1f} points",
            va="center", fontsize=9.5, color="#777777", style="italic")

ax.set_xlim(0, max(summary["pct"]) * 1.45)
ax.set_xlabel("Share of deliveries taking more than 48 hours (%)", fontsize=11, color="#444444")
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))

for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#999999")
ax.tick_params(axis="y", length=0)
ax.tick_params(axis="x", colors="#666666")

fig.suptitle("Swiftline let 1 in 7 parcels outlast the 48-hour cold packs;\n"
             "Northway and ParcelPro about 1 in 40",
             x=0.02, ha="left", fontsize=16, fontweight="bold", y=0.97)
ax.set_title("Swiftline is fastest on a typical delivery, but its late parcels arrive very late. "
             "Prices ($9.28–9.73) and ratings (4.2–4.3) are near-identical.\n"
             "Deliveries Aug–Oct 2026, Medley Pharmacy",
             loc="left", fontsize=10.5, color="#555555", pad=12)

fig.subplots_adjust(left=0.13, right=0.97, top=0.78, bottom=0.12)
