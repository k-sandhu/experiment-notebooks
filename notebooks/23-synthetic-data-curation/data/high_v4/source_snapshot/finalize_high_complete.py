"""Integrate a completed v4 study. Refuse to publish incomplete comparisons."""
import hashlib
import json
import re
from pathlib import Path
from refresh_high_complete import build

base = Path(__file__).parent
repo = base.parent / 'experiment_notebooks'
folder = repo / 'notebooks/23-synthetic-data-curation'
proposal = build(write=False)
if proposal['state'] != 'complete':
    raise RuntimeError('Finish and audit both paired arms before replacing the notebook narrative.')
report = proposal['report']
metrics = report['metrics']
original = metrics['original_collection']
audit = metrics['audit']
arms = {r['arm']: r for r in metrics['interventions']}
pair = metrics['paired_value_recovery']
n = pair['n_pairs']
nc = original['n_attempted_cases']
fresh = arms['fresh_retry']['value_correct_valid_schema']
repair = arms['feedback_repair']['value_correct_valid_schema']
ci_low, ci_high = pair['paired_bootstrap_95_interval_percentage_points']
pair_difference = pair['difference_percentage_points']
summary = (f'The higher-reasoning follow-up uses {nc} more demanding procurement packets and a separate '
    f'{audit["n_attempted_cases"]}-packet audit. Sol returned all seven values correctly on '
    f'{original["value_correct_valid_schema"]}/{nc} collection packets. On {n} selected original failures, '
    f'a fresh retry recovered {fresh}/{n}, and repair with the old answer and failed-field feedback recovered {repair}/{n}. '
    f'The observed repair advantage is {pair_difference:.1f} percentage points, with a paired 95% bootstrap interval from {ci_low:.1f} to {ci_high:.1f} points, so this run does not establish a reliable advantage. '
    'These are results on clean fictional records with exact answer keys and tools disabled; they do not measure training gains.')

top_workflow = '''### Higher-reasoning follow-up workflow

```mermaid
flowchart TB
    inputs["32 pilot + 1,056 potential main packets"] --> checks["Independent rendered-source audits<br/>every answer key agrees"]
    checks --> pilot["16 healthy Sol pilot requests<br/>level 2: 3 value failures / 8"]
    pilot --> main["N_COLLECTION collection originals<br/>Sol via codex exec, high reasoning"]
    main --> selected["N_PAIRS genuine original value failures<br/>fixed seeded ranking"]
    selected --> audit["24 separate audit originals<br/>excluded from selection"]
    audit --> review["All originals complete<br/>source and failure review"]
    review --> arms["N_ARMS paired intervention requests<br/>fresh retry and feedback repair"]
    arms --> result["Exact values, evidence, paired recovery<br/>unique source coverage"]
```

One selected failed source goes to both interventions. The repair gets its previous answer and failed-field names; the fresh retry gets the original task and source again. A correct answer must pass the same checker in either arm.
'''.replace('N_COLLECTION',str(nc)).replace('N_PAIRS',str(n)).replace('N_ARMS',str(2*n))


def remove_previous_summary(source):
    return re.sub(r'\n\n(?:The newest attempt requests high reasoning|The higher-reasoning follow-up uses).*?(?=\n\n|\Z)', '', source, flags=re.S)

notebook_path = folder / '23_synthetic_data_curation.ipynb'
notebook = json.loads(notebook_path.read_text(encoding='utf-8'))
start = next(i for i,c in enumerate(notebook['cells']) if c['cell_type']=='markdown' and
             ''.join(c['source']).startswith('## 13. Larger source packs and higher reasoning'))
prefix = notebook['cells'][:start]
sql_source = next(''.join(c['source']) for c in notebook['cells'] if c['cell_type']=='code' and
                  'HIGH_AUDITED_CASES = 0' in ''.join(c['source']))
for c in prefix:
    if c['cell_type'] != 'markdown':
        continue
    source = ''.join(c['source'])
    if source.startswith('# Making useful'):
        source = remove_previous_summary(source)
        source = source.rstrip() + '\n\n' + summary + '\n'
    if source.startswith('## Contents'):
        source = re.split(r'### Higher-reasoning follow-up (?:status|workflow)',source,maxsplit=1)[0].rstrip() + '\n\n' + top_workflow
    c['source'] = source.splitlines(keepends=True)

