import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Read data
df = pd.read_csv('data.csv')

# Subsets
std = df[df['format'] == 'standard']
large = df[df['format'] == 'large']
large_mature = large[large['opened_year'] < 2025]

# Averages
std_sales = std['annual_sales_musd'].mean()
large_sales = large['annual_sales_musd'].mean()
std_ppsf = std['sales_per_sqft_usd'].mean()
large_ppsf = large['sales_per_sqft_usd'].mean()
mature_ppsf = large_mature['sales_per_sqft_usd'].mean()

# Percentages for title / annotation
sales_pct = (large_sales / std_sales - 1) * 100
floor_pct = (large['sq_ft'].mean() / std['sq_ft'].mean() - 1) * 100

# Colours
std_color = '#BDBDBD'
large_color = '#D55E00'
mature_color = '#F0B27A'

fig, axes = plt.subplots(
    1, 2,
    figsize=(10, 6),
    gridspec_kw={'width_ratios': [1, 1.55]}
)

# Overall title
title = (
    f"Large stores deliver {sales_pct:.0f}% more sales but require {floor_pct:.0f}% more floor space;\n"
    f"they sell less per square foot, even when mature."
)
fig.suptitle(
    title,
    fontsize=14,
    fontweight='bold',
    x=0.02,
    ha='left',
    y=0.98
)

# Left panel: average annual sales per store
ax = axes[0]
x = np.arange(2)
sales_values = [std_sales, large_sales]
bars = ax.bar(x, sales_values, color=[std_color, large_color], width=0.65)

ax.set_xticks(x)
ax.set_xticklabels(['Standard', 'Large'], fontsize=10)
ax.set_ylabel('Annual sales ($m)', fontsize=10)
ax.set_ylim(0, max(sales_values) * 1.25)
ax.set_title('Average annual sales per store', fontsize=11, loc='left', pad=10)

for i, (bar, val) in enumerate(zip(bars, sales_values)):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        val + max(sales_values) * 0.03,
        f'${val:.1f}m',
        ha='center',
        va='bottom',
        fontsize=11,
        fontweight='bold' if i == 1 else 'normal'
    )

ax.text(
    0.5, 0.95,
    f"Large stores: +{floor_pct:.0f}% floor area",
    transform=ax.transAxes,
    ha='center',
    va='top',
    fontsize=9.5,
    color='#444444'
)

# Right panel: average annual sales per square foot
ax2 = axes[1]
x2 = np.arange(3)
ppsf_values = [std_ppsf, large_ppsf, mature_ppsf]
colors = [std_color, large_color, mature_color]

bars2 = ax2.bar(
    x2, ppsf_values,
    color=colors,
    width=0.65,
    edgecolor=[std_color, large_color, large_color],
    linewidth=1
)
bars2[2].set_hatch('///')

ax2.set_xticks(x2)
ax2.set_xticklabels(
    [
        f'Standard\n({len(std)} stores)',
        f'Large\n(all {len(large)})',
        f'Large\nmature ({len(large_mature)})'
    ],
    fontsize=10
)
ax2.set_ylabel('Sales per sq ft ($)', fontsize=10)
ax2.set_ylim(0, max(ppsf_values) * 1.25)
ax2.set_title('Average annual sales per square foot', fontsize=11, loc='left', pad=10)

for i, (bar, val) in enumerate(zip(bars2, ppsf_values)):
    ax2.text(
        bar.get_x() + bar.get_width() / 2,
        val + max(ppsf_values) * 0.03,
        f'${val:.0f}',
        ha='center',
        va='bottom',
        fontsize=11,
        fontweight='bold' if i in (1, 2) else 'normal'
    )

# Footnote
fig.text(
    0.02, 0.02,
    "Mature = opened before 2025; excludes 4 large stores opened in 2025–26 and still building up trade.",
    ha='left',
    va='bottom',
    fontsize=9,
    color='#555555'
)

# Clean styling
for ax in axes:
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', color='#E5E5E5', linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis='both', colors='#333333')
    ax.yaxis.label.set_color('#333333')

plt.tight_layout(rect=[0, 0.06, 1, 0.90])
