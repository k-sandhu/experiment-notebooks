"""Create an illustrated report from cached measurements; no model calls."""
from pathlib import Path
import base64
import html
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from safetensors.numpy import load_file

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data';FIG=ROOT/'figures';BASE=ROOT.parent
def read(name):return json.loads((DATA/name).read_text(encoding='utf-8'))
stats=read('weight_stats.json');summary=read('decoding_summary.json');records=read('all_generations.json')
structure=read('mlp_structure.json');bound=read('logit_scale_bound.json');precision=read('precision.json');cast=read('float16_representability.json')
stress=read('boundary_stress.json')
forced=read('teacher_forced_tokens.json');parity=read('parity.json');first=read('first_token_logits.json');environment=read('environment.json')
assert len(summary)==11,'Wait for every decoding condition to finish'
models=load_file(str(BASE/'tiny-sql-2208'/'round-03-astra'/'attempt-02'/'astra_candidate.safetensors'))
mlp=dict(np.load(BASE/'mlp-rings-388'/'data'/'astra'/'candidate.npz'))
reference=load_file(str(DATA/'reference'/'model.safetensors'))
groups={'SQL transformer':np.concatenate([v.ravel().astype(float) for k,v in models.items() if k!='frozen_embeddings']),
        'Successful MLP':np.concatenate([v.ravel() for v in mlp.values()]),
        'Trained Pythia core':np.concatenate([v.ravel().astype(float) for k,v in reference.items() if 'embed_' not in k])}
