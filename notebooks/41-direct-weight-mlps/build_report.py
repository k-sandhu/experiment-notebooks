"""Build this experiments README and self-contained cache-only notebook."""
from pathlib import Path
import importlib.util
import json,re,sys
import numpy as np
import nbformat as nbf
REPO=Path(__file__).resolve().parents[2]
MLP=Path(__file__).resolve().parent
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

def build_mlp():
    a=module(MLP/'analysis.py','weight_analysis41');summary=a.make_figures();rows=summary['results']
    valid=[r for r in rows if not r.get('pending') and r.get('format_failure') is None]
    first=[r for r in rows if not r.get('recovery') and not r.get('indexed')];readable=[r for r in first if r in valid]
    headline=f"{len(readable)} of six first submissions produced scored networks; {sum(not r.get('pending') and r.get('format_failure') is not None for r in first)} ended without a usable network. "
    headline+=' '.join(f"{r['label']} classified {r['test']['correct']}/1,797 test images correctly ({100*r['test']['accuracy']:.2f}%)." for r in readable)
    headline+=' Transport recoveries are reported separately below and never replace the first-attempt failure counts.'
    resultrows=[]
    for r in rows:
        if r in valid:
            lo,hi=np.array(r['test']['wilson_95'])*100
            workflow=f"Indexed, {r['outer_requests']} calls" if r.get('indexed') else ('Recovery' if r.get('recovery') else 'First submission')
            resultrows.append([r['label'],workflow,f"{r['test']['correct']}/1797 ({100*r['test']['accuracy']:.2f}%), {1797-r['test']['correct']} wrong",f'{lo:.2f}–{hi:.2f}%',
                               f"{100*r['visible']['accuracy']:.2f}%",f"{100*r['hidden_train']['accuracy']:.2f}%",'0'])
        else:
            reason='Pending' if r.get('pending') else r['format_failure']
            if r['model_key']=='gemini' and not r.get('recovery') and not r.get('pending'):reason='Provider rejected schema before decoding'
            if r['model_key']=='opus' and not r.get('recovery') and not r.get('pending'):reason='Thinking/output limit, then budget exhaustion'
            if r['model_key']=='opus' and r.get('recovery') and not r.get('pending'):reason='Refusal citing provider safety classifier; no weights'
            if r['model_key']=='nemotron' and not r.get('indexed'):reason='Output limit; reasoning only; no weights'
            workflow=f"Indexed, {r['outer_requests']} calls" if r.get('indexed') else ('Recovery' if r.get('recovery') else 'First submission')
            failures=f"{r['outer_requests']} provider errors" if r.get('indexed') else '1 unusable response'
            resultrows.append([r['label'],workflow,reason,'N/A','N/A','N/A','Pending' if r.get('pending') else failures])
    models=table(['Teacher','Pinned version or runtime ID','Provider and call','Published size/precision','Output settings','Why included'],[
        ['GPT-6 Astra','gpt-6-astra; revision not exposed','OpenAI, codex exec','Not disclosed','xhigh; legacy 17-value medium; no tools','Requested author; known-rule successes'],
        ['GPT-6.1 Sol','gpt-6.1-sol; immutable revision not exposed','OpenAI, codex exec','Not disclosed','xhigh; tools disabled','Requested second OpenAI numerical author'],
        ['Claude Opus 5.5','claude-opus-5-5; immutable revision not exposed','Anthropic, claude -p','Not disclosed','xhigh first; high continuation; tools disabled','Requested independent vendor; recovery kept separate'],
        ['Muse Wonder Full','muse-wonder-full-1.0; immutable revision not exposed','Meta, muse exec','Not disclosed','xhigh; empty preset; tools disabled','Requested independent vendor'],
        ['Nemotron 3.5 Super VL','nvidia/nemotron-3.5-super-vl-20261015','NVIDIA, OpenRouter free','120B total, 12B active; precision not attested','Reasoning first; off indexed; 131,072 cap; free only','Requested open-weight author; 388-value comparison'],
        ['Gemini 4 Argon batch','google/gemini-4-argon-20261013','Google Vertex, OpenRouter Batch API','Not disclosed','high original and schema retry; low final variant; 131,072 requested output cap','Requested Google comparison; asynchronous batch route']])
    interpretation=''
    if readable:
        ordered=sorted(readable,key=lambda r:-r['test']['accuracy']);best=ordered[0]
        interpretation=f"The highest first-attempt score observed is {best['label']} at {best['test']['correct']}/1,797 ({100*best['test']['accuracy']:.2f}%). The nearest-neighbour reference correctly labels {1750-best['test']['correct']} more images. "
        if len(ordered)>1:interpretation+=f"{ordered[0]['label']} and {ordered[1]['label']} differ by {ordered[0]['test']['correct']-ordered[1]['test']['correct']} correctly labelled images on this fixed test set. "
        interpretation+='These are differences between single submitted networks. They do not establish a stable ranking across repeated requests or new datasets.'
    recoveries=[r for r in valid if r.get('recovery') or r.get('indexed')]
    if recoveries:interpretation+=' '+' '.join(f"The separately labelled {r['label']} scored {r['test']['correct']}/1,797 ({100*r['test']['accuracy']:.2f}%) after its documented transport recovery." for r in recoveries)
    examples=read(MLP/'data/worked_examples.json');exampleparts=[]
    for i,c in enumerate(examples,1):
        preds=', '.join(f'{name} → {value}' for name,value in c['predictions'].items()) or 'No complete prediction available yet.'
        why='The shown predictions disagree with the gold label for at least one network.' if any(v!=c['gold'] for v in c['predictions'].values()) else 'Every available prediction shown matches the gold label.'
        exampleparts.append(f"### Case {i}: `{c['id']}`, gold digit {c['gold']}\n\nSelection: {c['selection']}. Observed outputs: {preds}. {why} This item contributes one count per scored network; the panel above shows its actual pixel grid. The stable row index connects it to `data/source/optdigits.tes` and the saved prediction arrays.")
    if valid:
        lead=sorted(valid,key=lambda r:-r['test']['accuracy'])[0];c=examples[0]
        with np.load(MLP/'data/dataset.npz') as d:raw=d['test'][c['index'],:64]
        with np.load(MLP/'data'/lead['candidate_folder']/'predictions.npz') as d:scores=d['test_scores'][c['index']]
        exampleparts.append(f"### End-to-end calculation for `{c['id']}`\n\nThe first eight raw ink counts are `{raw[:8].tolist()}`. Dividing by sixteen gives `{(raw[:8]/16).tolist()}` for the first input row. The complete input remains sixty-four numbers. {lead['label']}'s unchanged matrices yield the following ten output scores.\n\n"+table(['Digit','Observed score'],[[j,f'{v:.8g}'] for j,v in enumerate(scores)])+
            f"\n\nThe largest score has digit {int(scores.argmax())}; the hidden label is {c['gold']}. This contributes {int(scores.argmax()==c['gold'])} to that network's correct count. No score or label is fed back into its parameters.")
    reasoning=[];spend=[]
    for r in rows:
        folder=MLP/'data'/r['candidate_folder'];p=folder/'response.json'
        if r.get('indexed'):p=folder/('assembled_response.json' if (folder/'assembled_response.json').exists() else 'workflow_summary.json')
        native=read(p) if p.exists() else {};usage=native.get('usage') or {};input_tokens=usage.get('input_tokens',usage.get('prompt_tokens'));output_tokens=usage.get('output_tokens',usage.get('completion_tokens'));rt=usage.get('reasoning_output_tokens',(usage.get('completion_tokens_details') or {}).get('reasoning_tokens'))
        if usage.get('per_turn'):
            reported=[u for u in usage['per_turn'] if u and u.get('prompt_tokens') is not None]
            input_tokens=sum(u['prompt_tokens'] for u in reported) if reported else None
            output_tokens=sum(u.get('completion_tokens',0) for u in reported) if reported else None
            rt=sum((u.get('completion_tokens_details') or {}).get('reasoning_tokens',0) for u in reported) if reported else None
        if r['model_key']=='muse' and usage.get('models'):
            u=usage['models'][0];input_tokens=u.get('input_tokens');output_tokens=u.get('output_tokens');rt=u.get('reasoning_tokens')
        if r['model_key']=='opus':rt=(usage.get('output_tokens_details') or {}).get('thinking_tokens')
        chars=r.get('reasoning_characters',0);link=(folder/'reasoning.txt').relative_to(MLP).as_posix()
        evidence=p if p.exists() else (folder if r.get('indexed') else folder/'events.jsonl')
        reasoning.append([r['label'],f'[{chars:,} characters]({link})' if chars else 'No readable reasoning text emitted',rt if rt is not None else 'Not reported',f'[Raw evidence]({evidence.relative_to(MLP).as_posix()})'])
        cost_value=r.get('cost_usd') if r.get('cost_usd') is not None else native.get('cost_usd')
        cost=f"${cost_value:.6f}" if cost_value is not None else 'Not reported'
        if r['model_key']=='opus' and cost_value is not None:cost+=' (cumulative session list-price equivalent)'
        spend.append([r['label'],input_tokens if input_tokens is not None else 'Not reported',output_tokens if output_tokens is not None else 'Not reported',f"{native.get('wall_seconds',0):.1f} s" if p.exists() else 'Pending',cost])
    confusion_text='No scored network is available for a confusion matrix yet.'
    if valid:
        lead=sorted(valid,key=lambda r:-r['test']['accuracy'])[0];cm=np.array(lead['test']['confusion']);off=cm.copy();np.fill_diagonal(off,0)
        positions=np.argsort(off.ravel())[::-1][:2];details=[]
        for position in positions:
            gold,pred=np.unravel_index(position,off.shape)
            details.append(f"{off[gold,pred]} of {cm[gold].sum()} true digit-{gold} images were labelled {pred}")
        confusion_text=f"![Confusion matrix for highest observed score](figures/confusion.png)\n\nRows are gold digits and columns are predictions. Each cell counts official test images, and the diagonal counts correct answers. For {lead['label']}, "+'; '.join(details)+'. These are the two largest off-diagonal counts in this submitted network. The figure is selected descriptively by the highest observed score, not as an independently validated winner. Counts identify recurring class confusions; they do not establish why the errors occur.'
    ledger=read(MLP/'data/replication_ledger.json')
    brief={
      'pretrained-reference':('Pretrained reference','MacroStories inspected; no preserved scored generation'),
      'random-language-control':('Random language control','Ten untrained tokens; near-uniform scores'),
      'sql-sol':('Sol SQL writing and revision','Constant query: 1/8 exposed match; revision 0/12'),
      'sql-astra':('Astra SQL writing','Completed run 0/16; earlier cancellation unscored'),
      'sql-free':('Free-model SQL writing','Ultra malformed; Super 6 nonzeros, 0/16'),
      'sql-decoders':('SQL decoding controls','Zero schema matches in 1,845 outputs, 11 conditions'),
      'sql-priors':('Bounded SQL weights','All numerical checks pass; 0/16 SQL matches'),
      'weight-diagnostics':('Weight inspection','SQL score collapse; interpretable ring-network structure'),
      'mlp17':('Known-rule tiny MLPs','Astra 50,000/50,000 classification; regression error zero'),
      'mlp388':('Four-ring MLP','Astra 20,000/20,000; Nemotron 96.43%; boundary errors remain'),
      'mlp6570':('Sample-based digit MLP','Astra 91.54%, Sol 79.13%, Muse 33.72%; other first replies unusable'),
      'indexed-output':('Indexed output and continuation',ledger[-1]['outcome'])}
    replacements={'HEADLINE':headline,'MODEL_TABLE':models,'PREPOST':'```python\n'+(MLP/'data/pre_post_processing.py.txt').read_text()+'```',
        'REPLICATION_LEDGER':table(['Experiment','Network size','Observed outcome'],[[brief[r['id']][0],r['parameters'],brief[r['id']][1]] for r in ledger])+ '\n\nThe [full experiment ledger](data/replication_ledger.json) records scope and outcome categories, including interruptions and provider failures.',
        'RESULT_TABLE':table(['Submission','Workflow','Official test','Wilson 95%','Visible accuracy','Unused training','Format/service failures'],resultrows),
        'RESULT_INTERPRETATION':interpretation,'EXAMPLES':'\n\n'.join(exampleparts),
        'CONFUSION':confusion_text,
        'REASONING_TABLE':table(['Submission','Emitted reasoning text','Reasoning tokens','Raw evidence'],reasoning),
        'PARAMETER_TABLE':table(['Submission','Exact zeros / 6,570','Nonzero first-layer rows / 64','Nonzero second-layer rows / 32','Largest magnitude'],
            [[r['label'],r['zeros'],r['h1_nonzero_rows'],r['h2_nonzero_rows'],f"{r['max_abs']:.6g}"] for r in read(MLP/'data/parameter_use.json')]),
        'SPEND':table(['Submission','Native input tokens','Native output tokens','Wall time','Reported USD or list-price equivalent'],spend)}
    text=(MLP/'data/report_template.md').read_text(encoding='utf-8')
    for key,value in replacements.items():text=text.replace('{{'+key+'}}',value)
    text=text.replace('Six tool-free language models','Six tool-free language models')
    setup=code(MLP/'experiment.py')+'\n\n# Reproduction is offline; collection helpers are defined but never called.\nMAX_NEW_CALLS = 0\nALLOW_NEW_REQUESTS = False\n'+code(MLP/'analysis.py')
    setup+='\n\ndef _offline_network_guard(*args, **kwargs):\n    raise RuntimeError("Network requests are disabled in notebook replay; use the explicit collection script for new experiments.")\nrequests.sessions.Session.request = _offline_network_guard\n'
    replay='''# Revalidate only cached answers, never collect new ones.
for area in ['responses', 'recovery', 'indexed']:
    if not (DATA / area).exists():
        continue
    for folder in (DATA / area).iterdir():
        model_key = folder.name.split('-')[0]
        if model_key not in MODELS:
            continue
        cached = folder / ('assembled_response.json' if area == 'indexed' else 'response.json')
        if cached.exists():
            record = json.loads(cached.read_text(encoding='utf-8'))
            validate_and_score(model_key, record, out_override=folder)
summary = make_figures()
print(json.dumps({k:v for k,v in summary.items() if k != 'results'}, indent=2))
print('Fresh teacher calls: 0')'''
    replay+='''
reported_costs = []
claude_cumulative = []
for row in summary['results']:
    value = row.get('cost_usd')
    if value is not None:
        (claude_cumulative if row['model_key'] == 'opus' else reported_costs).append(value)
print('Reported USD/list-price equivalents, avoiding duplicate Claude cumulative counters:', sum(reported_costs) + max(claude_cumulative, default=0.0))
print('Other CLI dollar charges: not reported, not assumed zero.')
'''
    cells=[nbf.v4.new_code_cell(replay)]
    notebook(MLP,'41_direct_weight_mlps.ipynb',text,setup,cells)

if __name__ == '__main__':
    build_mlp()
    print((MLP/'README.md').stat().st_size)
