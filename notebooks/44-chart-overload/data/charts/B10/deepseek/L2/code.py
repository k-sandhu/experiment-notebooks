import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("data.csv")

# Decision-relevant data: Day-30 retention by signup cohort
d30 = df[df["day"] == 30].copy()
d30 = d30.sort_values("signup_month").reset_index(drop=True)

months = pd.to_datetime(d30["signup_month"]).dt.strftime("%b")
x = np.arange(len(d30))
colors = np.where(d30["onboarding_version"] == "old", "#BDBDBD", "#E4572E")

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(x, d30["retention_pct"], color=colors, width=0.65, zorder=3)

ax.set_xticks(x)
ax.set_xticklabels(months, fontsize=10)
ax.set_ylabel("Day-30 retention (%)", fontsize=10)
ax.set_ylim(0, 40)
ax.grid(axis="y", color="#E6E6E6", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)

for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)

ax.set_title(
    "Keep the new onboarding: Day-30 retention is higher, even after the TV campaign",
    fontsize=14, fontweight="bold", loc="left", pad=14
)

# Divider and direct group labels
ax.axvline(4.5, color="#999999", linestyle=":", linewidth=1.2, zorder=2)
ax.text(2, 38.3, "Old onboarding", ha="center", va="center",
        color="#777777", fontsize=9)
ax.text(6.5, 38.3, "New onboarding", ha="center", va="center",
        color="#E4572E", fontsize=9, fontweight="bold")

# Old-flow average reference
old_avg = d30.loc[d30["onboarding_version"] == "old", "retention_pct"].mean()
ax.axhline(old_avg, color="#777777", linestyle="--", linewidth=1.0,
           alpha=0.8, zorder=2)
ax.text(8.35, old_avg + 0.7, f"Old-flow avg {old_avg:.1f}%",
        ha="right", va="bottom", color="#777777", fontsize=8.5)

# New-flow average and post-TV September label
new_avg = d30.loc[
    (d30["onboarding_version"] == "new") & (d30["signup_month"] < "2026-09"),
    "retention_pct"
].mean()

ax.plot([5, 5, 7, 7], [35.0, 36.0, 36.0, 35.0],
        color="#E4572E", linewidth=1.2, clip_on=False)
ax.text(6, 36.2, f"Jun–Aug avg {new_avg:.1f}%", ha="center", va="bottom",
        color="#E4572E", fontsize=9, fontweight="bold")

sep_pos = d30.index[d30["signup_month"] == "2026-09"][0]
sep_val = d30.loc[sep_pos, "retention_pct"]
ax.text(sep_pos, sep_val + 0.8, f"{sep_val:.1f}%", ha="center", va="bottom",
        color="#E4572E", fontsize=9, fontweight="bold")
ax.annotate(
    "post-TV", xy=(sep_pos, sep_val + 0.1), xytext=(sep_pos, sep_val + 5.5),
    ha="center", va="bottom", fontsize=8, color="#555555",
    arrowprops=dict(arrowstyle="-", color="#999999", lw=0.8)
)

fig.text(
    0.01, 0.01,
    "TV campaign ran Jun–Aug; the September cohort (after the campaign) still reaches 28.6% at Day 30.",
    fontsize=8, color="#555555"
)

fig.tight_layout(rect=[0, 0.04, 1, 1])
