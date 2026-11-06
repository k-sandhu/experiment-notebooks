import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load data
df = pd.read_csv('data.csv')

# Use mid-month dates for plotting
df['month_dt'] = pd.to_datetime(df['month']) + pd.Timedelta(days=14)

# Pre- and post-restriction averages
pre = df[df['month_dt'] < '2026-06-01']
post = df[df['month_dt'] >= '2026-06-01']

pre_avg = pre.groupby('district')['litres_per_household_day'].mean()
post_avg = post.groupby('district')['litres_per_household_day'].mean()
reduction = ((pre_avg - post_avg) / pre_avg * 100).sort_values()

# Create figure with two panels
fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={'width_ratios': [1.2, 1]}
)

# ----- Left panel: monthly household water use -----
for dist, g in df.groupby('district'):
    if dist != 'Hillcrest':
        ax1.plot(
            g['month_dt'],
            g['litres_per_household_day'],
            color='gray',
            alpha=0.45,
            linewidth=1.5
        )

# Highlight Hillcrest
hill = df[df['district'] == 'Hillcrest'].sort_values('month_dt')
ax1.plot(
    hill['month_dt'],
    hill['litres_per_household_day'],
    color='crimson',
    linewidth=2.5,
    marker='o',
    label='Hillcrest'
)

# District average
avg_by_month = df.groupby('month_dt')['litres_per_household_day'].mean()
ax1.plot(
    avg_by_month.index,
    avg_by_month.values,
    color='black',
    linestyle='--',
    linewidth=2,
    marker='s',
    label='District average'
)

# Dummy handle for other districts
ax1.plot([], [], color='gray', alpha=0.6, label='Other districts')

# Restrictions start
ax1.axvline(pd.Timestamp('2026-06-01'), color='black', linestyle=':', linewidth=1.5)
ax1.text(
    pd.Timestamp('2026-06-05'),
    ax1.get_ylim()[1] * 0.97,
    'Restrictions\nbegin',
    va='top',
    fontsize=8
)

ax1.set_title('Monthly household water use')
ax1.set_ylabel('Litres per household per day')
ax1.set_xlabel('Month')
ax1.tick_params(axis='x', rotation=45)
ax1.legend(fontsize=8, loc='lower left')

# ----- Right panel: reduction after restrictions vs target -----
colors = ['crimson' if d == 'Hillcrest' else 'steelblue' for d in reduction.index]
ax2.barh(reduction.index, reduction.values, color=colors)

ax2.axvline(20, color='black', linestyle='--', linewidth=1.5, label='20% target')
ax2.set_xlabel('Reduction from Apr-May to Jun-Sep (%)')
ax2.set_title('Reduction after restrictions')
ax2.legend(fontsize=8, loc='lower right')

# Annotate bars
for i, (dist, val) in enumerate(reduction.items()):
    label = f'{val:.1f}%'
    if dist == 'Hillcrest':
        label += ' (meter adj. ~9%)'
    ax2.text(
        val + 0.5,
        i,
        label,
        va='center',
        fontsize=8,
        color='crimson' if dist == 'Hillcrest' else 'black'
    )

ax2.set_xlim(0, max(35, reduction.max() + 8))

fig.tight_layout()
