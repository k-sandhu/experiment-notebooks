import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

df = pd.read_csv("data.csv")

# One row per cohort, plus its day-30 retention
coh = (df.drop_duplicates("signup_month")
         .set_index("signup_month")[["onboarding_version", "cohort_size", "paid_conversion_30d_pct"]])
coh["d30"] = df[df["day"] == 30].set_index("signup_month")["retention_pct"]

months = coh.index.tolist()
labels = pd.to_datetime(months).strftime("%b")
x = np.arange(len(months))

OLD, NEW = "#B5B5B5", "#1F6FB4"
colors = [OLD if v == "old" else NEW for v in coh["onboarding_version"]]

is_old = coh["onboarding_version"] == "old"
tv = coh.index.isin(["2026-06", "2026-07", "2026-08"])
old_d30 = coh.loc[is_old, "d30"].mean()
new_d30 = coh.loc[tv, "d30"].mean()
sep_d30 = coh.loc["2026-09", "d30"]
old_paid = coh.loc[is_old, "paid_conversion_30d_pct"].mean()
new_paid = coh.loc[tv, "paid_conversion_30d_pct"].mean()

fig, axes = plt.subplots(1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [3, 2]})
fig.subplots_adjust(top=0.76, bottom=0.14, left=0.06, right=0.98, wspace=0.18)

panels = [
    (axes[0], coh["d30"], "Day-30 retention (% of cohort still active)", old_d30, "{:.1f}%", 38),
    (axes[1], coh["paid_conversion_30d_pct"], "Paid within 30 days (% of cohort)", old_paid, "{:.1f}%", 4.9),
]

for ax, vals, title, old_avg, fmt, ymax in panels:
    # TV campaign window
    ax.axvspan(4.5, 7.5, color="#FFF1C9", zorder=0)
    ax.text(6, ymax * 0.97, "TV campaign", ha="center", va="top",
            fontsize=9, color="#8A6D1A")

    bars = ax.bar(x, vals, color=colors, width=0.7, zorder=2)
    for xi, v in zip(x, vals):
        ax.text(xi, v + ymax * 0.012, fmt.format(v), ha="center", va="bottom",
                fontsize=9, color="#333333")

    # Old-onboarding baseline across all cohorts
    ax.axhline(old_avg, color="#555555", lw=1, ls="--", zorder=3)
    ax.text(len(x) - 0.55, old_avg - ymax * 0.015, f"old avg {fmt.format(old_avg)}",
            ha="right", va="top", fontsize=8.5, color="#555555", zorder=4,
            bbox=dict(facecolor="white", edgecolor="none", pad=1, alpha=0.85))

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9.5)
    ax.set_ylim(0, ymax)
    ax.set_yticks([])
    ax.set_title(title, loc="left", fontsize=11, color="#222222", pad=8)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#999999")
    ax.tick_params(axis="x", length=0)

# Call out September: the cohort after the campaign ended
axes[0].annotate("After campaign\nstill well above old",
                 xy=(8, sep_d30 + 2.6), xytext=(8, sep_d30 + 6.5),
                 ha="center", va="bottom", fontsize=8.5, color=NEW,
                 arrowprops=dict(arrowstyle="-|>", color=NEW, lw=1))

axes[0].legend(handles=[Patch(color=OLD, label="Old onboarding (Jan–May)"),
                        Patch(color=NEW, label="New onboarding (from 1 Jun)")],
               loc="upper left", frameon=False, fontsize=9)

fig.text(0.06, 0.95, "Keep the new onboarding: more users stay, and more pay",
         fontsize=16, fontweight="bold", color="#111111", ha="left")
fig.text(0.06, 0.885,
         f"Day-30 retention rose from {old_d30:.0f}% to {new_d30:.0f}% and held at {sep_d30:.0f}% in September, "
         f"after the TV campaign ended.\n"
         f"30-day paid conversion rose from {old_paid:.1f}% to {new_paid:.1f}%.",
         fontsize=10.5, color="#444444", ha="left", va="top")

fig.text(0.06, 0.03,
         "Retained on day 30 = completed a lesson on day 30 or later. Day-1 retention is ~70% for every cohort. "
         "Data to 2 Nov 2026. Bars show monthly sign-up cohorts.",
         fontsize=8, color="#777777", ha="left")
