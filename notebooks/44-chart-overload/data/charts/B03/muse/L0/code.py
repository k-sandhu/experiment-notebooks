import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data.csv", parse_dates=["date"])

# Aggregate conversion correctly: total orders / total sessions (not mean of %)
daily = (
    df.groupby(["date", "variant", "device"], as_index=False)
      .agg(sessions=("sessions", "sum"), orders=("orders", "sum"))
)
daily["conversion"] = 100 * daily["orders"] / daily["sessions"]

agg = (
    df.groupby(["device", "variant"], as_index=False)
      .agg(sessions=("sessions", "sum"), orders=("orders", "sum"))
)
agg["conversion"] = 100 * agg["orders"] / agg["sessions"]

overall = (
    df.groupby("variant", as_index=False)
      .agg(sessions=("sessions", "sum"), orders=("orders", "sum"))
)
overall["device"] = "overall"
overall["conversion"] = 100 * overall["orders"] / overall["sessions"]
agg = pd.concat([overall[["device", "variant", "sessions", "orders", "conversion"]], agg],
                ignore_index=True)

share = df.groupby("device")["sessions"].sum() / df["sessions"].sum() * 100
orders_by_variant = df.groupby("variant")["orders"].sum()
order_change = 100 * (orders_by_variant["new_checkout"] / orders_by_variant["control"] - 1)

outage = pd.Timestamp("2026-09-20")
bug_fix = pd.Timestamp("2026-09-26")

fig = plt.figure(figsize=(10, 6))
gs = fig.add_gridspec(1, 2, width_ratios=[1.75, 1.05], wspace=0.30)
ax0 = fig.add_subplot(gs[0, 0])
ax1 = fig.add_subplot(gs[0, 1])

fig.suptitle("New checkout lifts desktop but drags mobile — net fewer orders",
             fontsize=13, fontweight="bold", x=0.015, ha="left")
fig.text(0.015, 0.915,
         "Conversion = orders / sessions. Mobile is most traffic, so its drop outweighs the desktop gain.",
         fontsize=9, color="#444444")

# --- Left: daily conversion, desktop & mobile (tablet is only ~3% and very noisy) ---
styles = {
    ("desktop", "control"):      dict(color="#2E6EA6", ls="--", lw=1.6, marker="o"),
    ("desktop", "new_checkout"): dict(color="#2E6EA6", ls="-",  lw=2.4, marker="o"),
    ("mobile", "control"):       dict(color="#D55E00", ls="--", lw=1.6, marker="s"),
    ("mobile", "new_checkout"):  dict(color="#D55E00", ls="-",  lw=2.4, marker="s"),
}
labels = {
    ("desktop", "control"): "Desktop — control",
    ("desktop", "new_checkout"): "Desktop — new checkout",
    ("mobile", "control"): "Mobile — control",
    ("mobile", "new_checkout"): "Mobile — new checkout",
}
for key, style in styles.items():
    sub = daily[(daily["device"] == key[0]) & (daily["variant"] == key[1])].sort_values("date")
    ax0.plot(sub["date"], sub["conversion"], label=labels[key],
             markersize=4, alpha=0.95, **style)

# Post-bug-fix window and outage
ax0.axvspan(bug_fix, daily["date"].max() + pd.Timedelta(hours=12),
            color="#2E7D32", alpha=0.08, lw=0)
ax0.axvline(outage, color="#777777", ls=":", lw=1.4)
ax0.axvline(bug_fix, color="#2E7D32", ls=":", lw=1.4)

ax0.annotate("Sep 20 payment\noutage (both dip)",
             xy=(outage, 1.15), xytext=(pd.Timestamp("2026-09-20"), 4.55),
             fontsize=7.5, color="#555555", ha="center",
             arrowprops=dict(arrowstyle="-", color="#777777", lw=0.8))
ax0.annotate("Sep 26: mobile payment-\nbutton bug fixed",
             xy=(bug_fix, 2.35), xytext=(pd.Timestamp("2026-09-22"), 4.45),
             fontsize=7.5, color="#2E7D32", ha="center",
             arrowprops=dict(arrowstyle="->", color="#2E7D32", lw=0.9))

ax0.set_title("Daily conversion — desktop and mobile", fontsize=10, fontweight="bold", loc="left")
ax0.set_ylabel("Conversion (% of sessions)")
ax0.set_ylim(0, 5.1)
ax0.set_xlim(daily["date"].min() - pd.Timedelta(hours=6),
             daily["date"].max() + pd.Timedelta(hours=12))
ax0.xaxis.set_major_locator(mdates.DayLocator(interval=2))
ax0.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax0.grid(axis="y", alpha=0.3)
ax0.legend(fontsize=7.5, frameon=False, loc="upper left", ncols=2)
ax0.spines[["top", "right"]].set_visible(False)

# --- Right: 14-day aggregate by device ---
order = ["overall", "mobile", "desktop", "tablet"]
pretty = {
    "overall": "Overall",
    "mobile": f"Mobile\n({share['mobile']:.0f}% of sessions)",
    "desktop": f"Desktop\n({share['desktop']:.0f}% of sessions)",
    "tablet": f"Tablet\n({share['tablet']:.0f}% of sessions)",
}
y = np.arange(len(order))
h = 0.36
for i, device in enumerate(order):
    ctrl = agg[(agg["device"] == device) & (agg["variant"] == "control")]["conversion"].iloc[0]
    new = agg[(agg["device"] == device) & (agg["variant"] == "new_checkout")]["conversion"].iloc[0]
    pp = new - ctrl
    ax1.barh(i - h / 2, ctrl, height=h, color="#8A94A6",
             label="Control" if i == 0 else None)
    ax1.barh(i + h / 2, new, height=h, color="#1F4E79",
             label="New checkout" if i == 0 else None)
    ax1.text(ctrl + 0.06, i - h / 2, f"{ctrl:.2f}%", va="center", fontsize=8)
    ax1.text(new + 0.06, i + h / 2, f"{new:.2f}% ({pp:+.2f} pp)",
             va="center", fontsize=8,
             color="#B3261E" if pp < 0 else "#2E7D32", fontweight="bold")

ax1.set_yticks(y, [pretty[d] for d in order], fontsize=8)
ax1.invert_yaxis()
ax1.set_xlim(0, 5.4)
ax1.set_xlabel("14-day conversion (% of sessions)")
ax1.set_title("Aggregate conversion by device", fontsize=10, fontweight="bold", loc="left")
ax1.grid(axis="x", alpha=0.3)
ax1.legend(fontsize=8, frameon=False, loc="lower right")
ax1.spines[["top", "right"]].set_visible(False)

fig.text(0.015, 0.015,
         f"Total orders: {orders_by_variant['control']:,} control vs "
         f"{orders_by_variant['new_checkout']:,} new ({order_change:+.1f}%). "
         "AOV is similar (~$413 vs ~$411), so the order gap is broadly a revenue gap.\n"
         "Caution: the post-fix window is only Sep 26–27 and includes a Saturday (the usual weekly peak), "
         "so a mobile recovery is not yet proven. Tablet gain is on ~3% of sessions.",
         fontsize=7.5, color="#444444", va="bottom")

plt.tight_layout(rect=[0, 0.075, 1, 0.90])
