import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Load data
df = pd.read_csv('data.csv')

# Group definitions for the comparison
standard = df[df['format'] == 'standard']
large_established = df[(df['format'] == 'large') & (df['opened_year'] < 2025)]
large_new = df[(df['format'] == 'large') & (df['opened_year'] >= 2025)]

groups = [
    (f"Standard\n(n={len(standard)})", standard['sales_per_sqft_usd'].mean(), '#0B6E4F'),
    (f"Large, opened\nbefore 2025\n(n={len(large_established)})", large_established['sales_per_sqft_usd'].mean(), '#BDBDBD'),
    (f"Large, opened\n2025–26\n(n={len(large_new)})", large_new['sales_per_sqft_usd'].mean(), '#BDBDBD'),
]

labels = [g[0] for g in groups]
values = [g[1] for g in groups]
colors = [g[2] for g in groups]

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(labels, values, color=colors, width=0.6)

# Direct value labels
for bar, val in zip(bars, values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        val + 10,
        f"${val:,.0f}",
        ha='center',
        va='bottom',
        fontsize=14,
        fontweight='bold',
        color='#222222'
    )

# Title states the key message
ax.set_title(
    "Standard stores sell more per square foot than established large stores;\nnew large stores lag further",
    fontsize=15,
    fontweight='bold',
    loc='left',
    pad=16
)

ax.set_ylabel("Annual sales per square foot (USD)", fontsize=11)
ax.set_ylim(0, 700)
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f"${x:,.0f}"))
ax.tick_params(axis='x', labelsize=11, pad=6)
ax.tick_params(axis='y', labelsize=10)

# Clean, honest scales
ax.grid(axis='y', color='#DDDDDD', linewidth=0.8)
ax.set_axisbelow(True)
for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)
ax.spines['left'].set_color('#888888')
ax.spines['bottom'].set_color('#888888')

# Brief caveat
fig.text(
    0.01, 0.01,
    "Note: Large stores opened in 2025–26 are still ramping up; compare standard with established large stores.",
    fontsize=9,
    color='#555555',
    ha='left',
    va='bottom'
)

plt.tight_layout(rect=[0, 0.05, 1, 0.95])