plt.rcParams.update({'figure.dpi':145,'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
palette=['#b3483d','#3779a5','#5d956e']
fig,axes=plt.subplots(1,2,figsize=(11,4.5),constrained_layout=True)
bins=np.linspace(-30,23,90)
for (name,v),color in zip(groups.items(),palette):
    nz=np.log10(np.abs(v[v!=0]));hist,_=np.histogram(nz,bins=bins)
    axes[0].stairs(hist/len(nz),bins,label=name,color=color,linewidth=1.8)
axes[0].set(xlabel='log10 absolute nonzero weight (for example, −24 means 10⁻²⁴)',ylabel='Fraction of nonzero values per bin',title='The SQL weights span about 51 orders of magnitude')
axes[0].legend(fontsize=8)
zero=np.array([(v==0).mean()*100 for v in groups.values()])
bars=axes[1].bar(range(3),zero,color=palette)
axes[1].set(xticks=range(3),xticklabels=['SQL\n2,208 values','MLP\n388 values','Pythia core\n1,189,888 values'],ylabel='Exactly zero weights (%)',title='Sparsity alone does not explain success',ylim=(0,68))
for b,val in zip(bars,zero):axes[1].text(b.get_x()+b.get_width()/2,val+1,f'{val:.3g}%',ha='center')
fig.savefig(FIG/'weight_profiles.png');plt.close(fig)

fig,axs=plt.subplots(2,2,figsize=(10,8),constrained_layout=True)
ax=axs[0,0]
for i,v in enumerate(mlp['W1']):
    if np.linalg.norm(v)>0:
        ax.arrow(0,0,*v,length_includes_head=True,head_width=.045,color='#3779a5' if i<7 else '#b3483d',alpha=.8)
ax.add_patch(plt.Circle((0,0),1,fill=False,color='grey',linestyle=':'))
ax.set(xlim=(-1.2,1.2),ylim=(-1.2,1.2),aspect='equal',xlabel='Weight on x1',ylabel='Weight on x2',title='MLP W1: 14 unit directions and 2 unused neurons')
im=axs[0,1].imshow(mlp['W2'],cmap='RdBu_r',vmin=-1,vmax=1,aspect='auto')
axs[0,1].set(xlabel='First-layer neuron',ylabel='Second-layer neuron',title='MLP W2 repeats two column groups: rank 2')
fig.colorbar(im,ax=axs[0,1],label='Weight')
r=np.linspace(0,1,501)
for k in range(4):axs[1,0].plot(r,k*r+mlp['b3'][k],label=f'Class {k}')
for cut in structure['radial_feature_thresholds']:axs[1,0].axvline(cut,color='grey',linestyle=':',linewidth=.7)
axs[1,0].set(xlabel='Estimated radius feature',ylabel='Class score',title='Four scores are almost multiples of one feature')
axs[1,0].legend(fontsize=8)
theta=np.linspace(0,2*np.pi,36000,endpoint=False);x=np.column_stack([np.cos(theta),np.sin(theta)])
h1=np.maximum(0,x@mlp['W1'].T+mlp['b1']);h2=np.maximum(0,h1@mlp['W2'].T+mlp['b2']);radial=h2@mlp['W3'][1]
keep=theta<np.pi/2
axs[1,1].plot(np.degrees(theta[keep]),(radial[keep]-1)*1e6,color='#3779a5',linewidth=.75)
axs[1,1].axhline(0,color='black',linestyle='--',linewidth=.8)
axs[1,1].set(xlabel='Angle on the unit circle (degrees)',ylabel='Radius error (parts per million)',title='A small polygonal error remains between directions')
fig.savefig(FIG/'mlp_structure.png');plt.close(fig)

names={'greedy':'Raw greedy','greedy_trim_stop':'Trim + stop at semicolon','suppress_special':'Suppress control tokens',
       'repetition_1.2':'Repetition penalty 1.2','repetition_generated_only':'Penalty on generated tokens only',
       'no_repeat_trigram':'Block repeated trigrams','combined':'Penalty + trigram block',
       'sample_standard':'Sampling: T=0.7, top-p=0.9','beam4_standard':'Four-beam search',
       'sample_calibrated_DIAGNOSTIC':'Sampling + logit rescaling*','beam4_calibrated_DIAGNOSTIC':'Beam search + logit rescaling*'}
fig,ax=plt.subplots(figsize=(10,7.4),constrained_layout=True)
for i,row in enumerate(summary):
    pct=100*row['parseable_select']/row['n_outputs']
    color='#cb8a3a' if 'DIAGNOSTIC' in row['condition'] else '#3779a5'
    ax.barh(i,pct,color=color)
    ax.text(max(1,pct+1),i,f"{row['parseable_select']}/{row['n_outputs']} parsed; {row['schema_match']} correct",va='center',fontsize=8)
ax.set(yticks=range(len(summary)),yticklabels=[names[s['condition']] for s in summary],xlabel='Parser-accepted SELECT outputs (%)\n* Diagnostic output-logit gain; original checkpoint unchanged.',xlim=(0,108),
       title='Generation controls change syntax, but none recovers the requested schema')
ax.invert_yaxis()
fig.savefig(FIG/'decoder_comparison.png');plt.close(fig)

by_case={row['case']['id']:row['case'] for row in records if row['request']['decoding']['name']=='greedy'}
role_stats=[]
roles={}
for t in forced:
    case=by_case[t['case_id']];token=t['expected_token']
    role='Identifier words' if token in [case['table'],*case['columns']] else ('SQL keywords' if token in ['select','from'] else ('EOS' if token=='<EOS>' else 'Spaces / punctuation'))
    roles.setdefault(role,[]).append(t['rank'])
for name,ranks in roles.items():role_stats.append({'role':name,'n':len(ranks),'top1':sum(r==1 for r in ranks),'median_rank':float(np.median(ranks))})
(DATA/'teacher_forced_summary.json').write_text(json.dumps(role_stats,indent=2),encoding='utf-8')
repeat_rates={}
for row in summary:
    group=[r for r in records if r['request']['decoding']['name']==row['condition']]
    pairs=sum(max(0,len(r['generated_ids'])-1) for r in group)
    repeat_rates[row['condition']]={'adjacent_pairs':pairs,'repeated_pairs':row['adjacent_repeated_tokens'],
                                    'repeat_rate':row['adjacent_repeated_tokens']/pairs if pairs else 0}
(DATA/'repeat_rates.json').write_text(json.dumps(repeat_rates,indent=2),encoding='utf-8')

def esc(x):return html.escape(str(x))
def image(name,alt):
    data=base64.b64encode((FIG/name).read_bytes()).decode()
    return f'<figure><img src="data:image/png;base64,{data}" alt="{esc(alt)}"></figure>'
def table(headers,rows):return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def link(url,title):return f'<a href="{url}">{title}</a>'
def pct(x):return f'{x*100:.2f}%'
def science(x):return f'{x:.3g}'
zero_sql=stats['summary']['sql']['zero_fraction'];raw=summary[0];total=sum(r['n_outputs'] for r in summary)
all_zero=all(r['schema_match']==0 for r in summary)
assert all_zero,'Revise the report interpretation: a decoder matched a schema.'
sql_known=json.loads((BASE/'tiny-sql-2208'/'round-03-astra'/'attempt-02'/'raw_outputs.json').read_text(encoding='utf-8'))
mlp_result=json.loads((BASE/'mlp-rings-388'/'results.json').read_text(encoding='utf-8'))
meta=read('reference/metadata.json')
reference_rows=[]
for name,label in [('sql','Astra SQL transformer'),('mlp','Astra ring MLP'),('reference_core','Pretrained Pythia core')]:
    s=stats['summary'][name]
    reference_rows.append([label,f"{s['n']:,}",f"{s['zeros']:,} ({s['zero_fraction']*100:.6g}%)",science(s['min_abs_nonzero']),science(s['max_abs'])])
decoder_rows=[]
for row in summary:
    repeat=repeat_rates[row['condition']]['repeat_rate']
    decoder_rows.append([esc(names[row['condition']]),str(row['n_outputs']),str(row['parseable_select']),str(row['unreadable_sql']),str(row['wrong_readable']),str(row['schema_match']),str(row['eos']),pct(repeat)])
example_conditions=['greedy','repetition_1.2','no_repeat_trigram','sample_standard','beam4_calibrated_DIAGNOSTIC']
example_rows=[]
for name in example_conditions:
    rec=next(r for r in records if r['request']['decoding']['name']==name and r['case']['id']=='example-2')
    example_rows.append([esc(names[name]),'<pre>'+esc(rec['scored_output'])+'</pre>',esc('Parses, wrong schema' if rec['score']['parseable_select'] else 'Does not parse as one SELECT')])

content=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Astra-generated weights: numerical study and decoding tests</title><style>
body{{font-family:system-ui,Segoe UI,sans-serif;color:#202b36;background:#f5f7f9;margin:0;line-height:1.65}}
main{{max-width:1050px;margin:32px auto;background:white;padding:36px 46px;border:1px solid #dae1e8;border-radius:12px}}
h1{{font-size:2rem;line-height:1.2}}h2{{margin-top:2.2em;border-top:1px solid #dce2e7;padding-top:1em}}h3{{margin-top:1.6em}}
a{{color:#24618f}}.lead{{font-size:1.12rem}}.note{{background:#f1f5f8;padding:16px 20px;border-left:4px solid #3779a5}}.scroll{{overflow:auto}}
table{{border-collapse:collapse;width:100%;font-size:.91rem;margin:18px 0}}th,td{{border-bottom:1px solid #dce2e7;padding:9px 10px;text-align:left;vertical-align:top}}th{{background:#f0f4f7}}
pre,code{{font-family:Consolas,monospace}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.86rem;margin:0}}figure{{margin:24px 0}}img{{max-width:100%;height:auto}}
.small{{font-size:.85rem;color:#566371}}li{{margin:.4em 0}}@media(max-width:700px){{main{{margin:0;padding:22px}}}}
</style><main><h1>Astra-generated weights: what works, what fails, and whether decoding helps</h1>
<p class="small">Exploratory diagnostic study • November 2, 2026 • Original weights preserved • No training or fresh LLM requests</p>
<p class="lead">The successful classifier looks like a compact numerical program. The SQL transformer also has a highly engineered weight pattern, but its output scores are so small that ordinary softmax becomes uniform. Standard decoding controls changed its text without recovering the requested table and columns.</p>
<p>A weight is a number used inside a network's calculations. The same architecture can implement useful or useless functions depending on those numbers. Looking for a familiar histogram is therefore only a first check: the important questions are which function the numbers compute and whether the resulting scores support the intended decoding procedure.</p>
<p>This study examines the 388 values Astra supplied for the two-hidden-layer ring classifier and the 2,208 editable values it supplied for the one-block SQL transformer. It also measures one real pretrained language-model checkpoint as a distributional reference. The reference is not a SQL benchmark or a universal template for how all LLM weights should look.</p>
<nav><b>Contents:</b> <a href="#method">Method</a> · <a href="#profiles">Weight profiles</a> · <a href="#mlp">The working MLP</a> · <a href="#sql">The SQL model</a> · <a href="#decoders">Decoding tests</a> · <a href="#recommend">Practical postprocessing</a> · <a href="#limits">Limits and reproduction</a></nav>
<h2 id="method">1. What was measured</h2>
<p>The SQL checkpoint is Astra attempt 2 at <code>xhigh</code>. Its original greedy outputs on 16 schemas were reproduced exactly before the sweep. All 123 existing synthetic schemas were then evaluated under 11 fixed decoding conditions, producing {total:,} outputs. Sampling conditions use three seeds per schema; other conditions use one. The 16 inspected schemas and the 12 examples Astra received as feedback are not a blind benchmark. The additional 107 schemas broaden this diagnosis.</p>
<p>Every SQL condition uses the same frozen checkpoint, float64 arithmetic, up to 32 new tokens and a 64-token context limit. The tested controls do not contain a SQL grammar, a query template, a schema-copy routine or a replacement-name rule. The checkpoint hash remained unchanged. Each generation and full request is cached in <a href="data/generations/">data/generations/</a>; derived whitespace cleanup reuses the raw greedy output. Repetition and sampling processors come from Transformers 4.55.0; four-beam search is implemented in the tester using normalized log probabilities and length normalization. The same three sampling seeds are reused across schemas for paired comparisons, so the 369 sampled outputs are not 369 independent random streams.</p>
<p>SQL text was parsed with SQLGlot's SQLite dialect. A readable result means exactly one parsed SELECT. A schema match additionally requires the requested table and the requested column names in order, as plain column projections without filters or other extra clauses. <b>No tables were created and no SQL was executed.</b> Parser acceptance does not establish SQLite executability or correct returned rows. Parser failures and readable wrong answers are reported separately.</p>
<p>The independent reference is <a href="https://huggingface.co/EleutherAI/pythia-14m">EleutherAI/pythia-14m</a>, revision <code>{meta['sha']}</code>, Apache-2.0, stored in FP16. Its {sum(v.size for v in reference.values()):,} checkpoint values include large embedding tables; the comparison below uses the {stats['summary']['reference_core']['n']:,} non-embedding values. Only its weights were read; it was not used to generate text. Pythia is an open research suite designed for studies of training and scaling. <a href="https://arxiv.org/abs/2304.01373">Biderman et al. (2023)</a>.</p>
<h2 id="profiles">2. These are programmed weights, not ordinary pretrained profiles</h2>
{table(['Weights examined','Count','Exactly zero','Smallest nonzero magnitude','Largest magnitude'],reference_rows)}
{image('weight_profiles.png','Nonzero weight magnitude distributions and exact-zero fractions for Astra SQL, Astra MLP and pretrained Pythia core weights.')}
<p>The SQL values span {math.log10(stats['summary']['sql']['max_abs']/stats['summary']['sql']['min_abs_nonzero']):.1f} orders of magnitude. Its projection has RMS scale about 10⁻²⁴, while attention and feed-forward tensors contain values up to 10²⁰ and 10²². Its positional embedding RMS is about 10⁻¹³. The successful MLP instead has nonzero magnitudes from about 0.007 to 6, and only 63 distinct numeric values.</p>
<p>The trained reference is almost entirely dense: only two of its 1,189,888 core values are exactly zero. All 24 of its core matrices have full numerical rank, while the MLP's W2 and W3 have ranks 2 and 1. This is a measured contrast between these checkpoints, not a requirement for competence. The MLP demonstrates that a sparse, low-rank construction can be an excellent solution to a structured task.</p>
<p>There is no universal “healthy LLM weight histogram.” In a ReLU MLP, multiplying one neuron's incoming weights and bias by a positive constant and dividing its outgoing weights by the same constant preserves its function; magnitudes can therefore differ between equivalent networks. Permuting hidden units also preserves their function while changing their coordinate layout. <a href="https://arxiv.org/abs/2209.04836">Git Re-Basin (Ainsworth et al., 2023)</a> studies such permutation equivalences. Large-model research also finds important activation outliers; these should not automatically be clipped as errors. <a href="https://arxiv.org/abs/2208.07339">LLM.int8() (Dettmers et al., 2022)</a>. That activation result does not establish that this SQL model's enormous weight scale is useful.</p>
<p>The setup also differs from editing a pretrained LLM. The original <a href="https://rikiyat.github.io/blog/weight-space-programming/">weight-space-programming report</a> distinguishes constructing small networks from scratch from modifying an already-trained Qwen language model. Our SQL experiment supplies frozen word vectors but asks Astra to construct the autoregressive computation itself. <a href="https://aclanthology.org/D14-1162/">GloVe (Pennington et al., 2014)</a> learns word representations from word co-occurrence; it does not supply this transformer's sequence-generation behavior.</p>
<h2 id="mlp">3. The MLP can be interpreted as a radius estimator and three thresholds</h2>
<p>The first matrix has 14 nonzero unit-length directions and two unused rows. Its second matrix repeats two groups of columns, giving it numerical rank 2. Its output rows are, to within {structure['maximum_residual_from_W3_row_k_equals_k_times_row1']:.2g}, 0, 1, 2 and 3 times one vector. This means the output layer essentially uses a single scalar feature, which numerical probes identify as an estimated radius.</p>
<p>Writing that scalar as s(x), the four scores are approximately <code>0, s−0.249999616, 2s−0.749997887, 3s−1.499994685</code>. Adjacent scores cross at estimated radii {', '.join(f'{v:.9f}' for v in structure['radial_feature_thresholds'])}, very close to the task boundaries 0.25, 0.50 and 0.75. This is a functional explanation obtained from the emitted weights, not a claim about Astra's private reasoning.</p>
{image('mlp_structure.png','First-layer directions, the rank-two second matrix, four linear output scores, and measured angular error of the MLP radius feature.')}
<p>On 36,000 angles around the unit circle, the inferred radius lies between {structure['radial_feature_min']:.9f} and {structure['radial_feature_max']:.9f}. Its largest sampled relative error is {structure['radial_feature_max_absolute_error']*1e6:.2f} parts per million. Zero hidden biases make this feature positively homogeneous: scaling a nonnegative input radius scales the feature by the same factor. This supports the radius interpretation across radii, although finite angular sampling is not an exhaustive proof.</p>
<p>The original tests gave 20,000/20,000 balanced random points correct and 125,601/125,625 grid points correct. All 24 grid errors occurred at the specified class boundaries within 3×10⁻¹⁷, where tiny approximation and floating-point differences can change the selected side. The random test is at a ceiling, so it cannot resolve small differences among equally successful constructions.</p>
<p>A post-hoc stress test deliberately sampled within 10⁻⁵ or 10⁻⁶ of the three boundaries, using 3,600 angles per boundary/offset pair. It produced {stress['correct']:,}/{stress['total_points']:,} correct classifications ({pct(stress['correct']/stress['total_points'])}). This sample is intentionally concentrated on difficult slivers and is not an estimate of ordinary input accuracy. It confirms that the measured 100% random-sample score is not exact correctness everywhere. The offsets were fixed before this stress test and no weights were changed.</p>
{table(['True radius boundary','Offset from boundary','Correct / tested','Accuracy'],[[r['boundary'],f"{r['offset']:+.0e}",f"{r['correct']}/{r['n']}",pct(r['accuracy'])] for r in stress['rows']])}
<h2 id="sql">4. The SQL head has a global score-scale problem</h2>
<p>The effective vocabulary matrix is <code>F = frozen_GloVe @ projection</code>. The same F supplies the input vectors and output classifier. Sharing embeddings is a legitimate language-model design: <a href="https://arxiv.org/abs/1608.05859">Press and Wolf (2017)</a> describe training tied input and output embeddings. Our frozen-vector/shared-projection construction is a much stronger restriction than co-training those embeddings.</p>
<p>In the current checkpoint, all final LayerNorm gains are √10⁻⁵ ≈ 0.003162 and the final biases are zero. A width-8 normalized vector has L2 norm below √8, so the final hidden-state norm is bounded by {bound['final_hidden_l2_upper_bound']:.6g}. Combining this with the largest effective output-vector norm gives an absolute logit bound of <b>{bound['absolute_logit_upper_bound']:.3g}</b>, for every input sequence. This follows from LayerNorm's definition and the Cauchy–Schwarz inequality.</p>
<p>The first observed logits are around 10⁻³³. At ordinary temperature, softmax produces exactly 1/1,110 ≈ 0.0009009009 for every token in our float64 measurements. The head's bound is far below machine epsilon near 1, so ordinary exponentiation cannot resolve those differences. The correct-query token likelihood is correspondingly uniform. Greedy argmax still compares the tiny unnormalized scores directly and can therefore emit structured-looking fragments such as SELECT and FROM.</p>
<p>All three LayerNorm gains equal √epsilon. For vectors with variance much smaller than epsilon, this makes LayerNorm approximately subtract the mean without changing the scale. Combined with sparse huge/small coefficients, this is consistent with an attempt to program numerical gates. That is an interpretation of the weights, not confirmation of the author's intent. We did not reverse-engineer every gate.</p>
{table(['Canonical target-token group','Tokens examined','Expected token ranked first','Median rank'],[[esc(r['role']),r['n'],r['top1'],r['median_rank']] for r in role_stats])}
<p>These ranks use the correct preceding tokens (“teacher forcing”), not the model's own damaged prefixes. They diagnose the emitted checkpoint's preferences for one canonical spelling of the desired query. Other whitespace or capitalization could also be valid. The detailed per-token ranks and numerical output-geometry probe are saved in <a href="data/teacher_forced_tokens.json">the token diagnostics</a> and <a href="data/output_geometry.json">the geometry results</a>. The geometry probe is a numerical max-margin test, not an exact impossibility certificate.</p>
<p>An independent implementation of the specified forward equations agreed with the GPT-2 scaffold to a maximum {max(r['max_relative_to_logit_max'] for r in parity):.3g} relative to the largest logit, across 16 prompts. The original 16 generated outputs were reproduced exactly. This makes a simple tensor-order or transpose mistake less likely. Float32 generated identical token sequences on {sum(r['identical_ids'] for r in precision)}/16 cases, so higher precision alone has not been shown to fix the task.</p>
<p>Float16 is a separate portability problem: direct conversion overflows {cast['sql']['nonfinite_in_float16']} SQL values and rounds {cast['sql']['nonzero_values_rounded_to_zero_in_float16']} nonzero values to zero. The original task explicitly requested float64, so this is not a failure of that contract; it is evidence that ordinary FP16 deployment would require additional work. The MLP has neither representability problem under this check.</p>
<h2 id="decoders">5. Standard decoding controls do not repair schema binding</h2>
<p>Repetition penalties, no-repeat n-grams, sampling parameters, beam counts, suppressed tokens and stopping strings are common generation controls documented by <a href="https://huggingface.co/docs/transformers/en/main_classes/text_generation">Hugging Face Transformers</a>. They change how scores become text. They do not create a learned association between an input table name and the output identifier.</p>
{table(['Condition','Outputs','Parsed SELECT','Unreadable SQL','Readable but wrong','Schema matches','EOS stops','Adjacent repeat rate'],decoder_rows)}
{image('decoder_comparison.png','Parser acceptance under eleven decoding conditions. No condition matches the requested table and columns.')}
<p>Raw greedy produces a parser-accepted SELECT on {raw['parseable_select']}/123 cases ({pct(raw['parseable_select']/123)}), but all of those readable queries use the wrong schema or projection. The task score is 0/123. Reporting only parse acceptance would seriously overstate its usefulness.</p>
<p>Whitespace trimming and stopping after a semicolon leave the result unchanged. A repetition penalty of 1.2 reduces parser acceptance to {summary[3]['parseable_select']}/123. Blocking repeated trigrams reduces it to {summary[5]['parseable_select']}/123, even though it causes more EOS stops and less adjacent repetition. Stopping and non-repetition are not substitutes for selecting the right identifiers. Repeated quotation and separator patterns can be necessary in code, so hard n-gram bans deserve particular care.</p>
<p>Ordinary sampling and unscaled beam search operate on essentially uniform token probabilities here. A separate diagnostic multiplies logits by the inverse first-prompt logit standard deviation, about {1/first[0]['std_logit']:.3g}. This is a fixed output-score scale change, equivalent to an exceptionally small positive temperature. It was chosen from score magnitude, not tuned on correctness, and leaves all greedy rankings unchanged. This scale restoration is distinct from fitting a temperature to calibrate statistical confidence. The rescaled conditions remain at zero schema matches. Scaling can make relative scores visible to probability-based decoding; it cannot correct their ordering.</p>
<h3>A worked case: users(name,date)</h3>
<p>The requested query is <code>select "name","date" from "users";</code>. Below are literal generated outputs from the same checkpoint. These examples show the original failure and the effect of several controls; they were selected by stable item ID <code>example-2</code>, not by which output looked best.</p>
{table(['Condition','Observed output','Parser result'],example_rows)}
<p>A readable wrong query remains a failure even if a repetition control makes it shorter. For instance, other raw outputs include <code>select "login" from login</code> for the requested schema <code>subscribe(calendar)</code>. That text resembles a query, but it does not select the requested column from the requested table.</p>
<h2 id="recommend">6. Postprocessing that is reasonable to use</h2>
<ul>
<li><b>Keep harmless cleanup:</b> trim outer whitespace, decode special tokens consistently, stop on EOS and optionally a completed statement delimiter. These are useful output-hygiene controls; this checkpoint's scores did not improve under them.</li>
<li><b>Use repetition controls cautiously:</b> the tested penalty and n-gram bans reduced some repetition but did not improve the task, and they lowered parser acceptance. A penalty applied to the full prompt can also penalize the very names the model should copy.</li>
<li><b>Address output-score scale before sampling or beam search:</b> this model requires a special calibration because its logits are extraordinarily small. A positive scalar preserves greedy argmax. This is not a recommendation to use a temperature near 10⁻³³ on ordinary pretrained models.</li>
<li><b>Parse and reject invalid output:</b> validation can prevent downstream use of malformed SQL. It should report a failure rather than silently substitute different names. It adds reliability checks, not model competence.</li>
<li><b>Consider grammar-constrained decoding as a separate experiment:</b> <a href="https://arxiv.org/abs/2109.05093">PICARD (Scholak et al., 2021)</a> rejects syntactically inadmissible SQL continuations during decoding. It is a standard research-backed direction, but supplies external language rules. Restricting names to the supplied schema adds task knowledge too. Such results should be labeled separately from the unassisted network. No grammar constraint was used in this study.</li>
<li><b>For the MLP, keep argmax for class decisions:</b> softmax is optional for displaying scores as a distribution and does not change the winning class. Positive temperature scaling also preserves that winner. If calibrated probabilities are required, evaluate them on a separate labeled calibration set. <a href="https://arxiv.org/abs/1706.04599">Guo et al. (2017)</a> study post-hoc temperature calibration.</li>
</ul>
<p>Blanket normalization or clipping of the SQL weights would alter the numerical program. It is not ordinary text postprocessing and was not done. A useful next feedback message to the weight author would give the measured logit bound, the uniform softmax result, the canonical identifier ranks, and concrete wrong input/output pairs. The tester should continue to leave candidate weight selection to the separate model.</p>
<h2 id="limits">7. Limits, saved evidence and reproduction</h2>
<p>This is one emitted SQL checkpoint, one emitted MLP, one trained reference and a small synthetic schema set. It cannot establish a universal distribution for trained LLM weights or a general limit on Astra's ability. It is exploratory: the failure outputs were known before the diagnostic plan was written. No condition achieved any correct schema matches, so the sweep sits at a task-score floor and cannot rank general SQL competence. Parser validity is informative about formatting only.</p>
<p>The reference differs in width, number of layers, architecture, training, parameter count and precision. Half-precision storage affects its smallest values and number of distinct values. The measured comparison is descriptive. Attention distributions, matrix ranks and magnitude ranges do not independently identify every cause of failure.</p>
<p>All original candidate files remain unchanged. There were no new paid model calls, no optimization steps, no gradients and no generated reference-model text. The study ran on CPU with one Torch thread. The reference checkpoint file is about 28 MB and is pinned to the revision above. Every local generation is cached by checkpoint hash, prompt, seed and complete decoding settings.</p>
<ul><li><a href="study.py">Study code</a> and <a href="render_report.py">report/figure code</a>.</li>
<li><a href="data/decoder_protocol.json">Fixed decoding conditions and scoring protocol</a>.</li>
<li><a href="data/weight_stats.json">Per-tensor and aggregate weight statistics</a>, <a href="data/first_token_logits.json">logit measurements</a>, and <a href="data/logit_scale_bound.json">global bound</a>.</li>
<li><a href="data/decoding_summary.json">Decoding results</a>, <a href="data/all_generations.json">all generated outputs and requests</a>, and <a href="data/precision.json">precision checks</a>.</li>
<li><a href="data/mlp_structure.json">MLP structure measurements</a>, <a href="data/boundary_stress.json">boundary stress test</a>, <a href="data/parity.json">independent-forward comparison</a>, and <a href="data/environment.json">software versions</a>.</li></ul>
<p>From this folder, replay with the original experiment's Python environment:</p>
<pre>python download_reference.py
python study.py diagnostics
python study.py decoding
python boundary_stress.py
python render_report.py</pre>
<p>Existing generation caches are replayed without new model requests. The read-only reference tensors and the original experiment artifacts must remain at their relative paths. The environment record pins the versions used, including Torch 2.8.0+cpu, Transformers 4.55.0, SQLGlot 30.11.0, SciPy 1.17.1 and Matplotlib 3.11.2.</p>
<p class="small">Primary-source links were opened during this study on November 2, 2026. Sources are linked beside the claims they support. Measurements, failure examples, mathematical bounds and implementation interpretations are this study's own results.</p>
</main></html>'''
(ROOT/'report.html').write_text(content,encoding='utf-8')
print(json.dumps({'report':str(ROOT/'report.html'),'report_bytes':len(content.encode()),'output_count':total,'conditions':len(summary),'schema_matches':sum(s['schema_match'] for s in summary)},indent=2))
