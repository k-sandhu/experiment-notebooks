import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")
df["month_label"] = pd.to_datetime(df["signup_month"]).dt.strftime("%b")

C_OLD = "#9a9a9a"
C_NEW = "#1f6fb4"
C_SEP = "#d95f02"

def cohort_color(month, version):
    if version == "old":
        return C_OLD
    if month == "2026-09":
        return C_SEP
    return C_NEW

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1.45, 1]}
)

# Left panel: retention curves by cohort
for (month, version), g in df.groupby(["signup_month", "onboarding_version"], sort=True):
    g = g.sort_values("day")
    col = cohort_color(month, version)
    ax1.plot(
        g["day"], g["retention_pct"],
        color=col, lw=2.2 if version == "new" else 1.4,
        alpha=0.95 if version == "new" else 0.8,
        marker="o", ms=3.5,
    )

# Legend entries
ax1.plot([], [], color=C_OLD, lw=1.6, marker="o", ms=3.5, label="Old onboarding (Jan–May cohorts)")
ax1.plot([], [], color=C_NEW, lw=2.2, marker="o", ms=3.5, label="New onboarding, during TV campaign (Jun–Aug)")
ax1.plot([], [], color=C_SEP, lw=2.2, marker="o", ms=3.5, label="New onboarding, after campaign (Sep)")
ax1.legend(loc="upper right", fontsize=8.5, frameon=False)

ax1.annotate(
    "Day 1: ~70% in every cohort,\nbefore and after the change",
    xy=(1, 70), xytext=(12, 63), fontsize=8.5, color="#333333",
    arrowprops=dict(arrowstyle="-", color="#666666", lw=0.8),
)
ax1.annotate(
    "Gap opens after day 1:\n~22% vs ~31% at day 30",
    xy=(30, 27), xytext=(36, 33), fontsize=8.5, color="#333333",
    arrowprops=dict(arrowstyle="-", color="#666666", lw=0.8),
)

ax1.set_xticks([1, 7, 14, 30, 60, 90])
ax1.set_xlim(0, 93)
ax1.set_ylim(0, 75)
ax1.set_xlabel("Days since sign-up")
ax1.set_ylabel("Users retained (% of cohort)")
ax1.set_title("Retention curve by monthly cohort", fontsize=11, loc="left")
ax1.grid(axis="y", color="#e5e5e5", lw=0.8)
ax1.spines[["top", "right"]].set_visible(False)

# Right panel: day-30 retention by cohort
d30 = (
    df[df["day"] == 30]
    .sort_values("signup_month")
    .reset_index(drop=True)
)
x = np.arange(len(d30))
colors = [cohort_color(m, v) for m, v in zip(d30["signup_month"], d30["onboarding_version"])]

camp_idx = d30.index[d30["signup_month"].isin(["2026-06", "2026-07", "2026-08"])]
ax2.axvspan(camp_idx.min() - 0.5, camp_idx.max() + 0.5, color="#f1f1f1", zorder=0)
ax2.text((camp_idx.min() + camp_idx.max()) / 2, 37, "TV campaign", ha="center",
         va="center", fontsize=8.5, color="#555555")

bars = ax2.bar(x, d30["retention_pct"], color=colors, width=0.7, zorder=2)
for xi, v in zip(x, d30["retention_pct"]):
    ax2.text(xi, v + 0.5, f"{v:.1f}", ha="center", va="bottom", fontsize=8, color="#333333")

old_mask = d30["onboarding_version"] == "old"
old_avg = d30.loc[old_mask, "retention_pct"].mean()
new_avg = d30.loc[d30.index.isin(camp_idx), "retention_pct"].mean()
old_idx = d30.index[old_mask]
ax2.hlines(old_avg, old_idx.min() - 0.4, old_idx.max() + 0.4, colors="#555555",
           linestyles="--", lw=1, zorder=3)
ax2.text(old_idx.min() - 0.4, old_avg + 4.2, f"Old avg {old_avg:.1f}%",
         fontsize=8, color="#555555", ha="left")
ax2.hlines(new_avg, camp_idx.min() - 0.4, camp_idx.max() + 0.4, colors=C_NEW,
           linestyles="--", lw=1, zorder=3)

ax2.set_xticks(x)
ax2.set_xticklabels(d30["month_label"])
ax2.set_ylim(0, 39)
ax2.set_xlabel("Sign-up month (2026)")
ax2.set_ylabel("Day-30 retention (%)")
ax2.set_title("Day-30 retention by cohort", fontsize=11, loc="left")
ax2.grid(axis="y", color="#e5e5e5", lw=0.8, zorder=0)
ax2.spines[["top", "right"]].set_visible(False)

fig.suptitle(
    "New onboarding lifted day-30 retention from ~22% to ~31%, with no change at day 1",
    fontsize=13, fontweight="bold", x=0.01, ha="left", y=0.985,
)
fig.text(
    0.01, 0.915,
    "A TV campaign ran over the same months (Jun–Aug), so part of the gain may come from a different user mix. "
    "The September cohort,\nwhich signed up after the campaign, still reached 28.6% at day 30.",
    fontsize=9, color="#444444", ha="left", va="top",
)
fig.text(
    0.01, 0.01,
    "Retained on day N = completed a lesson on day N or later. Data through 2 Nov 2026: "
    "August cohort measured to day 60, September to day 30.",
    fontsize=7.5, color="#777777", ha="left", va="bottom",
)

fig.tight_layout(rect=[0, 0.04, 1, 0.86])
