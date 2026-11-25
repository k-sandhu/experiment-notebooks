import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv('data.csv')

# Aggregate forecast variance by department
dept = (df.groupby('department', as_index=False)
          .agg(variance=('variance_k', 'sum')))
dept = dept.sort_values('variance', ascending=True)

total_var = dept['variance'].sum()
transit_var = dept.loc[dept['department'] == 'Transit', 'variance'].iloc[0]
transit_share = transit_var / total_var if total_var != 0 else 0

transit_ot = df[(df['department'] == 'Transit') &
                (df['budget_line'] == 'Overtime')].iloc[0]
ot_var = transit_ot['variance_k']
ot_pct = transit_ot['variance_pct']

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor('white')

y = np.arange(len(dept))
colors = []
for d, v in zip(dept['department'], dept['variance']):
    if d == 'Transit':
        colors.append('#D62728')
    elif v > 0:
        colors.append('#F28E2B')
    elif v < 0:
        colors.append('#4C78A8')
    else:
        colors.append('#B0B0B0')

ax.barh(y, dept['variance'], color=colors, height=0.7)
ax.set_yticks(y)
ax.set_yticklabels(dept['department'], fontsize=10)
ax.axvline(0, color='#333333', linewidth=0.8)

ax.set_title('Transit is the clear focus for a mid-year spending review',
             fontsize=14, fontweight='bold', loc='left', pad=20)
ax.text(0, 1.02, 'Forecast year-end variance by department, $ thousands',
        transform=ax.transAxes, fontsize=10, color='#555555',
        ha='left', va='bottom')

# Bar labels
xmax = dept['variance'].max()
xmin = dept['variance'].min()
pad = max(abs(xmax), abs(xmin)) * 0.04

for yi, v, d in zip(y, dept['variance'], dept['department']):
    if v > 0:
        label = f'+${v:,.0f}k'
    elif v < 0:
        label = f'-${abs(v):,.0f}k'
    else:
        label = '$0k'

    ha = 'left' if v >= 0 else 'right'
    offset = pad if v >= 0 else -pad
    ax.text(v + offset, yi, label, va='center', ha=ha, fontsize=9,
            fontweight='bold' if d == 'Transit' else 'normal',
            color='#D62728' if d == 'Transit' else '#333333')

ax.set_xlim(xmin - pad * 6, xmax + pad * 14)
ax.set_xlabel('Forecast variance vs budget ($ thousands)', fontsize=9)
ax.xaxis.grid(True, linestyle=':', alpha=0.6)
ax.set_axisbelow(True)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)

# Callout box
ax.text(0.99, 0.04,
        f'Citywide forecast overspend: +${total_var:,.0f}k\n'
        f'Transit: +${transit_var:,.0f}k = {transit_share:.0%} of citywide overspend\n'
        f'Transit overtime alone: +${ot_var:,.0f}k (+{ot_pct:.0f}% vs budget)',
        transform=ax.transAxes, ha='right', va='bottom', fontsize=9,
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#F5F5F5', edgecolor='none'))

fig.tight_layout()
