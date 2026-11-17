import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

couriers = ["Swiftline", "Northway", "ParcelPro"]
colors = {"Swiftline": "#1f77b4", "Northway": "#ff7f0e", "ParcelPro": "#2ca02c"}

# Courier-level summary: sample size, share over 48h, and Wilson 95% CI
summary = []
for c in couriers:
    vals = df.loc[df["courier"] == c, "actual_hours"].dropna()
    n = len(vals)
    k = int((vals > 48).sum())
    p = k / n
    z = 1.96
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    summary.append({
        "courier": c,
        "n": n,
        "pct": p * 100,
        "ci_low": max(0, (center - half) * 100),
        "ci_high": min(100, (center + half) * 100),
    })

summary = pd.DataFrame(summary)

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.1, 1]}
)

# Left panel: ECDF of actual delivery time
for c in couriers:
    vals = np.sort(df.loc[df["courier"] == c, "actual_hours"].dropna().values)
    n = len(vals)
    y = np.arange(1, n + 1) / n * 100
    ax1.step(
        vals, y, where="post", color=colors[c], linewidth=2.2,
        label=f"{c} (n={n})"
    )

ax1.axvline(48, color="crimson", linestyle="--", linewidth=1.4)
ax1.text(48.8, 8, "48 h cold-pack limit", color="crimson", fontsize=9, va="bottom")
ax1.set_xlabel("Actual delivery time (hours)")
ax1.set_ylabel("Cumulative share of deliveries (%)")
ax1.set_title("Delivery time distributions")
ax1.set_xlim(0, df["actual_hours"].max() + 5)
ax1.set_ylim(0, 100)
ax1.grid(axis="y", alpha=0.25)
ax1.legend(frameon=False, loc="lower right")

# Right panel: percentage over 48h with 95% confidence intervals
x = np.arange(len(summary))
bar_colors = [colors[c] for c in summary["courier"]]
ax2.bar(x, summary["pct"], color=bar_colors, width=0.6, edgecolor="none")

yerr_low = summary["pct"] - summary["ci_low"]
yerr_high = summary["ci_high"] - summary["pct"]
ax2.errorbar(
    x, summary["pct"], yerr=[yerr_low, yerr_high],
    fmt="none", ecolor="black", capsize=5, linewidth=1.1
)

for i, row in summary.iterrows():
    ax2.text(
        i, row["ci_high"] + 0.8, f"{row['pct']:.1f}%",
        ha="center", va="bottom", fontsize=10, fontweight="bold"
    )

ax2.set_xticks(x)
ax2.set_xticklabels(
    [f"{row['courier']}\n(n={int(row['n'])})" for _, row in summary.iterrows()]
)
ax2.set_ylabel("Deliveries over 48 hours (%)")
ax2.set_title("Cold-chain risk by courier (95% CI)")
ax2.set_ylim(0, max(summary["ci_high"]) + 5)
ax2.grid(axis="y", alpha=0.25)

fig.suptitle(
    "Courier performance: typical speed and long-delivery risk",
    fontsize=14, fontweight="bold"
)
plt.tight_layout(rect=[0, 0, 1, 0.95])
