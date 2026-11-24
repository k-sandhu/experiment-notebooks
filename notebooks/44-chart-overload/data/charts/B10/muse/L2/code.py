import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Decision metric only: Day-30 retention by cohort
d30 = df[df["day"] == 30].copy().sort_values("signup_month").reset_index(drop=True)
d30["month_label"] = pd.to_datetime(d30["signup_month"]).dt.strftime("%b")

old = d30[d30["onboarding_version"] == "old"]
new_campaign = d30[(d30["onboarding_version"] == "new") & (d30["signup_month"] <= "2026-08")]
sep = d30[d30["signup_month"] == "2026-09"].iloc[0]

old_avg = 100 * old["retained_users"].sum() / old["cohort_size"].sum()
new_avg = 100 * new_campaign["retained_users"].sum() / new_campaign["cohort_size"].sum()
sep_val = sep["retention_pct"]

GREY = "#B8B8B8"
TEAL = "#0F766E"
DARK = "#222222"

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

colors = [GREY if v == "old" else TEAL for v in d30["onboarding_version"]]
ax.bar(d30["month_label"], d30["retention_pct"], color=colors, width=0.68, zorder=3)

# Group averages (Jun-Aug for new, so September stays visible as the clean test)
ax.hlines(old_avg, -0.5, 4.5, colors="#666666", linestyles="--", linewidth=1.4, zorder=4)
ax.hlines(new_avg, 4.5, 7.5, colors=TEAL, linestyles="--", linewidth=1.4, zorder=4)

# Launch divider
ax.axvline(4.5, color="#666666", linewidth=1.0, linestyle=":", zorder=2)

# Direct labels instead of a legend
ax.text(2, 36.2, "OLD onboarding", ha="center", va="center",
        fontsize=11, fontweight="bold", color="#666666")
ax.text(6.5, 36.2, "NEW onboarding\n(from 1 June)", ha="center", va="center",
        fontsize=11, fontweight="bold", color=TEAL)

# Only the numbers that carry the message
ax.text(2, old_avg + 1.0, f"avg {old_avg:.1f}%", ha="center", va="bottom",
        fontsize=12, fontweight="bold", color="#666666")
ax.text(6, new_avg + 1.0, f"avg {new_avg:.1f}%", ha="center", va="bottom",
        fontsize=12, fontweight="bold", color=TEAL)
ax.annotate(f"Sep: {sep_val:.1f}%\nafter TV campaign ended",
            xy=(8, sep_val), xytext=(8, sep_val + 3.2),
            ha="center", va="bottom", fontsize=11, fontweight="bold", color=TEAL,
            arrowprops=dict(arrowstyle="-", color=TEAL, lw=1.2))

# Caveat on the chart: TV campaign coincides with Jun-Aug
ax.annotate("", xy=(5, 33.8), xytext=(7, 33.8),
            arrowprops=dict(arrowstyle="-", color="#888888", lw=1.2))
ax.text(6, 34.3, "TV campaign", ha="center", va="bottom", fontsize=9, color="#666666")

ax.set_ylim(0, 39)
ax.set_ylabel("Day-30 retention\n(% of cohort still active)", fontsize=11, color=DARK)
ax.set_xlabel("Signup cohort (2026)", fontsize=11, color=DARK)
ax.tick_params(axis="x", labelsize=11, length=0)
ax.tick_params(axis="y", labelsize=10)
ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0f}%")
ax.grid(axis="y", color="#E6E6E6", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax.spines[spine].set_visible(False)
ax.spines["bottom"].set_color("#999999")

fig.suptitle("Keep the new onboarding: Day-30 retention jumped\n"
             f"from {old_avg:.0f}% to {new_avg:.0f}% — and held up after the TV campaign",
             x=0.07, y=0.97, ha="left", va="top",
             fontsize=17, fontweight="bold", color=DARK)

fig.text(0.07, 0.02,
         "Retained = completed a lesson on day 30 or later.  "
         "TV campaign ran Jun–Aug, so Sep is the first post-campaign test of the new flow.",
         ha="left", va="bottom", fontsize=8.5, color="#666666")

fig.tight_layout(rect=[0, 0.05, 1, 0.86])
