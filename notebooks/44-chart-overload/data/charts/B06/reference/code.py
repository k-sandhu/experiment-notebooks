import pandas as pd
import matplotlib.pyplot as plt

HL, GREY = "#C0392B", "#9AA0A6"
df = pd.read_csv("data.csv")
std, lrg = df[df.format == "standard"], df[df.format == "large"]
new = lrg.opened_year >= 2025
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(std.sq_ft / 1000, std.sales_per_sqft_usd, color=GREY, s=40)
ax.scatter(lrg[~new].sq_ft / 1000, lrg[~new].sales_per_sqft_usd, color=HL, s=50)
ax.scatter(lrg[new].sq_ft / 1000, lrg[new].sales_per_sqft_usd, facecolor="white", edgecolor=HL, s=50, lw=1.5)
for d, x0, x1 in [(std, 17, 33), (lrg, 37, 56)]:
    m = d.sales_per_sqft_usd.mean()
    ax.plot([x0, x1], [m, m], color="#333", lw=1.5)
    ax.text(x1, m + 8, f"average \\${m:.0f}", ha="right", fontsize=10.5, fontweight="bold")
ax.text(46.5, 350, "hollow = opened 2025-26, still ramping up", color=HL, fontsize=9.5, ha="center")
ax.text(25, 715, "Standard stores", color="#555", fontsize=11, ha="center")
ax.text(46.5, 600, "Large stores", color=HL, fontsize=11, ha="center")
s, l = std.annual_sales_musd.mean(), lrg.annual_sales_musd.mean()
gap = std.sales_per_sqft_usd.mean() - lrg.sales_per_sqft_usd.mean()
ax.set_title(f"Large stores sell \\${gap:.0f} less per square foot than standard stores", fontsize=14.5, loc="left", pad=28)
ax.text(0, 1.02, f"Average annual sales: \\${l:.1f}M per large store vs \\${s:.1f}M per standard store "
        f"({(l / s - 1) * 100:.0f}% more sales for {(lrg.sq_ft.mean() / std.sq_ft.mean() - 1) * 100:.0f}% more space).",
        transform=ax.transAxes, fontsize=10.5, color="#333")
ax.set_xlabel("Selling floor area, thousand sq ft")
ax.set_ylabel("Annual sales per sq ft, $")
ax.set_ylim(300, 760)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
ax.grid(alpha=0.25)
fig.tight_layout()
