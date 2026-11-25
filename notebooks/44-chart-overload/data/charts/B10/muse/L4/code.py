import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("data.csv")

# Decision metric only: Day-30 retention by cohort
d30 = df[df["day"] == 30].copy().sort_values("signup_month").reset_index(drop=True)
d30["month_label"] = pd.to_datetime(d30["signup_month"]).dt.strftime("%b")

old = d30[d30["onboarding_version"] == "old"]
new_campaign = d30[(d30["onboarding_version"] == "new") & (d30["signup_month"] <= "2026-08")]
sep_val = d30.loc[d30["signup_month"] == "2026-09", "retention_pct"].iloc[0]

old_avg = 100 * old["retained_users"].sum() / old["cohort_size"].sum()
new_avg = 100 * new_campaign["retained_users"].sum() / new_campaign["cohort_size"].sum()

GREY = "#B8B8B8"
TEAL = "#0F766E"
DARK = "#222222"
MIDGREY = "#666666"

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

x = np.arange(len(d30))
colors = [GREY if v == "old" else TEAL for v in d30["onboarding_version"]]
bars = ax.bar(x, d30["retention_pct"], color=colors, width=0.68, zorder=3)
# September is the clean post-campaign test — outline it
bars[-1].set_edgecolor("#0B4F4A")
bars[-1].set_linewidth(1.6)

# Group averages; new average covers Jun–Aug only, leaving Sep standing alone
ax.hlines(old_avg, -0.4, 4.4, colors=MIDGREY, linestyles="--", linewidth=1.4, zorder=4)
ax.hlines(new_avg, 4.6, 7.4, colors=TEAL, linestyles="--", linewidth=1.4, zorder=4)

# Launch divider between May and Jun
ax.axvline(4.5, color=MIDGREY, linewidth=1.0, linestyle=":", zorder=2, ymax=0.92)

# One stacked label per group, placed just above its average line
ax.text(2, old_avg + 3.6, "OLD onboarding", ha="center", va="bottom",
        fontsize=10, fontweight="bold", color=MIDGREY)
ax.text(2, old_avg + 0.9, f"avg {old_avg:.1f}%", ha="center", va="bottom",
        fontsize=13, fontweight="bold", color=MIDGREY)

ax.text(6, new_avg + 3.6, "NEW onboarding · from 1 June", ha="center", va="bottom",
        fontsize=10, fontweight="bold", color=TEAL)
ax.text(6, new_avg + 0.9, f"avg {new_avg:.1f}%", ha="center", va="bottom",
        fontsize=13, fontweight="bold", color=TEAL)

# September: the only other number that matters
ax.text(8, sep_val + 2.8, "after TV ended", ha="center", va="bottom",
        fontsize=9, color=TEAL)
ax.text(8, sep_val + 0.9, f"{sep_val:.1f}%", ha="center", va="bottom",
        fontsize=13, fontweight="bold", color=TEAL)

ax.set_xlim(-0.6, 8.6)
ax.set_ylim(0, 39)
ax.set_xticks(x)
ax.set_xticklabels(d30["month_label"])
ax.set_yticks([0, 10, 20, 30])
ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0f}%")
ax.set_ylabel("Day-30 retention\n(% of cohort still active)", fontsize=11, color=DARK)
ax.set_xlabel("Signup cohort (2026)", fontsize=11, color=DARK)
ax.tick_params(axis="x", labelsize=11, length=0)
ax.tick_params(axis="y", labelsize=10)
ax.grid(axis="y", color="#E6E6E6", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color("#999999")

fig.text(0.07, 0.97,
         "Keep the new onboarding: Day-30 retention jumped\n"
         f"from {old_avg:.0f}% to {new_avg:.0f}% — and held up after the TV campaign",
         ha="left", va="top", fontsize=17, fontweight="bold", color=DARK)

fig.text(0.07, 0.02,
         "Retained = completed a lesson on day 30 or later.  "
         "TV campaign ran Jun–Aug, so Sep is the first post-campaign test of the new flow.",
         ha="left", va="bottom", fontsize=8.5, color=MIDGREY)

fig.tight_layout(rect=[0, 0.05, 1, 0.86])
