import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Read data and calculate acquisition cost per dollar funded by channel
df = pd.read_csv("data.csv")
df["acq_cost_usd"] = df["funded_loans"] * df["acquisition_cost_per_loan_usd"]

g = (
    df.groupby("channel", as_index=False)
      .agg(
          acq_cost=("acq_cost_usd", "sum"),
          funded_value_musd=("funded_value_musd", "sum"),
      )
)
g["cost_pct"] = g["acq_cost"] / (g["funded_value_musd"] * 1_000_000) * 100

# Sort ascending so the highest cost appears at the top of the horizontal chart
g = g.sort_values("cost_pct", ascending=True)
channels = g["channel"].tolist()
values = g["cost_pct"].tolist()

colors = []
for ch in channels:
    if ch == "Broker":
        colors.append("#D55E00")
    elif ch == "Branch":
        colors.append("#7F7F7F")
    else:
        colors.append("#D9D9D9")

fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(channels, values, color=colors, height=0.55)

# Label only the two channels that carry the message
for ch, val in zip(channels, values):
    if ch in ["Broker", "Branch"]:
        ax.text(
            val + 0.08,
            ch,
            f"{val:.1f}%",
            va="center",
            ha="left",
            fontsize=13,
            fontweight="bold",
            color="#D55E00" if ch == "Broker" else "#444444",
        )

max_val = max(values)
ax.set_xlim(0, max_val * 1.35)
ax.set_xticks(np.arange(0, np.ceil(max_val) + 1, 1))
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{x:.0f}%"))
ax.set_xlabel("Acquisition cost as % of funded loan value", fontsize=11, color="#444444")
ax.tick_params(axis="y", labelsize=13)
ax.tick_params(axis="x", labelsize=10)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.spines["bottom"].set_color("#CCCCCC")
ax.grid(axis="x", color="#E5E5E5", linestyle="-", linewidth=0.8)
ax.set_axisbelow(True)

# Emphasise the key channel labels
for label in ax.get_yticklabels():
    if label.get_text() == "Broker":
        label.set_color("#D55E00")
        label.set_fontweight("bold")
    elif label.get_text() == "Branch":
        label.set_color("#444444")
        label.set_fontweight("bold")

cost_map = dict(zip(g["channel"], g["cost_pct"]))
broker_cost = cost_map["Broker"]
branch_cost = cost_map["Branch"]

fig.text(
    0.08,
    0.93,
    f"Broker's acquisition cost is {broker_cost:.1f}% of funded value—below branches at {branch_cost:.1f}%",
    fontsize=15,
    fontweight="bold",
    ha="left",
    color="#222222",
)
fig.text(
    0.08,
    0.87,
    "Acquisition cost as a share of funded loan value, Jan–Sep 2026",
    fontsize=11,
    ha="left",
    color="#555555",
)
fig.text(
    0.08,
    0.04,
    "Note: Funded value before defaults; broker and partner-app default rates are projected, not observed.",
    fontsize=9,
    ha="left",
    color="#666666",
)

fig.subplots_adjust(left=0.18, right=0.95, top=0.78, bottom=0.15)
