import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv("data.csv")

# Main comparison: change in manager support by department
q_manager = "My manager supports my growth"
mgr = (
    df[df["question"] == q_manager]
    .pivot(index="department", columns="year", values="pct_favourable")
)
mgr.columns = mgr.columns.astype(int)
change = (mgr[2026] - mgr[2025]).sort_values()

# Supporting detail: Customer Support intent-to-stay trend
q_intent = "I see myself working here in two years"
support_intent = (
    df[(df["department"] == "Customer Support") & (df["question"] == q_intent)]
    .sort_values("year")
)
intent_years = support_intent["year"].astype(int).tolist()
intent_vals = support_intent["pct_favourable"].tolist()

# Support response-rate caveat
support_rows = df[df["department"] == "Customer Support"]
resp_2025 = support_rows.loc[support_rows["year"] == 2025, "response_rate_pct"].iloc[0]
resp_2026 = support_rows.loc[support_rows["year"] == 2026, "response_rate_pct"].iloc[0]

# Colours
highlight = "#D55E00"
grey = "#BFBFBF"
dark_grey = "#555555"

fig, (ax1, ax2) = plt.subplots(
    1, 2,
    figsize=(10, 6),
    gridspec_kw={"width_ratios": [2.35, 1.0]}
)

# ---- Left panel: change in manager support by department ----
y_pos = np.arange(len(change))
colors = [highlight if d == "Customer Support" else grey for d in change.index]

ax1.barh(y_pos, change.values, color=colors, height=0.62)
ax1.axvline(0, color="#333333", linewidth=1)
ax1.invert_yaxis()

ax1.set_yticks(y_pos)
ax1.set_yticklabels(change.index)
for label, dept in zip(ax1.get_yticklabels(), change.index):
    if dept == "Customer Support":
        label.set_color(highlight)
        label.set_fontweight("bold")
    else:
        label.set_color(dark_grey)

# Label only the message number
cs_val = change.loc["Customer Support"]
ax1.text(
    cs_val - 1.0, list(change.index).index("Customer Support"),
    f"{cs_val:.0f} pts",
    ha="right", va="center",
    color=highlight, fontweight="bold", fontsize=11
)

ax1.set_xlim(change.min() - 7, max(change.max() + 4, 5))
ax1.set_xlabel("Change in % favourable, 2025 → 2026 (percentage points)",
               color=dark_grey, fontsize=10)
ax1.set_title("Manager support by department", loc="left",
              fontsize=11, fontweight="bold", color="#222222")

ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
ax1.spines["left"].set_visible(False)
ax1.tick_params(axis="x", colors=dark_grey)
ax1.tick_params(axis="y", length=0)
ax1.xaxis.grid(True, color="#E8E8E8", linewidth=0.8)
ax1.set_axisbelow(True)

# ---- Right panel: Support intent to stay ----
ax2.plot([0, 1], intent_vals, marker="o", color=highlight,
         linewidth=3, markersize=8)
ax2.set_xticks([0, 1])
ax2.set_xticklabels(["2025", "2026"], color=dark_grey)
ax2.set_ylim(min(intent_vals) - 12, max(intent_vals) + 10)
ax2.set_ylabel("% favourable", color=dark_grey)

ax2.text(0, intent_vals[0] + 2, f"{intent_vals[0]}%",
         ha="center", va="bottom", color=highlight, fontweight="bold")
ax2.text(1, intent_vals[1] - 3, f"{intent_vals[1]}%",
         ha="center", va="top", color=highlight, fontweight="bold")

drop = intent_vals[1] - intent_vals[0]
ax2.annotate(
    f"{drop:.0f} pts",
    xy=(0.5, (intent_vals[0] + intent_vals[1]) / 2),
    xytext=(0.55, (intent_vals[0] + intent_vals[1]) / 2 + 7),
    ha="center",
    color=highlight,
    fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=highlight, lw=1)
)

ax2.set_title("Support: 'I see myself here\nin two years'", loc="left",
              fontsize=11, fontweight="bold", color="#222222")
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.spines["left"].set_color("#CCCCCC")
ax2.spines["bottom"].set_color("#CCCCCC")
ax2.tick_params(axis="y", colors=dark_grey)
ax2.tick_params(axis="x", length=0)
ax2.yaxis.grid(True, color="#E8E8E8", linewidth=0.8)
ax2.set_axisbelow(True)

# ---- Title and caveat ----
fig.text(
    0.02, 0.95,
    "Customer Support should get the manager-support programme: manager support\n"
    "fell 27 points (largest drop) and intent to stay fell 23 points.",
    ha="left", va="top", fontsize=13.5, fontweight="bold", color="#222222"
)

fig.text(
    0.02, 0.035,
    f"Caveat: Support's 2026 survey response rate was {resp_2026:.0f}% "
    f"(vs {resp_2025:.0f}% in 2025), so its scores are less certain than other departments'.",
    ha="left", fontsize=9, color=dark_grey
)

fig.subplots_adjust(
    left=0.18, right=0.96, top=0.82, bottom=0.17, wspace=0.42
)
