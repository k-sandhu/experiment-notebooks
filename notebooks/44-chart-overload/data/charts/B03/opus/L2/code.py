import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data.csv", parse_dates=["date"])

# Total orders over the whole test
tot = df.groupby("variant")["orders"].sum()
old_orders, new_orders = tot["control"], tot["new_checkout"]
order_change = (new_orders / old_orders - 1) * 100

# Daily mobile conversion, recomputed from orders and sessions
mob = (df[df["device"] == "mobile"]
       .groupby(["date", "variant"])[["orders", "sessions"]].sum()
       .reset_index())
mob["conv"] = mob["orders"] / mob["sessions"] * 100
piv = mob.pivot(index="date", columns="variant", values="conv")

fix_date = pd.Timestamp("2026-09-26")
pre = mob[mob["date"] < fix_date].groupby("variant")[["orders", "sessions"]].sum()
pre_conv = pre["orders"] / pre["sessions"] * 100
post = mob[mob["date"] >= fix_date].groupby("variant")[["orders", "sessions"]].sum()
post_conv = post["orders"] / post["sessions"] * 100

mobile_share = (df[df["device"] == "mobile"]["sessions"].sum()
                / df["sessions"].sum() * 100)

ACCENT = "#D1495B"
GREY = "#9A9A9A"

fig, ax = plt.subplots(figsize=(10, 6))

# Post-fix window shading
ax.axvspan(fix_date - pd.Timedelta(hours=12), piv.index.max() + pd.Timedelta(hours=12),
           color="#F2F2F2", zorder=0)

ax.plot(piv.index, piv["control"], color=GREY, lw=2.5, marker="o", ms=4, zorder=2)
ax.plot(piv.index, piv["new_checkout"], color=ACCENT, lw=3, marker="o", ms=5, zorder=3)

# Direct line labels
last = piv.index.max()
ax.text(last + pd.Timedelta(hours=18), piv.loc[last, "control"] + 0.12,
        "Old checkout", color=GREY, fontsize=11, fontweight="bold", va="center")
ax.text(last + pd.Timedelta(hours=18), piv.loc[last, "new_checkout"] - 0.12,
        "New checkout", color=ACCENT, fontsize=11, fontweight="bold", va="center")

# Key numbers: average mobile conversion before the fix
ax.annotate(f"Before fix: new {pre_conv['new_checkout']:.2f}% vs old {pre_conv['control']:.2f}%",
            xy=(pd.Timestamp("2026-09-23"), piv.loc["2026-09-23", "new_checkout"]),
            xytext=(pd.Timestamp("2026-09-21"), 0.75),
            fontsize=11, color=ACCENT, fontweight="bold",
            arrowprops=dict(arrowstyle="-", color=ACCENT, lw=1))

# Caveat about the bug fix
ax.text(fix_date + pd.Timedelta(hours=12), 0.25,
        f"Payment-button bug fixed\n26 Sep: new {post_conv['new_checkout']:.2f}%\n"
        f"vs old {post_conv['control']:.2f}%,\nbut only 2 days of data",
        fontsize=9.5, color="#444444", ha="center", va="bottom")

# Outage note
ax.annotate("Payment-provider\noutage (both dipped)",
            xy=(pd.Timestamp("2026-09-20"), piv.loc["2026-09-20", "control"]),
            xytext=(pd.Timestamp("2026-09-20"), 0.3),
            fontsize=9, color="#666666", ha="center",
            arrowprops=dict(arrowstyle="-", color="#AAAAAA", lw=0.8))

ax.set_ylim(0, 3.2)
ax.set_ylabel("Mobile conversion (orders as % of sessions)", fontsize=10)
ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
ax.set_xlim(piv.index.min() - pd.Timedelta(hours=12), last + pd.Timedelta(days=2.2))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}%"))

for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
ax.spines["left"].set_color("#BBBBBB")
ax.spines["bottom"].set_color("#BBBBBB")
ax.tick_params(colors="#555555")
ax.grid(axis="y", color="#E6E6E6", lw=0.8)
ax.set_axisbelow(True)

fig.suptitle("Don't roll out yet: the new checkout lost mobile orders until the 26 Sep bug fix",
             x=0.02, ha="left", fontsize=14.5, fontweight="bold", y=0.97)
ax.set_title(f"Mobile is {mobile_share:.0f}% of sessions, so the new checkout produced "
             f"{abs(order_change):.1f}% fewer orders overall ({new_orders:,} vs {old_orders:,}, "
             f"14 days). Re-test mobile after the fix.",
             loc="left", fontsize=10.5, color="#444444", pad=12)

fig.subplots_adjust(left=0.08, right=0.97, top=0.86, bottom=0.08)
