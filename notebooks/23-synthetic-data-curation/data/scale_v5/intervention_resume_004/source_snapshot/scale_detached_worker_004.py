"""Hidden one-shot WMI worker with a temporary calling-thread idle-sleep lease.

No power plan is changed. Forced user sleep remains possible. The request ends
on child exit, launch error or the fixed sixteen-hour hard cap.
"""
import argparse,ctypes,hashlib,json,os,subprocess,sys,time,threading
from datetime import datetime,timezone
from pathlib import Path

ES_CONTINUOUS=0x80000000
ES_SYSTEM_REQUIRED=0x00000001
MAX_LEASE_SECONDS=16*60*60

def write_new(p,v):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')

def publish_ready(path,value):
 """Publish fully written ready bytes in one final Windows rename operation."""
 path=Path(path);temporary=path.with_name(path.name+'.complete.tmp')
 raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode('utf-8')
 with temporary.open('xb') as stream:
  stream.write(raw);stream.flush();os.fsync(stream.fileno())
 # Windows rename fails if destination exists. Nothing fallible follows this
 # publication before supervised waiting; the collector never sees partial JSON.
 os.rename(temporary,path)

def in_job():
 from ctypes import wintypes
 flag=wintypes.BOOL();kernel=ctypes.WinDLL('kernel32',use_last_error=True)
 kernel.GetCurrentProcess.restype=wintypes.HANDLE
 kernel.IsProcessInJob.argtypes=[wintypes.HANDLE,wintypes.HANDLE,ctypes.POINTER(wintypes.BOOL)];kernel.IsProcessInJob.restype=wintypes.BOOL
 if not kernel.IsProcessInJob(kernel.GetCurrentProcess(),None,ctypes.byref(flag)):raise ctypes.WinError(ctypes.get_last_error())
 return bool(flag.value)

def job_flags():
 from ctypes import wintypes
 class BASIC(ctypes.Structure):_fields_=[('perproc',ctypes.c_int64),('perjob',ctypes.c_int64),('flags',wintypes.DWORD),('minws',ctypes.c_size_t),('maxws',ctypes.c_size_t),('count',wintypes.DWORD),('affinity',ctypes.c_size_t),('priority',wintypes.DWORD),('scheduling',wintypes.DWORD)]
 class IO(ctypes.Structure):_fields_=[(n,ctypes.c_uint64) for n in ('a','b','c','d','e','f')]
 class EXT(ctypes.Structure):_fields_=[('basic',BASIC),('io',IO),('proc_mem',ctypes.c_size_t),('job_mem',ctypes.c_size_t),('peak_proc',ctypes.c_size_t),('peak_job',ctypes.c_size_t)]
 k=ctypes.WinDLL('kernel32',use_last_error=True);k.QueryInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)];k.QueryInformationJobObject.restype=wintypes.BOOL
 b=EXT();n=wintypes.DWORD()
 if not k.QueryInformationJobObject(None,9,ctypes.byref(b),ctypes.sizeof(b),ctypes.byref(n)):raise ctypes.WinError(ctypes.get_last_error())
 return b.basic.flags

class OwnedJob:
 """New unnamed job, owned only by this WMI worker; no breakaway flags."""
 def __init__(self,audit):
  from ctypes import wintypes
  self.audit=audit;self.handle=None;self.assigned=False
  class BASIC(ctypes.Structure):_fields_=[('perproc',ctypes.c_int64),('perjob',ctypes.c_int64),('flags',wintypes.DWORD),('minws',ctypes.c_size_t),('maxws',ctypes.c_size_t),('count',wintypes.DWORD),('affinity',ctypes.c_size_t),('priority',wintypes.DWORD),('scheduling',wintypes.DWORD)]
  class IO(ctypes.Structure):_fields_=[(n,ctypes.c_uint64) for n in ('a','b','c','d','e','f')]
  class EXT(ctypes.Structure):_fields_=[('basic',BASIC),('io',IO),('proc_mem',ctypes.c_size_t),('job_mem',ctypes.c_size_t),('peak_proc',ctypes.c_size_t),('peak_job',ctypes.c_size_t)]
  k=self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
  k.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR];k.CreateJobObjectW.restype=wintypes.HANDLE
  k.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD];k.SetInformationJobObject.restype=wintypes.BOOL
  k.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE];k.AssignProcessToJobObject.restype=wintypes.BOOL
  k.TerminateJobObject.argtypes=[wintypes.HANDLE,wintypes.UINT];k.TerminateJobObject.restype=wintypes.BOOL
  k.CloseHandle.argtypes=[wintypes.HANDLE];k.CloseHandle.restype=wintypes.BOOL
  handle=k.CreateJobObjectW(None,None)
  if not handle:raise ctypes.WinError(ctypes.get_last_error())
  try:
   limits=EXT();limits.basic.flags=0x2000
   if not k.SetInformationJobObject(handle,9,ctypes.byref(limits),ctypes.sizeof(limits)):raise ctypes.WinError(ctypes.get_last_error())
   self.handle=handle;self.audit(dict(event='owned_containment_job_created',limit_flags=0x2000,breakaway_allowed=False,handle_inherited=False))
  except BaseException:k.CloseHandle(handle);raise
 def assign(self,child):
  from ctypes import wintypes
  if not self.handle or self.assigned:raise RuntimeError('One owned child assignment only')
  if not self.kernel.AssignProcessToJobObject(self.handle,wintypes.HANDLE(int(child._handle))):raise ctypes.WinError(ctypes.get_last_error())
  self.assigned=True;self.audit(dict(event='owned_child_assigned_before_startup_gate',pid=child.pid,limit_flags=0x2000))
 def terminate(self):
  if self.handle and not self.kernel.TerminateJobObject(self.handle,0xE004):raise ctypes.WinError(ctypes.get_last_error())
  try:self.audit(dict(event='owned_job_terminated_on_worker_error',exit_code=0xE004,descendants_included=True))
  except Exception:pass
 def close(self):
  if self.handle:
   handle=self.handle;self.handle=None
   if not self.kernel.CloseHandle(handle):raise ctypes.WinError(ctypes.get_last_error())
   try:self.audit(dict(event='owned_job_closed',kill_on_close=True,descendants_included=True))
   except Exception:pass

