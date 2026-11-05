import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('data.csv')
df['month'] = pd.to_datetime(df['month'])

# Baseline (April-May) and post-restriction (June-September) use per district
baseline = df[df['month'].dt.month.isin([4, 5])].groupby('district')['litres_per_household_day'].mean()
post = df[df['month'].dt.month.isin([6, 7, 8, 9])].groupby('district')['litres_per_household_day'].mean()
raw_cut = (baseline - post) / baseline * 100

# Adjust Hillcrest for July meter replacement: new meters read ~8% higher
hill = df[(df['district'] == 'Hillcrest') & (df['month'].dt.month.isin([6, 7, 8, 9]))].copy()
hill['adj_lphd'] = hill['litres_per_household_day']
mask = hill['month'].dt.month >= 7
hill.loc[mask, 'adj_lphd'] = hill.loc[mask, 'litres_per_household_day'] / 1.08
hill_adj_post = hill['adj_lphd'].mean()
hill_adj_cut = (baseline['Hillcrest'] - hill_adj_post) / baseline['Hillcrest'] * 100

# Plot Hillcrest adjusted cut, raw cuts for other districts
cuts = raw_cut.copy()
cuts['Hillcrest'] = hill_adj_cut
cuts_sorted = cuts.sort_values(ascending=True)
districts = cuts_sorted.index.tolist()
plot_cuts = cuts_sorted.values

highlight = '#C0392B'
context = '#BDBDBD'
colors = [highlight if d == 'Hillcrest' else context for d in districts]

fig, ax = plt.subplots(figsize=(10, 6))
fig.subplots_adjust(left=0.18, right=0.95, top=0.78, bottom=0.20)

y = np.arange(len(districts))
ax.barh(y, plot_cuts, color=colors, height=0.62)

ax.set_yticks(y)
ax.set_yticklabels(districts, fontsize=10)
ax.invert_yaxis()

ax.set_xlim(0, 30)
ax.set_xticks(np.arange(0, 31, 5))
ax.set_xlabel('Reduction in use per household, Jun–Sep vs Apr–May (%)', fontsize=10)
ax.xaxis.grid(True, linestyle=':', alpha=0.5)
ax.set_axisbelow(True)
for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)

# Target line
ax.axvline(20, color='#333333', linestyle='--', linewidth=1.1, alpha=0.8)
ax.text(20.3, 0.98, '20% target', transform=ax.get_xaxis_transform(),
        ha='left', va='top', fontsize=9, color='#333333')

# Direct label for Hillcrest
raw_hill = raw_cut['Hillcrest']
adj_hill = cuts['Hillcrest']
ax.text(adj_hill + 0.4, 0, f'≈{adj_hill:.0f}% adjusted\n(raw {raw_hill:.0f}%)',
        va='center', ha='left', fontsize=9.5, color=highlight, fontweight='bold')

# Title states the key message
title = ("Hillcrest is the clear enforcement priority: after meter adjustment it cut use only ~9%,\n"
         "far short of the 20% target and the 17–27% cuts in the other seven districts.")
fig.text(0.01, 0.96, title, fontsize=13, fontweight='bold', ha='left', va='top')

# Caveat and actual-use note
note = ("Hillcrest raw cut 4%; adjusted ≈9% for July meter replacement (new meters read ~8% high). "
        "Its Jun–Sep use was 414 L/household/day vs 342 target.")
fig.text(0.01, 0.03, note, fontsize=8.5, color='dimgray', ha='left', va='bottom')
