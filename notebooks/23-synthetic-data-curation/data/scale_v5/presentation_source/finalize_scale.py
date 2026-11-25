"""Present the completed larger study as one self-contained lesson."""
import hashlib
import gzip
import json
from pathlib import Path
import re
import shutil

from refresh_scale_report import build

BASE = Path(__file__).resolve().parent
REPO = BASE.parent / 'experiment_notebooks'
ROOT = REPO / 'notebooks' / '23-synthetic-data-curation'
DATA = ROOT / 'data' / 'scale_v5'

INTRODUCTION = '''# Making useful practice examples from fictional orders

A language model can be trained on practice examples: a task, information to solve it and an answer to learn from. A useful collection exercises a skill and gives checked answers. Writing more questions alone does not establish that the examples are useful.

A wrong answer can teach the wrong lesson. If an example says 30 items remain to be delivered when the records show 36, training may reward that incorrect quantity. Supporting records let us inspect, correct or reject it.

### An illustrative practice case

Consider a fictional order for 50 notebooks. The practice task is to read the records and say how many notebooks the customer is still owed.

The warehouse sends 20 notebooks. There are 30 left to send: the original 50 minus the 20 already delivered. A checked answer should connect that quantity to both the order and the delivery record.

Now six delivered notebooks are returned and must be replaced. The customer is owed 36 notebooks: the 30 that had not been sent, plus six replacements. Reading only the order and delivery would miss the return and give a plausible but wrong answer of 30.

A person would combine the order, delivery and return, counting each event once. These numbers are an illustration, not a measured response. We can write longer fictional histories in code and establish their answers before asking a model to read them.

### Comparing two ways to collect a correction

Suppose an answer to one of those histories fails the check. One way to obtain a correction is to ask the original question again in a new conversation. This fresh attempt receives the same records and no previous answer. It shows what another attempt can achieve by itself.

Another way is to show the previous answer and tell the model which field failed the check. The correct value is still withheld. The model must use the records to produce a correction, and the whole answer is checked again because a correction could introduce another mistake.

Checking answers and choosing which ones to keep is called curation. Here both ways of collecting corrections are tried on each original mistake. Each pair faces the same records, separating the benefit of the correction package from simply trying again.

The question is whether the previous answer and a verified failed-field label produce more checked corrections than a fresh attempt. This study collects and checks possible practice data. It does not train a model or measure improvement after training.
'''


def polish_reader_text(text):
    """Shorten repeated explanations without changing measured statements."""
    changes={
        'The original baseline counts every called source in its split. An all-value success requires valid schema and all seven typed values exactly right. Full acceptance also needs source citations.':'The original baseline includes every called source. Acceptance also checks citations.',
        'The audit has its own seed and fewer cases. The collection percentage does not establish a stable accuracy rate on every new packet.':'The audit is smaller and uses an independent seed.',
        'The short literal input excerpt does not contain every movement; the linked packet contains the full evidence.':'The excerpt omits movements; the frozen packet preserves them.',
        'The excerpt is a few literal source rows, not the complete ledger arithmetic. All selected/excluded events remain in the frozen packet and full trace.':'The excerpt is partial; the frozen packet preserves every event.',
        'A terminal transport failure remains a non-recovery in its observed pair. It is separate from a genuine wrong-value reply and from the unavailable controller-interrupted outcomes. Any parsed answer retained after a transport error is excluded from field-error and numeric-regression diagnostics; the frozen operational artifacts remain unchanged.':'Service failures remain operational non-recovery. Retained answers are excluded from wrong-field and regression diagnostics.',
        'A preference pair stores a verified correct follow-up and the actual wrong original answer to the same task. Its candidate and request IDs connect both answers to their raw caches. The rejection logs also retain service failures and unavailable attempts for accounting; those entries do not supply invented wrong answers.':'Preference records pair a checked correction with its actual wrong original. Rejection logs retain unusable requests without inventing answers.',
        'These per-answer counts include every observed follow-up, including an observed partner whose other outcome is unknown. The paired recovery analysis excludes that incomplete source; curation does not discard its real observed answer. Only unavailable request keys and unusable answers are excluded. The separate audit is excluded. Acceptance also requires source citations.':'Curation includes every observed answer, including the known partner of an incomplete pair. Unusable or unknown answers and the separate audit are excluded. Acceptance also requires citations.',
        'Case-level inference is conditional on stopped accrual, pilot calibration and a shared generator; it does not establish a training or frontier-model gain.':'This interval concerns selected cases from one generator.',
        '1 partially unavailable pairs':'1 partially unavailable pair',
        '| Unusable replies |':'| Other unreadable |',
        'The case ID joins its frozen source and saved answers.':'',
    }
    for old,new in changes.items():text=text.replace(old,new)
    text=re.sub(r'(Original|Fresh retry|Feedback repair): gpt-6\.1-sol via codex exec, effort high, stage (?:generate|repair), sample \d+\. ',r'\1: ',text)
    text=re.sub(r'<details><summary>([^<]+)</summary>',r'\1',text).replace('</details>','')
    return '\n'.join(line.rstrip() for line in text.splitlines()).rstrip()+'\n'


def timeout_example(data, gold):
    """Inspect retained text; never re-score or accept a failed request."""
    path=data/'intervention_resume_005/amendment_005.json'
    if not path.is_file():return ''
    amendment=json.loads(path.read_bytes())
    for item in amendment['retained_transport_failures']:
        if 'timeout' not in item['error'].lower():continue
        cid=item['case_id'];key=item['request_key']
        if cid not in gold:continue
        with gzip.open(data/'main/cache'/(key+'.json.gz'),'rt',encoding='utf-8') as stream:cache=json.load(stream)
        raw=cache['attempts'][-1].get('final_assistant_response','')
        try: answer=next(r['answer'] for r in json.loads(raw)['results'] if r['case_id']==cid)
        except (ValueError,KeyError,StopIteration,TypeError):continue
        if not all(type(answer.get(k)) is type(v) and answer[k]==v for k,v in gold[cid].items()):continue
        start=raw.find('"quantity_units"');end=raw.find(',"currency"',start)
        fragment=raw[start:end] if start>=0 and end>start else raw[:100]
        return (f'#### A correct answer retained after a timeout\n\nService case `{cid}` retained the raw fragment `{fragment}`. '
                'All seven values match the saved answer key. The recorded 900-second timeout still scores zero operational recovery. '
                'That score records the timeout, not a wrong quantity. '
                f'[Full raw cache](data/scale_v5/main/cache/{key}.json.gz). '
                'The other service failure ended at provider capacity without a completed answer. Neither is counted as a wrong-value error.\n\n')
    return ''


