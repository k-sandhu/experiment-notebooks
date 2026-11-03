"""Check pilot provenance and replay its review export without sources or model calls."""
import contextlib
import io
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch

import tagged_kimi_pilot as p
import smoke_study as s


def validate():
    design=s.load(p.OUT/'preregistration.json')
    assert design['planned_calls']==20 and design['models']==p.MODELS and design['effort']=='high'
    initial=(p.ROOT/'data/prompt_conditions/simple_prose_v3.txt').read_text(encoding='utf-8')
    followup=(p.ROOT/'data/prompt_conditions/simple_prose_v3_followup.txt').read_text(encoding='utf-8')
    assert initial==design['initial_template'] and followup==design['followup']
    source=(p.ROOT/design['article']['local_input']).read_text(encoding='utf-8')
    assert s.sha(source)==design['article']['text_sha256']
    records=[s.load(x) for x in sorted((p.OUT/'responses').glob('*/*/*.json')) if '.started.' not in x.name]
    assert len(records)==20 and not list((p.OUT/'responses').glob('*/*/*.started.json'))
    assert not s.load(p.OUT/'collection_events.json')
    sessions=set()
    for model in p.MODELS:
        part=sorted([r for r in records if r['requested_model']==model],key=lambda r:r['turn'])
        assert [r['turn'] for r in part]==list(range(1,6))
        assert len({r['session_id'] for r in part})==1
        sid=part[0]['session_id'];assert sid not in sessions;sessions.add(sid)
        history=[]
        for r in part:
            turn=r['turn']
            full=s.load(p.ROOT/r['private_cache'])
            request=full['request']
            expected=initial.replace('{{complete_article_text}}',source) if turn==1 else followup
            assert request['stdin']==expected and s.sha(expected)==r['prompt_sha256']
            assert request['messages']==history+[dict(role='user',content=expected)]
            assert s.sha(s.canonical(request))==r['request_sha256']==full['request_sha256']
            assert full['response']['text']==r['text']
            assert request['prior_session_id']==(None if turn==1 else sid)
            assert request['effort']=='high' and request['tools']=='disabled' and request['web_search']=='disabled'
            assert r['request']['messages'][0]['content']==initial
            assert r['request_redacted'] and source not in s.canonical(r['request'])
            assert r['status']=='ok' and not r['tool_events']
            raw=(p.OUT/'responses/01-kimi'/model/f'{turn:02d}.jsonl').read_text(encoding='utf-8')
            native=s.parse_result(model,raw)
            assert native['text']==r['text'] and s.sha(raw)==r['raw_sha256']
            assert native['session_id']==sid and native['completed']
            extracted=p.parse_post(r['text'])
            assert all(r[k]==v for k,v in extracted.items())
            history=request['messages']+[dict(role='assistant',content=r['text'])]
    earlier=set()
    for condition in ['main','plain_prose_v2']:
        earlier.update(s.load(x)['session_id'] for x in (p.ROOT/'data'/condition/'responses').glob('*/*/*.json') if '.started.' not in x.name)
    assert not sessions&earlier
    before={name:(p.OUT/name).read_bytes() for name in ['summary.json','outputs.md']}
    with tempfile.TemporaryDirectory(prefix='nb40-tagged-pilot-') as tmp:
        clone=Path(tmp)/'pilot';shutil.copytree(p.OUT,clone)
        with (patch.object(p,'OUT',clone),
              patch('requests.get',side_effect=AssertionError('Unexpected network')),
              patch('requests.post',side_effect=AssertionError('Unexpected model call')),
              patch('subprocess.Popen',side_effect=AssertionError('Unexpected CLI call')),
              contextlib.redirect_stdout(io.StringIO())):
            p.export()
        assert all((clone/name).read_bytes()==value for name,value in before.items())
    report=dict(responses_checked=20,conversations_checked=4,source_and_request_hashes_checked=True,
                raw_response_identity_checked=True,private_full_request_cache_checked=True,
                fresh_conversations_checked=True,offline_export_identical=True,
                valid_tagged_posts=sum(r['post_body'] is not None for r in records),
                invalid_tag_posts=sum(r['post_body'] is None for r in records),
                outside_text_posts=sum(bool(r['extra_text_present']) for r in records))
    s.save(p.OUT/'validation.json',report)
    print(s.canonical(report))


if __name__=='__main__':validate()
