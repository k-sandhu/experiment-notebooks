from pathlib import Path
import nbformat
import textwrap

root = Path(__file__).resolve().parents[1]
data = root / 'data'
nb = nbformat.v4.new_notebook()
cells = []

def md(heading, text):
    cells.append(nbformat.v4.new_markdown_cell(heading + '\n\nNARRATIVE TODO: ' + text))

def code(text):
    cells.append(nbformat.v4.new_code_cell(text))

def source(name, message):
    code((data / name).read_text(encoding='utf-8') + '\nprint(' + repr(message) + ')')

md('# A weaker model as tie-breaker between strong judges', 'Claude writes the complete reader-facing narrative. Introduce why people compare model answers and use independent judges. Do not open with model names or results.')
md('## 1. Choosing between conflicting judgments', 'Build a labelled illustrative example gradually: ordinary correctness check, one complication, two strong judges disagree, smaller model either checks the pair alone or reads both reasons. Explain why a persuasive wrong reason matters.')
md('## 2. Question and study summary', 'State the actual cohort and disagreement counts from data/route_summary.csv, expected half-credit scoring for splits, unreadable-failure and unreadable-coin variants, the reasons-versus-alone headline from paired_comparisons.csv and one main caveat. Explain accuracy before giving numbers. Give original/new/all results, family concentration and the zero-error upper bound when applicable.')
md('## Contents', 'Keep these links and add a short reading guide.\n\n' + '\n'.join('- ['+title+'](#'+title.lower().replace('.','').replace(',','').replace(' ','-')+')' for title in [
    '1. Choosing between conflicting judgments','2. Question and study summary','3. Setup and models','4. Frozen exam and disagreement set',
    '5. Tie-breakers and reading rules','6. Collection and worked example','7. Tie-breaker accuracy','8. Full rules, costs and reviews',
    '9. Reasons, families and revision','10. Error analysis','11. Limitations','12. How to reproduce','13. Future work and further reading']))