def cell(source, kind='markdown'):
    item={'cell_type':kind,'metadata':{},'source':source.splitlines(keepends=True),
          'id':'high-final-'+hashlib.sha256(source.encode()).hexdigest()[:14]}
    if kind=='code':item.update(execution_count=None,outputs=[])
    return item

cells=[cell(proposal['markdown'])]
for name in ['high_transport.py','high_fixtures.py','high_material_audit.py','high_experiment.py']:
    cells += [cell('### Embedded '+name.replace('_',' ').replace('.py','')+'\n\nThis frozen code defines source generation, exact checks or cached CLI requests. The replay cells below explicitly disable new calls.'),
              cell((base/name).read_text(encoding='utf-8'),'code')]
pilot_code='''# Rebuild the successful serial pilot from its exact cached requests.
HIGH_PROTOCOL = "23-high-v4d"
HIGH_PILOT_CONFIG = {**HIGH_PILOT_CONFIG, "protocol": HIGH_PROTOCOL}
HIGH_MAIN_CONFIG = {**HIGH_MAIN_CONFIG, "protocol": HIGH_PROTOCOL}
HIGH_HEALTHY_PILOT = high_run_pilot(root=Path.cwd(), live=False)
print("Pilot selected level:", HIGH_HEALTHY_PILOT["selected_level"])
print("Threshold met:", HIGH_HEALTHY_PILOT["threshold_met"])
'''
cells += [cell('### Replay the healthy serial pilot\n\nThis stage reconstructs the fixed packets and reads the successful v4d cache. The earlier service attempts remain archived and cannot influence selection.'),cell(pilot_code,'code')]
smoke='''# Optional new small pilot. Defaults off and never overwrites these results.
if HIGH_V4_LIVE:
    import uuid
    assert HIGH_V4_MODELS == ["gpt-6.1-sol"]
    assert 1 <= N_HIGH_LIVE_PILOT_CASES <= 8
    HIGH_NEW_ROOT = Path.cwd() / "data" / "tmp" / ("high_smoke_" + uuid.uuid4().hex[:12])
    HIGH_SMALL_CONFIG = {**HIGH_PILOT_CONFIG, "n_cases": N_HIGH_LIVE_PILOT_CASES,
                         "min_value_failures": min(3, N_HIGH_LIVE_PILOT_CASES)}
    HIGH_NEW_PILOT = high_run_pilot(config=HIGH_SMALL_CONFIG, root=HIGH_NEW_ROOT, live=True)
else:
    print("No new CLI calls. HIGH_V4_LIVE is False.")
'''
cells += [cell('### Optional small live pilot\n\nHIGH_V4_LIVE defaults to False near the top. Its two-case default permits at most eight new requests across four levels, uses a two-failure threshold, and writes to a new ignored data/tmp/ folder. This smaller smoke test is separate from the full study. It does not automatically collect main originals or run repairs.'),cell(smoke,'code'),
          cell('### Embedded main dispatch helper\n\nThe serial pilot is now complete. This helper retains the frozen scoring and request construction, then dispatches main requests in waves of at most two. Both settle before a new wave begins; service failures stop the phase.'),cell((base/'high_parallel.py').read_text(encoding='utf-8'),'code')]
main_code='''# Cache-only replay of the pre-audited cohort, original answers and both arms.
HIGH_PREPARED = high_prepare_main(root=Path.cwd())
HIGH_ORIGINALS = high_collect_originals(root=Path.cwd(), live=False)
HIGH_BUNDLE = high_run_interventions(root=Path.cwd(), live=False)
print("Collection originals:", HIGH_BUNDLE["metrics"]["original_collection"])
print("Separate audit:", HIGH_BUNDLE["metrics"]["audit"])
print("Paired recovery:", HIGH_BUNDLE["metrics"]["paired_value_recovery"])
'''
cells += [cell('### Replay originals and paired interventions\n\nThe original phase reproduces the declared expansion and fixed random selection. The intervention phase then reads one saved fresh retry and one saved feedback repair per selected case. All calls use live=False; a missing cache raises instead of querying a model.'),cell(main_code,'code')]
for name in ['high_reporting.py','high_complete_reporting.py']:
    cells += [cell('### Embedded '+name.replace('_',' ').replace('.py','')+'\n\nThis presentation code reads the cached evidence, checks counts and lineage, and draws the figures. It does not invoke a model.'),cell((base/name).read_text(encoding='utf-8'),'code')]
