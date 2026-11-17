import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

df = pd.read_csv("data.csv")

dept_order = [
    "Customer Support", "Engineering", "Sales", "Marketing",
    "Product", "Operations", "Design", "People", "Finance",
]
dept_order = [d for d in dept_order if d in df["department"].unique()]

q_order = [
    "I would recommend Northlight as a place to work",
    "My manager supports my growth",
    "I have the tools I need to do my job",
    "My workload is manageable",
    "I see myself working here in two years",
    "I understand the company's strategy",
]
q_short = ["Recommend\nNorthlight", "Manager\nsupports growth", "Tools to\ndo my job",
           "Workload\nmanageable", "Stay 2\nmore years", "Understand\nstrategy"]

p25 = df[df.year == 2025].pivot(index="department", columns="question", values="pct_favourable").reindex(index=dept_order, columns=q_order)
p26 = df[df.year == 2026].pivot(index="department", columns="question", values="pct_favourable").reindex(index=dept_order, columns=q_order)
change = p26 - p25

# company-wide weighted favourable (for title)
w = df.assign(fav=df.pct_favourable / 100 * df.n_responses).groupby("year").apply(
    lambda g: 100 * g.fav.sum() / g.n_responses.sum(), include_groups=False)
w25, w26 = w.get(2025, np.nan), w.get(2026, np.nan)

# response rate per department/year (constant within dept-year)
resp = df.drop_duplicates(["department", "year"]).pivot(
    index="department", columns="year", values="response_rate_pct").reindex(dept_order)

fig, (ax, axr) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [3.4, 1.15], "wspace": 0.08},
    sharey=True)

# --- Left: heatmap of change, annotated with 2026 level ---
vmax = 28
im = ax.imshow(change.values, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")

ax.set_xticks(range(len(q_short)), q_short, fontsize=8)
ax.set_yticks(range(len(dept_order)), dept_order, fontsize=9)
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_xticks(np.arange(-0.5, len(q_short), 1), minor=True)
ax.set_yticks(np.arange(-0.5, len(dept_order), 1), minor=True)
ax.grid(which="minor", color="white", linewidth=1.2)
ax.tick_params(which="minor", length=0)

for i in range(len(dept_order)):
    for j in range(len(q_order)):
        c, lvl = change.values[i, j], p26.values[i, j]
        if np.isnan(c):
            continue
        col = "white" if abs(c) >= 16 else "black"
        ax.text(j, i - 0.14, f"{c:+.0f}", ha="center", va="center",
                fontsize=8.5, fontweight="bold", color=col)
        ax.text(j, i + 0.22, f"({lvl:.0f}%)", ha="center", va="center",
                fontsize=6.5, color=col)

# highlight the two large Support falls
for j in (1, 4):  # manager growth, stay 2 years
    ax.add_patch(Rectangle((j - 0.5, -0.5), 1, 1, fill=False, edgecolor="black", linewidth=2))

ax.set_title("Change 2025 $\\rightarrow$ 2026 (pp), with 2026 % favourable in brackets",
             fontsize=9.5, loc="left", pad=10)
cbar = fig.colorbar(im, ax=ax, shrink=0.92, pad=0.015, ticks=[-20, -10, 0, 10, 20])
cbar.set_label("pp change", fontsize=8)
cbar.ax.tick_params(labelsize=8)
cbar.outline.set_visible(False)

# --- Right: response rate, to flag uncertainty ---
y = np.arange(len(dept_order))
colors = ["#c0392b" if d == "Customer Support" else "#bdbdbd" for d in dept_order]
axr.barh(y, resp[2026].values, height=0.55, color=colors, edgecolor="none", label="2026")
axr.scatter(resp[2025].values, y, color="black", s=32, zorder=3, label="2025")
for i, d in enumerate(dept_order):
    axr.text(resp.loc[d, 2026] + 1.5, i, f"{resp.loc[d, 2026]:.0f}%",
             va="center", fontsize=7.5,
             color="#c0392b" if d == "Customer Support" else "black",
             fontweight="bold" if d == "Customer Support" else "normal")
axr.set_xlim(0, 105)
axr.set_xlabel("Response rate (%)", fontsize=8)
axr.set_title("Response rate\n(bar=2026, dot=2025)", fontsize=9.5, loc="left", pad=10)
axr.tick_params(labelsize=8)
axr.invert_yaxis()
ax.invert_yaxis()
for s in ["top", "right"]:
    axr.spines[s].set_visible(False)
axr.grid(axis="x", color="#eeeeee", linewidth=0.8)
axr.set_axisbelow(True)

fig.suptitle(
    f"Engagement flat overall ({w25:.0f}% in 2025, {w26:.0f}% in 2026), but Customer Support fell sharply \u2014 on far fewer replies",
    fontsize=11.5, fontweight="bold", x=0.02, ha="left")

fig.text(0.02, 0.02,
         "Red = fall, blue = rise. Boxed: Support \u2018manager supports my growth\u2019 71% $\\rightarrow$ 44% (\u221227, largest change) and \u2018stay 2 years\u2019 64% $\\rightarrow$ 41%.\n"
         "Strategy understanding rose in every department (right column). Levels in brackets: lowest is Sales workload, 39%; highest is Engineering tools, 88%.\n"
         "Caution: Support response fell 81% $\\rightarrow$ 38% (n=53 of 140), so its 2026 results are less certain; Finance is smallest (22 staff, n=18). Survey: 8\u201322 September.",
         fontsize=7.2, color="#333333", va="bottom")

plt.tight_layout(rect=[0, 0.09, 1, 0.94])
