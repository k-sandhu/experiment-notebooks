import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('data.csv', parse_dates=['date'])

# Days when demand exceeded available capacity during the Unit 3 outage
target_dates = pd.to_datetime([
    '2026-01-12', '2026-01-13', '2026-01-14', '2026-01-15'
])
df_short = df[df['date'].isin(target_dates)].copy()
df_short = df_short.set_index('date').loc[target_dates].reset_index()

# Shortfalls
df_short['shortfall_outage'] = (
    df_short['actual_peak_mw'] - df_short['available_capacity_mw']
).clip(lower=0)

# If Unit 3 (50 MW) had been running, capacity would have been 960 MW
df_short['shortfall_unit3'] = (
    df_short['actual_peak_mw'] - 960
).clip(lower=0)

# Forecast under-prediction on very cold days (min temp < -15°C)
cold = df[df['min_temp_c'] < -15]
cold_diff = (cold['actual_peak_mw'] - cold['forecast_peak_mw']).mean()
cold_pct = ((cold['actual_peak_mw'] / cold['forecast_peak_mw'] - 1).mean() * 100)

# Figure
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(len(df_short))
w = 0.35

# Bars
ax.bar(
    x - w / 2, df_short['shortfall_outage'], width=w,
    color='#BDBDBD', edgecolor='#7F7F7F', linewidth=0.8, zorder=3
)
ax.bar(
    x + w / 2, df_short['shortfall_unit3'], width=w,
    color='#D55E00', edgecolor='#D55E00', linewidth=0.8, zorder=4
)

# 40 MW extra-capacity line
ax.axhline(40, color='#333333', linestyle=(0, (4, 3)), linewidth=1.5, zorder=5)
ax.text(
    3.45, 42, '40 MW extra capacity',
    ha='right', va='bottom', fontsize=9.5, color='#333333'
)

# Direct labels for 14 Jan
x14_outage = x[2] - w / 2
x14_unit3 = x[2] + w / 2
ax.text(
    x14_outage, df_short['shortfall_outage'].iloc[2] + 3,
    '102 MW', ha='center', va='bottom', fontsize=10, color='#444444'
)
ax.text(
    x14_unit3, df_short['shortfall_unit3'].iloc[2] + 3,
    '52 MW', ha='center', va='bottom', fontsize=10,
    color='#D55E00', fontweight='bold'
)

# Remaining gap after a 40 MW purchase
ax.annotate(
    '12 MW still uncovered',
    xy=(x14_unit3, 52), xytext=(x14_unit3 + 0.45, 70),
    arrowprops=dict(arrowstyle='->', color='#D55E00', lw=1.2),
    fontsize=9.5, color='#D55E00', ha='left', va='center'
)

# Notes
ax.text(
    0.02, 0.98,
    "Grey: shortfall during 10–16 Jan Unit 3 outage (910 MW capacity).\n"
    "Orange: if Unit 3 had been running (960 MW); only 14 Jan remains short.",
    transform=ax.transAxes, fontsize=9, va='top', ha='left', color='#444444'
)
ax.text(
    0.98, 0.98,
    f"Very cold days (<−15°C):\n"
    f"actual peak +{cold_pct:.1f}% vs forecast\n"
    f"(≈{cold_diff:.0f} MW higher).",
    transform=ax.transAxes, fontsize=9, va='top', ha='right', color='#444444'
)

# Titles and axes
ax.set_title(
    "A 40 MW buffer would still leave the 14 Jan cold-snap peak 12 MW short.",
    fontsize=14, fontweight='bold', pad=20
)
ax.set_xticks(x)
ax.set_xticklabels(
    [d.strftime('%-d %b') for d in df_short['date']], fontsize=11
)
ax.set_ylabel(
    'Shortfall below available capacity (MW)\n(emergency imports needed)',
    fontsize=10
)
ax.set_xlabel('January 2026', fontsize=10)
ax.set_ylim(0, 115)
ax.set_xlim(-0.6, 3.6)

# Clean styling
ax.grid(axis='y', color='#E5E5E5', linewidth=0.8, zorder=0)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.tick_params(axis='both', length=0)
ax.set_facecolor('white')

fig.tight_layout()
