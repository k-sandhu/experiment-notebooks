import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data.csv", parse_dates=["date"])

# ---------- aggregates (recompute conversion from orders/sessions) ----------
agg = df.groupby(["device", "variant"], as_index=False).agg(
    sessions=("sessions", "sum"), orders=("orders", "sum")
)
agg["conv"] = 100 * agg["orders"] / agg["sessions"]
agg["se"] = 100 * np.sqrt((agg["conv"] / 100) * (1 - agg["conv"] / 100) / agg["sessions"])
agg["ci95"] = 1.96 * agg["se"]

total_sessions = df["sessions"].sum()
share = df.groupby("device")["sessions"].sum() / total_sessions * 100

tot = df.groupby("variant")["orders"].sum()
orders_old, orders_new = int(tot["control"]), int(tot["new_checkout"])
orders_diff_pct = 100 * (orders_new - orders_old) / orders_old

order = ["mobile", "desktop", "tablet"]
labels = [f"Mobile\n{share['mobile']:.0f}% of sessions",
          f"Desktop\n{share['desktop']:.0f}% of sessions",
          f"Tablet\n{share['tablet']:.0f}% of sessions"]

def get(device, variant, col):
    return float(agg.loc[(agg.device == device) & (agg.variant == variant), col].iloc[0])

old = [get(d, "control", "conv") for d in order]
new = [get(d, "new_checkout", "conv") for d in order]
old_ci = [get(d, "control", "ci95") for d in order]
new_ci = [get(d, "new_checkout", "ci95") for d in order]

# Mobile daily series
mob = df[df.device == "mobile"].copy()
mob["conv"] = 100 * mob["orders"] / mob["sessions"]
mob_old = mob[mob.variant == "control"].sort_values("date")
mob_new = mob[mob.variant == "new_checkout"].sort_values("date")
fix_date = pd.Timestamp("2026-09-26")
outage_date = pd.Timestamp("2026-09-20")

# ---------- figure ----------
GREY, BLUE, RED, GREEN = "#8A8D93", "#1455A3", "#C0392B", "#1B7A3D"
fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6),
    gridspec_kw={"width_ratios": [1.0, 1.35], "wspace": 0.30},
)
fig.patch.set_facecolor("white")
fig.subplots_adjust(left=0.07, right=0.98, top=0.81, bottom=0.21)

fig.text(0.015, 0.975, "New checkout wins on desktop, loses on mobile —",
         fontsize=17, fontweight="bold", ha="left", va="top", color="#111111")
fig.text(0.015, 0.933, "not ready to roll out to everyone",
         fontsize=17, fontweight="bold", ha="left", va="top", color=RED)
fig.text(0.015, 0.888,
         f"14–27 Sep 2026  •  50/50 split  •  AOV unchanged (~$412)  •  "
         f"Overall orders {orders_new:,} vs {orders_old:,}  ({orders_diff_pct:+.1f}%)",
         fontsize=10, ha="left", va="top", color="#444444")

# ---------- Panel 1: conversion by device ----------
x = np.arange(len(order))
w = 0.38
ax1.bar(x - w / 2, old, w, label="Old checkout", color=GREY,
        yerr=old_ci, capsize=3, error_kw={"lw": 1})
ax1.bar(x + w / 2, new, w, label="New checkout", color=BLUE,
        yerr=new_ci, capsize=3, error_kw={"lw": 1})

for i, (o, n) in enumerate(zip(old, new)):
    ax1.text(i - w / 2, o + 0.14, f"{o:.2f}%", ha="center", va="bottom", fontsize=9, color="#333333")
    ax1.text(i + w / 2, n + 0.14, f"{n:.2f}%", ha="center", va="bottom", fontsize=9,
             fontweight="bold", color=BLUE)
    rel = 100 * (n - o) / o
    col = GREEN if rel > 0 else RED
    arrow = "▲" if rel > 0 else "▼"
    ax1.text(i, max(o, n) + 0.55, f"{arrow} {rel:+.0f}%", ha="center", va="bottom",
             fontsize=11, fontweight="bold", color=col,
             bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=col, lw=1))

