"""Prepare a bounded-weight instruction variant. Does not call a model or choose weights."""
from pathlib import Path
import hashlib
import json
import math

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PROFILE='bounded-sql-v1'
def dump(name,data):(HERE/name).write_text(json.dumps(data,indent=2),encoding='utf-8')
def matrix(name,shape,sigma,columns=None,residual=False):
    return {'tensor':name,'shape':shape,'columns':columns,'kind':'matrix','target_mean':0,'target_rms':sigma,
            'hard_min':-2,'hard_max':2,'hard_abs_mean_max':.25*sigma,'hard_rms_min':.5*sigma,'hard_rms_max':2*sigma,
            'meaningful_magnitude_threshold':.05*sigma,'hard_min_meaningful_fraction':.8,
            'scale_basis':'sqrt(2/(fan_in+fan_out))'+(' / sqrt(2*n_layers), n_layers=1' if residual else '')}
specs=[matrix('projection',[50,8],math.sqrt(2/58))]
pos=matrix('transformer.wpe.weight',[64,8],.05)
pos.update(hard_min=-.5,hard_max=.5,hard_abs_mean_max=.02,hard_rms_min=.01,hard_rms_max=.2,
           scale_basis='Experiment-chosen positional-embedding target; broad range, not a trained-model law.')
specs.append(pos)
for label,start in [('Q',0),('K',8),('V',16)]:
    item=matrix('transformer.h.0.attn.c_attn.weight',[8,8],math.sqrt(2/16),columns=[start,start+8])
    item['label']=label;specs.append(item)
specs += [matrix('transformer.h.0.attn.c_proj.weight',[8,8],math.sqrt(2/16)/math.sqrt(2),residual=True),
          matrix('transformer.h.0.mlp.c_fc.weight',[8,56],math.sqrt(2/64)),
          matrix('transformer.h.0.mlp.c_proj.weight',[56,8],math.sqrt(2/64)/math.sqrt(2),residual=True)]
layout=json.loads((ROOT/'tensor_layout.json').read_text(encoding='utf-8'))
for entry in layout:
    name=entry['name']
    if '.ln_' in name and name.endswith('.weight'):
        specs.append({'tensor':name,'shape':entry['shape'],'kind':'layernorm_gain','target_mean':1,
                      'hard_min':.5,'hard_max':2,'hard_mean_min':.8,'hard_mean_max':1.2})
    elif name.endswith('.bias'):
        specs.append({'tensor':name,'shape':entry['shape'],'kind':'bias','target_mean':0,'zero_allowed':True,
                      'hard_min':-.5,'hard_max':.5,'hard_abs_mean_max':.05,'hard_rms_min':0,'hard_rms_max':.1})
assert sum(math.prod(s['shape']) for s in specs)==2208
profile={'profile':PROFILE,'scope':'Only the 2208-parameter SQL transformer. Does not constrain the working MLP.',
         'parameter_count':2208,'global_scalar_bounds':[-2,2],'matrix_mean_convention':'Arithmetic mean within each tensor or Q/K/V block; do not center all parameter types together.',
         'constraints_are':'Experiment-chosen restrictions informed by initialization and numerical-stability priors, not universal statistics of trained LLMs.',
         'parameter_groups':specs,
         'projection_hard_checks':{'rank':8,'max_condition_number':100},
         'advisory_checks':['Prefer useful, distinct feature directions; avoid duplicate/proportional rows or columns and dead attention heads.',
                            'Other learned matrices preferably have healthy numerical rank; rank deficiency is reported as a warning, not rejected automatically.',
                            'Prefer moderate hidden activations and nontrivial attention score differences without relying on extreme saturation.',
                            'Aim for vocabulary-logit standard deviations on an ordinary scale, approximately 0.3 to 5 on representative contexts; this is not a guarantee of calibration.',
                            'Required identifiers and EOS should win by useful margins under correct prefixes; statistical adherence does not replace task accuracy.'],
         'no_tester_repairs':True,'on_violation':'Save and flag the unmodified submission. Adherence and behavioral results remain separate.',
         'sources':[{'url':'https://proceedings.mlr.press/v9/glorot10a.html','supports':'Fan-in/fan-out initialization scale and variance propagation.'},
                    {'url':'https://github.com/huggingface/transformers/blob/v4.55.0/src/transformers/models/gpt2/modeling_gpt2.py','supports':'Zero-mean initialization, zero biases, LayerNorm gains of one, and residual-projection depth scaling.'}],
         'chosen_policy_not_source_requirements':['Hard caps','RMS tolerance factors','80% meaningful-entry minimum','Mean tolerances','Projection condition-number ceiling','Positional scale range']}
