import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('data.csv')

# Department net forecast variance in $M
dept = df.groupby('department', as_index=False)['variance_k'].sum()
dept['variance_m'] = dept['variance_k'] / 1000.0
dept = dept.sort_values('variance_m', ascending=False).reset_index(drop=True)

total_m = dept['variance_m'].sum()
transit_m = dept.loc[dept['department'] == 'Transit', 'variance_m'].iloc[0]
transit_share = transit_m / total_m * 100

# One strong colour for what matters; grey for context
strong = '#D55E00'
grey_pos = '#9E9E9E'
grey_neg = '#D0D0D0'
colors = [
    strong if d == 'Transit' else (grey_pos if v >= 0 else grey_neg)
    for d, v in zip(dept['department'], dept['variance_m'])
]

fig, (ax, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={'width_ratios': [2.7, 1.0]}
)

# Main chart: department forecast variance
y = np.arange(len(dept))
ax.barh(y, dept['variance_m'], color=colors, height=0.7, edgecolor='white')
ax.set_yticks(y)
ax.set_yticklabels(dept['department'])
ax.invert_yaxis()
ax.axvline(0, color='black', linewidth=0.8)
ax.set_xlabel('Forecast year-end variance ($M; positive = overspend)', fontsize=9)
ax.grid(axis='x', color='#E8E8E8', linewidth=0.8)
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.tick_params(axis='y', length=0, labelsize=9)
ax.tick_params(axis='x', labelsize=8)
ax.set_xlim(-0.55, 4.0)

# Direct labels for the three departments that matter for the decision
for name in ['Transit', 'Roads', 'Police']:
    yi = dept.index[dept['department'] == name][0]
    val = dept.loc[yi, 'variance_m']
    if name == 'Transit':
        label = f"${val:.1f}M\n({transit_share:.0f}% of city total)"
        ax.text(val + 0.08, yi, label, va='center', ha='left',
                fontsize=10, fontweight='bold', color='black')
    else:
        ax.text(val + 0.08, yi, f"${val:.1f}M", va='center', ha='left',
                fontsize=9, color='black')

# Roads weather caveat
roads_y = dept.index[dept['department'] == 'Roads'][0]
ax.annotate(
    'Snow-clearing risk: up to +$1.5M\nif harsh winter',
    xy=(dept.loc[roads_y, 'variance_m'], roads_y),
    xytext=(1.1, roads_y + 0.05),
    va='center', ha='left', fontsize=8, color='#555555',
    arrowprops=dict(arrowstyle='-', color='#777777', lw=0.7)
)

# Figure title states the decision-relevant message
fig.suptitle(
    f"Transit should be the first mid-year review: it drives {transit_share:.0f}% "
    f"of the city's ${total_m:.1f}M forecast overspend, mostly through overtime.",
    x=0.02, y=0.98, ha='left', fontsize=12.5, fontweight='bold'
)
fig.subplots_adjust(left=0.17, right=0.96, top=0.83, bottom=0.12, wspace=0.55)

# Right panel: Transit overtime detail
budget_ot = 2.0
forecast_ot = 4.4
over_ot = forecast_ot - budget_ot

ax2.bar([0], [budget_ot], width=0.55, color='#C9C9C9', edgecolor='white')
ax2.bar([0], [over_ot], bottom=[budget_ot], width=0.55, color=strong, edgecolor='white')
ax2.axhline(budget_ot, color='#555555', linestyle='--', linewidth=0.9)

ax2.text(0, budget_ot / 2, f"Budget\n${budget_ot:.1f}M",
         ha='center', va='center', fontsize=8.5, color='#333333')
ax2.text(0, budget_ot + over_ot / 2, f"Over\n${over_ot:.1f}M\n(+120%)",
         ha='center', va='center', fontsize=8.5, color='white', fontweight='bold')
ax2.text(0, forecast_ot + 0.15, f"Forecast ${forecast_ot:.1f}M",
         ha='center', va='bottom', fontsize=8.5, color='#222222')

ax2.set_xlim(-0.6, 0.6)
ax2.set_ylim(0, 5.3)
ax2.set_xticks([])
ax2.set_ylabel('$M', fontsize=8.5)
ax2.set_title('Transit overtime', fontsize=10, loc='left', pad=6)
ax2.grid(axis='y', color='#E8E8E8', linewidth=0.8)
ax2.set_axisbelow(True)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.spines['left'].set_visible(False)
ax2.tick_params(axis='y', labelsize=8)

ax2.text(0, -0.35, 'Driver vacancies covered by extra shifts',
         ha='center', va='top', fontsize=7.5, color='#555555',
         transform=ax2.transData, clip_on=False)
