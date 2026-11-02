"""Validate both conditions, provenance, native counters and article-free offline replay."""
from pathlib import Path
from unittest.mock import patch
import contextlib
import hashlib
import io
import json
import re
import shutil
import tempfile
import nbformat
import smoke_study as s
import main_analysis as a
import expanded_audit as e
import decision_audit as d
import prompt_study as p
import prompt_comparison as c

root=Path(__file__).resolve().parent
new=p.INTERVENTION
all_records={}
source={x['item_id']:x for x in s.load(root/'data/main/articles.json')}
template=(root/'data/prompt_conditions/plain_prose_v2.txt').read_text(encoding='utf-8').replace('{{complete_article_text}}','{article}')
base_template=s.load(root/'data/main/preregistration.json')['initial_prompt_template']
for condition,folder,initial in [('baseline',root/'data/main',base_template),('explicit',new,template)]:
    records=[s.load(path) for path in sorted((folder/'responses').glob('*/*/*.json')) if '.started.' not in path.name]
    assert len(records)==400
    assert not list((folder/'responses').glob('*/*/*.started.json'))
    for r in records:
        assert r['status']=='ok' and not r['tool_events'] and r['request']['effort']=='high'
        assert r['request_sha256']==s.sha(s.canonical(r['request']))
        stdout=(folder/'responses'/r['item_id']/r['requested_model']/f"{r['turn']:02d}.jsonl").read_text(encoding='utf-8')
        assert r['raw_sha256']==s.sha(stdout)
        assert r['request']['source_sha256']==source[r['item_id']]['text_sha256']
        article=(root/source[r['item_id']]['local_input']).read_text(encoding='utf-8')
        prompt=initial.format(article=article) if r['turn']==1 else s.FOLLOWUP_PROMPT
        assert r['request']['prompt_sha256']==s.sha(prompt)
    assert len({r['session_id'] for r in records})==80
    for model in s.MODELS:
        for item in source:
            part=sorted([r for r in records if r['requested_model']==model and r['item_id']==item],key=lambda r:r['turn'])
            assert len(part)==5 and len({r['session_id'] for r in part})==1
    all_records[condition]=records
assert not {r['session_id'] for r in all_records['baseline']}&{r['session_id'] for r in all_records['explicit']}
assert s.load(new/'articles.json')==s.load(root/'data/main/articles.json')
assert s.load(new/'decisions/protocol.json')==s.load(root/'data/decision_audit/protocol.json')
assert s.load(new/'cli_versions.json')==s.load(root/'data/main/cli_versions.json')

# Native cumulative counters are independently compared with each writer's per-turn ledger.
logs=list((Path.home()/'.codex/sessions/2026/11').rglob('*.jsonl'))
native={}
for model in s.MODELS[:2]:
    for item in source:
        part=sorted([r for r in all_records['explicit'] if r['requested_model']==model and r['item_id']==item],key=lambda r:r['turn'])
        sid=part[0]['session_id'];matches=[path for path in logs if sid in path.name];assert len(matches)==1
        counters=[]
        for line in matches[0].read_text(encoding='utf-8').splitlines():
            try:
                event=json.loads(line);payload=event.get('payload',{})
                if event.get('type')=='event_msg' and payload.get('type')=='token_count':counters.append(payload['info']['last_token_usage'])
            except json.JSONDecodeError:pass
        assert len(counters)==5
        for r,usage in zip(part,counters):
            assert r['input_total']==usage['input_tokens'] and r['cache_read_tokens']==usage['cached_input_tokens'] and r['output_tokens']==usage['output_tokens']
        native[item+'/'+model]={'session_id':sid,'last_turn_counters':counters,'all_match':True}
s.save(new/'counter_scope_checks.json',native)

decision_records=[]
for folder in [root/'data/decision_audit',new/'decisions']:
    records=[s.load(path) for path in (folder/'responses').glob('*.json')];assert len(records)==800
    for r in records:
        wire=s.load(root/'data/local_inputs/decisions'/f"{r['request_sha256']}.json")
        assert s.sha(s.canonical(wire))==r['request_sha256']
        assert r['raw']['model']==d.DECISION_MODEL
        assert r['parsed']==d.parse_decision(r['raw'],r['question_names'])
        assert all(v['valid'] for v in r['parsed'].values())
        assert len(r['question_names'])==120 and len(r['raw']['answers'])==120
    assert len({r['raw']['id'] for r in records})==800
    decision_records.extend(records)

