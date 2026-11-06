import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("data.csv")

# For refrigerated medicine, only the tail beyond the 48-hour
# cold-pack limit matters for safety — not typical speed.
summary = (
    df.groupby("courier")
    .agg(
        pct_over_48=("actual_hours", lambda s: (s > 48).mean() * 100),
        n=("actual_hours", "size"),
        n_over=("actual_hours", lambda s: (s > 48).sum()),
    )
    .reindex(["Swiftline", "ParcelPro", "Northway"])
)

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.23, right=0.97, top=0.79, bottom=0.16)

couriers = summary.index.tolist()
values = summary["pct_over_48"].values
labels = [f"{c}  (n={int(summary.loc[c, 'n'])})" for c in couriers]
colors = ["#C1272D" if c == "Swiftline" else "#B8B8B8" for c in couriers]

ax.barh(labels, values, color=colors, height=0.62)
ax.invert_yaxis()

# Tighter, cleaner scale: the value label now sits inside the bar,
# so no dead space is needed to the right of the plot.
ax.set_xlim(0, 16)
ax.set_xticks([0, 5, 10, 15])
ax.set_xticklabels(["0%", "5%", "10%", "15%"])
ax.set_xlabel("Deliveries taking more than 48 hours", fontsize=11)
ax.tick_params(axis="y", labelsize=13, length=0)
ax.tick_params(axis="x", labelsize=11)
for tick_label in ax.get_yticklabels():
    if "Swiftline" in tick_label.get_text():
        tick_label.set_fontweight("bold")
ax.xaxis.grid(True, color="#E6E6E6", linewidth=0.8)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

# Only the number that carries the message is labelled
swift = summary.loc["Swiftline"]
ax.text(
    swift["pct_over_48"] - 0.35, 0,
    f"{swift['pct_over_48']:.1f}%  ({int(swift['n_over'])} of {int(swift['n'])})",
    va="center", ha="right", fontsize=13, fontweight="bold", color="white",
)

# Caveat placed on the bar it applies to, where it will be seen,
# rather than buried in a footnote.
pp = summary.loc["ParcelPro"]
ax.text(
    pp["pct_over_48"] + 0.35, 1,
    "1 of 40 — less certain",
    va="center", ha="left", fontsize=10, style="italic", color="#666666",
)

# Title aligned with the courier labels, large enough to read in seconds
fig.text(
    0.055, 0.97,
    "Swiftline puts 1 in 7 refrigerated deliveries\npast the 48-hour safety limit",
    fontsize=19, fontweight="bold", ha="left", va="top",
)
fig.text(
    0.055, 0.845,
    "Cold packs keep medicines safe for 48 hours.",
    fontsize=11, color="#555555", ha="left", va="top",
)

fig.text(
    0.055, 0.035,
    "ParcelPro started in September (40 deliveries vs 90 each for the others). "
    "Cost and customer ratings are similar across couriers.",
    fontsize=9.5, color="#555555", ha="left", va="bottom",
)
