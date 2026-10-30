"""Posthoc replay-guard tests use only synthetic temporary metadata files."""
import gzip
import json
from pathlib import Path
import tempfile
import unittest

import replay_scale_notebook as qa


class DiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'notebooks/23-synthetic-data-curation';self.data=self.root/'data/scale_v5'
        self.write('source_freeze.json',{'protocol':'23-scale-v5'})
        self.write('infrastructure_resume/amendment_001.json',{'protocol':'23-scale-v5','amendment_version':'23-scale-capacity-continuation-v1',
            'source_freeze_sha256':qa.scale_qa_sha(self.data/'source_freeze.json')})
        self.write('main/dispatch.json',{'jobs':'frozen input metadata'})
        self.write('main/manifest.json',{'phase':'interventions_complete'})
        gate={'protocol':'23-scale-v5','phase':'interventions_authorized_after_independent_audit','sha256':{}}
        for i in range(36):
            name='prearm/input_'+str(i)+'.json';self.write(name,{'input':i});gate['sha256'][name]=qa.scale_qa_sha(self.data/name)
        for name in ['source_freeze.json','infrastructure_resume/amendment_001.json']:
            gate['sha256'][name]=qa.scale_qa_sha(self.data/name)
        self.write('intervention_start_declaration.json',gate)
        self.write('intervention_resume/source_snapshot/scale_intervention_resume.py',{'frozen implementation':'metadata only'})
        self.write('intervention_resume/analysis_plan.json',{'exclude_only_known_missing_pairs':True})
        self.amendment={'protocol':'23-scale-v5','amendment_version':'23-scale-intervention-interruption-v1',
            'protected_files':[self.binding(p) for p in ['source_freeze.json','intervention_start_declaration.json','infrastructure_resume/amendment_001.json','main/dispatch.json']],
            'implementation':self.binding('intervention_resume/source_snapshot/scale_intervention_resume.py'),
            'analysis_plan':self.binding('intervention_resume/analysis_plan.json')}
        self.write('intervention_resume/amendment_002.json',self.amendment)
        self.value={'new_cli_subprocesses_this_run':0,'replayed_requests_this_run':1200,'offline':True}
        self.receipt=self.add_receipt(self.value)

    def write(self,name,value):
        p=self.data/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value),encoding='utf-8',newline='\n')
    def binding(self,name):return {'path':name,'sha256':qa.scale_qa_sha(self.data/name)}
    def add_receipt(self,value,relative=None):
        if relative is None:
            ah=qa.scale_qa_sha(self.data/'intervention_resume/amendment_002.json')[:12]
            relative='main/intervention_continuation_diagnostics/'+ah+'/validation_'+qa.scale_qa_hash(value)[:12]+'.json'
        self.write(relative,value);return self.data/relative
    def read(self):return qa.scale_qa_continuation_diagnostics(self.root)

    def test_only_valid_operational_receipt_is_excluded(self):
        result=self.read();self.assertEqual(len(result),1)
        self.assertNotIn(self.receipt.relative_to(self.root).as_posix(),qa.scale_qa_v5_outputs(self.root))
        self.assertTrue(qa.scale_qa_continuation_changes({},result))
    def test_unknown_payload_field_rejected(self):
        self.receipt.unlink();self.add_receipt({**self.value,'model_response':'forbidden'})
        with self.assertRaises(RuntimeError):self.read()
    def test_boolean_counter_rejected(self):
        self.receipt.unlink();self.add_receipt({**self.value,'replayed_requests_this_run':True})
        with self.assertRaises(RuntimeError):self.read()
    def test_new_live_receipt_rejected_by_change_guard(self):
        self.receipt.unlink();self.add_receipt({**self.value,'offline':False,'new_cli_subprocesses_this_run':1080})
        with self.assertRaises(RuntimeError):qa.scale_qa_continuation_changes({},self.read())
    def test_deleted_receipt_rejected(self):
        before=self.read();self.receipt.unlink()
        with self.assertRaises(RuntimeError):qa.scale_qa_continuation_changes(before,self.read())
    def test_wrong_payload_hash_rejected(self):
        bad=self.receipt.with_name('validation_'+'0'*12+'.json');self.receipt.rename(bad)
        with self.assertRaises(RuntimeError):self.read()
    def test_unbound_directory_or_nested_path_rejected(self):
        for relative in ['main/intervention_continuation_diagnostics/'+'0'*12+'/validation_'+qa.scale_qa_hash(self.value)[:12]+'.json',
                'main/intervention_continuation_diagnostics/extra/nested/value.json']:
            p=self.add_receipt(self.value,relative)
            with self.assertRaises(RuntimeError):self.read()
            p.unlink()
    def test_protected_protocol_change_rejected(self):
        self.write('main/dispatch.json',{'jobs':'changed'})
        with self.assertRaises(RuntimeError):self.read()
    def test_prearm_gate_binding_change_rejected(self):
        self.write('prearm/input_0.json',{'input':'changed'})
        with self.assertRaises(RuntimeError):self.read()
    def test_implementation_and_analysis_hashes_required(self):
        for name in ['intervention_resume/source_snapshot/scale_intervention_resume.py','intervention_resume/analysis_plan.json']:
            p=self.data/name;old=p.read_bytes();p.write_bytes(b'changed')
            with self.assertRaises(RuntimeError):self.read()
            p.write_bytes(old)
    def test_raw_four_pending_cache_hashes_have_no_exception(self):
        for i in range(4):
            p=self.data/'main/cache'/('a'+str(i)+'.json.gz');p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(gzip.compress(json.dumps({'attempts':[{'pending':True}]}).encode(),mtime=0))
        before=qa.scale_qa_cache_hashes(self.root)
        self.assertEqual(len(before),4)
        target=next((self.data/'main/cache').glob('*'));target.write_bytes(target.read_bytes()+b'changed')
        self.assertNotEqual(before,qa.scale_qa_cache_hashes(self.root))
    def test_incomplete_run_cannot_inspect_cache_inventory(self):
        (self.data/'main/manifest.json').unlink()
        with self.assertRaises(RuntimeError):qa.scale_qa_cache_hashes(self.root)

    def third(self):
        self.write('main/selection.json',{'selected':'frozen'})
        for name in ['implementation.py','analysis.json','process.json','inventory.json']:
            self.write('intervention_resume_003/'+name,{'metadata':name})
        third={'protocol':'23-scale-v5','amendment_version':'23-scale-intervention-interruption-v2',
            'predecessor':self.binding('intervention_resume/amendment_002.json'),
            'protected_files':[self.binding(p) for p in ['source_freeze.json','intervention_start_declaration.json','main/dispatch.json','main/selection.json']],
            **{k:self.binding('intervention_resume_003/'+v) for k,v in [('implementation','implementation.py'),('analysis_plan','analysis.json'),('process_proof','process.json'),('cache_inventory','inventory.json')]}}
        self.write('intervention_resume_003/amendment_003.json',third)
        digest=qa.scale_qa_sha(self.data/'intervention_resume_003/amendment_003.json')
        self.add_receipt(self.value,'main/intervention_continuation_diagnostics/'+digest[:12]+'/validation_'+qa.scale_qa_hash(self.value)[:12]+'.json')
        return third

    def test_third_and_predecessor_receipts_both_bound(self):
        self.third();self.assertEqual(len(self.read()),2)

    def test_third_selection_change_rejected(self):
        self.third();self.write('main/selection.json',{'selected':'changed'})
        with self.assertRaises(RuntimeError):self.read()

    def test_third_predecessor_change_rejected(self):
        third=self.third();third['predecessor']['sha256']='0'*64
        self.write('intervention_resume_003/amendment_003.json',third)
        with self.assertRaises(RuntimeError):self.read()

    def fourth(self):
        third=self.third()
        self.write('intervention_resume_003/continuation_start_003.json',{'gate':'frozen'})
        for name in ['source.py','process.json','inventory.json','stop.json','sleep.json','error.json','handling.json']:
            self.write('intervention_resume_004/'+name,{'metadata':name})
        fourth={'protocol':'23-scale-v5','amendment_version':'23-scale-intervention-timeout-continuation-v1',
            'predecessor':self.binding('intervention_resume_003/amendment_003.json'),
            'protected_files':[self.binding(p) for p in ['source_freeze.json','intervention_start_declaration.json','main/dispatch.json','main/selection.json','intervention_resume_003/continuation_start_003.json']],
            'analysis_plan':third['analysis_plan'],
            **{k:self.binding('intervention_resume_004/'+v) for k,v in [('implementation','source.py'),('process_proof','process.json'),('cache_inventory','inventory.json'),('stop_record','stop.json'),('sleep_event','sleep.json'),('error_metadata','error.json'),('handling_plan','handling.json')]}}
        fourth['provenance_sha256']={'intervention_resume_004/handling.json':fourth['handling_plan']['sha256']}
        self.write('intervention_resume_004/amendment_004.json',fourth)
        digest=qa.scale_qa_sha(self.data/'intervention_resume_004/amendment_004.json')
        self.add_receipt(self.value,'main/intervention_continuation_diagnostics/'+digest[:12]+'/validation_'+qa.scale_qa_hash(self.value)[:12]+'.json')
        return fourth

    def test_fourth_receipts_and_prior_receipts_bound(self):
        self.fourth();self.assertEqual(len(self.read()),3)

    def test_fourth_error_proof_byte_change_rejected(self):
        self.fourth();self.write('intervention_resume_004/error.json',{'changed':True})
        with self.assertRaises(RuntimeError):self.read()

    def test_fourth_analysis_plan_cannot_change(self):
        fourth=self.fourth();fourth['analysis_plan']=fourth['error_metadata']
        self.write('intervention_resume_004/amendment_004.json',fourth)
        with self.assertRaises(RuntimeError):self.read()


if __name__=='__main__':unittest.main()
