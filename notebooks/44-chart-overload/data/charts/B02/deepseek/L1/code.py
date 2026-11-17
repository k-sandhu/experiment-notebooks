import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv('data.csv')

df['left_unseen'] = df['visits'] * df['left_without_being_seen_pct'] / 100.0

g = df.groupby('hospital', sort=False)
hosp = pd.DataFrame({
    'visits': g['visits'].sum(),
    'left_unseen': g['left_unseen'].sum()
})
hosp['lwbs_pct'] = 100.0 * hosp['left_unseen'] / hosp['visits']
hosp = hosp.sort_values('left_unseen', ascending=True)

fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6), gridspec_kw={'width_ratios': [1.15, 1.0]}
)

# Left panel: absolute number of patients leaving without being seen
y = np.arange(len(hosp))
colors = ['#d62728' if h == 'Riverside' else '#bdbdbd' for h in hosp.index]
ax1.barh(y, hosp['left_unseen'], color=colors, height=0.65, edgecolor='white')

ax1.set_yticks(y)
ax1.set_yticklabels(hosp.index, fontsize=10)
ax1.set_xlabel('Patients leaving without being seen per quarter', fontsize=10)
ax1.set_title('Patients leaving without being seen', fontsize=11,
              fontweight='bold', loc='left', pad=8)

max_left = hosp['left_unseen'].max()
for yi, (h, row) in enumerate(hosp.iterrows()):
    ax1.text(
        row['left_unseen'] + max_left * 0.02,
        yi,
        f"{row['left_unseen']:.0f}  ({row['lwbs_pct']:.1f}%)",
        va='center',
        fontsize=9,
        color='#2b2b2b'
    )

ax1.set_xlim(0, max_left * 1.30)
ax1.grid(axis='x', color='#e6e6e6', linewidth=0.8)
ax1.set_axisbelow(True)
for spine in ['top', 'right']:
    ax1.spines[spine].set_visible(False)
ax1.tick_params(axis='x', labelsize=9)

# Right panel: median wait by triage category, highlighting Riverside
cat_y = {'Urgent': 2, 'Semi-urgent': 1, 'Non-urgent': 0}

for cat in ['Urgent', 'Semi-urgent', 'Non-urgent']:
    sub = df[df['triage_category'] == cat]
    other = sub[sub['hospital'] != 'Riverside']

    jitter = np.linspace(-0.08, 0.08, len(other))
    ax2.scatter(
        other['median_wait_min'],
        cat_y[cat] + jitter,
        s=42,
        color='#9e9e9e',
        alpha=0.75,
        edgecolor='white',
        linewidth=0.4,
        label='Other EDs' if cat == 'Urgent' else None
    )

    riv = sub[sub['hospital'] == 'Riverside'].iloc[0]
    ax2.scatter(
        riv['median_wait_min'],
        cat_y[cat],
        s=150,
        marker='D',
        color='#d62728',
        edgecolor='white',
        linewidth=1.2,
        zorder=5,
        label='Riverside' if cat == 'Urgent' else None
    )
    ax2.text(
        riv['median_wait_min'] + 5,
        cat_y[cat],
        f"{riv['median_wait_min']:.0f} min",
        va='center',
        fontsize=9,
        fontweight='bold',
        color='#d62728'
    )

ax2.set_yticks([0, 1, 2])
ax2.set_yticklabels(['Non-urgent', 'Semi-urgent', 'Urgent'], fontsize=10)
ax2.set_xlabel('Median minutes to first seen by a doctor', fontsize=10)
ax2.set_title('Median wait by triage category', fontsize=11,
              fontweight='bold', loc='left', pad=8)
ax2.set_xlim(0, df['median_wait_min'].max() * 1.18)
ax2.grid(axis='x', color='#e6e6e6', linewidth=0.8)
ax2.set_axisbelow(True)
for spine in ['top', 'right']:
    ax2.spines[spine].set_visible(False)
ax2.tick_params(axis='x', labelsize=9)
ax2.legend(loc='upper right', frameon=False, fontsize=9, handletextpad=0.4)

fig.suptitle(
    'Funding priority for 12 extra triage nurses: Riverside ED',
    x=0.01, y=0.98, ha='left', fontsize=15.5,
    fontweight='bold', color='#d62728'
)
fig.text(
    0.01, 0.925,
    'Riverside has the most patients leaving without being seen and the longest median waits in every triage category.',
    ha='left', fontsize=10.5, color='#333333'
)
fig.text(
    0.01, 0.045,
    'Note: Northgate waits begin at registration rather than triage (~15 min longer); Riverside remains the longest after this adjustment.',
    ha='left', fontsize=8.3, color='#555555'
)

fig.subplots_adjust(
    left=0.155, right=0.985, top=0.82, bottom=0.17, wspace=0.38
)
