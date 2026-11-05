import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")

std = df[df["format"] == "standard"]
lg = df[df["format"] == "large"]
lg_new = lg[lg["opened_year"] >= 2025]
lg_est = lg[lg["opened_year"] < 2025]

std_psf = std["sales_per_sqft_usd"].mean()
est_psf = lg_est["sales_per_sqft_usd"].mean()
new_psf = lg_new["sales_per_sqft_usd"].mean()
gap_pct = (1 - est_psf / std_psf) * 100

sales_uplift = (lg_est["annual_sales_musd"].mean() / std["annual_sales_musd"].mean() - 1) * 100
space_uplift = (lg_est["sq_ft"].mean() / std["sq_ft"].mean() - 1) * 100
catch_ratio = lg_est["catchment_pop_k"].mean() / std["catchment_pop_k"].mean()

C_STD = "#2b6c9e"
C_LG = "#d95f02"
C_GREY = "#555555"

fig, (ax, axb) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={"width_ratios": [2.1, 1]}
)

# --- Left: sales vs floor area, with standard-store productivity line ---
x_line = np.array([0, 58000])
ax.plot(x_line / 1000, std_psf * x_line / 1e6, ls="--", color=C_GREY, lw=1.2, zorder=1)
ax.text(57.5, std_psf * 57500 / 1e6 + 0.6,
        f"If sales kept pace with\nstandard stores (${std_psf:.0f}/sq ft)",
        ha="right", va="bottom", fontsize=9, color=C_GREY)

ax.scatter(std["sq_ft"] / 1000, std["annual_sales_musd"], s=45, color=C_STD,
           alpha=0.85, edgecolor="white", lw=0.6, zorder=3,
           label=f"Standard ({len(std)} stores)")
ax.scatter(lg_est["sq_ft"] / 1000, lg_est["annual_sales_musd"], s=60, color=C_LG,
           edgecolor="white", lw=0.6, zorder=3,
           label=f"Large, opened {lg_est['opened_year'].min()}–{str(lg_est['opened_year'].max())[2:]} ({len(lg_est)})")
ax.scatter(lg_new["sq_ft"] / 1000, lg_new["annual_sales_musd"], s=60, facecolor="white",
           edgecolor=C_LG, lw=1.6, zorder=3,
           label=f"Large, opened 2025–26, still ramping up ({len(lg_new)})")

ax.set_xlim(0, 58)
ax.set_ylim(0, 37)
ax.set_xlabel("Selling floor area (thousand sq ft)", fontsize=10)
ax.set_ylabel("Annual sales ($ millions)", fontsize=10)
ax.legend(loc="upper left", frameon=False, fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", color="#e5e5e5", lw=0.8)
ax.set_axisbelow(True)
ax.set_title("Large stores sit below the line that standard-store productivity would give",
             fontsize=10, loc="left", color="#333333")

# --- Right: sales per sq ft by group ---
labels = ["Standard", "Large,\nestablished", "Large,\nopened 2025–26"]
vals = [std_psf, est_psf, new_psf]
colors = [C_STD, C_LG, "white"]
edges = [C_STD, C_LG, C_LG]
y = np.arange(len(vals))[::-1]
axb.barh(y, vals, color=colors, edgecolor=edges, lw=1.6, height=0.6)
for yi, v in zip(y, vals):
    axb.text(v + 10, yi, f"${v:.0f}", va="center", fontsize=11, fontweight="bold")
axb.set_yticks(y)
axb.set_yticklabels(labels, fontsize=10)
axb.set_xlim(0, max(vals) * 1.25)
axb.set_xticks([])
axb.spines[["top", "right", "bottom"]].set_visible(False)
axb.set_title("Sales per sq ft, per year (average)", fontsize=10, loc="left", color="#333333")

fig.suptitle(
    f"Large stores earn about {gap_pct:.0f}% less per square foot than standard stores",
    x=0.02, ha="left", fontsize=15, fontweight="bold", y=0.975,
)
fig.text(
    0.02, 0.895,
    f"Established large stores bring {sales_uplift:.0f}% more sales per site but use {space_uplift:.0f}% more space, "
    f"even though their catchments are {catch_ratio:.1f}× larger.\n"
    "New large stores (2025–26) are excluded from the comparison while they build up trade.",
    ha="left", va="top", fontsize=9.5, color="#444444",
)

fig.tight_layout(rect=[0, 0, 1, 0.83])
