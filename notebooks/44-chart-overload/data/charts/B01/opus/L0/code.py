import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data.csv")
df["date"] = pd.to_datetime(df["month"] + "-01")

plans = ["Couple", "Family", "Single", "Vegetarian"]
FAMILY = "#c8423b"
GREYS = {"Couple": "#7a7a7a", "Single": "#a9a9a9", "Vegetarian": "#8f9aa3"}
price_change = pd.Timestamp("2026-04-01")

def color(p):
    return FAMILY if p == "Family" else GREYS[p]

def dodge(values, min_gap):
    """Spread label y-positions apart so they don't overlap."""
    order = np.argsort(values)
    pos = np.array(values, dtype=float)
    adj = pos.copy()
    for i in range(1, len(order)):
        prev, cur = order[i - 1], order[i]
        if adj[cur] - adj[prev] < min_gap:
            adj[cur] = adj[prev] + min_gap
    return adj

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.15, 1]}
)

# Panel 1: cancellation rate. September is left out because it covers only 1-14 Sept.
full = df[df["month"] <= "2026-08"]

for p in plans:
    d = full[full["plan"] == p].sort_values("date")
    ax1.plot(d["date"], d["cancellation_rate_pct"], color=color(p),
             lw=2.6 if p == "Family" else 1.6, zorder=3 if p == "Family" else 2)

last1 = full[full["month"] == "2026-08"].set_index("plan")["cancellation_rate_pct"]
ys = dodge([last1[p] for p in plans], 0.32)
for p, y in zip(plans, ys):
    ax1.text(pd.Timestamp("2026-08-12"), y, p, color=color(p), va="center",
             fontsize=9.5, fontweight="bold" if p == "Family" else "normal")

ax1.axvline(price_change, color=FAMILY, ls="--", lw=1, alpha=0.7)
ax1.text(price_change + pd.Timedelta(days=4), 7.35,
         "Family price\n$79 → $89/week", color=FAMILY, fontsize=9, va="top")

fam = full[full["plan"] == "Family"]
pre = fam[fam["date"] < price_change]["cancellation_rate_pct"].mean()
post = fam[fam["date"] >= price_change]["cancellation_rate_pct"].mean()
ax1.text(pd.Timestamp("2025-12-20"), pre + 0.45, f"avg {pre:.1f}%",
         color=FAMILY, fontsize=9, ha="center")
ax1.text(pd.Timestamp("2026-06-01"), post - 0.75, f"avg {post:.1f}%",
         color=FAMILY, fontsize=9, ha="center")

ax1.set_ylim(0, 7.5)
ax1.set_xlim(pd.Timestamp("2025-09-20"), pd.Timestamp("2026-10-10"))
ax1.set_ylabel("Cancellations as % of active subscribers")
ax1.set_title("Monthly cancellation rate (Oct 2025 – Aug 2026)", fontsize=11, loc="left")

# Panel 2: active subscribers at start of month (the September start count is complete)
for p in plans:
    d = df[df["plan"] == p].sort_values("date")
    ax2.plot(d["date"], d["active_subscribers"] / 1000, color=color(p),
             lw=2.6 if p == "Family" else 1.6, zorder=3 if p == "Family" else 2)

last2 = df[df["month"] == "2026-09"].set_index("plan")["active_subscribers"] / 1000
ys2 = dodge([last2[p] for p in plans], 1.2)
for p, y in zip(plans, ys2):
    ax2.text(pd.Timestamp("2026-09-12"), y, f"{p} {last2[p]:.1f}k", color=color(p),
             va="center", fontsize=9.5, fontweight="bold" if p == "Family" else "normal")

ax2.axvline(price_change, color=FAMILY, ls="--", lw=1, alpha=0.7)
ax2.annotate("Family: −19%\nsince April", xy=(pd.Timestamp("2026-07-01"), 12.7),
             xytext=(pd.Timestamp("2026-04-20"), 9.0), color=FAMILY, fontsize=9,
             arrowprops=dict(arrowstyle="-", color=FAMILY, lw=0.8))

ax2.set_ylim(0, 24)
ax2.set_xlim(pd.Timestamp("2025-09-20"), pd.Timestamp("2026-12-15"))
ax2.set_ylabel("Active subscribers (thousands)")
ax2.set_title("Active subscribers, start of month", fontsize=11, loc="left")

for ax in (ax1, ax2):
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[10, 1, 4, 7]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e6e6e6", lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=9)

fig.suptitle("Family plan cancellations doubled after the April price rise, "
             "and the plan began shrinking", fontsize=13, fontweight="bold",
             x=0.02, ha="left")
fig.text(0.02, 0.015,
         "September 2026 cancellation rate is omitted: that month's data covers 1–14 Sept only. "
         "Figures exclude gift subscriptions (about 3% of orders).",
         fontsize=8, color="#555555", ha="left")

fig.tight_layout(rect=[0, 0.04, 1, 0.95])
