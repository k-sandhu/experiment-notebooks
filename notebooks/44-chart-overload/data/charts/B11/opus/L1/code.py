import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")
df["total_cost_usd"] = df["funded_loans"] * df["acquisition_cost_per_loan_usd"]

g = df.groupby("channel").agg(
    loans=("funded_loans", "sum"),
    value_musd=("funded_value_musd", "sum"),
    cost_usd=("total_cost_usd", "sum"),
)
g["cost_per_loan"] = g["cost_usd"] / g["loans"]
g["cost_per_100"] = g["cost_usd"] / (g["value_musd"] * 1e6) * 100
g["avg_loan_k"] = g["value_musd"] * 1e3 / g["loans"]
g["value_share"] = g["value_musd"] / g["value_musd"].sum() * 100

order = ["Branch", "Online", "Broker", "Partner app"]
g = g.loc[order]
total_value = g["value_musd"].sum()

broker_color = "#d4691e"
other_color = "#b8b8b8"
colors = [broker_color if c == "Broker" else other_color for c in order]
y = np.arange(len(order))

fig, axes = plt.subplots(1, 3, figsize=(10, 6), sharey=True)
fig.subplots_adjust(top=0.74, bottom=0.2, left=0.12, right=0.97, wspace=0.3)

panels = [
    ("Acquisition cost\nper funded loan", "cost_per_loan", lambda v, c: f"${v:,.0f}"),
    ("Acquisition cost\nper $100 lent", "cost_per_100", lambda v, c: f"${v:.2f}"),
    ("Funded value,\nJan–Sep 2026", "value_musd",
     lambda v, c: f"${v:.0f}M ({g.loc[c, 'value_share']:.0f}%)"),
]

for ax, (title, col, fmt) in zip(axes, panels):
    vals = g[col].values
    ax.barh(y, vals, color=colors, height=0.62)
    for yi, v, c in zip(y, vals, order):
        ax.text(v + vals.max() * 0.03, yi, fmt(v, c), va="center", fontsize=10.5,
                color=broker_color if c == "Broker" else "#444444",
                fontweight="bold" if c == "Broker" else "normal")
    ax.set_xlim(0, vals.max() * 1.55)
    ax.set_title(title, fontsize=11.5, loc="left", color="#222222")
    ax.set_xticks([])
    for s in ["top", "right", "bottom"]:
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#999999")
    ax.tick_params(axis="y", length=0)

axes[0].set_yticks(y)
axes[0].set_yticklabels(order, fontsize=11)
for lbl in axes[0].get_yticklabels():
    if lbl.get_text() == "Broker":
        lbl.set_color(broker_color)
        lbl.set_fontweight("bold")
axes[0].invert_yaxis()

b = g.loc["Broker"]
br = g.loc["Branch"]
fig.text(0.02, 0.95,
         "Broker costs the most per loan, but less per dollar lent than branches",
         fontsize=15, fontweight="bold", ha="left", color="#111111")
fig.text(0.02, 0.885,
         f"Broker loans average ${b['avg_loan_k']:.0f}k, so acquisition costs ${b['cost_per_100']:.2f} per $100 lent "
         f"(branch ${br['cost_per_100']:.2f}).\n"
         f"Closing broker would give up {b['value_share']:.0f}% of the ${total_value:.0f}M funded Jan–Sep 2026.",
         fontsize=11, ha="left", va="top", color="#333333")

fig.text(0.02, 0.035,
         "Caution: broker's 12-month default rate (2.1%) is a model projection, not observed. Broker lending began Nov 2025, "
         "so no loan has a full year of history.\n"
         "Partner app launched Mar 2026 (7 months of data); its 3.0% default rate is also projected. "
         "Acquisition cost = marketing, commission and processing per funded loan.",
         fontsize=8.5, ha="left", va="bottom", color="#666666")
