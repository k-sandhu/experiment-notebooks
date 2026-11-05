import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Aggregate Jan-Sep 2026 by channel (Partner app: from Mar 2026 launch)
df["total_acq_cost"] = df["acquisition_cost_per_loan_usd"] * df["funded_loans"]

g = df.groupby("channel").agg(
    funded_loans=("funded_loans", "sum"),
    funded_value_musd=("funded_value_musd", "sum"),
    total_acq_cost=("total_acq_cost", "sum"),
).reset_index()

g["avg_loan_k"] = g["funded_value_musd"] * 1e6 / g["funded_loans"] / 1e3
g["cost_per_loan"] = g["total_acq_cost"] / g["funded_loans"]
# Decision-relevant normalisation: interest income scales with $ lent, not loan count
g["cost_per_1000"] = g["total_acq_cost"] / (g["funded_value_musd"] * 1e6) * 1000
g["share_value_pct"] = g["funded_value_musd"] / g["funded_value_musd"].sum() * 100

# Cheapest per $1,000 at the top
g = g.sort_values("cost_per_1000", ascending=False).reset_index(drop=True)

broker = g[g["channel"] == "Broker"].iloc[0]
total_value = g["funded_value_musd"].sum()

labels = [f"{r.channel}\navg loan ${r.avg_loan_k:,.0f}k" for r in g.itertuples()]
colors = ["#C0392B" if c == "Broker" else "#7A8A99" for c in g["channel"]]
y = np.arange(len(g))

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6),
    gridspec_kw={"width_ratios": [1.30, 1.0], "wspace": 0.38},
)

# ---- Left: cost per $1,000 funded ----
ax1.barh(y, g["cost_per_1000"], color=colors, height=0.62)
ax1.set_yticks(y, labels, fontsize=11)
ax1.set_xlabel("Acquisition cost per $1,000 funded\n(total cost ÷ total $ lent)", fontsize=10)
ax1.set_title("Cost per $1,000 lent: Broker is 2nd-cheapest",
              fontsize=12, fontweight="bold", loc="left", pad=12)
ax1.set_xlim(0, g["cost_per_1000"].max() * 1.42)
ax1.xaxis.grid(True, color="#D5DBDB", linewidth=0.7)
ax1.set_axisbelow(True)
for yi, r in zip(y, g.itertuples()):
    ax1.text(r.cost_per_1000 + 0.7, yi,
             f"${r.cost_per_1000:,.0f}  (${r.cost_per_loan:,.0f}/loan)",
             va="center", fontsize=10.5,
             fontweight="bold" if r.channel == "Broker" else "normal",
             color="#C0392B" if r.channel == "Broker" else "#222222")

# ---- Right: what closing Broker would lose ----
ax2.barh(y, g["share_value_pct"], color=colors, height=0.62)
ax2.set_yticks(y, g["channel"], fontsize=11)
ax2.set_xlabel(f"Share of ${total_value:,.0f}M funded, Jan-Sep 2026 (%)", fontsize=10)
ax2.set_title("Closing Broker loses ~1/3 of lending",
              fontsize=12, fontweight="bold", loc="left", pad=12)
ax2.set_xlim(0, g["share_value_pct"].max() * 1.48)
ax2.xaxis.grid(True, color="#D5DBDB", linewidth=0.7)
ax2.set_axisbelow(True)
for yi, r in zip(y, g.itertuples()):
    ax2.text(r.share_value_pct + 0.7, yi,
             f"{r.share_value_pct:,.0f}%  (${r.funded_value_musd:,.0f}M)",
             va="center", fontsize=10.5,
             fontweight="bold" if r.channel == "Broker" else "normal",
             color="#C0392B" if r.channel == "Broker" else "#222222")

for ax in (ax1, ax2):
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(labelsize=10)
    for tick, ch in zip(ax.get_yticklabels(), g["channel"]):
        if ch == "Broker":
            tick.set_fontweight("bold")
            tick.set_color("#C0392B")

fig.suptitle(
    "Closing Broker would not fix acquisition costs\n"
    "per dollar lent, Broker is second-cheapest",
    fontsize=16, fontweight="bold", x=0.015, ha="left", y=0.98,
)
fig.text(
    0.015, 0.885,
    f"Broker costs ${broker.cost_per_loan:,.0f}/loan only because its loans average "
    f"${broker.avg_loan_k:,.0f}k (vs $9-20k elsewhere) — yet it supplies "
    f"{broker.share_value_pct:,.0f}% of all dollars lent.",
    fontsize=10.5, color="#333333",
)
fig.text(
    0.015, 0.02,
    "Jan-Sep 2026 totals; Partner app launched Mar 2026.  "
    "Risk caveat: Broker (2.1%) and Partner app (3.0%) 12-month defaults are projections, "
    "not observed history\n(Branch 1.8% and Online 2.4% are actuals) — so cost alone does not prove risk-adjusted profit.",
    fontsize=8, color="#555555",
)

fig.subplots_adjust(left=0.16, right=0.98, top=0.82, bottom=0.16)
