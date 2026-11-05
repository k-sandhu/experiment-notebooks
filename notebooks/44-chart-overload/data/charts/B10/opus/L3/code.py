import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Day-30 retention per cohort
d30 = df[df["day"] == 30].copy().sort_values("signup_month").reset_index(drop=True)
d30["label"] = pd.to_datetime(d30["signup_month"]).dt.strftime("%b")

old = d30[d30["onboarding_version"] == "old"]
campaign = d30[d30["signup_month"].isin(["2026-06", "2026-07", "2026-08"])]
sep = d30[d30["signup_month"] == "2026-09"]

old_ret = old["retention_pct"].mean()           # 22.3
camp_ret = campaign["retention_pct"].mean()     # 31.4
sep_ret = sep["retention_pct"].iloc[0]          # 28.6

old_conv = old["paid_conversion_30d_pct"].mean()        # 3.1
camp_conv = campaign["paid_conversion_30d_pct"].mean()  # 3.9

GREY = "#B5B5B5"
BLUE = "#1F6FB4"
DARK = "#333333"

fig, (ax, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [3.2, 1], "wspace": 0.35}
)

# ---------- Left panel: day-30 retention by cohort ----------
x = range(len(d30))
colors = [BLUE if v == "new" else GREY for v in d30["onboarding_version"]]
ax.bar(x, d30["retention_pct"], color=colors, width=0.7, zorder=2)

# TV campaign band (Jun–Aug)
camp_idx = list(campaign.index)
ax.axvspan(camp_idx[0] - 0.45, camp_idx[-1] + 0.45, color="#F1F1F1", zorder=0)
ax.text((camp_idx[0] + camp_idx[-1]) / 2, 39.2, "TV campaign\n(Jun–Aug)",
        ha="center", va="top", fontsize=9.5, color="#666666")

# Group average lines + labels
old_idx = list(old.index)
ax.hlines(old_ret, old_idx[0] - 0.4, old_idx[-1] + 0.4, color=DARK, lw=1.5,
          linestyles="--", zorder=3)
ax.text((old_idx[0] + old_idx[-1]) / 2, old_ret + 1.0,
        f"Old onboarding: {old_ret:.1f}% avg", ha="center", va="bottom",
        fontsize=10.5, color=DARK)

ax.hlines(camp_ret, camp_idx[0] - 0.4, camp_idx[-1] + 0.4, color=DARK, lw=1.5,
          linestyles="--", zorder=3)
ax.text((camp_idx[0] + camp_idx[-1]) / 2, camp_ret + 1.0,
        f"New: {camp_ret:.1f}% avg", ha="center", va="bottom",
        fontsize=10.5, color=BLUE, fontweight="bold")

sep_i = sep.index[0]
ax.text(sep_i, sep_ret + 1.0, f"{sep_ret:.1f}%\nafter\ncampaign", ha="center",
        va="bottom", fontsize=10, color=BLUE, fontweight="bold")

ax.set_xticks(list(x))
ax.set_xticklabels(d30["label"], fontsize=10)
ax.set_ylim(0, 40)
ax.set_ylabel("Users active at day 30 (% of cohort)", fontsize=10)
ax.set_title("Day-30 retention by 2026 sign-up month", loc="left",
             fontsize=11.5, color=DARK)

# ---------- Right panel: 30-day paid conversion ----------
labels = ["Old\nJan–May", "New\nJun–Aug"]
vals = [old_conv, camp_conv]
ax2.bar([0, 1], vals, color=[GREY, BLUE], width=0.6, zorder=2)
for i, v in enumerate(vals):
    ax2.text(i, v + 0.1, f"{v:.1f}%", ha="center", va="bottom", fontsize=11,
             color=BLUE if i == 1 else DARK, fontweight="bold" if i == 1 else None)
ax2.set_xticks([0, 1])
ax2.set_xticklabels(labels, fontsize=10)
ax2.set_ylim(0, 4.8)
ax2.set_ylabel("Paid within 30 days (% of cohort)", fontsize=10)
ax2.set_title("Paid conversion", loc="left", fontsize=11.5, color=DARK)

for a in (ax, ax2):
    a.spines[["top", "right"]].set_visible(False)
    a.tick_params(axis="y", labelsize=9, colors="#666666")
    a.grid(axis="y", color="#E5E5E5", lw=0.8, zorder=0)

fig.suptitle(
    "Keep the new onboarding: day-30 retention rose from 22% to 31%,\n"
    "and still held at 29% after the TV campaign ended",
    x=0.06, y=0.98, ha="left", fontsize=15, fontweight="bold", color="#111111",
)
fig.text(
    0.06, 0.02,
    "Caveat: the TV campaign overlapped the new onboarding (Jun–Aug), so part of that "
    "gain may reflect different users; September is the cleanest read.",
    ha="left", fontsize=9, color="#555555",
)
fig.subplots_adjust(left=0.08, right=0.98, top=0.83, bottom=0.12)
