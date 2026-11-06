import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('data.csv')

# Focus on the latest quarter (Q3 2026) for a clean quality comparison
q3 = df[df['quarter'] == '2026Q3'].copy()
q3 = q3.sort_values('defect_share_of_returns_pct', ascending=True)

# Create figure
fig, ax = plt.subplots(figsize=(10, 6))

# Highlight Footwear, grey out the rest
colors = ['#D62728' if c == 'Footwear' else '#BDBDBD' for c in q3['category']]
bars = ax.barh(
    q3['category'],
    q3['defect_share_of_returns_pct'],
    color=colors,
    edgecolor='none',
    height=0.7
)

# Direct label only the key number and the next-highest comparison
footwear_val = q3.loc[q3['category'] == 'Footwear', 'defect_share_of_returns_pct'].values[0]
ax.text(
    footwear_val + 0.8,
    len(q3) - 1,
    f'{footwear_val:.0f}%',
    va='center',
    ha='left',
    fontsize=12,
    fontweight='bold',
    color='#D62728'
)

next_val = q3.iloc[-2]['defect_share_of_returns_pct']
ax.text(
    next_val + 0.8,
    len(q3) - 2,
    f'{next_val:.0f}%',
    va='center',
    ha='left',
    fontsize=10,
    color='#666666'
)

# Formatting
ax.set_xlim(0, 52)
ax.set_xlabel('Defect share of returns (%)', fontsize=11)
ax.set_title(
    "Footwear is the clear quality outlier: 46% of Q3 2026 returns reported a defect, vs ≤12% for all other categories.",
    fontsize=13,
    fontweight='bold',
    loc='left',
    pad=15
)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(axis='y', length=0, labelsize=10)
ax.tick_params(axis='x', labelsize=10)
ax.grid(axis='x', color='#E0E0E0', linewidth=0.8)
ax.set_axisbelow(True)

# Brief caveat
fig.text(
    0.01,
    0.01,
    "Defect share isolates quality from return-window effects. Source: data.csv.",
    fontsize=8,
    color='#666666'
)

plt.tight_layout(rect=[0, 0.03, 1, 1])
