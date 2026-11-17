import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Read data
df = pd.read_csv('data.csv')

# Totals
total_apps = df['applications'].sum()
total_value = df['funded_value_musd'].sum()

# Broker shares
broker_df = df[df['channel'] == 'Broker']
broker_apps = broker_df['applications'].sum()
broker_value = broker_df['funded_value_musd'].sum()
broker_app_share = broker_apps / total_apps * 100
broker_value_share = broker_value / total_value * 100

# Weighted acquisition cost per funded loan by channel
df['total_cost'] = df['acquisition_cost_per_loan_usd'] * df['funded_loans']
cost_agg = df.groupby('channel').agg(
    total_cost=('total_cost', 'sum'),
    total_loans=('funded_loans', 'sum')
)
cost_per_loan = cost_agg['total_cost'] / cost_agg['total_loans']

# Colours
highlight = '#C0392B'
grey = '#BDBDBD'
darkgrey = '#4D4D4D'

# Figure
fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(10, 6),
    gridspec_kw={'width_ratios': [0.8, 1.4], 'wspace': 0.55}
)

# Left panel: Broker share of applications vs funded value
left_labels = ['Applications', 'Funded value']
left_vals = [broker_app_share, broker_value_share]
left_colors = [grey, highlight]
bars = ax1.bar(left_labels, left_vals, color=left_colors, width=0.6)

ax1.set_ylim(0, 40)
ax1.set_yticks(np.arange(0, 41, 10))
ax1.set_yticklabels([f'{x}%' for x in range(0, 41, 10)], fontsize=9)
ax1.set_ylabel('Share of total (%)', fontsize=10)
ax1.set_title('Broker share of total', fontsize=11, loc='left', fontweight='bold')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.tick_params(axis='x', labelsize=10)

for bar, val in zip(bars, left_vals):
    ax1.text(
        bar.get_x() + bar.get_width() / 2,
        val + 1,
        f'{val:.0f}%',
        ha='center', va='bottom',
        fontsize=12, fontweight='bold', color=darkgrey
    )

# Right panel: acquisition cost per funded loan
cost_sorted = cost_per_loan.sort_values(ascending=True)
channels = cost_sorted.index.tolist()
cost_vals = cost_sorted.values
y_pos = np.arange(len(channels))
right_colors = [highlight if ch == 'Broker' else grey for ch in channels]

bars2 = ax2.barh(y_pos, cost_vals, color=right_colors, height=0.6)
ax2.set_yticks(y_pos)
ax2.set_yticklabels(channels, fontsize=10)
ax2.set_xlim(0, 1600)
ax2.set_xticks([0, 400, 800, 1200, 1600])
ax2.set_xticklabels(['$0', '$400', '$800', '$1,200', '$1,600'], fontsize=9)
ax2.set_xlabel('Acquisition cost per funded loan (US$)', fontsize=10)
ax2.set_title('Cost per funded loan', fontsize=11, loc='left', fontweight='bold')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.grid(axis='x', color='#E0E0E0', linewidth=0.8)
ax2.set_axisbelow(True)

for bar, val in zip(bars2, cost_vals):
    ax2.text(
        val + 20,
        bar.get_y() + bar.get_height() / 2,
        f'${val:,.0f}',
        va='center', ha='left',
        fontsize=10, color=darkgrey
    )

# Main title and subtitle
fig.suptitle(
    'Broker loans bring 32% of funded value but cost $1,446 each—4.2x online',
    fontsize=14, fontweight='bold', x=0.5, y=0.98
)
fig.text(
    0.5, 0.915,
    'Broker: 17% of applications, $58k average loan vs $9k–$20k elsewhere',
    ha='center', fontsize=10, color=darkgrey
)

# Caveat
fig.text(
    0.5, 0.03,
    'Caveat: broker default rate (2.1%) is a projection, not observed (same for partner app).',
    ha='center', fontsize=8.5, color='#666666', style='italic'
)

plt.subplots_adjust(top=0.82, bottom=0.15, left=0.08, right=0.95)
