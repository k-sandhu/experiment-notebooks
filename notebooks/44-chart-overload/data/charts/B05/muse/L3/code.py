import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("data.csv")

order = ["Swiftline", "Northway", "ParcelPro"]

stats = df.groupby("courier").agg(
    n=("actual_hours", "size"),
    breaches=("actual_hours", lambda x: (x > 48).sum()),
    breach_pct=("actual_hours", lambda x: 100 * (x > 48).mean()),
    median_h=("actual_hours", "median"),
).reindex(order)

breach_pct = stats["breach_pct"].values
median_h = stats["median_h"].values

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.5, 1]}
)
fig.subplots_adjust(left=0.08, right=0.97, top=0.80, bottom=0.20, wspace=0.28)

# Title states the decision message
fig.text(
    0.08, 0.95,
    "Swiftline puts 1 in 7 refrigerated parcels past the\n48-hour cold-pack safe limit",
    fontsize=17, fontweight="bold", va="top", ha="left", color="#1a1a1a",
)
fig.text(
    0.08, 0.855,
    "It is fastest on a typical delivery — the risk is its long tail, not its typical speed",
    fontsize=11, va="top", ha="left", color="#555555",
)

# --- Main panel: share over 48 hours ---
colours = ["#C0392B", "#B8B8B8", "#B8B8B8"]
bars1 = ax1.bar(order, breach_pct, color=colours, width=0.62, zorder=3)
ax1.set_title("Delivered after 48 hours", fontsize=12, fontweight="bold", loc="left")
ax1.set_ylabel("% of deliveries", fontsize=11)
ax1.set_ylim(0, max(breach_pct) * 1.28)
ax1.set_yticks(np.arange(0, 16, 5))
ax1.grid(axis="y", color="#E5E5E5", linewidth=0.8, zorder=0)
ax1.tick_params(axis="both", labelsize=11)
ax1.set_xticklabels([f"{c}\n(n={int(stats.loc[c, 'n'])})" for c in order])

# Only the number that carries the message is labelled on a bar
ax1.annotate(
    f"{stats.loc['Swiftline', 'breach_pct']:.1f}%",
    xy=(0, breach_pct[0]), xytext=(0, breach_pct[0] + 0.7),
    ha="center", fontsize=16, fontweight="bold", color="#C0392B",
)

# --- Context panel: typical (median) delivery ---
ax2.bar(order, median_h, color="#B8B8B8", width=0.62, zorder=3)
ax2.set_title("Typical delivery (median)", fontsize=12, fontweight="bold", loc="left")
ax2.set_ylabel("Hours", fontsize=11)
ax2.set_ylim(0, 28)
ax2.set_yticks(np.arange(0, 29, 10))
ax2.grid(axis="y", color="#E5E5E5", linewidth=0.8, zorder=0)
ax2.tick_params(axis="both", labelsize=11)
ax2.annotate(
    f"{stats.loc['Swiftline', 'median_h']:.1f}h",
    xy=(0, median_h[0]), xytext=(0, median_h[0] + 0.9),
    ha="center", fontsize=12, fontweight="bold", color="#444444",
)

for ax in (ax1, ax2):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#AAAAAA")

# Exact supporting figures and the one caveat that affects reading
fig.text(
    0.08, 0.02,
    f"Breaches: Northway {stats.loc['Northway', 'breach_pct']:.1f}% , "
    f"ParcelPro {stats.loc['ParcelPro', 'breach_pct']:.1f}%  •  "
    f"Medians: Northway {stats.loc['Northway', 'median_h']:.1f}h, "
    f"ParcelPro {stats.loc['ParcelPro', 'median_h']:.1f}h\n"
    "Caveat: ParcelPro started in September — n=40 vs 90 each for the others; "
    "its 2.5% is a single parcel and could easily be 2–3 in a larger sample.",
    fontsize=8.5, color="#666666", va="bottom", ha="left",
)
