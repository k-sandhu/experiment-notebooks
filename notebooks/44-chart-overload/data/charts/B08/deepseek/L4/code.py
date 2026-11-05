import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load and prepare data
df = pd.read_csv('data.csv')
df['date'] = pd.to_datetime(df['date'])

critical = df[
    (df['date'] >= pd.Timestamp('2026-01-12')) &
    (df['date'] <= pd.Timestamp('2026-01-15'))
].copy()

capacity = float(critical['available_capacity_mw'].iloc[0])  # 910 MW during Unit 3 outage
critical['shortfall'] = critical['actual_peak_mw'] - capacity
critical['covered'] = np.minimum(critical['shortfall'], 40)
critical['remaining'] = np.maximum(critical['shortfall'] - 40, 0)

positions = np.arange(len(critical))
covered = critical['covered'].to_numpy()
remaining = critical['remaining'].to_numpy()
dates = critical['date'].dt.strftime('%d %b').tolist()

jan13 = int(np.where(critical['date'].dt.day == 13)[0][0])
jan14 = int(np.where(critical['date'].dt.day == 14)[0][0])

# Plot
fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(top=0.79, bottom=0.18, left=0.10, right=0.95)

ax.bar(
    positions, covered, width=0.58,
    color='#BDBDBD', edgecolor='none', zorder=2
)
ax.bar(
    positions, remaining, width=0.58, bottom=covered,
    color='#D73027', edgecolor='none', zorder=2
)

# 40 MW purchase reference
ax.hlines(
    40, -0.5, 3.5,
    colors='#222222', linestyles=(0, (5, 3)),
    linewidth=1.4, zorder=4
)
ax.text(
    3.58, 40,
    '40 MW extra\ncapacity',
    va='center', ha='left', fontsize=9, color='#222222'
)

# Label only the shortfalls that remain after the purchase
ax.text(
    jan13, 43.5,
    '1 MW',
    ha='center', va='bottom',
    fontsize=8.5, color='#D73027', fontweight='bold'
)
ax.text(
    jan14, covered[jan14] + remaining[jan14] / 2,
    '62 MW\nstill short',
    ha='center', va='center',
    fontsize=9.5, color='white', fontweight='bold', zorder=5
)

# Axes formatting
ax.set_xticks(positions)
ax.set_xticklabels(dates, fontsize=10)
ax.set_xlim(-0.55, 4.2)
ax.set_ylim(0, 115)
ax.set_yticks([0, 20, 40, 60, 80, 100])
ax.set_ylabel('Shortfall below available capacity (MW)', fontsize=10)

ax.grid(axis='y', color='#E5E5E5', linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(axis='both', colors='#333333')

# Titles and caveat
fig.text(
    0.10, 0.94,
    '40 MW extra still leaves 14 Jan 62 MW short during the Unit 3 outage',
    fontsize=13.3, fontweight='bold', ha='left'
)
fig.text(
    0.10, 0.885,
    'Shortfall below 910 MW available capacity, 12–15 Jan; grey is covered by the purchase, red remains uncovered.',
    fontsize=9.8, color='#444444', ha='left'
)
fig.text(
    0.10, 0.055,
    "With Unit 3 running, 14 Jan's 1,012 MW peak is 52 MW above 960 MW capacity; 40 MW extra would leave 12 MW short.",
    fontsize=8.7, color='#666666', ha='left'
)
