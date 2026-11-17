import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data.csv", parse_dates=["date"])

C_CTRL = "#8c8c8c"
C_NEW = "#1f6fb4"
labels = {"control": "Old checkout", "new_checkout": "New checkout"}
colors = {"control": C_CTRL, "new_checkout": C_NEW}

# Daily mobile conversion
mob = (df[df.device == "mobile"]
       .groupby(["date", "variant"])[["orders", "sessions"]].sum())
mob["conv"] = mob.orders / mob.sessions * 100
mob = mob["conv"].unstack("variant")

# Pooled conversion by device over the 14 days
dev = df.groupby(["device", "variant"])[["orders", "sessions"]].sum()
dev["conv"] = dev.orders / dev.sessions * 100
dev = dev["conv"].unstack("variant").loc[["mobile", "desktop", "tablet"]]
share = df.groupby("device").sessions.sum() / df.sessions.sum() * 100

tot = df.groupby("variant").orders.sum()
pct = (tot["new_checkout"] / tot["control"] - 1) * 100

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.7, 1]})

# Panel 1: mobile over time
fix_start = pd.Timestamp("2026-09-25 12:00")
ax1.axvspan(fix_start, mob.index.max() + pd.Timedelta(hours=12),
            color="#e6f0e6", zorder=0)
ax1.text(fix_start + pd.Timedelta(hours=3), 0.6,
         "Payment-button\nbug fixed\n(26 Sep)", fontsize=8.5,
         color="#2e6b2e", va="bottom")

for v in ["control", "new_checkout"]:
    ax1.plot(mob.index, mob[v], marker="o", ms=4, lw=2,
             color=colors[v], label=labels[v])

out = pd.Timestamp("2026-09-20")
ax1.annotate("Payment-provider\noutage", xy=(out, mob.loc[out].min()),
             xytext=(out + pd.Timedelta(days=1.2), 0.75),
             fontsize=8.5, color="#555",
             arrowprops=dict(arrowstyle="-", color="#999", lw=0.8))

ax1.set_ylim(0.5, 3.0)
ax1.set_ylabel("Mobile conversion (orders / sessions, %)")
ax1.set_title("Mobile, daily", loc="left", fontsize=11)
ax1.xaxis.set_major_locator(mdates.DayLocator(interval=2))
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
ax1.legend(frameon=False, loc="upper left")
ax1.grid(axis="y", alpha=0.3)

# Panel 2: pooled by device
x = np.arange(len(dev))
w = 0.38
for i, v in enumerate(["control", "new_checkout"]):
    bars = ax2.bar(x + (i - 0.5) * w, dev[v], w, color=colors[v],
                   label=labels[v])
    for b, val in zip(bars, dev[v]):
        ax2.text(b.get_x() + b.get_width() / 2, val + 0.05, f"{val:.2f}",
                 ha="center", va="bottom", fontsize=8.5)
ax2.set_xticks(x)
ax2.set_xticklabels([f"{d.capitalize()}\n{share[d]:.0f}% of sessions"
                     for d in dev.index], fontsize=9)
ax2.set_ylabel("Conversion, 14 days pooled (%)")
ax2.set_title("All devices, 14–27 Sep", loc="left", fontsize=11)
ax2.set_ylim(0, 4.3)
ax2.grid(axis="y", alpha=0.3)
ax2.set_axisbelow(True)

for ax in (ax1, ax2):
    ax.spines[["top", "right"]].set_visible(False)

fig.suptitle(
    "New checkout lifted desktop conversion but cut mobile conversion until "
    "a bug fix on 26 Sep",
    fontsize=12.5, fontweight="bold", x=0.01, ha="left")
fig.text(0.01, 0.905,
         f"Mobile is {share['mobile']:.0f}% of sessions, so the new checkout "
         f"produced {abs(pct):.1f}% fewer orders overall "
         f"({tot['new_checkout']:,} vs {tot['control']:,}). "
         "Only two days of post-fix data; tablet samples are small.",
         fontsize=9, color="#444", ha="left")

fig.tight_layout(rect=(0, 0, 1, 0.89))
