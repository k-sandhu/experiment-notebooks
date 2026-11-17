import pandas as pd
import matplotlib.pyplot as plt

HL, GREY = "#C0392B", "#9AA0A6"
df = pd.read_csv("data.csv")
v = df.groupby("department").variance_k.sum().sort_values() / 1000
ot = df[(df.department == "Transit") & (df.budget_line == "Overtime")].variance_k.sum() / 1000
names = list(v.index)
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(names, v.values, color=[HL if d == "Transit" else GREY for d in names])
i = names.index("Transit")
ax.barh(i, ot, color="#7B241C")
ax.text(ot / 2, i, f"overtime \\${ot:.1f}M", color="white", ha="center", va="center", fontsize=10, fontweight="bold")
ax.text(v["Transit"] + 0.05, i, f"\\${v['Transit']:.1f}M", va="center", color=HL, fontweight="bold")
ax.text(v["Roads"] + 0.05, names.index("Roads"), "a harsh winter could add up to \\$1.5M (snow clearing)", va="center", fontsize=9.5, color="#333")
ax.axvline(0, color="#333", lw=0.8)
ax.set_title(f"Transit is \\${v['Transit']:.1f}M of the city's \\${v.sum():.1f}M forecast overspend, mostly overtime",
             fontsize=14.5, loc="left", pad=12)
ax.set_xlabel("Forecast year-end variance, $ millions (positive = over budget)")
ax.set_xlim(-0.6, 4.6)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", alpha=0.25)
fig.tight_layout()
