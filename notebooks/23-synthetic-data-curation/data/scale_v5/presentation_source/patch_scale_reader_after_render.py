"""Synchronize final prose after rendering; no bootstrap, model or scoring call."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import gzip

import finalize_scale as finalizer
import refresh_scale_report as refresh

BASE=Path(__file__).resolve().parent
ROOT=finalizer.ROOT
DATA=ROOT/'data/scale_v5'
status=json.loads((BASE/'scale_intervention_006_operational_status.json').read_bytes())
assert status['complete'] and status['processed_arm_slots']==1200 and status['new_transport_failure_events']==0
analysis=json.loads((DATA/'presentation_results/missing_outcome_analysis.json').read_bytes())
assert analysis['n_observed_pairs']==595 and analysis['n_completions']==512
metrics=json.loads((DATA/'main/metrics.json').read_bytes())
protocol=json.loads((DATA/'main/protocol.json').read_bytes())
namespace,helper=refresh.scale_report_namespace(ROOT)
originals=namespace['scale_report_rows'](DATA/'main/candidates.jsonl')
operational=namespace['scale_report_rows'](DATA/'main/interventions.jsonl')
observed=set(analysis['observed_case_ids'])
scientific=[namespace['scale_report_diagnostic_row'](row) for row in operational if row['case_id'] in observed]
gold={}
for block in protocol['blocks']:
    for case in namespace['scale_iter_corpus'](DATA/'main'/block['source_path'],block['manifest']):
        gold[case['case_id']]=case['gold']
selection=json.loads((DATA/'main/selection.json').read_bytes())
selection['selected_case_ids']=analysis['observed_case_ids']
report={'root':str(ROOT),'originals':originals,'interventions':scientific,
        'operational_interventions':operational,'selection':selection,
        'source_metadata':{cid:{'gold':answer} for cid,answer in gold.items()}}
readme_path=ROOT/'README.md';text=readme_path.read_text(encoding='utf-8')
report['examples']=[{'case_id':cid} for _,cid in re.findall(r'^#### Case (\d+): .*?, (account-\S+)',text,re.M)]
assert len(report['examples'])==5
error=namespace['scale_report_error_markdown'](report)
nulls=sum(r['split']=='collection' and not r['transport_error'] and r['verification']['valid_schema'] and r['response']['answer']['quantity_units'] is None for r in originals)
wrong=metrics['original_collection']['wrong_field_counts']['quantity_units']
assert nulls==27 and wrong-nulls==705
error+=f'\n\nOf {wrong} wrong original quantities, {nulls} were legal JSON null answers and {wrong-nulls} were wrong numbers. Null is a readable abstention, but it is incorrect against these fully specified records. These null answers are not format failures; unreadable service outcomes are counted separately.'
error+='\n\n'+finalizer.timeout_example(DATA,gold)
prompt=namespace['scale_report_prompt_markdown'](report)
with gzip.open(DATA/'main/exports/curated_unique.jsonl.gz','rt',encoding='utf-8') as stream:
    accepted=sum(bool(line.strip()) for line in stream)
assert accepted==579
training=finalizer.training_context_text(metrics['original_collection'],analysis['paired_value_recovery'],
    sum(b['manifest']['n_cases'] for b in protocol['blocks']),accepted,analysis['fresh_recovered'],analysis['repair_recovered'])
oracle='The generator already knows every correct answer and could label packets directly; model calls measure errors and correction yield, without establishing a cheaper way to create labels.'

def patch(markdown):
    markdown=re.sub(r'(?s)(#### Case 1: Original success,.*?)(?=\n\n## |\Z)',lambda m:m.group(1).replace('Unavailable','Not run'),markdown)
    markdown=re.sub(r'(?s)### Inspect the supplied CLI inputs for Case \d+.*?(?=\n\n!\[Audited quantity calculation)',lambda _:prompt.rstrip(),markdown)
    markdown=re.sub(r'(?s)### Error size, type and newly damaged fields.*?(?=\n\n!\[Absolute quantity)',lambda _:error.rstrip(),markdown)
    markdown=re.sub(r'(?s)### From checked corrections to a training experiment.*?(?=\n\n## 8\.|\Z)',lambda _:training.rstrip(),markdown)
    if '## 8. What the evidence supports' in markdown and oracle not in markdown:
        end=markdown.find('\n\n## 9.')
        if end<0:markdown=markdown.rstrip()+'\n\n'+oracle+'\n'
        else:markdown=markdown[:end].rstrip()+'\n\n'+oracle+'\n\n'+markdown[end:].lstrip()
    return finalizer.polish_reader_text(markdown)

patched=patch(text)
notebook_path=ROOT/'23_synthetic_data_curation.ipynb'
notebook=json.loads(notebook_path.read_bytes())
for cell in notebook['cells']:
    source=''.join(cell['source'])
    if cell['cell_type']=='markdown':source=patch(source)
    elif 'def scale_report_load(' in source and 'SCALE_MISSING_006_VERSION' in source:source=helper
    else:continue
    cell['source']=source.splitlines(keepends=True)
    cell['id']='scale-final-'+hashlib.sha256(source.encode()).hexdigest()[:14]
assert len({cell['id'] for cell in notebook['cells']})==len(notebook['cells'])
for cell in notebook['cells']:
    if cell['cell_type']=='code':compile(''.join(cell['source']),'final-notebook-cell','exec')
assert 25000<=len(patched.encode())<=50000,len(patched.encode())
readme_path.write_text(patched,encoding='utf-8',newline='\n')
temporary=notebook_path.with_suffix('.ipynb.tmp')
temporary.write_text(json.dumps(notebook,ensure_ascii=False,indent=1)+'\n',encoding='utf-8',newline='\n')
temporary.replace(notebook_path)
for name in ('finalize_scale.py','scale_reporting.py','refresh_scale_report.py','patch_scale_reader_after_render.py'):
    shutil.copy2(BASE/name,DATA/'presentation_source'/name)
print(json.dumps({'readme_bytes':readme_path.stat().st_size,'null_original_quantities':nulls,
    'retained_timeout_example':bool(finalizer.timeout_example(DATA,gold)),
    'accepted_sources':accepted,'notebook_cells':len(notebook['cells']),
    'model_calls':0,'bootstrap_calls':0,'scoring_calls':0}))
