import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")
df["over48"] = df["actual_hours"] > 48

order = ["ParcelPro", "Northway", "Swiftline"]  # bottom to top

g = df.groupby("courier").agg(
    n=("delivery_id", "size"),
    n_over=("over48", "sum"),
    median_h=("actual_hours", "median"),
    cost=("cost_usd", "mean"),
    rating=("customer_rating", "mean"),
    damaged=("damaged", "sum"),
).loc[order]
g["pct_over"] = 100 * g["n_over"] / g["n"]

colors = {"Swiftline": "#C1272D", "Northway": "#1B6B6B", "ParcelPro": "#7A8A99"}
bar_colors = [colors[c] for c in g.index]

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6),
    gridspec_kw={"width_ratios": [1.55, 1.0], "wspace": 0.38},
)

# --- Title: the decision, readable in 10 seconds ---
fig.suptitle(
    "Swiftline is fastest — but unsafe for refrigerated medicine",
    fontsize=19, fontweight="bold", x=0.5, y=0.97, ha="center",
)
fig.text(
    0.5, 0.915,
    "Cold packs last 48 hours.  One in seven Swiftline parcels arrived after that.",
    fontsize=12.5, ha="center", color="#333333",
)

# --- Left (main): % exceeding the 48 h cold-pack limit ---
y = np.arange(len(g))
ax1.barh(y, g["pct_over"], height=0.55, color=bar_colors, edgecolor="none")

for yi, courier in zip(y, g.index):
    pct, n_over, n = g.loc[courier, ["pct_over", "n_over", "n"]]
    label = f"{pct:.1f}%   ({int(n_over)} of {int(n)})"
    if courier == "Swiftline":
        label += "  —  1 in 7 unsafe"
    ax1.text(
        pct + 0.4, yi, label,
        va="center", ha="left", fontsize=12.5,
        fontweight="bold" if courier == "Swiftline" else "normal",
        color=colors[courier] if courier == "Swiftline" else "#222222",
    )

ax1.set_yticks(y)
ax1.set_yticklabels(
    [f"{c}\n(n={int(g.loc[c, 'n'])})" for c in g.index], fontsize=11.5
)
ax1.set_xlim(0, 19)
ax1.set_xticks([0, 5, 10, 15])
ax1.set_xticklabels(["0%", "5%", "10%", "15%"], fontsize=10)
ax1.set_xlabel("Parcels delivered after 48 hours", fontsize=11)
ax1.set_title("UNSAFE DELIVERIES  (> 48 h)", fontsize=12, fontweight="bold", pad=10)
ax1.spines[["top", "right", "left"]].set_visible(False)
ax1.tick_params(length=0)
ax1.grid(axis="x", color="#DDDDDD", linewidth=0.7)
ax1.set_axisbelow(True)

# --- Right (context): typical speed, where Swiftline wins ---
ax2.barh(y, g["median_h"], height=0.55, color=bar_colors, edgecolor="none", alpha=0.9)
ax2.axvline(48, color="#C1272D", linestyle="--", linewidth=1.6)
ax2.text(48.6, len(g) - 0.35, "48 h\ncold-pack\nlimit",
         fontsize=9, color="#C1272D", va="top", ha="left")

for yi, courier in zip(y, g.index):
    med = g.loc[courier, "median_h"]
    ax2.text(med + 1, yi, f"{med:.1f} h", va="center", ha="left", fontsize=12)

ax2.set_yticks(y)
ax2.set_yticklabels([])
ax2.set_xlim(0, 60)
ax2.set_xticks([0, 24, 48])
ax2.set_xticklabels(["0", "24", "48 h"], fontsize=10)
ax2.set_xlabel("Median delivery time", fontsize=11)
ax2.set_title("TYPICAL SPEED  (median)", fontsize=12, fontweight="bold", pad=10)
ax2.spines[["top", "right", "left"]].set_visible(False)
ax2.tick_params(length=0)
ax2.grid(axis="x", color="#DDDDDD", linewidth=0.7)
ax2.set_axisbelow(True)
ax2.text(
    0.5, -0.22,
    "Swiftline's typical parcel is quick —\nits failures are the problem.",
    transform=ax2.transAxes, ha="center", fontsize=9.5, color="#444444",
)

# --- Recommendation + why nothing else decides it ---
cost_lo, cost_hi = g["cost"].min(), g["cost"].max()
rate_lo, rate_hi = g["rating"].min(), g["rating"].max()

fig.text(
    0.5, 0.13,
    "RECOMMENDATION:  Contract Northway.  Do not use Swiftline for refrigerated deliveries.",
    ha="center", fontsize=13, fontweight="bold", color="white",
    bbox=dict(boxstyle="round,pad=0.5", facecolor="#1B6B6B", edgecolor="none"),
)
fig.text(
    0.5, 0.055,
    f"Price (${cost_lo:.2f}–${cost_hi:.2f}/delivery), rating ({rate_lo:.1f}–{rate_hi:.1f}/5) and damage "
    f"(1 parcel each) are near-identical — safety decides it.\n"
    "ParcelPro looks as safe as Northway but rests on only 40 deliveries (since September), "
    "vs 90 proven for Northway.",
    ha="center", fontsize=9.5, color="#333333",
)

plt.subplots_adjust(left=0.13, right=0.97, top=0.82, bottom=0.24)
