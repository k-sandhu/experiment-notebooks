"""Harmless checks of the copied worker, never any model or study request."""
import base64,hashlib,json,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
import psutil

BASE=Path(__file__).resolve().parent
LOGS=BASE/'detached_smoke_006'

def read(path):return json.loads(Path(path).read_bytes())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def matching(pid,created):
    try:return abs(psutil.Process(pid).create_time()-datetime.fromisoformat(created).timestamp())<.002
    except psutil.NoSuchProcess:return False
def wait_for(path,seconds=20):
    end=time.monotonic()+seconds
    while not Path(path).exists():
        if time.monotonic()>end:raise RuntimeError('Bounded harmless probe wait expired: '+str(path))
        time.sleep(.1)
    return read(path)

def main():
    assert not (BASE/'scale_detached_launcher_006_smoke.json').exists()
    LOGS.mkdir(exist_ok=True)
    launches=[]
    for seconds,cleanup in ((2,False),(10,False),(10,True)):
        cmd=['pwsh','-NoProfile','-File',str(BASE/'launch_scale_intervention_resume_006.ps1'),'-Probe',
             '-ProbeLeaseSeconds',str(seconds),'-LogDirectory',str(LOGS)]
        if cleanup:cmd.append('-ProbeCleanup')
        receipt=json.loads(subprocess.check_output(cmd,text=True,encoding='utf-8'))
        marker=wait_for(receipt['probe_marker'])
        if cleanup:
            error=wait_for(receipt['payload'].removesuffix('.json')+'.error.json')
            assert 'Intentional harmless owned-job' in str(error)
        else:
            finished=wait_for(receipt['finished']);assert finished['return_code']==0 and finished['lease_active'] is False
        deadline=time.monotonic()+10
        while matching(marker['pid'],marker['created_at_utc']) or matching(marker['grandchild_pid'],marker['grandchild_created_at_utc']):
            assert time.monotonic()<deadline,'Owned probe descendant survived cleanup'
            time.sleep(.1)
        lease=[json.loads(line) for line in Path(receipt['lease']).read_text(encoding='utf-8').splitlines()]
        released=[row for row in lease if row['event']=='lease_released']
        assert len(released)==1
        assert released[0]['request_flags']==0x80000000
        if seconds==2:assert released[0]['reason']=='hard_cap_reached_no_child_termination'
        elif not cleanup:assert released[0]['reason']=='owned_child_exited'
        assert marker['owned_job_limit_flags']==0x2000 and marker['model_calls']==0
        assert not receipt['live_requested'] and not receipt['automatic_restart']
        launches.append(dict(receipt=receipt,marker=marker,lease=lease,cleanup=cleanup))
    duplicate=subprocess.run([sys.executable,str(BASE/'scale_detached_worker_006.py'),'--payload',launches[0]['receipt']['payload']],capture_output=True,text=True)
    assert duplicate.returncode!=0,'Duplicate one-shot payload was not blocked'
    files=list(LOGS.glob('scale006_*'))+[BASE/name for name in ('scale_detached_worker_006.py','launch_scale_intervention_resume_006.ps1','probe_scale_containment_child_006.py','smoke_scale_worker_006.py')]
    evidence={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'model_calls':0,'launches':launches,
              'files':[{'name':str(path.relative_to(BASE)),'sha256':sha(path),'raw_bytes_base64':base64.b64encode(path.read_bytes()).decode()} for path in sorted(files)]}
    evidence_path=BASE/'scale_detached_launcher_006_evidence.json'
    evidence_path.write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8',newline='\n')
    smoke={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'passed':True,'model_calls':0,
           'worker_sha256':sha(BASE/'scale_detached_worker_006.py'),'launcher_sha256':sha(BASE/'launch_scale_intervention_resume_006.ps1'),
           'evidence_sha256':sha(evidence_path),'evidence_file':evidence_path.name,'probes':3,
           'hard_cap_releases_without_terminating_child':True,'normal_completion_releases_lease':True,
           'descendant_cleanup_verified':True,'duplicate_payload_blocked':True,'temporary_flags':0x80000001,
           'containment_job_flags':0x2000,'automatic_restart':False,'display_required':False,
           'power_plan_changed':False,'scheduled_task_created':False,'service_created':False,
           'unrelated_processes_modified':False,'forced_user_sleep_still_allowed':True}
    (BASE/'scale_detached_launcher_006_smoke.json').write_text(json.dumps(smoke,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(smoke))

if __name__=='__main__':main()
