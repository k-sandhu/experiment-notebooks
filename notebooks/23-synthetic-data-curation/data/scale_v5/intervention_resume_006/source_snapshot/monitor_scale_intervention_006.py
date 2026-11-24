"""Metadata-only observation for a reviewed006launch. Never runs a model."""
import argparse,gzip,hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
import psutil
BASE=Path(__file__).resolve().parent
ROOT=BASE.parent/'experiment_notebooks/notebooks/23-synthetic-data-curation';DATA=ROOT/'data/scale_v5';MAIN=DATA/'main'
STATUS=BASE/'scale_intervention_006_operational_status.json';JOURNAL=BASE/'scale_intervention_006_operational_events.jsonl'
def read(path):
 raw=Path(path).read_bytes();return json.loads(gzip.decompress(raw) if Path(path).suffix=='.gz' else raw)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def identity(pid,expected_creation=None):
 try:
  p=psutil.Process(pid);created=datetime.fromtimestamp(p.create_time(),timezone.utc).isoformat()
  if expected_creation is not None and created!=expected_creation:return None
  return dict(pid=pid,created_at_utc=created,parent_pid=p.ppid(),executable=p.exe(),command_line=p.cmdline())
 except psutil.NoSuchProcess:return None

def completion_gate(main,finished):
 main=Path(main);manifest=main/'manifest.json';phase=read(manifest).get('phase') if manifest.exists() else None
 paths=[main/'exports'/arm/(name+'.jsonl.gz') for arm in ('original','fresh_retry','feedback_repair') for name in ('accepted_examples','rejected_examples','value_preference_pairs')]+[main/'exports/curated_unique.jsonl.gz']
 return dict(manifest_phase=phase,expected_export_files=10,export_files_present=sum(p.is_file() for p in paths),clean_finished_receipt=bool(finished and finished.get('return_code')==0),complete=bool(phase=='interventions_complete' and finished and finished.get('return_code')==0 and all(p.is_file() for p in paths)))

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--launch-receipt',type=Path,required=True);args=parser.parse_args();launch=read(args.launch_receipt);started=read(launch['started']);payload=read(launch['payload'])
 if STATUS.exists():
  previous=read(STATUS)
  if previous.get('monitor_pid') and identity(previous['monitor_pid'],previous.get('monitor_created_at_utc')):raise RuntimeError('An exact006monitor is already active')
 if launch.get('mode')!='study' or launch.get('live_requested') is not True or launch.get('automatic_restart') is not False:raise RuntimeError('Exactone-shot live006receipt required')
 collector=identity(started['pid'],started['process_created_at_utc']);worker=identity(started['worker_pid'])
 if not collector or not worker:raise RuntimeError('Ownedprocess absent beforemonitorstart; never restart collector')
 expected=DATA/'intervention_resume_006/source_snapshot/scale_intervention_resume_006.py'
 amendment=DATA/'intervention_resume_006/amendment_006.json';amendment_sha=sha(amendment);ready=read(launch['startup_gate'])
 if (payload.get('amendment_sha256')!=amendment_sha or ready.get('amendment_sha256')!=amendment_sha or payload.get('startup_nonce')!=ready.get('startup_nonce') or Path(payload['program'][1]).resolve()!=expected.resolve() or Path(payload['program'][6]).resolve()!=amendment.resolve() or Path(payload['program'][4]).resolve()!=ROOT.resolve() or ready.get('collector_pid')!=collector['pid'] or ready.get('collector_created_at_utc')!=collector['created_at_utc']):raise RuntimeError('Launch payload, ready gate and exact006amendment binding required')
 if Path(collector['command_line'][2]).resolve()!=expected.resolve():raise RuntimeError('Exact006collector script required')
 expected_worker=DATA/'intervention_resume_006/source_snapshot/scale_detached_worker_006.py'
 if (Path(worker['command_line'][1]).resolve()!=expected_worker.resolve() or Path(worker['command_line'][-1]).resolve()!=Path(launch['payload']).resolve() or collector['parent_pid']!=worker['pid']):raise RuntimeError('Exact006worker/payload/parent identity required')
 prefix=read(DATA/'intervention_resume_006/prior_cache_inventory_006.json')['requests'];assert len(prefix)==2268
 assert all(sha(MAIN/'cache'/(key+'.json.gz'))==digest for key,digest in prefix.items())
 state=dict(protocol='23-scale-v5',monitor_version='outcome-blind-006-v1',monitor_pid=psutil.Process().pid,monitor_created_at_utc=datetime.fromtimestamp(psutil.Process().create_time(),timezone.utc).isoformat(),phase='interventions_collecting',collector=collector,worker=worker,launch_receipt=str(args.launch_receipt),started_receipt=launch['started'],stdout=launch['stdout'],stderr=launch['stderr'],lease=launch['lease'],startup_gate=launch['startup_gate'],worker_job_limit_flags=started['worker_job_limit_flags'],owned_collector_job_limit_flags=started['containment_job_limit_flags'],automatic_restart=False,scheduled_pairs=600,scheduled_arm_slots=1200,preexisting_cache_count=2268,prior_unknown_slots=9,prior_retained_terminal_errors=2,remaining_unsent_at_launch=52,prefix_integrity_verified=True,prefix_integrity_verified_at_utc=now(),model_outputs_accessed=False,verification_flags_accessed=False,arm_recovery_rates_accessed=False,processed_arm_slots=0,new_terminal_slots_this_continuation=0,unavailable_slots_processed=0,retained_transport_failures_processed=0,new_transport_failure_events=0)
 def save(event):
  state['checked_at_utc']=now();state['stderr_bytes']=Path(launch['stderr']).stat().st_size;state['recorded_cache_count']=len(list((MAIN/'cache').glob('*.json.gz')))
  temporary=STATUS.with_suffix('.tmp');temporary.write_text(json.dumps(state,sort_keys=True,indent=2)+'\n',encoding='utf-8');temporary.replace(STATUS)
  with JOURNAL.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(event=event,**state),sort_keys=True)+'\n')
 save('monitor_started');offset=0;last_save=time.monotonic()
 while True:
  with Path(launch['stdout']).open('rb') as f:f.seek(offset);chunk=f.read()
  complete=chunk.rfind(b'\n')
  if complete>=0:
   lines=chunk[:complete+1].splitlines();offset+=complete+1
   for line in lines:
    event=json.loads(line)
    if event.get('event')=='request_terminal_or_unavailable':
     state['processed_arm_slots']=event['completed_this_phase'];state['new_terminal_slots_this_continuation']+=event['cached'] is False;state['unavailable_slots_processed']+=event.get('outcome_unavailable') is True;state['retained_transport_failures_processed']+=event.get('retained_transport_failure') is True;state['new_transport_failure_events']+=event.get('transport_failure') is True
     if event.get('transport_failure') is True:save('new_transport_failure');print(json.dumps(dict(operational_alert='new_transport_failure',processed_arm_slots=state['processed_arm_slots'])),flush=True)
     elif state['processed_arm_slots']%4==0:save('wave_progress');last_save=time.monotonic()
  finished=read(launch['finished']) if Path(launch['finished']).exists() else None
  state.update(completion_gate(MAIN,finished));state['collector_present_matching_creation']=identity(collector['pid'],collector['created_at_utc']) is not None;state['worker_present_matching_creation']=identity(worker['pid'],worker['created_at_utc']) is not None
  lease_raw=Path(launch['lease']).read_bytes();lease_complete=lease_raw.rfind(b'\n');lease_events=[json.loads(line) for line in lease_raw[:lease_complete+1].splitlines()] if lease_complete>=0 else []
  state['lease_active']=bool(lease_events and not any(e['event']=='lease_released' for e in lease_events));state['lease_release_reason']=next((e['reason'] for e in reversed(lease_events) if e['event']=='lease_released'),None)
  if finished or (not state['collector_present_matching_creation'] and not state['worker_present_matching_creation']):
   state['finished_receipt']=finished;state['phase']='interventions_complete' if state['complete'] else 'infrastructure_stopped_or_incomplete'
   state['prefix_integrity_verified']=all(sha(MAIN/'cache'/(key+'.json.gz'))==digest for key,digest in prefix.items());state['prefix_integrity_verified_at_utc']=now();terminal=pending=0;pending_keys=set()
   for job in read(MAIN/'dispatch.json')['jobs']:
    path=MAIN/'cache'/(job['request_key']+'.json.gz')
    if path.exists():
     attempts=read(path)['attempts'];assert len(attempts)==1
     if attempts[0].get('pending') is True:pending+=1;pending_keys.add(job['request_key'])
     elif attempts[0].get('pending') is False:terminal+=1
     else:raise RuntimeError('Invalid attemptmetadata')
   state.update(terminal_arm_records=terminal,pending_arm_slots=pending,unrecorded_arm_slots=1200-terminal-pending)
   expected_pending=set(read(DATA/'intervention_resume_006/amendment_006.json')['unavailable_request_keys'])
   state['pending_request_keys_preserved']=pending_keys==expected_pending
   state['complete']=bool(state['complete'] and state['prefix_integrity_verified'] and terminal==1191 and pending==9 and pending_keys==expected_pending and state['processed_arm_slots']==1200 and state['new_terminal_slots_this_continuation']==52 and state['new_transport_failure_events']==0 and state['unavailable_slots_processed']==9 and state['retained_transport_failures_processed']==2)
   state['phase']='interventions_complete' if state['complete'] else 'infrastructure_stopped_or_incomplete'
   save('monitor_terminal');print(json.dumps(state),flush=True);return
  if time.monotonic()-last_save>=60:save('metadata_heartbeat');last_save=time.monotonic()
  time.sleep(2)
if __name__=='__main__':main()
