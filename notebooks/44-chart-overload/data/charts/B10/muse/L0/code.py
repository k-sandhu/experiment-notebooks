import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

df = pd.read_csv("data.csv")
df = df.sort_values(["signup_month", "day"])

OLD = "#4C72B0"
NEW = "#DD8452"
SEP = "#55A868"
GREY = "#555555"

days = [1, 7, 14, 30, 60, 90]
x_of_day = {d: i for i, d in enumerate(days)}

old = df[df["onboarding_version"] == "old"]
new_main = df[(df["onboarding_version"] == "new") & (df["signup_month"] <= "2026-08")]
sep = df[df["signup_month"] == "2026-09"]

old_avg = old.groupby("day")["retention_pct"].mean().reindex(days)
new_avg = new_main.groupby("day")["retention_pct"].mean().reindex(days)

# One-row-per-cohort metrics (repeated on every day-row in the file)
cohorts = df.drop_duplicates("signup_month")
old_c = cohorts[cohorts["onboarding_version"] == "old"]
new_c = cohorts[(cohorts["onboarding_version"] == "new") & (cohorts["signup_month"] <= "2026-08")]
paid_old, paid_new = old_c["paid_conversion_30d_pct"].mean(), new_c["paid_conversion_30d_pct"].mean()
les_old, les_new = old_c["avg_lessons_first_30d"].mean(), new_c["avg_lessons_first_30d"].mean()
les_gain = 100 * (les_new - les_old) / les_old

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.55, 1.0]}
)
fig.subplots_adjust(left=0.07, right=0.97, top=0.82, bottom=0.20, wspace=0.28)

fig.suptitle("New onboarding cohorts retain far better after week 1",
             fontsize=15, fontweight="bold", x=0.07, ha="left")
fig.text(0.07, 0.905,
         "Day-1 retention is unchanged at ~70%; the gap opens by day 7 and persists to day 90.",
         fontsize=10, color=GREY, ha="left")

# ---- Panel A: retention curves ----
for month, g in df[df["signup_month"] != "2026-09"].groupby("signup_month"):
    color = OLD if g["onboarding_version"].iloc[0] == "old" else NEW
    ax1.plot([x_of_day[d] for d in g["day"]], g["retention_pct"],
             color=color, lw=1.0, alpha=0.35, marker="o", ms=3, zorder=2)

ax1.plot(range(len(days)), old_avg, color=OLD, lw=3, marker="o", ms=5, zorder=4,
         label="Old onboarding (Jan-May, mean)")
ax1.plot(range(len(days)), new_avg, color=NEW, lw=3, marker="o", ms=5, zorder=4,
         label="New onboarding (Jun-Aug, mean)")
ax1.plot([x_of_day[d] for d in sep["day"]], sep["retention_pct"], color=SEP,
         lw=2, ls="--", marker="o", ms=4, zorder=4,
         label="September only (post-campaign, to day 30)")

ax1.text(5.08, old_avg.loc[90], f"{old_avg.loc[90]:.1f}%", color=OLD,
         fontweight="bold", va="center", fontsize=9)
ax1.text(5.08, new_avg.loc[90] + 1.2, f"{new_avg.loc[90]:.1f}%", color=NEW,
         fontweight="bold", va="center", fontsize=9)
ax1.annotate(f"Day 30: {old_avg.loc[30]:.1f}% vs {new_avg.loc[30]:.1f}%",
             xy=(3, new_avg.loc[30]), xytext=(2.35, 46),
             fontsize=9, fontweight="bold", color="#222222",
             arrowprops=dict(arrowstyle="->", color=GREY, lw=1))
ax1.annotate("both ~70% at day 1", xy=(0, 69.5), xytext=(0.45, 63),
             fontsize=8.5, color=GREY,
             arrowprops=dict(arrowstyle="->", color=GREY, lw=0.8))

ax1.set_title("A. Retention by days since sign-up", loc="left", fontsize=11, fontweight="bold")
ax1.set_xticks(range(len(days)))
ax1.set_xticklabels([f"Day {d}" for d in days])
ax1.set_xlim(-0.2, 5.9)
ax1.set_ylim(0, 78)
ax1.set_ylabel("Retained users (% of cohort)")
ax1.grid(axis="y", color="#DDDDDD", lw=0.7)
ax1.set_axisbelow(True)
for s in ("top", "right"):
    ax1.spines[s].set_visible(False)