dump('parameter_priors.json',profile)
lines=[
    'BOUNDED-WEIGHT SQL EXPERIMENT: PRIORITY NUMERICAL INSTRUCTIONS',
    'These instructions apply to the SQL transformer specified below, with the same 2,208 editable values and frozen vocabulary/embeddings.',
    'This is a fresh complete bounded-weight submission. Earlier sparse/extreme weights are not a template to retain.',
    'These are experiment constraints informed by initialization priors. They are not universal laws for trained language-model weights.',
    'You still have no tools. Return only the complete numeric JSON weight object; do not return code or formulas.',
    '',
    'HARD NUMERICAL CONSTRAINTS',
    'Every editable scalar must be finite and in [-2,2]. The parameter-type constraints below can be tighter.',
    'For each matrix/block, aim for mean 0; enforce the listed mean, RMS and range constraints.',
    'RMS means sqrt(mean(w*w)), computed within the listed group. Near-zero mean makes it close to standard deviation.',
    'Q, K and V are checked separately, not as one combined [8,24] tensor.',
    'At least 80% of entries in EACH matrix/block must have abs(value) at least 5% of its target RMS.',
    'This meaningful-entry requirement also applies to the positional table. Zero biases remain valid.',
    '',
]
for s in specs:
    if s['kind']!='matrix':continue
    label=s.get('label',s['tensor'])
    lines += [f"{label} ({s['tensor']}, shape {s['shape']}, columns {s['columns'] if s['columns'] else 'all'}):",
              f"  Target RMS {s['target_rms']}; allowed RMS [{s['hard_rms_min']}, {s['hard_rms_max']}].",
              f"  Abs(mean) <= {s['hard_abs_mean_max']}; every value in [{s['hard_min']},{s['hard_max']}].",
              f"  At least 80% of entries must have abs(value) >= {s['meaningful_magnitude_threshold']}."]
lines += [
    '',
    'Every LayerNorm gain vector: all entries in [0.5,2.0], mean in [0.8,1.2], target mean 1.',
    'Every bias vector, including LayerNorm biases: all entries in [-0.5,0.5], abs(mean) <= 0.05, RMS <= 0.1; zeros are allowed.',
    'Projection P must have numerical column rank 8 and condition number <= 100.',
    '',
    'ADDITIONAL DESIGN PRIORS',
    'Use the allowed density for functional, distinct features. Do not add decorative tiny filler merely to satisfy a count.',
    'Prefer approximately balanced positive and negative matrix coefficients, healthy feature diversity, and useful contributions from both attention heads.',
    'Do not obtain scale separation through coefficients such as 1e-24 and 1e22, inverse-gain cancellations, or zeroing most of a matrix.',
    'Do not set LayerNorm gains to sqrt(epsilon) to bypass normalization. The architecture and epsilon remain unchanged.',
    'Prefer moderate hidden activations. Avoid a design that depends on exact cancellation of large terms or extreme numerical saturation.',
    'With ordinary temperature 1, logits should have meaningful differences, roughly standard deviations 0.3 to 5 on representative contexts.',
    'That logit scale is advisory, not a probability-calibration guarantee. No external logit rescaling will be supplied.',
    'Required table/column tokens should rank first with useful score margins under the correct prefix; emit EOS when the query is complete.',
    'Plausible statistics are secondary to implementing the task: do not return arbitrary random-looking weights that only meet the statistics.',
    '',
    'TESTER POLICY',
    'The tester separately reports hard-constraint adherence and raw behavioral performance. It may evaluate a noncompliant submission, but will flag it.',
    'It will never clip, rescale, recenter, pad, optimize, or replace any candidate value. You alone choose every weight.',
    'No grammar mask, SQL template, identifier replacement, copying helper, query execution, or training will be used.',
    'Return a complete {"weights":[2208 explicit JSON numbers]} in the original tensor layout. Do not include this explanatory text in your response.',
]
priors='\n'.join(lines)+'\n'
(HERE/'weight_priors.txt').write_text(priors,encoding='utf-8')
previous=ROOT/'round-03-astra'/'attempt-02'
observed=json.loads((previous/'raw_outputs.json').read_text(encoding='utf-8'))['outputs'][:4]
feedback=[
    'OBSERVATIONAL FEEDBACK FROM THE PREVIOUS ASTRA SUBMISSION',
    'The prior 2,208 numbers were loaded unchanged; frozen embeddings, tokenizer, architecture and float64 inference matched the supplied specification.',
    'That submission had 57.1% exactly zero values and nonzero magnitudes from about 2.2e-29 to 1e22.',
    'Projection RMS was about 1.08e-24; final LayerNorm gains were 0.003162277660168379.',
    'All vocabulary logits were bounded in magnitude by about 6.9e-25, making ordinary softmax numerically uniform.',
    'Raw greedy output matched the requested table and columns on 0 of 123 schemas. Standard decoding controls did not repair this.',
    'Under correct query prefixes, expected identifier words were ranked first in only 3 of 368 positions; EOS was never ranked first at the expected stop.',
    'Below are four exact observed examples. The tester offers no proposed numerical weight values.',
]
for item in observed:
    c=item['case'];expected='select '+','.join('"'+col+'"' for col in c['columns'])+' from "'+c['table']+'";'
    feedback += ['',f"Case {c['id']}",'Input: '+item['request']['prompt'],'Observed: '+json.dumps(item['raw_output']),
                 'Required: '+expected+'<EOS>']
