import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Load data
df = pd.read_csv('data.csv')

# Define comparison groups: standard vs established large (exclude 2025–26 openings)
standard = df[df['format'] == 'standard']
large_est = df[(df['format'] == 'large') & (df['opened_year'] < 2025)]

# Compute metrics
std_total = standard['annual_sales_musd'].mean()
std_psf = standard['sales_per_sqft_usd'].mean()
large_total = large_est['annual_sales_musd'].mean()
large_psf = large_est['sales_per_sqft_usd'].mean()

total_diff = (large_total / std_total - 1) * 100
psf_diff = (large_psf / std_psf - 1) * 100

# Create figure with two panels
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6))

x = np.arange(2)
width = 0.5
colors = ['#BDBDBD', '#1F6FB4']  # grey for context, strong blue for large stores

# Left panel: total sales per store
bars1 = ax1.bar(x, [std_total, large_total], width=width, color=colors)
ax1.set_ylabel('Average annual sales per store\n($ millions)', fontsize=11)
ax1.set_xticks(x)
ax1.set_xticklabels([f'Standard\n(n={len(standard)})', f'Established large\n(n={len(large_est)})'], fontsize=10)
ax1.set_ylim(0, 30)
ax1.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f'${v:.0f}M'))
ax1.grid(axis='y', color='#DDDDDD', linewidth=0.8)
ax1.set_axisbelow(True)
for spine in ['top', 'right']:
    ax1.spines[spine].set_visible(False)
for bar, val in zip(bars1, [std_total, large_total]):
    ax1.text(bar.get_x() + bar.get_width()/2, val + 0.8, f'${val:.1f}M',
             ha='center', va='bottom', fontsize=12, fontweight='bold', color='#222222')

# Right panel: sales per square foot
bars2 = ax2.bar(x, [std_psf, large_psf], width=width, color=colors)
ax2.set_ylabel('Annual sales per square foot\n($ per sq ft)', fontsize=11)
ax2.set_xticks(x)
ax2.set_xticklabels([f'Standard\n(n={len(standard)})', f'Established large\n(n={len(large_est)})'], fontsize=10)
ax2.set_ylim(0, 700)
ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f'${v:.0f}'))
ax2.grid(axis='y', color='#DDDDDD', linewidth=0.8)
ax2.set_axisbelow(True)
for spine in ['top', 'right']:
    ax2.spines[spine].set_visible(False)
for bar, val in zip(bars2, [std_psf, large_psf]):
    ax2.text(bar.get_x() + bar.get_width()/2, val + 20, f'${val:.0f}',
             ha='center', va='bottom', fontsize=12, fontweight='bold', color='#222222')

# Main title states the trade-off as a sentence
fig.suptitle(
    f'Large stores generate {total_diff:.0f}% more total sales but {abs(psf_diff):.0f}% less per square foot than standard stores',
    fontsize=14, fontweight='bold', x=0.05, ha='left', y=0.98
)

# Caveat note
fig.text(0.05, 0.01,
         'Excludes four large stores opened in 2025–26 that are still ramping up.',
         fontsize=9, color='#555555', ha='left', va='bottom')

plt.tight_layout(rect=[0, 0.05, 1, 0.93])
