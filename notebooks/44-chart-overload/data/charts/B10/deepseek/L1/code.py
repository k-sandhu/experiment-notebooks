import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# Read data
df = pd.read_csv('data.csv')
df['signup_month'] = df['signup_month'].astype(str)

# Cohort-level day-30 table
day30 = df[df['day'] == 30].copy().sort_values('signup_month')

old_months = ['2026-01', '2026-02', '2026-03', '2026-04', '2026-05']
new_campaign_months = ['2026-06', '2026-07', '2026-08']
sep_month = '2026-09'

old_avg30 = day30.loc[day30['onboarding_version'] == 'old', 'retention_pct'].mean()
new_campaign_avg30 = day30.loc[
    (day30['onboarding_version'] == 'new') &
    day30['signup_month'].isin(new_campaign_months),
    'retention_pct'
].mean()
sep30 = day30.loc[day30['signup_month'] == sep_month, 'retention_pct'].iloc[0]

old_paid = day30.loc[
    day30['onboarding_version'] == 'old',
    'paid_conversion_30d_pct'
].mean()
new_paid = day30.loc[
    (day30['onboarding_version'] == 'new') &
    day30['signup_month'].isin(new_campaign_months),
    'paid_conversion_30d_pct'
].mean()

old_lessons = day30.loc[
    day30['onboarding_version'] == 'old',
    'avg_lessons_first_30d'
].mean()
new_lessons = day30.loc[
    (day30['onboarding_version'] == 'new') &
    day30['signup_month'].isin(new_campaign_months),
    'avg_lessons_first_30d'
].mean()

# Later-day retention: old vs new campaign cohorts
days = [30, 60, 90]
old_vals = []
new_vals = []
for d in days:
    old_vals.append(
        df.loc[
            (df['onboarding_version'] == 'old') &
            (df['day'] == d) &
            (df['signup_month'].isin(old_months)),
            'retention_pct'
        ].mean()
    )
    new_vals.append(
        df.loc[
            (df['onboarding_version'] == 'new') &
            (df['day'] == d) &
            (df['signup_month'].isin(new_campaign_months)),
            'retention_pct'
        ].mean()
    )

# Figure
fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6),
    gridspec_kw={'width_ratios': [1.25, 1]}
)
fig.subplots_adjust(top=0.84, bottom=0.16, left=0.08, right=0.95, wspace=0.35)

# Left panel: day-30 retention by cohort
x = np.arange(len(day30))
colors = [
    '#8D99AE' if v == 'old' else '#2A9D8F'
    for v in day30['onboarding_version']
]

campaign_mask = day30['signup_month'].isin(new_campaign_months)
if campaign_mask.any():
    ax1.axvspan(
        x[campaign_mask].min() - 0.5,
        x[campaign_mask].max() + 0.5,
        color='#F4D35E', alpha=0.20, zorder=0
    )

bars = ax1.bar(
    x, day30['retention_pct'].values,
    color=colors, edgecolor='white', linewidth=1.2, zorder=3
)

# Emphasize September post-campaign bar
for i, row in enumerate(day30.itertuples()):
    if row.signup_month == sep_month:
        bars[i].set_facecolor('#5BC0B6')
        bars[i].set_edgecolor('#1F6F66')
        bars[i].set_hatch('//')
        bars[i].set_linewidth(1.4)

# Old average reference line
ax1.axhline(old_avg30, color='#5C677D', linestyle='--', linewidth=1.5, zorder=2)
ax1.text(
    x[-1] + 0.4, old_avg30 + 0.7,
    f'Old avg {old_avg30:.1f}%',
    color='#5C677D', ha='right', va='bottom', fontsize=9
)

# Value labels
for i, row in enumerate(day30.itertuples()):
    ax1.text(
        i, row.retention_pct + 0.4, f'{row.retention_pct:.1f}',
        ha='center', va='bottom', fontsize=8
    )

month_labels = pd.to_datetime(
    day30['signup_month'], format='%Y-%m'
).dt.strftime('%b')

ax1.set_xticks(x)
ax1.set_xticklabels(month_labels)
ax1.set_ylim(0, 38)
ax1.set_ylabel('Retained at day 30 (%)')
ax1.set_title(
    'Day-30 retention by signup cohort',
    loc='left', fontsize=12, fontweight='bold'
)

ax1.text(
    x[campaign_mask].mean(), 36.2,
    f'TV campaign\nJun–Aug\nNew avg {new_campaign_avg30:.1f}%',
    ha='center', va='top', fontsize=8.5, color='#8A6D00'
)

ax1.text(
    x[day30['signup_month'] == sep_month][0], sep30 + 1.8,
    f'Post-campaign\n{sep30:.1f}%',
    ha='center', va='bottom', fontsize=8.5, color='#1F6F66'
)

legend_elements = [
    Patch(facecolor='#8D99AE', label='Old onboarding (Jan–May)'),
    Patch(facecolor='#2A9D8F', label='New onboarding (Jun–Aug)'),
    Patch(
        facecolor='#5BC0B6', hatch='//', edgecolor='#1F6F66',
        label='New onboarding: Sep (post-campaign)'
    )
]
ax1.legend(
    handles=legend_elements, loc='upper left',
    fontsize=7.5, frameon=True, framealpha=0.9
)

# Right panel: later-day retention lift
x2 = np.arange(len(days))
width = 0.36

b_old = ax2.bar(
    x2 - width / 2, old_vals, width,
    color='#8D99AE', label='Old onboarding (Jan–May)'
)
b_new = ax2.bar(
    x2 + width / 2, new_vals, width,
    color='#2A9D8F', label='New onboarding (Jun–Aug)'
)

for bars_group in (b_old, b_new):
    for b in bars_group:
        h = b.get_height()
        ax2.text(
            b.get_x() + b.get_width() / 2, h + 0.5, f'{h:.1f}',
            ha='center', va='bottom', fontsize=8
        )

ax2.set_xticks(x2)
ax2.set_xticklabels([f'Day {d}' for d in days])
ax2.set_ylim(0, 38)
ax2.set_ylabel('Retention (%)')
ax2.set_title(
    'Retention lift persists past day 30',
    loc='left', fontsize=12, fontweight='bold'
)
ax2.legend(loc='upper right', fontsize=8, frameon=True)

# Overall title and subtitle
fig.suptitle(
    'New onboarding lifts retention after day 1 — September post-campaign still beats old cohorts',
    fontsize=13, fontweight='bold', x=0.01, ha='left', y=0.98
)
fig.text(
    0.01, 0.915,
    'Retention = % of cohort active on or after that day. TV campaign June–August shaded.',
    fontsize=9, ha='left'
)

# Bottom note with secondary metrics
fig.text(
    0.5, 0.035,
    f'Day-1 retention flat: ~69–70% in both groups    |    '
    f'Paid conversion 30d: {old_paid:.1f}% → {new_paid:.1f}%    |    '
    f'Lessons first 30d: {old_lessons:.1f} → {new_lessons:.1f} '
    f'(+{100 * (new_lessons / old_lessons - 1):.0f}%)',
    ha='center', va='bottom', fontsize=8.5
)
