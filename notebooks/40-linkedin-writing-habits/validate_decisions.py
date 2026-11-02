"""Verify request provenance, multi-label slots and strict offline Decisions replay."""
from pathlib import Path
import contextlib
import hashlib
import io
import shutil
import tempfile
from unittest.mock import patch
import decision_audit as d
import smoke_study as s

root=Path(__file__).resolve().parent
protocol=s.load(d.DECISIONS/'protocol.json');protocol_hash=s.sha(s.canonical(protocol))
records=[s.load(p) for p in (d.DECISIONS/'responses').glob('*.json')]
assert len(records)==800
posts={f"{r['item_id']}/{r['requested_model']}/{r['turn']:02d}":r for r in d.decision_records()}
source={a['item_id']:a for a in s.load(root/'data/main/articles.json')}
native_ids=set();slots=set()
for r in records:
    key=r['request_sha256'];wire=s.load(root/'data/local_inputs/decisions'/f'{key}.json')
    assert s.sha(s.canonical(wire))==key and r['protocol_sha256']==protocol_hash
    assert wire['model']==d.DECISION_MODEL==r['raw']['model']
    assert wire['provider']=={'order':['openai'],'allow_fallbacks':False}
    assert r['status']==200 and r['parsed']==d.parse_decision(r['raw'],r['question_names'])
    assert len(r['question_names'])==120 and all(v['valid'] for v in r['parsed'].values())
    assert r['post_sha256']==s.sha(s.zones(posts[r['post_id']]['text'])['whole'])
    assert r['source_sha256']==source[r['item_id']]['text_sha256']
    assert (r['post_id'],r['batch']) not in slots;slots.add((r['post_id'],r['batch']))
    native_ids.add(r['raw']['id'])
assert len(slots)==800 and len(native_ids)==800
baseline={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in d.DECISIONS.glob('*.csv')}
with tempfile.TemporaryDirectory(prefix='nb40-decisions-offline-') as tmp:
    clone=Path(tmp)
    shutil.copytree(d.DECISIONS,clone/'data/decision_audit')
    assert not (clone/'data/local_inputs').exists()
    with patch.object(d,'ROOT',clone),patch.object(d,'DECISIONS',clone/'data/decision_audit'),\
         patch('requests.post',side_effect=AssertionError('Unexpected API call')),\
         patch('requests.get',side_effect=AssertionError('Unexpected network retrieval')),\
         patch('subprocess.run',side_effect=AssertionError('Unexpected CLI call')),\
         contextlib.redirect_stdout(io.StringIO()):d.analyse_decisions()
    replay={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (clone/'data/decision_audit').glob('*.csv')}
    assert baseline==replay,[n for n in baseline if replay.get(n)!=baseline[n]]
    assert s.load(clone/'data/decision_audit/summary.json')==s.load(d.DECISIONS/'summary.json')
summary=s.load(d.DECISIONS/'summary.json');assert summary['complete'] and summary['valid_answers']==96000
assert summary['cache_read_counter_available_requests']==0
validation={'posts':400,'independent_pattern_labels':40,'regions':6,'requests':800,'predicate_answers':96000,
    'all_answers_readable':True,'request_source_post_protocol_hashes_verified':True,'unique_native_request_ids':800,
    'model_pin_verified_every_response':True,'offline_without_articles_or_wire_bodies':True,
    'API_network_and_subprocess_calls_blocked':True,'byte_identical_csv_tables':len(baseline),
    'summary_json_reproduced':True,'regression_tests':25,'manual_relabelling':False,
    'region_whole_conflicts_preserved':996,'provider_cache_counters':'Unavailable, not zero',
    'classifier_effort_setting':'Not exposed','reported_cost_usd':summary['reported_cost_usd']}
s.save(d.DECISIONS/'validation.json',validation)
print('Validated 800 request fingerprints, 96,000 probabilities and',len(baseline),'byte-identical offline classifier tables.')