feedback='\n'.join(feedback)+'\n'
(HERE/'observational_feedback.txt').write_text(feedback,encoding='utf-8')
base=(ROOT/'generator_prompt.txt').read_text(encoding='utf-8')
base=base.replace('It scores both executable SQL and correct returned columns and rows.','It checks generated text and requested identifiers without executing SQL.')
base=base.replace('Other legal capitalization and whitespace are accepted if the output executes and returns the specified\ncolumns in order. The real table\'s contents are unknown to you; copying constant result values cannot pass.',
                  'Other legal capitalization and whitespace are accepted if the generated SELECT names the supplied\ncolumns in order and the supplied table. No SQL is executed during testing.')
assert 'output executes' not in base and 'scores both executable SQL' not in base
prompt=priors+'\nORIGINAL TASK AND COMPLETE FIXED MODEL SPECIFICATION\n'+base+'\n\n'+feedback+'\nFINAL REMINDER: '+priors
(HERE/'prepared_prompt.txt').write_text(prompt,encoding='utf-8')
schema=json.loads((ROOT/'weights_schema.json').read_text(encoding='utf-8'))
schema['properties']['weights']['items'].update(minimum=-2,maximum=2)
dump('weights_schema.json',schema)
dump('preparation_manifest.json',{'status':'prepared_not_started','profile':PROFILE,'model':'gpt-6-astra','reasoning_effort':'xhigh',
                                 'parameter_count':2208,'frozen_embeddings_unchanged':True,'prompt_bytes':len(prompt.encode()),
                                 'prior_block_sha256':hashlib.sha256(priors.encode()).hexdigest(),
                                 'previous_checkpoint_path':str(previous/'astra_candidate.safetensors'),
                                 'previous_weight_response_path':str(previous/'generator_weights_output.json'),
                                 'feedback_case_ids':[x['case']['id'] for x in observed],
                                 'launch_environment':{'ASTRA_SQL_PREPARED_DIR':str(HERE),'ASTRA_SQL_EFFORT':'xhigh','ASTRA_SQL_KEEP_HISTORY':'1','ASTRA_SQL_ATTEMPT':'1'},
                                 'launcher':str(ROOT/'run_astra_weights.py'),'generation_started':False})
print(json.dumps({'prepared_directory':str(HERE),'prompt_bytes':len(prompt.encode()),'profile':PROFILE,'parameter_groups':len(specs),'model_call_made':False},indent=2))
