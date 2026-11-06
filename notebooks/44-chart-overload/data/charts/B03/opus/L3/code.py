import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data.csv", parse_dates=["date"])

ACCENT = "#C8442F"   # new checkout
GREY = "#9A9A9A"     # old checkout (context)
DARK = "#333333"

# ---- Aggregates ---------------------------------------------------------
agg = df.groupby(["device", "variant"])[["sessions", "orders"]].sum()
agg["conv"] = agg["orders"] / agg["sessions"] * 100

tot = df.groupby("variant")["orders"].sum()
order_change = (tot["new_checkout"] / tot["control"] - 1) * 100
mobile_share = df.loc[df.device == "mobile", "sessions"].sum() / df["sessions"].sum() * 100

mob = df[df.device == "mobile"].copy()
daily = mob.pivot_table(index="date", columns="variant", values=["orders", "sessions"], aggfunc="sum")
daily_conv = daily["orders"] / daily["sessions"] * 100

post = mob[mob.date >= "2026-09-26"].groupby("variant")[["orders", "sessions"]].sum()
post_conv = post["orders"] / post["sessions"] * 100

# ---- Figure -------------------------------------------------------------
fig = plt.figure(figsize=(10, 6))
gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.6], left=0.07, right=0.97,
                      top=0.76, bottom=0.12, wspace=0.28)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])

fig.text(0.02, 0.95,
         f"Don't roll out yet: the new checkout lost {abs(order_change):.1f}% of orders "
         "because mobile conversion fell",
         fontsize=14.5, fontweight="bold", color=DARK, ha="left")
fig.text(0.02, 0.885,
         f"Desktop improved, but mobile is {mobile_share:.0f}% of sessions "
         f"({tot['new_checkout']:,} vs {tot['control']:,} orders over 14 days). "
         "A phone payment-button bug was fixed on 26 Sep;\n"
         "since then mobile looks close to the old checkout, "
         "but two days is too short to judge. Keep testing on mobile.",
         fontsize=10, color="#555555", ha="left", va="top")

# ---- Left panel: conversion by device ----------------------------------
devices = ["mobile", "desktop"]
x = np.arange(len(devices))
w = 0.36
old_vals = [agg.loc[(d, "control"), "conv"] for d in devices]
new_vals = [agg.loc[(d, "new_checkout"), "conv"] for d in devices]

b_old = ax1.bar(x - w / 2, old_vals, w, color=GREY)
b_new = ax1.bar(x + w / 2, new_vals, w, color=ACCENT)

for bars, vals, col in [(b_old, old_vals, "#666666"), (b_new, new_vals, ACCENT)]:
    for b, v in zip(bars, vals):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.06, f"{v:.2f}%",
                 ha="center", va="bottom", fontsize=10.5, fontweight="bold", color=col)

# direct labels instead of a legend
ax1.text(x[0] - w / 2, 0.12, "Old", ha="center", va="bottom", color="white", fontsize=10, fontweight="bold")
ax1.text(x[0] + w / 2, 0.12, "New", ha="center", va="bottom", color="white", fontsize=10, fontweight="bold")

ax1.set_xticks(x)
ax1.set_xticklabels([f"Mobile\n({mobile_share:.0f}% of sessions)", "Desktop"], fontsize=10.5)
ax1.set_ylim(0, 4.2)
ax1.set_ylabel("Conversion (% of sessions)", fontsize=10)
ax1.set_title("Conversion over 14 days", fontsize=11.5, loc="left", color=DARK)

# ---- Right panel: daily mobile conversion ------------------------------
dates = daily_conv.index
ax2.axvspan(pd.Timestamp("2026-09-25 12:00"), pd.Timestamp("2026-09-27 12:00"),
            color=ACCENT, alpha=0.08, lw=0)

ax2.plot(dates, daily_conv["control"], color=GREY, lw=2.2, marker="o", ms=4)
ax2.plot(dates, daily_conv["new_checkout"], color=ACCENT, lw=2.8, marker="o", ms=4.5)

lab_day = pd.Timestamp("2026-09-22")
ax2.text(lab_day, daily_conv.loc[lab_day, "control"] + 0.17, "Old checkout",
         color="#666666", fontsize=10.5, fontweight="bold", ha="center")
ax2.text(lab_day, daily_conv.loc[lab_day, "new_checkout"] - 0.33, "New checkout",
         color=ACCENT, fontsize=10.5, fontweight="bold", ha="center")

ax2.annotate("Bug fixed 26 Sep\n"
             f"New {post_conv['new_checkout']:.2f}% vs old {post_conv['control']:.2f}%\n"
             "only 2 days of data",
             xy=(pd.Timestamp("2026-09-26 12:00"), 2.65), ha="right", va="bottom",
             xytext=(pd.Timestamp("2026-09-25 06:00"), 2.72),
             fontsize=9.5, color=ACCENT, fontweight="bold",
             arrowprops=dict(arrowstyle="-", color=ACCENT, lw=1))

out_day = pd.Timestamp("2026-09-20")
ax2.text(out_day, 0.82, "payment\noutage", ha="center", va="top", fontsize=8, color="#888888")

ax2.set_ylim(0, 3.2)
ax2.set_xlim(dates.min() - pd.Timedelta(hours=12), dates.max() + pd.Timedelta(hours=12))
ax2.set_ylabel("Mobile conversion (% of sessions)", fontsize=10)
ax2.set_title("Mobile conversion by day", fontsize=11.5, loc="left", color=DARK)
ax2.xaxis.set_major_locator(mdates.DayLocator(interval=2))
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))

for ax in (ax1, ax2):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#BBBBBB")
    ax.spines["bottom"].set_color("#BBBBBB")
    ax.tick_params(colors="#555555", labelsize=9.5)
    ax.yaxis.grid(True, color="#EEEEEE", lw=0.8)
    ax.set_axisbelow(True)

fig.text(0.02, 0.025, "A/B test, 14–27 Sep 2026, sessions split 50/50. "
         "Tablet (3% of sessions) not shown; included in order totals.",
         fontsize=8.5, color="#888888", ha="left")
