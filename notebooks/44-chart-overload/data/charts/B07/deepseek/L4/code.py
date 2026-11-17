import pandas as pd
import matplotlib.pyplot as plt

# Load data and focus on the latest quarter for the quality comparison
df = pd.read_csv('data.csv')
q3 = df[df['quarter'] == '2026Q3'].copy()
q3 = q3.sort_values('defect_share_of_returns_pct', ascending=True)

# Create figure
fig, ax = plt.subplots(figsize=(10, 6))

# Highlight Footwear, use grey for context
colors = ['#C62828' if c == 'Footwear' else '#C0C0C0' for c in q3['category']]
ax.barh(
    q3['category'],
    q3['defect_share_of_returns_pct'],
    color=colors,
    edgecolor='none',
    height=0.68
)

# Label the key values: Footwear and the next-highest category
footwear_val = q3.loc[q3['category'] == 'Footwear', 'defect_share_of_returns_pct'].iloc[0]
ax.text(
    footwear_val + 1.2,
    len(q3) - 1,
    f'{footwear_val:.0f}%',
    va='center',
    ha='left',
    fontsize=14,
    fontweight='bold',
    color='#C62828'
)

second = q3.iloc[-2]
ax.text(
    second['defect_share_of_returns_pct'] + 1.2,
    len(q3) - 2,
    f"{second['defect_share_of_returns_pct']:.0f}%",
    va='center',
    ha='left',
    fontsize=11,
    color='#555555'
)

# Emphasize Footwear on the y-axis
for label in ax.get_yticklabels():
    if label.get_text() == 'Footwear':
        label.set_fontweight('bold')
        label.set_color('#C62828')

# Formatting
ax.set_xlim(0, 52)
ax.set_xlabel('Defect share of returns (%)', fontsize=11)
ax.set_title(
    "Investigate Footwear first: 46% of its Q3 2026 returns cited a defect, vs ≤12% elsewhere.",
    fontsize=15,
    fontweight='bold',
    loc='left',
    pad=16
)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(axis='y', length=0, labelsize=11)
ax.tick_params(axis='x', labelsize=10)
ax.grid(axis='x', color='#E6E6E6', linewidth=0.8)
ax.set_axisbelow(True)

# Brief caveat
fig.text(
    0.01,
    0.01,
    "Defect share = returns citing a defect ÷ all returns. Footwear's Q3 return-window extension explains only ~2 pts of return rate, not the defect spike.",
    fontsize=8,
    color='#666666'
)

plt.tight_layout(rect=[0, 0.04, 1, 1])
