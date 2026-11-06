import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Read data
df = pd.read_csv("data.csv")
df["total_acq_cost"] = df["funded_loans"] * df["acquisition_cost_per_loan_usd"]

# Totals
total_apps = df["applications"].sum()
total_funded_value = df["funded_value_musd"].sum()
total_acq_cost = df["total_acq_cost"].sum()

# Broker totals
broker = df[df["channel"] == "Broker"]
broker_apps = broker["applications"].sum()
broker_funded_value = broker["funded_value_musd"].sum()
broker_acq_cost = broker["total_acq_cost"].sum()

# Broker shares
shares = {
    "Applications": broker_apps / total_apps * 100,
    "Acquisition cost": broker_acq_cost / total_acq_cost * 100,
    "Funded value": broker_funded_value / total_funded_value * 100,
}

categories = list(shares.keys())
values = list(shares.values())

# Chart
fig, ax = plt.subplots(figsize=(10, 6))

colors = ["#D9D9D9", "#A6A6A6", "#D55E00"]
bars = ax.barh(categories, values, color=colors, height=0.55)
ax.invert_yaxis()

# Direct labels
for bar, val in zip(bars, values):
    is_value = val == shares["Funded value"]
    ax.text(
        val + 1.0,
        bar.get_y() + bar.get_height() / 2,
        f"{val:.0f}%",
        va="center",
        ha="left",
        fontsize=14,
        fontweight="bold" if is_value else "normal",
        color="#D55E00" if is_value else "#444444",
    )

ax.set_xlim(0, 40)
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{x:.0f}%"))
ax.set_xlabel("Share of Ridgeview total, Jan–Sep 2026", fontsize=11, color="#444444")
ax.tick_params(axis="y", labelsize=13)
ax.tick_params(axis="x", labelsize=10)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.spines["bottom"].set_color("#CCCCCC")
ax.grid(axis="x", color="#E5E5E5", linestyle="-", linewidth=0.8)
ax.set_axisbelow(True)

# Title and subtitle
value_pct = shares["Funded value"]
cost_pct = shares["Acquisition cost"]

fig.text(
    0.08,
    0.92,
    f"Closing the broker channel would cut {value_pct:.0f}% of funded value",
    fontsize=16,
    fontweight="bold",
    ha="left",
    color="#222222",
)
fig.text(
    0.08,
    0.86,
    f"to save {cost_pct:.0f}% of acquisition cost.",
    fontsize=16,
    fontweight="bold",
    ha="left",
    color="#222222",
)
fig.text(
    0.08,
    0.80,
    "Broker channel share of total, Jan–Sep 2026",
    fontsize=11,
    ha="left",
    color="#555555",
)

# Caveat
fig.text(
    0.08,
    0.04,
    "Note: Broker default rate is projected, not observed history.",
    fontsize=9,
    ha="left",
    color="#666666",
)

fig.subplots_adjust(left=0.22, right=0.95, top=0.72, bottom=0.15)
