import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read data
df = pd.read_csv('data.csv')

# Summarize forecast variance by department
dept = df.groupby('department', as_index=False)['variance_k'].sum()
dept['variance_m'] = dept['variance_k'] / 1000

# Key values for the message
transit_m = dept.loc[dept['department'] == 'Transit', 'variance_m'].iloc[0]
city_total_m = df['variance_k'].sum() / 1000
transit_share = transit_m / city_total_m * 100
transit_overtime_m = df[(df['department'] == 'Transit') &
                        (df['budget_line'] == 'Overtime')]['variance_k'].sum() / 1000

# Top three overspending departments, plus all others netted together
top3 = dept.sort_values('variance_m', ascending=False).head(3).copy()
other_net = dept.loc[~dept['department'].isin(top3['department']), 'variance_m'].sum()

plot_df = pd.concat([
    top3,
    pd.DataFrame({
        'department': ['All other departments\n(net)'],
        'variance_m': [other_net]
    })
], ignore_index=True)

# Sort ascending so the largest bar appears at the top in a horizontal chart
plot_df = plot_df.sort_values('variance_m', ascending=True).reset_index(drop=True)

fig, ax = plt.subplots(figsize=(10, 6))

colors = ['#D55E00' if d == 'Transit' else '#BDBDBD' for d in plot_df['department']]
ax.barh(plot_df['department'], plot_df['variance_m'], color=colors, height=0.65)

# Zero line
ax.axvline(0, color='#333333', linewidth=1)

# Direct labels only where they support the decision
for i, row in plot_df.iterrows():
    d = row['department']
    v = row['variance_m']

    if d == 'Transit':
        ax.text(
            v + 0.06, i,
            f"${v:.1f}m ({transit_share:.0f}%)",
            va='center', ha='left',
            fontsize=10.5, color='#D55E00', fontweight='bold'
        )
        ax.text(
            v / 2, i,
            f"Overtime +${transit_overtime_m:.1f}m",
            va='center', ha='center',
            fontsize=10, color='white', fontweight='bold'
        )
    elif d in ['Roads', 'Police']:
        ax.text(
            v + 0.06, i,
            f"${v:.1f}m",
            va='center', ha='left',
            fontsize=10.5, color='#555555'
        )

# Title states the recommendation and the core reason
ax.set_title(
    f"Put Transit under mid-year review: its ${transit_m:.1f}m forecast overspend\n"
    f"is {transit_share:.0f}% of the city's ${city_total_m:.1f}m net overrun",
    fontsize=15, fontweight='bold', loc='left', pad=12
)

ax.set_xlabel(
    "Forecast year-end variance vs budget ($ millions; positive = overspend)",
    fontsize=11
)
ax.set_xlim(0, 4.0)

# Styling
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.tick_params(axis='y', length=0, labelsize=11)
ax.tick_params(axis='x', labelsize=10)
ax.grid(axis='x', color='#E0E0E0', linewidth=0.8)
ax.set_axisbelow(True)

# Emphasise Transit on the y-axis too
for label in ax.get_yticklabels():
    if label.get_text() == 'Transit':
        label.set_fontweight('bold')
        label.set_color('#D55E00')

# Brief caveat
fig.text(
    0.01, 0.02,
    "Roads assumes average snow clearing; a harsh winter (+$1.5m) would still leave it below Transit.",
    ha='left', va='bottom', fontsize=9, color='#555555'
)

fig.subplots_adjust(left=0.20, right=0.96, top=0.82, bottom=0.18)
