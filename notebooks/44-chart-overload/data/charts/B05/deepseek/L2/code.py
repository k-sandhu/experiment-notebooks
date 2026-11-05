import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv('data.csv')
df['actual_hours'] = pd.to_numeric(df['actual_hours'], errors='coerce')
df['over48'] = df['actual_hours'] > 48

summary = (
    df.groupby('courier')
      .agg(n=('actual_hours', 'size'), over48=('over48', 'sum'))
      .reset_index()
)
summary['pct_over48'] = summary['over48'] / summary['n'] * 100
summary = summary.sort_values('pct_over48', ascending=False).reset_index(drop=True)

couriers = summary['courier'].tolist()
pct = summary['pct_over48'].to_numpy()
counts = summary['over48'].to_numpy()
ns = summary['n'].to_numpy()

colors = ['#C0392B' if c == 'Swiftline' else '#BDBDBD' for c in couriers]

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(couriers, pct, color=colors, width=0.62, edgecolor='none', zorder=3)

fig.suptitle(
    "For refrigerated medicines, choose Northway or ParcelPro: Swiftline breaches the 48-hour cold-chain limit far more often",
    x=0.02, y=0.98, ha='left', fontsize=13.8, fontweight='bold'
)
ax.set_title(
    "Share of deliveries taking more than 48 hours from dispatch to delivery, by courier",
    loc='left', fontsize=10.5, color='#555555', pad=12
)

ax.set_ylabel("% of deliveries over 48 hours", fontsize=11)
ymax = np.ceil(max(pct) * 1.35 / 2) * 2
ax.set_ylim(0, ymax)
ax.set_yticks(np.arange(0, ymax + 1, 2))
ax.set_yticklabels([f"{int(t)}%" for t in ax.get_yticks()])
ax.grid(axis='y', color='#E5E5E5', linewidth=0.8, zorder=0)
ax.set_axisbelow(True)

for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)
ax.spines['left'].set_color('#999999')
ax.spines['bottom'].set_color('#999999')
ax.tick_params(axis='x', labelsize=12)
ax.tick_params(axis='y', labelsize=10, colors='#555555')

for bar, c, v, o, n in zip(bars, couriers, pct, counts, ns):
    highlight = (c == 'Swiftline')
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + max(pct) * 0.035,
        f"{v:.1f}%\n({o} of {n})",
        ha='center', va='bottom',
        fontsize=11.5 if highlight else 10,
        color='#C0392B' if highlight else '#444444',
        fontweight='bold' if highlight else 'normal'
    )

fig.text(
    0.02, 0.02,
    "Cold packs keep these medicines safe for 48 hours.  ParcelPro is based on only 40 deliveries (1 over 48h), so its rate is less certain; Northway and Swiftline each have 90.",
    ha='left', va='bottom', fontsize=8.5, color='#555555'
)

plt.subplots_adjust(left=0.10, right=0.97, top=0.81, bottom=0.16)
