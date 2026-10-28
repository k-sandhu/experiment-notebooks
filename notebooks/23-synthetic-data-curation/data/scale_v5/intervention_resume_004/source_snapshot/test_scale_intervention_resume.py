"""Temporary mocked files only; no study writes or model calls."""
import copy
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import scale_intervention_resume as resume


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.data = self.root / 'data/scale_v5'; self.main = self.data / 'main'
        self.cache = self.main / 'cache'; self.cache.mkdir(parents=True)
        self.new_calls = []; self.progress = []
        self.profile = dict(model='gpt-6.1-sol', reasoning_effort='high', protocol='23-scale-v5', timeout_s=900)
        self.requests = {}; self.dispatch = []; self.plan = []; self.jobs = []; self.inventory = {}
        originals = []
        for index in range(1120):
            req = self.request('original-'+str(index), 'generate', 0)
            key = resume.sir_hash(req); originals.append(key); self.record(req)
        for index in range(1200):
            cid = 'pair-'+str(index//2); arm = 'fresh_retry' if index%2 == 0 else 'feedback_repair'
            stage, sample = ('generate', 1) if index%2 == 0 else ('repair', 0)
            req = self.request(cid, stage, sample); key = resume.sir_hash(req)
            item = dict(request_key=key, case_id=cid, arm=arm, input_hash=resume.sir_hash(req['case_inputs']), feedback_hash=resume.sir_hash(req['feedback']))
            self.dispatch.append(item); self.plan.append(dict(request_key=key,case_id=cid,arm=arm,stage=stage,sample=sample,source_hash='source-'+cid))
            self.requests[key] = req
            self.jobs.append(dict(request_key=key, case={'case_id':cid}, arm=arm, stage=stage, sample=sample))
            if index < 120: self.record(req, pending=index>=116)
        self.write('main/original_manifest.json', dict(phase='originals_complete',request_keys=originals))
        self.write('main/dispatch.json', dict(jobs=self.dispatch))
        self.write('main/request_plans/arms.json', self.plan)
        companion = '''def scale_resume_install(root, path, namespace):
 namespace.setdefault('SCALE_RESUME_INSTALLED', {'approved':{}})
def scale_resume_write(path, value, unique=False):
 from pathlib import Path
 import json
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 for i in range(100):
  target=path if not i else path.with_name(path.stem+'_'+str(i)+path.suffix)
  try:
   with target.open('x',encoding='utf-8') as f:json.dump(value,f)
   return target
  except FileExistsError:pass
'''
        self.write_bytes('infrastructure_resume/source_snapshot/scale_resume.py', companion.encode())
        self.write('infrastructure_resume/amendment_001.json',dict(implementation=self.binding('infrastructure_resume/source_snapshot/scale_resume.py')))
        self.write('source_freeze.json',{'protocol':'23-scale-v5','source_sha256':{}})
        gate = {'phase':'interventions_authorized_after_independent_audit','sha256':{}}
        for i in range(37):
            name='bound/'+str(i)+'.json'; self.write(name,{'input':i}); gate['sha256'][name]=resume.sir_sha(self.data/name)
        gate['sha256']['main/original_manifest.json']=resume.sir_sha(self.main/'original_manifest.json')
        self.write('intervention_start_declaration.json',gate)
        self.write('intervention_resume/implementation.py',{'source':'mock only'})
        self.write('intervention_resume/analysis_plan.json',{'exclude_unavailable_pairs':True})
        self.write('intervention_resume/process.json',dict(checked_at_utc='2026-01-01T02:00:00+00:00',owned_workers=0,collector_session_available=False))
        self.write('intervention_resume/inventory.json',dict(protocol='23-scale-v5',count=1240,requests=self.inventory))
        missing=[]
        for index in range(116,120):
            key=self.plan[index]['request_key']; req=self.requests[key]; p=self.plan[index]
            missing.append(dict(request_key=key,cache_sha256=self.inventory[key],case_id=p['case_id'],content_hash=p['source_hash'],
                request_input_hash=resume.sir_hash(req['case_inputs']),feedback_hash=resume.sir_hash(req['feedback']),arm=p['arm'],stage=p['stage'],sample=p['sample'],profile=self.profile))
        self.amendment=dict(protocol='23-scale-v5',amendment_version=resume.SCALE_INTERVENTION_RESUME_VERSION,
            declared_at_utc='2026-01-01T03:00:00+00:00',loss_observed_at_utc='2026-01-01T02:00:00+00:00',
            protected_files=[self.binding(p) for p in ['source_freeze.json','intervention_start_declaration.json','infrastructure_resume/amendment_001.json','main/dispatch.json']],
            implementation=self.binding('intervention_resume/implementation.py'),analysis_plan=self.binding('intervention_resume/analysis_plan.json'),
            process_proof=self.binding('intervention_resume/process.json'),cache_inventory=self.binding('intervention_resume/inventory.json'),
            request_plans=[self.binding('main/request_plans/arms.json')],unavailable_requests=missing)
        self.amendment_path=self.data/'intervention_resume/amendment_002.json'; self.refresh_amendment()
        self.ns={'scale_request_key':resume.sir_hash,'scale_call_model':self.call,'scale_dispatch_waves':lambda *a,**k:('delegated',[]),
            'scale_run_interventions':lambda **kw:kw,'scale_write_json':lambda p,v:self.write_bytes(Path(p).relative_to(self.data),json.dumps(v).encode()),
            'SCALE_InfrastructureStop':RuntimeError}
        self.ns['SCALE_RUNTIME_SOURCE_HASHES']={}
        self.ns['SCALE_RESUME_INSTALLED']={'approved':{},'version':'23-scale-capacity-continuation-v1','root':self.root,
            'amendment_sha256':resume.sir_sha(self.data/'infrastructure_resume/amendment_001.json')}

    def request(self,cid,stage,sample):
        return dict(model='gpt-6.1-sol',reasoning_effort='high',protocol='23-scale-v5',stage=stage,sample=sample,
            expected_case_ids=[cid],case_inputs=[{'case_id':cid,'document':'visible source only','task_instructions':'extract seven fields'}],
            feedback=None if stage=='generate' else {cid:{'original_output':{'quantity_units':123},'validator_feedback':{'wrong_fields':['quantity_units']}}},runner_limits={'timeout_s':900})
    def record(self,req,pending=False):
        key=resume.sir_hash(req); self.requests[key]=req
        attempt=dict(pending=pending,started_at='2026-01-01T00:00:00+00:00',timeout_s=900)
        if not pending:attempt['finished_at']='2026-01-01T01:00:00+00:00'
        raw=gzip.compress(json.dumps(dict(key=key,request=req,attempts=[attempt])).encode(),mtime=0)
        (self.cache/(key+'.json.gz')).write_bytes(raw); self.inventory[key]=resume.sir_sha(self.cache/(key+'.json.gz'))
    def write_bytes(self,name,raw):
        p=self.data/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    def write(self,name,value):self.write_bytes(name,json.dumps(value).encode())
    def binding(self,name):return dict(path=name,sha256=resume.sir_sha(self.data/name))
    def refresh_amendment(self):self.write_bytes('intervention_resume/amendment_002.json',json.dumps(self.amendment).encode())
    def install(self):return resume.scale_intervention_resume_install(self.root,self.amendment_path,self.ns)
    def call(self,request,cache_dir,live=False,timeout_s=900,_runner=None):
        key=resume.sir_hash(request);p=Path(cache_dir)/(key+'.json.gz')
        if p.exists():
            if resume.sir_read(p)['attempts'][0]['pending']:raise AssertionError('pending must never reach frozen call')
            return dict(request_key=key,cached=True,error=None)
        if not live:raise FileNotFoundError(key)
        self.new_calls.append(key);self.record(request);return dict(request_key=key,cached=False,error=None)
    def invoke(self,job):
        key=job['request_key']; req=self.requests[key]; response=self.ns['scale_call_model'](req,self.cache,live=True)
        plan=next(x for x in self.plan if x['request_key']==key)
        row=dict(request_key=key,case_id=plan['case_id'],arm=plan['arm'],stage=plan['stage'],sample=plan['sample'],split='collection',
            content_hash=plan['source_hash'],request_input_hash=resume.sir_hash(req['case_inputs']),feedback_hash=resume.sir_hash(req['feedback']),
            response=None,transport_error=response.get('error'))
        return row,dict(request_key=key,cached_this_run=response['cached'],transport_error=response.get('error'),
            finished_at=response.get('finished_at'),subprocess_elapsed_s=response.get('elapsed_s'),return_code=response.get('return_code'))

    def test_verification_and_exact_two_pairs(self):
        s=resume.scale_intervention_resume_verify(self.root,self.amendment_path)
        self.assertEqual(len(s['approved']),4);self.assertEqual(len({x['case_id'] for x in s['approved'].values()}),2)
    def test_pending_projection_no_requery_no_fake_telemetry(self):
        s=self.install(); before={k:(self.cache/(k+'.json.gz')).read_bytes() for k in s['approved']}
        for key in s['approved']:
            r=self.ns['scale_call_model'](self.requests[key],self.cache,live=True)
            self.assertTrue(r['cached']);self.assertTrue(r['outcome_unavailable']);self.assertIsNone(r['parsed'])
            self.assertEqual(r['started_at'],resume.sir_read(self.cache/(key+'.json.gz'))['attempts'][0]['started_at'])
            for name in ['finished_at','elapsed_s','return_code','events','usage','final_assistant_response']:self.assertNotIn(name,r)
        self.assertEqual(self.new_calls,[])
        self.assertEqual(before,{k:(self.cache/(k+'.json.gz')).read_bytes() for k in s['approved']})
    def test_all_four_projected_rows_same_wave(self):
        self.install(); rows,ledger=self.ns['scale_dispatch_waves'](self.jobs[116:124],self.invoke,self.main,4,self.progress.append)
        self.assertEqual(len(rows),8);self.assertEqual(sum(r.get('outcome_unavailable',False) for r in rows),4)
        self.assertEqual(len(self.new_calls),4);self.assertFalse(any(x['transport_failure'] for x in self.progress))
        self.assertTrue(all(x['finished_at'] is None and x['return_code'] is None for x in ledger[:4]))
    def test_delete_any_prior_cache_blocks(self):
        key=next(iter(self.inventory));(self.cache/(key+'.json.gz')).unlink()
        with self.assertRaises(FileNotFoundError):self.install()
    def test_changed_any_prior_cache_blocks(self):
        key=next(iter(self.inventory));(self.cache/(key+'.json.gz')).write_bytes(b'changed')
        with self.assertRaises(ValueError):self.install()
    def test_post_install_delete_never_resubmits(self):
        self.install();key=self.plan[0]['request_key'];(self.cache/(key+'.json.gz')).unlink()
        with self.assertRaises(FileNotFoundError):self.ns['scale_call_model'](self.requests[key],self.cache,live=True)
        self.assertEqual(self.new_calls,[])
    def test_only_exact_pending_identity(self):
        self.amendment['unavailable_requests'][0]['request_input_hash']='0'*64;self.refresh_amendment()
        with self.assertRaises(ValueError):self.install()
    def test_unbalanced_pair_rejected(self):
        self.amendment['unavailable_requests'][0]['arm']='feedback_repair';self.refresh_amendment()
        with self.assertRaises(ValueError):self.install()
    def test_proof_and_timing_required(self):
        self.amendment['declared_at_utc']=self.amendment['loss_observed_at_utc'];self.refresh_amendment()
        with self.assertRaises(ValueError):self.install()
    def test_new_error_drains_wave_stops_and_preserves_stops(self):
        self.install();old=self.main/'infrastructure_stop.json';old.write_bytes(b'original stop')
        visited=[]
        def invoke(job):
            visited.append(job['request_key']);row,entry=self.invoke(job)
            row['transport_error']='new provider error';entry['transport_error']='new provider error'
            return row,entry
        for _ in range(2):
            with self.assertRaises(RuntimeError):self.ns['scale_dispatch_waves'](self.jobs[120:128],invoke,self.main,4)
        self.assertEqual(len(visited),8);self.assertEqual(old.read_bytes(),b'original stop')
        self.assertEqual(len(list(self.main.glob('infrastructure_stop_intervention_resume_*.json'))),2)
    def test_four_worker_and_pilot_scope(self):
        self.install()
        with self.assertRaises(ValueError):self.ns['scale_dispatch_waves']([],self.invoke,self.main,2)
        self.assertEqual(self.ns['scale_dispatch_waves']([],self.invoke,self.data/'pilot',4),('delegated',[]))
    def test_full_cached_replay_all_original_and_arm_keys(self):
        self.install()
        for job in self.jobs[120:]:self.record(self.requests[job['request_key']])
        for key in list(self.inventory):self.ns['scale_call_model'](self.requests[key],self.cache,live=False)
        self.assertEqual(self.new_calls,[])
        with self.assertRaises(ValueError):self.ns['scale_run_interventions'](root=self.root,live=True)
    def test_request_and_feedback_bytes_unchanged_no_gold(self):
        self.install();key=self.plan[116]['request_key'];before=copy.deepcopy(self.requests[key])
        self.ns['scale_call_model'](self.requests[key],self.cache,live=True)
        self.assertEqual(before,self.requests[key]);self.assertEqual(resume.sir_hash(before),key)
        self.assertNotIn('gold',json.dumps(before));self.assertNotIn('expectedvalues',json.dumps(before))
    def test_notebook_namespace_reuses_embedded_companion_without_exec(self):
        isolated={'__name__':'notebook_embedded_extension'}
        exec(compile(Path(resume.__file__).read_bytes(),'embedded_extension','exec'),isolated)
        with patch('builtins.exec',side_effect=AssertionError('no external helper execution')):
            state=isolated['scale_intervention_resume_install'](self.root,self.amendment_path,self.ns)
        self.assertIs(state['namespace'],self.ns)
    def test_original_capacity_replay_is_still_allowed(self):
        self.install();key=next(k for k in self.inventory if k not in self.requests or k not in {p['request_key'] for p in self.plan})
        cid=self.requests[key]['expected_case_ids'][0]
        known=dict(case_id=cid,content_hash='oldsource',request_input_hash='oldinput',transport_error='reviewed capacity')
        self.ns['SCALE_RESUME_INSTALLED']['approved'][key]=known
        job=dict(request_key=key,case={'case_id':cid},arm='original')
        def invoke(_):
            return dict(request_key=key,**known,arm='original',stage='generate',sample=0,split='collection',response=None),dict(request_key=key,cached_this_run=True)
        rows,_=self.ns['scale_dispatch_waves']([job],invoke,self.main,4)
        self.assertEqual(rows[0]['transport_error'],'reviewed capacity');self.assertEqual(self.new_calls,[])


if __name__=='__main__':unittest.main()
