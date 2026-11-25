import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Day-30 cohort data
d30 = df[df["day"] == 30].copy()
d30["date"] = pd.to_datetime(d30["signup_month"] + "-01")
d30 = d30.sort_values("date").reset_index(drop=True)
labels = d30["date"].dt.strftime("%b")
x = np.arange(len(d30))

colors = np.where(d30["onboarding_version"] == "new", "#1f77b4", "#b3b3b3")

old = d30[d30["onboarding_version"] == "old"]
new = d30[d30["onboarding_version"] == "new"]
new_jun_aug = new[new["signup_month"].isin(["2026-06", "2026-07", "2026-08"])]

old_ret_avg = old["retention_pct"].mean()
new_ret_avg = new_jun_aug["retention_pct"].mean()
old_conv_avg = old["paid_conversion_30d_pct"].mean()
new_conv_avg = new_jun_aug["paid_conversion_30d_pct"].mean()

sep = d30[d30["signup_month"] == "2026-09"].iloc[0]
sep_idx = d30.index[d30["signup_month"] == "2026-09"][0]

fig = plt.figure(figsize=(10, 6))
gs = fig.add_gridspec(
    2, 1, height_ratios=[4.2, 1.3], hspace=0.18,
    left=0.09, right=0.97, top=0.86, bottom=0.10
)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1], sharex=ax1)

# Shade TV campaign period
ax1.axvspan(4.5, 7.5, color="#f0f0f0", zorder=0)
ax2.axvspan(4.5, 7.5, color="#f0f0f0", zorder=0)

# Main panel: day-30 retention
ax1.bar(
    x, d30["retention_pct"], color=colors, width=0.70,
    edgecolor="white", linewidth=0.6, zorder=3
)

ax1.text(2.0, 41.2, "Old onboarding", ha="center", va="center",
         fontsize=9, color="#777777", fontweight="bold")
ax1.text(6.5, 41.2, "New onboarding", ha="center", va="center",
         fontsize=9, color="#1f77b4", fontweight="bold")
ax1.text(6.0, 36.0, "TV campaign\nJun–Aug", ha="center", va="center",
         fontsize=8.5, color="#555555")

ax1.hlines(old_ret_avg, x[0] - 0.4, x[4] + 0.4,
           colors="#777777", linestyles="--", linewidth=1.1, zorder=4)
ax1.hlines(new_ret_avg, x[5] - 0.4, x[7] + 0.4,
           colors="#1f77b4", linestyles="--", linewidth=1.1, zorder=4)
ax1.text(x[2], old_ret_avg + 0.8, f"Old avg {old_ret_avg:.1f}%",
         ha="center", va="bottom", fontsize=9, color="#555555")
ax1.text((x[5] + x[7]) / 2, new_ret_avg + 0.8, f"New avg {new_ret_avg:.1f}%",
         ha="center", va="bottom", fontsize=9, color="#1f77b4")

ax1.text(
    sep_idx, sep["retention_pct"] + 0.8,
    f"{sep['retention_pct']:.1f}%\nafter campaign",
    ha="center", va="bottom", fontsize=9,
    color="#1f77b4", fontweight="bold"
)

ax1.set_ylabel("Day-30 retention (%)", fontsize=10)
ax1.set_ylim(0, 43)
ax1.set_yticks([0, 10, 20, 30, 40])
ax1.grid(axis="y", color="#dddddd", linewidth=0.6, zorder=0)
ax1.set_axisbelow(True)
ax1.tick_params(axis="x", labelbottom=False)

# Bottom panel: paid conversion within 30 days
conv = d30["paid_conversion_30d_pct"].values
ax2.bar(
    x, conv, color=colors, width=0.70,
    edgecolor="white", linewidth=0.6, zorder=3
)

ax2.hlines(old_conv_avg, x[0] - 0.4, x[4] + 0.4,
           colors="#777777", linestyles="--", linewidth=1.0, zorder=4)
ax2.hlines(new_conv_avg, x[5] - 0.4, x[7] + 0.4,
           colors="#1f77b4", linestyles="--", linewidth=1.0, zorder=4)
ax2.text(x[2], old_conv_avg + 0.15, f"Old avg {old_conv_avg:.1f}%",
         ha="center", va="bottom", fontsize=8, color="#555555")
ax2.text((x[5] + x[7]) / 2, new_conv_avg + 0.15, f"New avg {new_conv_avg:.1f}%",
         ha="center", va="bottom", fontsize=8, color="#1f77b4")

ax2.set_ylabel("Paid conversion\nwithin 30d (%)", fontsize=9)
ax2.set_ylim(0, 4.8)
ax2.set_yticks([0, 2, 4])
ax2.grid(axis="y", color="#dddddd", linewidth=0.6, zorder=0)
ax2.set_axisbelow(True)
ax2.set_xticks(x)
ax2.set_xticklabels(labels, fontsize=9)
ax2.set_xlabel("Signup month", fontsize=9)

for ax in [ax1, ax2]:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

fig.suptitle(
    "New onboarding lifted day-30 retention and paid conversion; September suggests the gain survives the TV campaign",
    fontsize=12.5, fontweight="bold", y=0.975
)