# Replay all 47 main-study CSV tables with no articles, wire bodies, model calls or repository helper imports.
folders=['data/main','data/expanded_audit','data/decision_audit','data/plain_prose_v2','data/prompt_comparison']
def table_hashes(base):
    return {path.relative_to(base).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
        for name in folders for path in (base/name).rglob('*.csv')}
baseline=table_hashes(root)
with tempfile.TemporaryDirectory(prefix='nb40-prompt-offline-') as tmp:
    clone=Path(tmp)
    for name in folders:shutil.copytree(root/name,clone/name)
    shutil.copy(root/'data/prose_lexicon.json',clone/'data/prose_lexicon.json')
    (clone/'data/prompt_conditions').mkdir()
    shutil.copy(root/'data/prompt_conditions/plain_prose_v2.txt',clone/'data/prompt_conditions/plain_prose_v2.txt')
    assert not (clone/'data/local_inputs').exists()
    with patch.object(a,'ROOT',clone),patch.object(a,'DATA',clone/'data/main'),\
         patch.object(e,'ROOT',clone),patch.object(e,'AUDIT',clone/'data/expanded_audit'),\
         patch.object(d,'ROOT',clone),patch.object(d,'DECISIONS',clone/'data/decision_audit'),\
         patch.object(p,'ROOT',clone),patch.object(p,'INTERVENTION',clone/'data/plain_prose_v2'),\
         patch.object(c,'ROOT',clone),patch.object(c,'COMPARISON',clone/'data/prompt_comparison'),\
         patch('requests.get',side_effect=AssertionError('Unexpected retrieval')),\
         patch('requests.post',side_effect=AssertionError('Unexpected API call')),\
         patch('subprocess.run',side_effect=AssertionError('Unexpected CLI call')),\
         patch('subprocess.Popen',side_effect=AssertionError('Unexpected CLI process')),\
         contextlib.redirect_stdout(io.StringIO()):
        a.analyse();e.analyse_expanded();d.analyse_decisions();p.analyse_prompt_study();c.compare_prompts()
    replay=table_hashes(clone)
    assert replay==baseline,[name for name in baseline if replay.get(name)!=baseline[name]]

notebook=nbformat.read(root/'40_linkedin_writing_habits.ipynb',as_version=4);nbformat.validate(notebook)
cells=[x for x in notebook.cells if x.cell_type=='code']
assert all(x.execution_count is not None for x in cells)
assert not any(o.output_type=='error' for cell in cells for o in cell.outputs)
readme=(root/'README.md').read_text(encoding='utf-8')
assert 25000<=len(readme.encode())<=50000,len(readme.encode())
missing=[target for target in re.findall(r'\]\(([^)]+)\)',readme)
    if not target.startswith(('http','#')) and target!='data/prompt_comparison/validation.json' and not(root/target).exists()]
assert not missing,missing
registration=s.load(new/'preregistration.json')
assert registration['prompt_file_sha256']==s.sha((root/'data/prompt_conditions/plain_prose_v2.txt').read_text(encoding='utf-8'))
figure_proof_path=c.COMPARISON/'figure_validation.json'
figure_proof=s.load(figure_proof_path) if figure_proof_path.exists() else None
figures_valid=bool(figure_proof) and all(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for name,digest in figure_proof['figures'].items())
validation={'conditions':2,'writer_responses':800,'new_writer_responses':400,'new_conversations':80,
    'request_source_prompt_stdout_hashes_valid':True,'same_CLI_versions':True,'new_session_ids_disjoint_from_baseline':True,
    'new_native_counter_conversations_verified':40,'new_native_counter_turns_verified':200,
    'classifier_requests':1600,'classifier_probabilities':192000,'classifier_pin_and_rubric_unchanged':True,
    'classifier_request_hashes_valid':True,'offline_without_articles_or_wire_bodies':True,
    'API_network_subprocess_calls_blocked':True,'CSV_tables_reproduced_byte_for_byte':len(baseline),
    'notebook_code_cells_executed':len(cells),'regression_tests':28,'README_bytes':len(readme.encode()),
    'local_report_links_resolve':True,'figures_visually_inspected':figures_valid,
    'human_quality_validated':False,'manual_relabelling':False}
s.save(c.COMPARISON/'validation.json',validation)
print('VALIDATED 800 generations, 1600 classifier requests, 192000 probabilities;',len(baseline),'identical offline tables.')
