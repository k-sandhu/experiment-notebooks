import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv("data.csv")
df["date"] = pd.to_datetime(df["month"], format="%Y-%m")

# ------------------------------------------------------------
# Figure setup
# ------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(
    1, 2,
    figsize=(10, 6),
    gridspec_kw={"width_ratios": [1.45, 1]}
)

fig.suptitle(
    "Family cancellations doubled after the April price rise;\n"
    "Family lost 19% of subscribers while other plans grew.",
    fontsize=13.5,
    fontweight="bold",
    y=0.97
)

fig.subplots_adjust(top=0.82, bottom=0.14, left=0.08, right=0.96, wspace=0.35)

# ------------------------------------------------------------
# Left panel: Family cancellation rate
# ------------------------------------------------------------
family = df[df["plan"] == "Family"].sort_values("date").reset_index(drop=True)

x = np.arange(len(family))
rates = family["cancellation_rate_pct"].values

months = family["date"].dt.strftime("%b").tolist()
months[3] = "Jan\n'26"  # January 2026 marker

pre_idx = np.arange(0, 6)      # Oct 2025 - Mar 2026
post_idx = np.arange(6, 11)    # Apr 2026 - Aug 2026
sep_idx = 11                   # Sep 2026

# Pre-rise context in grey
ax1.bar(pre_idx, rates[pre_idx], color="#bdbdbd", width=0.82)

# Post-rise in strong color
ax1.bar(post_idx, rates[post_idx], color="#c0392b", width=0.82)

# September shown separately because it is only a partial month
ax1.bar(
    [sep_idx], [rates[sep_idx]],
    color="white",
    edgecolor="#c0392b",
    hatch="////",
    linewidth=1.2,
    width=0.82
)

# Averages before and after the price rise
pre_avg = rates[:6].mean()
post_avg = rates[6:11].mean()

ax1.hlines(pre_avg, -0.5, 5.5, color="#7f7f7f", linestyle="--", linewidth=1.2)
ax1.hlines(post_avg, 5.5, 10.5, color="#c0392b", linestyle="--", linewidth=1.4)

ax1.text(
    2.5, pre_avg + 0.35,
    f"Oct–Mar avg {pre_avg:.1f}%",
    ha="center", va="bottom", fontsize=9, color="#555555"
)
ax1.text(
    8.0, post_avg + 0.35,
    f"Apr–Aug avg {post_avg:.1f}%",
    ha="center", va="bottom", fontsize=9, color="#c0392b", fontweight="bold"
)

# Price increase marker
ax1.axvline(5.5, color="black", linestyle=":", linewidth=1.2)
ax1.text(
    5.6, 7.8,
    "$79 → $89/wk\nfrom 1 Apr",
    fontsize=8.5, va="top", ha="left"
)

# September caveat
ax1.annotate(
    "Sep 1–14 only;\nnot a recovery",
    xy=(11, rates[11]),
    xytext=(9.4, 4.7),
    fontsize=8,
    ha="center",
    arrowprops=dict(arrowstyle="-|>", color="black", lw=0.8)
)

ax1.set_title("Family monthly cancellation rate", fontsize=11, loc="left")
ax1.set_ylabel("Cancellations (% of active subscribers)", fontsize=9)
ax1.set_xticks(x)
ax1.set_xticklabels(months, fontsize=8)
ax1.set_ylim(0, 8.4)
ax1.set_xlim(-0.6, 11.6)
ax1.grid(axis="y", color="#e5e5e5", linewidth=0.7)
ax1.set_axisbelow(True)

for spine in ["top", "right"]:
    ax1.spines[spine].set_visible(False)

# ------------------------------------------------------------
# Right panel: active subscribers indexed to April 2026
# ------------------------------------------------------------
start = pd.Timestamp("2026-04-01")
end = pd.Timestamp("2026-09-01")

sub = df[(df["date"] >= start) & (df["date"] <= end)].copy()
piv = sub.pivot(index="date", columns="plan", values="active_subscribers").sort_index()
idx = piv / piv.iloc[0] * 100.0

# Context plans in grey
for plan in ["Single", "Couple", "Vegetarian"]:
    ax2.plot(
        idx.index, idx[plan],
        color="#9e9e9e",
        linewidth=1.5,
        alpha=0.85,
        marker="o",
        markersize=3
    )

# Family in strong color
ax2.plot(
    idx.index, idx["Family"],
    color="#c0392b",
    linewidth=3,
    marker="o",
    markersize=5
)

# Direct labels at the end of each line
last_date = idx.index[-1]
offsets = {"Family": 4, "Single": 1, "Couple": -2, "Vegetarian": 2}

for plan in ["Family", "Single", "Couple", "Vegetarian"]:
    val = idx[plan].iloc[-1]
    color = "#c0392b" if plan == "Family" else "#6f6f6f"
    weight = "bold" if plan == "Family" else "normal"
    ax2.annotate(
        f"{plan} {val:.0f}",
        xy=(last_date, val),
        xytext=(4, offsets[plan]),
        textcoords="offset points",
        fontsize=9 if plan == "Family" else 8,
        color=color,
        fontweight=weight,
        va="center",
        ha="left"
    )

# Reference line at April 2026 = 100
ax2.axhline(100, color="#bdbdbd", linestyle="--", linewidth=0.8)

ax2.set_title("Active subscribers indexed to Apr 2026 = 100", fontsize=11, loc="left")
ax2.set_ylabel("Active subscribers (Apr 2026 = 100)", fontsize=9)
ax2.set_ylim(75, 118)
ax2.set_yticks([80, 90, 100, 110])
ax2.set_xlim(pd.Timestamp("2026-03-25"), pd.Timestamp("2026-09-25"))
ax2.set_xticks(piv.index)
ax2.set_xticklabels([d.strftime("%b") for d in piv.index], fontsize=8)
ax2.grid(axis="y", color="#e5e5e5", linewidth=0.7)
ax2.set_axisbelow(True)

for spine in ["top", "right"]:
    ax2.spines[spine].set_visible(False)
