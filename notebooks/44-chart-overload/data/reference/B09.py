import pandas as pd
import matplotlib.pyplot as plt

HL, GREY = "#C0392B", "#9AA0A6"
df = pd.read_csv("data.csv")
q = "My manager supports my growth"
p = df[df.question == q].pivot(index="department", columns="year", values="pct_favourable")
p = p.assign(ch=p[2026] - p[2025]).sort_values("ch", ascending=False)
fig, ax = plt.subplots(figsize=(10, 6))
for i, (d, r) in enumerate(p.iterrows()):
    c = HL if d == "Customer Support" else GREY
    ax.plot([r[2025], r[2026]], [i, i], color=c, lw=2.5 if c == HL else 1.5)
    ax.scatter([r[2025]], [i], color="white", edgecolor=c, s=45, zorder=3)
    ax.scatter([r[2026]], [i], color=c, s=45, zorder=3)
i = list(p.index).index("Customer Support")
ax.text(p.loc["Customer Support", 2026] - 1.5, i, f"{p.loc['Customer Support', 2026]:.0f}%", ha="right", va="center", color=HL, fontweight="bold")
ax.text(p.loc["Customer Support", 2025] + 1.5, i, f"{p.loc['Customer Support', 2025]:.0f}% in 2025", va="center", color="#555")
two = df[(df.department == "Customer Support") & (df.question.str.startswith("I see myself"))].set_index("year").pct_favourable
ax.set_yticks(range(len(p)), p.index)
ax.invert_yaxis()
ax.set_xlim(30, 90)
ax.set_xlabel("% favourable, 'My manager supports my growth' (hollow = 2025, filled = 2026)")
ax.set_title("Customer Support's manager-support score fell 27 points, the largest drop anywhere", fontsize=14, loc="left", pad=28)
ax.text(0, 1.02, f"Support staff who see themselves here in two years: {two[2025]:.0f}% to {two[2026]:.0f}%. "
        "Only 38% of Support answered this year (81% last year).", transform=ax.transAxes, fontsize=10.5, color="#333")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", alpha=0.25)
fig.tight_layout()
