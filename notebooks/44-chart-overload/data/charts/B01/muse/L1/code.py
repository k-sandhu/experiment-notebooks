import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# --- Data -------------------------------------------------------------------
df = pd.read_csv("data.csv", parse_dates=["month"])

fam = df[df["plan"] == "Family"].sort_values("month").copy()
others = (
    df[df["plan"] != "Family"]
    .groupby("month", as_index=False)[["active_subscribers", "cancellations"]]
    .sum()
    .sort_values("month")
)
others["cancellation_rate_pct"] = (
    100 * others["cancellations"] / others["active_subscribers"]
)

price_date = pd.Timestamp("2026-04-01")
last_full = pd.Timestamp("2026-08-01")   # September is 1-14 Sep only
sep_date = pd.Timestamp("2026-09-01")

# Family churn: full months only, so September cannot look like a recovery
fam_full = fam[fam["month"] <= last_full]
oth_full = others[others["month"] <= last_full]
pre = fam_full[fam_full["month"] < price_date]
post = fam_full[fam_full["month"] >= price_date]
pre_churn = pre["cancellation_rate_pct"].mean()
post_churn = post["cancellation_rate_pct"].mean()

# Weekly revenue proxy (start-of-September subscribers are complete)
fam["revenue_m"] = fam["active_subscribers"] * fam["price_per_week_usd"] / 1e6
pre_rev = fam[fam["month"] < price_date]["revenue_m"].mean()
apr_row = fam[fam["month"] == price_date].iloc[0]
sep_row = fam[fam["month"] == sep_date].iloc[0]
sub_change = 100 * (sep_row["active_subscribers"] /
                    apr_row["active_subscribers"] - 1)

# --- Figure -----------------------------------------------------------------
RED, GREY, DARK = "#C1272D", "#8A8A8A", "#222222"
fig, (ax1, ax2) = plt.subplots(
    2, 1, figsize=(10, 6), sharex=True,
    gridspec_kw={"height_ratios": [1.05, 1], "hspace": 0.32},
)
fig.patch.set_facecolor("white")

for ax in (ax1, ax2):
    ax.axvspan(price_date, pd.Timestamp("2026-09-25"),
               color=RED, alpha=0.06, zorder=0)
    ax.axvline(price_date, color=RED, lw=1.4, ls="--", zorder=1)
    ax.grid(axis="y", color="grey", alpha=0.25, lw=0.7)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=9)

# Panel 1: cancellation rate (control = other plans pooled)
ax1.plot(oth_full["month"], oth_full["cancellation_rate_pct"],
         color=GREY, lw=2, marker="o", ms=4, zorder=3)
ax1.plot(fam_full["month"], fam_full["cancellation_rate_pct"],
         color=RED, lw=3.2, marker="o", ms=5, zorder=4)
ax1.hlines(pre_churn, pre["month"].min(), pre["month"].max(),
           color=RED, lw=1.2, ls=":", zorder=2)
ax1.hlines(post_churn, post["month"].min(), post["month"].max(),
           color=RED, lw=1.2, ls=":", zorder=2)
ax1.set_ylim(0, 8.2)
ax1.set_ylabel("% cancelling\nper month", fontsize=9.5)
ax1.yaxis.set_major_formatter(mticker.PercentFormatter())
ax1.set_title("1   Cancellations doubled — only on Family",
              loc="left", fontsize=11.5, fontweight="bold", color=DARK)

ax1.text(pd.Timestamp("2025-11-05"), pre_churn + 0.55,
         f"Family before: {pre_churn:.1f}%", color=RED,
         fontsize=10, fontweight="bold")
ax1.text(pd.Timestamp("2026-05-12"), post_churn + 0.55,
         f"Family after: {post_churn:.1f}%", color=RED,
         fontsize=11, fontweight="bold")
ax1.text(pd.Timestamp("2026-08-08"),
         fam_full["cancellation_rate_pct"].iloc[-1],
         "  Family", color=RED, fontsize=10.5,
         fontweight="bold", va="center")
ax1.text(pd.Timestamp("2026-08-08"),
         oth_full["cancellation_rate_pct"].iloc[-1],
         "  Other plans\n  (pooled)", color="#666666",
         fontsize=9.5, fontweight="bold", va="center")
ax1.text(price_date + pd.Timedelta(days=6), 7.75,
         "1 Apr 2026\nFamily $79 \u2192 $89 / week (+13%)",
         color=RED, fontsize=10, fontweight="bold", va="top")

# Panel 2: Family weekly revenue proxy
ax2.plot(fam["month"], fam["revenue_m"], color=RED, lw=3.2,
         marker="o", ms=5, zorder=4)
ax2.axhline(pre_rev, color="#666666", lw=1.3, ls="--", zorder=2)
ax2.set_ylim(0.92, 1.36)
ax2.set_ylabel("$m per week", fontsize=9.5)
ax2.set_title("2   Family revenue is now below its pre-rise level, "
              "and still falling",
              loc="left", fontsize=11.5, fontweight="bold", color=DARK)
ax2.text(pd.Timestamp("2025-10-05"), pre_rev + 0.025,
         f"Pre-rise average: ${pre_rev:.2f}m / week",
         color="#666666", fontsize=9.5, fontweight="bold")
ax2.annotate(f"Apr: ${apr_row['revenue_m']:.2f}m\n"
             f"{apr_row['active_subscribers']:,.0f} subscribers",
             xy=(apr_row["month"], apr_row["revenue_m"]),
             xytext=(18, 8), textcoords="offset points",
             fontsize=9.5, color=DARK, fontweight="bold")
ax2.annotate(f"Sep: ${sep_row['revenue_m']:.2f}m\n"
             f"{sep_row['active_subscribers']:,.0f} subscribers "
             f"({sub_change:.0f}% since Apr)",
             xy=(sep_row["month"], sep_row["revenue_m"]),
             xytext=(-178, -34), textcoords="offset points",
             fontsize=10, color=RED, fontweight="bold",
             arrowprops=dict(arrowstyle="->", color=RED, lw=1.3))

# Shared time axis
months = sorted(df["month"].unique())
ax2.set_xticks(months)
ax2.set_xticklabels([pd.Timestamp(m).strftime("%b %y") for m in months],
                    rotation=30, ha="left", fontsize=9)
ax2.set_xlim(pd.Timestamp("2025-09-22"), pd.Timestamp("2026-09-24"))

# Headline, subtitle and footnote
fig.text(0.055, 0.955,
         "Reverse the Family price rise: it now earns less than before",
         fontsize=17, fontweight="bold", color=DARK, va="top")
fig.text(0.055, 0.905,
         "Churn doubled after $79 \u2192 $89, the Family base is down 19% "
         "since April, and other plans are unchanged.",
         fontsize=11, color="#444444", va="top")
fig.text(0.055, 0.018,
         "Notes: Sep 2026 covers 1\u201314 Sep only, so September "
         "cancellations are excluded (top); start-of-September subscribers "
         "are complete.  Revenue = active subscribers \u00d7 weekly price; "
         "excludes gift subscriptions.",
         fontsize=7.5, color="#777777", va="bottom")

plt.tight_layout(rect=[0, 0.045, 1, 0.875])
