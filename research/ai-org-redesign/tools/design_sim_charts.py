from pathlib import Path
import csv
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter

# Shared visual style for all four figures.
plt.rcParams.update({'figure.facecolor': '#fcfcfb', 'axes.facecolor': '#fcfcfb',
    'text.color': '#0b0b0b', 'axes.labelcolor': '#0b0b0b', 'xtick.color': '#52514e',
    'ytick.color': '#52514e', 'axes.edgecolor': '#e1e0d9', 'grid.color': '#e1e0d9',
    'axes.spines.top': False, 'axes.spines.right': False, 'font.size': 10,
    'axes.titlesize': 11, 'figure.dpi': 160, 'savefig.dpi': 160})
BLUE, ORANGE, GREEN, YELLOW = '#2a78d6', '#eb6834', '#1baf7a', '#eda100'
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'figures'
OUT.mkdir(exist_ok=True)
SUBTITLE = 'Simulated values under assumed parameters, not measurements.'
DESIGNS = ['role_for_role', 'case_owner_all', 'case_owner_legal', 'shared_record_all',
           'shared_record_legal', 'checker_all', 'checker_legal']
LABELS = ['Role for role', 'Case owner, people at every control',
          'Case owner, people only where law requires', 'Shared record, people at every control',
          'Shared record, people only where law requires', 'Independent checker, people at every control',
          'Independent checker, people only where law requires']
PARAMS = {'agent_time': 'Agent time on desk work', 'agent_queue': 'Agent queue wait',
          'batch_kept': 'Batch waits kept', 'agent_error': 'Agent error rate',
          'handoff_loss': 'Loss per agent handoff', 'record_loss_kept': 'Handoff loss kept with shared record',
          'owner_drift': 'Case owner drift', 'shared_blind_spot': 'Shared record blind spot',
          'catch_person': "Person's catch rate", 'catch_agent': "Agent's catch rate",
          'catch_checker': "Checker's catch rate", 'checker_time': 'Final checker time',
          'repair_share': 'Repair work per caught defect'}

def read(name):
    with (ROOT / name).open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def header(fig, title):
    fig.text(.03, .975, title, ha='left', va='top', fontsize=13, fontweight='bold')
    fig.text(.03, .900 if '\n' in title else .933, SUBTITLE, ha='left', va='top', fontsize=10, color='#52514e')
    print(title)

def log_ticks(ax):
    lo, hi = ax.get_xlim()
    ax.xaxis.set_major_locator(FixedLocator([v for v in (.1, .2, .5, 1, 2, 5, 10) if lo <= v <= hi]))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value:g}'))
    ax.xaxis.set_minor_formatter(NullFormatter())

def finish(fig, name, rect=(0, 0, 1, .86)):
    fig.tight_layout(rect=rect)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for ax, annotation in getattr(fig, '_bar_labels', []):
        bounds = annotation.get_window_extent(renderer).expanded(1.08, 1)
        reference = ax.transData.transform((1, 0))[0]
        shift = 0
        if bounds.x0 <= reference <= bounds.x1:
            shift = reference - bounds.x1 - 4 * fig.dpi / 72
        if bounds.x1 + shift > ax.bbox.x1:
            shift += ax.bbox.x1 - bounds.x1 - shift - 4 * fig.dpi / 72
        if bounds.x0 + shift < ax.bbox.x0:
            shift += ax.bbox.x0 - bounds.x0 - shift + 4 * fig.dpi / 72
        annotation.xyann = (annotation.xyann[0] + shift * 72 / fig.dpi, annotation.xyann[1])
    fig.savefig(OUT / name, dpi=160)
    plt.close(fig)

results, sensitivity = read('design_sim_results.csv'), read('design_sim_sensitivity.csv')
central = {r['design']: r for r in sensitivity if r['parameter'] == 'central'}
workflows = defaultdict(dict)
for r in results:
    key = (r['id'], r['org'])
    if r['design'] in workflows[key]:
        raise ValueError(f'Duplicate workflow design: {key} {r["design"]}')
    workflows[key][r['design']] = r

# Median comparison.
fig, axes = plt.subplots(1, 3, figsize=(11, 5.8), sharey=True)
y = np.arange(len(DESIGNS))
fig._bar_labels = []
for ax, col, label in zip(axes, ['elapsed', 'person', 'escaped'],
                          ['Elapsed time', "People's hands-on time", 'Escaped defects']):
    values = [float(central[d][col]) for d in DESIGNS]
    ax.barh(y, values, height=.55, color=BLUE, zorder=3)
    if col == 'escaped':
        ax.set_xscale('log')
        ax.set_xlim(min(values) * .65, max(1.2, max(values)) * 2.5)
        log_ticks(ax)
    else:
        ax.set_xlim(0, max(1.35, max(values) * 1.4))
    ax.axvline(1, color='#52514e', linewidth=1, linestyle='--')
    ax.text(1, 1.02, 'as-is', transform=ax.get_xaxis_transform(), ha='center', va='bottom', fontsize=9)
    for pos, value in zip(y, values):
        annotation = ax.annotate(f'{value:.2f}', (value, pos), xytext=(4, 0), textcoords='offset points', va='center', fontsize=9,
                                 bbox=dict(facecolor=fig.get_facecolor(), edgecolor='none', pad=1))
        fig._bar_labels.append((ax, annotation))
    ax.set_title(label, pad=22)
    ax.set_xlabel('Relative to as-is\n(1.0 = no change)')
    ax.grid(axis='x', linewidth=.6)
