import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load and prepare data
df = pd.read_csv('data.csv')
df['date'] = pd.to_datetime(df['date'])

critical = df[
    (df['date'] >= pd.Timestamp('2026-01-12')) &
    (df['date'] <= pd.Timestamp('2026-01-15'))
].reset_index(drop=True)

positions = np.arange(len(critical))
actual = critical['actual_peak_mw'].to_numpy()
available = critical['available_capacity_mw'].iloc[0]  # 910 MW during Unit 3 outage
with_extra = available + 40

# Highlight 14 January
colors = ['#BDBDBD'] * len(critical)
jan14_idx = int(np.where(critical['date'].dt.day == 14)[0][0])
colors[jan14_idx] = '#D73027'

# Plot
fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(top=0.80, bottom=0.18, left=0.09, right=0.95)

ax.bar(
    positions, actual, width=0.55,
    color=colors, edgecolor='none', zorder=2
)

# Capacity lines
ax.hlines(
    available, -0.4, 3.55,
    colors='#777777', linestyles=(0, (4, 3)),
    linewidth=1.6, zorder=3
)
ax.hlines(
    with_extra, -0.4, 3.55,
    colors='black', linestyles='-',
    linewidth=1.6, zorder=4
)

# Direct labels for capacity lines
ax.text(
    3.58, available + 6,
    'Available capacity\n910 MW',
    va='bottom', ha='left', fontsize=9, color='#666666'
)
ax.text(
    3.58, with_extra + 6,
    'With 40 MW extra\n950 MW',
    va='bottom', ha='left', fontsize=9, color='black', fontweight='bold'
)

# Annotate 14 Jan peak and remaining shortfall
y14 = actual[jan14_idx]
ax.text(
    jan14_idx, y14 + 10,
    '1,012 MW',
    ha='center', va='bottom', fontsize=9.5,
    color='#D73027', fontweight='bold'
)

ax.annotate(
    '', xy=(jan14_idx, with_extra), xytext=(jan14_idx, y14),
    arrowprops=dict(arrowstyle='<->', color='#D73027', lw=1.6),
    zorder=5
)
ax.text(
    jan14_idx + 0.12, (with_extra + y14) / 2,
    '62 MW\nstill short',
    va='center', ha='left', fontsize=10,
    color='#D73027', fontweight='bold'
)

# Axes formatting
ax.set_xticks(positions)
ax.set_xticklabels([d.strftime('%d %b') for d in critical['date']], fontsize=10)
ax.set_xlim(-0.6, 4.8)
ax.set_ylim(0, 1100)
ax.set_yticks(np.arange(0, 1001, 200))
ax.set_ylabel('Peak demand / capacity (MW)', fontsize=10)

ax.grid(axis='y', color='#E5E5E5', linewidth=0.8, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(axis='both', colors='#333333')

# Titles and caveat
fig.text(
    0.09, 0.93,
    '40 MW extra cuts the 14 Jan shortfall from 102 MW to 62 MW—but does not close it',
    fontsize=13.5, fontweight='bold', ha='left'
)
fig.text(
    0.09, 0.88,
    'Critical days during the 10–16 Jan Unit 3 outage; bars are actual peak demand.',
    fontsize=10, color='#444444', ha='left'
)
fig.text(
    0.09, 0.04,
    'If Unit 3 were running, 14 Jan would be 12 MW above the 1,000 MW post-purchase capacity.',
    fontsize=8.7, color='#666666', ha='left'
)
