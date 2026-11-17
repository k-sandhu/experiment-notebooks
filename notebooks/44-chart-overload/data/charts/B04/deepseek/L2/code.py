import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read data
df = pd.read_csv('data.csv')

# Summarize forecast variance by department
dept = df.groupby('department', as_index=False)['variance_k'].sum()
dept['variance_m'] = dept['variance_k'] / 1000
dept = dept.sort_values('variance_m', ascending=True).reset_index(drop=True)

fig, ax = plt.subplots(figsize=(10, 6))

colors = ['#D55E00' if d == 'Transit' else '#BEBEBE' for d in dept['department']]
ax.barh(dept['department'], dept['variance_m'], color=colors, height=0.65)

ax.axvline(0, color='#333333', linewidth=1)

# Direct labels for the three largest overspending departments
for i, row in dept.iterrows():
    if row['department'] in ['Transit', 'Roads', 'Police']:
        v = row['variance_m']
        ax.text(
            v + 0.08, i, f"{v:+.1f}m",
            va='center', ha='left', fontsize=11,
            color='#D55E00' if row['department'] == 'Transit' else '#555555',
            fontweight='bold' if row['department'] == 'Transit' else 'normal'
        )

ax.set_title(
    "Review Transit first: its $3.1m forecast overspend\nis 65% of the city's $4.8m overrun",
    fontsize=15, fontweight='bold', loc='left', pad=12
)

ax.set_xlabel("Forecast variance vs budget ($ millions; positive = overspend)", fontsize=11)
ax.set_xlim(-0.6, 3.6)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.tick_params(axis='y', length=0, labelsize=11)
ax.tick_params(axis='x', labelsize=10)
ax.grid(axis='x', color='#E0E0E0', linewidth=0.8)
ax.set_axisbelow(True)

fig.text(
    0.99, 0.02,
    "Caveat: Roads forecast assumes average snow clearing; a harsh winter could add up to $1.5m to Roads' overspend.",
    ha='right', va='bottom', fontsize=9, color='#555555'
)

fig.subplots_adjust(left=0.16, right=0.96, top=0.84, bottom=0.18)
