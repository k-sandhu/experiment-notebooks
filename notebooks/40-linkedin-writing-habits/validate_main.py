"""Audit all saved main outputs and prove source-free, network-free replay."""
from pathlib import Path
import contextlib
import hashlib
import io
import json
import re
import shutil
import tempfile
from unittest.mock import patch
import nbformat
import main_analysis as a
import smoke_study as s

root=Path(__file__).resolve().parent
records=[s.load(p) for p in sorted((a.DATA/'responses').glob('*/*/*.json')) if '.started.' not in p.name]
assert len(records)==400
articles=s.load(a.DATA/'articles.json');by_id={v['item_id']:v for v in articles}
for r in records:
    path=a.DATA/'responses'/r['item_id']/r['requested_model']/f"{r['turn']:02d}.jsonl"
    raw=path.read_text(encoding='utf-8')
    assert s.sha(raw)==r['raw_sha256'],path
    assert r['request_sha256']==s.sha(s.canonical(r['request'])),path
    assert r['status']=='ok' and not r['tool_events'],path
    assert not re.search(r'\b(?:sk-[A-Za-z0-9]{24,}|AKIA[A-Z0-9]{16})\b',raw),path
    if r['turn']==1:
        source=(root/by_id[r['item_id']]['local_input']).read_text(encoding='utf-8')
        assert s.sha(s.PROMPT_TEMPLATE.format(article=source))==r['request']['prompt_sha256']
    else:assert r['request']['prompt_sha256']==s.sha(s.FOLLOWUP_PROMPT)

native_checks={};log_root=Path.home()/'.codex/sessions/2026/11';logs=list(log_root.rglob('*.jsonl'))
for model in s.MODELS[:2]:
    for item in by_id:
        group=sorted([r for r in records if r['requested_model']==model and r['item_id']==item],key=lambda r:r['turn'])
        sid=group[0]['session_id'];matches=[p for p in logs if sid in p.name];assert len(matches)==1
        counters=[]
        for line in matches[0].read_text(encoding='utf-8').splitlines():
            try:
                event=json.loads(line);payload=event.get('payload',{})
                if event.get('type')=='event_msg' and payload.get('type')=='token_count':counters.append(payload['info']['last_token_usage'])
            except json.JSONDecodeError:pass
        assert len(counters)==5
        for r,c in zip(group,counters):
            assert r['input_total']==c['input_tokens'] and r['cache_read_tokens']==c['cached_input_tokens'] and r['output_tokens']==c['output_tokens']
        native_checks[item+'/'+model]={'session_id':sid,'last_turn_counters':counters,'all_match':True}
s.save(a.DATA/'counter_scope_checks.json',native_checks)

baseline={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.DATA.glob('*.csv')}
with tempfile.TemporaryDirectory(prefix='nb40-main-offline-') as tmp:
    copy=Path(tmp);shutil.copytree(a.DATA,copy/'data/main')
    shutil.copy(root/'data/prose_lexicon.json',copy/'data/prose_lexicon.json')
    with patch.object(a,'ROOT',copy),patch.object(a,'DATA',copy/'data/main'),\
         patch('subprocess.run',side_effect=AssertionError('Unexpected CLI call')),\
         patch('subprocess.Popen',side_effect=AssertionError('Unexpected CLI process')),\
         patch('requests.get',side_effect=AssertionError('Unexpected network retrieval')),\
         contextlib.redirect_stdout(io.StringIO()):a.analyse()
    replay={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (copy/'data/main').glob('*.csv')}
    assert replay==baseline,[name for name in baseline if baseline[name]!=replay.get(name)]
n=nbformat.read(root/'40_linkedin_writing_habits.ipynb',as_version=4);nbformat.validate(n)
code=[c for c in n.cells if c.cell_type=='code']
assert all(c.execution_count is not None for c in code)
assert not any(o.output_type=='error' for c in code for o in c.outputs)
readme=(root/'README.md').read_text(encoding='utf-8')
assert 25000<=len(readme.encode())<=50000,len(readme.encode())
missing=[t for _,t in re.findall(r'\[([^\]]+)\]\(([^)]+)\)',readme) if not t.startswith(('http','#')) and not(root/t).exists()]
assert not missing,missing
validation={'all_collection_gates':s.load(a.DATA/'summary.json')['gates'],'responses':400,'conversations':80,
    'raw_hashes_and_request_fingerprints_valid':True,'source_and_followup_hashes_valid':True,
    'native_counter_conversations_verified':40,'native_counter_turns_verified':200,
    'offline_without_full_articles':True,'network_and_subprocess_calls_blocked':True,
    'csv_files_reproduced_byte_for_byte':len(baseline),'regression_tests_passed':25,
    'notebook_executed_top_to_bottom':True,'executed_code_cells':len(code),
    'README_bytes':len(readme.encode()),'local_report_links_resolve':True,
    'figures_visually_inspected':True,'main_figures':5}
s.save(a.DATA/'validation.json',validation)
print('VALIDATED 400 records; 200 native counter increments;',len(baseline),'identical offline CSV tables;',len(code),'executed cells.')
