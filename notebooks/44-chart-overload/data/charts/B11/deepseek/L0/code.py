import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv('data.csv')
df['month'] = pd.to_datetime(df['month'], format='%Y-%m')

month_order = sorted(df['month'].unique())
month_labels = [pd.Timestamp(m).strftime('%b') for m in month_order]

channels = ['Branch', 'Online', 'Broker', 'Partner app']
colors = {
    'Branch': '#1f77b4',
    'Online': '#ff7f0e',
    'Broker': '#2ca02c',
    'Partner app': '#d62728'
}

app_pivot = (
    df.pivot_table(index='month', columns='channel', values='applications', aggfunc='sum')
      .reindex(index=month_order, columns=channels)
)

value_pivot = (
    df.pivot_table(index='month', columns='channel', values='funded_value_musd', aggfunc='sum')
      .reindex(index=month_order, columns=channels)
      .fillna(0)
)

fig, axes = plt.subplots(2, 2, figsize=(10, 6))

# Applications by channel over time
ax = axes[0, 0]
for ch in channels:
    ax.plot(
        range(len(month_order)),
        app_pivot[ch].values,
        marker='o',
        markersize=3,
        linewidth=1.5,
        color=colors[ch],
        label=ch
    )
ax.set_title('Applications by channel', fontsize=10)
ax.set_xticks(range(len(month_order)))
ax.set_xticklabels(month_labels, fontsize=8)
ax.set_ylabel('Applications')
ax.grid(alpha=0.3)
ax.legend(fontsize=7, loc='upper left', ncol=2)

# Funded value by channel over time
ax = axes[0, 1]
bottom = np.zeros(len(month_order))
for ch in channels:
    vals = value_pivot[ch].values
    ax.bar(
        range(len(month_order)),
        vals,
        bottom=bottom,
        color=colors[ch],
        width=0.75,
        label=ch
    )
    bottom += vals
ax.set_title('Funded value by channel', fontsize=10)
ax.set_xticks(range(len(month_order)))
ax.set_xticklabels(month_labels, fontsize=8)
ax.set_ylabel('$ millions')
ax.grid(axis='y', alpha=0.3)

# Channel-level weighted averages
stats_rows = []
for ch in channels:
    g = df[df['channel'] == ch]
    w = g['funded_loans']
    stats_rows.append({
        'channel': ch,
        'acq_cost': np.average(g['acquisition_cost_per_loan_usd'], weights=w),
        'avg_loan_k': np.average(g['avg_loan_k'], weights=w),
        'default_rate': np.average(g['default_rate_12m_pct'], weights=w),
        'basis': g['default_rate_basis'].iloc[0]
    })

stats = pd.DataFrame(stats_rows).set_index('channel').reindex(channels)
x = np.arange(len(channels))

# Acquisition cost per funded loan
ax = axes[1, 0]
acq = stats['acq_cost'].values
ax.bar(x, acq, color=[colors[ch] for ch in channels])
ax.set_xticks(x)
ax.set_xticklabels(channels, fontsize=8)
ax.set_ylabel('USD')
ax.set_title('Acquisition cost per funded loan', fontsize=10)
for i, v in enumerate(acq):
    ax.text(i, v, f'${v:,.0f}', ha='center', va='bottom', fontsize=8)
ax.grid(axis='y', alpha=0.3)

# Average loan size and default rate
ax = axes[1, 1]
loan = stats['avg_loan_k'].values
dr = stats['default_rate'].values
basis = stats['basis'].values

ax.bar(x, loan, color=[colors[ch] for ch in channels])
ax.set_xticks(x)
ax.set_xticklabels(channels, fontsize=8)
ax.set_ylabel('$ thousands')
ax.set_title('Avg loan size and 12m default rate (* projected)', fontsize=9)

for i, (v, d, b) in enumerate(zip(loan, dr, basis)):
    suffix = '*' if b == 'projected' else ''
    ax.text(i, v, f'${v:.1f}k\n{d:.1f}%{suffix}', ha='center', va='bottom', fontsize=7)

ax.grid(axis='y', alpha=0.3)

fig.suptitle('Loan channel performance, Jan–Sep 2026', fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.96])
