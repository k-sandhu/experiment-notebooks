import os
from pathlib import Path

os.environ.pop('NB_LIVE', None)
os.environ['NB_PROFILE']='full'
os.chdir(Path(__file__).resolve().parents[1])
for name in ['setup34.py','transport34.py','generator34.py','from_33/reading_rules_v1.py','design34.py','analysis34.py']:
    exec(compile((Path('data')/name).read_text(encoding='utf-8'),name,'exec'))

verify_sources()
items=[json.loads(s) for s in (DATA/'from_33/exam_v1.jsonl').read_text(encoding='utf-8').splitlines()]
items=[i for i in items if i['split']=='test']
rows=run_parallel(baseline_job,[(i,n,'test') for i in items for n in STRONG],'Offline source baseline audit')
routes=routing(items,rows)
assert sum(r['route']=='disagreed' for r in routes)==34
assert sum(r['route']=='agreed' for r in routes)==206
assert sum(r['route']=='agreed' and not r['agreed_correct'] for r in routes)==0
assert all(r['origin']=='33' for r in rows)
assert new_calls==0
assert canonical_winner('A','BA')=='B'
assert canonical_winner('B','BA')=='A'
assert canonical_winner(None,'BA') is None
assert pair_state([dict(lenient_canonical='A'),dict(lenient_canonical='B')])=='split'
assert pair_state([dict(lenient_canonical='A'),dict(lenient_canonical=None)])=='missing'
assert pair_state([dict(lenient_canonical='B'),dict(lenient_canonical='B')])=='B'
assert quota_message(dict(stdout='{"event":"error","message":"You have hit your usage limit. Try again at 22:00"}'))
assert quota_message(dict(stderr='insufficient credits'))
assert not quota_message(dict(error='Details: [bio]. See acceptable use policy'))
assert not retry_required(dict(error='Details: [bio]. See acceptable use policy'))
assert any(r['strict_unreadable_type']=='no_parseable_json' and not r['lenient_unreadable_type'] for r in rows)
bad_req=request_for(JUDGES['Sol'],'This deliberately uncached request must fail offline.','offline_canary')
try:
    ask(JUDGES['Sol'],bad_req['prompt'],bad_req['purpose'])
except RuntimeError as exc:
    assert 'Offline cache miss' in str(exc)
else:
    raise AssertionError('Replay cache miss reached transport')
assert new_calls==0
save(DATA/'engineering_checks.json',dict(at=now(),original_items=240,agreed=206,disagreed=34,agreed_both_wrong=0,
                                      source_hashes_valid=True,baseline_prompts_and_settings_exact=True,
                                      strict_fence_difference_confirmed=True,quota_event_detection=True,policy_refusal_not_quota=True,
                                      cache_miss_fails_offline=True,new_calls=0))
print('ENGINEERING CHECKS PASSED')
