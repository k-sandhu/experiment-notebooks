import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")
df["month_dt"] = pd.to_datetime(df["month"])
df = df.sort_values(["plan", "month_dt"])

months = sorted(df["month_dt"].unique())
month_to_x = {m: i for i, m in enumerate(months)}
df["x"] = df["month_dt"].map(month_to_x)
x_labels = [pd.Timestamp(m).strftime("%b\n%Y") if i in (0, 3, 6, 11) else pd.Timestamp(m).strftime("%b") for i, m in enumerate(months)]

price_x = month_to_x[pd.Timestamp("2026-04-01")] - 0.5  # boundary between Mar and Apr
apr_x = month_to_x[pd.Timestamp("2026-04-01")]
aug_x = month_to_x[pd.Timestamp("2026-08-01")]
sep_x = month_to_x[pd.Timestamp("2026-09-01")]

fam = df[df["plan"] == "Family"].copy()
others = df[df["plan"] != "Family"].copy()

pre = fam[fam["month"].isin(["2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03"])]
post = fam[fam["month"].isin(["2026-04", "2026-05", "2026-06", "2026-07", "2026-08"])]
pre_avg = pre["cancellation_rate_pct"].mean()
post_avg = post["cancellation_rate_pct"].mean()

fam_apr = fam.loc[fam["month"] == "2026-04", "active_subscribers"].iloc[0]
fam_sep = fam.loc[fam["month"] == "2026-09", "active_subscribers"].iloc[0]
pct_change = (fam_sep / fam_apr - 1) * 100

STRONG = "#C1272D"
GREY = "#9A9A9A"
LIGHT_GREY = "#C4C4C4"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6))
fig.subplots_adjust(top=0.80, bottom=0.17, wspace=0.28, left=0.08, right=0.93)

fig.suptitle(
    "Family cancellations doubled after the April price rise,\ncosting 19% of subscribers",
    fontsize=15, fontweight="bold", ha="left", x=0.08, y=0.98, va="top",
)

# ---------- Panel 1: cancellation rate ----------
for _, g in others.groupby("plan"):
    g = g.sort_values("x")
    main = g[g["x"] <= aug_x]
    sept = g[g["x"] == sep_x]
    ax1.plot(main["x"], main["cancellation_rate_pct"], color=LIGHT_GREY, lw=1.4, zorder=2)
    ax1.plot(sept["x"], sept["cancellation_rate_pct"], marker="o", mfc="white",
             mec=GREY, mew=1.4, ms=5, ls="none", zorder=3)

fam_main = fam[fam["x"] <= aug_x]
fam_sept = fam[fam["x"] == sep_x]
ax1.plot(fam_main["x"], fam_main["cancellation_rate_pct"], color=STRONG, lw=3,
         marker="o", ms=4, zorder=4)
ax1.plot(fam_sept["x"], fam_sept["cancellation_rate_pct"], marker="o", mfc="white",
         mec=STRONG, mew=1.8, ms=7, ls="none", zorder=5)

# averages
ax1.hlines(pre_avg, 0, price_x, color=STRONG, lw=1.6, ls="--", zorder=3)
ax1.hlines(post_avg, price_x, aug_x, color=STRONG, lw=1.6, ls="--", zorder=3)
ax1.text(1.2, pre_avg + 0.45, f"Family avg\nOct–Mar: {pre_avg:.1f}%",
         color=STRONG, fontsize=10, fontweight="bold", ha="center", va="bottom")
ax1.text((apr_x + aug_x) / 2, post_avg + 0.45, f"Apr–Aug: {post_avg:.1f}%",
         color=STRONG, fontsize=11, fontweight="bold", ha="center", va="bottom")

ax1.axvline(price_x, color="#333333", lw=1.2, ls="-", zorder=1)
ax1.text(price_x + 0.15, 7.85, "Family price\n$79 → $89/week\n1 April 2026",
         fontsize=8.5, ha="left", va="top", color="#333333")

