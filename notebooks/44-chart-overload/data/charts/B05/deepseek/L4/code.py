import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv('data.csv')
df['actual_hours'] = pd.to_numeric(df['actual_hours'], errors='coerce')
df['over48'] = df['actual_hours'] > 48

summ = (df.groupby('courier')
          .agg(n=('actual_hours', 'size'),
               over48=('over48', 'sum'),
               median_h=('actual_hours', 'median'))
          .reindex(['Swiftline', 'Northway', 'ParcelPro']))
summ['pct'] = summ['over48'] / summ['n'] * 100

RED, GREY, DARK, MID = '#B0332B', '#CBCBCB', '#1F1F1F', '#5A5A5A'

fig, ax = plt.subplots(figsize=(10, 6))
plt.subplots_adjust(left=0.075, right=0.985, top=0.79, bottom=0.25)

x = np.arange(len(summ))
ax.bar(x, summ['pct'].values, width=0.55, color=[RED, GREY, GREY], zorder=3)

ax.set_ylim(0, 17.2)
ax.set_yticks([0, 4, 8, 12, 16])
ax.set_yticklabels(['0%', '4%', '8%', '12%', '16%'])
ax.tick_params(axis='y', colors=MID, labelsize=10, length=0)
ax.set_ylabel('% of deliveries over 48 hours', fontsize=10.5, color=MID, labelpad=10)

for s in ('top', 'right', 'left'):
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color('#B5B5B5')
ax.grid(axis='y', color='#ECECEC', linewidth=0.9, zorder=0)
ax.set_axisbelow(True)

ax.set_xticks(x)
ax.set_xticklabels(summ.index, fontsize=13, color=DARK)
ax.tick_params(axis='x', length=0, pad=5)

# typical delivery time, kept grey so it stays context
for xi, m in zip(x, summ['median_h'].values):
    ax.text(xi, -0.115, f"median {m:.1f} h", transform=ax.get_xaxis_transform(),
            ha='center', va='top', fontsize=9, color='#8C8C8C')

# Swiftline callout (the message)
sw = summ.loc['Swiftline']
ax.text(0, sw['pct'] + 0.35, f"{sw['pct']:.1f}%", ha='center', va='bottom',
        fontsize=18, fontweight='bold', color=RED, zorder=4)
ax.text(0, sw['pct'] + 1.95, f"{int(sw['over48'])} of {int(sw['n'])} deliveries",
        ha='center', va='bottom', fontsize=10.5, color=RED, zorder=4)

# small grey labels for the safe couriers
for xi, name in zip(x[1:], summ.index[1:]):
    v = summ.loc[name, 'pct']
    ax.text(xi, v + 0.35, f"{v:.1f}%", ha='center', va='bottom',
            fontsize=12.5, color=MID, zorder=4)

fig.text(0.035, 0.965, "Contract Northway or ParcelPro for refrigerated deliveries:",
         fontsize=15, fontweight='bold', color=DARK, ha='left', va='top')
fig.text(0.035, 0.900, "Swiftline breaks the 48-hour cold-chain limit about six times as often",
         fontsize=15, fontweight='bold', color=DARK, ha='left', va='top')
fig.text(0.035, 0.835, "Share of each courier's deliveries taking more than 48 hours from dispatch, Aug–Oct 2026",
         fontsize=10.5, color=MID, ha='left', va='top')

fig.text(0.035, 0.085,
         "Cold packs keep these medicines safe for 48 hours.  Prices (within $0.50) and customer ratings (4.2–4.3) are alike for all three,\n"
         "so cold-chain reliability is the deciding difference.  ParcelPro's rate rests on 40 deliveries (1 over 48 h); the others have 90 each.",
         fontsize=8.8, color=MID, ha='left', va='top', linespacing=1.6)
