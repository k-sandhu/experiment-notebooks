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
    scored=sorted(valid,key=lambda r:-r['test']['accuracy']);unusable=[r for r in rows if not r.get('pending') and r.get('format_failure') is not None]
    num=lambda n:{1:'one',2:'two',3:'three',4:'four',5:'five',6:'six',7:'seven',8:'eight',9:'nine',10:'ten',11:'eleven',12:'twelve',13:'thirteen',14:'fourteen',15:'fifteen'}.get(n,str(n))
    n_models=len({r['model_key'] for r in rows});n_open=sum(bool(r.get('open')) for r in rows)
    first_valid=[r for r in readable if not r.get('open')];open_valid=[r for r in readable if r.get('open')]
    headline=(f"{num(n_models).capitalize()} models received {num(len(first))} first requests (Opus 5.5 twice, at two settings). "
              f"Of the {num(len(first)-n_open)} asked for a flat list of numbers, **{num(len(first_valid))} returned a network that could be scored**"
              +((f"; all {num(n_open)} open-weight models, asked for numbered entries from the start, did" if len(open_valid)==n_open
                 else f"; of the {num(n_open)} open-weight models asked for numbered entries from the start, {num(len(open_valid))} did") if n_open else '')
              +f". Counting numbered-entry retries, {num(len(scored))} networks could be scored in all. Best first, they classified this many of the 1,797 test images correctly: "
              +'; '.join(f"{r['label'].replace(' numbered entries',' (numbered entries)')} {r['test']['correct']:,} ({100*r['test']['accuracy']:.2f}%)" for r in scored)
              +f". The other {len(unusable)} submissions produced no network to score, and they are counted apart from wrong digits.")
    def workflow(r):
        if r.get('indexed'):return f"Numbered entries, {r['outer_requests']} call"+('s' if r['outer_requests']!=1 else '')
        if r.get('family'):return 'Claude request, high effort'
        if r.get('open'):return f"Numbered from the start, {r['outer_requests']} call"+('s' if r['outer_requests']!=1 else '')
        return 'Recovery' if r.get('recovery') else 'First request'
    resultrows=[];failrows=[]
    for r in a.ordered_rows(rows):
        if r in valid:
            lo,hi=np.array(r['test']['wilson_95'])*100
            resultrows.append([r['label'],workflow(r),f"{r['test']['correct']:,}/1,797 ({100*r['test']['accuracy']:.2f}%), {1797-r['test']['correct']} wrong",f'{lo:.2f}–{hi:.2f}%',
                               f"{100*r['visible']['accuracy']:.2f}%",f"{100*r['hidden_train']['accuracy']:.2f}%"])
        else:
            reason=a.failure_note(r)
            if r['model_key']=='opus' and r.get('recovery'):reason+=', citing a provider safety classifier'
            failures=(f"{r['outer_requests']} provider errors" if r.get('failure_category')=='provider_unavailable' else '1 unusable assembly') if (r.get('indexed') or r.get('open')) else '1 unusable reply'
            failrows.append([r['label'],workflow(r),reason,'Pending' if r.get('pending') else failures])
    models=table(['Teacher','Pinned version or runtime ID','Provider and call','Published size/precision','Output settings','Why included'],[
        ['GPT-6 Astra','gpt-6-astra; revision not exposed','OpenAI, codex exec','Not disclosed','xhigh; legacy 17-value medium; no tools','Requested author; known-rule successes'],
        ['GPT-6.1 Sol','gpt-6.1-sol; revision not exposed','OpenAI, codex exec','Not disclosed','xhigh; tools disabled','Requested second OpenAI numerical author'],
        ['Claude Opus 5.5','claude-opus-5-5; revision not exposed','Anthropic, claude -p','Not disclosed','xhigh with 64,000-token allowance first; high continuation; separate high request with 128,000 tokens; tools disabled','Requested independent vendor; the high-effort request checks whether the first failure was an output-budget effect'],
        ['Claude Fable 5.1','claude-fable-5-1; revision not exposed','Anthropic, claude -p','Not disclosed','high; 128,000-token allowance; tools disabled','Requested; completes the current Claude family'],
        ['Claude Sonnet 5.5','claude-sonnet-5-5; revision not exposed','Anthropic, claude -p','Not disclosed','high; 128,000-token allowance; tools disabled','Requested; mid-size Claude model'],
        ['Claude Haiku 5.5','claude-haiku-5-5; revision not exposed','Anthropic, claude -p','Not disclosed','high; 128,000-token allowance; tools disabled','Requested; smallest and fastest Claude model'],
        ['DeepSeek V4.1 Flash 1017','deepseek/deepseek-v4.1-flash-20261017; weights deepseek-ai/DeepSeek-V4.1-Flash-1017','DeepSeek, OpenRouter, no fallback','763B stored values in the published safetensors (MIT); serving precision not stated','medium reasoning; 131,072-token allowance; numbered entries from the start','Highest open-weight model on the Artificial Analysis Progress Index (324) that OpenRouter serves'],
        ['GLM-5.3','z-ai/glm-5.3-20260816; weights zai-org/GLM-5.3','Z.AI, OpenRouter, no fallback','753B stored values, mostly fp8 (GLM-5.3 licence); served in fp8','medium reasoning; 131,072-token allowance; numbered entries from the start','Second-highest open-weight model on the same index (323)'],
        ['MiMo-V2.6-Pro','xiaomi/mimo-v2.6-pro-20260921; weights XiaomiMiMo/MiMo-V2.6-Pro-RL','Xiaomi, OpenRouter, no fallback','1.02T stored values, mostly packed 8-bit (MIT); served in fp8','reasoning on (no effort setting); 131,072-token allowance; numbered entries from the start','Third open-weight model on the same index (321) that OpenRouter serves with weights'],
        ['Muse Wonder Full','muse-wonder-full-1.0; revision not exposed','Meta, muse exec','Not disclosed','xhigh; empty preset; tools disabled','Requested independent vendor'],
        ['Nemotron 3.5 Super VL','nvidia/nemotron-3.5-super-vl-20261015','NVIDIA, OpenRouter free','120B total, 12B active; precision not attested','Reasoning first; off indexed; 131,072 cap; free only','Requested open-weight author; 388-value comparison'],
        ['Gemini 4 Argon batch','google/gemini-4-argon-20261013','Google Vertex, OpenRouter Batch API','Not disclosed','high original and schema retry; low final variant; 131,072 requested output cap','Requested Google comparison; asynchronous batch route']])
    interpretation=''
    if readable:
        ordered=sorted(readable,key=lambda r:-r['test']['accuracy']);best=ordered[0]
        interpretation=f"The highest first-request score is {best['label']}'s, {best['test']['correct']:,}/1,797 ({100*best['test']['accuracy']:.2f}%); the nearest-neighbour reference labels {1750-best['test']['correct']} more images correctly. "
        if len(ordered)>1:interpretation+=f"{ordered[0]['label']} and {ordered[1]['label']}, both first requests, differ by {ordered[0]['test']['correct']-ordered[1]['test']['correct']} images. "
    recoveries=sorted([r for r in valid if r.get('recovery') or r.get('indexed')],key=lambda r:-r['test']['accuracy'])
    words={1:'One',2:'Two',3:'Three',4:'Four',5:'Five',6:'Six'}
    if recoveries:interpretation+=f"{words.get(len(recoveries),len(recoveries))} networks come from numbered-entry retries and are not first-reply successes: "+', '.join(f"{r['label'].replace(' numbered entries','')} {r['test']['correct']:,}" for r in recoveries)+'. '
    interpretation+='All of these are differences between single submitted networks, not a stable ranking across repeated requests or new datasets.'
    examples=read(MLP/'data/worked_examples.json');exampleparts=[]
    for i,c in enumerate(examples,1):
        short=lambda n:n.replace(' numbered entries','').replace(' high','').replace(' batch','')
        wrong=[f'{short(name)} → {value}' for name,value in c['predictions'].items() if value!=c['gold']]
        preds=(f"{len(c['predictions'])-len(wrong)} of {len(c['predictions'])} networks correct"+(f"; wrong: {', '.join(wrong)}" if wrong else ''))
        why='The shown predictions disagree with the gold label for at least one network.' if any(v!=c['gold'] for v in c['predictions'].values()) else 'Every available prediction shown matches the gold label.'
        exampleparts.append(f"### Case {i}: `{c['id']}`, gold digit {c['gold']}\n\nSelection: {c['selection']}. {preds}.")
    if valid:
        lead=sorted(valid,key=lambda r:-r['test']['accuracy'])[0];c=examples[0]
        with np.load(MLP/'data/dataset.npz') as d:raw=d['test'][c['index'],:64]
        with np.load(MLP/'data'/lead['candidate_folder']/'predictions.npz') as d:scores=d['test_scores'][c['index']]
        exampleparts.append(f"### End-to-end calculation for `{c['id']}`\n\nThe first eight raw ink counts are `{raw[:8].tolist()}`; dividing by sixteen gives `{(raw[:8]/16).tolist()}`, and the other 56 inputs are scaled the same way. {lead['label']}'s unchanged matrices yield these ten scores:\n\n"+
            ' · '.join(f'{j}: {v:.6g}' for j,v in enumerate(scores))+
            f"\n\nThe largest score has digit {int(scores.argmax())}; the hidden label is {c['gold']}, so this image adds {int(scores.argmax()==c['gold'])} to the network's correct count. Nothing is fed back into its parameters.")
    reasoning=[];spend=[]
    for r in a.ordered_rows(rows):
        folder=MLP/'data'/r['candidate_folder'];u=a.usage_row(r);rt=u['reasoning_tokens']
        chars=r.get('reasoning_characters',0);link=(folder/'reasoning.txt').relative_to(MLP).as_posix()
        evidence=MLP/'data'/u['evidence'] if u['evidence'] else (folder if r.get('indexed') else folder/'events.jsonl')
        cost_value=u['cost_usd'];cost=f"${cost_value:.2f}" if cost_value is not None else 'Not reported'
        if r['model_key']=='opus' and r.get('recovery') and cost_value is not None:cost+=' (session total)'
        fmt=lambda v:f'{v:,}' if v is not None else 'Not reported'
        spend.append([r['label'],fmt(u['input_tokens']),fmt(u['output_tokens']),fmt(rt),f"{u['wall_seconds']:,.0f} s" if u['wall_seconds'] is not None else 'Pending',cost])
    confusion_text='No scored network is available for a confusion matrix yet.'
    if valid:
        lead=sorted(valid,key=lambda r:-r['test']['accuracy'])[0];cm=np.array(lead['test']['confusion']);off=cm.copy();np.fill_diagonal(off,0)
        positions=np.argsort(off.ravel())[::-1][:2];details=[]
        for position in positions:
            gold,pred=np.unravel_index(position,off.shape)
            details.append(f"{off[gold,pred]} of {cm[gold].sum()} true digit-{gold} images were labelled {pred}")
        confusion_text=f"![Confusion matrix for highest observed score](figures/confusion.png)\n\nRows are gold digits and columns are predictions. Each cell counts official test images, and the diagonal counts correct answers. For {lead['label']}, "+'; '.join(details)+'. These are the two largest off-diagonal counts; they show which confusions recur, not why.'
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
      'mlp6570':('Sample-based digit MLP, twelve models','First requests: Astra 91.54%, Fable 90.60%, Sol 79.13%, Muse 33.72%; open-weight 10.8% to 21.1%; six unusable'),
      'indexed-output':('Numbered entries and continuation','Opus 87.92%, Sonnet 67.56%, Gemini 60.71%; Nemotron timeouts; Haiku declined')}
    replacements={'HEADLINE':headline,'MODEL_TABLE':models,'PREPOST':'```python\n'+(MLP/'data/pre_post_processing.py.txt').read_text()+'```',
        'REPLICATION_LEDGER':table(['Experiment','Network size','Observed outcome'],[[brief[r['id']][0],r['parameters'],brief[r['id']][1]] for r in ledger])+ '\n\nThe [full ledger](data/replication_ledger.json) adds scope, interruptions and provider failures.',
        'RESULT_TABLE':table(['Submission','Workflow','Official test','Wilson 95%','Visible accuracy','Unused training'],resultrows)
            +'\n\nThese submissions produced no network to score:\n\n'+table(['Submission','Workflow','Why no network','Unusable replies'],failrows),
        'RESULT_INTERPRETATION':interpretation,'EXAMPLES':'\n\n'.join(exampleparts),
        'SONNET_TEMPLATE_CHECK':(lambda e:'the one-template-per-digit reading of Sonnet\'s network matches its full scores exactly' if e==0 else
            f'the one-template-per-digit reading of Sonnet\'s network matches its full scores to within {e:.1g}')(read(MLP/'data/program_structure.json')['template_matching']['Sonnet 5.5 numbered entries']['max_difference_from_full_network']),
        'SCORED_TOKEN_RANGE':(lambda s:f"{min(s):,} to {max(s):,}")([u['output_tokens'] for u in read(MLP/'data/usage_summary.json') if u['usable']]),
        'CONFUSION':confusion_text,
        'PARAMETER_TABLE':table(['Submission','Exact zeros / 6,570','Nonzero first-layer rows / 64','Nonzero second-layer rows / 32','Largest magnitude'],
            [[r['label'],r['zeros'],r['h1_nonzero_rows'],r['h2_nonzero_rows'],f"{r['max_abs']:.6g}"] for r in read(MLP/'data/parameter_use.json')]),
        'SPEND':table(['Submission','Input tokens','Output tokens','Of which reasoning','Wall time','Reported USD or list-price equivalent'],spend)}
    text=(MLP/'data/report_template.md').read_text(encoding='utf-8')
    for key,value in replacements.items():text=text.replace('{{'+key+'}}',value)
    text=text.replace('Six tool-free language models','Six tool-free language models')
    setup=code(MLP/'experiment.py')+'\n\n# Reproduction is offline; collection helpers are defined but never called.\nMAX_NEW_CALLS = 0\nALLOW_NEW_REQUESTS = False\n'+code(MLP/'analysis.py')
    setup+='\n\ndef _offline_network_guard(*args, **kwargs):\n    raise RuntimeError("Network requests are disabled in notebook replay; use the explicit collection script for new experiments.")\nrequests.sessions.Session.request = _offline_network_guard\n'
    replay='''# Revalidate only cached answers, never collect new ones.
for area in ['responses', 'recovery', 'indexed', 'claude_family', 'open_models']:
    if not (DATA / area).exists():
        continue
    for folder in (DATA / area).iterdir():
        model_key = folder.name.split('-')[0]
        if model_key not in MODELS:
            continue
        cached = folder / ('assembled_response.json' if area in ('indexed', 'open_models') else 'response.json')
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
    value = usage_row(row)['cost_usd']
    if value is not None:
        # The first Opus request and its continuation share one session, whose counter is cumulative.
        first_session = row['model_key'] == 'opus' and not row.get('family') and not row.get('indexed')
        (claude_cumulative if first_session else reported_costs).append(value)
print('Reported USD/list-price equivalents, avoiding duplicate Claude cumulative counters:', round(sum(reported_costs) + max(claude_cumulative, default=0.0), 2))
print('Other CLI dollar charges: not reported, not assumed zero.')
'''
    cells=[nbf.v4.new_code_cell(replay)]
    notebook(MLP,'41_direct_weight_mlps.ipynb',text,setup,cells)

if __name__ == '__main__':
    build_mlp()
    print((MLP/'README.md').stat().st_size)
