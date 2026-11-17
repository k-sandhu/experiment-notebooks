import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Aggregate Jan to Sep 2026 by channel
df["acq_cost_total"] = df["funded_loans"] * df["acquisition_cost_per_loan_usd"]
g = df.groupby("channel").agg(
    loans=("funded_loans", "sum"),
    value_musd=("funded_value_musd", "sum"),
    cost=("acq_cost_total", "sum"),
)
g["cost_per_loan"] = g["cost"] / g["loans"]
g["cost_per_100"] = g["cost"] / (g["value_musd"] * 1e6) * 100

order = ["Branch", "Online", "Partner app", "Broker"]   # Broker at the top of the horizontal bars
g = g.loc[order]

broker_share = g.loc["Broker", "value_musd"] / g["value_musd"].sum() * 100
total_value = g["value_musd"].sum()

HIGHLIGHT = "#C0392B"
GREY = "#B8B8B8"
colors = [HIGHLIGHT if c == "Broker" else GREY for c in order]

fig, axes = plt.subplots(1, 2, figsize=(10, 6), sharey=True)
fig.subplots_adjust(left=0.12, right=0.96, top=0.74, bottom=0.17, wspace=0.12)

panels = [
    ("cost_per_loan", "Cost per funded loan (US$)", lambda v: f"${v:,.0f}"),
    ("cost_per_100", "Cost per $100 lent (US$)", lambda v: f"${v:.2f}"),
]

for ax, (col, label, fmt) in zip(axes, panels):
    vals = g[col].values
    ax.barh(order, vals, color=colors, height=0.6)
    ax.set_xlim(0, vals.max() * 1.25)
    ax.set_title(label, loc="left", fontsize=12, fontweight="bold", color="#333333")
    for i, (c, v) in enumerate(zip(order, vals)):
        is_b = c == "Broker"
        ax.text(v + vals.max() * 0.02, i, fmt(v), va="center",
                fontsize=12 if is_b else 10,
                fontweight="bold" if is_b else "normal",
                color=HIGHLIGHT if is_b else "#555555")
    ax.xaxis.set_visible(False)
    for s in ["top", "right", "bottom"]:
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#999999")
    ax.tick_params(axis="y", length=0, labelsize=11)

for lbl in axes[0].get_yticklabels():
    if lbl.get_text() == "Broker":
        lbl.set_color(HIGHLIGHT)
        lbl.set_fontweight("bold")

# Title and subtitle
fig.text(0.02, 0.95,
         "Broker loans cost the most each, but less per dollar lent than branch loans",
         fontsize=15, fontweight="bold", color="#222222", ha="left")
fig.text(0.02, 0.875,
         f"Acquisition cost by channel, Jan to Sep 2026. Broker loans average about $58k, so the cost is spread\n"
         f"over more lending. Broker brought in {broker_share:.0f}% of all funded value "
         f"(${g.loc['Broker','value_musd']:.0f}M of ${total_value:.0f}M).",
         fontsize=10.5, color="#555555", ha="left", va="top")

# Caveat that affects the decision
fig.text(0.02, 0.05,
         "Caution: Broker's 12-month default rate (2.1%) is a model projection. The channel began in Nov 2025, so there is no "
         "observed loss history yet.\nBranch (1.8%) and Online (2.4%) are observed rates. Acquisition cost includes marketing, "
         "commission and processing.",
         fontsize=9, color="#555555", ha="left", va="bottom", style="italic")
