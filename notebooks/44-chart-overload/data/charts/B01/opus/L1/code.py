import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv("data.csv")
df["date"] = pd.to_datetime(df["month"] + "-01")
df = df.sort_values(["plan", "date"])

FAM = "#c0392b"
GREY = "#b5b5b5"
rise_date = pd.Timestamp("2026-04-01")

fam = df[df["plan"] == "Family"].copy()
fam["weekly_rev_k"] = fam["active_subscribers"] * fam["price_per_week_usd"] / 1000

# September covers 1-14 Sep only, so leave it out of the monthly cancellation rate
full = df[df["month"] != "2026-09"]
fam_full = full[full["plan"] == "Family"]
pre_rate = fam_full.loc[fam_full["date"] < rise_date, "cancellation_rate_pct"].mean()
post_rate = fam_full.loc[fam_full["date"] >= rise_date, "cancellation_rate_pct"].mean()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6), gridspec_kw={"wspace": 0.28})

# Panel 1: monthly cancellation rate
for i, (plan, g) in enumerate(full[full["plan"] != "Family"].groupby("plan")):
    ax1.plot(g["date"], g["cancellation_rate_pct"], color=GREY, lw=1.5,
             label="Other plans" if i == 0 else None)
ax1.plot(fam_full["date"], fam_full["cancellation_rate_pct"], color=FAM, lw=3,
         marker="o", ms=4, label="Family")

ax1.set_ylim(0, 8)
ax1.set_title("Monthly cancellation rate (%)", loc="left", fontsize=12, fontweight="bold")
ax1.text(pd.Timestamp("2025-10-10"), pre_rate + 0.55,
         f"avg {pre_rate:.1f}% at $79", color=FAM, fontsize=10)
ax1.text(pd.Timestamp("2026-04-10"), post_rate + 0.55,
         f"avg {post_rate:.1f}% at $89", color=FAM, fontsize=10, fontweight="bold")
ax1.legend(loc="lower left", frameon=False, fontsize=9)

# Panel 2: Family weekly revenue
pre_level = fam.loc[fam["month"] == "2026-03", "weekly_rev_k"].iloc[0]
peak = fam.loc[fam["month"] == "2026-04", "weekly_rev_k"].iloc[0]
latest = fam.loc[fam["month"] == "2026-09", "weekly_rev_k"].iloc[0]

ax2.plot(fam["date"], fam["weekly_rev_k"], color=FAM, lw=3, marker="o", ms=4)
ax2.axhline(pre_level, color="#555555", ls="--", lw=1.2)
ax2.text(pd.Timestamp("2025-10-05"), pre_level + 12,
         f"March level at $79: ${pre_level/1000:.2f}M", fontsize=9, color="#555555")
ax2.annotate(f"${peak/1000:.2f}M", (pd.Timestamp("2026-04-01"), peak),
             xytext=(6, 6), textcoords="offset points", color=FAM, fontsize=10)
ax2.annotate(f"${latest/1000:.2f}M\n(Sep)", (pd.Timestamp("2026-09-01"), latest),
             xytext=(-10, -36), textcoords="offset points", color=FAM,
             fontsize=10, fontweight="bold", ha="center")
ax2.set_ylim(900, 1350)
ax2.set_title("Family weekly revenue ($ thousands)", loc="left", fontsize=12, fontweight="bold")

for ax in (ax1, ax2):
    ax.axvline(rise_date, color="#333333", lw=1, ls=":")
    ax.text(rise_date, ax.get_ylim()[1], " Price $79→$89", va="top", fontsize=9, color="#333333")
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[10, 1, 4, 7]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#eeeeee")
    ax.set_xlim(pd.Timestamp("2025-09-20"), pd.Timestamp("2026-09-20"))

fig.suptitle("Family price rise doubled cancellations; weekly revenue is now below its pre-rise level",
             x=0.06, ha="left", fontsize=13.5, fontweight="bold", y=0.98)
fig.text(0.06, 0.905,
         f"Family subscribers fell 19% since April (14,358 → 11,625); the other three plans grew.",
         fontsize=10.5, color="#333333")
fig.text(0.06, 0.015,
         "Cancellation rate excludes Sep 2026 (data cover 1–14 Sep only). Revenue = start-of-month "
         "active subscribers × weekly price; excludes gift subscriptions (~3% of orders).",
         fontsize=8, color="#666666")
fig.subplots_adjust(left=0.06, right=0.97, top=0.82, bottom=0.13)
