import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

RED = "#C1272D"
GREY = "#BDBDBD"
DARK = "#222222"

latest_q = df["quarter"].max()  # 2026Q3

# --- Data needed for the decision -----------------------------------------
# Change in return rate: Q3 2026 vs average of all previous quarters
current = df[df["quarter"] == latest_q].set_index("category")["return_rate_pct"]
prior_avg = (
    df[df["quarter"] < latest_q]
    .groupby("category")["return_rate_pct"]
    .mean()
)
change = (current - prior_avg).sort_values(ascending=True)  # Footwear ends on top

# Footwear defect share: prior average vs Q3 2026
foot = df[df["category"] == "Footwear"]
foot_now_rate = foot.loc[foot["quarter"] == latest_q, "return_rate_pct"].iloc[0]
foot_prior_rate = foot.loc[foot["quarter"] < latest_q, "return_rate_pct"].mean()
foot_now_defect = foot.loc[foot["quarter"] == latest_q,
                           "defect_share_of_returns_pct"].iloc[0]
foot_prior_defect = foot.loc[foot["quarter"] < latest_q,
                             "defect_share_of_returns_pct"].mean()
jump = foot_now_rate - foot_prior_rate

# --- Figure ---------------------------------------------------------------
fig = plt.figure(figsize=(10, 6))
gs = fig.add_gridspec(1, 2, width_ratios=[1.65, 1.0], wspace=0.34)
ax0 = fig.add_subplot(gs[0, 0])
ax1 = fig.add_subplot(gs[0, 1])
fig.subplots_adjust(left=0.115, right=0.975, top=0.80, bottom=0.20)

fig.suptitle(
    "Investigate Footwear first: defects drove its return rate\n"
    f"to {foot_now_rate:.1f}% in Q3 2026",
    x=0.115, y=0.97, ha="left", va="top",
    fontsize=16, fontweight="bold", color=DARK,
)

# --- Left panel: only Footwear jumped -------------------------------------
colors = [RED if c == "Footwear" else GREY for c in change.index]
ax0.barh(change.index, change.values, color=colors, height=0.62)
ax0.axvline(0, color=DARK, linewidth=0.9)
ax0.set_xlim(-2.2, 14.5)
ax0.set_xlabel("Change in return rate, Q3 2026 vs prior average\n(percentage points)",
               fontsize=9.5, color=DARK)
ax0.set_title("Only Footwear jumped", loc="left",
              fontsize=11.5, fontweight="bold", color=DARK, pad=10)
ax0.tick_params(axis="y", labelsize=10, length=0)
ax0.tick_params(axis="x", labelsize=9)
for label in ax0.get_yticklabels():
    if label.get_text() == "Footwear":
        label.set_fontweight("bold")
        label.set_color(RED)
ax0.xaxis.grid(True, color="#E6E6E6", linewidth=0.7)
ax0.set_axisbelow(True)
for spine in ["top", "right", "left"]:
    ax0.spines[spine].set_visible(False)

# Sole number label: the bar that carries the message
ax0.text(
    change["Footwear"] + 0.25, "Footwear",
    f"+{jump:.1f} pts\n({foot_now_rate:.1f}% vs {foot_prior_rate:.1f}% avg)",
    va="center", ha="left", fontsize=10, fontweight="bold", color=RED,
)

# --- Right panel: defects drove the jump ----------------------------------
bars = ax1.bar(
    [0, 1], [foot_prior_defect, foot_now_defect],
    color=[GREY, RED], width=0.56,
)
ax1.set_xticks([0, 1])
ax1.set_xticklabels(["Prior 6 quarters\naverage", "Q3 2026"], fontsize=9.5)
ax1.set_ylim(0, 55)
ax1.set_ylabel("% of Footwear returns\nreporting a defect", fontsize=9.5, color=DARK)
ax1.set_title("Defects drove the jump", loc="left",
              fontsize=11.5, fontweight="bold", color=DARK, pad=10)
ax1.tick_params(axis="y", labelsize=9)
ax1.tick_params(axis="x", length=0)
ax1.yaxis.grid(True, color="#E6E6E6", linewidth=0.7)
ax1.set_axisbelow(True)
for spine in ["top", "right"]:
    ax1.spines[spine].set_visible(False)

ax1.text(0, foot_prior_defect + 1.2, f"{foot_prior_defect:.0f}%",
         ha="center", fontsize=11, fontweight="bold", color="#666666")
ax1.text(1, foot_now_defect + 1.2, f"{foot_now_defect:.0f}%",
         ha="center", fontsize=13, fontweight="bold", color=RED)
ax1.text(1, foot_now_defect / 2, "mostly soles\ncoming apart",
         ha="center", va="center", fontsize=8.5, color="white",
         fontweight="bold")

# --- Caveat that changes how the chart should be read ---------------------
fig.text(
    0.115, 0.015,
    "Caveat: Footwear's return window rose from 30 to 60 days in Q3 2026. Past extensions added "
    f"~2 pts to the return rate —\nfar less than this +{jump:.1f}-pt jump, so the policy explains only a small part of it.",
    fontsize=8.8, color="#444444", ha="left", va="bottom",
)
