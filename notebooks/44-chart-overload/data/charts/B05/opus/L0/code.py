import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")
df["over48"] = df["actual_hours"] > 48

order = ["Swiftline", "Northway", "ParcelPro"]
LIMIT = 48
c_ok = "#9aa5b1"
c_bad = "#c0392b"

stats = (df.groupby("courier")
           .agg(n=("actual_hours", "size"),
                median=("actual_hours", "median"),
                over=("over48", "sum"))
           .reindex(order))
stats["pct"] = 100 * stats["over"] / stats["n"]

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.6, 1]}
)

# Left panel: every delivery, with the 48-hour cold-pack limit
rng = np.random.default_rng(1)
for i, c in enumerate(order):
    sub = df[df["courier"] == c]
    x = i + rng.uniform(-0.22, 0.22, len(sub))
    colors = np.where(sub["over48"], c_bad, c_ok)
    ax1.scatter(x, sub["actual_hours"], s=22, c=colors, alpha=0.8,
                edgecolors="white", linewidths=0.4, zorder=3)
    med = stats.loc[c, "median"]
    ax1.hlines(med, i - 0.3, i + 0.3, color="black", lw=2.2, zorder=4)
    ax1.text(i + 0.32, med, f"median\n{med:.1f} h", va="center",
             ha="left", fontsize=8.5)

ax1.axhline(LIMIT, color=c_bad, ls="--", lw=1.3, zorder=2)
ax1.text(-0.45, LIMIT + 1.2, "48 h: cold packs stop protecting the medicine",
         color=c_bad, fontsize=9, va="bottom")
ax1.set_xticks(range(len(order)))
ax1.set_xticklabels([f"{c}\n(n={stats.loc[c, 'n']})" for c in order])
ax1.set_xlim(-0.5, len(order) - 0.5 + 0.35)
ax1.set_ylabel("Hours from dispatch to delivery")
ax1.set_ylim(0, max(80, df["actual_hours"].max() + 5))
ax1.set_title("Each dot is one delivery", fontsize=11, loc="left")
for s in ["top", "right"]:
    ax1.spines[s].set_visible(False)
ax1.grid(axis="y", alpha=0.3, zorder=0)

# Right panel: share of parcels over 48 hours
y = np.arange(len(order))[::-1]
bar_colors = [c_bad if c == "Swiftline" else c_ok for c in order]
ax2.barh(y, stats["pct"], color=bar_colors, height=0.55, zorder=3)
for yi, c in zip(y, order):
    p = stats.loc[c, "pct"]
    ax2.text(p + 0.4, yi, f"{p:.1f}%  ({int(stats.loc[c, 'over'])} of {stats.loc[c, 'n']})",
             va="center", fontsize=10)
ax2.set_yticks(y)
ax2.set_yticklabels(order)
ax2.set_xlim(0, max(stats["pct"]) * 1.6)
ax2.set_xlabel("% of parcels delivered after more than 48 h")
ax2.set_title("Parcels past the cold-pack limit", fontsize=11, loc="left")
for s in ["top", "right"]:
    ax2.spines[s].set_visible(False)
ax2.grid(axis="x", alpha=0.3, zorder=0)

fig.suptitle("Swiftline is fastest on a typical delivery, but about 1 in 7 of its "
             "parcels\narrive after the 48-hour cold-pack limit",
             fontsize=13, fontweight="bold", x=0.02, ha="left")
fig.text(0.02, 0.015,
         "Aug–Oct 2026. Prices ($9.28–$9.73 per delivery) and customer ratings (4.2–4.3 of 5) "
         "are similar across couriers.\nParcelPro started in September, so its rate rests on "
         "only 40 deliveries; one late parcel more or less moves it by 2.5 points.",
         fontsize=8.5, color="#555555", ha="left", va="bottom")

fig.tight_layout(rect=[0, 0.08, 1, 0.9])
