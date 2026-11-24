import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("data.csv")

# Use only Day-30 retention, which is available for every cohort shown.
d30 = df[df["day"] == 30].copy()

old_avg = d30.loc[
    d30["onboarding_version"] == "old", "retention_pct"
].mean()

new_pre_campaign_avg = d30.loc[
    (d30["onboarding_version"] == "new") & (d30["signup_month"] < "2026-09"),
    "retention_pct"
].mean()

sep_post_campaign = d30.loc[
    (d30["onboarding_version"] == "new") & (d30["signup_month"] == "2026-09"),
    "retention_pct"
].iloc[0]

labels = [
    "Old onboarding\nJan–May avg",
    "New onboarding\nJun–Aug avg",
    "New onboarding\nSep (post-TV)"
]
values = [old_avg, new_pre_campaign_avg, sep_post_campaign]
colors = ["#BDBDBD", "#E4572E", "#E4572E"]

fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(values))

ax.bar(
    x, values, color=colors, width=0.55,
    edgecolor="white", linewidth=1.2, zorder=3
)

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=11)
ax.set_ylabel("Day-30 retention (%)", fontsize=11)
ax.set_ylim(0, 36)
ax.set_yticks(np.arange(0, 36, 5))

ax.grid(axis="y", color="#E6E6E6", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)

for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.spines["left"].set_color("#999999")
ax.spines["bottom"].set_color("#999999")
ax.tick_params(axis="x", length=0)
ax.tick_params(axis="y", colors="#555555")

# Direct labels: the levels and the post-campaign robustness check are the message.
for i, v in enumerate(values):
    label_color = "#666666" if i == 0 else "#E4572E"
    ax.text(
        i, v + 0.8, f"{v:.1f}%",
        ha="center", va="bottom",
        fontsize=12, fontweight="bold", color=label_color
    )

ax.set_title(
    "Keep the new onboarding: Day-30 retention is ~9 points higher, even after the TV campaign",
    fontsize=14.5, fontweight="bold", loc="left", pad=16
)

fig.text(
    0.01, 0.015,
    "Day-30 retention = active on day 30 or later. TV campaign ran Jun–Aug; Sep is the first post-campaign cohort.",
    fontsize=8.5, color="#555555"
)

fig.tight_layout(rect=[0, 0.05, 1, 1])