class ExecutionLease:
 """Same-thread SYSTEM_REQUIRED request, with an independent release deadline."""
 def __init__(self,seconds,audit,set_state=None,clock=None,thread_id=None):
  if not 0<seconds<=MAX_LEASE_SECONDS:raise ValueError('Lease hard cap must be positive and at most16hours')
  if set_state is None:
   from ctypes import wintypes
   set_state=ctypes.WinDLL('kernel32',use_last_error=True).SetThreadExecutionState
   set_state.argtypes=[wintypes.DWORD];set_state.restype=wintypes.DWORD
  self.seconds=seconds;self.audit=audit;self.set_state=set_state;self.clock=clock or time.monotonic;self.thread_id=thread_id or threading.get_ident
  self.active=False;self.owner=None;self.deadline=None;self.child=None
 def acquire(self):
  if self.active or self.owner is not None:raise RuntimeError('One lease acquisition only')
  self.owner=self.thread_id();previous=self.set_state(ES_CONTINUOUS|ES_SYSTEM_REQUIRED)
  if not previous:raise RuntimeError('SetThreadExecutionState acquisition failed; child must not start')
  self.active=True;self.deadline=self.clock()+self.seconds
  self.audit(dict(event='lease_acquired',request_flags=ES_CONTINUOUS|ES_SYSTEM_REQUIRED,previous_state=int(previous),hard_cap_seconds=self.seconds,owner_thread=self.owner))
 def bind_child(self,identity):
  if not self.active or self.thread_id()!=self.owner:raise RuntimeError('Lease owner thread required')
  self.child=dict(identity);self.audit(dict(event='lease_bound_to_owned_child',child=self.child))
 def release(self,reason):
  if not self.active:return
  if self.thread_id()!=self.owner:raise RuntimeError('Lease must be released by its acquiring thread')
  result=self.set_state(ES_CONTINUOUS)
  if not result:raise RuntimeError('SetThreadExecutionState release failed')
  self.active=False;self.audit(dict(event='lease_released',request_flags=ES_CONTINUOUS,reason=reason,owner_thread=self.owner,child=self.child))
 def check_deadline(self):
  if self.active and self.clock()>=self.deadline:self.release('hard_cap_reached_no_child_termination')


def cleanup_owned_child(child,audit):
 """Use the retained Popen HANDLE, never a PID lookup or replacement process."""
 if child is None:return
 if child.poll() is None:
  try:child.terminate()
  except OSError:
   if child.poll() is None:raise
 child.wait(timeout=10)
 try:audit(dict(event='owned_child_cleaned_up_after_worker_error',pid=child.pid,handle_bound_cleanup=True))
 except Exception:pass  # Receipt/disk failure must not prevent owned cleanup.

def identify_owned_child(child,exe,program):
 import psutil
 owned=psutil.Process(child.pid);creation=owned.create_time();command=owned.cmdline()
 if command[1:]!=program or Path(owned.exe()).resolve()!=exe:raise RuntimeError('Owned child command identity mismatch')
 return dict(pid=child.pid,created_at_utc=datetime.fromtimestamp(creation,timezone.utc).isoformat(),executable=str(exe),script=program[1])

