import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Read and prepare data
df = pd.read_csv('data.csv')
df['date'] = pd.to_datetime(df['date'])

fix_date = pd.Timestamp('2026-09-26')

# Mobile only — the decision-critical segment
mobile = df[df['device'] == 'mobile'].copy()
mobile['period'] = np.where(
    mobile['date'] < fix_date,
    'Before fix\nSep 14–25',
    'After fix\nSep 26–27 (2 days)'
)

periods = ['Before fix\nSep 14–25', 'After fix\nSep 26–27 (2 days)']
variants = ['control', 'new_checkout']

agg = (
    mobile.groupby(['period', 'variant'])
    .agg(sessions=('sessions', 'sum'), orders=('orders', 'sum'))
    .reset_index()
)
agg['conversion'] = 100 * agg['orders'] / agg['sessions']
conv = agg.pivot(index='period', columns='variant', values='conversion').reindex(periods)

control_vals = conv['control'].values
new_vals = conv['new_checkout'].values

# Context numbers
orders_by_variant = df.groupby('variant')['orders'].sum()
overall_diff = 100 * (orders_by_variant['new_checkout'] - orders_by_variant['control']) / orders_by_variant['control']

post = df[df['date'] >= fix_date]
post_orders = post.groupby('variant')['orders'].sum()
post_diff = 100 * (post_orders['new_checkout'] - post_orders['control']) / post_orders['control']

mobile_sessions = df[df['device'] == 'mobile']['sessions'].sum()
total_sessions = df['sessions'].sum()
mobile_share = 100 * mobile_sessions / total_sessions

# Plot
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(periods))
width = 0.35

bars_old = ax.bar(
    x - width / 2, control_vals, width,
    color='#B0B0B0', edgecolor='white', linewidth=1
)
bars_new = ax.bar(
    x + width / 2, new_vals, width,
    color='#1F77B4', edgecolor='white', linewidth=1
)

# Direct bar labels
for bar, val in zip(bars_old, control_vals):
    ax.text(
        bar.get_x() + bar.get_width() / 2, 0.10, 'Old',
        ha='center', va='bottom', fontsize=9, color='#444444'
    )
    ax.annotate(
        f'{val:.2f}%',
        xy=(bar.get_x() + bar.get_width() / 2, val),
        xytext=(0, 4), textcoords='offset points',
        ha='center', va='bottom', fontsize=10, color='#666666'
    )

for bar, val in zip(bars_new, new_vals):
    ax.text(
        bar.get_x() + bar.get_width() / 2, 0.10, 'New',
        ha='center', va='bottom', fontsize=9, color='white', fontweight='bold'
    )
    ax.annotate(
        f'{val:.2f}%',
        xy=(bar.get_x() + bar.get_width() / 2, val),
        xytext=(0, 4), textcoords='offset points',
        ha='center', va='bottom', fontsize=11, color='#1F77B4', fontweight='bold'
    )

ax.set_xticks(x)
ax.set_xticklabels(periods, fontsize=11)
ax.set_ylabel('Mobile conversion (%)', fontsize=11)
ax.set_ylim(0, 2.9)
ax.set_yticks(np.arange(0, 3.1, 0.5))
ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.1f}%'))

ax.grid(axis='y', color='#DDDDDD', linewidth=0.8, alpha=0.7)
ax.set_axisbelow(True)

for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)
for spine in ['left', 'bottom']:
    ax.spines[spine].set_color('#888888')

ax.set_title(
    'The payment fix restored mobile conversion;\n'
    'two post-fix days are too few to justify a full rollout.',
    fontsize=15, fontweight='bold', loc='left', pad=15
)

note = (
    f"Mobile = {mobile_share:.0f}% of sessions.\n"
    f"Post-fix (2 days): new checkout {post_diff:+.1f}% orders vs old.\n"
    f"Full period: {overall_diff:+.1f}% (pre-fix payment bug)."
)
ax.text(
    0.99, 0.98, note,
    transform=ax.transAxes, ha='right', va='top',
    fontsize=9, color='#555555', linespacing=1.4,
    bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='#DDDDDD', alpha=0.95)
)

fig.tight_layout()
