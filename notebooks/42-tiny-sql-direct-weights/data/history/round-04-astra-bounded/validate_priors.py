"""Report numerical-prior adherence. Never modifies or generates candidate values."""
from pathlib import Path
import argparse,json,math
import numpy as np
HERE=Path(__file__).resolve().parent
def validate(values):
    profile=json.loads((HERE/'parameter_priors.json').read_text(encoding='utf-8'))
    layout=json.loads((HERE.parent/'tensor_layout.json').read_text(encoding='utf-8'))
    violations=[];warnings=[];groups=[]
    if not isinstance(values,list) or len(values)!=2208:
        return {'passes_hard_constraints':False,'violations':['Expected exactly 2208 scalar values.'],'groups':[],'candidate_changed':False}
    try:
        finite=all(type(v) in (int,float) and math.isfinite(v) for v in values)
    except OverflowError:
        finite=False
    if not finite:
        return {'passes_hard_constraints':False,'violations':['All values must be finite JSON numbers.'],'groups':[],'candidate_changed':False}
    flat=np.asarray(values,dtype=np.float64)
    if np.any(np.abs(flat)>2):violations.append('Global scalar bound [-2,2] violated.')
    tensors={e['name']:flat[e['offset']:e['offset']+e['count']].reshape(e['shape']) for e in layout}
    for group in profile['parameter_groups']:
        a=tensors[group['tensor']]
        if group.get('columns'):a=a[:,group['columns'][0]:group['columns'][1]]
        label=group.get('label',group['tensor']);before=len(violations)
        mean=float(a.mean());rms=float(np.sqrt(np.mean(a*a)))
        if a.min()<group['hard_min'] or a.max()>group['hard_max']:violations.append(label+': value range violated.')
        if 'hard_abs_mean_max' in group and abs(mean)>group['hard_abs_mean_max']+1e-12:violations.append(label+': mean too far from zero.')
        if 'hard_mean_min' in group and not group['hard_mean_min']-1e-12<=mean<=group['hard_mean_max']+1e-12:violations.append(label+': gain mean outside allowed range.')
        if 'hard_rms_min' in group and not group['hard_rms_min']-1e-12<=rms<=group['hard_rms_max']+1e-12:violations.append(label+': RMS outside allowed range.')
        detail={'label':label,'kind':group['kind'],'mean':mean,'rms':rms,'min':float(a.min()),'max':float(a.max())}
        if group['kind']=='matrix':
            meaningful=float(np.mean(np.abs(a)>=group['meaningful_magnitude_threshold']-1e-12))
            detail['meaningful_fraction']=meaningful
            if meaningful+1e-12<group['hard_min_meaningful_fraction']:violations.append(label+': fewer than 80% meaningful entries.')
            singular=np.linalg.svd(a,compute_uv=False);rank=int(np.sum(singular>singular[0]*1e-6)) if singular[0]>0 else 0
            detail['rank_relative_1e_6']=rank
            if rank<min(a.shape):warnings.append(label+': reduced numerical rank; this is advisory except for projection.')
        detail['passes_hard_constraints']=len(violations)==before;groups.append(detail)
    p=tensors['projection'];s=np.linalg.svd(p,compute_uv=False)
    rank=int(np.sum(s>s[0]*1e-6)) if s[0]>0 else 0
    condition=float(s[0]/s[-1]) if s[-1]>0 else None
    if rank!=8:violations.append('Projection: numerical column rank must be 8.')
    if condition is None or condition>100:violations.append('Projection: condition number must be <= 100.')
    return {'profile':profile['profile'],'passes_hard_constraints':not violations,'violations':violations,'warnings':warnings,
            'groups':groups,'projection_rank':rank,'projection_condition_number':condition,'candidate_changed':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('weight_json',type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args();payload=json.loads(args.weight_json.read_text(encoding='utf-8'));report=validate(payload.get('weights') if isinstance(payload,dict) else None)
    if args.output:args.output.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'passes_hard_constraints':report['passes_hard_constraints'],'violation_count':len(report['violations']),
                      'first_violations':report['violations'][:10],'candidate_changed':False},indent=2))
    raise SystemExit(0 if report['passes_hard_constraints'] else 2)