def supervise_owned_child(p,exe,program,lease,audit,job_present,flags,ancestors,_popen=None,_identify=None,_write=None,_job_factory=None):
 child=None;job=(_job_factory or OwnedJob)(audit);write=_write or write_new
 try:
  with open(p['stdout'],'xb') as out,open(p['stderr'],'xb') as err:
   child=(_popen or subprocess.Popen)([str(exe),*program],cwd=p['root'],stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP)
   # The trusted collector/probe waits at its startup gate and cannot dispatch.
   job.assign(child)
   identity=(_identify or identify_owned_child)(child,exe,program)
   lease.bind_child(identity)
   write(p['started'],dict(pid=child.pid,process_created_at_utc=identity['created_at_utc'],worker_pid=os.getpid(),worker_in_job=job_present,worker_job_limit_flags=flags,worker_ancestors=ancestors,automatic_restart=False,model_calls=0 if p['mode']=='probe' else None,mode=p['mode'],started_at_utc=datetime.now(timezone.utc).isoformat(),program=program,stdout=p['stdout'],stderr=p['stderr'],lease=p['lease'],lease_hard_cap_seconds=p['lease_hard_cap_s'],containment_job_limit_flags=0x2000,startup_gate=p['ready']))
   audit(dict(event='startup_gate_release_prepared_after_job_identity_lease_and_receipt',pid=child.pid,gate=p['ready']))
   (_write or publish_ready)(p['ready'],dict(protocol='23-scale-v5',collector_pid=identity['pid'],collector_created_at_utc=identity['created_at_utc'],script=identity['script'],amendment_sha256=p['amendment_sha256'],startup_nonce=p['startup_nonce'],containment_job_assigned=True,containment_job_limit_flags=0x2000,worker_pid=os.getpid()))
   if p.get('probe_cleanup'):
    deadline=time.monotonic()+10
    while not Path(p['probe_marker']).exists():
     if time.monotonic()>=deadline:raise RuntimeError('Harmless cleanup probe marker timeout')
     time.sleep(.05)
    raise RuntimeError('Intentional harmless owned-job descendant cleanup probe')
   while child.poll() is None:
    lease.check_deadline();time.sleep(.25)
   return child,child.wait()
 except BaseException:
  try:job.terminate()
  finally:cleanup_owned_child(child,audit)
  raise
 finally:job.close()

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--payload',type=Path,required=True);args=parser.parse_args();p=json.loads(args.payload.read_text(encoding='utf-8-sig'))
 job_present=in_job();flags=job_flags() if job_present else 0
 if flags&0x2000:raise RuntimeError('Worker job has KILL_ON_JOB_CLOSE; no study child may start')
 import psutil
 ancestors=[dict(pid=x.pid,name=x.name(),created_at_utc=datetime.fromtimestamp(x.create_time(),timezone.utc).isoformat()) for x in psutil.Process().parents()]
 if not any(x['name'].lower()=='wmiprvse.exe' for x in ancestors):raise RuntimeError('Worker must be created by WMI service')
 write_new(p['claim'],dict(pid=os.getpid(),started_at_utc=datetime.now(timezone.utc).isoformat(),automatic_restart=False))
 program=p['program'];exe=Path(p['python']).resolve();seconds=p['lease_hard_cap_s']
 if p['mode']=='probe':
  if seconds not in (2,10):raise ValueError('Only bounded harmless probe lease sizes')
  program=['-u',str(Path(__file__).with_name('probe_scale_containment_child_004.py')),'--ready',p['ready'],'--nonce',p['startup_nonce'],'--marker',p['probe_marker']]
 elif p['mode']=='study':
  if seconds!=MAX_LEASE_SECONDS or p.get('probe_cleanup'):raise ValueError('Study lease has fixed16hour cap and no probe faults')
  root=Path(p['root']).resolve();expected=root/'data/scale_v5/intervention_resume_004/source_snapshot/scale_intervention_resume_004.py';amendment=root/'data/scale_v5/intervention_resume_004/amendment_004.json'
  if Path(program[1]).resolve()!=expected or Path(program[6]).resolve()!=amendment:raise ValueError('Only exact reviewed004snapshot permitted')
  a=json.loads(amendment.read_bytes())
  if hashlib.sha256(expected.read_bytes()).hexdigest()!=a['implementation']['sha256']:raise ValueError('Implementation hash changed')
  if p['amendment_sha256']!=hashlib.sha256(amendment.read_bytes()).hexdigest():raise ValueError('Amendment hash changed')
  program+=['--startup-gate',p['ready'],'--startup-nonce',p['startup_nonce']]
 else:raise ValueError('Unknown launch mode')
 lease_path=Path(p['lease']);lease_path.open('x',encoding='utf-8').close()
 def audit(event):
  with lease_path.open('a',encoding='utf-8') as f:f.write(json.dumps(dict(at_utc=datetime.now(timezone.utc).isoformat(),**event),sort_keys=True)+'\n')
 lease=ExecutionLease(seconds,audit);child=None;code=None
 try:
  lease.acquire()  # Fail closed before Popen, on this same calling thread.
  child,code=supervise_owned_child(p,exe,program,lease,audit,job_present,flags,ancestors)
 finally:lease.release('owned_child_exited' if child is not None and child.poll() is not None else 'worker_launch_or_wait_error')
 write_new(p['finished'],dict(pid=child.pid,return_code=code,finished_at_utc=datetime.now(timezone.utc).isoformat(),automatic_restart=False,mode=p['mode'],lease_active=lease.active))
if __name__=='__main__':
 try:main()
 except Exception as exc:
  payload=Path(sys.argv[sys.argv.index('--payload')+1]);write_new(payload.with_suffix('.error.json'),dict(type=type(exc).__name__,message=str(exc),pid=os.getpid(),model_calls=None));raise
