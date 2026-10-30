"""Bind reviewed unknown-outcome handling before sending only unsent requests."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

from scale_intervention_resume import scale_intervention_resume_verify, sir_hash

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent / 'experiment_notebooks/notebooks/23-synthetic-data-curation'
DATA = ROOT / 'data/scale_v5'
PUBLIC = 'intervention_resume/'
SOURCE_SHA = 'fe172853d9f7f8ac496e36eb3560433888b8575a79c050cdc62250308e32a727'
TEST_SHA = '2452398d14aabc85e1c9593f6e30edff2728d3b1a7710f12053099e96ad61cf4'
ANALYSIS_SHA = '3e92df76e0a136c92389852f86530bd7df0ea828588b93269b35ed08d651bca2'
ANALYSIS_TEST_SHA = '4d9c749b22eea7effca38e7ed72f4002eaa1fa2c9db93b05720172d839dead71'


def sha(raw): return hashlib.sha256(raw).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def encode(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2)+'\n').encode('utf-8')


def main():
    amendment_path = DATA / PUBLIC / 'amendment_002.json'
    if amendment_path.exists():
        state = scale_intervention_resume_verify(ROOT, amendment_path)
        print(json.dumps({'existing_amendment_verified': True, 'sha256': state['amendment_sha256']}))
        return
    assert sha((BASE/'scale_intervention_resume.py').read_bytes()) == SOURCE_SHA
    assert sha((BASE/'test_scale_intervention_resume.py').read_bytes()) == TEST_SHA
    assert sha((BASE/'scale_missing_outcomes.py').read_bytes()) == ANALYSIS_SHA
    assert sha((BASE/'test_scale_missing_outcomes.py').read_bytes()) == ANALYSIS_TEST_SHA
    for name, source, test in [('scale_intervention_resume_review', SOURCE_SHA, TEST_SHA),
                               ('scale_missing_outcomes_review', ANALYSIS_SHA, ANALYSIS_TEST_SHA)]:
        review = read(BASE/(name+'.json'))
        assert review.get('passed') is True or review.get('status') == 'passed'
        assert not review.get('issues') and review['model_calls'] == 0
        assert review['source_sha256'] == source and review['tests_sha256'] == test
        log_name = 'scale_intervention_resume_unit_tests.log' if name == 'scale_intervention_resume_review' else 'scale_missing_outcomes_unit_tests.log'
        assert review['test_log_sha256'] == sha((BASE/log_name).read_bytes())
    assert read(DATA/'main/original_manifest.json')['phase'] == 'originals_complete'
    assert not (DATA/'main/manifest.json').exists(), 'Interventions already complete'
    prior = read(BASE/'scale_intervention_interruption_inventory.json')
    inventory = {'protocol': '23-scale-v5', 'count': 1240, 'requests': prior['requests']}
    current = {p.name.removesuffix('.json.gz'): sha(p.read_bytes()) for p in (DATA/'main/cache').glob('*.json.gz')}
    assert current == inventory['requests'] and len(current) == 1240, 'Prior cache bytes changed'
    dispatch = read(DATA/'main/dispatch.json')['jobs']
    assert len(dispatch) == 1200
    arm_keys = [job['request_key'] for job in dispatch]
    plans = []
    for path in (DATA/'main/request_plans').glob('*.json'):
        rows = read(path)
        if [row['request_key'] for row in rows] == arm_keys:
            plans.append((path, rows))
    assert len(plans) == 1
    plan_path, plan_rows = plans[0]
    by_key = {row['request_key']: row for row in plan_rows}
    unavailable = []
    for job in dispatch[116:120]:
        key = job['request_key']
        cache = read(DATA/'main/cache'/(key+'.json.gz'))
        assert cache['key'] == sir_hash(cache['request']) == key
        assert len(cache['attempts']) == 1 and set(cache['attempts'][0]) == {'pending','started_at','timeout_s'}
        assert cache['attempts'][0]['pending'] is True
        p, request = by_key[key], cache['request']
        unavailable.append({'request_key': key, 'cache_sha256': current[key], 'case_id': job['case_id'],
            'content_hash': p['source_hash'], 'request_input_hash': job['input_hash'],
            'feedback_hash': job['feedback_hash'], 'arm': job['arm'], 'stage': request['stage'], 'sample': request['sample'],
            'profile': {'model': 'gpt-6.1-sol','reasoning_effort':'high','protocol':'23-scale-v5','timeout_s':900}})
    proof = {'checked_at_utc':'2026-10-27T16:46:54+00:00', 'owned_workers':0,
        'collector_session_available':False, 'collector_session':60410,
        'last_operational_log_write_at_utc':'2026-10-27T16:07:12+00:00',
        'actual_loss_time_utc':None, 'actual_loss_cause':None,
        'checks':['The old exec session returned Unknown process id 60410.',
                  'A Win32_Process query found no Python collector for the exact reviewed runner path.',
                  'A read-only psutil query found zero Python/node/codex/PowerShell processes with cwd containing nb23_codex_empty_; zero inaccessible candidates.'],
        'note':'No processes touched. Pending records prove persisted attempt slots, not confirmed CLI launches or model outcomes. The session disappeared around the client refresh; cause and actual termination time are unknown.'}
    now = datetime.now(timezone.utc)
    analysis_plan = {'protocol':'23-scale-v5', 'version':'23-scale-v5-missing-outcomes-v1',
        'declared_at_utc':now.isoformat(), 'scheduled_pairs':600, 'unavailable_whole_pairs':2,
        'unavailable_outcomes':4, 'available_pair_target':598,
        'unavailable_request_keys':sorted(x['request_key'] for x in unavailable),
        'unavailable_case_ids':sorted(set(x['case_id'] for x in unavailable)),
        'analysis_source_sha256':ANALYSIS_SHA, 'analysis_tests_sha256':ANALYSIS_TEST_SHA,
        'bootstrap_draws':20000, 'bootstrap_seed':246600,
        'complete_pair_analysis':'Compute recovery rates, exact two-sided McNemar test and paired percentile bootstrap on the 598 pairs with two observed outcomes. Never classify the four unavailable model outcomes as wrong answers.',
        'scheduled_pair_sensitivity':'Enumerate all 16 binary success/failure assignments for the four unavailable outcomes. These are hypothetical statistical completions, never model responses. Bound the 600-pair difference by (observed repair-minus-fresh success count minus two)/600 through (observed count plus two)/600. Compute exact tests and bootstrap endpoint envelopes for every completion.',
        'amended_claim_rule':'Claim a repair advantage only if repair-minus-fresh is positive and the exact two-sided McNemar p-value is below 0.05 in EVERY completion. Otherwise the amended primary decision is inconclusive.',
        'selection_policy':'Retain all 600 originally selected sources; no replacement, resampling, new source, model draw, prompt, feedback, scoring, ranking or call-budget change. Resume only 1080 unsent jobs.',
        'data_handling':'Preserve all 1240 existing gzip cache bytes, including four pending records. Overlay only a controller-interruption/unavailable observation in memory. No reconstructed answer, provider event, finish time, return code, elapsed time or usage. Actual physical launch count for these four slots is unknown.',
        'efficacy_access':'No intervention response or recovery rate was inspected before this declaration. The reviewer initially mistook old original-collection stop output for arm output and corrected the disclosure; no intervention efficacy was exposed.',
        'limit':'The original preregistration had no clause for controller loss. This separate conservative missing-data amendment precedes resumed calls and every efficacy comparison.'}
    copies = {PUBLIC+'prior_cache_inventory_002.json':encode(inventory),
              PUBLIC+'process_absence_002.json':encode(proof), PUBLIC+'analysis_plan.json':encode(analysis_plan)}
    for name in ('scale_intervention_resume.py','test_scale_intervention_resume.py','scale_missing_outcomes.py',
                 'test_scale_missing_outcomes.py','declare_scale_intervention_resume.py'):
        copies[PUBLIC+'source_snapshot/'+name] = (BASE/name).read_bytes()
    # The statistics test uses this exact adjacent frozen reference implementation.
    copies[PUBLIC+'source_snapshot/scale_experiment.py'] = (DATA/'source_snapshot/scale_experiment.py').read_bytes()
    for name in ('scale_interruption_review.json','scale_interruption_review.md',
                 'scale_intervention_resume_review.json','scale_intervention_resume_review.md',
                 'scale_intervention_resume_unit_tests.log','scale_missing_outcomes_review.json',
                 'scale_missing_outcomes_review.md','scale_missing_outcomes_unit_tests.log'):
        copies[PUBLIC+name] = (BASE/name).read_bytes()
    copies[PUBLIC+'initial_interventions_live.log'] = (BASE/'scale_interventions_live.log').read_bytes()
    launcher = BASE/'launch_scale_intervention_resume.ps1'
    launch_proof = BASE/'scale_detached_launcher_smoke.json'
    assert launcher.exists() and read(launch_proof)['passed'], 'Detached launcher smoke must pass first'
    assert read(launch_proof)['launcher_sha256'] == sha(launcher.read_bytes()), 'Launcher changed after smoke test'
    assert read(launch_proof)['model_calls'] == 0
    copies[PUBLIC+'source_snapshot/'+launcher.name] = launcher.read_bytes()
    copies[PUBLIC+launch_proof.name] = launch_proof.read_bytes()
    def binding(name): return {'path':name, 'sha256':sha(copies[name]) if name in copies else sha((DATA/name).read_bytes())}
    protected_names = ['source_freeze.json','intervention_start_declaration.json',
        'infrastructure_resume/amendment_001.json','main/dispatch.json','main/original_manifest.json',
        'main/selection.json','main/protocol.json','main/allocation.json']
    amendment = {'protocol':'23-scale-v5','amendment_version':'23-scale-intervention-interruption-v1',
        'declared_at_utc':now.isoformat(),'loss_observed_at_utc':proof['checked_at_utc'],
        'protected_files':[binding(name) for name in protected_names],
        'request_plans':[binding(plan_path.relative_to(DATA).as_posix())],
        'cache_inventory':binding(PUBLIC+'prior_cache_inventory_002.json'),
        'process_proof':binding(PUBLIC+'process_absence_002.json'),
        'implementation':binding(PUBLIC+'source_snapshot/scale_intervention_resume.py'),
        'analysis_plan':binding(PUBLIC+'analysis_plan.json'),
        'tests':[binding(PUBLIC+'source_snapshot/test_scale_intervention_resume.py'),binding(PUBLIC+'source_snapshot/test_scale_missing_outcomes.py')],
        'provenance_sha256':{name:sha(raw) for name,raw in copies.items()},
        'unavailable_requests':unavailable,
        'unavailable_case_ids':analysis_plan['unavailable_case_ids'],
        'unavailable_request_keys':analysis_plan['unavailable_request_keys'],
        'remaining_unsent_jobs':1080,'retained_terminal_arm_requests':116,
        'scope':'Continue unsent frozen jobs only. Never reissue any recorded key. All four unavailable raw pending artifacts remain unchanged. Any new infrastructure failure drains the current wave and stops for review.',
        'scientific_handling':'598 complete pairs plus all-16-completion sensitivity, as fixed in the bound analysis plan. No missing outcomes are imputed as observed answers or counted as model mistakes.'}
    copies[PUBLIC+'amendment_002.json'] = encode(amendment)
    for name,raw in copies.items():
        assert not (DATA/name).exists() or (DATA/name).read_bytes() == raw, 'Existing artifact differs: '+name
    for name,raw in copies.items():
        path = DATA/name;path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():
            with path.open('xb') as stream: stream.write(raw)
    state = scale_intervention_resume_verify(ROOT, amendment_path)
    print(json.dumps({'passed':True,'model_calls':0,'raw_caches_preserved':len(current),
        'unknown_outcome_slots':len(state['approved']),'unsent_jobs':1080,
        'amendment_sha256':state['amendment_sha256'],'declared_at_utc':now.isoformat()}))


if __name__ == '__main__': main()
