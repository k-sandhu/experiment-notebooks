import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Day-30 retention per sign-up cohort, the cleanest comparable metric across all cohorts
d30 = (df[df["day"] == 30]
       .sort_values("signup_month")
       .reset_index(drop=True))

month_names = {"01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May",
               "06": "Jun", "07": "Jul", "08": "Aug", "09": "Sep"}
d30["label"] = d30["signup_month"].str[-2:].map(month_names)

x = np.arange(len(d30))
is_new = d30["onboarding_version"].eq("new").values
is_campaign = d30["signup_month"].isin(["2026-06", "2026-07", "2026-08"]).values

old_avg = d30.loc[~is_new, "retention_pct"].mean()
new_campaign_avg = d30.loc[is_campaign, "retention_pct"].mean()
sep_val = d30.loc[d30["signup_month"] == "2026-09", "retention_pct"].iloc[0]
sep_idx = int(np.where(d30["signup_month"] == "2026-09")[0][0])

GREY = "#B5B5B5"
BLUE = "#1F6FB4"
DARK = "#333333"

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(top=0.80, bottom=0.14, left=0.08, right=0.97)

# TV campaign shading (context for the caveat)
ax.axvspan(x[is_campaign].min() - 0.5, x[is_campaign].max() + 0.5,
           color="#F1F1F1", zorder=0)
ax.text(x[is_campaign].mean(), 38.6, "TV campaign ran Jun–Aug\n(may have brought different users)",
        ha="center", va="top", fontsize=9.5, color="#666666")

# Bars
colors = np.where(is_new, BLUE, GREY)
ax.bar(x, d30["retention_pct"], color=colors, width=0.68, zorder=2)

# Launch marker
launch_x = x[is_new].min() - 0.5
ax.axvline(launch_x, color=DARK, lw=1, ls=(0, (3, 3)), zorder=3)
ax.text(launch_x - 0.08, 38.6, "New onboarding\nlaunched 1 Jun", ha="right", va="top",
        fontsize=9.5, color=DARK)

# Group averages (the numbers that carry the message)
ax.hlines(old_avg, x[~is_new].min() - 0.4, x[~is_new].max() + 0.4,
          color="#555555", lw=1.8, zorder=4)
ax.text(x[~is_new].mean(), old_avg + 1.0, f"Old onboarding avg {old_avg:.1f}%",
        ha="center", va="bottom", fontsize=11, color="#444444", fontweight="bold")

ax.hlines(new_campaign_avg, x[is_campaign].min() - 0.4, x[is_campaign].max() + 0.4,
          color="#0B3F6E", lw=1.8, zorder=4)
ax.text(x[is_campaign].mean(), new_campaign_avg + 1.0, f"New avg {new_campaign_avg:.1f}%",
        ha="center", va="bottom", fontsize=11, color=BLUE, fontweight="bold")

# September: the cohort after the campaign ended
ax.text(sep_idx, sep_val + 1.0, f"{sep_val:.1f}%", ha="center", va="bottom",
        fontsize=11, color=BLUE, fontweight="bold")
ax.annotate("After campaign ended:\nstill well above old flow",
            xy=(sep_idx, sep_val * 0.55), xytext=(sep_idx, sep_val * 0.55),
            ha="center", va="center", fontsize=9, color="white", fontweight="bold")

# Axes styling
ax.set_xticks(x)
ax.set_xticklabels(d30["label"], fontsize=11)
ax.set_xlabel("Sign-up month (2026 cohorts)", fontsize=10, color="#555555")
ax.set_ylabel("Day-30 retention (% of cohort)", fontsize=10, color="#555555")
ax.set_ylim(0, 40)
ax.set_xlim(-0.6, len(x) - 0.4)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.tick_params(colors="#555555")
ax.grid(axis="y", color="#E3E3E3", lw=0.8, zorder=0)
ax.set_axisbelow(True)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
for s in ["left", "bottom"]:
    ax.spines[s].set_color("#999999")

# Title states the decision-relevant message
fig.text(0.08, 0.94,
         "Keep the new onboarding: day-30 retention rose from 22% to 31%",
         fontsize=16, fontweight="bold", color="#111111", ha="left")
fig.text(0.08, 0.875,
         f"The lift held at {sep_val:.1f}% in September, after the TV campaign ended, "
         "so the campaign does not explain it all.\n"
         "Paid conversion within 30 days also rose, from 3.1% to 3.9%.",
         fontsize=10.5, color="#444444", ha="left", va="top")

fig.text(0.08, 0.025,
         "Retained on day 30 = completed a lesson on day 30 or later. September is a single cohort; "
         "data to 2 Nov 2026.",
         fontsize=8.5, color="#777777", ha="left")
