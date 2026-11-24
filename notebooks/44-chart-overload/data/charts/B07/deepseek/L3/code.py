import pandas as pd
import matplotlib.pyplot as plt

# Read the data
df = pd.read_csv('data.csv')

# Previous six quarters (all except Q3 2026)
prev_quarters = ['2025Q1', '2025Q2', '2025Q3', '2025Q4', '2026Q1', '2026Q2']

# Average return rate over previous quarters for each category
prev_avg = df[df['quarter'].isin(prev_quarters)].groupby('category')['return_rate_pct'].mean()

# Q3 2026 return rate for each category
q3_2026 = df[df['quarter'] == '2026Q3'].set_index('category')['return_rate_pct']

# Change from prior average
change = (q3_2026 - prev_avg).dropna()
change_sorted = change.sort_values(ascending=False)

# Colors: strong red for Footwear, grey for context
colors = ['#D62728' if cat == 'Footwear' else '#B0B0B0' for cat in change_sorted.index]

# Create figure
fig, ax = plt.subplots(figsize=(10, 6))

# Horizontal bars
ax.barh(change_sorted.index, change_sorted.values, color=colors, edgecolor='none')

# Put the largest (Footwear) at the top
ax.invert_yaxis()

# Zero reference line
ax.axvline(0, color='black', linewidth=0.8, alpha=0.5)

# Set x-axis limits to fit annotation
min_change = change_sorted.min()
max_change = change_sorted.max()
ax.set_xlim(min_change - 1.5, max_change + 7)

# Footwear annotation
footwear_change = change_sorted['Footwear']
footwear_q3_rate = q3_2026['Footwear']
footwear_q3_defect = df[(df['category'] == 'Footwear') & (df['quarter'] == '2026Q3')]['defect_share_of_returns_pct'].values[0]
footwear_prev_defect = df[(df['category'] == 'Footwear') & (df['quarter'].isin(prev_quarters))]['defect_share_of_returns_pct'].mean()

text_x = footwear_change + 0.3
text_y = 0  # Footwear is at y=0 after invert
ax.text(text_x, text_y,
        f"Q3'26: {footwear_q3_rate:.1f}% return rate\n{footwear_q3_defect:.0f}% defects (vs ~{footwear_prev_defect:.0f}% prior)",
        va='center', ha='left', fontsize=10, color='#D62728', fontweight='bold')

# Axis labels and ticks
ax.set_xlabel('Change in return rate (percentage points)', fontsize=10)
ax.set_ylabel('')
ax.tick_params(axis='y', labelsize=10)
ax.tick_params(axis='x', labelsize=9)

# Title and subtitle
title = "Investigate Footwear first: its Q3 2026 return rate jumped to 19.2%, driven by defects"
subtitle = "Change in return rate vs prior 6-quarter average."
fig.text(0.01, 0.97, title, fontsize=14, fontweight='bold', ha='left', va='top')
fig.text(0.01, 0.92, subtitle, fontsize=10, color='gray', ha='left', va='top')

# Caveat
caveat = ("Footwear return window extended 30→60 days for Q3'26 promotion;\n"
          "past extensions added ~2 pts, so policy explains only a small part of the jump.")
fig.text(0.01, 0.02, caveat, fontsize=9, color='gray', ha='left', va='bottom')

# Grid and spines
ax.grid(axis='x', alpha=0.3, linestyle='--')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Layout adjustments
plt.subplots_adjust(top=0.85, bottom=0.15, left=0.18, right=0.95)
