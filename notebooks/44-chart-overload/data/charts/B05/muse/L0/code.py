import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

df = pd.read_csv("data.csv")

order = ["Swiftline", "Northway", "ParcelPro"]
df = df[df["courier"].isin(order)].copy()

# Summary statistics, calculated from the data
summary = (
    df.groupby("courier")
    .agg(
        n=("actual_hours", "size"),
        median=("actual_hours", "median"),
        over48=("actual_hours", lambda x: (x > 48).sum()),
        mean_cost=("cost_usd", "mean"),
        mean_rating=("customer_rating", "mean"),
        damaged=("damaged", "sum"),
    )
    .reindex(order)
)
summary["pct_over48"] = 100 * summary["over48"] / summary["n"]

# Wilson 95% confidence intervals for % over 48 hours
z = 1.96
ci_low, ci_high = [], []
for _, row in summary.iterrows():
    n, k = row["n"], row["over48"]
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    ci_low.append(100 * max(0, centre - half))
    ci_high.append(100 * min(1, centre + half))
summary["ci_low"] = ci_low
summary["ci_high"] = ci_high

fig, (ax, ax2) = plt.subplots(
    1, 2,
    figsize=(10, 6),
    sharey=True,
    gridspec_kw={"width_ratios": [2.35, 1.0], "wspace": 0.08},
)

fig.suptitle(
    "Swiftline is fastest on a typical delivery — but most often outlasts the cold pack",
    fontsize=14, fontweight="bold", x=0.06, ha="left",
)
fig.text(
    0.06, 0.92,
    "Medicines stay safe for 48 hours. Swiftline's low median hides a long, unsafe tail.",
    fontsize=10.5, color="#444444", ha="left",
)

# --- Left panel: every delivery ---
rng = np.random.default_rng(42)
colours = {"safe": "#4C78A8", "unsafe": "#C1272D"}

y_labels = []
for i, courier in enumerate(order):
    sub = df[df["courier"] == courier]
    y = i + rng.uniform(-0.18, 0.18, size=len(sub))
    safe = sub["actual_hours"] <= 48

    ax.scatter(
        sub.loc[safe, "actual_hours"], y[safe.values],
        s=22, color=colours["safe"], alpha=0.55,
        edgecolors="white", linewidths=0.4, zorder=3,
    )
    ax.scatter(
        sub.loc[~safe, "actual_hours"], y[(~safe).values],
        s=34, color=colours["unsafe"], alpha=0.9,
        edgecolors="white", linewidths=0.5, zorder=4,
    )

    med = summary.loc[courier, "median"]
    ax.plot([med, med], [i - 0.30, i + 0.30], color="black", lw=3, zorder=5)
    y_labels.append(
        f"{courier}\nmedian {med:.1f} h, n={int(summary.loc[courier, 'n'])}"
    )

ax.axvline(48, color=colours["unsafe"], lw=1.8, ls="--", zorder=2)
ax.text(
    48.7, -0.62, "48-hour\ncold-pack limit",
    color=colours["unsafe"], fontsize=8.5, va="bottom", fontweight="bold",
)
ax.set_xlim(0, 82)
ax.set_xlabel("Actual time from dispatch to delivery (hours)")
ax.set_title("Every delivery", fontsize=11, fontweight="bold", loc="left")
ax.set_yticks(range(len(order)))
ax.set_yticklabels(y_labels)
ax.invert_yaxis()
ax.set_ylim(len(order) - 0.35, -0.65)
ax.grid(axis="x", color="#DDDDDD", lw=0.6)
ax.set_axisbelow(True)

legend_handles = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor=colours["safe"],
           markersize=6, label="Delivered within 48 h"),
    Line2D([0], [0], marker="o", color="w", markerfacecolor=colours["unsafe"],
           markersize=7, label="Delivered after 48 h"),
    Line2D([0], [0], color="black", lw=3, label="Median"),
]
ax.legend(handles=legend_handles, frameon=False, fontsize=8.5, loc="lower right")

# --- Right panel: share beyond the safety limit ---
bar_colours = ["#C1272D", "#7A7A7A", "#7A7A7A"]
y_pos = np.arange(len(order))
pcts = summary["pct_over48"].values
xerr = np.vstack([
    pcts - summary["ci_low"].values,
    summary["ci_high"].values - pcts,
])
ax2.barh(y_pos, pcts, color=bar_colours, height=0.52, zorder=3)
ax2.errorbar(
    pcts, y_pos, xerr=xerr, fmt="none",
    ecolor="black", elinewidth=1.1, capsize=3, zorder=4,
)
for i, courier in enumerate(order):
    row = summary.loc[courier]
    ax2.text(
        row["ci_high"] + 0.7, i,
        f"{row['pct_over48']:.1f}%  ({int(row['over48'])}/{int(row['n'])})",
        va="center", fontsize=9,
        fontweight="bold" if courier == "Swiftline" else "normal",
    )

ax2.set_xlim(0, 27)
ax2.set_xlabel("Deliveries taking >48 hours (%)")
ax2.set_title("Beyond the safety limit", fontsize=11, fontweight="bold", loc="left")
ax2.grid(axis="x", color="#DDDDDD", lw=0.6)
ax2.set_axisbelow(True)

for a in (ax, ax2):
    for spine in ("top", "right"):
        a.spines[spine].set_visible(False)

cost_lo, cost_hi = summary["mean_cost"].min(), summary["mean_cost"].max()
rate_lo, rate_hi = summary["mean_rating"].min(), summary["mean_rating"].max()
fig.text(
    0.06, 0.02,
    "Each dot is one delivery (n=220, Aug–Oct 2026). Error bars are 95% Wilson intervals; ParcelPro "
    "only started in September (n=40), so its estimate is less certain.\n"
    f"Couriers were otherwise similar: mean cost ${cost_lo:.2f}–${cost_hi:.2f}, "
    f"mean rating {rate_lo:.1f}–{rate_hi:.1f}/5, and one damaged parcel each.",
    fontsize=8.5, color="#555555", ha="left", va="bottom",
)

fig.tight_layout(rect=[0, 0.07, 1, 0.89])
