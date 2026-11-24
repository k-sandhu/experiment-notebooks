# Display-only amendment: distinguish readable errors from unreadable replies.
def worked_examples_readable(frame,checklists,quality):
 items={i['item_id']:i for i in source_items()+source_items('dev')};original=frame[frame.variant=='original'];examples=[]
 pivot=original.pivot(index=['item_id','judge'],columns='method',values='lenient_correct')
 wrong_pivot=original.pivot(index=['item_id','judge'],columns='method',values='lenient_wrong')
 candidates={
  'checklist_caught_error':pivot[wrong_pivot.free_form&pivot.item_checklist],
  'structure_made_worse':pivot[pivot.free_form&wrong_pivot.item_checklist],
  'rubric_made_worse':pivot[pivot.free_form&wrong_pivot.general_rubric],
  'typical_success':pivot[pivot.free_form&pivot.exam_prompt&pivot.item_checklist],
  'typical_failure':pivot[wrong_pivot.free_form&wrong_pivot.item_checklist],
 }
 for purpose,g in candidates.items():
  for family in FAMILIES:
   matches=[(item_id,name) for item_id,name in g.index if items[item_id]['family']==family]
   if matches:
    item_id,name=matches[0];examples.append(dict(purpose=purpose,item_id=item_id,judge=name,matching_item_judge_cases=len(g),matching_family_item_judge_cases=len(matches)))
 missed=[r for r in quality if r['category']=='absent']
 for r in missed[:3]:examples.append(dict(purpose='checklist_missed_decisive_check',item_id=r['item_id'],quality=r,matching_items=len(missed)))
 unreadable=frame[frame.lenient_unreadable_type!='']
 for _,r in unreadable.head(6).iterrows():examples.append(dict(purpose='unreadable',item_id=r.item_id,judge=r.judge,method=r.method,unreadable_type=r.lenient_unreadable_type,matching_judgments=len(unreadable)))
 strict_only=frame[(frame.strict_unreadable_type!='')&(frame.lenient_unreadable_type=='')]
 for _,r in strict_only.head(4).iterrows():examples.append(dict(purpose='strict_failure_lenient_recovery',item_id=r.item_id,judge=r.judge,method=r.method,matching_judgments=len(strict_only)))
 if len(frame):examples.insert(0,dict(purpose='end_to_end',item_id=frame.iloc[0].item_id,judge=frame.iloc[0].judge))
 for e in examples:
  item_id=e['item_id'];e['item']=items[item_id];e['checklist']=checklists[item_id];e['quality']=next(r for r in quality if r['item_id']==item_id)
  observed=frame[frame.item_id==item_id]
  if e.get('judge'):observed=observed[observed.judge==e['judge']]
  e['observed']=json.loads(observed.to_json(orient='records'));keys=set(k for r in e['observed'] for k in r['raw_reply_cache_keys']);e['raw_replies']={k:CACHE[k]['response'] for k in sorted(keys)}
  focused=[r for r in e['observed'] if r['method']==e.get('method') and (r['lenient_unreadable_type'] if e['purpose']=='unreadable' else r['strict_unreadable_type'])]
  e['selected_raw_replies']={k:CACHE[k]['response'] for r in focused for k in r['raw_reply_cache_keys']}
 save(OUT/'worked_examples.json',examples)
 selected=[];seen=set()
 for purpose in ['end_to_end','checklist_caught_error','structure_made_worse','checklist_missed_decisive_check','typical_failure','unreadable','typical_success']:
  choices=[e for e in examples if e['purpose']==purpose and e['item_id'] not in seen]
  if choices:selected.append(choices[0]);seen.add(choices[0]['item_id'])
  if len(selected)==4:break
 import textwrap
 fig,axes=plt.subplots(max(len(selected),1),1,figsize=(12,max(3.1*len(selected),3.5)))
 for ax,e in zip(np.atleast_1d(axes),selected):
  ax.axis('off');i=e['item'];bad='B' if i['better']=='A' else 'A';good=i['candidates'][i['better']]['check'];wrong=i['candidates'][bad]['check'];family=i['family']
  if family=='instructions':
   detail=f"Required: {i['rules']['min_words']}-{i['rules']['max_words']} regex-counted words. Better answer: {good['word_count']} words. Worse answer: {wrong['word_count']} words. Failed checks: "+', '.join(k for k,v in wrong['checks'].items() if not v)+'.'
  elif family=='code':
   failed=[t for t,p in zip(i['hidden_tests'],wrong.get('checks',[])) if not p];test=failed[0] if failed else {}
   detail=f"Hidden checks: better {good.get('passed')}/{good.get('total')}; worse {wrong.get('passed')}/{wrong.get('total')}. First failing input: {canonical(test.get('input'))}. Expected: {canonical(test.get('expected'))}."
  elif family=='worked':
   detail='Exact final value: '+i['exact_answer']+'. Worse final value: '+str(numeric_answer(i['candidates'][bad]['text']))+'.'
  else:
   m=i.get('ground_mutation',{});detail=f"Correct net charge: {i['exact_answer']}. Worse charge: {numeric_answer(i['candidates'][bad]['text'])}. Selected {m.get('field')}: correct entry {m.get('old_entry')} = {m.get('old_value')}; worse entry {m.get('new_entry')} = {m.get('new_value')}."
  observed=[r for r in e['observed'] if r['variant']=='original' and r['method'] in ['free_form','exam_prompt','item_checklist']];name=e.get('judge') or observed[0]['judge'];observed=[r for r in observed if r['judge']==name]
  title=e['purpose'].replace('_',' ')+' | '+e['item_id']+' | '+name
  expected=observed[0]['expected_winner'];title+=f' | expected displayed {expected}'
  line='; '.join(METHOD_LABEL[r['method']]+': '+str(r['lenient_winner'])+' ('+('correct' if r['lenient_correct'] else ('unreadable: '+r['lenient_unreadable_type']) if r['lenient_unreadable_type'] else 'undecided' if r['lenient_undecided'] else 'wrong')+')' for r in observed)
  ax.text(0,1,title,transform=ax.transAxes,va='top',fontsize=10,fontweight='bold');ax.text(0,.72,textwrap.fill(detail,110),transform=ax.transAxes,va='top',fontsize=10);ax.text(0,.16,textwrap.fill(line,110),transform=ax.transAxes,va='top',fontsize=10)
 fig.tight_layout();fig.savefig(FIG/'worked_cases.png');plt.close(fig);return examples


examples=worked_examples_readable(frame,checklists,quality)
