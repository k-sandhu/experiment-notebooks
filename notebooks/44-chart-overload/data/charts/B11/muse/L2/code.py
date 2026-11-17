import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

df = pd.read_csv("data.csv")

df["funded_value_usd"] = df["funded_value_musd"] * 1e6
df["acquisition_total_usd"] = df["funded_loans"] * df["acquisition_cost_per_loan_usd"]

agg = df.groupby("channel").agg(
    funded_value=("funded_value_usd", "sum"),
    acquisition_total=("acquisition_total_usd", "sum"),
    funded_loans=("funded_loans", "sum"),
)
agg["cost_per_1000"] = agg["acquisition_total"] / agg["funded_value"] * 1000
agg["share_pct"] = agg["funded_value"] / agg["funded_value"].sum() * 100
agg["avg_loan"] = agg["funded_value"] / agg["funded_loans"]
agg["cost_per_loan"] = agg["acquisition_total"] / agg["funded_loans"]

broker = agg.loc["Broker"]
online = agg.loc["Online"]

# Sort by cost per $1,000 so the reframing is immediately visible.
agg = agg.sort_values("cost_per_1000", ascending=True)

strong = "#0B5FA5"
grey = "#C2C2C2"
colors = [strong if ch == "Broker" else grey for ch in agg.index]

fig, axes = plt.subplots(
    1, 2, figsize=(10, 6), sharey=True,
    gridspec_kw={"width_ratios": [1, 1], "wspace": 0.08},
)

axes[0].barh(agg.index, agg["cost_per_1000"], color=colors, height=0.58)
axes[1].barh(agg.index, agg["share_pct"], color=colors, height=0.58)

axes[0].set_xlim(0, agg["cost_per_1000"].max() * 1.32)
axes[1].set_xlim(0, agg["share_pct"].max() * 1.42)

axes[0].set_title("Acquisition cost per $1,000 funded", loc="left",
                   fontsize=12, fontweight="bold", pad=10)
axes[1].set_title("Share of funded value, Jan–Sep 2026", loc="left",
                   fontsize=12, fontweight="bold", pad=10)

axes[0].xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x:.0f}"))
axes[1].xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0f}%"))

for ax in axes:
    ax.xaxis.grid(True, color="#E6E6E6", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", labelsize=11, length=0)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#999999")

for label in axes[0].get_yticklabels():
    if label.get_text() == "Broker":
        label.set_fontweight("bold")
        label.set_color(strong)

pos = {ch: i for i, ch in enumerate(agg.index)}

# Only the numbers that carry the message are labelled.
axes[0].text(
    broker["cost_per_1000"] + 0.7, pos["Broker"],
    f"${broker['cost_per_1000']:.0f} per $1,000",
    va="center", fontsize=12, fontweight="bold", color=strong,
)
axes[0].text(
    online["cost_per_1000"] + 0.7, pos["Online"],
    f"${online['cost_per_1000']:.0f}",
    va="center", fontsize=11, color="#555555",
)
axes[1].text(
    broker["share_pct"] + 0.7, pos["Broker"],
    f"{broker['share_pct']:.0f}%  (${broker['funded_value'] / 1e6:.0f}m)",
    va="center", fontsize=12, fontweight="bold", color=strong,
)

fig.text(
    0.06, 0.97,
    f"Broker is cheap per dollar lent — closing it\n"
    f"would remove {broker['share_pct']:.0f}% of funded value",
    ha="left", va="top", fontsize=17, fontweight="bold", color="#111111",
)
fig.text(
    0.06, 0.875,
    f"Its ${broker['cost_per_loan']:,.0f} cost per loan reflects loans averaging "
    f"${broker['avg_loan']:,.0f}, versus ${online['avg_loan']:,.0f} online.",
    ha="left", va="top", fontsize=11.5, color="#333333",
)
fig.text(
    0.06, 0.045,
    "Acquisition cost only — excludes credit losses. Broker's 2.1% 12-month default rate is projected, not yet observed.\n"
    "Partner app launched Mar 2026, so its 9-month value share is not comparable.",
    ha="left", va="bottom", fontsize=8.5, color="#666666",
)

fig.subplots_adjust(left=0.14, right=0.97, top=0.79, bottom=0.13)
