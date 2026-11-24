import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")
df["month"] = pd.to_datetime(df["month"], format="%Y-%m")
months = sorted(df["month"].unique())
labels = [pd.Timestamp(m).strftime("%b\n%Y") if pd.Timestamp(m).month in (10, 1) else pd.Timestamp(m).strftime("%b")
          for m in months]
x_all = np.arange(len(months))

ACCENT = "#C8102E"
GREY = "#A6A6A6"
DARK = "#333333"

fam = df[df["plan"] == "Family"].sort_values("month").reset_index(drop=True)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1, 1.1]})
fig.subplots_adjust(left=0.07, right=0.88, top=0.80, bottom=0.17, wspace=0.28)

# Title
fig.text(0.07, 0.95,
         "Since the April price rise, Family cancellations doubled and subscribers fell 19%",
         fontsize=15, fontweight="bold", color=DARK, ha="left", va="top")
fig.text(0.07, 0.895,
         "Family plan price went from $79 to $89 a week on 1 April 2026; the other plans kept their prices and grew",
         fontsize=10.5, color="#555555", ha="left", va="top")

# ---------- Panel 1: Family cancellation rate (Oct-Aug, full months only) ----------
full = fam.iloc[:11]
x1 = np.arange(len(full))
ax1.axvspan(5.5, 10.5, color=ACCENT, alpha=0.06, lw=0)
ax1.axvline(5.5, color=DARK, lw=1, ls=":")
ax1.text(5.6, 7.75, "Price $79 → $89", fontsize=9, color=DARK, va="top")

ax1.plot(x1, full["cancellation_rate_pct"], color=ACCENT, lw=2.5, marker="o", ms=5, zorder=3)

before = full["cancellation_rate_pct"].iloc[:6].mean()
after = full["cancellation_rate_pct"].iloc[6:11].mean()
ax1.hlines(before, -0.2, 5.3, color=DARK, lw=1, ls="--")
ax1.hlines(after, 5.7, 10.2, color=DARK, lw=1, ls="--")
ax1.text(2.5, before - 0.55, f"Avg {before:.1f}% a month", ha="center", fontsize=10.5,
         color=DARK, fontweight="bold")
ax1.text(8, after + 0.45, f"Avg {after:.1f}% a month", ha="center", fontsize=10.5,
         color=ACCENT, fontweight="bold")

ax1.set_ylim(0, 8)
ax1.set_xlim(-0.5, 10.5)
ax1.set_xticks(x1)
ax1.set_xticklabels(labels[:11], fontsize=8.5)
ax1.set_ylabel("Cancellations, % of subscribers per month", fontsize=9.5)
ax1.set_title("Family plan monthly cancellation rate", fontsize=11, loc="left", color=DARK)

# ---------- Panel 2: active subscribers indexed, all plans ----------
ax2.axvspan(5.5, 11.3, color=ACCENT, alpha=0.06, lw=0)
ax2.axvline(5.5, color=DARK, lw=1, ls=":")
for plan in ["Single", "Couple", "Vegetarian", "Family"]:
    d = df[df["plan"] == plan].sort_values("month")
    idx = d["active_subscribers"].values / d["active_subscribers"].values[0] * 100
    is_fam = plan == "Family"
    ax2.plot(x_all, idx, color=ACCENT if is_fam else GREY,
             lw=2.8 if is_fam else 1.6, zorder=3 if is_fam else 2)
    ax2.text(x_all[-1] + 0.3, idx[-1], plan, va="center", fontsize=10,
             color=ACCENT if is_fam else "#7F7F7F", fontweight="bold" if is_fam else "normal")

fam_idx = fam["active_subscribers"].values / fam["active_subscribers"].values[0] * 100
ax2.scatter([6, 11], [fam_idx[6], fam_idx[11]], color=ACCENT, s=30, zorder=4)
ax2.annotate("14,358 → 11,625\n−19% since April",
             xy=(11, fam_idx[11]), xytext=(6.4, 76),
             fontsize=10, color=ACCENT, fontweight="bold", va="center",
             arrowprops=dict(arrowstyle="-", color=ACCENT, lw=0.8))

ax2.axhline(100, color="#DDDDDD", lw=0.8, zorder=1)
ax2.set_ylim(70, 145)
ax2.set_xlim(-0.5, 11.3)
ax2.set_xticks(x_all)
ax2.set_xticklabels(labels, fontsize=8.5)
ax2.set_ylabel("Active subscribers, index (Oct 2025 = 100)", fontsize=9.5)
ax2.set_title("Active subscribers at start of month, by plan", fontsize=11, loc="left", color=DARK)

for ax in (ax1, ax2):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors="#555555")
    ax.grid(axis="y", color="#EEEEEE", lw=0.8)
    ax.set_axisbelow(True)

fig.text(0.07, 0.04,
         "Note: September 2026 data cover 1–14 Sep only, so it is left out of the cancellation-rate panel. "
         "Its 3.1% rate reflects half a month,\nnot a recovery. Subscriber counts are taken at the start of each month, "
         "so September's is complete.",
         fontsize=8.8, color="#555555", ha="left", va="bottom")
