import os
from pathlib import Path

os.environ['NB_LIVE'] = '1'
os.environ['NB_PROFILE'] = 'smoke'
os.chdir(Path(__file__).resolve().parents[1])
for name in ['setup34.py', 'transport34.py', 'from_33/reading_rules_v1.py']:
    exec(compile((Path('data') / name).read_text(encoding='utf-8'), name, 'exec'))

checks_path = DATA / 'resume_transport_checks.json'
checks = load(checks_path) if checks_path.exists() else []
try:
    for name, spec in {**JUDGES, **WRITERS}.items():
        force={n.strip() for n in os.environ.get('NB_TRANSPORT_FORCE_MODELS','').split(',') if n.strip()}
        if name not in force and any(c['name'] == name and c['passed'] for c in checks):
            continue
        prompt = 'Choose the correct sum. A: 4. B: 5. Task: 2+2. Return JSON only: {"winner":"A","confidence":99,"reason":"Four is correct."}'
        extra = dict(choices={'A':'4','B':'5'}, state='Choose the correct sum for 2+2.') if spec['backend']=='decisions' else {}
        tag=os.environ.get('NB_TRANSPORT_CHECK_TAG','20261124')
        row = ask(spec, prompt, 'nb34:resume-'+tag+':transport:' + name, budget=300, max_attempts=1, **extra)
        out = row['response']
        parsed = parse_judgment(row, False)
        served = bool(not out.get('error') and out.get('status',200)<400 and out.get('returncode',0)==0)
        passed = served and parsed.get('winner')=='A'
        check = dict(at=now(), name=name, model=spec['model'], provider=spec.get('provider',spec['backend']),
                     key=row['key'], passed=passed, served=served, parsed=parsed,
                     error_diagnostics=error_diagnostics(out)[:4000], text=out.get('text','')[:1000],
                     attempts=1, purpose='Fresh transport check after 25-day pause; no substitution')
        checks.append(check)
        save(checks_path, checks)
        log('resume_transport_check', **{k:v for k,v in check.items() if k!='at'})
        print(name, 'PASS' if passed else 'STOP', parsed, flush=True)
        if not passed:
            save(DATA/'resume_transport_stop.json',check)
            raise RuntimeError('Pinned model transport check failed: '+name+'; no substitution or collection allowed')
    if (DATA/'resume_transport_stop.json').exists():
        (DATA/'resume_transport_stop.json').rename(DATA/('resume_transport_stop_resolved_'+tag+'.json'))
    save(DATA/'resume_transport_ready.json',dict(at=now(),models=len(JUDGES)+len(WRITERS),all_passed=True,new_calls=new_calls,
        accounted_openrouter_usd=accounted_openrouter()))
    print('ALL RESUMED PINNED TRANSPORT CHECKS PASSED', flush=True)
except BaseException:
    p=ROOT/'HANDOFF.md'
    previous=p.read_text(encoding='utf-8') if p.exists() else ''
    status=load(DATA/'cli429_stop.json') if (DATA/'cli429_stop.json').exists() else load(DATA/'quota_stop.json') if (DATA/'quota_stop.json').exists() else load(DATA/'resume_transport_stop.json') if (DATA/'resume_transport_stop.json').exists() else {'status':'Transport check interrupted; inspect log.'}
    p.write_text('# Status: resumed transport checks stopped collection\n\n'+json.dumps(status,indent=2)+
        '\n\nNo substitute model was used. Completed batch1: 120 new items plus original240; 48 disagreements. '
        'Batch2 has32 completed items (30 code,2 worked);88 remain before its strong judging. '
        'Later batches depend on the frozen stopping rule. Final tie-breakers and offline notebook execution remain pending. '
        'Current cached replies are intact. Resume checks are data/resume_transport_checks.json. '
        'Manual owner pause on2026-10-30 at19:07:47UTC and25-day resume gap are data/resume_record.json; '
        'four interrupted requests reserve USD0.04 with no scored outcomes.\n\n'+previous,encoding='utf-8')
    raise