cells += [cell('### Rebuild results and figures offline\n\nThis cell rechecks the paired outcomes and exact feedback against saved rows, then recreates the figures in this section.'),cell(proposal['replay_code'],'code'),
          cell('### Recompute every potential main target\n\nThe separate SQL/Decimal reader derives all 1,056 potential main answers again from their saved visible text. A passed source audit establishes a calculable target; it is not a model prediction.'),cell(sql_source,'code')]
cost_code='''print("Recorded high-v4 request attempts:", HIGH_COMPLETE_REPORT["base"]["n_started_requests"])
print("Observed token components:", HIGH_COMPLETE_REPORT["base"]["recorded_usage"])
print("Requests without usage:", HIGH_COMPLETE_REPORT["base"]["n_requests_missing_usage"])
print("USD spend is unknown: the subscription CLI does not expose billing. Missing usage is not zero.")
'''
cells += [cell('### Recorded spend\n\nThe totals include the healthy study and preserved service attempts. Reasoning and cached-input counts are components of the reported totals; they are not added a second time. Authoring-agent usage is outside these experiment CLI counters.'),cell(cost_code,'code')]

future='''## 14. Future work and further reading

The links were checked on October 26, 2026. The follow-ups below address limits of the measured high-reasoning comparison.

### Future work

- Repeat the paired comparison on independently authored source templates and new cases. Measure recovery and unique accepted-source coverage. The current result is conditional on N_PAIRED original failures and six families sharing most rules.
- Add an old-answer-only arm beside fresh retry and old answer plus field feedback. Measure the separate value of the diagnosis. The current repair arm receives both kinds of extra information, so its difference from a fresh retry cannot isolate feedback alone.
- Give Sol a calculator or ledger-reconciliation tool on matched packets. Measure quantity and price errors, tokens and time against the tool-disabled setting. The present source audit makes the balances exactly inspectable, while model answers alone do not reveal which substep caused a wrong quantity.
- Compare matched cases at 32,64,128 and192 shipment histories, changing one source rule at a time. Measure failure rates with uncertainty and test whether more history consistently increases errors. The pilot stopped at level2 and the families here are mixed variants rather than causal ablations.
- Replace exact-key field flags with an independent verifier that sees only the packet and proposed answer. Measure diagnostic precision and paired recovery. Our repair package uses oracle feedback whose correctness an ordinary workflow may not have.

### Further reading

- [Large Language Models Cannot Self-Correct Reasoning Yet](https://arxiv.org/abs/2310.01798) (Huang et al.,2024). Studies correction without external feedback; this experiment supplies externally verified failed-field labels.
- [Learning to Build the Environment: Self-Evolving Reasoning RL via Verifiable Environment Synthesis](https://arxiv.org/abs/2605.14392) (Shi et al.,2026). Motivates executable task generation,verification and difficulty calibration; this notebook collects data without reproducing its training procedure.
- [Self-Evolve With a Reference: Anchored Training of Tool-Integrated Agents](https://arxiv.org/abs/2610.09856) (Liao et al.,2026). Motivates separating curriculum-selection signals from measured learning; our exact keys check extraction correctness.
- [Absolute Zero: Reinforced Self-play Reasoning with Zero Data](https://arxiv.org/abs/2505.03335) (Zhao et al.,2025). Combines task proposal and executable verification in a training loop; this experiment stops before training.
- [Deduplicating Training Data Makes Language Models Better](https://aclanthology.org/2022.acl-long.577/) (Lee et al.,2022). Explains why repeated records and split overlap need explicit accounting when preparing data.
- [Self-Instruct: Aligning Language Models with Self-Generated Instructions](https://aclanthology.org/2023.acl-long.754/) (Wang et al.,2023). An earlier example of generating instruction examples and filtering invalid or similar items.
'''.replace('N_PAIRED',str(n)).replace('et al.,','et al., ').replace('32,64,128 and192','32, 64, 128 and 192').replace('level2','level 2').replace('generation,verification','generation, verification')
cells += [cell(future)]
notebook['cells']=prefix+cells
for item in notebook['cells']:
    if item['cell_type'] != 'markdown':
        continue
    source = ''.join(item['source'])
    heading = re.search(r'^## (\d+\. [^\n]+)', source, re.M)
    if heading:
        slug = re.sub(r'[^\w\- ]', '', heading.group(1).lower())
        slug = re.sub(r' +', '-', slug)
        anchor = f'<a id="{slug}"></a>'
        if anchor not in source:
            source = source[:heading.end()] + '\n\n' + anchor + source[heading.end():]
            item['source'] = source.splitlines(keepends=True)
