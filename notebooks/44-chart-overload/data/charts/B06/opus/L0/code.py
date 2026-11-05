import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

df = pd.read_csv("data.csv")

std = df[df["format"] == "standard"]
large = df[df["format"] == "large"]
large_new = large[large["opened_year"] >= 2025]
large_est = large[large["opened_year"] < 2025]

c_std = "#7f8c8d"
c_large = "#c0392b"

fig, ax = plt.subplots(figsize=(10, 6))

ax.scatter(std["sq_ft"], std["sales_per_sqft_usd"], s=55, color=c_std, alpha=0.8,
           edgecolor="white", linewidth=0.6, label="Standard stores", zorder=3)
ax.scatter(large_est["sq_ft"], large_est["sales_per_sqft_usd"], s=70, color=c_large,
           edgecolor="white", linewidth=0.6, label="Large stores, opened before 2025", zorder=3)
ax.scatter(large_new["sq_ft"], large_new["sales_per_sqft_usd"], s=70, facecolor="white",
           edgecolor=c_large, linewidth=1.6,
           label="Large stores, opened 2025–26 (still building trade)", zorder=3)

# Group averages as short reference lines spanning each group's size range
def mean_line(sub, color, text, va="bottom"):
    m = sub["sales_per_sqft_usd"].mean()
    x0, x1 = sub["sq_ft"].min(), sub["sq_ft"].max()
    ax.hlines(m, x0, x1, colors=color, linestyles="--", linewidth=1.3, zorder=2)
    ax.text(x1 + 400, m, f"{text}: ${m:,.0f}", color=color, va="center",
            ha="left", fontsize=9.5)

mean_line(std, c_std, "Avg")
mean_line(large_est, c_large, "Avg")
mean_line(large_new, c_large, "Avg")

ax.set_xlabel("Selling floor area (sq ft)", fontsize=11)
ax.set_ylabel("Annual sales per square foot", fontsize=11)
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v/1000:,.0f}k"))
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"${v:,.0f}"))
ax.set_xlim(15000, 62000)
ax.set_ylim(330, 750)

for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
ax.grid(axis="y", color="#e5e5e5", linewidth=0.8, zorder=0)
ax.legend(loc="lower left", frameon=False, fontsize=9.5)

fig.suptitle("Large stores sell less per square foot than standard stores",
             x=0.06, ha="left", fontsize=14, fontweight="bold")
fig.text(0.06, 0.905,
         "Annual sales per sq ft by store size, 46 stores. The gap remains when the four "
         "large stores opened in 2025–26 are set aside.",
         ha="left", fontsize=10, color="#444444")

fig.subplots_adjust(left=0.1, right=0.97, top=0.86, bottom=0.1)