ax1.legend(handles=[
    Line2D([0], [0], color=OLD, lw=3, marker="o", label="Old (Jan-May) mean; thin = each cohort"),
    Line2D([0], [0], color=NEW, lw=3, marker="o", label="New (Jun-Aug) mean; thin = each cohort"),
    Line2D([0], [0], color=SEP, lw=2, ls="--", marker="o", label="Sep (post-campaign), to day 30"),
], frameon=False, fontsize=8, loc="lower left")

# ---- Panel B: day-30 retention by cohort ----
d30 = df[df["day"] == 30].sort_values("signup_month").reset_index(drop=True)
labels = pd.to_datetime(d30["signup_month"]).dt.strftime("%b")
colors = [SEP if m == "2026-09" else (OLD if v == "old" else NEW)
          for m, v in zip(d30["signup_month"], d30["onboarding_version"])]

ax2.axvspan(4.5, 8.5, color=NEW, alpha=0.07, zorder=0)
bars = ax2.bar(range(len(d30)), d30["retention_pct"], color=colors, zorder=3, width=0.68)
bars[-1].set_hatch("///")
bars[-1].set_edgecolor("white")

for i, v in enumerate(d30["retention_pct"]):
    ax2.text(i, v + 0.6, f"{v:.1f}%", ha="center", fontsize=7.5, color=GREY)

ax2.plot([-0.5, 4.5], [old_avg.loc[30]] * 2, color=OLD, lw=2, ls="--", zorder=4)
ax2.plot([4.5, 7.5], [new_avg.loc[30]] * 2, color=NEW, lw=2, ls="--", zorder=4)
ax2.text(2, old_avg.loc[30] - 2.2, f"old mean {old_avg.loc[30]:.1f}%",
         ha="center", fontsize=8.5, color=OLD, fontweight="bold")
ax2.text(6, new_avg.loc[30] + 1.6, f"new mean {new_avg.loc[30]:.1f}%",
         ha="center", fontsize=8.5, color=NEW, fontweight="bold")
ax2.annotate("", xy=(4.35, new_avg.loc[30]), xytext=(4.35, old_avg.loc[30]),
             arrowprops=dict(arrowstyle="<->", color="#222222", lw=1.2))
ax2.text(4.25, (old_avg.loc[30] + new_avg.loc[30]) / 2,
         f"+{new_avg.loc[30] - old_avg.loc[30]:.1f} pp",
         ha="right", va="center", fontsize=9, fontweight="bold")
ax2.text(4.5, 35.2, "  new onboarding from Jun ->", fontsize=8, color=GREY, va="top")

ax2.set_title("B. Day-30 retention by sign-up cohort", loc="left", fontsize=11, fontweight="bold")
ax2.set_xticks(range(len(d30)))
ax2.set_xticklabels(labels, rotation=45, ha="right")
ax2.set_xlim(-0.6, 8.6)
ax2.set_ylim(0, 37)
ax2.set_ylabel("Day-30 retention (% of cohort)")
ax2.grid(axis="y", color="#DDDDDD", lw=0.7)
ax2.set_axisbelow(True)
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)

ax2.text(0.0, -0.30,
         f"Also up Jun-Aug vs Jan-May: paid conversion (30d) "
         f"{paid_old:.1f}% -> {paid_new:.1f}%;\n"
         f"lessons in first 30d {les_old:.1f} -> {les_new:.1f} (+{les_gain:.0f}%).",
         transform=ax2.transAxes, fontsize=8.5, color="#222222", va="top",
         bbox=dict(boxstyle="round,pad=0.4", facecolor="#F2F2F2", edgecolor="#CCCCCC"))

fig.text(0.07, 0.045,
         "Caution: a TV campaign ran Jun-Aug, so part of the gain may reflect different users rather than onboarding alone. "
         "September (after the campaign)\nstill reached 28.6% at day 30.",
         fontsize=8, color=GREY, ha="left", va="bottom")
fig.text(0.07, 0.008,
         "Data to 2 Nov 2026: August is measured to day 60 and September to day 30, so the new-cohort day-90 point uses Jun-Jul only. "
         "Retained on day N = completed a lesson on day N or later.",
         fontsize=7.5, color=GREY, ha="left", va="bottom")
