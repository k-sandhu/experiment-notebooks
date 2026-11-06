import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Read data
df = pd.read_csv('data.csv')

# Total acquisition cost by row
df['acq_cost_total'] = df['acquisition_cost_per_loan_usd'] * df['funded_loans']

# Aggregate by channel
agg = (
    df.groupby('channel', as_index=False)
      .agg(
          applications=('applications', 'sum'),
          funded_loans=('funded_loans', 'sum'),
          funded_value_musd=('funded_value_musd', 'sum'),
          acq_cost_total=('acq_cost_total', 'sum')
      )
)

# Metrics
agg['cost_per_musd'] = agg['acq_cost_total'] / agg['funded_value_musd']
agg['value_share'] = agg['funded_value_musd'] / agg['funded_value_musd'].sum()
agg['cost_share'] = agg['acq_cost_total'] / agg['acq_cost_total'].sum()
agg['avg_loan_k'] = agg['funded_value_musd'] * 1000 / agg['funded_loans']

overall_cost_per_musd = agg['acq_cost_total'].sum() / agg['funded_value_musd'].sum()

# Sort for bar chart: highest cost per $1M funded at top
agg = agg.sort_values('cost_per_musd', ascending=True).reset_index(drop=True)

# Figure
fig, ax = plt.subplots(figsize=(10, 6))

colors = ['#d95f02' if c == 'Broker' else '#b0b0b0' for c in agg['channel']]
bars = ax.barh(
    agg['channel'],
    agg['cost_per_musd'],
    color=colors,
    height=0.6,
    edgecolor='white'
)

# Overall average line
ax.axvline(
    overall_cost_per_musd,
    color='#333333',
    linestyle='--',
    linewidth=1.2,
    zorder=1
)
ax.text(
    overall_cost_per_musd * 1.01,
    len(agg) - 0.45,
    f'Overall average\n${overall_cost_per_musd / 1000:.1f}k',
    ha='left',
    va='top',
    fontsize=9,
    color='#333333'
)

# Value labels
for i, row in agg.iterrows():
    ax.text(
        row['cost_per_musd'] + overall_cost_per_musd * 0.02,
        i,
        f"${row['cost_per_musd'] / 1000:.0f}k",
        va='center',
        ha='left',
        fontsize=10,
        fontweight='bold' if row['channel'] == 'Broker' else 'normal',
        color='#d95f02' if row['channel'] == 'Broker' else '#333333'
    )

# Key broker context
broker_row = agg[agg['channel'] == 'Broker'].iloc[0]
ax.text(
    0.98, 0.03,
    f"Broker = {broker_row['cost_share']:.0%} of acquisition cost\n"
    f"= {broker_row['value_share']:.0%} of funded value\n"
    f"Avg loan ${broker_row['avg_loan_k']:.0f}k",
    transform=ax.transAxes,
    ha='right',
    va='bottom',
    fontsize=9,
    bbox=dict(
        boxstyle='round,pad=0.4',
        facecolor='white',
        edgecolor='#d95f02',
        alpha=0.95
    )
)

# Labels and formatting
ax.set_xlabel('Acquisition cost per $1M of funded loans (USD)')
ax.set_title(
    'Broker is not the costliest channel per dollar funded',
    loc='left',
    fontsize=14,
    fontweight='bold',
    pad=20
)
ax.text(
    0, 1.01,
    'Costs include marketing, commission and processing per funded loan. Dashed line = overall average.',
    transform=ax.transAxes,
    fontsize=9,
    color='#555555'
)

ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f'${x / 1000:.0f}k'))
ax.set_xlim(0, max(agg['cost_per_musd']) * 1.35)
ax.grid(axis='x', linestyle=':', alpha=0.5)
ax.set_axisbelow(True)

for spine in ['top', 'right', 'left']:
    ax.spines[spine].set_visible(False)

ax.tick_params(axis='y', length=0, labelsize=11)
ax.tick_params(axis='x', labelsize=9)

plt.tight_layout()
