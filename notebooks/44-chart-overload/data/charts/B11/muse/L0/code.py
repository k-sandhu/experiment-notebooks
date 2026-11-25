import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

df = pd.read_csv("data.csv", parse_dates=["month"])
df = df.sort_values("month")

channels = ["Branch", "Online", "Broker", "Partner app"]
colors = {
    "Branch": "#4C72B0",
    "Online": "#DD8452",
    "Broker": "#55A868",
    "Partner app": "#C44E52",
}

# Monthly funded value by channel (for the stacked columns)
monthly = (
    df.pivot_table(index="month", columns="channel",
                   values="funded_value_musd", aggfunc="sum")
      .reindex(columns=channels)
      .sort_index()
)
monthly_filled = monthly.fillna(0)  # only for stacking totals; Partner app did not exist Jan-Feb
month_labels = monthly.index.strftime("%b")
totals = monthly_filled.sum(axis=1)

# Whole-period channel totals and shares
summary = df.groupby("channel").agg(
    applications=("applications", "sum"),
    funded_loans=("funded_loans", "sum"),
    funded_value_musd=("funded_value_musd", "sum"),
).reindex(channels)
summary["app_share"] = 100 * summary["applications"] / summary["applications"].sum()
summary["value_share"] = 100 * summary["funded_value_musd"] / summary["funded_value_musd"].sum()
# Weighted average loan size ($k): $m -> $k is x1000
summary["avg_loan_k"] = summary["funded_value_musd"] * 1000 / summary["funded_loans"]
summary["gap"] = summary["value_share"] - summary["app_share"]
summary = summary.sort_values("gap", ascending=False)  # Broker at top after invert below

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.55, 1.0]}
)

# --- Left: monthly funded value, stacked by channel ---
x = np.arange(len(monthly))
bottom = np.zeros(len(monthly))
for ch in channels:
    vals = monthly_filled[ch].to_numpy()
    ax1.bar(x, vals, bottom=bottom, color=colors[ch], label=ch,
            edgecolor="white", linewidth=0.6, width=0.72)
    bottom += vals

for xi, tot in zip(x, totals):
    ax1.text(xi, tot + 0.7, f"{tot:.0f}", ha="center", va="bottom", fontsize=8)

peak_i = int(np.argmax(totals.to_numpy()))
ax1.annotate(
    f"March peak: ${totals.iloc[peak_i]:.0f}m",
    xy=(x[peak_i], totals.iloc[peak_i]),
    xytext=(x[peak_i] + 0.4, totals.iloc[peak_i] + 4.5),
    fontsize=8.5,
    arrowprops=dict(arrowstyle="-", color="black", lw=0.8),
)
ax1.axvline(1.5, color="grey", linestyle="--", linewidth=0.8)
ax1.text(1.58, totals.max() * 0.35, "Partner app\nlaunches\nMar 2026",
         fontsize=7.5, va="center", color="#333333")

ax1.set_xticks(x)
ax1.set_xticklabels(month_labels)
ax1.set_xlim(-0.6, len(monthly) - 0.4)
ax1.set_ylim(0, totals.max() * 1.22)
ax1.set_ylabel("Funded value ($ millions per month)")
ax1.set_title("Monthly funded value by channel", fontsize=11, loc="left")
ax1.grid(axis="y", alpha=0.25)
ax1.set_axisbelow(True)
ax1.legend(frameon=False, fontsize=8.5, loc="upper left", ncol=2)
for spine in ["top", "right"]:
    ax1.spines[spine].set_visible(False)

# --- Right: share of applications vs share of funded value ---
y = np.arange(len(summary))
h = 0.36
bars_app = ax2.barh(y - h / 2, summary["app_share"], height=h,
                    color="#C9C9C9", edgecolor="white", label="Share of applications")
bars_val = ax2.barh(y + h / 2, summary["value_share"], height=h,
                    color="#2F5597", edgecolor="white", label="Share of funded value")

for bars in (bars_app, bars_val):
    for bar in bars:
        w = bar.get_width()
        ax2.text(w + 0.7, bar.get_y() + bar.get_height() / 2,
                 f"{w:.0f}%", va="center", ha="left", fontsize=8.5)

ax2.set_yticks(y)
ax2.set_yticklabels(
    [f"{ch}\n(avg loan ${summary.loc[ch, 'avg_loan_k']:.0f}k)" for ch in summary.index],
    fontsize=8.5,
)
ax2.invert_yaxis()
ax2.set_xlim(0, max(summary["app_share"].max(), summary["value_share"].max()) * 1.22)
ax2.set_xlabel("Share of Jan-Sep 2026 total (%)")
ax2.set_title("Applications vs funded value\n(same totals, different loan sizes)",
              fontsize=11, loc="left")
ax2.grid(axis="x", alpha=0.25)
ax2.set_axisbelow(True)
ax2.legend(
    handles=[Patch(facecolor="#C9C9C9", label="Share of applications"),
             Patch(facecolor="#2F5597", label="Share of funded value")],
    frameon=False, fontsize=8.5, loc="lower right",
)
for spine in ["top", "right"]:
    ax2.spines[spine].set_visible(False)

total_value = df["funded_value_musd"].sum()
fig.suptitle("Broker delivers about a third of funded value from a sixth of applications",
             fontsize=13, fontweight="bold", x=0.01, ha="left")
fig.text(
    0.01, 0.01,
    f"Note: Partner app launched in March 2026, so it is absent (not zero demand) in Jan-Feb and its "
    f"period shares cover Mar-Sep only.\n"
    f"Total funded Jan-Sep 2026: ${total_value:.0f} million. Average loan size explains the gap between "
    f"application and value shares.",
    fontsize=7.5, color="#444444", va="bottom",
)
fig.tight_layout(rect=[0, 0.07, 1, 0.94])
