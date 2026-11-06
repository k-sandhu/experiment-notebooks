import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

Q = "My manager supports my growth"
sub = df[df["question"] == Q].copy()

d25 = sub[sub["year"] == 2025].set_index("department")
d26 = sub[sub["year"] == 2026].set_index("department")

plot = pd.DataFrame({
    "pct25": d25["pct_favourable"],
    "pct26": d26["pct_favourable"],
    "n26": d26["n_responses"],
    "headcount": d26["headcount"],
    "resp25": d25["response_rate_pct"],
    "resp26": d26["response_rate_pct"],
}).reset_index()

plot["change"] = plot["pct26"] - plot["pct25"]
# 95% CI (normal approx) from number of respondents
p = plot["pct26"] / 100.0
plot["ci"] = 1.96 * np.sqrt(p * (1 - p) / plot["n26"]) * 100

plot = plot.sort_values("pct26", ascending=True).reset_index(drop=True)
# worst at top
plot = plot.iloc[::-1].reset_index(drop=True)

company_avg = (plot["pct26"] * plot["n26"]).sum() / plot["n26"].sum()

is_support = plot["department"] == "Customer Support"
colors = np.where(is_support, "#C1272D", "#5B7A99")
colors_resp = np.where(is_support, "#C1272D", "#B8C6D3")

y = np.arange(len(plot))

plt.rcParams["font.family"] = "DejaVu Sans"
fig, (ax, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), sharey=True,
    gridspec_kw={"width_ratios": [3.1, 1.1], "wspace": 0.08}
)

# --- Main panel: % favourable ---
bars = ax.barh(y, plot["pct26"], color=colors, height=0.58, zorder=3)
# hatch Support to flag extra uncertainty from low response
for bar, flag in zip(bars, is_support):
    if flag:
        bar.set_hatch("///")
        bar.set_edgecolor("white")

ax.errorbar(
    plot["pct26"], y, xerr=plot["ci"], fmt="none",
    ecolor="#333333", elinewidth=1.2, capsize=3, zorder=4
)
ax.scatter(
    plot["pct25"], y, s=75, facecolor="white", edgecolor="black",
    linewidth=1.4, zorder=5, label="2025 score"
)
ax.axvline(company_avg, color="#333333", linestyle="--", linewidth=1.2, zorder=2)
ax.text(company_avg + 1, len(plot) - 0.35, f"Company avg {company_avg:.0f}%",
        fontsize=8.5, color="#333333", va="bottom")

# value + change labels
for yi, pct, ci, chg, flag in zip(y, plot["pct26"], plot["ci"], plot["change"], is_support):
    ax.text(
        pct + ci + 1.5, yi, f"{pct:.0f}%  ({chg:+.0f})",
        va="center", ha="left",
        fontsize=11 if flag else 9.5,
        fontweight="bold" if flag else "normal",
        color="#C1272D" if flag else "#222222",
    )

# arrow showing Support's 27-point fall
cs_y = y[is_support.values][0]
cs25 = plot.loc[is_support, "pct25"].iloc[0]
cs26 = plot.loc[is_support, "pct26"].iloc[0]
ax.annotate(
    "", xy=(cs26 + 1, cs_y + 0.42), xytext=(cs25 - 1, cs_y + 0.42),
    arrowprops=dict(arrowstyle="->", color="#C1272D", lw=1.8)
)
ax.text((cs25 + cs26) / 2, cs_y + 0.55, "−27 pts", ha="center", va="bottom",
        fontsize=10, fontweight="bold", color="#C1272D")

ax.set_yticks(y)
ax.set_yticklabels(
    [f"{d}  ({int(h)} staff)" for d, h in zip(plot["department"], plot["headcount"])],
    fontsize=10
)
for label, flag in zip(ax.get_yticklabels(), is_support):
    if flag:
        label.set_fontweight("bold")
        label.set_color("#C1272D")

ax.set_xlim(0, 105)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xlabel("% favourable — “My manager supports my growth”  (2026)", fontsize=10)
ax.grid(axis="x", color="0.85", linewidth=0.7, zorder=0)
ax.set_axisbelow(True)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
ax.legend(loc="lower right", fontsize=8.5, frameon=True)

# --- Side panel: response rate (reliability check) ---
bars2 = ax2.barh(y, plot["resp26"], color=colors_resp, height=0.58, zorder=3)
for bar, flag in zip(bars2, is_support):
    if flag:
        bar.set_hatch("///")
        bar.set_edgecolor("white")

ax2.scatter(
    plot["resp25"], y, s=75, facecolor="white", edgecolor="black",
    linewidth=1.4, zorder=5
)
for yi, r, n, h, flag in zip(y, plot["resp26"], plot["n26"], plot["headcount"], is_support):
    ax2.text(
        r + 2, yi, f"{r:.0f}%",
        va="center", ha="left",
        fontsize=11 if flag else 9,
        fontweight="bold" if flag else "normal",
        color="#C1272D" if flag else "#222222",
    )

ax2.set_xlim(0, 108)
ax2.set_xticks([0, 50, 100])
ax2.set_xlabel("Response rate 2026 (%)\n○ = 2025", fontsize=10)
ax2.grid(axis="x", color="0.85", linewidth=0.7, zorder=0)
ax2.set_axisbelow(True)
for s in ["top", "right"]:
    ax2.spines[s].set_visible(False)
ax2.text(52, cs_y + 0.55, "only 53 of 140\nanswered", ha="left", va="bottom",
         fontsize=8.5, fontweight="bold", color="#C1272D", linespacing=1.1)

# --- Title = the decision ---
fig.text(0.07, 0.965, "Give the manager-support programme to Customer Support",
         fontsize=16.5, fontweight="bold", ha="left", va="top", color="#111111")
fig.text(0.07, 0.915,
         "Lowest score (44%) and by far the largest fall since 2025 — every other department is 58–79% and within ±3 pts.",
         fontsize=10.5, ha="left", va="top", color="#333333")

fig.text(
    0.07, 0.015,
    "Whiskers = 95% CI from n respondents.  ⚠ Support response fell 81%→38%, so non-response bias could move its true score beyond the whiskers —\n"
    "follow up urgently to verify, but the gap is too large to deprioritise. Next lowest: Sales (58%, stable).  Survey: Sep 2025 vs Sep 2026.",
    fontsize=8, ha="left", va="bottom", color="#444444", linespacing=1.35
)

plt.subplots_adjust(left=0.24, right=0.97, top=0.85, bottom=0.14)