md('## Workflow', 'Add a Mermaid diagram before code: original 240 pairs plus frozen sequential 120-pair batches -> Opus and Sol each in both orders -> agree/disagree/missing routes -> selected tie-breaker calls -> strict and lenient readers -> item-cluster intervals and full rules. Counts are in stopping_history.json, route_summary.csv and usage_ledger.csv. Explain one item travelling through it.')
md('## 3. Setup and models', 'Explain replay default, small live smoke default, full profile knobs and USD5 guard. Insert models table from data/models.json including provider, pin limitations, size/precision, settings, date/source and rationale for this notebook. Update generic notebook33 rationales to the actual roles here.')
source('setup34.py', 'Setup ready')
source('transport34.py', 'Cache loaded; per-key locks and backend concurrency limits ready')
md('## 4. Frozen exam and disagreement set', 'Explain unchanged level10 generator, code/exact ground truth, writer-derived candidates, new seed, stopping selection and cohort differences. Show actual inputs with stable IDs. Explain missing versus split, label-preserving order mapping, batch freezes and fresh-date provenance. Use from_33/SOURCE.md, freeze_record.json, batch freeze files, date_provenance.json and route_summary.csv.')
source('generator34.py', 'Unchanged notebook33 generator defined locally')
md('## 5. Tie-breakers and reading rules', 'Compare all methods in plain language before technical names. Show exact prompt excerpts from prompt_templates.json and strict/lenient rules from from_33/reading_rules_v1.py. Explain split half credit and unreadable policies. Explain confidence ties, strict fixed-route sensitivity, revision unresolved/human fallback. Add model call graph and two-agent revision sequence diagram, with original calls, parallel independent revision calls, one wait and no extra round.')
source('from_33/reading_rules_v1.py', 'Unchanged strict and lenient readers defined locally')
source('design34.py', 'Study design and call graph implemented')
md('## 6. Collection and worked example', 'Show the exact task and candidates, both original judgments and same-order reasons, randomized Judge1/2 labels, raw weak reply, strict/lenient parse and item score for one end-to-end item in worked_examples.json. Keep run bookkeeping in PROTOCOL.md. The collector below resumes from its complete-request cache.')
code("try:\n    items, rows, routes = run_study()\nexcept CollectorQuotaStop:\n    quota_handoff()\n    raise\nprint('Items',len(items),'judgments',len(rows),'disagreements',sum(r['route']=='disagreed' for r in routes))")
md('## 7. Tie-breaker accuracy', 'Explain the headline chart, expected half credit, item-cluster bootstrap intervals and paired same-item comparisons. Separate readable wrong, split, unreadable and unresolved counts. Use tie_breakers.csv, reply_summary.csv, unreadable_summary.csv, paired_comparisons.csv and figures/headline.png. Discuss original/new/all cohorts and readable-only ranking, ceilings and floors.')
source('analysis34.py', 'Analysis, item-cluster intervals and figure functions ready')
code("tables = summarize_study(items,rows,routes)\nfigures34(tables)\ndisplay(tables['route_summary'])\ndisplay(tables['tie_breakers'])\nfrom IPython.display import Image\ndisplay(Image(filename=str(FIG/'headline.png')))")
md('## 8. Full rules, costs and reviews', 'Use full_rules.csv and figures/full_rule_cost.png to compare expected accuracy, four baseline calls per item plus method calls, actual attempts, returned OpenRouter dollars, labelled CLI list/proxy estimates and human reviews. Distinguish reuse/incremental collection spend from economic full-rule cost. Humans are assumed correct and unpriced; unresolved revision is separate from human fallback.')
code("display(tables['full_rules'])\ndisplay(Image(filename=str(FIG/'full_rule_cost.png')))\nledger, spend = spend_tables()\ndisplay(spend)")
md('## 9. Reasons, families and revision', 'Use reasons_alignment.csv and reasons_alignment_summary.csv for same-order different-verdict cases, with denominators and item-cluster intervals. Report whether weak verdicts match the right/longer/more confident/first judge, without causal claims. Use family_results.csv and trap_results.csv with sparse flags and counts. Explain which strong judge moved using revision_moves.csv. Discuss instruction concentration and thin code/trap evidence.')
code("display(tables['paired_comparisons'].query(\"cohort=='all' and reader=='lenient' and unreadable_policy=='failure'\"))\ndisplay(tables['reasons_alignment_summary'])\ndisplay(tables['family_results'])\ndisplay(tables['revision_moves'].groupby('judge')[['moved','improved','harmed']].sum())\ndisplay(Image(filename=str(FIG/'reasons_vs_alone.png')))\ndisplay(Image(filename=str(FIG/'disagreement_families.png')))")
md('## 10. Error analysis', 'Select at least five measured examples from worked_examples.json: end-to-end, ordinary success, reasons helped, reasons harmed or closest available, hard disagreement and agreed-both-wrong if observed. Say when an example category is absent. Show expected/observed answers and checker evidence. Inspect unreadable_examples.json, including Haiku policy blocks and strict code fences. Give selection rules/eligible_n and aggregate frequency. Do not infer persuasion caused an error merely because the wrong argument was longer.')
code("worked_cases(items,rows,routes,tables)\ndisplay(tables['unreadable_summary'])\nexamples = load(DATA/'worked_examples.json')\ndisplay(pd.DataFrame([{k:v for k,v in e.items() if k not in ('item','replies')} for e in examples]))\ndisplay(Image(filename=str(FIG/'reply_outcomes.png')))")
md('## 11. Limitations', 'Explain synthetic verified mutations, selected disagreements and optional stopping, original/new difficulty and writer construction, shared errors hidden from tie-breakers, zero observed agreed errors versus 95% upper bound, sparse traps, policy refusals, strict-route sensitivity, human oracle assumption and finite code-test domain. Link analysis_plan.json and PROTOCOL.md for what was fixed before results and any engineering amendments.')
md('## 12. How to reproduce', 'Give PowerShell replay and live commands from HANDOFF.md; replay makes zero network/model calls. Explain dependencies, small default live profile, full profile, source and per-batch hashes, caches keyed by complete request, quota stop/resume and USD5 accounting. Put final spend and collection wall time here, not in opening.')
supplement=(data/'supplemental34.py').read_text(encoding='utf-8').replace('root=Path(__file__).resolve().parents[1]','root=Path.cwd()')
code('def export_supplements():\n'+textwrap.indent(supplement,'    ')+'\nexport_supplements()')
code("validate34(items,rows,routes,tables)\nprint('OpenRouter accounted USD:',round(accounted_openrouter(),6),'| new calls this execution:',new_calls)")
code("ledger = pd.read_csv(DATA/'usage_ledger.csv')\ncli_mask = ledger.backend.isin(OPTIONS)\nprint('OpenRouter returned USD:',round(ledger.openrouter_usd.sum(),6))\nprint('OpenRouter unpriced returned-attempt reserves USD:',round(ledger.unpriced_reservation_usd.sum(),6))\nprint('Interrupted unknown OpenRouter reserves USD:',load(DATA/'interrupted_attempts.json')['total_reservation_usd'])\nprint('CLI returned invocations:',int(cli_mask.sum()),'| estimated list/proxy USD:',round(ledger.loc[cli_mask,'cli_estimated_list_usd'].sum(),6))\nprint('Invocation wall span, seconds including idle gaps:',round((pd.to_datetime(ledger.completed_at,utc=True).max()-pd.to_datetime(ledger.started_at,utc=True).min()).total_seconds(),1))\nprint('New calls in this executed replay:',new_calls)")
md('## 13. Future work and further reading', 'Claude: last numbered section. Add ### Future work with 3-5 experiments tied to measured limitations (more code disagreements, independently sampled natural errors, structured count evidence, randomized reasons interventions). Add ### Further reading with 3-6 canonical linked papers/docs and the date links were opened. Khan et al. 2024 was opened on 2026-10-30; see data/sources_checked.json.')
nb['cells'] = cells
nb['metadata'] = dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),language_info=dict(name='python',version='3.11'))
nbformat.write(nb,root/'34_weak_tiebreakers.ipynb')
print('Notebook built:',len(cells),'cells')