def training_context_text(collection, pairs, potential_main_count, accepted_source_count, fresh, repair):
    return f'''### From checked corrections to a training experiment

The collection produced {collection['value_failure_cases']}/{collection['n_attempted_cases']} genuine wrong-value cases after all {potential_main_count:,} potential sources passed independent checks. That validation establishes solvable errors to learn from. The observed weakness is long-ledger reconciliation with tools disabled; it is not an intrinsic limit of the model with a calculator or other records.

Neither follow-up recovered {pairs['neither_success']}/{pairs['n_pairs']} selected failures, including a repair attempt with verified field feedback. Repair recovered {repair}, fresh retry {fresh}, without an established repair benefit. Even the {accepted_source_count} distinct accepted sources in section 6 share one generator. Their count measures candidate data, not a generalized skill acquired through training.

To test training value, compare training on corrections with training on fresh-attempt examples under an equal budget. Evaluate both on unseen records from separately written generators. Keep all versions of a source on the same side of the training/evaluation split, so memorizing a record cannot count as learning a new skill.
'''


def cell(source, kind='markdown'):
    if kind=='markdown':source=polish_reader_text(source)
    result = {'cell_type': kind, 'metadata': {}, 'source': source.splitlines(keepends=True),
              'id': 'scale-final-' + hashlib.sha256(source.encode()).hexdigest()[:14]}
    if kind == 'code':
        result.update(execution_count=None, outputs=[])
    return result



def report_parts(markdown):
    fragments = re.split(r"^### ([^\n]+)\n", markdown, flags=re.M)
    sections = [(fragments[i], "### "+fragments[i]+"\n"+fragments[i+1]) for i in range(1,len(fragments),2)]
    return sections


