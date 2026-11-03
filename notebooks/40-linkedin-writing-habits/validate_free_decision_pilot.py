"""Validate free-route classification provenance and source-free offline replay."""
import contextlib
import io
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch

import free_decision_pilot as f
import smoke_study as s


def validate():
    protocol=s.load(f.OUT/'protocol_40.json')
    original=s.load(f.ROOT/'data/decision_audit/protocol.json')
    assert protocol['definitions']==original['definitions'] and protocol['zones']==original['zones']
    source_info=next(a for a in s.load(f.ROOT/'data/main/articles.json') if a['item_id']=='01-kimi')
    source=(f.ROOT/source_info['local_input']).read_text(encoding='utf-8')
    assert s.sha(source)==source_info['text_sha256']
    posts={f"{r['item_id']}/{r['requested_model']}/{r['turn']:02d}":r for r in f.pilot_records()}
    records=[s.load(path) for path in (f.OUT/'responses_40').glob('*.json')]
    assert len(records)==114 and not list((f.OUT/'started').glob('*.json'))
    slots=set();request_ids=set()
    for r in records:
        full=s.load(f.ROOT/r['private_cache']);wire=full['request']
        assert full['response']==r['raw']
        assert s.sha(s.canonical(wire))==r['request_sha256']==full['request_sha256']
        assert wire==f.payload_for(posts[r['post_id']],r['batch'],protocol,source)
        assert wire['model']==f.MODEL
        assert wire['provider']['max_price']=={'prompt':0,'completion':0}
        assert wire['provider']['only']==['respan'] and not wire['provider']['allow_fallbacks']
        assert r['status']==200 and len(r['question_names'])==40
        assert r['raw']['model']=='respan/span-01-lite-20260925'
        assert r['raw']['provider']=='Respan' and r['raw']['usage']['cost']==0
        assert r['parsed']==f.d.parse_decision(r['raw'],r['question_names'])
        assert all(v['valid'] for v in r['parsed'].values())
        assert r['raw']['id'] not in request_ids;request_ids.add(r['raw']['id'])
        for question in r['question_names']:
            slot=(r['post_id'],question)
            assert slot not in slots;slots.add(slot)
    assert len(slots)==4560 and len({r['post_id'] for r in records})==19
    assert protocol['excluded']==[{'post_id':'01-kimi/gpt-6.1-terra/01','reason':'invalid_tags'}]
    controls=s.load(f.OUT/'controls/protocol.json')
    control_rows={r['control_id']:r for r in [s.load(path) for path in (f.OUT/'controls/responses').glob('*.json')]}
    assert len(control_rows)==3
    for fixture in controls['fixtures']:
        r=control_rows[fixture['id']]
        expected=f.payload_for(dict(text=fixture['post'],post_body=fixture['post']),0,protocol,controls['source'])
        assert r['request']==expected and s.sha(s.canonical(expected))==r['request_sha256']
        assert r['status']==200 and r['response']['usage']['cost']==0
        assert r['parsed']==f.d.parse_decision(r['response'],expected['questions'])
        assert all(v['valid'] for v in r['parsed'].values())
    summary=s.load(f.OUT/'summary.json');assert summary['complete'] and summary['unpriced_requests']==0
    names=['classifications.csv','counts.csv','region_consistency.csv','summary.json']
    before={name:(f.OUT/name).read_bytes() for name in names}
    with tempfile.TemporaryDirectory(prefix='nb40-free-classifier-') as tmp:
        clone=Path(tmp)/'audit';shutil.copytree(f.OUT,clone)
        with (patch.object(f,'OUT',clone),patch.object(f,'ROOT',Path(tmp)),
              patch('requests.get',side_effect=AssertionError('Unexpected network')),
              patch('requests.post',side_effect=AssertionError('Unexpected API call')),
              patch('subprocess.Popen',side_effect=AssertionError('Unexpected CLI call')),
              contextlib.redirect_stdout(io.StringIO())):
            f.analyse()
        assert all((clone/name).read_bytes()==value for name,value in before.items())
    report=dict(requests_checked=114,valid_probabilities_checked=4560,post_bodies_checked=19,
                rubric_identical_to_previous_audit=True,zero_price_routes_checked=True,
                native_cost_zero_requests=114,unique_provider_request_ids=114,
                separate_pattern_controls_checked=3,
                invalid_generation_not_scored=True,full_private_requests_and_raw_replies_checked=True,
                duplicate_slots=0,source_free_network_blocked_replay_identical=True)
    s.save(f.OUT/'validation.json',report)
    print(s.canonical(report))


if __name__=='__main__':validate()
