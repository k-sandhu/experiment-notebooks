import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

quarters = sorted(df["quarter"].unique())
q_to_x = {q: i for i, q in enumerate(quarters)}
df["x"] = df["quarter"].map(q_to_x)

last_q = quarters[-1]
foot = df[df["category"] == "Footwear"].sort_values("x").copy()
pre = foot[foot["quarter"] != last_q]
pre_avg = pre["return_rate_pct"].mean()
pre_defect_share = pre["defect_share_of_returns_pct"].mean()
last = foot[foot["quarter"] == last_q].iloc[0]
policy_expected = pre_avg + 2.0  # analyst note: past 30->60 day extensions added ~2 pp

# Decompose Footwear return rate into defect vs. non-defect (points of units sold)
foot["defect_pp"] = foot["return_rate_pct"] * foot["defect_share_of_returns_pct"] / 100.0
foot["other_pp"] = foot["return_rate_pct"] - foot["defect_pp"]

RED = "#C1272D"
DARK = "#333333"
GREY = "#B8B8B8"
BLUEGREY = "#5B7A99"

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True,
                               gridspec_kw={"hspace": 0.12, "height_ratios": [1.05, 1.0]})

fig.suptitle("Footwear returns spiked in 2026 Q3 — defects, not the longer return window",
             x=0.07, ha="left", fontsize=13, fontweight="bold", color=DARK)
fig.text(0.07, 0.935,
         "Every other category stayed in its usual range; Footwear alone jumped, and almost all of the jump reported a defect.",
         ha="left", fontsize=9, color="#555555")

# --- Panel A: context — return rate for all categories ---
for cat, g in df.groupby("category"):
    if cat == "Footwear":
        continue
    g = g.sort_values("x")
    ax1.plot(g["x"], g["return_rate_pct"], color=GREY, lw=1.1, alpha=0.85, zorder=1)

ax1.plot(foot["x"], foot["return_rate_pct"], color=RED, lw=2.8, marker="o",
         ms=5, markerfacecolor="white", markeredgewidth=1.6, zorder=4, label="Footwear")
ax1.axhline(pre_avg, color=RED, ls="--", lw=1.0, alpha=0.65, zorder=2)
ax1.text(-0.28, pre_avg + 0.7, f"Footwear avg, prior 6 qtrs: {pre_avg:.1f}%",
         fontsize=8, color=RED, ha="left")

# Direct labels for the range anchors, placed at the last quarter
for cat, dy in [("Swimwear", 0.4), ("Accessories", 0.4)]:
    row = df[(df["category"] == cat) & (df["quarter"] == last_q)].iloc[0]
    ax1.text(row["x"] + 0.10, row["return_rate_pct"] + dy, cat,
             fontsize=8, color="#666666", ha="left", va="center")

ax1.annotate(f"Footwear {last_q}\n{last['return_rate_pct']:.1f}%",
             xy=(last["x"], last["return_rate_pct"]),
             xytext=(last["x"] - 1.55, last["return_rate_pct"] + 4.2),
             fontsize=9, fontweight="bold", color=RED, ha="center",
             arrowprops=dict(arrowstyle="-", color=RED, lw=1.2,
                             connectionstyle="arc3,rad=-0.15"))

ax1.set_ylabel("Return rate\n(% of units sold)", fontsize=9)
ax1.set_ylim(0, 28)
ax1.set_xlim(-0.35, len(quarters) - 0.25)
ax1.set_yticks([0, 5, 10, 15, 20, 25])
ax1.grid(axis="y", color="#E5E5E5", lw=0.7)
ax1.set_axisbelow(True)
ax1.tick_params(labelbottom=False)
ax1.set_title("A. Return rate by category — only Footwear moves in 2026 Q3",
              loc="left", fontsize=10, color=DARK, pad=6)

# --- Panel B: Footwear decomposition ---
ax2.bar(foot["x"], foot["other_pp"], width=0.60, color=BLUEGREY,
        label="Returns not reporting a defect")
ax2.bar(foot["x"], foot["defect_pp"], width=0.60, bottom=foot["other_pp"],
        color=RED, label="Returns reporting a defect (mostly soles coming apart)")

ax2.axhline(pre_avg, color=DARK, ls="--", lw=1.0)
ax2.text(len(quarters) - 0.35, pre_avg + 0.6, f"prior avg {pre_avg:.1f}%",
         fontsize=8, color=DARK, ha="right")
ax2.axhline(policy_expected, color="#888888", ls=":", lw=1.3)
ax2.text(len(quarters) - 0.35, policy_expected + 0.6,
         f"expected from 60-day window (~+2 pp): {policy_expected:.1f}%",
         fontsize=8, color="#666666", ha="right")

for _, r in foot.iterrows():
    ax2.text(r["x"], r["return_rate_pct"] + 0.55, f"{r['return_rate_pct']:.1f}%",
             ha="center", fontsize=8, color=DARK,
             fontweight="bold" if r["quarter"] == last_q else "normal")

lr = foot[foot["quarter"] == last_q].iloc[0]
ax2.text(lr["x"], lr["other_pp"] + lr["defect_pp"] / 2,
         f"defect\n{lr['defect_pp']:.1f} pp\n({lr['defect_share_of_returns_pct']:.0f}% of returns)",
         ha="center", va="center", fontsize=8, fontweight="bold", color="white")
ax2.text(foot["x"].iloc[2], foot["other_pp"].iloc[2] + foot["defect_pp"].iloc[2] + 2.2,
         f"before: defects were ~{pre_defect_share:.0f}% of Footwear returns\n"
         f"(~{pre['return_rate_pct'].mean() * pre_defect_share / 100:.1f} pp of units sold)",
         ha="center", fontsize=8, color="#555555")

ax2.set_ylabel("Footwear return rate\n(pp of units sold)", fontsize=9)
ax2.set_ylim(0, 23)
ax2.set_xticks(range(len(quarters)))
ax2.set_xticklabels(quarters, fontsize=9)
ax2.grid(axis="y", color="#E5E5E5", lw=0.7)
ax2.set_axisbelow(True)
ax2.set_title("B. Footwear detail — the entire jump is the red (defect) segment",
              loc="left", fontsize=10, color=DARK, pad=6)
ax2.legend(loc="upper left", fontsize=8, frameon=False, handlelength=1.2)

for ax in (ax1, ax2):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")

fig.text(0.07, 0.02,
         "Source: data.csv (83 category-quarters; Kids launched 2025 Q2).  "
         "Defect pp = return rate x defect share of returns.  Grey lines in A = other 11 categories.",
         fontsize=7.5, color="#777777", ha="left")

plt.tight_layout(rect=[0, 0.04, 1, 0.91])
