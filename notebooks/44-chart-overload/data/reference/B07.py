import pandas as pd
import matplotlib.pyplot as plt

HL, GREY = "#C0392B", "#9AA0A6"
df = pd.read_csv("data.csv")
piv = df.pivot(index="quarter", columns="category", values="return_rate_pct")
x = list(range(len(piv)))
fig, ax = plt.subplots(figsize=(10, 6))
for c in piv.columns.drop("Footwear"):
    ax.plot(x, piv[c], color=GREY, lw=1, alpha=0.7)
ax.plot(x, piv["Footwear"], color=HL, lw=3, marker="o")
fw = df[df.category == "Footwear"].set_index("quarter")
ax.text(6.15, piv["Footwear"].iloc[-1], f"Footwear\n{piv['Footwear'].iloc[-1]:.1f}%", color=HL, va="center", fontweight="bold")
ax.text(6.15, piv["Swimwear"].iloc[-1] + 0.6, "Swimwear (always high, fit)", color="#555", va="center", fontsize=9.5)
ax.text(2.5, 1.0, "Grey: the other 11 categories", color="#555", fontsize=9.5)
ax.set_xticks(x, [q.replace("Q", " Q") for q in piv.index])
ax.set_xlim(-0.2, 8.4)
ax.set_ylim(0, 27)
ax.set_ylabel("Units returned, % of units sold")
ax.set_title(f"Footwear returns jumped to {piv['Footwear'].iloc[-1]:.0f}% in Q3 2026; "
             f"{fw.loc['2026Q3', 'defect_share_of_returns_pct']:.0f}% of them cite a defect", fontsize=14, loc="left", pad=28)
ax.text(0, 1.02, f"The previous six quarters averaged {piv['Footwear'].iloc[:-1].mean():.1f}%. The return window was extended to 60 days "
        "in Q3, which usually adds about 2 points.", transform=ax.transAxes, fontsize=10.5, color="#333")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
