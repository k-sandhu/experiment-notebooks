import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

df = pd.read_csv('data.csv')
df['date'] = pd.to_datetime(df['month'] + '-01')

price_date = pd.Timestamp('2026-04-01')
cutoff = pd.Timestamp('2026-09-01')  # exclude partial September

# Family plan data
family = df[df['plan'] == 'Family'].sort_values('date').copy()
family = family[family['date'] < cutoff]
family['weekly_revenue'] = family['price_per_week_usd'] * family['active_subscribers']

# Cancellation rates
cancel = df.pivot_table(
    index='date', columns='plan', values='cancellation_rate_pct'
).sort_index()
cancel = cancel[cancel.index < cutoff]

family_rate = cancel['Family']
other_rate = cancel.drop(columns='Family').mean(axis=1)

pre_rate = family_rate[family_rate.index < price_date].mean()
post_rate = family_rate[family_rate.index >= price_date].mean()

# Revenue
pre_rev = family.loc[family['date'] < price_date, 'weekly_revenue'].mean() / 1e6
aug = family[family['date'] == pd.Timestamp('2026-08-01')].iloc[0]
aug_rev = aug['weekly_revenue'] / 1e6

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6))

# Panel 1: cancellation rate
ax1.plot(
    family_rate.index, family_rate.values,
    marker='o', color='#c0392b', linewidth=2.5, label='Family'
)
ax1.plot(
    other_rate.index, other_rate.values,
    marker='o', color='#7f8c8d', linewidth=1.8, linestyle='--',
    label='Other plans (avg)'
)
ax1.axvline(price_date, color='black', linestyle='--', linewidth=1.2)
ax1.text(
    price_date, 0.95, ' Family price\n $79→$89',
    transform=ax1.get_xaxis_transform(), ha='center', va='top',
    fontsize=8.5, backgroundcolor='white'
)
ax1.hlines(
    pre_rate, family_rate.index.min(), price_date,
    colors='#c0392b', linestyles=':', linewidth=1.2
)
ax1.hlines(
    post_rate, price_date, family_rate.index.max(),
    colors='#c0392b', linestyles=':', linewidth=1.2
)
ax1.text(
    family_rate.index.min(), pre_rate + 0.18,
    f'Pre avg {pre_rate:.1f}%', color='#c0392b', fontsize=8, va='bottom'
)
ax1.text(
    price_date, post_rate + 0.18,
    f'Post avg {post_rate:.1f}%', color='#c0392b', fontsize=8, va='bottom'
)
ax1.set_title(
    'Family cancellations doubled after price rise',
    loc='left', fontsize=11, fontweight='bold'
)
ax1.set_ylabel('Monthly cancellation rate (%)')
ax1.legend(frameon=False, loc='upper left', fontsize=8.5)
ax1.grid(axis='y', alpha=0.25)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%Y'))
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax1.text(
    0.99, 0.02, 'Sep 2026 excluded\n(partial month)',
    transform=ax1.transAxes, ha='right', va='bottom',
    fontsize=8, color='#555'
)

# Panel 2: weekly revenue
ax2.plot(
    family['date'], family['weekly_revenue'] / 1e6,
    marker='o', color='#c0392b', linewidth=2.5,
    label='Family weekly revenue'
)
ax2.axhline(
    pre_rev, color='gray', linestyle=':', linewidth=1.2,
    label=f'Pre-rise avg (${pre_rev:.2f}M)'
)
ax2.axvline(price_date, color='black', linestyle='--', linewidth=1.2)
ax2.text(
    price_date, 0.95, ' Family price\n $79→$89',
    transform=ax2.get_xaxis_transform(), ha='center', va='top',
    fontsize=8.5, backgroundcolor='white'
)
ax2.set_ylim(1.00, 1.32)
ax2.annotate(
    f'Aug: ${aug_rev:.2f}M\nbelow pre-rise',
    xy=(aug['date'], aug_rev),
    xytext=(pd.Timestamp('2026-05-15'), 1.01),
    textcoords='data', ha='left', va='bottom',
    fontsize=8.5, color='#c0392b',
    arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1)
)
ax2.set_title(
    'Revenue gain faded as subscribers cancelled',
    loc='left', fontsize=11, fontweight='bold'
)
ax2.set_ylabel('Weekly revenue from active subscribers ($M)')
ax2.legend(frameon=False, loc='upper right', fontsize=8.5)
ax2.grid(axis='y', alpha=0.25)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%Y'))
ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax2.text(
    0.99, 0.02, 'Sep 2026 excluded\n(partial month)',
    transform=ax2.transAxes, ha='right', va='bottom',
    fontsize=8, color='#555'
)

fig.suptitle(
    'Family plan: April price rise hurt retention; August revenue fell below pre-rise level',
    fontsize=12.5, fontweight='bold', x=0.01, ha='left'
)
plt.tight_layout(rect=[0, 0, 1, 0.94])
