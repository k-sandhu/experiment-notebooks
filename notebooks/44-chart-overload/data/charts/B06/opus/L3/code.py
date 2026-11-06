import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

std = df[df["format"] == "standard"]
lrg = df[df["format"] == "large"]
lrg_est = lrg[lrg["opened_year"] < 2025]
n_new = int((lrg["opened_year"] >= 2025).sum())

# Key figures
sales_std = std["annual_sales_musd"].mean()
sales_lrg = lrg["annual_sales_musd"].mean()
sqft_std = std["sq_ft"].mean()
sqft_lrg = lrg["sq_ft"].mean()
sales_uplift = (sales_lrg / sales_std - 1) * 100
space_uplift = (sqft_lrg / sqft_std - 1) * 100

psf_std = std["sales_per_sqft_usd"].mean()
psf_lrg = lrg["sales_per_sqft_usd"].mean()
psf_lrg_est = lrg_est["sales_per_sqft_usd"].mean()

BLUE = "#1f5fa8"
GREY = "#a6a6a6"
LIGHT_GREY = "#cfcfcf"
DARK = "#333333"

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [1, 1.35], "wspace": 0.35}
)
fig.subplots_adjust(top=0.78, bottom=0.17, left=0.07, right=0.97)

# Title and subtitle
fig.text(0.07, 0.94,
         "Standard stores earn more from every square foot",
         fontsize=18, fontweight="bold", color=DARK, ha="left")
fig.text(0.07, 0.875,
         f"Large stores bring {sales_uplift:.0f}% more sales for {space_uplift:.0f}% more floor space, "
         "even after setting aside new openings",
         fontsize=12, color="#555555", ha="left")

# Panel 1: sales per store
labels1 = ["Standard", "Large"]
vals1 = [sales_std, sales_lrg]
bars1 = ax1.bar(labels1, vals1, color=[BLUE, GREY], width=0.6)
for b, v in zip(bars1, vals1):
    ax1.text(b.get_x() + b.get_width() / 2, v + 0.4, f"${v:.1f}M",
             ha="center", va="bottom", fontsize=12, fontweight="bold", color=DARK)
ax1.set_ylim(0, max(vals1) * 1.45)
ax1.set_title("Annual sales per store ($ millions)", fontsize=11.5,
              color=DARK, loc="left", pad=10)
ax1.annotate(f"+{sales_uplift:.0f}% sales\nfor +{space_uplift:.0f}% space",
             xy=(1, sales_lrg + 2.6), ha="center", va="bottom",
             fontsize=11, color=DARK)

# Panel 2: sales per square foot
labels2 = ["Standard\n(35 stores)",
           "Large\n(all 11)",
           f"Large, excl. {n_new}\nopened 2025–26"]
vals2 = [psf_std, psf_lrg, psf_lrg_est]
bars2 = ax2.bar(labels2, vals2, color=[BLUE, GREY, LIGHT_GREY], width=0.6)
for b, v in zip(bars2, vals2):
    ax2.text(b.get_x() + b.get_width() / 2, v + 10, f"${v:.0f}",
             ha="center", va="bottom", fontsize=12, fontweight="bold", color=DARK)
ax2.set_ylim(0, max(vals2) * 1.25)
ax2.set_title("Annual sales per square foot (US$)", fontsize=11.5,
              color=DARK, loc="left", pad=10)

for ax in (ax1, ax2):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#999999")
    ax.set_yticks([])
    ax.tick_params(axis="x", length=0, labelsize=11, colors=DARK)

# Caveat
fig.text(0.07, 0.05,
         f"Note: {n_new} of the 11 large stores opened in 2025–26 and are still building trade. "
         f"Without them, large stores average ${psf_lrg_est:.0f}/sq ft,\nstill below standard stores. "
         "Averages across FreshWay stores, last 12 months.",
         fontsize=9.5, color="#666666", ha="left", va="bottom")
