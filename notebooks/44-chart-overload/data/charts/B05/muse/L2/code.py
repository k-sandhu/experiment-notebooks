import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv("data.csv")

# For refrigerated medicine, only the tail beyond the 48-hour
# cold-pack limit matters for safety — not typical speed.
summary = (
    df.groupby("courier")
    .agg(pct_over_48=("actual_hours", lambda s: (s > 48).mean() * 100),
         n=("actual_hours", "size"),
         n_over=("actual_hours", lambda s: (s > 48).sum()))
    .reindex(["Swiftline", "ParcelPro", "Northway"])
)

fig, ax = plt.subplots(figsize=(10, 6))

couriers = summary.index.tolist()
values = summary["pct_over_48"].values
labels = [f"{c}  (n={int(summary.loc[c, 'n'])})" for c in couriers]
colors = ["#C1272D" if c == "Swiftline" else "#B8B8B8" for c in couriers]

ax.barh(labels, values, color=colors, height=0.55)
ax.invert_yaxis()

ax.set_xlim(0, max(values) * 1.35)
ax.set_xlabel("Deliveries taking more than 48 hours (%)", fontsize=11)
ax.tick_params(axis="y", labelsize=12, length=0)
ax.tick_params(axis="x", labelsize=11)
ax.xaxis.grid(True, color="#E6E6E6", linewidth=0.8)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)

# Only the number that carries the message is labelled
swift = summary.loc["Swiftline"]
ax.text(swift["pct_over_48"] + 0.4, 0,
        f"{swift['pct_over_48']:.1f}%  ({int(swift['n_over'])} of {int(swift['n'])})",
        va="center", ha="left", fontsize=13, fontweight="bold", color="#C1272D")

ax.set_title("Swiftline puts 1 in 7 refrigerated deliveries past the 48-hour safety limit",
             loc="left", fontsize=16, fontweight="bold", pad=14)

pp = summary.loc["ParcelPro"]
fig.text(0.07, 0.03,
         f"Cold packs keep medicines safe for 48 hours. ParcelPro started in September "
         f"({int(pp['n'])} deliveries vs 90 each for the others),\n"
         f"so its figure rests on {int(pp['n_over'])} late parcel and is less certain. "
         f"Cost and customer ratings are similar across couriers.",
         fontsize=9, color="#555555", ha="left", va="bottom")

plt.tight_layout(rect=[0, 0.09, 1, 0.96])
