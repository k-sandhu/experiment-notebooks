import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

df = pd.read_csv("data.csv", parse_dates=["date"])

RED = "#C1272D"
DARK = "#3F3F3F"
MID = "#8A8A8A"
LIGHT = "#C9C9C9"

# --- Aggregates needed for the decision (tablet excluded from main bars) ---
agg = (
    df[df["device"].isin(["mobile", "desktop"])]
    .groupby(["device", "variant"])[["sessions", "orders"]]
    .sum()
)
conv = (100 * agg["orders"] / agg["sessions"]).unstack()

mobile_old = conv.loc["mobile", "control"]
mobile_new = conv.loc["mobile", "new_checkout"]
desktop_old = conv.loc["desktop", "control"]
desktop_new = conv.loc["desktop", "new_checkout"]

mobile_share = 100 * df[df["device"] == "mobile"]["sessions"].sum() / df["sessions"].sum()
total_orders = df.groupby("variant")["orders"].sum()
order_change = 100 * (total_orders["new_checkout"] - total_orders["control"]) / total_orders["control"]

post_fix = df[
    (df["device"] == "mobile")
    & (df["variant"] == "new_checkout")
    & (df["date"] >= "2026-09-26")
]
post_fix_conv = 100 * post_fix["orders"].sum() / post_fix["sessions"].sum()

mobile_daily = (
    df[df["device"] == "mobile"]
    .pivot(index="date", columns="variant", values="conversion_pct")
    .sort_index()
)

# --- Figure ---
fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.0, 1.45], "wspace": 0.28}
)
fig.patch.set_facecolor("white")

fig.text(
    0.06, 0.95,
    "Hold the rollout: new checkout cut total orders by 6.5%, driven by mobile",
    fontsize=16, weight="bold", color=DARK, va="top", ha="left",
)
fig.text(
    0.06, 0.895,
    "Desktop improved, but mobile is 68% of sessions. Post-bug-fix recovery is only 2 days — too early to judge.",
    fontsize=10.5, color=MID, va="top", ha="left",
)

# --- Left panel: conversion by device ---
devices = ["Mobile\n68% of sessions", "Desktop"]
old_vals = [mobile_old, desktop_old]
new_vals = [mobile_new, desktop_new]
x = np.arange(len(devices))
w = 0.34

ax1.bar(x - w / 2, old_vals, width=w, color=LIGHT, edgecolor="none")
ax1.bar(x[0] + w / 2, new_vals[0], width=w, color=RED, edgecolor="none")
ax1.bar(x[1] + w / 2, new_vals[1], width=w, color=DARK, edgecolor="none")

for xi, v in zip(x - w / 2, old_vals):
    ax1.text(xi, v + 0.09, f"Old\n{v:.2f}%", ha="center", va="bottom", fontsize=9, color=MID, linespacing=1.1)
ax1.text(x[0] + w / 2, new_vals[0] + 0.09, f"New\n{new_vals[0]:.2f}%",
         ha="center", va="bottom", fontsize=10, weight="bold", color=RED, linespacing=1.1)
ax1.text(x[1] + w / 2, new_vals[1] + 0.09, f"New\n{new_vals[1]:.2f}%",
         ha="center", va="bottom", fontsize=9, weight="bold", color=DARK, linespacing=1.1)

ax1.annotate(f"{mobile_new - mobile_old:+.2f} pp", xy=(x[0], 2.55),
             ha="center", fontsize=11, weight="bold", color=RED)
ax1.annotate(f"{desktop_new - desktop_old:+.2f} pp", xy=(x[1], 4.05),
             ha="center", fontsize=10, weight="bold", color=DARK)

ax1.set_xticks(x)
ax1.set_xticklabels(devices, fontsize=10, color=DARK)
ax1.set_ylabel("Conversion (% of sessions)", fontsize=10, color=DARK)
ax1.set_ylim(0, 4.6)
ax1.set_yticks([0, 1, 2, 3, 4])
ax1.tick_params(axis="y", labelsize=9, colors=MID)
ax1.yaxis.grid(True, color="#E5E5E5", linewidth=0.7)
ax1.set_axisbelow(True)
for s in ["top", "right", "left"]:
    ax1.spines[s].set_visible(False)