ax1.text(aug_x + 0.18, 6.71, "Family", color=STRONG, fontsize=11,
         fontweight="bold", va="center", ha="left")
ax1.text(aug_x + 0.18, 2.55, "Other\nplans", color=GREY, fontsize=9, va="center", ha="left")
ax1.text(sep_x, 3.08 + 0.55, "Sep○", color=STRONG, fontsize=8, ha="center", va="bottom")

ax1.set_title("Cancellation rate", fontsize=11, fontweight="bold", loc="left", pad=8)
ax1.set_ylabel("Cancellations (% of active subscribers\nper month)", fontsize=9)
ax1.set_ylim(0, 8.2)
ax1.set_xlim(-0.2, sep_x + 0.6)
ax1.set_xticks(range(len(months)))
ax1.set_xticklabels(x_labels, fontsize=8)
ax1.set_yticks([0, 2, 4, 6, 8])
ax1.set_yticklabels(["0%", "2%", "4%", "6%", "8%"], fontsize=9)
ax1.grid(axis="y", color="#E6E6E6", lw=0.8, zorder=0)
ax1.set_axisbelow(True)

# ---------- Panel 2: active subscribers, indexed ----------
plot_df = df.copy()
base = plot_df[plot_df["month"] == "2025-10"].set_index("plan")["active_subscribers"]
plot_df["indexed"] = plot_df.apply(
    lambda r: r["active_subscribers"] / base[r["plan"]] * 100, axis=1
)

for plan, g in plot_df[plot_df["plan"] != "Family"].groupby("plan"):
    g = g.sort_values("x")
    ax2.plot(g["x"], g["indexed"], color=LIGHT_GREY, lw=1.6, zorder=2)
    last = g.iloc[-1]
    ax2.text(last["x"] + 0.18, last["indexed"], plan, color=GREY,
             fontsize=8.5, va="center", ha="left")

fam_idx = plot_df[plot_df["plan"] == "Family"].sort_values("x")
ax2.plot(fam_idx["x"], fam_idx["indexed"], color=STRONG, lw=3, marker="o", ms=4, zorder=4)
fam_last = fam_idx.iloc[-1]
ax2.text(fam_last["x"] + 0.18, fam_last["indexed"], "Family", color=STRONG,
         fontsize=11, fontweight="bold", va="center", ha="left")

ax2.axhline(100, color=GREY, lw=1.0, ls="--", zorder=1)
ax2.axvline(price_x, color="#333333", lw=1.2, zorder=1)
ax2.text(price_x + 0.15, 143, "Price rise\n1 April 2026",
         fontsize=8.5, ha="left", va="top", color="#333333")

ax2.annotate(
    f"{fam_apr:,.0f} in April → {fam_sep:,.0f} in September\n({pct_change:.0f}%)",
    xy=(sep_x, fam_last["indexed"]), xytext=(6.4, 88),
    color=STRONG, fontsize=10, fontweight="bold", ha="left", va="top",
    arrowprops=dict(arrowstyle="->", color=STRONG, lw=1.4),
)

ax2.set_title("Active subscribers", fontsize=11, fontweight="bold", loc="left", pad=8)
ax2.set_ylabel("Active subscribers at month start\n(indexed, Oct 2025 = 100)", fontsize=9)
ax2.set_ylim(75, 145)
ax2.set_xlim(-0.2, sep_x + 0.6)
ax2.set_xticks(range(len(months)))
ax2.set_xticklabels(x_labels, fontsize=8)
ax2.tick_params(axis="y", labelsize=9)
ax2.grid(axis="y", color="#E6E6E6", lw=0.8, zorder=0)
ax2.set_axisbelow(True)

for ax in (ax1, ax2):
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")

fig.text(
    0.08, 0.03,
    "September ○ covers 1–14 September only (half month) — its lower cancellation rate is not a recovery "
    "and is excluded from the 6.5% average.\nSubscriber counts are at the start of the month, so September is a full count.",
    fontsize=8.5, color="#555555", ha="left", va="bottom",
)
