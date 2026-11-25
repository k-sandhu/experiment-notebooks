import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")
df["month_dt"] = pd.to_datetime(df["month"] + "-01")

channels = ["Branch", "Online", "Broker", "Partner app"]
colors = {"Branch": "#4C72B0", "Online": "#55A868", "Broker": "#C44E52", "Partner app": "#8172B2"}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.25, 1]})

# Left panel: monthly funded value by channel
pv = df.pivot(index="month_dt", columns="channel", values="funded_value_musd")
for ch in channels:
    s = pv[ch].dropna()
    ax1.plot(s.index, s.values, marker="o", ms=4, lw=2, color=colors[ch])
    ax1.annotate(f"{ch}\n${s.iloc[-1]:.1f}M", xy=(s.index[-1], s.values[-1]),
                 xytext=(6, 0), textcoords="offset points", va="center",
                 fontsize=9, color=colors[ch], fontweight="bold")

partner_start = pv["Partner app"].first_valid_index()
ax1.annotate("Partner app\nlaunched", xy=(partner_start, pv.loc[partner_start, "Partner app"]),
             xytext=(0, 22), textcoords="offset points", ha="center", fontsize=8,
             color=colors["Partner app"], arrowprops=dict(arrowstyle="-", color=colors["Partner app"], lw=0.8))

ax1.set_ylim(0, 16)
ax1.set_ylabel("Funded value, $ millions")
ax1.set_title("Funded value per month", loc="left", fontsize=11)
months = pv.index
ax1.set_xticks(months)
ax1.set_xticklabels([m.strftime("%b") for m in months])
ax1.set_xlim(months[0] - pd.Timedelta(days=10), months[-1] + pd.Timedelta(days=75))
ax1.grid(axis="y", alpha=0.3)
for sp in ["top", "right"]:
    ax1.spines[sp].set_visible(False)

# Right panel: acquisition cost per $100 lent (Jan–Sep totals)
df["total_cost"] = df["acquisition_cost_per_loan_usd"] * df["funded_loans"]
agg = df.groupby("channel").agg(total_cost=("total_cost", "sum"),
                                value=("funded_value_musd", "sum"),
                                loans=("funded_loans", "sum"))
agg["cost_per_100"] = agg["total_cost"] / (agg["value"] * 1e6) * 100
agg["cost_per_loan"] = agg["total_cost"] / agg["loans"]
agg["avg_loan_k"] = agg["value"] * 1e3 / agg["loans"]
agg = agg.loc[channels].sort_values("cost_per_100")

y = np.arange(len(agg))
ax2.barh(y, agg["cost_per_100"], color=[colors[c] for c in agg.index], height=0.6)
for i, (ch, r) in enumerate(agg.iterrows()):
    ax2.text(r["cost_per_100"] + 0.06, i, f"${r['cost_per_100']:.2f}",
             va="center", fontsize=10, fontweight="bold")
    ax2.text(0.08, i - 0.42,
             f"${r['cost_per_loan']:,.0f} per loan · avg loan ${r['avg_loan_k']:.0f}k",
             va="center", fontsize=8, color="#444444")
ax2.set_yticks(y)
ax2.set_yticklabels(agg.index)
ax2.set_xlim(0, agg["cost_per_100"].max() * 1.25)
ax2.set_ylim(-0.75, len(agg) - 0.5)
ax2.set_xlabel("Acquisition cost per $100 lent, US dollars")
ax2.set_title("Acquisition cost per $100 lent, Jan–Sep", loc="left", fontsize=11)
ax2.grid(axis="x", alpha=0.3)
for sp in ["top", "right"]:
    ax2.spines[sp].set_visible(False)

fig.suptitle("Broker costs most per loan, but per dollar lent branches are the costliest channel",
             fontsize=13, fontweight="bold", x=0.02, ha="left")
fig.text(0.02, 0.01,
         "Acquisition cost = marketing, commission and processing. Partner app launched March 2026. "
         "Total funded value Jan–Sep 2026: ${:.0f}M.".format(df["funded_value_musd"].sum()),
         fontsize=8, color="#555555")
fig.tight_layout(rect=[0, 0.03, 1, 0.94])
