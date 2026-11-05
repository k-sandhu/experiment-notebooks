import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")
df = df.sort_values(["plan", "month"])

months = sorted(df["month"].unique())
idx = {m: i for i, m in enumerate(months)}
df["x"] = df["month"].map(idx)
tick_labels = [pd.Period(m, "M").strftime("%b\n'%y") for m in months]

FAM = "#C0392B"
GREY = "#B5B5B5"
DARK = "#333333"
MID = "#666666"

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6))
fig.subplots_adjust(left=0.07, right=0.97, top=0.80, bottom=0.17, wspace=0.28)

price_x = idx["2026-04"] - 0.5  # price rose 1 April 2026
XLIM = (-0.5, len(months) + 0.6)
ticks = list(range(0, len(months), 2))

# ---------- Left panel: cancellation rate (full months only, Oct-Aug) ----------
full = df[df["month"] < "2026-09"]
for plan in ["Single", "Couple", "Vegetarian"]:
    d = full[full["plan"] == plan]
    ax1.plot(d["x"], d["cancellation_rate_pct"], color=GREY, lw=1.5, zorder=1)
fam = full[full["plan"] == "Family"]
ax1.plot(fam["x"], fam["cancellation_rate_pct"], color=FAM, lw=3, marker="o",
         ms=4, zorder=3)

before = fam[fam["month"] < "2026-04"]["cancellation_rate_pct"].mean()
after = fam[fam["month"] >= "2026-04"]["cancellation_rate_pct"].mean()
ax1.text(2.5, before + 0.45, f"Avg {before:.1f}%", color=FAM, ha="center",
         fontsize=11, fontweight="bold")
ax1.text(8, after + 0.55, f"Avg {after:.1f}%", color=FAM, ha="center",
         fontsize=11, fontweight="bold")

ax1.axvline(price_x, color=DARK, lw=1, ls="--")
ax1.text(price_x - 0.15, 7.75, "Price \\$79 → \\$89\n(1 Apr)", ha="right", va="top",
         fontsize=9, color=DARK)

last_x = fam["x"].max()
ax1.text(last_x + 0.25, fam["cancellation_rate_pct"].iloc[-1], "Family",
         color=FAM, va="center", fontsize=10, fontweight="bold")
ax1.text(last_x + 0.25, 2.75, "Other\nplans", color="#888888", va="center", fontsize=9)

ax1.set_xlim(*XLIM)
ax1.set_ylim(0, 8)
ax1.set_ylabel("Monthly cancellation rate (%)")
ax1.set_title("Family cancellations doubled after the rise", loc="left",
              fontsize=11, color=DARK)

# ---------- Right panel: estimated weekly revenue, Family ----------
f_all = df[df["plan"] == "Family"].copy()
f_all["rev_k"] = f_all["active_subscribers"] * f_all["price_per_week_usd"] / 1000
ax2.plot(f_all["x"], f_all["rev_k"], color=FAM, lw=3, marker="o", ms=4, zorder=3)

pre = f_all.loc[f_all["month"] == "2026-03", "rev_k"].iloc[0]
latest = f_all.loc[f_all["month"] == "2026-09", "rev_k"].iloc[0]
peak = f_all.loc[f_all["month"] == "2026-04", "rev_k"].iloc[0]
pct = (latest / pre - 1) * 100

ax2.axhline(pre, color="#888888", lw=1, ls=":", zorder=1)
ax2.text(-0.3, pre + 8, f"March, last month at \\$79: \\${pre:,.0f}k",
         color=MID, fontsize=9, va="bottom")
ax2.axvline(price_x, color=DARK, lw=1, ls="--")
ax2.text(price_x - 0.15, 1340, "Price rise\n(1 Apr)", ha="right", va="top",
         fontsize=9, color=DARK)

ax2.annotate(f"\\${peak:,.0f}k", (idx["2026-04"], peak), xytext=(7, 4),
             textcoords="offset points", fontsize=10, color=FAM)
ax2.annotate(f"\\${latest:,.0f}k\n({pct:+.0f}% vs pre-rise)",
             (idx["2026-09"], latest), xytext=(14, -40), textcoords="offset points",
             ha="right", fontsize=10, color=FAM, fontweight="bold")

ax2.set_xlim(*XLIM)
ax2.set_ylim(900, 1350)
ax2.set_ylabel("Est. weekly revenue (US\\$ thousands)")
ax2.set_title("…so Family revenue is below pre-rise, and still falling",
              loc="left", fontsize=11, color=DARK)

for ax in (ax1, ax2):
    ax.set_xticks(ticks)
    ax.set_xticklabels([tick_labels[i] for i in ticks], fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors=DARK)

# ---------- Title, subtitle, caveats ----------
fig.text(0.07, 0.95,
         "The Family price rise has cost more in cancellations than it earns",
         fontsize=16, fontweight="bold", color=DARK, ha="left")
fig.text(0.07, 0.895,
         "Family subscribers fell 19% from April to September; the other three plans kept growing",
         fontsize=11, color="#555555", ha="left")
fig.text(0.07, 0.03,
         "Revenue estimated as active subscribers at start of month × weekly price "
         "(excludes gift subscriptions); revenue axis starts at \\$900k.\n"
         "September cancellation rate omitted: it covers 1–14 Sep only (half a month), "
         "so its lower figure is not a recovery.",
         fontsize=8.5, color=MID, ha="left")