axes[0].set_yticks(y, LABELS)
axes[0].invert_yaxis()
axes[0].set_ylabel('Design')
role = central['role_for_role']
header(fig, f"Role for role cuts people's hands-on time to {float(role['person']):.2f} of as-is\n"
            f"but elapsed time only to {float(role['elapsed']):.2f}")
finish(fig, 'design_medians.png')

# Pair workflow outcomes using both workflow identifiers.
x, yy = [], []
for rows in workflows.values():
    x.append(float(rows['role_for_role']['elapsed_vs_as_is']))
    yy.append(min(float(rows[d]['elapsed_vs_as_is']) for d in ['case_owner_all', 'shared_record_all', 'checker_all']))
n = sum(b < a - .02 for a, b in zip(x, yy))
fig, ax = plt.subplots(figsize=(11, 6))
ax.scatter(x, yy, s=32, color=BLUE, edgecolors='white', linewidths=.6, zorder=3)
limit = max(1.05, max(x + yy) * 1.02)
ax.plot([0, limit], [0, limit], color='#52514e', linestyle='--', label='same as role for role')
ax.set(xlim=(0, limit), ylim=(0, limit), xlabel='Role for role elapsed time relative to as-is (1.0 = no change)',
       ylabel='Fastest redesign elapsed time relative to as-is (1.0 = no change)')
ax.grid(axis='x', linewidth=.6); ax.legend(loc='upper left', frameon=False, fontsize=9)
header(fig, f'A redesign that keeps every control is faster than role for role\n'
            f'in {n} of {len(x)} processes')
finish(fig, 'design_role_for_role_vs_redesign.png')

# Compare the shared-record result with its fixed-wait share.
x = [float(rows['shared_record_legal']['as_is_fixed_wait_share']) for rows in workflows.values()]
yy = [float(rows['shared_record_legal']['elapsed_vs_as_is']) for rows in workflows.values()]
median_wait = np.median(x) * 100
fig, ax = plt.subplots(figsize=(11, 6))
ax.scatter(x, yy, s=32, color=BLUE, edgecolors='white', linewidths=.6, zorder=3)
lim = max(1.05, max(x + yy) * 1.05)
ax.plot([0, lim], [0, lim], color='#52514e', linestyle='--', label='floor: waiting no design removes')
ax.set(xlim=(0, lim), ylim=(0, lim), xlabel='As-is fixed wait share of elapsed time (fraction)',
       ylabel='Shared record elapsed time relative to as-is (1.0 = no change)')
ax.grid(axis='x', linewidth=.6); ax.legend(loc='upper left', frameon=False, fontsize=9)
header(fig, f'Half of processes have at least {median_wait:.0f}% of their elapsed time\n'
            'in waits no design removes')
finish(fig, 'design_fixed_wait_ceiling.png')

# Sensitivity endpoints are ordered by the parameter value, not by the result.
selected = ['role_for_role', 'case_owner_legal', 'shared_record_legal', 'checker_legal']
fig, axes = plt.subplots(1, 2, figsize=(11, 8.8), sharey=True)
elapsed_spans, escaped_spans = [], []
for ax, metric, label in zip(axes, ['elapsed', 'escaped'], ['Elapsed time', 'Escaped defects']):
    for i, parameter in enumerate(PARAMS):
        for j, (design, color) in enumerate(zip(selected, [BLUE, ORANGE, GREEN, YELLOW])):
            rows = sorted((r for r in sensitivity if r['parameter'] == parameter and r['design'] == design),
                          key=lambda r: float(r['value']))
            if len(rows) != 2:
                raise ValueError(f'Expected two sensitivity rows for {parameter}, {design}')
            low, high = (float(r[metric]) for r in rows)
            if metric == 'escaped':
                escaped_spans.append((abs(np.log(high / low)), parameter))
            else:
                elapsed_spans.append(abs(high - low))
            pos = i + (j - 1.5) * .16
            ax.plot([low, high], [pos, pos], color=color, linewidth=2, zorder=2)
            ax.scatter(float(central[design][metric]), pos, s=32, color=color, edgecolor='white', linewidth=.6, zorder=3)
    if metric == 'escaped':
        ax.set_xscale('log')
        log_ticks(ax)
    ax.axvline(1, color='#52514e', linewidth=.8, linestyle='--')
    ax.grid(axis='x', linewidth=.6)
    ax.set_title(label)
    ax.set_xlabel('Relative to as-is\n(1.0 = no change)')
axes[0].set_yticks(np.arange(len(PARAMS)), list(PARAMS.values()))
axes[0].invert_yaxis(); axes[0].set_ylabel('Parameter varied')
handles = [Line2D([0], [0], color=c, marker='o', markeredgecolor='white', markersize=6, linewidth=2, label=LABELS[DESIGNS.index(d)])
           for d, c in zip(selected, [BLUE, ORANGE, GREEN, YELLOW])]
fig.legend(handles=handles, loc='lower center', ncol=2, frameon=False, fontsize=9, bbox_to_anchor=(.5, .005))
widest_parameter = max(escaped_spans)[1]
header(fig, f'Elapsed time moves at most {max(elapsed_spans):.2f} across the sweep;\n'
            f'escaped defects swing most with {PARAMS[widest_parameter]}')
finish(fig, 'design_sensitivity.png', rect=(0, .10, 1, .86))

