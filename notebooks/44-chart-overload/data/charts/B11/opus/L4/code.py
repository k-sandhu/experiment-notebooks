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

order = ["Partner app", "Online", "Branch", "Broker"]   # Broker at top, Branch next to it
g = g.loc[order]

total_value = g["value_musd"].sum()
broker_value = g.loc["Broker", "value_musd"]
broker_share = broker_value / total_value * 100
broker_cost_m = g.loc["Broker", "cost"] / 1e6

HIGHLIGHT = "#C0392B"
COMPARE = "#7A7A7A"
GREY = "#D3D3D3"
color_map = {"Broker": HIGHLIGHT, "Branch": COMPARE}
colors = [color_map.get(c, GREY) for c in order]

fig, axes = plt.subplots(1, 2, figsize=(10, 6), sharey=True)
fig.subplots_adjust(left=0.13, right=0.96, top=0.72, bottom=0.16, wspace=0.15)

panels = [
    ("cost_per_loan", "Acquisition cost per funded loan (US\\$)", lambda v: f"\\${v:,.0f}"),
    ("cost_per_100", "Acquisition cost per \\$100 lent (US\\$)", lambda v: f"\\${v:.2f}"),
]

for ax, (col, label, fmt) in zip(axes, panels):
    vals = g[col].values
    ax.barh(order, vals, color=colors, height=0.62)
    ax.set_xlim(0, vals.max() * 1.28)
    ax.set_title(label, loc="left", fontsize=11.5, fontweight="bold", color="#333333", pad=10)
    for i, (c, v) in enumerate(zip(order, vals)):
        if c not in color_map:
            continue  # only label the comparison that carries the message
        is_b = c == "Broker"
        ax.text(v + vals.max() * 0.02, i, fmt(v), va="center",
                fontsize=13 if is_b else 11,
                fontweight="bold",
                color=HIGHLIGHT if is_b else COMPARE)
    ax.xaxis.set_visible(False)
    for s in ["top", "right", "bottom"]:
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#999999")
    ax.tick_params(axis="y", length=0, labelsize=11)

for lbl in axes[0].get_yticklabels():
    t = lbl.get_text()
    if t == "Broker":
        lbl.set_color(HIGHLIGHT)
        lbl.set_fontweight("bold")
    elif t == "Branch":
        lbl.set_color("#444444")
        lbl.set_fontweight("bold")
    else:
        lbl.set_color("#888888")

# Title and subtitle
fig.text(0.02, 0.95,
         "Broker costs most per loan, but less per dollar lent than Branch",
         fontsize=16, fontweight="bold", color="#222222", ha="left")
fig.text(0.02, 0.885,
         f"Closing Broker would save about \\${broker_cost_m:.1f}M in acquisition cost, but lose "
         f"\\${broker_value:.0f}M of lending ({broker_share:.0f}% of all funded value), Jan to Sep 2026.\n"
         f"Broker loans average about \\$58k, so each loan's cost is spread over more lending.",
         fontsize=10.5, color="#444444", ha="left", va="top")

# Caveat that affects the decision
fig.text(0.02, 0.04,
         "Caution: Broker's 2.1% 12-month default rate is a model projection (channel began Nov 2025, no loss history yet).\n"
         "Branch (1.8%) and Online (2.4%) are observed. Acquisition cost = marketing, commission and processing.",
         fontsize=9, color="#555555", ha="left", va="bottom", style="italic")
