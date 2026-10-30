"""One-shot unsent-only continuation after the 005 controller disappeared.

All 2268 raw caches remain immutable. Only 52 unsent slots may run. Nine
unknown outcomes and both known terminal errors retain their exact bytes.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import inspect
import os
import time
import json
from pathlib import Path
import threading

VERSION='23-scale-intervention-interruption-v3'
CAPACITY_ERROR="Codex reported turn.failed: {'type': 'turn.failed', 'error': {'message': 'Selected model is at capacity. Please try a different model.'}}"
ATTEMPT_FIELDS=('pending','error','return_code','timed_out','started_at','finished_at','elapsed_s','timeout_s')


def load_predecessor(root, amendment):
    data=Path(root).resolve()/'data/scale_v5';item=amendment['predecessor']
    if item['path']!='intervention_resume_005/amendment_005.json':raise ValueError('Exact005predecessor required')
    path=data/item['path'];raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('Predecessor amendment changed')
    info=json.loads(raw);relative=Path(info['implementation']['path'])
    if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsafe predecessor implementation')
    source=data/relative;source_bytes=source.read_bytes();digest=info['implementation']['sha256']
    if hashlib.sha256(source_bytes).hexdigest()!=digest:raise ValueError('005implementation changed')
    embedded=globals().get('SCALE_INTERVENTION_006_PREDECESSOR_SOURCE')
    if embedded is not None:
        if not isinstance(embedded,str) or hashlib.sha256(embedded.encode()).hexdigest()!=digest:raise ValueError('Embedded005source changed')
        source_bytes=embedded.encode()
    old={'__name__':'archived_intervention_resume_005'}
    for name in ('SCALE_INTERVENTION_005_PREDECESSOR_SOURCE','SCALE_INTERVENTION_004_PREDECESSOR_SOURCE','SCALE_INTERVENTION_PREDECESSOR_SOURCE'):
        if name in globals():old[name]=globals()[name]
    exec(compile(source_bytes,str(source),'exec'),old)
    return old


def scale_intervention_resume_006_verify(root, amendment_path):
    """Read typed request/attempt metadata and byte hashes; never inspect answers."""
    root=Path(root).resolve();data=root/'data/scale_v5';main=data/'main';amendment_path=Path(amendment_path).resolve()
    if not amendment_path.is_relative_to(data):raise ValueError('Amendment outside study')
    amendment=json.loads(amendment_path.read_bytes())
    if amendment.get('protocol')!='23-scale-v5' or amendment.get('amendment_version')!=VERSION:raise ValueError('Wrong amendment version')
    old=load_predecessor(root,amendment);prior=old['scale_intervention_resume_005_verify'](root,data/amendment['predecessor']['path']);core=prior['core']
    read,sha,hash_,time_=(core[n] for n in ('sir_read','sir_sha','sir_hash','sir_time'))
    def bound(directory,item):
        relative=Path(item['path'])
        if relative.is_absolute() or relative.drive or '..' in relative.parts:raise ValueError('Unsafe relative provenance path')
        return core['sir_bound'](directory,item)
    declared=time_(amendment['declared_at_utc']);loss=time_(amendment['loss_observed_at_utc'])
    if not loss<declared<=datetime.now(timezone.utc):raise ValueError('Invalid declaration time')
    required={'source_freeze.json','intervention_start_declaration.json','main/dispatch.json','main/selection.json','intervention_resume_005/amendment_005.json','intervention_resume_005/continuation_start_005.json'}
    protected=amendment['protected_files']
    if len({x['path'] for x in protected})!=len(protected) or not required<={x['path'] for x in protected}:raise ValueError('Missing frozen source/dispatch/selection/gate binding')
    for item in protected:bound(data,item)
    for name in ('implementation','analysis_plan','previous_analysis_plan','process_proof','cache_inventory','stop_record','recovery_review','handling_plan'):bound(data,amendment[name])
    for item in amendment.get('tests',[]):bound(data,item)
    provenance=amendment.get('provenance_sha256')
    if not isinstance(provenance,dict) or not provenance:raise ValueError('Require complete pre-call provenance inventory')
    for relative,digest in provenance.items():bound(data,dict(path=relative,sha256=digest))
    proof=read(bound(data,amendment['process_proof']))
    if (type(proof.get('owned_workers')) is not int or proof['owned_workers']!=0 or proof.get('collector_session_available') is not False
        or type(proof.get('inaccessible_owned_candidates')) is not int or proof['inaccessible_owned_candidates']!=0
        or not loss<=time_(proof['checked_at_utc'])<declared):raise ValueError('Post-loss owned-process absence proof required')
    stop=read(bound(data,amendment['stop_record']))
    if (stop.get('reason')!='controller_disappeared_without_finished_receipt' or stop.get('finished_receipt_present') is not False
        or stop.get('manifest_present') is not False or stop.get('export_files_present')!=0
        or stop.get('new_transport_failure_events')!=0):raise ValueError('Exact metadata-only controller loss required')
    inventory=read(bound(data,amendment['cache_inventory']));prefix=inventory.get('requests',{})
    dispatch=read(main/'dispatch.json')['jobs'];original=set(read(main/'original_manifest.json')['request_keys'])
    indexed={x['request_key']:x for x in dispatch}
    if (inventory.get('protocol')!='23-scale-v5' or inventory.get('count')!=2268 or len(prefix)!=2268 or len(dispatch)!=1200
        or len(indexed)!=1200 or set(prefix)!=original|{x['request_key'] for x in dispatch[:1148]}):raise ValueError('Exact2268cache/1148arm prefix required')
    if any(prefix.get(k)!=v for k,v in prior['inventory'].items()):raise ValueError('Prior2124prefix changed')
    plans={}
    for binding in prior['prior']['prior']['predecessor_state']['amendment']['request_plans']:
        plans.update({x['request_key']:x for x in read(bound(data,binding))})
    pending=set();terminal=0;terminal_errors=set()
    for key,digest in prefix.items():
        if sha(main/'cache'/(key+'.json.gz'))!=digest:raise ValueError('Recorded cache changed; no reissue')
        cache=read(main/'cache'/(key+'.json.gz'))
        if cache['key']!=key or hash_(cache['request'])!=key or len(cache['attempts'])!=1:raise ValueError('Request identity/attempt count changed')
        attempt=cache['attempts'][0]
        if attempt.get('pending') is True:
            if set(attempt)!={'pending','started_at','timeout_s'} or attempt['timeout_s']!=900 or time_(attempt['started_at'])>=loss:raise ValueError('Pending telemetry changed')
            pending.add(key)
        elif attempt.get('pending') is not False or not attempt.get('finished_at') or time_(attempt['finished_at'])>=declared:raise ValueError('Invalid terminal metadata')
        elif key not in original:
            terminal+=1
            if attempt.get('error'):terminal_errors.add(key)
    if len(pending)!=9 or terminal!=1139 or not set(prior['approved'])<pending:raise ValueError('Require nine pending slots and1139terminal arm records')
    failures=amendment['retained_transport_failures'];retained={x['request_key']:x for x in failures}
    if failures!=prior['retained_transport_failures'] or set(retained)!=terminal_errors:raise ValueError('Exactly unchanged two terminal errors required; no new bypass')
    approved={};profile={'model':'gpt-6.1-sol','reasoning_effort':'high','protocol':'23-scale-v5','timeout_s':900}
    for item in amendment['unavailable_requests']:
        key=item['request_key']
        if key in approved or key not in pending or item['cache_sha256']!=prefix[key]:raise ValueError('Unknown/duplicate/unbound unavailable request')
        cache=read(main/'cache'/(key+'.json.gz'));req=cache['request'];plan=plans[key];job=indexed[key]
        actual_profile={k:req.get(k) for k in profile if k!='timeout_s'};actual_profile['timeout_s']=req.get('runner_limits',{}).get('timeout_s')
        stage,sample=('generate',1) if item['arm']=='fresh_retry' else ('repair',0)
        if (item['profile']!=profile or actual_profile!=profile or item['arm'] not in {'fresh_retry','feedback_repair'}
            or any(item[k]!=plan[k] for k in ('case_id','arm','stage','sample')) or item['content_hash']!=plan['source_hash']
            or req['stage']!=stage or req['sample']!=sample or req['expected_case_ids']!=[item['case_id']]
            or len(req['case_inputs'])!=1 or req['case_inputs'][0]['case_id']!=item['case_id']
            or hash_(req['case_inputs'])!=item['request_input_hash'] or hash_(req['feedback'])!=item['feedback_hash']
            or job['case_id']!=item['case_id'] or job['arm']!=item['arm'] or job['input_hash']!=item['request_input_hash'] or job['feedback_hash']!=item['feedback_hash']):raise ValueError('Unavailable frozen request identity changed')
        approved[key]=item
    if set(approved)!=pending or amendment['unavailable_request_keys']!=sorted(pending):raise ValueError('Require all nine exact pending identities')
    if any(approved[k]!=v for k,v in prior['approved'].items()):raise ValueError('Eight prior unavailable identities changed')
    newkey=next(iter(pending-set(prior['approved'])));new=approved[newkey]
    if new['arm']!='feedback_repair' or new['case_id'] in {x['case_id'] for x in prior['approved'].values()}:raise ValueError('Only one newly partial repair case permitted')
    partner=[j for j in dispatch if j['case_id']==new['case_id'] and j['arm']=='fresh_retry']
    if len(partner)!=1 or partner[0]['request_key'] not in prefix or partner[0]['request_key'] in pending:raise ValueError('Known fresh partner must be retained')
    partner=partner[0];cases=sorted({x['case_id'] for x in approved.values()})
    if len(cases)!=5 or amendment['unavailable_case_ids']!=cases:raise ValueError('Five exact incomplete cases required')
    if amendment['previous_analysis_plan']!=prior['amendment']['analysis_plan']:raise ValueError('Previous003analysis binding changed')
    analysis=read(bound(data,amendment['analysis_plan']))
    expected={'scheduled_pairs':600,'observed_pair_target':595,'unknown_outcomes':9,'unknown_whole_pairs':4,'unknown_partial_pairs':1,'hypothetical_completions':512,'bootstrap_samples':20000,'bootstrap_seed':246600,'unknown_request_keys':sorted(pending),'unknown_case_ids':cases,'partial_pair_case_id':new['case_id'],'known_partner_request_key':partner['request_key'],'known_partners':[{'case_id':new['case_id'],'arm':'fresh_retry','request_key':partner['request_key'],'cache_sha256':prefix[partner['request_key']]}]}
    if any(analysis.get(k)!=v for k,v in expected.items()):raise ValueError('New006 missingness plan differs from exact metadata/fixed analysis')
    if amendment.get('remaining_unsent_jobs')!=52 or amendment.get('recorded_arm_requests')!=1148 or amendment.get('retained_terminal_arm_requests')!=1139:raise ValueError('Wrong continuation size')
    return dict(root=root,data=data,main=main,amendment=amendment,amendment_sha256=sha(amendment_path),inventory=prefix,
                approved=approved,retained=retained,retained_transport_failures=failures,retained_transport_failure_request_keys=sorted(retained),old=old,core=core,prior=prior,unsent_request_keys={x['request_key'] for x in dispatch[1148:]})


def startup_expected(amendment_sha256,nonce):
 import psutil
 if not isinstance(nonce,str) or len(nonce)!=32 or any(c not in '0123456789abcdef' for c in nonce):raise ValueError('Exact startup nonce required')
 source=globals().get('__file__')
 if source is None:raise ValueError('Live entry requires its exact saved collector script')
 return dict(protocol='23-scale-v5',collector_pid=os.getpid(),collector_created_at_utc=datetime.fromtimestamp(psutil.Process().create_time(),timezone.utc).isoformat(),script=str(Path(source).resolve()),amendment_sha256=amendment_sha256,startup_nonce=nonce,containment_job_assigned=True,containment_job_limit_flags=0x2000)

def wait_startup_gate(path,expected,timeout_s=60):
 if path is None or not Path(path).is_absolute():raise ValueError('Live dispatch requires an absolute worker startup gate')
 path=Path(path);deadline=time.monotonic()+timeout_s
 while not path.exists():
  if time.monotonic()>=deadline:raise TimeoutError('Worker did not authorize owned-job startup; no model calls permitted')
  time.sleep(.05)
 gate=json.loads(path.read_bytes())
 if any(gate.get(k)!=v or type(gate.get(k)) is not type(v) for k,v in expected.items()):raise ValueError('Startup gate child/creation/script/amendment/job/nonce mismatch')
 if type(gate.get('worker_pid')) is not int or gate['worker_pid']<=0:raise ValueError('Startup gate worker identity required')
 return gate

def scale_intervention_resume_006_install(root,amendment_path,namespace=None,startup_gate=None,startup_nonce=None):
    state=scale_intervention_resume_006_verify(root,amendment_path);old=state['old'];core=state['core']
    if namespace is None:
        prior_state=old['scale_intervention_resume_005_install'](root,state['data']/state['amendment']['predecessor']['path']);namespace=prior_state['namespace']
    else:
        prior_state=namespace.get('SCALE_INTERVENTION_RESUME_005_INSTALLED')
        if not prior_state or prior_state['amendment_sha256']!=core['sir_sha'](state['data']/state['amendment']['predecessor']['path']):raise ValueError('Install bound005namespace first')
    if namespace.get('SCALE_INTERVENTION_RESUME_006_INSTALLED'):raise ValueError('Fresh namespace required')
    # Unwrap only the byte-bound 005 live-start wrapper. Its frozen_run already
    # bypasses the consumed 003 and 002 start receipts without altering files.
    wrapped=namespace['scale_run_interventions']
    values=inspect.getclosurevars(wrapped).nonlocals
    if 'frozen_run' not in values or not callable(values['frozen_run']):raise ValueError('Predecessor runtime closure changed')
    wrapped=values['frozen_run']
    frozen_run=wrapped;call_old=namespace['scale_call_model'];dispatch_old=namespace['scale_dispatch_waves'];sha=core['sir_sha'];lock=threading.Lock()
    lower=namespace['SCALE_INTERVENTION_RESUME_INSTALLED'];lower['inventory']=state['inventory'];lower['approved']=state['approved'];lower['amendment_sha256']=state['amendment_sha256']
    prior_state['inventory']=state['inventory'];namespace['SCALE_INTERVENTION_RESUME_004_INSTALLED']['inventory']=state['inventory'];namespace['SCALE_INTERVENTION_RESUME_003_INSTALLED']['inventory']=state['inventory'];state['namespace']=namespace;state['startup_gate']=startup_gate;state['startup_nonce']=startup_nonce
    def call(request,cache_dir,live=False,timeout_s=900,_runner=None):
        key=namespace['scale_request_key'](request)
        if Path(cache_dir).resolve()==state['main']/'cache':
            if timeout_s!=900:raise ValueError('Fixed900second request timeout required')
            if key in state['inventory']:
                if sha(Path(cache_dir)/(key+'.json.gz'))!=state['inventory'][key]:raise ValueError('Recorded cache changed; never resubmit')
            elif key not in state['unsent_request_keys']:raise ValueError('Only exact52unsent frozen requests permitted')
        return call_old(request,cache_dir,live=live,timeout_s=timeout_s,_runner=_runner)
    def dispatch(jobs,invoke,directory,max_workers=4,progress=None):
        if Path(directory).resolve()!=state['main']:return dispatch_old(jobs,invoke,directory,max_workers,progress)
        jobs=list(jobs)
        if jobs and all(j.get('arm')=='original' for j in jobs):return dispatch_old(jobs,invoke,directory,max_workers,progress)
        if any(j.get('arm') not in {'fresh_retry','feedback_repair'} for j in jobs):raise ValueError('Mixed or unexpected main dispatch arms')
        if max_workers!=4:raise ValueError('Fixed four-worker intervention scope required')
        rows=[];ledger=[]
        def work(job):
            key=job['request_key']
            try:
                if key in state['inventory'] and sha(state['main']/'cache'/(key+'.json.gz'))!=state['inventory'][key]:raise ValueError('Recorded cache changed')
                row,entry=invoke(job);unknown=state['approved'].get(key);retained=state['retained'].get(key)
                known=unknown or retained
                if known:
                    expected_error=core['SCALE_INTERVENTION_UNAVAILABLE'] if unknown else retained['error']
                    if (entry['cached_this_run'] is not True or row['transport_error']!=expected_error
                        or any(row[k]!=known[k] for k in ('case_id','arm','stage','sample','content_hash','request_input_hash','feedback_hash'))):raise ValueError('Known infrastructure identity changed')
                    if unknown:
                        row.update(outcome_unavailable=True,error_kind='outcome_unavailable');entry.update(outcome_unavailable=True,telemetry_status='raw_pending_preserved')
                    # The retained terminal row is otherwise unchanged. In
                    # particular, do not inspect or replace response/verification.
                if progress:
                    with lock:progress(dict(arm=row['arm'],case_id=row['case_id'],cached=entry['cached_this_run'],transport_failure=bool(row['transport_error']) and not bool(known),outcome_unavailable=bool(unknown),retained_transport_failure=bool(retained)))
                return dict(row=row,ledger=entry,exception=None,request_key=key,known_infrastructure=bool(known))
            except Exception as exc:return dict(row=None,ledger=None,exception=dict(type=type(exc).__name__,message=str(exc)),request_key=key)
        with ThreadPoolExecutor(max_workers=4) as pool:
            for start in range(0,len(jobs),4):
                wave=jobs[start:start+4];results=[f.result() for f in [pool.submit(work,j) for j in wave]]
                if any(x['exception'] or (x['row']['transport_error'] and not x.get('known_infrastructure')) for x in results):
                    path=core['sir_write'](state['main']/('infrastructure_stop_intervention_resume_006_'+state['amendment_sha256'][:12]+'.json'),dict(protocol='23-scale-v5',phase_complete=False,wave_index=start//4,wave_results=results,remaining_jobs_not_dispatched=len(jobs)-start-len(wave)),unique=True)
                    raise namespace['SCALE_InfrastructureStop']('New infrastructure error; wave drained; stop='+str(path))
                rows.extend(x['row'] for x in results);ledger.extend(x['ledger'] for x in results)
        return rows,ledger
    def run(root=Path('.'),live=False,progress=None):
        if Path(root).resolve()!=state['root']:raise ValueError('Wrong bound root')
        if live:
            wait_startup_gate(state['startup_gate'],startup_expected(state['amendment_sha256'],state['startup_nonce']))
            if (state['main']/'manifest.json').exists():raise ValueError('Already complete')
            current={p.name.removesuffix('.json.gz'):sha(p) for p in (state['main']/'cache').glob('*.json.gz')}
            if current!=state['inventory']:raise ValueError('Exact2268prefix required before live continuation')
            receipt=state['main']/('intervention_resume_006_start_'+state['amendment_sha256'][:12]+'.json')
            with receipt.open('x',encoding='utf-8') as f:json.dump(dict(amendment_sha256=state['amendment_sha256'],started_at_utc=datetime.now(timezone.utc).isoformat(),automatic_restart=False),f)
        return frozen_run(root=root,live=live,progress=progress)
    namespace.update(scale_call_model=call,scale_dispatch_waves=dispatch,scale_run_interventions=run,SCALE_INTERVENTION_RESUME_006_INSTALLED=state)
    return state


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('phase',choices=['interventions']);parser.add_argument('--root',type=Path,required=True);parser.add_argument('--amendment',type=Path,required=True);parser.add_argument('--live',action='store_true');parser.add_argument('--startup-gate',type=Path);parser.add_argument('--startup-nonce');args=parser.parse_args()
    if args.live and (args.startup_gate is None or args.startup_nonce is None):parser.error('--live requires the reviewed worker startup gate and nonce')
    state=scale_intervention_resume_006_install(args.root,args.amendment,startup_gate=args.startup_gate,startup_nonce=args.startup_nonce);count=[0]
    def progress(event):
        count[0]+=1;print(json.dumps(dict(event='request_terminal_or_unavailable',completed_this_phase=count[0],**event)),flush=True)
    result=state['namespace']['scale_run_interventions'](root=args.root,live=args.live,progress=progress)
    print(json.dumps(dict(phase=result['manifest']['phase'],amendment_sha256=state['amendment_sha256'])),flush=True)
if __name__=='__main__':main()

