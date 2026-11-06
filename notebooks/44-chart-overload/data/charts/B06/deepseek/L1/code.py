import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('data.csv')

std = df[df['format'] == 'standard']
large = df[df['format'] == 'large']
large_mature = df[(df['format'] == 'large') & (df['opened_year'] < 2025)]

labels = ['Standard', 'Large\n(all)', 'Large\n(excl. 2025-26)']
colors = ['#4C78A8', '#F58518', '#B8720E']

sales_means = [
    std['annual_sales_musd'].mean(),
    large['annual_sales_musd'].mean(),
    large_mature['annual_sales_musd'].mean()
]
spf_means = [
    std['sales_per_sqft_usd'].mean(),
    large['sales_per_sqft_usd'].mean(),
    large_mature['sales_per_sqft_usd'].mean()
]

fig, axes = plt.subplots(1, 2, figsize=(10, 6))

bars1 = axes[0].bar(labels, sales_means, color=colors, width=0.65)
axes[0].set_title('Average annual sales per store', fontsize=13, fontweight='bold')
axes[0].set_ylabel('$ millions', fontsize=11)
axes[0].bar_label(bars1, fmt='$%.1fM', padding=3, fontsize=10, fontweight='bold')
axes[0].set_ylim(0, max(sales_means) * 1.18)
axes[0].tick_params(axis='x', labelsize=10)
axes[0].grid(axis='y', alpha=0.25)
axes[0].set_axisbelow(True)

bars2 = axes[1].bar(labels, spf_means, color=colors, width=0.65)
axes[1].set_title('Average sales per square foot', fontsize=13, fontweight='bold')
axes[1].set_ylabel('$ per sq ft', fontsize=11)
axes[1].bar_label(bars2, fmt='$%.0f', padding=3, fontsize=10, fontweight='bold')
axes[1].set_ylim(0, max(spf_means) * 1.18)
axes[1].tick_params(axis='x', labelsize=10)
axes[1].grid(axis='y', alpha=0.25)
axes[1].set_axisbelow(True)
axes[1].axhline(spf_means[0], color=colors[0], linestyle='--', linewidth=1, alpha=0.7)

for ax in axes:
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

fig.suptitle(
    'Large stores: more total sales, but lower sales per square foot',
    fontsize=15,
    fontweight='bold',
    y=0.98
)
fig.text(
    0.5, 0.01,
    'Large stores average 88% more floor area. "Excl. 2025-26" removes 4 large stores still building trade.',
    ha='center', fontsize=9, color='#444444'
)

plt.tight_layout(rect=[0, 0.05, 1, 0.93])