ax1.set_xticks(x)
ax1.set_xticklabels(labels, fontsize=9)
ax1.set_ylim(0, 4.6)
ax1.set_ylabel("Conversion\n(orders / sessions, %)", fontsize=9)
ax1.set_title("1  Conversion by device (14 days)", fontsize=11, fontweight="bold", loc="left", pad=10)
ax1.legend(frameon=False, fontsize=9, loc="upper right")
ax1.grid(axis="y", alpha=0.25)
ax1.set_axisbelow(True)
for s in ["top", "right"]:
    ax1.spines[s].set_visible(False)

# ---------- Panel 2: mobile over time ----------
ax2.axvspan(fix_date - pd.Timedelta(hours=12), mob["date"].max() + pd.Timedelta(hours=12),
            color=GREEN, alpha=0.10, zorder=0)
ax2.plot(mob_old["date"], mob_old["conv"], color=GREY, lw=2.5, marker="o", ms=4, label="Old — mobile")
ax2.plot(mob_new["date"], mob_new["conv"], color=BLUE, lw=2.5, marker="o", ms=4, label="New — mobile")
ax2.fill_between(mob_old["date"], mob_old["conv"].values, mob_new["conv"].values,
                 where=(mob_new["conv"].values < mob_old["conv"].values),
                 color=RED, alpha=0.15, interpolate=True)

post = mob_new[mob_new.date >= fix_date]
ax2.plot(post["date"], post["conv"], color=BLUE, lw=0, marker="o", ms=10,
         markerfacecolor="none", markeredgewidth=2)

ax2.axvline(outage_date, color="#666666", ls=":", lw=1.2)
ax2.text(outage_date, 2.62, "20 Sep\noutage\n(both dip)", ha="center", va="top", fontsize=7.5, color="#666666")
ax2.axvline(fix_date, color=GREEN, ls="--", lw=1.4)
ax2.text(fix_date + pd.Timedelta(hours=6), 2.62, "26 Sep: phone\npayment-button\nbug fixed",
         ha="left", va="top", fontsize=7.5, color=GREEN, fontweight="bold")
ax2.annotate("New ≈ old for 2 days\n— too early to judge",
             xy=(pd.Timestamp("2026-09-27"), float(post.loc[post.date == "2026-09-27", "conv"].iloc[0])),
             xytext=(pd.Timestamp("2026-09-21"), 1.18),
             fontsize=8.5, color=GREEN, fontweight="bold",
             arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.2))
ax2.text(pd.Timestamp("2026-09-17"), 1.78, "mobile gap\non most days",
         fontsize=8, color=RED, ha="center", style="italic")

ax2.set_ylim(0.8, 2.75)
ax2.set_ylabel("Mobile conversion (%)", fontsize=9)
ax2.set_title("2  Mobile daily conversion — recovery only after the fix",
              fontsize=11, fontweight="bold", loc="left", pad=10)
ax2.legend(frameon=False, fontsize=9, loc="lower left")
ax2.grid(axis="y", alpha=0.25)
ax2.set_axisbelow(True)
for s in ["top", "right"]:
    ax2.spines[s].set_visible(False)
ax2.xaxis.set_major_locator(mdates.DayLocator(interval=2))
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
ax2.tick_params(axis="x", labelsize=8)
ax2.set_xlim(mob["date"].min() - pd.Timedelta(hours=12), mob["date"].max() + pd.Timedelta(hours=12))

# ---------- decision banner + footer ----------
fig.text(
    0.5, 0.075,
    "DECISION:  Hold the full rollout.  Desktop gain is clear, but mobile (2 in 3 visits) drove the overall loss.\n"
    "Keep mobile on test for at least a full week post-fix — ship to all only if the recovery holds.",
    ha="center", va="center", fontsize=10, fontweight="bold", color="#7A3B06",
    bbox=dict(boxstyle="round,pad=0.55", fc="#FFF3E0", ec="#E67E22", lw=1.4),
)
fig.text(0.015, 0.012, "Error bars in panel 1 = 95% CI.  Tablet gain is based on only 3% of sessions.",
         fontsize=7.5, ha="left", va="bottom", color="#777777")
