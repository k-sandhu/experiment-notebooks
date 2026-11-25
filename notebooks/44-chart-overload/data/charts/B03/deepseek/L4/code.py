import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

# Read and prepare data
df = pd.read_csv('data.csv')
df['date'] = pd.to_datetime(df['date'])

mobile = df[df['device'] == 'mobile'].copy()
daily = (
    mobile.groupby(['date', 'variant'])
    .agg(sessions=('sessions', 'sum'), orders=('orders', 'sum'))
    .reset_index()
)
daily['conversion_pct'] = 100 * daily['orders'] / daily['sessions']
conv = daily.pivot(index='date', columns='variant', values='conversion_pct').sort_index()

fix_date = pd.Timestamp('2026-09-26')
last_date = conv.index.max()
post_days = int((conv.index >= fix_date).sum())

orders_by_variant = df.groupby('variant')['orders'].sum()
order_change = (
    100 * (orders_by_variant['new_checkout'] - orders_by_variant['control'])
    / orders_by_variant['control']
)

mobile_share = (
    100 * df.loc[df['device'] == 'mobile', 'sessions'].sum()
    / df['sessions'].sum()
)

# Figure
fig, ax = plt.subplots(figsize=(10, 6))

# Shade the short post-fix window
ax.axvspan(
    fix_date,
    last_date + pd.Timedelta(days=1),
    color='#EAF2FA',
    zorder=0
)
ax.axvline(
    fix_date,
    color='#555555',
    linestyle='--',
    linewidth=1.2,
    zorder=1
)

# Lines
ax.plot(
    conv.index, conv['control'],
    color='#9E9E9E', linewidth=2.5,
    marker='o', markersize=4, zorder=2
)
ax.plot(
    conv.index, conv['new_checkout'],
    color='#1F77B4', linewidth=3.0,
    marker='o', markersize=5, zorder=3
)

# Direct labels at the right end
last_old = conv['control'].iloc[-1]
last_new = conv['new_checkout'].iloc[-1]

ax.annotate(
    'Old checkout',
    xy=(last_date, last_old),
    xytext=(8, -14),
    textcoords='offset points',
    color='#666666', fontsize=10, fontweight='bold', va='center'
)
ax.annotate(
    'New checkout',
    xy=(last_date, last_new),
    xytext=(8, 8),
    textcoords='offset points',
    color='#1F77B4', fontsize=10, fontweight='bold', va='center'
)

# Annotations
ax.text(
    fix_date + pd.Timedelta(days=0.4), 2.82,
    'Payment bug fixed\nSep 26',
    fontsize=10, color='#333333',
    ha='left', va='top', linespacing=1.15
)
ax.text(
    fix_date + pd.Timedelta(days=0.4), 1.05,
    f'Only {post_days} days\npost-fix',
    fontsize=10, color='#1F77B4',
    ha='left', va='bottom', fontweight='bold', linespacing=1.15
)

# Title
ax.set_title(
    "Don't roll out yet: mobile conversion only returned to near parity after the Sep 26 fix,\n"
    "with just two days of data",
    fontsize=15, fontweight='bold', loc='left', pad=15
)

# Axes
ax.set_ylabel('Mobile conversion (%)', fontsize=11)
ax.set_ylim(0, 3.0)
ax.set_yticks(np.arange(0, 3.1, 0.5))
ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.1f}%'))

ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax.set_xlim(
    conv.index.min() - pd.Timedelta(days=0.5),
    last_date + pd.Timedelta(days=2.5)
)

ax.grid(axis='y', color='#DDDDDD', linewidth=0.8, alpha=0.8)
ax.set_axisbelow(True)

for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)
for spine in ['left', 'bottom']:
    ax.spines[spine].set_color('#888888')

# Context note
note = (
    f"Mobile is {mobile_share:.0f}% of sessions.  "
    f"Full-period orders: old {orders_by_variant['control']:,}; "
    f"new {orders_by_variant['new_checkout']:,} ({order_change:+.1f}%)."
)
ax.text(
    0.01, 0.02, note,
    transform=ax.transAxes, fontsize=9, color='#555555',
    ha='left', va='bottom'
)

fig.tight_layout()
