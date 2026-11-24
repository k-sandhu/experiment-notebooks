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
rel_drop = (1 - pre_conv["new_checkout"] / pre_conv["control"]) * 100

mobile_share = (df[df["device"] == "mobile"]["sessions"].sum()
                / df["sessions"].sum() * 100)

ACCENT = "#D1495B"
GREY = "#9A9A9A"
TEXT = "#444444"

fig, ax = plt.subplots(figsize=(10, 6))

first, last = piv.index.min(), piv.index.max()
half = pd.Timedelta(hours=12)

# Post-fix window shading
ax.axvspan(fix_date - half, last + half, color="#EFEFEF", zorder=0, lw=0)

# Shade the pre-fix gap (mobile orders lost)
pre_idx = piv.index[piv.index < fix_date]
ax.fill_between(pre_idx, piv.loc[pre_idx, "new_checkout"], piv.loc[pre_idx, "control"],
                where=piv.loc[pre_idx, "control"] >= piv.loc[pre_idx, "new_checkout"],
                color=ACCENT, alpha=0.12, lw=0, zorder=1, interpolate=True)

ax.plot(piv.index, piv["control"], color=GREY, lw=2.5, marker="o", ms=4, zorder=2)
ax.plot(piv.index, piv["new_checkout"], color=ACCENT, lw=3, marker="o", ms=5, zorder=3)

# Direct line labels
ax.text(last + pd.Timedelta(hours=16), piv.loc[last, "control"] + 0.12,
        "Old checkout", color=GREY, fontsize=11, fontweight="bold", va="center")
ax.text(last + pd.Timedelta(hours=16), piv.loc[last, "new_checkout"] - 0.12,
        "New checkout", color=ACCENT, fontsize=11, fontweight="bold", va="center")

# Key message: pre-fix mobile conversion
ax.text(first, 1.28,
        f"Before fix (14–25 Sep): new {pre_conv['new_checkout']:.2f}% vs old "
        f"{pre_conv['control']:.2f}%",
        color=ACCENT, fontsize=11.5, fontweight="bold", ha="left", va="top")
ax.text(first, 1.10,
        f"about {rel_drop:.0f}% fewer mobile orders per session",
        color=ACCENT, fontsize=10, ha="left", va="top")

# Post-fix caveat
mid_post = fix_date + half
ax.text(mid_post, 3.12, "Payment-button\nbug fixed 26 Sep",
        fontsize=9.5, color=TEXT, fontweight="bold", ha="center", va="top")
ax.text(mid_post, 1.62,
        f"new {post_conv['new_checkout']:.2f}%\nvs old {post_conv['control']:.2f}%\n"
        f"only 2 days:\ntoo early to judge",
        fontsize=9, color=TEXT, ha="center", va="top", linespacing=1.3)

# Outage note (context only)
ax.text(pd.Timestamp("2026-09-20"), 0.92, "Payment-provider outage\n(both dipped)",
        fontsize=8.5, color="#888888", ha="center", va="top")

ax.set_ylim(0, 3.2)
ax.set_ylabel("Mobile conversion (orders as % of sessions)", fontsize=10, color=TEXT)
ax.set_xticks(piv.index[1::2])
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
ax.set_xlim(first - half, last + pd.Timedelta(days=2.0))
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
             loc="left", fontsize=10.5, color=TEXT, pad=12)

fig.subplots_adjust(left=0.08, right=0.97, top=0.86, bottom=0.08)
