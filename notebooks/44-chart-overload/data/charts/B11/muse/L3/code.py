import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

df["cost_total"] = df["acquisition_cost_per_loan_usd"] * df["funded_loans"]

agg = df.groupby("channel").agg(
    applications=("applications", "sum"),
    funded_loans=("funded_loans", "sum"),
    funded_value=("funded_value_musd", "sum"),
    cost_total=("cost_total", "sum"),
)
agg["cost_per_loan"] = agg["cost_total"] / agg["funded_loans"]
agg["avg_loan_k"] = agg["funded_value"] * 1000 / agg["funded_loans"]
agg = agg.sort_values("cost_per_loan", ascending=False)

broker_app_share = 100 * agg.loc["Broker", "applications"] / agg["applications"].sum()
broker_val_share = 100 * agg.loc["Broker", "funded_value"] / agg["funded_value"].sum()
broker_avg_k = agg.loc["Broker", "avg_loan_k"]
others = agg.drop(index="Broker")["avg_loan_k"]
broker_default = df.loc[df["channel"] == "Broker", "default_rate_12m_pct"].iloc[0]

STRONG = "#C1272D"
GREY = "#B8B8B8"
DARK = "#333333"

fig, axes = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.35, 1]}
)
fig.subplots_adjust(left=0.08, right=0.97, top=0.78, bottom=0.19, wspace=0.30)

fig.text(
    0.02, 0.96,
    f"Broker costs most per loan, but closing it\nwould remove {broker_val_share:.0f}% of funded value",
    fontsize=17, fontweight="bold", ha="left", va="top", color="#111111",
)

# Left: acquisition cost per funded loan
ax = axes[0]
colors = [STRONG if c == "Broker" else GREY for c in agg.index]
bars = ax.bar(agg.index, agg["cost_per_loan"], color=colors, width=0.62)
ax.set_title("Acquisition cost per funded loan", fontsize=12, color=DARK)
ax.set_ylabel("$ per funded loan", fontsize=11)
ax.set_ylim(0, agg["cost_per_loan"].max() * 1.22)
ax.grid(axis="y", color="#DDDDDD", linewidth=0.7)
ax.set_axisbelow(True)
ax.tick_params(axis="x", labelsize=10)
ax.tick_params(axis="y", labelsize=10)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for bar, channel in zip(bars, agg.index):
    is_broker = channel == "Broker"
    ax.text(
        bar.get_x() + bar.get_width() / 2, bar.get_height() + 35,
        f"${bar.get_height():,.0f}",
        ha="center", va="bottom",
        fontsize=12 if is_broker else 10,
        fontweight="bold" if is_broker else "normal",
        color=STRONG if is_broker else DARK,
    )

# Right: what Broker contributes
ax = axes[1]
labels = ["Share of\napplications", "Share of\nfunded value"]
values = [broker_app_share, broker_val_share]
bars = ax.bar(labels, values, color=[GREY, STRONG], width=0.58)
ax.set_title("What Broker brings, Jan-Sep 2026", fontsize=12, color=DARK)
ax.set_ylabel("Share of total (%)", fontsize=11)
ax.set_ylim(0, max(values) * 1.5)
ax.grid(axis="y", color="#DDDDDD", linewidth=0.7)
ax.set_axisbelow(True)
ax.tick_params(axis="x", labelsize=10)
ax.tick_params(axis="y", labelsize=10)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for bar in bars:
    ax.text(
        bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
        f"{bar.get_height():.0f}%",
        ha="center", va="bottom", fontsize=12,
        fontweight="bold", color=DARK,
    )
ax.text(
    0.5, 0.82,
    f"Avg Broker loan: ${broker_avg_k:.0f}k\nOther channels: ${others.min():.0f}k-${others.max():.0f}k",
    transform=ax.transAxes, ha="center", va="center", fontsize=10.5, color=DARK,
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#F2F2F2", edgecolor="none"),
)

fig.text(
    0.02, 0.03,
    f"Caveat: Broker's {broker_default:.1f}% 12-month default rate is projected, not observed - "
    "Broker loans began in Nov 2025.\nPartner app's default rate is also projected.",
    fontsize=9, ha="left", va="bottom", color="#555555",
)
