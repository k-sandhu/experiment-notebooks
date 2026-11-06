import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

# Quality signal: defective returns per 100 units sold.
# This separates a defect problem from high fit/style returns (Swimwear, Dresses).
df["defect_returns"] = df["units_returned"] * df["defect_share_of_returns_pct"] / 100.0
df["defect_per_100_sold"] = df["defect_returns"] / df["units_sold"] * 100.0

quarters = sorted(df["quarter"].unique())
q_index = {q: i for i, q in enumerate(quarters)}
df["q_idx"] = df["quarter"].map(q_index)
latest_q = quarters[-1]

fw = df[df["category"] == "Footwear"].sort_values("q_idx")
fw_latest = fw[fw["quarter"] == latest_q].iloc[0]
fw_prior = fw[fw["quarter"] != latest_q]
fw_prior_rate = fw_prior["defect_returns"].sum() / fw_prior["units_sold"].sum() * 100.0

latest = df[df["quarter"] == latest_q].copy()
other_max_latest = latest.loc[latest["category"] != "Footwear", "defect_per_100_sold"].max()

RED = "#C1272D"
GREY = "#B8B8B8"
DARK = "#222222"

fig = plt.figure(figsize=(10, 6))
gs = fig.add_gridspec(1, 2, width_ratios=[1.75, 1.0], wspace=0.32)
ax = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])

# ---- Left: trend, all categories muted except Footwear ----
for cat, g in df.groupby("category"):
    g = g.sort_values("q_idx")
    if cat == "Footwear":
        continue
    ax.plot(g["q_idx"], g["defect_per_100_sold"], color=GREY, lw=1.3, alpha=0.75, zorder=2)

ax.plot(
    fw["q_idx"], fw["defect_per_100_sold"],
    color=RED, lw=3.6, marker="o", markersize=6,
    markerfacecolor=RED, markeredgecolor="white", markeredgewidth=1.2, zorder=5,
)

ax.annotate(
    f"FOOTWEAR: {fw_latest['defect_per_100_sold']:.1f} per 100 sold\n"
    f"was {fw_prior_rate:.1f} on average before\n"
    f"{fw_latest['defect_share_of_returns_pct']:.0f}% of returns defective "
    f"({fw_latest['defect_returns']:.0f} units)",
    xy=(fw_latest["q_idx"], fw_latest["defect_per_100_sold"]),
    xytext=(1.15, 6.55),
    fontsize=10.5, color=RED, fontweight="bold", va="top",
    arrowprops=dict(arrowstyle="->", color=RED, lw=1.6),
)
ax.text(0.0, 3.05, "All other categories:\nflat, no defect spike", fontsize=9.5, color="#666666", va="top")

ax.set_title("Trend: only Footwear moves", fontsize=12, fontweight="bold", color=DARK, loc="left", pad=10)
ax.set_xticks(range(len(quarters)))
ax.set_xticklabels([q.replace("Q", "\nQ") for q in quarters], fontsize=9)
ax.set_ylabel("Defective returns per 100 units sold", fontsize=10.5)
ax.set_ylim(0, max(9.8, fw_latest["defect_per_100_sold"] * 1.12))
ax.set_xlim(-0.2, len(quarters) - 0.55)
ax.grid(axis="y", color="#E6E6E6", lw=0.8)
ax.set_axisbelow(True)
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
ax.tick_params(labelsize=9.5)

# ---- Right: latest-quarter ranking ----
latest = latest.sort_values("defect_per_100_sold", ascending=True)
colors = [RED if c == "Footwear" else GREY for c in latest["category"]]
bars = ax2.barh(latest["category"], latest["defect_per_100_sold"], color=colors, height=0.68)

for bar, (_, row) in zip(bars, latest.iterrows()):
    is_fw = row["category"] == "Footwear"
    ax2.text(
        bar.get_width() + 0.18, bar.get_y() + bar.get_height() / 2,
        f"{row['defect_per_100_sold']:.1f}",
        va="center", ha="left", fontsize=10 if is_fw else 8.5,
        fontweight="bold" if is_fw else "normal",
        color=RED if is_fw else "#666666",
    )

ax2.set_title(f"Latest quarter ({latest_q})", fontsize=12, fontweight="bold", color=DARK, loc="left", pad=10)
ax2.set_xlabel("Defective returns\nper 100 sold", fontsize=10)
ax2.set_xlim(0, fw_latest["defect_per_100_sold"] * 1.22)
ax2.grid(axis="x", color="#E6E6E6", lw=0.8)
ax2.set_axisbelow(True)
for s in ["top", "right"]:
    ax2.spines[s].set_visible(False)
ax2.tick_params(labelsize=9.5)
for label in ax2.get_yticklabels():
    if label.get_text() == "Footwear":
        label.set_color(RED)
        label.set_fontweight("bold")

# ---- Takeaway headline ----
fig.text(
    0.055, 0.96,
    "Investigate Footwear first — defect returns spiked in 2026 Q3",
    fontsize=16.5, fontweight="bold", color=DARK, va="top",
)
fig.text(
    0.055, 0.905,
    f"Footwear: {fw_latest['defect_per_100_sold']:.1f} defective returns per 100 sold vs {fw_prior_rate:.1f} before; "
    f"next-highest category is only {other_max_latest:.1f}.\n"
    "High Swimwear / Dresses return rates are fit and style — not defects.",
    fontsize=10.5, color="#444444", va="top",
)
fig.text(
    0.055, 0.015,
    "Defective returns = units returned × defect share of returns.  "
    "Footwear's extended 60-day window may lift total returns slightly; it does not explain the defect share jumping to 46%.",
    fontsize=8, color="#777777", va="bottom",
)

fig.tight_layout(rect=[0, 0.045, 1, 0.845])
