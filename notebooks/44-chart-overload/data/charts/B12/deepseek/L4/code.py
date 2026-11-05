import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv('data.csv')

# Restriction period: June–September 2026
post = df[df['month'].between('2026-06', '2026-09')].copy()

# Adjust Hillcrest's July–September readings for the new meters (read ~8% high)
post['adj_lphd'] = post['litres_per_household_day']
hill_mask = (post['district'] == 'Hillcrest') & (post['month'] >= '2026-07')
post.loc[hill_mask, 'adj_lphd'] = post.loc[hill_mask, 'adj_lphd'] / 1.08

post_avg = post.groupby('district')['adj_lphd'].mean()
target = df.groupby('district')['target_lphd'].first()
gap = post_avg - target

# Sort from largest over-target to largest under-target
order = gap.sort_values(ascending=False).index
gap_sorted = gap.loc[order]

fig, ax = plt.subplots(figsize=(10, 6))
y = np.arange(len(order))

colors = ['#D55E00' if d == 'Hillcrest' else '#BDBDBD' for d in order]
ax.barh(y, gap_sorted.values, color=colors, height=0.66, edgecolor='none', zorder=2)

ax.set_yticks(y)
ax.set_yticklabels(order, fontsize=12)
ax.invert_yaxis()

ax.axvline(0, color='#444444', linewidth=1.1, zorder=1)

ax.set_xlabel(
    'Average daily use over (+) / under (–) target (L/household/day), Jun–Sep',
    fontsize=10
)
ax.set_xlim(-35, 65)
ax.set_xticks([-20, 0, 20, 40, 60])

ax.grid(axis='x', color='#E6E6E6', linewidth=0.8, zorder=0)
ax.set_axisbelow(True)

for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)
ax.tick_params(axis='both', length=0)

ax.set_title(
    'Hillcrest is the enforcement priority: it remains 48 L/household/day over target after meter adjustment',
    loc='left', fontsize=14, fontweight='bold', pad=14
)

hill_idx = list(order).index('Hillcrest')
hill_gap = gap_sorted.loc['Hillcrest']
ax.text(
    hill_gap + 1.5, hill_idx, f'{hill_gap:.0f} L over',
    va='center', ha='left', fontsize=11,
    color='#D55E00', fontweight='bold'
)

fig.text(
    0.01, 0.02,
    'Hillcrest Jul–Sep meter readings adjusted down 8% for new meters '
    '(unadjusted gap: 72 L). Bars left of zero are below target.',
    fontsize=9, color='#555555', ha='left', va='bottom'
)

fig.subplots_adjust(left=0.18, right=0.95, top=0.83, bottom=0.17)