ax1.spines["bottom"].set_color("#CCCCCC")
ax1.set_title("Conversion: old vs new checkout", fontsize=11, weight="bold", color=DARK, loc="left", pad=12)

ax1.text(
    0.5, -0.22,
    f"14-day orders: Old {total_orders['control']:,}  vs  New {total_orders['new_checkout']:,}  ({order_change:.1f}%)",
    transform=ax1.transAxes, ha="center", va="top", fontsize=9.5, weight="bold", color=RED,
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#FDECEC", edgecolor="none"),
)

# --- Right panel: mobile daily trend and bug-fix caveat ---
ax2.plot(mobile_daily.index, mobile_daily["control"], color=MID, linewidth=2.2, marker="o", markersize=4)
ax2.plot(mobile_daily.index, mobile_daily["new_checkout"], color=RED, linewidth=2.6, marker="o", markersize=4)

bug_fix = pd.Timestamp("2026-09-26")
ax2.axvspan(bug_fix, mobile_daily.index.max() + pd.Timedelta(hours=12), color="#FDECEC", zorder=0)
ax2.axvline(bug_fix, color=RED, linestyle="--", linewidth=1.3)
ax2.text(bug_fix, 2.82, " Payment-button bug\n fixed 26 Sep", fontsize=8.5, color=RED, va="top", ha="left", linespacing=1.2)

last_date = mobile_daily.index.max()
ax2.text(last_date + pd.Timedelta(hours=8), mobile_daily["control"].iloc[-1], "Old",
         fontsize=10, weight="bold", color=MID, va="center")
ax2.text(last_date + pd.Timedelta(hours=8), mobile_daily["new_checkout"].iloc[-1] + 0.12, "New",
         fontsize=10, weight="bold", color=RED, va="center")

ax2.annotate(
    f"26–27 Sep, new: {post_fix_conv:.2f}%\nclose to old — but only 2 days",
    xy=(bug_fix + pd.Timedelta(days=1), post_fix_conv),
    xytext=(pd.Timestamp("2026-09-21"), 0.35),
    fontsize=9, color=DARK, linespacing=1.3,
    arrowprops=dict(arrowstyle="->", color=DARK, lw=1.1),
    bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#CCCCCC"),
)

ax2.annotate("20 Sep dip:\nboth versions", xy=(pd.Timestamp("2026-09-20"), 1.07),
             xytext=(pd.Timestamp("2026-09-15"), 0.35), fontsize=7.5, color=MID, linespacing=1.2,
             arrowprops=dict(arrowstyle="->", color=MID, lw=0.9))

ax2.set_title("Mobile conversion by day", fontsize=11, weight="bold", color=DARK, loc="left", pad=12)
ax2.set_ylabel("Conversion (% of sessions)", fontsize=10, color=DARK)
ax2.set_ylim(0, 3.0)
ax2.set_yticks([0, 1, 2, 3])
ax2.tick_params(axis="y", labelsize=9, colors=MID)
ax2.tick_params(axis="x", labelsize=8, colors=MID)
ax2.xaxis.set_major_locator(mdates.DayLocator(interval=3))
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d Sep"))
ax2.yaxis.grid(True, color="#E5E5E5", linewidth=0.7)
ax2.set_axisbelow(True)
for s in ["top", "right", "left"]:
    ax2.spines[s].set_visible(False)
ax2.spines["bottom"].set_color("#CCCCCC")
ax2.set_xlim(mobile_daily.index.min() - pd.Timedelta(hours=6),
             mobile_daily.index.max() + pd.Timedelta(days=1.4))

fig.text(0.06, 0.03, "14–27 Sep 2026  •  Tablet (3% of sessions) not shown  •  Keep testing mobile after the fix before deciding.",
         fontsize=8, color=MID, ha="left")

plt.subplots_adjust(left=0.06, right=0.97, top=0.84, bottom=0.14)
