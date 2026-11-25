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

# Sort from largest overshoot to largest under-target
order = gap.sort_values(ascending=False).index
gap_sorted = gap.loc[order]

fig, ax = plt.subplots(figsize=(10, 6))
y = np.arange(len(order))
colors = ['#c0392b' if d == 'Hillcrest' else '#bdbdbd' for d in order]
ax.barh(y, gap_sorted.values, color=colors, height=0.68, edgecolor='none')

ax.set_yticks(y)
ax.set_yticklabels(order)
ax.invert_yaxis()

ax.axvline(0, color='black', linewidth=1.0)
ax.text(0, -0.65, 'Target', ha='center', va='bottom', fontsize=9, color='black')

ax.set_xlabel('Average daily use above/below target (litres per household per day), Jun–Sep')
ax.set_xlim(-35, 70)
ax.grid(axis='x', color='#e8e8e8', linewidth=0.8)
ax.set_axisbelow(True)
for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)

ax.set_title(
    'Hillcrest is the clear enforcement priority: even after meter adjustment, it exceeds its target by ~48 L/household/day.',
    loc='left', fontsize=13, fontweight='bold', pad=16
)

hill_idx = list(order).index('Hillcrest')
hill_gap = gap_sorted.loc['Hillcrest']
ax.text(hill_gap + 1.5, hill_idx, f'+{hill_gap:.0f} L over', va='center', ha='left',
        fontsize=11, color='#c0392b', fontweight='bold')

fig.text(
    0.01, 0.015,
    'Hillcrest Jul–Sep readings adjusted down 8% for new meters; unadjusted gap is 72 L. '
    'Negative bars are below target.',
    fontsize=9, color='#555555', ha='left', va='bottom'
)

fig.subplots_adjust(left=0.18, right=0.95, top=0.82, bottom=0.17)
