import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Day-30 retention, one row per cohort
d30 = df[df["day"] == 30].copy().sort_values("signup_month").reset_index(drop=True)
# Paid conversion is repeated on every day row; keep one row per cohort
cohorts = df.drop_duplicates("signup_month").copy().sort_values("signup_month")

old_ret = d30[d30["onboarding_version"] == "old"]["retention_pct"].mean()          # Jan-May
new_ret = d30[(d30["signup_month"] >= "2026-06") & (d30["signup_month"] <= "2026-08")]["retention_pct"].mean()  # Jun-Aug
sep_ret = d30[d30["signup_month"] == "2026-09"]["retention_pct"].iloc[0]

old_paid = cohorts[cohorts["onboarding_version"] == "old"]["paid_conversion_30d_pct"].mean()
new_paid = cohorts[(cohorts["signup_month"] >= "2026-06") & (cohorts["signup_month"] <= "2026-08")]["paid_conversion_30d_pct"].mean()

STRONG = "#0F7B6C"
GREY = "#B8B8B8"

fig = plt.figure(figsize=(10, 6))
gs = fig.add_gridspec(1, 2, width_ratios=[3.2, 1.15], wspace=0.32,
                      left=0.07, right=0.97, top=0.84, bottom=0.16)
ax = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])

fig.suptitle("Keep the new onboarding: day-30 retention rose from 22.3% to 31.4%",
             fontsize=16, fontweight="bold", x=0.07, ha="left")

# --- Main panel: day-30 retention by cohort ---
x = range(len(d30))
cols = [GREY if v == "old" else STRONG for v in d30["onboarding_version"]]
ax.bar(x, d30["retention_pct"], color=cols, width=0.72, zorder=3)

# TV campaign window (the caveat, shown where it falls)
ax.axvspan(4.5, 7.5, color=STRONG, alpha=0.08, zorder=0)
ax.text(6, 36.5, "TV campaign", ha="center", fontsize=9, color="#444444", style="italic")
ax.axvline(4.5, color="#333333", linewidth=1.2, linestyle="--")

# Group-average lines, labelled directly (no legend, no per-bar labels)
ax.hlines(old_ret, -0.4, 4.4, color="#555555", linewidth=2)
ax.text(2, old_ret + 1.4, f"Old\n{old_ret:.1f}%", ha="center", fontsize=11,
        fontweight="bold", color="#555555")
ax.hlines(new_ret, 4.6, 7.4, color=STRONG, linewidth=2)
ax.text(6, new_ret + 1.4, f"New  {new_ret:.1f}%", ha="center", fontsize=11,
        fontweight="bold", color=STRONG)

# September: the one bar whose number matters — it answers the caveat
ax.text(8, sep_ret + 1.2, f"{sep_ret:.1f}%", ha="center", fontsize=11,
        fontweight="bold", color=STRONG)
ax.text(8, 36.5, "after\ncampaign", ha="center", fontsize=9, color="#444444", style="italic")
ax.text(4.6, 3, "New onboarding\nfrom 1 June", fontsize=9, color=STRONG, fontweight="bold")

ax.set_xticks(list(x))
ax.set_xticklabels([pd.to_datetime(m).strftime("%b") for m in d30["signup_month"]], fontsize=10)
ax.set_ylim(0, 40)
ax.set_ylabel("Day-30 retention (%)", fontsize=11)
ax.set_xlabel("Signup cohort", fontsize=11)
ax.set_title("Day-30 retention by cohort", fontsize=12, fontweight="bold", loc="left")
ax.yaxis.grid(True, color="#E5E5E5", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

# --- Side panel: paid conversion ---
ax2.bar([0, 1], [old_paid, new_paid], color=[GREY, STRONG], width=0.6, zorder=3)
ax2.text(0, old_paid + 0.12, f"{old_paid:.1f}%", ha="center", fontsize=11, fontweight="bold", color="#555555")
ax2.text(1, new_paid + 0.12, f"{new_paid:.1f}%", ha="center", fontsize=11, fontweight="bold", color=STRONG)
ax2.set_xticks([0, 1])
ax2.set_xticklabels(["Old\nJan–May", "New\nJun–Aug"], fontsize=10)
ax2.set_ylim(0, 5)
ax2.set_ylabel("Paid conversion within 30 days (%)", fontsize=10)
ax2.set_title("Paid conversion\nalso rose", fontsize=12, fontweight="bold", loc="left")
ax2.yaxis.grid(True, color="#E5E5E5", linewidth=0.8, zorder=0)
ax2.set_axisbelow(True)
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)

fig.text(0.07, 0.04,
         "Caveat: a TV campaign ran Jun–Aug, so part of that gain may be a different mix of users — "
         "but September, after it ended, still reached 28.6%.",
         fontsize=9, color="#444444", style="italic")
