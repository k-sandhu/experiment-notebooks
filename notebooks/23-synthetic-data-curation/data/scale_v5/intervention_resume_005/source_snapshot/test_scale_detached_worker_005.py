"""Pure mocked execution-state calls. No process or real power requests."""
import unittest,tempfile
from pathlib import Path
from scale_detached_worker_005 import ExecutionLease,ES_CONTINUOUS,ES_SYSTEM_REQUIRED,supervise_owned_child,publish_ready
class Tests(unittest.TestCase):
 def setUp(self):self.calls=[];self.events=[];self.clock=[0.0];self.thread=[123]
 def lease(self,seconds=2,ret=ES_CONTINUOUS):
  def call(flags):self.calls.append(flags);return ret
  return ExecutionLease(seconds,self.events.append,call,lambda:self.clock[0],lambda:self.thread[0])
 def test_acquire_bind_release_same_thread(self):
  s=self.lease();s.acquire();s.bind_child({'pid':99,'created_at_utc':'exact','script':'reviewed.py'});s.release('owned_child_exited');self.assertEqual(self.calls,[ES_CONTINUOUS|ES_SYSTEM_REQUIRED,ES_CONTINUOUS]);self.assertFalse(s.active)
 def test_acquisition_failure_is_closed(self):
  s=self.lease(ret=0)
  with self.assertRaises(RuntimeError):s.acquire()
  self.assertFalse(s.active);self.assertEqual(self.calls,[ES_CONTINUOUS|ES_SYSTEM_REQUIRED])
 def test_hardcap_releases_without_child_action(self):
  s=self.lease();s.acquire();self.clock[0]=2;s.check_deadline();s.check_deadline();self.assertFalse(s.active);self.assertEqual(self.calls,[0x80000001,0x80000000]);self.assertEqual(self.events[-1]['reason'],'hard_cap_reached_no_child_termination')
 def test_release_on_spawn_failure_finally(self):
  s=self.lease()
  try:
   s.acquire();raise OSError('mocked spawn failure')
  except OSError:pass
  finally:s.release('worker_launch_or_wait_error')
  self.assertFalse(s.active);self.assertEqual(self.calls[-1],ES_CONTINUOUS)
 def test_no_reacquire_or_wrong_thread(self):
  s=self.lease();s.acquire()
  with self.assertRaises(RuntimeError):s.acquire()
  self.thread[0]=124
  with self.assertRaises(RuntimeError):s.release('wrong thread')
  self.thread[0]=123;s.release('cleanup')
 def test_release_failure_visible(self):
  s=self.lease();s.acquire();s.set_state=lambda flags:0
  with self.assertRaises(RuntimeError):s.release('failure')
  self.assertTrue(s.active)
 def test_hard_cap_cannot_exceed16hours(self):
  with self.assertRaises(ValueError):self.lease(57601)
  with self.assertRaises(ValueError):self.lease(0)
 def test_post_spawn_faults_cleanup_owned_job_and_clear_lease(self):
  for fault in ('assignment','identity','bind','receipt','audit','ready','wait'):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as directory:
    actions=[]
    class Child:
     pid=909;_handle=object()
     def __init__(self):self.dead=False;self.terminated_handle=None;self.waited=0
     def poll(self):return 1 if self.dead else None
     def terminate(self):self.terminated_handle=self._handle;self.dead=True
     def wait(self,timeout=None):self.waited+=1;return 1
    child=Child()
    class Job:
     assigned=False;terminated=False;closed=False;descendant_alive=True
     def assign(self,c):
      actions.append('assign')
      if fault=='assignment':raise OSError('mocked assignment failure')
      self.assigned=True
     def terminate(self):
      self.terminated=True;self.descendant_alive=False
      if self.assigned:child.dead=True
     def close(self):self.closed=True;self.descendant_alive=False
    job=Job();lease=self.lease();root=Path(directory);p=dict(root=directory,stdout=str(root/'out'),stderr=str(root/'err'),started=str(root/'started'),ready=str(root/'ready'),mode='probe',lease=str(root/'lease'),lease_hard_cap_s=2,amendment_sha256='mock',startup_nonce='a'*32)
    def fail(*args,**kwargs):raise OSError('mocked '+fault+' failure')
    def identity(*args):actions.append('identity');return dict(pid=909,created_at_utc='exact-create',script='exact.py')
    def write(path,value):
     action='ready' if str(path).endswith('ready') else 'receipt';actions.append(action)
     if fault==action:raise OSError('mocked '+fault+' failure')
    if fault=='bind':lease.bind_child=fail
    if fault=='wait':lease.check_deadline=fail
    def audit(event):
     if fault=='audit' and event.get('event','').startswith('startup_gate_release_prepared'):raise OSError('mocked audit failure before gate')
     self.events.append(event)
    lease.acquire()
    try:
     with self.assertRaises(OSError):supervise_owned_child(p,Path('python.exe'),['-u','exact.py'],lease,audit,False,0,[],_popen=lambda *a,**k:child,_identify=fail if fault=='identity' else identity,_write=write,_job_factory=lambda audit:job)
    finally:lease.release('mocked error cleanup')
    self.assertTrue(job.terminated);self.assertTrue(job.closed);self.assertFalse(job.descendant_alive);self.assertGreaterEqual(child.waited,1);self.assertFalse(lease.active);self.assertEqual(self.calls[-1],ES_CONTINUOUS)
    if fault=='assignment':self.assertIs(child.terminated_handle,child._handle)
    if fault in ('assignment','identity','bind','receipt','audit'):self.assertNotIn('ready',actions)
    if 'ready' in actions:self.assertLess(actions.index('assign'),actions.index('ready'));self.assertLess(actions.index('receipt'),actions.index('ready'))
 def test_spawn_failure_clears_lease_without_a_child(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);p=dict(root=directory,stdout=str(root/'out'),stderr=str(root/'err'))
   class EmptyJob:
    def terminate(self):pass
    def close(self):pass
   def fail(*args,**kwargs):raise OSError('mocked Popen failure')
   lease=self.lease();lease.acquire()
   try:
    with self.assertRaises(OSError):supervise_owned_child(p,Path('python.exe'),[],lease,self.events.append,False,0,[],_popen=fail,_job_factory=lambda audit:EmptyJob())
   finally:lease.release('spawn failure')
   self.assertFalse(lease.active);self.assertEqual(self.calls[-1],ES_CONTINUOUS)
 def test_atomic_ready_publication_preserves_existing_gate(self):
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'ready.json';publish_ready(path,{'complete':True})
   import json
   self.assertEqual(json.loads(path.read_bytes()),{'complete':True})
   with self.assertRaises(FileExistsError):publish_ready(path,{'replaced':True})
   self.assertEqual(json.loads(path.read_bytes()),{'complete':True})
if __name__=='__main__':unittest.main()
