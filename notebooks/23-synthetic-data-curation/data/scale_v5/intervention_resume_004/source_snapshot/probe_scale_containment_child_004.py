"""Harmless child and long-lived grandchild. No model CLI or network access."""
import argparse,ctypes,json,os,subprocess,sys,time
from ctypes import wintypes
from datetime import datetime,timezone
from pathlib import Path
import psutil
p=argparse.ArgumentParser();p.add_argument('--ready',type=Path,required=True);p.add_argument('--nonce',required=True);p.add_argument('--marker',type=Path,required=True);a=p.parse_args()
created=datetime.fromtimestamp(psutil.Process().create_time(),timezone.utc).isoformat();deadline=time.monotonic()+60
while not a.ready.exists():
 if time.monotonic()>=deadline:raise RuntimeError('No startup gate; no grandchild may start')
 time.sleep(.05)
g=json.loads(a.ready.read_bytes())
assert g['collector_pid']==os.getpid() and g['collector_created_at_utc']==created and g['script']==str(Path(__file__).resolve()) and g['startup_nonce']==a.nonce and g['containment_job_assigned'] is True and g['containment_job_limit_flags']==0x2000
k=ctypes.WinDLL('kernel32',use_last_error=True);k.QueryInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)];k.QueryInformationJobObject.restype=wintypes.BOOL
buf=ctypes.create_string_buffer(144);length=wintypes.DWORD()
if not k.QueryInformationJobObject(None,9,buf,144,ctypes.byref(length)):raise ctypes.WinError(ctypes.get_last_error())
flags=int.from_bytes(buf.raw[16:20],'little');assert flags==0x2000
child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(300)'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
meta=dict(probe_started=True,pid=os.getpid(),created_at_utc=created,grandchild_pid=child.pid,grandchild_created_at_utc=datetime.fromtimestamp(psutil.Process(child.pid).create_time(),timezone.utc).isoformat(),owned_job_limit_flags=flags,model_calls=0)
with a.marker.open('x',encoding='utf-8') as f:json.dump(meta,f);f.write('\n')
print(json.dumps(meta),flush=True);time.sleep(4);print(json.dumps(dict(probe_finished=True)),flush=True)
