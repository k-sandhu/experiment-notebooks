"""Post-hoc diagnostic of the MLP's measured polygonal approximation, with unchanged weights."""
from pathlib import Path
import json
import numpy as np
ROOT=Path(__file__).resolve().parent
weights=np.load(ROOT.parent/'mlp-rings-388'/'data'/'astra'/'candidate.npz')
angles=np.linspace(0,2*np.pi,3600,endpoint=False)
direction=np.column_stack([np.cos(angles),np.sin(angles)])
rows=[];all_inputs=[];all_expected=[];all_predicted=[];condition_index=[]
for boundary in [.25,.5,.75]:
    for offset in [-1e-5,-1e-6,1e-6,1e-5]:
        x=(boundary+offset)*direction
        expected=np.searchsorted([.25,.5,.75],np.hypot(x[:,0],x[:,1]),side='right')
        h1=np.maximum(0,x@weights['W1'].T+weights['b1'])
        h2=np.maximum(0,h1@weights['W2'].T+weights['b2'])
        predicted=(h2@weights['W3'].T+weights['b3']).argmax(axis=1)
        all_inputs.append(x);all_expected.append(expected);all_predicted.append(predicted);condition_index.append(np.full(len(x),len(rows)))
        rows.append({'boundary':boundary,'offset':offset,'n':len(x),'correct':int((predicted==expected).sum()),'accuracy':float((predicted==expected).mean())})
report={'purpose':'Post-hoc boundary stress test prompted by angular approximation error despite ceiling random-test accuracy. Offsets fixed before this test; no fitting or changes to weights.',
        'angular_points_per_condition':3600,'offsets':[-1e-5,-1e-6,1e-6,1e-5],'rows':rows,
        'total_points':sum(r['n'] for r in rows),'correct':sum(r['correct'] for r in rows)}
(ROOT/'data'/'boundary_stress.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
np.savez_compressed(ROOT/'data'/'boundary_stress_predictions.npz',inputs=np.vstack(all_inputs),expected=np.concatenate(all_expected),
                    predicted=np.concatenate(all_predicted),condition_index=np.concatenate(condition_index))
print(json.dumps(report,indent=2))
