import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv('data.csv')

# Urgent median wait by hospital
urgent = (
    df[df['triage_category'] == 'Urgent']
    .set_index('hospital')['median_wait_min']
)

# Overall percentage left without being seen, weighted by visits
weighted_lwbs = (
    df['visits'] * df['left_without_being_seen_pct']
).groupby(df['hospital']).sum()
total_visits = df.groupby('hospital')['visits'].sum()
lwbs = weighted_lwbs / total_visits

# Order hospitals by urgent wait, longest first
order = urgent.sort_values(ascending=False).index.tolist()
urgent = urgent.loc[order]
lwbs = lwbs.loc[order]

# Averages for the other seven hospitals
other = [h for h in order if h != 'Riverside']
avg_urgent = urgent[other].mean()
other_mask = df['hospital'].isin(other)
avg_lwbs = (
    (df.loc[other_mask, 'visits'] * df.loc[other_mask, 'left_without_being_seen_pct']).sum()
    / df.loc[other_mask, 'visits'].sum()
)

# Colours
highlight = '#D55E00'
grey = '#BDBDBD'
text_col = '#333333'
line_col = '#7F7F7F'
colors = [highlight if h == 'Riverside' else grey for h in order]

y = np.arange(len(order))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6), sharey=True)

# Left panel: urgent wait
ax1.barh(y, urgent.values, color=colors, height=0.68, zorder=2)
ax1.axvline(avg_urgent, color=line_col, linestyle='--', linewidth=1, zorder=1)
ax1.text(
    avg_urgent + 1, -0.55, f'Other avg {avg_urgent:.0f} min',
    color=line_col, fontsize=8, va='center', ha='left'
)

y_r = order.index('Riverside')
ax1.text(
    urgent.loc['Riverside'] + 1, y_r,
    f"{urgent.loc['Riverside']:.0f} min",
    va='center', ha='left', fontsize=10, color=highlight, fontweight='bold'
)

y_n = order.index('Northgate')
ax1.text(
    urgent.loc['Northgate'] + 1, y_n,
    '41 min raw; ≈26 adj.',
    va='center', ha='left', fontsize=8, color=text_col
)
# Mark Northgate's adjusted value on the bar
ax1.plot(
    [26, 26], [y_n - 0.25, y_n + 0.25],
    color=text_col, linewidth=2, zorder=3
)

ax1.set_xlabel('Median urgent wait (minutes)', fontsize=10)
ax1.set_xlim(0, 90)
ax1.set_yticks(y)
ax1.set_yticklabels(order)
ax1.set_ylim(len(order) - 0.5, -0.8)
ax1.grid(axis='x', color='#E6E6E6', linewidth=0.8, zorder=0)
ax1.set_axisbelow(True)

# Right panel: left without being seen
ax2.barh(y, lwbs.values, color=colors, height=0.68, zorder=2)
ax2.axvline(avg_lwbs, color=line_col, linestyle='--', linewidth=1, zorder=1)
ax2.text(
    avg_lwbs + 0.2, -0.55, f'Other avg {avg_lwbs:.1f}%',
    color=line_col, fontsize=8, va='center', ha='left'
)
ax2.text(
    lwbs.loc['Riverside'] + 0.2, y_r,
    f"{lwbs.loc['Riverside']:.1f}%",
    va='center', ha='left', fontsize=10, color=highlight, fontweight='bold'
)

ax2.set_xlabel('% left without being seen', fontsize=10)
ax2.set_xlim(0, 11)
ax2.tick_params(axis='y', left=False, labelleft=False)
ax2.grid(axis='x', color='#E6E6E6', linewidth=0.8, zorder=0)
ax2.set_axisbelow(True)

# Clean axes
for ax in (ax1, ax2):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.tick_params(axis='x', labelsize=9)

# Title and caveat
fig.suptitle(
    'Riverside should get the 12 triage nurses:\n'
    'its urgent waits are twice as long and a higher share leave without being seen.',
    fontsize=13, fontweight='bold', x=0.5, y=0.98, ha='center'
)

fig.text(
    0.5, 0.02,
    "Northgate's wait clock starts at registration (adds ~15 min); its 41-min urgent wait is "
    "≈26 min on the same basis. Dashed lines show the average of the other seven hospitals.",
    fontsize=8, ha='center', va='bottom', color=text_col
)

fig.subplots_adjust(top=0.80, bottom=0.16, left=0.15, right=0.95, wspace=0.22)
