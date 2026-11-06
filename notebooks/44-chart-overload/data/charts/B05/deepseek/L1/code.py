import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('data.csv')
df['over48'] = df['actual_hours'] > 48

summary = (
    df.groupby('courier')
      .agg(n=('delivery_id', 'size'),
           over48=('over48', 'sum'),
           median_hours=('actual_hours', 'median'))
      .reset_index()
)
summary['pct'] = 100 * summary['over48'] / summary['n']
summary = summary.sort_values('pct', ascending=True)  # highest bar at top for barh

color_map = {'Northway': '#4C72B0', 'ParcelPro': '#55A868', 'Swiftline': '#C44E52'}
colors = [color_map[c] for c in summary['courier']]

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(summary['courier'], summary['pct'], color=colors, height=0.55)

ax.set_xlabel('Deliveries exceeding 48 hours (%)', fontsize=12)
ax.set_xlim(0, max(summary['pct']) * 1.35)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.grid(axis='x', alpha=0.25)
ax.set_axisbelow(True)
ax.tick_params(axis='y', labelsize=12)
ax.tick_params(axis='x', labelsize=11)

for bar, (_, row) in zip(bars, summary.iterrows()):
    x = bar.get_width()
    ax.text(
        x + max(summary['pct']) * 0.02,
        bar.get_y() + bar.get_height() / 2,
        f"{row['pct']:.1f}%  ({int(row['over48'])}/{int(row['n'])})",
        va='center', ha='left', fontsize=11, fontweight='bold'
    )

ax.set_title(
    'Refrigerated medicine: risk of a cold-chain breach',
    fontsize=15, fontweight='bold', pad=18
)
ax.text(
    0.0, 1.02,
    'Share of deliveries taking longer than the 48-hour cold-pack limit',
    transform=ax.transAxes, fontsize=11, color='#444444',
    ha='left', va='bottom'
)

swift_med = summary.loc[summary['courier'] == 'Swiftline', 'median_hours'].iloc[0]
ax.text(
    0.62, 0.28,
    f"Swiftline is typically fastest\n(median {swift_med:.1f}h), but has\n~7× the >48h risk.",
    transform=ax.transAxes, fontsize=10.5, ha='left', va='center',
    bbox=dict(boxstyle='round,pad=0.5', fc='#FFF8E1', ec='#D9A400', alpha=0.95)
)

fig.text(
    0.5, 0.02,
    'Prices and customer ratings are similar; each courier damaged one parcel. '
    'ParcelPro has only 40 deliveries, so its estimate is less certain.',
    ha='center', fontsize=9, color='#555555'
)

plt.tight_layout(rect=[0, 0.05, 1, 0.93])
