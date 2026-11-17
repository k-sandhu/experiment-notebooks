import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")
metric = "My manager supports my growth"
d = df[df["question"] == metric].copy()

wide = d.pivot(index="department", columns="year", values="pct_favourable")
wide = wide.sort_values(2026, ascending=True)

rr26 = d[d["year"] == 2026].set_index("department")["response_rate_pct"].reindex(wide.index)
n26 = d[d["year"] == 2026].set_index("department")["n_responses"].reindex(wide.index)
rr25_cs = d[(d["department"] == "Customer Support") & (d["year"] == 2025)]["response_rate_pct"].iloc[0]

fig, ax = plt.subplots(figsize=(10, 6))
y = np.arange(len(wide))
departments = wide.index.tolist()
colors = ["#C0392B" if dep == "Customer Support" else "#9EC1DD" for dep in departments]

ax.barh(y, wide[2026].values, color=colors, height=0.62, zorder=2)

for i, dep in enumerate(departments):
    prev = wide.loc[dep, 2025]
    cur = wide.loc[dep, 2026]
    highlight = dep == "Customer Support"
    line_color = "#C0392B" if highlight else "#888888"
    ax.plot([prev, cur], [i, i], color=line_color, lw=2.5 if highlight else 1.2,
            zorder=3, alpha=0.95)
    ax.scatter(prev, i, s=60, facecolor="white", edgecolor=line_color,
               linewidth=2.0 if highlight else 1.3, zorder=4)
    ax.text(cur + 1.2, i, f"{cur:.0f}%", va="center", ha="left", fontsize=10,
            fontweight="bold" if highlight else "normal",
            color="#C0392B" if highlight else "#333333", zorder=5)

cs_i = departments.index("Customer Support")
cs_prev = wide.loc["Customer Support", 2025]
cs_cur = wide.loc["Customer Support", 2026]
ax.text(cs_cur + 10.5, cs_i,
        f"down {cs_prev - cs_cur:.0f} pts\n(2025: {cs_prev:.0f}%)",
        va="center", ha="left", fontsize=9.5, color="#C0392B", fontweight="bold")

ax.set_xlim(0, 100)
ax.set_yticks(y)
ax.set_yticklabels(departments)
ax.set_xlabel("Percentage favourable (%)", fontsize=10)
ax.xaxis.grid(True, color="#E6E6E6", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0, labelsize=10)
ax.tick_params(axis="x", labelsize=9)

fig.text(0.17, 0.93, "Manager support is weakest in Customer Support",
         ha="left", va="bottom", fontsize=15, fontweight="bold")
fig.text(0.17, 0.895, "“My manager supports my growth”: 2026 bars vs 2025 dots",
         ha="left", va="bottom", fontsize=10, color="#555555")
fig.text(0.17, 0.02,
         f"Customer Support 2026 response rate: {rr26.loc['Customer Support']:.0f}% "
         f"(n={int(n26.loc['Customer Support'])}), down from {rr25_cs:.0f}% in 2025; interpret the drop with some caution.",
         fontsize=8.5, color="#666666")
fig.subplots_adjust(left=0.17, right=0.96, top=0.82, bottom=0.14)
