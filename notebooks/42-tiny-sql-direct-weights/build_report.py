"""Build this experiments README and self-contained cache-only notebook."""
from pathlib import Path
import importlib.util
import json,re,sys
import numpy as np
import nbformat as nbf
REPO=Path(__file__).resolve().parents[2]
SQL=Path(__file__).resolve().parent
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def read(p):return json.loads(p.read_text(encoding='utf-8'))

def code(p):return p.read_text(encoding='utf-8').split("if __name__",1)[0].rstrip()

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+
                     ['| '+' | '.join(str(x).replace('|','\\|').replace('\n',' ') for x in row)+' |' for row in rows])

def excerpt(s,n=125):return s if len(s)<=n else s[:n]+'… [excerpt]'

def notebook(root,name,markdown,setup,extra=None):
    # Narrative remains independently readable when every code cell is hidden.
    parts=re.split(r'(?m)(?=^## (?:Contents|[0-9]+\.))',markdown)
    cells=[]
    for part in parts:
        if not part.strip():continue
        cells.append(nbf.v4.new_markdown_cell(part.rstrip()))
        if part.startswith('## Contents'):
            cells.append(nbf.v4.new_markdown_cell('### Replay setup\n\nThe next cell defines this notebook\'s helpers in place. It does not import experiment code from another folder and does not invoke a teacher. Ordinary execution uses only committed data.'))
            cells.append(nbf.v4.new_code_cell(setup))
            if extra:cells.extend(extra)
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
        'language_info':{'name':'python','version':sys.version.split()[0]}})
    nbf.write(nb,root/name)
    (root/'README.md').write_text(markdown,encoding='utf-8')

def build_sql():
    replay=module(SQL/'replay.py','weight_replay42');summary=replay.analyse()
    submission=table(['Submission','Cases','Schema matches','Readable but wrong','Unreadable/non-SELECT','EOS'],[
        [r['name'],r['n_cases'],r['correct'],r['wrong_readable'],r['unreadable_or_nonselect'],r['eos']] for r in summary['submissions']])
    dec=table(['Condition','Outputs','Readable SELECT','Unreadable/non-SELECT','Schema matches','EOS'],[
        [r['condition'],r['n_outputs'],r['parseable_select'],r['unreadable_sql'],r['schema_match'],r['eos']] for r in summary['decoding']])
    models=table(['Teacher','Pinned version or requested ID','Provider and call','Published size/precision','Settings','Why included'],[
        ['GPT-6.1 Sol','gpt-6.1-sol; dated revision not exposed','OpenAI, codex exec','Not disclosed','xhigh; tool-free; initial and verbal-feedback revision','Initial numerical editor and feedback attempt'],
        ['GPT-6 Astra','gpt-6-astra; dated revision not exposed','OpenAI, codex exec','Not disclosed','xhigh completed runs; max interrupted run retained','Requested replacement editor and bounded-prior comparison'],
        ['Nemotron 3 Ultra free','nvidia/nemotron-3-ultra-550b-a55b:free; see archived request metadata','NVIDIA, OpenRouter free','Snapshot size/precision not separately attested','Reasoning enabled; zero-price route','Free alternative; overlong incomplete submission retained'],
        ['Nemotron 3.5 Super VL free','nvidia/nemotron-3.5-super-vl-20261015','NVIDIA, OpenRouter free','120B total, 12B active; serving precision unknown','Reasoning enabled; zero-price route','Free alternative; valid but degenerate submitted network'],
        ['Pythia-14m reference','EleutherAI/pythia-14m @ cf967c0a9a04383db6f7b1108d86b2962634b4ac','Local checkpoint inspection only','14,067,712 parameters; FP16 stored weights','No generation or training','Descriptive trained-weight reference, not a competing SQL teacher']])
    examples=[]
    chosen=[summary['worked_examples'][0],summary['worked_examples'][1],summary['worked_examples'][3],summary['worked_examples'][7],summary['worked_examples'][10],summary['worked_examples'][12]]
    for i,c in enumerate(chosen,1):
        expected='select '+','.join('"'+x+'"' for x in c['case']['columns'])+' from "'+c['case']['table']+'";'
        outcome='Readable SELECT with incorrect schema.' if c['parseable_select'] and not c['schema_match'] else ('Matches this exposed schema.' if c['schema_match'] else 'Unreadable or not a SELECT statement.')
        examples.append(f"### Measured case {i}: {c['submission']}, `{c['case']['id']}`\n\nInput: `{c['prompt']}`\n\nExpected query:\n\n```sql\n{expected}\n```\n\nObserved raw output (long strings explicitly excerpted):\n\n```text\n{excerpt(c['raw_output'],180)}\n```\n\n{outcome} The scorer compares the parsed table and ordered columns; it does not substitute the expected names. This same case ID is retained in that submission's `raw_outputs.json`.")
    allgen=read(SQL/'data/diagnostics/all_generations.json')
    # Save an auditable postprocessing example directly from the cached sweep.
    if isinstance(allgen,list):
        selected=[];seen=set()
        for c in allgen:
            if c.get('case',{}).get('id')=='example-2':
                condition=c['request']['decoding']['name']
                if condition not in seen:
                    selected.append({'condition':condition,'output':c.get('scored_output',c.get('raw_output'))});seen.add(condition)
        if selected:examples.append('### Same request under decoder changes\n\nThese are saved outputs for `example-2`, not repaired SQL.\n\n'+table(['Condition','Cached output excerpt'],[[r['condition'],'`'+excerpt(str(r['output']),95)+'`'] for r in selected[:6]]))
    spend=[]
    for label,folder in [('Sol initial',SQL/'data/history'),('Sol revised',SQL/'data/history/round-02/attempt-02'),
                         ('Astra unbounded',SQL/'data/history/round-03-astra/attempt-02'),('Astra bounded',SQL/'data/history/round-04-astra-bounded'),
                         ('Nemotron Super free',SQL/'data/history/round-05-nemotron-super-free')]:
        audit=read(folder/'generator_audit.json');u=audit.get('usage',{}) or {}
        spend.append([label,u.get('input_tokens',u.get('prompt_tokens','Not reported')),u.get('output_tokens',u.get('completion_tokens','Not reported')),u.get('reasoning_output_tokens',(u.get('completion_tokens_details') or {}).get('reasoning_tokens','Not reported')),f"{audit['wall_seconds']:.1f} s" if audit.get('wall_seconds') is not None else 'Not reported','$0 free API' if label=='Nemotron Super free' else 'Unknown CLI charge'])
    text=(SQL/'data/report_template.md').read_text(encoding='utf-8')
    for k,v in {'MODEL_TABLE':models,'SUBMISSION_TABLE':submission,'DECODER_TABLE':dec,'WORKED_EXAMPLES':'\n\n'.join(examples),
                'SPEND':table(['Submission','Input tokens','Output tokens','Reasoning tokens','Wall time','Dollar spend'],spend)}.items():text=text.replace('{{'+k+'}}',v)
    cells=[nbf.v4.new_code_cell("report = analyse()\nprint(json.dumps({'submissions':report['submissions'], 'exact_numpy_replays':report['numpy_exact_matches'], 'decoder_outputs':report['all_decoding_outputs']}, indent=2))\nprint('Fresh teacher calls: 0; SQL executions: 0')")]
    notebook(SQL,'42_tiny_sql_direct_weights.ipynb',text,code(SQL/'replay.py'),cells)

if __name__ == '__main__':
    build_sql()
    print((SQL/'README.md').stat().st_size)