assert len({c['id'] for c in notebook['cells']})==len(notebook['cells'])
notebook_path.write_text(json.dumps(notebook,ensure_ascii=False,indent=1)+'\n',encoding='utf-8',newline='\n')

readme_path=folder/'README.md'
readme=readme_path.read_text(encoding='utf-8')
front=readme.split('## 13. Larger source packs and higher reasoning')[0].rstrip()
front=remove_previous_summary(front)
front=front.replace('\n\n## Contents', '\n\n'+summary+'\n\n## Contents', 1)
# Keep the original historical overview and mirror the new follow-up flow before section 1.
contents, rest = front.split('\n\n## 1. Task and question', 1)
contents = re.split(r'### Higher-reasoning follow-up (?:status|workflow)',contents,maxsplit=1)[0].rstrip()
front=contents+'\n\n'+top_workflow+'\n\n## 1. Task and question'+rest
reproduction='''
### Reproduction and saved materials

Normal execution of [the notebook](23_synthetic_data_curation.ipynb) replays the historical protocols, the healthy pilot, the original high-reasoning answers and both intervention arms from exact request caches. It also recomputes all 1,056 potential main targets from source text. It makes no new model calls. The optional small-pilot knob defaults to False and uses a separate ignored folder.

```powershell
python -m nbconvert --to notebook --execute --inplace 23_synthetic_data_curation.ipynb
python -m unittest discover -s data/high_v4/source_snapshot -p "test_high*.py"
```

The 34 new tests check source solvability, hand calculations, request isolation, generic feedback, paired statistics and bounded dispatch. [Provenance](data/high_v4/provenance.json), [the artifact audit](data/high_v4/artifact_audit.json), [the source index](data/high_v4/preflight/manifest.json), [the independent SQL audit](data/high_v4/preflight/independent_sql_audit.json) and [the independent Fraction audit](data/high_v4/preflight/independent_fraction_audit.json) connect these claims to saved records. The 31 earlier service-attempt records remain archived, including four interrupted outcomes and their unknown usage.
'''
readme_path.write_text(front+'\n\n'+proposal['readme_appendix']+'\n'+reproduction+'\n'+future,encoding='utf-8',newline='\n')

root_path=repo/'README.md'
lines=root_path.read_text(encoding='utf-8').splitlines()
for i,line in enumerate(lines):
    if line.startswith('| 23 |'):
        lines[i]=(f'| 23 | [Synthetic data generation and curation](notebooks/23-synthetic-data-curation/) | '
            f'Generated extraction examples need exact values and inspectable evidence. After three earlier protocols,this follow-up compares a fresh high-reasoning Sol retry with feedback repair on genuine failures from {nc} longer procurement packets,plus a separate24-case audit. Does the repair package recover more cases than another attempt? | '
            f'Sol returned all seven values correctly on {original["value_correct_valid_schema"]}/{nc} collection cases and {audit["value_correct_valid_schema"]}/24 audit cases. On {n} selected genuine failures,fresh retry recovered {fresh}/{n} and feedback repair {repair}/{n}: {pair["repair_only"]} repair-only,{pair["fresh_only"]} retry-only,{pair["both_success"]} both and {pair["neither_success"]} neither. The {pair_difference:+.1f}-point difference has a paired 95% interval of {ci_low:.1f} to {ci_high:.1f} points. Every source passed independent audits before calls. No model was trained. |').replace('protocols,this','protocols, this').replace('packets,plus','packets, plus').replace('separate24','separate 24').replace('failures,fresh','failures, fresh').replace('repair-only,','repair-only, ').replace('retry-only,','retry-only, ')
    if line.startswith('* Notebook 23 runs offline') or line.startswith('* Notebook 23 replays'):
        lines[i]='* Notebook 23 replays its completed protocols and paired interventions offline, preserves interrupted service attempts, and recomputes 1,056 potential main targets from saved text. Live knobs default off; small fresh pilots write to isolated ignored data/tmp/ folders.'
    if line.startswith('Notebook 23 uses fictional order threads'):
        lines[i]=line.replace('records source audits and service interruptions', 'records source audits, paired outcomes and service history')
root_path.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
proposal=build(write=True)
print(json.dumps({'state':proposal['state'],'cells':len(notebook['cells']),'paired_cases':n,'collection_cases':nc,'fresh_recovered':fresh,'repair_recovered':repair,'figures':len(proposal['figures'])}))
