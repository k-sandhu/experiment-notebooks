import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data.csv")
df["format"] = df["format"].str.strip()

format_colors = {"standard": "#2E86AB", "large": "#F18F01"}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6))

# Left panel: sales per sq ft vs floor area
for fmt, color in format_colors.items():
    subset = df[df["format"] == fmt]
    ax1.scatter(
        subset["sq_ft"],
        subset["sales_per_sqft_usd"],
        s=subset["annual_sales_musd"] * 8,
        alpha=0.7,
        color=color,
        edgecolor="white",
        linewidth=0.7,
        label=f"{fmt.title()} stores"
    )

for fmt, color in format_colors.items():
    mean_sp = df.loc[df["format"] == fmt, "sales_per_sqft_usd"].mean()
    ax1.axhline(mean_sp, color=color, linestyle="--", linewidth=1, alpha=0.6)

s39 = df[df["store_id"] == "S39"].iloc[0]
ax1.annotate(
    f"S39: top seller\n${s39['annual_sales_musd']:.1f}m sales",
    xy=(s39["sq_ft"], s39["sales_per_sqft_usd"]),
    xytext=(10, 10),
    textcoords="offset points",
    fontsize=8,
    arrowprops=dict(arrowstyle="->", lw=0.8)
)

new_large = df[(df["format"] == "large") & (df["opened_year"] >= 2025)]
for _, row in new_large.iterrows():
    ax1.annotate(
        row["store_id"],
        xy=(row["sq_ft"], row["sales_per_sqft_usd"]),
        xytext=(4, -8),
        textcoords="offset points",
        fontsize=7,
        color=format_colors["large"]
    )

ax1.set_xlabel("Selling floor area (sq ft)")
ax1.set_ylabel("Sales per sq ft ($/year)")
ax1.set_title("Sales productivity by store format")
ax1.legend(frameon=False, loc="lower left")
ax1.grid(True, alpha=0.25)

# Right panel: average sales per sq ft by format and store maturity
standard_mean = df.loc[df["format"] == "standard", "sales_per_sqft_usd"].mean()
large_all_mean = df.loc[df["format"] == "large", "sales_per_sqft_usd"].mean()
large_established_mean = df.loc[
    (df["format"] == "large") & (df["opened_year"] < 2025),
    "sales_per_sqft_usd"
].mean()

labels = ["Standard", "Large\n(all)", "Large\n(opened <2025)"]
values = [standard_mean, large_all_mean, large_established_mean]
colors_bar = [format_colors["standard"], format_colors["large"], "#F6C177"]

bars = ax2.bar(labels, values, color=colors_bar, edgecolor="white")
ax2.set_ylabel("Average sales per sq ft ($/year)")
ax2.set_title("Large stores remain less productive")
ax2.grid(True, axis="y", alpha=0.25)
ax2.set_ylim(0, max(values) * 1.15)

for bar, val in zip(bars, values):
    ax2.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + max(values) * 0.02,
        f"${val:.0f}",
        ha="center",
        va="bottom",
        fontsize=9
    )

fig.tight_layout()
