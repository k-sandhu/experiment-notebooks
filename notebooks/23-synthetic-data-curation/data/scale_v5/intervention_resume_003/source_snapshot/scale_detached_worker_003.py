"""One-shot WMI-created hidden worker, with a service ancestry and job-limit gate."""
import argparse,ctypes,hashlib,json,os,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path

def write_new(p,v):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
def in_job():
 from ctypes import wintypes
 flag=wintypes.BOOL();kernel=ctypes.WinDLL('kernel32',use_last_error=True)
 kernel.GetCurrentProcess.restype=wintypes.HANDLE
 kernel.IsProcessInJob.argtypes=[wintypes.HANDLE,wintypes.HANDLE,ctypes.POINTER(wintypes.BOOL)]
 kernel.IsProcessInJob.restype=wintypes.BOOL
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

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--payload',type=Path,required=True);parser.add_argument('--escaped',action='store_true');args=parser.parse_args();p=json.loads(args.payload.read_text(encoding='utf-8-sig'))
 job_present=in_job();flags=job_flags() if job_present else 0
 # WMI hosts have their own service job (observed flags0x1800), separate
 # from tool-session job0x2800. Reject every kill-on-close job before calls.
 if flags & 0x2000:raise RuntimeError('Worker job has KILL_ON_JOB_CLOSE; no study child may start')
 import psutil
 ancestors=[dict(pid=x.pid,name=x.name(),created_at_utc=datetime.fromtimestamp(x.create_time(),timezone.utc).isoformat()) for x in psutil.Process().parents()]
 if not any(x['name'].lower()=='wmiprvse.exe' for x in ancestors):raise RuntimeError('Worker must be created by WMI service')
 # A duplicate invocation with the same payload cannot spawn twice.
 write_new(p['claim'],dict(pid=os.getpid(),started_at_utc=datetime.now(timezone.utc).isoformat(),automatic_restart=False))
 program=p['program'];exe=Path(p['python']).resolve()
 if p['mode']=='probe':
  program=['-u','-c',"import time,json,os; print(json.dumps({'probe_started':True,'pid':os.getpid()}),flush=True); time.sleep(4); print(json.dumps({'probe_finished':True}),flush=True)"]
 elif p['mode']=='study':
  root=Path(p['root']).resolve();expected=root/'data/scale_v5/intervention_resume_003/source_snapshot/scale_intervention_resume_003.py';amendment=root/'data/scale_v5/intervention_resume_003/amendment_003.json'
  if Path(program[1]).resolve()!=expected or Path(program[6]).resolve()!=amendment:raise ValueError('Only exact reviewed003snapshot permitted')
  a=json.loads(amendment.read_bytes())
  if hashlib.sha256(expected.read_bytes()).hexdigest()!=a['implementation']['sha256']:raise ValueError('Implementation hash changed')
 else:raise ValueError('Unknown launch mode')
 with open(p['stdout'],'xb') as out,open(p['stderr'],'xb') as err:
  child=subprocess.Popen([str(exe),*program],cwd=p['root'],stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP)
  write_new(p['started'],dict(pid=child.pid,worker_pid=os.getpid(),worker_in_job=job_present,worker_job_limit_flags=flags,worker_ancestors=ancestors,automatic_restart=False,model_calls=0 if p['mode']=='probe' else None,mode=p['mode'],started_at_utc=datetime.now(timezone.utc).isoformat(),program=program,stdout=p['stdout'],stderr=p['stderr']))
  code=child.wait()
 write_new(p['finished'],dict(pid=child.pid,return_code=code,finished_at_utc=datetime.now(timezone.utc).isoformat(),automatic_restart=False,mode=p['mode']))
if __name__=='__main__':
 try:main()
 except Exception as exc:
  payload=Path(sys.argv[sys.argv.index('--payload')+1]);target=payload.with_suffix('.error.json')
  write_new(target,dict(type=type(exc).__name__,message=str(exc),pid=os.getpid(),model_calls=None))
  raise
