import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

order = ["Swiftline", "Northway", "ParcelPro"]
df["over48"] = df["actual_hours"] > 48

median_hours = df.groupby("courier")["actual_hours"].median().reindex(order)
over48_pct = df.groupby("courier")["over48"].mean().reindex(order) * 100
counts = df.groupby("courier").size().reindex(order)

fig, ax = plt.subplots(figsize=(10, 6))

colors = ["#C0392B" if c == "Swiftline" else "#9AA0A6" for c in order]
sizes = [230 if c == "Swiftline" else 130 for c in order]

for c, color, size in zip(order, colors, sizes):
    ax.scatter(
        median_hours[c],
        over48_pct[c],
        s=size,
        color=color,
        edgecolor="white",
        linewidth=1.2,
        zorder=3
    )

ax.annotate(
    f"Swiftline\n{median_hours['Swiftline']:.1f} h median\n{over48_pct['Swiftline']:.1f}% over 48 h",
    xy=(median_hours["Swiftline"], over48_pct["Swiftline"]),
    xytext=(median_hours["Swiftline"] + 0.8, over48_pct["Swiftline"] - 1.8),
    fontsize=10,
    color="#C0392B",
    fontweight="bold",
    va="top",
    ha="left",
    arrowprops=dict(arrowstyle="-", color="#C0392B", lw=0.8)
)

ax.annotate(
    f"Northway\n{median_hours['Northway']:.1f} h, {over48_pct['Northway']:.1f}% over 48 h",
    xy=(median_hours["Northway"], over48_pct["Northway"]),
    xytext=(median_hours["Northway"] + 0.7, over48_pct["Northway"] + 2.2),
    fontsize=9.5,
    color="#333333",
    va="bottom",
    ha="left",
    arrowprops=dict(arrowstyle="-", color="#777777", lw=0.8)
)

ax.annotate(
    f"ParcelPro\n{median_hours['ParcelPro']:.1f} h, {over48_pct['ParcelPro']:.1f}% over 48 h\n(n={counts['ParcelPro']})",
    xy=(median_hours["ParcelPro"], over48_pct["ParcelPro"]),
    xytext=(median_hours["ParcelPro"] - 0.9, over48_pct["ParcelPro"] + 3.3),
    fontsize=9.5,
    color="#333333",
    va="bottom",
    ha="right",
    arrowprops=dict(arrowstyle="-", color="#777777", lw=0.8)
)

ax.set_xlim(0, 26)
ax.set_ylim(0, 17)
ax.set_xlabel("Median actual delivery time (hours; lower is better)", fontsize=11)
ax.set_ylabel("Deliveries over 48 hours (%; lower is better)", fontsize=11)
ax.grid(True, axis="both", color="#E6E6E6", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.tick_params(axis="both", labelsize=9.5, colors="#333333")

fig.suptitle(
    "Swiftline is fastest typically, but far more likely to breach the\n48-hour cold-pack limit",
    fontsize=15,
    fontweight="bold",
    ha="center",
    y=0.97
)

fig.text(
    0.5,
    0.025,
    "Caveat: ParcelPro has only 40 deliveries (1 over 48 h) vs 90 each for Swiftline and Northway; treat its low breach rate cautiously.",
    fontsize=9,
    ha="center",
    color="#555555"
)

fig.subplots_adjust(left=0.10, right=0.96, top=0.82, bottom=0.18)