def main():
    proposal = build(root=ROOT, write=False)
    assert proposal['state'] == 'complete', 'Publish only a complete paired comparison'
    for name in ('scale_main_material_review.json', 'scale_original_failure_review.json'):
        assert json.loads((DATA / name).read_text(encoding='utf-8'))['passed'], name
    report, s = proposal['report'], proposal['summary']
    p, metrics = s['paired'], report['metrics']
    n, collection, audit = s['n_pairs'], s['collection'], s['audit']
    potential_main_count=sum(block['manifest']['n_cases'] for block in report['protocol']['blocks'])
    scheduled = s.get('n_scheduled_pairs', n)
    unavailable_pairs = s.get('n_unavailable_pairs', 0)
    missing_completions = report['missing_outcomes']['n_completions']
    fresh, repair = s['fresh_recovered'], s['repair_recovered']
    delta = p['difference_percentage_points']
    lo, hi = p['paired_bootstrap_95_interval_percentage_points']
    pv = p['exact_mcnemar_two_sided_p']
    if not n:
        conclusion = 'The fixed original cap produced no eligible pairs, so the repair comparison is unavailable.'
        effect = ''
    else:
        if metrics['primary_decision']['criterion_met']:
            conclusion = 'The comparison supports a repair advantage within these fictional histories.'
        elif delta < 0 and pv < .05 and not unavailable_pairs:
            conclusion = 'The comparison supports a fresh-attempt advantage within these fictional histories.'
        else:
            conclusion = 'The comparison does not establish a repair advantage within these fictional histories.'
        if not metrics['primary_decision']['criterion_met'] and lo<0<hi:
            conclusion+=' The uncertainty interval allows both a decline and an improvement; it does not establish a fresh-attempt advantage either.'
        effect = (f'The repair-minus-retry difference is {delta:+.2f} percentage points '
                  f'(paired 95% interval {lo:.2f} to {hi:.2f}; exact paired p={pv:.6g}). ')
    plain_effect = ((f'Among cases with both follow-up outcomes known, feedback corrected {abs(delta):.2f} ' + ('more' if delta > 0 else 'fewer') +
                     ' cases per 100 original mistakes. ') if n and delta else
                    'Both methods corrected the same number of cases with known outcomes. ' if n else '')
    summary = (
        '## The study in brief\n\n'
        f'This study compares {n} complete pairs of attempts to correct verified mistakes from {collection["n_attempted_cases"]:,} '
        'fresh fictional order histories. Both approaches use GPT-6.1 Sol with high reasoning effort. '
        'A corrected case must have valid output and all seven extracted values exactly right. '
        + '\n\n'
        f'A fresh attempt corrected {fresh}/{n} cases; the previous answer plus verified failed-field labels corrected {repair}/{n}. '
        + plain_effect
        + conclusion + '\n\n'
        + (f'The target was 600 pairs; the fixed collection cap left a shortfall of {s["target_shortfall"]}. '
           if s['target_shortfall'] else '')
        + (f'{unavailable_pairs} of {scheduled} planned pairs have an unknown outcome, so the result must also hold under every possible missing result before a repair advantage is claimed. ' if unavailable_pairs else '')
        + 'One program generated all the histories, so the result applies to these fictional records and does not establish performance across businesses. '
        'The conclusion concerns checked corrections; no model was trained.'
    )
    readable={arm:[row for row in report['interventions'] if row['arm']==arm and not row['transport_error'] and row['response'] is not None and row['verification']['valid_schema']] for arm in ('fresh_retry','feedback_repair')}
    readable_n={arm:len(rows) for arm,rows in readable.items()}
    unreadable_n={arm:n-count for arm,count in readable_n.items()}
    if any(unreadable_n.values()) and all(readable_n.values()):
        raw_direction=(repair>fresh)-(repair<fresh)
        readable_direction=(repair*readable_n['fresh_retry']>fresh*readable_n['feedback_repair'])-(repair*readable_n['fresh_retry']<fresh*readable_n['feedback_repair'])
        summary+=f"\n\nUnreadable outcomes on paired sources: fresh {unreadable_n['fresh_retry']}, repair {unreadable_n['feedback_repair']}. Scoring readable replies only {'changes' if raw_direction!=readable_direction else 'does not change'} the recovery ranking."
    if n and max(fresh,repair)==n and pv>=.05:
        summary+=f'\n\nOne approach reaches the observed ceiling of {n}/{n}, but only {p["discordant_pairs"]} pairs distinguish the approaches. This sample does not settle their ranking.'
    future = '''## 10. Future work and further reading

The links were checked on October 30, 2026. These follow-ups address the limits of the larger paired comparison.

### Future work

- Repeat the paired design on independently authored procurement, payment and logistics generators. Measure recovery across tasks, because this study's many cases share one generator.
- Add an old-answer-only arm under the same call budget. Measure the contribution of failed-field labels, which the current package combines with prior-answer exposure.
- Give Sol a calculator and ledger-query tool on matched sources. Measure quantity errors, tokens and elapsed time: the present answers reveal mismatches without revealing the calculation that failed.
- Under the same two-call budget, compare two fresh attempts with a fresh attempt plus repair. Measure distinct accepted sources. Repair-only successes add examples here, but there is no second-fresh-attempt control to show which mixture collects more.
- Use a separate verifier that sees source text and the proposed answer, without the answer key. Measure diagnostic accuracy and recovery, because the current feedback has privileged access to ground truth.

### Further reading

- [Large Language Models Cannot Self-Correct Reasoning Yet](https://arxiv.org/abs/2310.01798) (Huang et al., 2024). Studies correction without external feedback; this experiment supplies externally verified failed-field labels.
- [Absolute Zero: Reinforced Self-play Reasoning with Zero Data](https://arxiv.org/abs/2505.03335) (Zhao et al., 2025). Uses executable tasks and verification in a training loop; this experiment stops at data collection and curation.
- [Self-Instruct: Aligning Language Models with Self-Generated Instructions](https://aclanthology.org/2023.acl-long.754/) (Wang et al., 2023). Describes generated instruction examples and filtering, an earlier setting for the data-selection questions here.
- [Deduplicating Training Data Makes Language Models Better](https://aclanthology.org/2022.acl-long.577/) (Lee et al., 2022). Explains why repeated records and split overlap need explicit accounting when preparing data.
- [McNemar's test documentation](https://www.statsmodels.org/stable/generated/statsmodels.stats.contingency_tables.mcnemar.html) (statsmodels developers, checked 2026). Defines the exact binomial test used to compare the two outcomes on each selected failed case.
'''

    parts = report_parts(proposal['markdown'])
    used = set()
    def take(*headings, starts=()):
        found=[]
        for i,(title,text) in enumerate(parts):
            if title in headings or any(title.startswith(start) for start in starts):
                assert i not in used, 'Narrative section used twice: '+title
                used.add(i); found.append(text)
        return '\n\n'.join(found)
    take('Question, data and headline')  # Replaced by the plain-language study summary.
    workflow=take('Experiment workflow')
    if not workflow:
        diagrams=re.findall(r'```mermaid\n.*?```',proposal['markdown'],flags=re.S)
        assert diagrams, 'The saved study must have a workflow before code'
        workflow='### Experiment workflow\n\n'+'\n\n'.join(diagrams)
    data_text=take('Model and settings')
    design_details=take('Source rules and material checks')
    data_text+='''

### What one packet contains

Each packet describes one fictional purchase order. Return seven values: order ID, item code, open quantity in individual items, price in cents per item, currency, promised shipment date and active status. Cite the source groups supporting each value.

P01 is the signed order; P02 contains approvals; P03 converts boxes or other handling units into individual items; P04 allocates shipments to order lines; P05 sets prices; P06 records revisions. These are clean text tables with full rules, without scans or missing contracts. The [frozen collection corpus](data/scale_v5/main/sources/collection.jsonl.gz) contains every measured input, joined by case ID.

The cutoff is October 26 at noon. For each shipment or return, choose the latest revision recorded by that time, then check its date and status. A voided movement contributes nothing. A reversal removes its referenced shipment once. A return uses the packaging and allocation that applied to its original shipment, so today's box size cannot silently change a historical return.

Open quantity is approved demand minus allocated shipments plus accepted returns. Price starts with the applicable pack price, converts it to an individual-item price, applies rebates and fees, and rounds once to cents. The full rules and exact arithmetic are preserved in the packets and [design details](data/scale_v5/presentation_results/design_details.md).

Independently written source readers reconstruct the answer from the supplied text. All 2,144 potential main packets passed these checks before calls. This prevents an unsolvable packet from counting as a model mistake; it does not establish realism across businesses.
'''
    data_text+='\n\n### When the data were made\n\nEvery generated item records a creation date of October 26, 2026. The [official Sol documentation](https://developers.openai.com/api/docs/models/gpt-6.1-sol), checked October 30, lists an April 30, 2026 knowledge cutoff. Only experiment-authored cases enter this study. Their dates, source and selection rule are in [the freshness manifest](data/scale_v5/freshness_manifest.json).'
    design_details+='\n\n'+take('Difficulty calibration','Planned sensitivity to a five-point gain','Planned precision and the five-point limit','How original failures were accrued')
    cfg=report['protocol']['config']
    pilot_description='; '.join(f"{b['metrics']['value_failure_cases']}/{b['metrics']['n_attempted_cases']} wrong-value cases with {b['tier']} shipments" for b in report['pilot'])
    five_point_power=[r['primary_positive_direction_power_by_n_pairs']['600'] for r in report['power']['grid']['rows'] if r['true_recovery_difference']==.05]
    method_text=f'''### Choosing records with room for a correction

A separate difficulty check found {pilot_description}. It selected {report['protocol']['selected_tier']} base shipments per main packet. Each tier uses fresh cases, so this check finds a workable setting without isolating shipment count as the cause of errors.

The plan began with {cfg['n_initial']} collection sources, adding {cfg['chunk_size']}-source batches until {cfg['target_failures']} wrong-value cases or a {cfg['collection_cap']}-source cap. It found {collection['value_failure_cases']} eligible cases in {collection['n_attempted_cases']} sources. A seeded ranking selected {scheduled} before corrections were seen. The separate {audit['n_attempted_cases']}-source audit contributes no intervention cases.

Both follow-ups see the same packet and request seven values plus citations in a new CLI call. Fresh retry sees no old answer. Feedback repair also receives the old answer and checked failed-field labels, without correct values. Their order is randomized within small dispatch waves. They never see one another's replies. Equal call counts do not equalize prompt length or computation.

### Counting a corrected case

A case scores one when its output has the required types and every extracted value is exactly right; otherwise it scores zero. Full acceptance also requires sufficient source citations. An answer with six correct values and one wrong quantity is not a solved order.

For an illustrative ten failed orders, suppose fresh retry solves four and feedback repair solves six. The difference is 20 percentage points, or two more corrected orders per ten attempts. If both solve three, repair alone solves three, fresh alone solves one and neither solves three. The shared successes cannot distinguish the methods; the disagreement is three versus one.

The measured comparison keeps these outcomes paired by source. Its 95% bootstrap interval resamples whole source pairs 20,000 times and uses the middle 95% of the resulting differences. It shows sampling uncertainty within this selected cohort. The exact McNemar test asks how unusual the imbalance between repair-only and fresh-only successes would be if their chances were equal. A small p-value does not measure the size or business value of a difference.

Under the original planning assumptions, 600 pairs have only {100*min(five_point_power):.1f}% to {100*max(five_point_power):.1f}% probability of detecting a true five-point gain. Thus an inconclusive result cannot establish that the methods are equivalent. Full difficulty, stopping and power calculations are in [design details](data/scale_v5/presentation_results/design_details.md).
'''
    # Place each visual and measured example beside the idea it explains.
    specs={item['name']:item for item in proposal['figures']}
    used_figures=set()
    def figure(name):
        if name not in specs: return ''
        used_figures.add(name)
        item=specs[name]
        alt={'nominal_power.png':'Planned power for five- and ten-point recovery gains',
             'accrual.png':'Collection sources and accrued eligible original failures',
             'baseline_recovery.png':'Original accuracy and recovery on selected failures',
             'paired_outcomes.png':'Fresh and repair outcomes paired by source',
             'numeric_errors.png':'Absolute quantity and price errors across attempts',
             'variants.png':'Original failures and correction recovery by source variant',
             'leave_one_variant_out.png':'Recovery differences after omitting each variant',
             'quantity_audit.png':'Audited quantity calculation for one source'}[name]
        return ('\n\n!['+alt+']('+item['path']+')\n\n'+item['interpretation'])
    take('Figures and how to read them')
    method_text+=figure('nominal_power.png')+figure('accrual.png')
    results_text=take('Original accuracy and failure-only recovery','Observed paired recovery and new damage')
    results_text+=figure('baseline_recovery.png')+figure('paired_outcomes.png')
    results_text+='\n\n'+take('Controller interruption, unavailable outcomes and sensitivity')
    error_text=take('Error size, type and newly damaged fields')
    null_originals=sum(r['split']=='collection' and not r['transport_error'] and r['verification']['valid_schema'] and r['response']['answer']['quantity_units'] is None for r in report['originals'])
    wrong_quantities=collection['wrong_field_counts']['quantity_units']
    if null_originals:
        error_text+=f'\n\nOf {wrong_quantities} wrong original quantities, {null_originals} were legal JSON null answers and {wrong_quantities-null_originals} were wrong numbers. Null is a readable abstention, but it is incorrect against these fully specified records. These null answers are not format failures; unreadable service outcomes are counted separately.'
    service_note=timeout_example(DATA,{cid:row['gold'] for cid,row in report['source_metadata'].items()})
    results_text+='\n\n'+error_text+'\n\n'+service_note+figure('numeric_errors.png')
    results_text+='\n\n'+take('Scenario composition and paired recovery','Scenario variants and descriptive sensitivity')
    results_text+=figure('variants.png')+figure('leave_one_variant_out.png')
    worked=take('Worked inputs, answers and corrections')
    case_fragments=re.split(r'(?=^#### Case \d+:)',worked,flags=re.M)
    case_intro=case_fragments[0]
    case_blocks=case_fragments[1:]
    prompt=take(starts=('Inspect the supplied CLI inputs for Case ',))
    paired_number=re.search(r'CLI inputs for Case (\d+)',prompt)
    end_to_end=next((block for block in case_blocks if paired_number and block.startswith('#### Case '+paired_number.group(1)+':')),None)
    ordinary=next((block for block in case_blocks if ': Original success,' in block),None)
    if ordinary and ordinary!=end_to_end:
        case_blocks.remove(ordinary)
        data_text+='\n\n### One measured source and its answer\n\nThe cases below are chosen by stable item ID to cover observed outcomes, rather than sampled to estimate their frequency. Category counts and the selection rule appear in section 6.\n\n'+ordinary
    if end_to_end:
        case_blocks.remove(end_to_end)
        method_text+='\n\n### An end-to-end correction\n\nThe following measured case connects the supplied record, the checked answer and the two follow-up outcomes. A case scores one only when all seven values are right, so repairing one number is insufficient if another field becomes wrong.\n\n'+end_to_end+'\n\n'+prompt
    else:
        method_text+='\n\n'+prompt
    method_text+=figure('quantity_audit.png')
    examples_text=case_intro+'\n\n'+'\n\n'.join(case_blocks)+'\n\n'+take('Distinct usable correction data')
    assert used_figures==set(specs), 'Every figure needs a reading location'
    take('Why improving an already capable model takes more than corrected answers')
    accepted_source_count=len({r['semantic_hash'] for r in report['originals']+report.get('operational_interventions',report['interventions']) if r['split']=='collection' and not r['transport_error'] and r['response'] is not None and r['verification']['accepted']})
    improvement_text=training_context_text(collection,p,potential_main_count,accepted_source_count,fresh,repair)
    take('What the comparison can support')
    limits_text='''The comparison supports a decision about collecting corrections from these selected fictional records. It supplies both the old answer and privileged failed-field checks; it cannot separate their contributions. The verifier knows the answer key, which an ordinary workflow may lack.

One generator creates clean, active orders with explicit rules. Shared templates, tools disabled during solving, selection on original failure and stopping after enough failures limit transfer to other businesses or ordinary incoming work. The requested service alias is mutable, so unchanged model weights during collection are not guaranteed.

Missing outcomes are handled by a plan fixed before recovery results were inspected, with [the protocol](data/scale_v5/PROTOCOL.md) recording each loss and its amendment. The all-completion decision protects against those unknown binary outcomes in this selected cohort. It cannot remove generator bias. An inconclusive difference does not establish equivalence, and checked corrections alone do not establish a post-training gain.

The generator already knows every correct answer and could label packets directly; model calls measure errors and correction yield, without establishing a cheaper way to create labels.'''
    operational_history=take('Infrastructure stop and declared continuation','Known follow-up transport stop and unchanged scoring')
    operational_history+='\n\n### Reviewer identity\n\nThe requested authoring reviewer was gpt-6.1-luna; the available reviewer ID was gpt-6-luna at high reasoning effort. Reviewer work is outside measured solver requests and tokens.\n'
    operational_history+='\n\n### Frozen operational fields and scientific inference\n\nThe frozen operational metrics retain every scheduled slot, with unavailable success absent for execution accounting. Their nominal primary_decision field is preserved for replay compatibility. The report uses the separately declared all-completion amended scientific decision, not that nominal field. Per-answer curation retains observed partners of incomplete pairs; only complete-pair inference omits their source. Scoring and parsing are unchanged.\n'
    records_text=('### Collection interruptions\n\n'
                  f'Controller interruptions left {s.get("n_unavailable_outcomes",0)} outcomes unknown across {unavailable_pairs} incomplete pairs. A timeout and a provider capacity error are known unusable follow-ups, counted as non-recovery and excluded from wrong-value diagnostics. No recorded request was repeated. '
                  'The missing-outcome rule was fixed before recovery results were inspected. Full chronology, request identities and amendments are in [the protocol](data/scale_v5/PROTOCOL.md) and [detailed operational record](data/scale_v5/presentation_results/run_records.md).\n\n'
                  )
    detailed_usage=take('Calls, tokens and reproducible evidence')
    usage=report.get('raw_metrics',report['metrics'])['usage']
    usage_rows=[]
    for arm,item in usage['by_arm'].items():
        usage_rows.append('| '+arm.replace('_',' ')+' | '+str(item['physical_cli_requests'])+' | '+str(item['tokens'].get('input_tokens','Unknown'))+' | '+str(item['tokens'].get('output_tokens','Unknown'))+' | '+(f"{item['median_request_seconds']:.2f}" if item['median_request_seconds'] is not None else 'Unknown')+' |')
    records_text+='''### Calls, tokens and spend

| Main request group | Request slots | Input tokens | Output tokens | Median seconds/request |
| --- | --- | --- | --- | --- |
'''+ '\n'.join(usage_rows)+f'''

Usage is present for {usage['requests_with_usage']} main requests and missing for {usage['requests_missing_usage']}. Dollar spend is unavailable, not zero. Input and output are separate components; cached-input and reasoning tokens must not be added again to totals that already include them. These counts cover this study, excluding earlier demonstrations and authoring/review agents. The [detailed usage record](data/scale_v5/presentation_results/run_records.md) preserves reconnect counts, request accounting and cache-reading instructions.
'''
    assert len(used)==len(parts), 'Ungrouped narrative headings: '+str([title for i,(title,_) in enumerate(parts) if i not in used])
    titles=['The records and their answer key','Setup and independent source validation','Comparing the two correction methods',
            'Replaying the saved model calls','Results and uncertainty','Worked records, errors and correction data',
            'Why further improvement is difficult','What the evidence supports','Reproduction and run records',
            'Future work and further reading']
    def heading(number): return '## '+str(number)+'. '+titles[number-1]
    contents='## Contents\n\n'+'\n'.join('- ['+str(i)+'. '+title+'](#'+re.sub(r'[^\w -]','',str(i)+'. '+title).lower().replace(' ','-')+')' for i,title in enumerate(titles,1))
    contents+='\n\n'+workflow+'\n\nOne selected original error travels to both follow-ups. Each sees the same source record. The repair also receives the exact old answer and the checked names of failed fields. The two follow-ups never see one another’s result.'
    config = """# Default execution uses saved data only. Optional live demonstration stays small.
import json
from pathlib import Path
SCALE_LIVE = False
N_SCALE_LIVE_PILOT_CASES = 2
SCALE_MODELS = ["gpt-6.1-sol"]
"""
    notebook={'cells':[],'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
        'language_info':{'name':'python','version':'3.13'}},'nbformat':4,'nbformat_minor':5}
    opening=[cell(INTRODUCTION),cell(summary),cell(contents),cell(heading(1)+'\n\n'+data_text)]
    setup_intro=cell(heading(2)+'\n\nThe exact generator, source readers and scoring rules are defined below. Each source has a numerical answer before Sol is called. Independent readers reconstruct that answer from the text actually supplied, checking that the task does not depend on hidden facts. This offline replay repeats those checks. No new model request is needed.')
    cells = []
    for filename in ('scale_transport.py', 'scale_fixtures.py', 'scale_parallel.py', 'scale_experiment.py'):
        cells += [cell('### Embedded ' + filename.replace('_', ' ').replace('.py', '') +
                       '\n\nThese frozen definitions preserve the preregistered requests, sources, dispatch and checks. Defining them makes no model calls.'),
                  cell((BASE / filename).read_text(encoding='utf-8'), 'code')]
    cores = {name: (BASE / name).read_text(encoding='utf-8') for name in
             ('high_fixtures.py', 'high_material_audit.py', 'audit_high_rendered_sources.py')}
    embedded = ('# All source/verification code is embedded, with isolated namespaces.\n'
                'SCALE_EMBEDDED_CORES = ' + repr(cores) + '\n'
                'SCALE_CORE_CHECK = scale_load_cores(core_sources=SCALE_EMBEDDED_CORES)\n'
                'SCALE_FREEZE = json.loads((Path.cwd()/"data/scale_v5/source_freeze.json").read_text(encoding="utf-8"))\n'
                'SCALE_RUNTIME_SOURCE_HASHES = SCALE_FREEZE["source_sha256"]\n'
                'print(SCALE_CORE_CHECK)\n')
    cells += [cell('### Embedded independent source readers\n\nThree separately isolated source readers are stored inside this notebook. Their hashes must match before any replay.'), cell(embedded, 'code')]
    resume_source = (BASE / 'scale_resume.py').read_text(encoding='utf-8')
    resume_code = ('# A separate infrastructure amendment preserves every prior request.\n'
                   'SCALE_RESUME_SOURCE = ' + repr(resume_source) + '\n'
                   'SCALE_RESUME_NAMESPACE = {"__name__": "scale_notebook_reviewed_resume"}\n'
                   'exec(compile(SCALE_RESUME_SOURCE, "scale_resume.py", "exec"), SCALE_RESUME_NAMESPACE)\n'
                   'SCALE_RESUME_STATE = SCALE_RESUME_NAMESPACE["scale_resume_install"](\n'
                   '    Path.cwd(), Path.cwd()/"data/scale_v5/infrastructure_resume/amendment_001.json", namespace=globals())\n'
                   'print("Reviewed infrastructure amendment:", SCALE_RESUME_STATE["amendment_sha256"])\n')
    cells += [cell('### Preserve the recorded infrastructure interruption\n\nOne original provider capacity failure is replayed from its exact cache without a new request. This companion preserves its failure row; new service failures still stop dispatch. Full run history is in [the protocol](data/scale_v5/PROTOCOL.md).'), cell(resume_code, 'code')]
    intervention_resume_source = (BASE / 'scale_intervention_resume.py').read_text(encoding='utf-8')
    interruption_code = ('# Four raw pending records remain unchanged and are never reissued.\n'
                         'SCALE_INTERVENTION_RESUME_SOURCE = ' + repr(intervention_resume_source) + '\n'
                         'SCALE_INTERVENTION_RESUME_NAMESPACE = {"__name__": "scale_notebook_intervention_resume"}\n'
                         'exec(compile(SCALE_INTERVENTION_RESUME_SOURCE, "scale_intervention_resume.py", "exec"), SCALE_INTERVENTION_RESUME_NAMESPACE)\n'
                         'SCALE_INTERVENTION_RESUME_STATE = SCALE_INTERVENTION_RESUME_NAMESPACE["scale_intervention_resume_install"](\n'
                         '    Path.cwd(), Path.cwd()/"data/scale_v5/intervention_resume/amendment_002.json", namespace=globals())\n'
                         'print("Reviewed unavailable-outcome amendment:", SCALE_INTERVENTION_RESUME_STATE["amendment_sha256"])\n')
    cells += [cell('### Preserve the unavailable follow-up outcomes\n\nThis companion defines the first overlay for records with no saved outcome. It preserves raw pending bytes and never invents a model answer, completion time or usage.'), cell(interruption_code, 'code')]
    second_source = (BASE / 'scale_intervention_resume_003.py').read_bytes().decode('utf-8')
    second_code = ('# Preserve the second interrupted wave as well as the first.\n'
                   'SCALE_INTERVENTION_RESUME_003_SOURCE = ' + repr(second_source) + '\n'
                   'SCALE_INTERVENTION_RESUME_003_NAMESPACE = {"__name__": "scale_notebook_intervention_resume_003", "SCALE_INTERVENTION_PREDECESSOR_SOURCE": SCALE_INTERVENTION_RESUME_SOURCE}\n'
                   'exec(compile(SCALE_INTERVENTION_RESUME_003_SOURCE, "scale_intervention_resume_003.py", "exec"), SCALE_INTERVENTION_RESUME_003_NAMESPACE)\n'
                   'SCALE_INTERVENTION_RESUME_003_STATE = SCALE_INTERVENTION_RESUME_003_NAMESPACE["scale_intervention_resume_003_install"](\n'
                   '    Path.cwd(), Path.cwd()/"data/scale_v5/intervention_resume_003/amendment_003.json", namespace=globals())\n'
                   'SCALE_INTERVENTION_RESUME_STATE = SCALE_INTERVENTION_RESUME_003_STATE\n'
                   'print("Second reviewed interruption amendment:", SCALE_INTERVENTION_RESUME_003_STATE["amendment_sha256"])\n')
    cells += [cell('### Preserve the earlier missing-data declaration\n\nThis frozen companion retains the earlier interruption declaration and its pending bytes. The final missing-data analysis is specified separately below; the full chronology is in the protocol.'), cell(second_code, 'code')]
    fourth_source = (BASE / 'scale_intervention_resume_004.py').read_bytes().decode('utf-8')
    fourth_code = ('# Preserve the recorded terminal timeout without requesting another answer.\n'
                   'SCALE_INTERVENTION_RESUME_004_SOURCE = ' + repr(fourth_source) + '\n'
                   'SCALE_INTERVENTION_RESUME_004_NAMESPACE = {"__name__": "scale_notebook_intervention_resume_004", "SCALE_INTERVENTION_004_PREDECESSOR_SOURCE": SCALE_INTERVENTION_RESUME_003_SOURCE, "SCALE_INTERVENTION_PREDECESSOR_SOURCE": SCALE_INTERVENTION_RESUME_SOURCE}\n'
                   'exec(compile(SCALE_INTERVENTION_RESUME_004_SOURCE, "scale_intervention_resume_004.py", "exec"), SCALE_INTERVENTION_RESUME_004_NAMESPACE)\n'
                   'SCALE_INTERVENTION_RESUME_004_STATE = SCALE_INTERVENTION_RESUME_004_NAMESPACE["scale_intervention_resume_004_install"](\n'
                   '    Path.cwd(), Path.cwd()/"data/scale_v5/intervention_resume_004/amendment_004.json", namespace=globals())\n'
                   'SCALE_INTERVENTION_RESUME_STATE = SCALE_INTERVENTION_RESUME_004_STATE\n'
                   'print("Reviewed terminal-timeout amendment:", SCALE_INTERVENTION_RESUME_004_STATE["amendment_sha256"])\n')
    cells += [cell('### Preserve a timed-out follow-up\n\nA recorded follow-up timeout remains known operational non-recovery even if the raw cache contains a parsed answer. The companion preserves its error, timing, return code and usage. It is excluded from wrong-value diagnostics. See [the protocol](data/scale_v5/PROTOCOL.md) for the recorded host sleep and temporary collection safeguards.'), cell(fourth_code, 'code')]
    fifth_source = (BASE / 'scale_intervention_resume_005.py').read_bytes().decode('utf-8')
    fifth_code = ('# Preserve both recorded service failures, with no request resubmission.\n'
                  'SCALE_INTERVENTION_RESUME_005_SOURCE = '+repr(fifth_source)+'\n'
                  'SCALE_INTERVENTION_RESUME_005_NAMESPACE = {"__name__": "scale_notebook_intervention_resume_005", "SCALE_INTERVENTION_005_PREDECESSOR_SOURCE": SCALE_INTERVENTION_RESUME_004_SOURCE, "SCALE_INTERVENTION_004_PREDECESSOR_SOURCE": SCALE_INTERVENTION_RESUME_003_SOURCE, "SCALE_INTERVENTION_PREDECESSOR_SOURCE": SCALE_INTERVENTION_RESUME_SOURCE}\n'
                  'exec(compile(SCALE_INTERVENTION_RESUME_005_SOURCE, "scale_intervention_resume_005.py", "exec"), SCALE_INTERVENTION_RESUME_005_NAMESPACE)\n'
                  'SCALE_INTERVENTION_RESUME_005_STATE = SCALE_INTERVENTION_RESUME_005_NAMESPACE["scale_intervention_resume_005_install"](\n'
                  '    Path.cwd(), Path.cwd()/"data/scale_v5/intervention_resume_005/amendment_005.json", namespace=globals())\n'
                  'SCALE_INTERVENTION_RESUME_STATE = SCALE_INTERVENTION_RESUME_005_STATE\n'
                  'print("Reviewed terminal-service-failure amendment:", SCALE_INTERVENTION_RESUME_005_STATE["amendment_sha256"])\n')
    cells += [cell('### Preserve the second terminal service failure\n\nA provider capacity error remains a known operational non-recovery, separate from wrong extracted values. This companion replays both known terminal errors without requesting another answer. The complete interruption history is in [the protocol record](data/scale_v5/PROTOCOL.md).'),cell(fifth_code,'code')]
    if report.get('intervention_interruption_amendment_006'):
        sixth_source=(BASE/'scale_intervention_resume_006.py').read_bytes().decode('utf-8')
        sixth_code=('# Preserve all nine unknown outcomes and both known service errors.\n'
                    'SCALE_INTERVENTION_RESUME_006_SOURCE = '+repr(sixth_source)+'\n'
                    'SCALE_INTERVENTION_RESUME_006_NAMESPACE = {"__name__": "scale_notebook_intervention_resume_006", "SCALE_INTERVENTION_006_PREDECESSOR_SOURCE": SCALE_INTERVENTION_RESUME_005_SOURCE, "SCALE_INTERVENTION_005_PREDECESSOR_SOURCE": SCALE_INTERVENTION_RESUME_004_SOURCE, "SCALE_INTERVENTION_004_PREDECESSOR_SOURCE": SCALE_INTERVENTION_RESUME_003_SOURCE, "SCALE_INTERVENTION_PREDECESSOR_SOURCE": SCALE_INTERVENTION_RESUME_SOURCE}\n'
                    'exec(compile(SCALE_INTERVENTION_RESUME_006_SOURCE, "scale_intervention_resume_006.py", "exec"), SCALE_INTERVENTION_RESUME_006_NAMESPACE)\n'
                    'SCALE_INTERVENTION_RESUME_006_STATE = SCALE_INTERVENTION_RESUME_006_NAMESPACE["scale_intervention_resume_006_install"](\n'
                    '    Path.cwd(), Path.cwd()/"data/scale_v5/intervention_resume_006/amendment_006.json", namespace=globals())\n'
                    'SCALE_INTERVENTION_RESUME_STATE = SCALE_INTERVENTION_RESUME_006_STATE\n'
                    'print("Reviewed final missing-data amendment:", SCALE_INTERVENTION_RESUME_006_STATE["amendment_sha256"])\n')
        cells += [cell('### Preserve the final missing-data declaration\n\nThe final companion binds nine unknown outcomes: four whole pairs and one partial pair. The observed partner stays fixed in every scheduled-cohort sensitivity calculation. It preserves all recorded bytes and makes no new requests.'),cell(sixth_code,'code')]
    preparation = '''# Reconstruct the fixed cohorts and pilot selection from committed artifacts.
SCALE_PILOT = scale_run_pilot(root=Path.cwd(), live=False)
SCALE_PREPARED = scale_prepare_main(root=Path.cwd())
print("Selected tier:", SCALE_PILOT["selected_tier"])
'''
    source_audit = '''# Recheck every potential main source, including uncalled collection slots.
# These independent readers use the supplied text, not a model response.
SCALE_RECHECKED_SOURCES = 0
for SCALE_BLOCK in SCALE_PREPARED["blocks"]:
    SCALE_BLOCK_COUNT = 0
    for SCALE_CASE in scale_iter_corpus(SCALE_PREPARED["directory"]/SCALE_BLOCK["source_path"], SCALE_BLOCK["manifest"]):
        SCALE_CASE_AUDIT = scale_audit_case(SCALE_CASE)
        assert SCALE_CASE_AUDIT["passed"]
        SCALE_BLOCK_COUNT += 1
    assert SCALE_BLOCK_COUNT == SCALE_BLOCK["manifest"]["n_cases"]
    SCALE_RECHECKED_SOURCES += SCALE_BLOCK_COUNT
assert SCALE_RECHECKED_SOURCES == 2144
print("Potential main sources independently rechecked:", SCALE_RECHECKED_SOURCES)
'''
    cells += [cell('### Reconstruct and recheck the supplied materials\n\nAll 2,144 potential main packets were audited before model calls. Replay repeats the independent text-based calculation for every packet, including sources never called after the stopping rule was met. The readers check version selection, dated shipment and return joins, units and exact price arithmetic. A disagreement stops the notebook.'), cell(preparation, 'code'), cell(source_audit, 'code')]

    setup_cells=[setup_intro,cell(config,'code')]+cells
    cells=[]
    replay = '''# Missing or altered caches stop execution. No CLI requests are permitted.
SCALE_ORIGINALS = scale_collect_originals(root=Path.cwd(), live=False)
SCALE_BUNDLE = scale_run_interventions(root=Path.cwd(), live=False)
print("Selected tier:", SCALE_PILOT["selected_tier"])
print("Collection originals correct:", SCALE_BUNDLE["metrics"]["original_collection"]["value_correct_valid_schema"], "/", SCALE_BUNDLE["metrics"]["original_collection"]["n_attempted_cases"])
print("Fixed audit correct:", SCALE_BUNDLE["metrics"]["audit"]["value_correct_valid_schema"], "/", SCALE_BUNDLE["metrics"]["audit"]["n_attempted_cases"])
print("Scheduled failure pairs:", SCALE_BUNDLE["manifest"]["n_selected"])
print("Unavailable follow-up outcomes:", len(SCALE_INTERVENTION_RESUME_STATE["approved"]))
print("The analysis below uses complete observed pairs and all possible unavailable outcomes.")
'''
    cells += [cell('### Replay the complete saved study\n\nThe difficulty selection, fixed original batches, random failure ranking and both follow-ups are reconstructed from the full request caches under the original plan and its recorded amendments. This cell uses live=False throughout.'), cell(replay, 'code')]
    cells += [cell('### Embedded presentation code\n\nThis code checks the completed bundle and builds readable examples and figures. It refuses to inspect partial intervention outcomes.'),
              cell(proposal['helper_source'], 'code'),
              cell('### Rebuild the presentation offline\n\nThe following cell recreates only the new study figures from completed cached evidence.'),
              cell(proposal['replay_code'], 'code')]
    reproduction = """### Reproduce and inspect the saved study

Run [the notebook](23_synthetic_data_curation.ipynb) from this folder. Definitions and saved request caches are self-contained; ordinary execution makes no new model calls.

```powershell
python -m nbconvert --to notebook --execute --ExecutePreprocessor.timeout=1200 --inplace 23_synthetic_data_curation.ipynb
python -m unittest discover -s data/scale_v5/source_snapshot -p "test_scale*.py"
python -m unittest discover -s data/scale_v5/intervention_resume_005/source_snapshot -p "test_scale_intervention_resume_005.py"
python -m unittest discover -s data/scale_v5/intervention_resume_005/source_snapshot -p "test_scale_detached_worker_005.py"
```

The [protocol](data/scale_v5/PROTOCOL.md) records the plan and its amendments. The [source audit](data/scale_v5/scale_main_material_review.json) and [failure review](data/scale_v5/scale_original_failure_review.json) check solvability and eligibility; the [artifact audit](data/scale_v5/artifact_audit.json) connects exports to raw caches. All missing-outcome completions are saved in [the analysis JSON](data/scale_v5/presentation_results/missing_outcome_analysis.json).

The live demonstration defaults off. Enabling it permits a small new difficulty check in a separate ignored folder. It never replaces committed evidence. Frozen runtime and mocked reporting tests make no model calls.
"""
    reproduction += '\n\n### How the study got here\n\nAn earlier 45-pair comparison was too uncertain to settle whether the repair package helped. Its evidence stays in `data/high_v4/` and is not pooled here. This study increased history length after a separate difficulty check and fixed a 600-failure target before comparing corrections.\n'
    if report.get('intervention_interruption_amendment_006'):
        reproduction=reproduction.replace('intervention_resume_005/source_snapshot','intervention_resume_006/source_snapshot').replace('test_scale_intervention_resume_005.py','test_scale_intervention_resume_006.py').replace('test_scale_detached_worker_005.py','test_scale_detached_worker_006.py')
    replay_cells=[cell(heading(4)+'\n\nThe following code reconstructs the original collection and both follow-ups from exact request caches. An altered or missing response stops replay. The charts and examples are then rebuilt from the completed comparison, with the unavailable outcomes handled by the fixed analysis plan.')]+cells
    cells=[]
    smoke = '''# Explicit, small new pilot only; never replaces the frozen study.
if SCALE_LIVE:
    import uuid
    assert SCALE_MODELS == ["gpt-6.1-sol"]
    assert 1 <= N_SCALE_LIVE_PILOT_CASES <= 16
    SCALE_SMOKE_ROOT = Path.cwd()/"data/tmp"/("scale_smoke_"+uuid.uuid4().hex[:12])
    SCALE_SMOKE = scale_run_pilot({"n_cases":N_SCALE_LIVE_PILOT_CASES,
        "min_value_failures":min(6,N_SCALE_LIVE_PILOT_CASES)}, root=SCALE_SMOKE_ROOT, live=True)
else:
    print("No new CLI calls: SCALE_LIVE is False.")
'''
    cells += [cell('### Optional small new pilot\n\nThe top-level SCALE_LIVE flag defaults to False. With two cases per tier, the optional demonstration permits at most four new CLI requests and writes to a new ignored folder. It does not start main collection or repairs.'), cell(smoke, 'code')]
    spend_code = '''# Observed components only. Cached input/reasoning tokens are not extra totals.
from collections import Counter
SCALE_OBSERVED_TOKENS = Counter(SCALE_BUNDLE["metrics"]["usage"]["overall"])
SCALE_MISSING_USAGE = SCALE_BUNDLE["metrics"]["usage"]["requests_missing_usage"]
for SCALE_PILOT_TIER in SCALE_PILOT["tiers"]:
    SCALE_OBSERVED_TOKENS.update(SCALE_PILOT_TIER["metrics"]["usage"]["overall"])
    SCALE_MISSING_USAGE += SCALE_PILOT_TIER["metrics"]["usage"]["requests_missing_usage"]
SCALE_REQUEST_SLOTS = SCALE_BUNDLE["manifest"]["total_pilot_plus_main_requests"]
SCALE_UNAVAILABLE_SLOTS = len(SCALE_INTERVENTION_RESUME_STATE["approved"])
print("V5 pilot + main scheduled request slots:", SCALE_REQUEST_SLOTS)
print("Terminal CLI records:", SCALE_REQUEST_SLOTS-SCALE_UNAVAILABLE_SLOTS)
print("Attempt slots with unknown physical launch/outcome:", SCALE_UNAVAILABLE_SLOTS)
print("Physical CLI start-count bounds:", [SCALE_REQUEST_SLOTS-SCALE_UNAVAILABLE_SLOTS, SCALE_REQUEST_SLOTS])
print("Observed token components:", dict(SCALE_OBSERVED_TOKENS))
print("Requests without usage:", SCALE_MISSING_USAGE)
print("USD spend: unknown. Subscription CLI billing is not exposed; unknown is not zero.")
print("Authoring and review agent usage is outside these experiment CLI counters.")
'''
    cells += [cell('### Recorded V5 usage\n\nThese totals include the pilot, all called originals, the fixed audit and both follow-ups. They exclude earlier protocols and authoring or review agent work. Token subcomponents are displayed separately so they are not charged twice in a calculation.'),
              cell(spend_code, 'code')]

    run_record_cells=[cell(heading(9)+'\n\n'+records_text+'\n\n'+reproduction)]+cells
    notebook['cells']=(opening+setup_cells+[cell(heading(3)+'\n\n'+method_text)]+replay_cells+
        [cell(heading(5)+'\n\n'+results_text),cell(heading(6)+'\n\n'+examples_text),
         cell(heading(7)+'\n\n'+improvement_text),cell(heading(8)+'\n\n'+limits_text)]+
        run_record_cells+[cell(future)])
    for entry in notebook['cells']:
        if entry['cell_type']=='markdown':
            source=''.join(entry['source']).replace('2,144',f'{potential_main_count:,}')
            match=re.search(r'^## (\d+\. [^\n]+)',source,re.M)
            if match:
                slug=re.sub(r'[^\w -]','',match.group(1)).lower().replace(' ','-')
                source=source[:match.end()]+'\n\n<a id="'+slug+'"></a>'+source[match.end():]
                entry['source']=source.splitlines(keepends=True)
    assert len({entry['id'] for entry in notebook['cells']})==len(notebook['cells'])
    (ROOT/'23_synthetic_data_curation.ipynb').write_text(json.dumps(notebook,ensure_ascii=False,indent=1)+'\n',encoding='utf-8',newline='\n')
    setup_readme='The notebook embeds the generator, source readers, request profile and checker. It rechecks every potential source before replaying saved responses. Reproduction commands appear in section 9.'
    replay_readme=f'The saved requests reconstruct selection and both follow-ups without model calls. All {s.get("n_unavailable_outcomes",0)} unknown outcomes retain their pending bytes. Known service failures remain separate from wrong values; the predeclared rule checks every hypothetical missing result.'
    sections=[INTRODUCTION,summary,contents,heading(1),data_text,heading(2),setup_readme,
              heading(3),method_text,heading(4),replay_readme,heading(5),results_text,
              heading(6),examples_text,heading(7),improvement_text,heading(8),limits_text,
              heading(9),records_text,reproduction,future]
    (ROOT/'README.md').write_text(polish_reader_text(('\n\n'.join(sections)+'\n').replace('2,144',f'{potential_main_count:,}')),encoding='utf-8',newline='\n')
    run_record_path=DATA/'presentation_results/run_records.md'
    run_record_path.parent.mkdir(exist_ok=True)
    run_record_path.write_text('# Detailed collection record\n\n'+(operational_history+'\n\n'+detailed_usage).replace('](data/scale_v5/','](../')+'\n',encoding='utf-8',newline='\n')
    (run_record_path.parent/'design_details.md').write_text('# Source rules and study design\n\n'+design_details.replace('](data/scale_v5/','](../')+'\n',encoding='utf-8',newline='\n')
    rows = (REPO / 'README.md').read_text(encoding='utf-8').splitlines()
    for i, row in enumerate(rows):
        if row.startswith('| 23 |') and '[Synthetic data generation and curation](notebooks/23-synthetic-data-curation/)' in row:
            rows[i] = (f'| 23 | [Synthetic data generation and curation](notebooks/23-synthetic-data-curation/) | '
                       f'Practice examples need checked answers so later training does not reward mistakes. On {collection["n_attempted_cases"]:,} new fictional order histories and {audit["n_attempted_cases"]} separate audit histories, does Sol correct more of its own mistakes when shown its old answer and verified failed-field labels than when asked again without them? | '
                       f'Originals correct: {collection["value_correct_valid_schema"]:,}/{collection["n_attempted_cases"]:,}. Of {scheduled} scheduled failure pairs, {n} have both outcomes and {unavailable_pairs} are unavailable. Fresh retry recovered {fresh}/{n}; feedback repair {repair}/{n}. '
                       + plain_effect + conclusion + ' Every potential source was independently audited before calls. No training. |')
        if row.startswith('* Notebook 23 replays') or row.startswith('* Notebook 23 runs offline'):
            rows[i] = '* Notebook 23 replays its completed protocols offline, including the preregistered larger paired study. It preserves all prior caches, verifies source solvability and keeps live demonstrations small and opt-in.'
    (REPO / 'README.md').write_text('\n'.join(rows)+'\n', encoding='utf-8', newline='\n')
    output = DATA / 'presentation_source'
    output.mkdir(exist_ok=True)
    for name in ('scale_reporting.py', 'refresh_scale_report.py', 'scale_missing_outcomes.py', 'scale_missing_outcomes_003.py', 'scale_missing_outcomes_006.py', 'test_scale_missing_outcomes_006.py',
                 'test_scale_reporting_observed_006.py','test_finalize_scale_standalone.py','scale_reporting_reading_v2_mock_tests.log',
                 'test_scale_reporting_missing.py', 'scale_reporting_missing_unit_tests.log',
                 'scale_reporting_missing_003_unit_tests.log',
                 'scale_reporting_transport_004_unit_tests.log',
                 'scale_reporting_transport_005_mock_tests.log',
                 'finalize_scale.py', 'audit_scale_artifacts.py'):
        shutil.copy2(BASE / name, output / name)
    for name in ('scale_transport.py', 'scale_fixtures.py', 'scale_parallel.py', 'scale_experiment.py',
                 'high_fixtures.py', 'high_material_audit.py', 'audit_high_rendered_sources.py',
                 'test_scale_experiment.py', 'scale_power_plan.json'):
        shutil.copy2(DATA / 'source_snapshot' / name, output / name)
    build(root=ROOT, write=True)
    readme_bytes=(ROOT/'README.md').stat().st_size
    assert 25000<=readme_bytes<=50000, f'Review the actual README size: {readme_bytes} bytes'
    print(json.dumps({'completed': True, 'notebook_cells': len(notebook['cells']), 'selected_pairs': n,
                      'figures': len(proposal['figures']), 'headline': proposal['headline']}))


if __name__ == '__main__':
    main()
