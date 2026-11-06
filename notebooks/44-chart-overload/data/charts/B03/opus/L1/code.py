import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data.csv", parse_dates=["date"])

OLD, NEW = "control", "new_checkout"
C_OLD, C_NEW = "#9a9a9a", "#d9480f"
FIX_DATE = pd.Timestamp("2026-09-26")
OUTAGE_DATE = pd.Timestamp("2026-09-20")

# Daily mobile conversion by variant
mob = (df[df.device == "mobile"]
       .groupby(["date", "variant"])[["orders", "sessions"]].sum())
mob["conv"] = mob.orders / mob.sessions * 100
mob = mob["conv"].unstack("variant")

# Total orders by device and variant
tot = df.groupby(["device", "variant"])["orders"].sum().unstack("variant")
diff = (tot[NEW] - tot[OLD]).reindex(["mobile", "desktop", "tablet"])
pct = (diff / tot[OLD].reindex(diff.index) * 100)
all_old, all_new = tot[OLD].sum(), tot[NEW].sum()
all_pct = (all_new - all_old) / all_old * 100

# Mobile conversion after the fix
post = df[(df.device == "mobile") & (df.date >= FIX_DATE)].groupby("variant")[["orders", "sessions"]].sum()
post_conv = post.orders / post.sessions * 100

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.6, 1]}
)
fig.subplots_adjust(top=0.78, bottom=0.12, left=0.07, right=0.97, wspace=0.35)

fig.suptitle(
    f"Don't roll out yet: the new checkout lost {abs(all_pct):.1f}% of orders, all on mobile",
    x=0.07, ha="left", fontsize=15, fontweight="bold", y=0.97,
)
fig.text(
    0.07, 0.875,
    f"The mobile loss tracks the payment-button bug fixed on 26 Sep. After the fix, mobile is on par "
    f"({post_conv[NEW]:.2f}% vs {post_conv[OLD]:.2f}%),\n"
    "but that is only two weekend days. Keep testing on mobile before deciding; desktop already gains.",
    ha="left", va="top", fontsize=10.5, color="#333333",
)

# Left panel: mobile conversion over time
ax1.axvspan(FIX_DATE - pd.Timedelta(hours=12), mob.index.max() + pd.Timedelta(hours=12),
            color="#2b8a3e", alpha=0.10, lw=0)
ax1.plot(mob.index, mob[OLD], color=C_OLD, lw=2.2, marker="o", ms=4)
ax1.plot(mob.index, mob[NEW], color=C_NEW, lw=2.6, marker="o", ms=4)
ax1.text(mob.index[0], mob[OLD].iloc[0] + 0.12, "Old checkout", color="#555555",
         fontsize=10, fontweight="bold")
ax1.text(mob.index[0], mob[NEW].iloc[0] - 0.22, "New checkout", color=C_NEW,
         fontsize=10, fontweight="bold")
ax1.text(FIX_DATE, 0.62, "Bug fixed\n26 Sep", color="#2b8a3e", fontsize=9.5,
         fontweight="bold", va="bottom")
ax1.annotate("Payment-provider\noutage (both)", xy=(OUTAGE_DATE, mob.loc[OUTAGE_DATE].min()),
             xytext=(OUTAGE_DATE + pd.Timedelta(days=0.4), 0.7), fontsize=8.5, color="#666666",
             arrowprops=dict(arrowstyle="-", color="#999999", lw=0.8))
ax1.set_title("Mobile conversion per day (% of sessions)", loc="left", fontsize=11.5,
              fontweight="bold")
ax1.set_ylim(0.5, 3.0)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}%"))
ax1.xaxis.set_major_locator(mdates.DayLocator(interval=3))
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
ax1.grid(axis="y", color="#e5e5e5", lw=0.8)
for s in ["top", "right"]:
    ax1.spines[s].set_visible(False)
ax1.tick_params(labelsize=9)

# Right panel: change in orders by device
labels = [f"{d.capitalize()}" for d in diff.index]
colors = [C_NEW if v < 0 else "#2b8a3e" for v in diff.values]
y = np.arange(len(diff))[::-1]
ax2.barh(y, diff.values, color=colors, height=0.6)
ax2.axvline(0, color="#333333", lw=1)
for yi, v, p in zip(y, diff.values, pct.values):
    ax2.text(v + (15 if v >= 0 else -15), yi, f"{v:+,.0f}\n({p:+.0f}%)",
             va="center", ha="left" if v >= 0 else "right", fontsize=9.5,
             fontweight="bold", color=C_NEW if v < 0 else "#2b8a3e")
ax2.set_yticks(y)
ax2.set_yticklabels(labels, fontsize=10.5)
ax2.set_xlim(-900, 550)
ax2.set_title(f"Orders, new vs old, 14 days\nTotal: {all_new - all_old:+,.0f} ({all_pct:+.1f}%)",
              loc="left", fontsize=11.5, fontweight="bold")
ax2.tick_params(axis="x", labelsize=9)
ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:+,.0f}" if v else "0"))
for s in ["top", "right", "left"]:
    ax2.spines[s].set_visible(False)
ax2.tick_params(axis="y", length=0)

fig.text(0.07, 0.025,
         "Traffic split 50/50 · Average order value about equal ($413 old vs $411 new) · "
         "14–27 Sep 2026",
         fontsize=8.5, color="#777777", ha="left")
