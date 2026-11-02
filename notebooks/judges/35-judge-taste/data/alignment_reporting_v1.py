# Exact paragraph-boundary audit added after inspecting the results.
def normalize_alignment_text(text):
 return re.sub(r'\s+',' ',text).strip()

def audit_alignment_pairs():
 candidates=[p for p in read_jsonl('pairs.jsonl') if p['eligible']]
 train_ids={p['pair_id'] for p in read_jsonl('train_pairs.jsonl')}
 test_ids={p['pair_id'] for p in read_jsonl('test_pairs.jsonl')}
 dev_ids={p['pair_id'] for p in read_jsonl('dev_pairs.jsonl')}
 rubric_ids=set(read_json('rubric_metadata.json')['source_ids'])
 assert train_ids.isdisjoint(test_ids)
 assert {p['pair_id'] for p in candidates}==train_ids|test_ids
 sources={(s['merge_commit'],s['path']):s for s in read_json('source_manifest.json')['sources']}
 reviews=read_json('alignment_review_v1.json')['reviews']
 source_cache={};rows=[]
 for pair in candidates:
  identity=(pair['merge_commit'],pair['path'])
  if identity not in source_cache:
   source=sources[identity];texts={};paths={}
   for side in ['before','after']:
    rel=Path('source_snapshots')/pair['merge_commit'][:12]/(pair['path'].replace('/','__')+'.'+side+'.md')
    assert file_hash(DATA/rel)==source[side+'_sha256'],str(rel)
    texts[side]=(DATA/rel).read_text(encoding='utf-8');paths[side]=rel.as_posix()
   source_cache[identity]=(texts,paths)
  texts,paths=source_cache[identity];matches=[];remaining={}
  for side,opposite,kind in [('before','after','kept elsewhere'),('after','before','existed before')]:
   remaining[side]=[]
   for paragraph in re.split(r'\n\s*\n',pair[side]):
    normalized=normalize_alignment_text(paragraph)
    found=(len(normalized)>40 and normalized in normalize_alignment_text(texts[opposite])
           and normalized not in normalize_alignment_text(pair[opposite]))
    if found:
     pattern=r'\s+'.join(re.escape(w) for w in paragraph.split())
     location=re.search(pattern,texts[opposite]);assert location is not None
     matches.append(dict(side=side,flag_type=kind,paragraph=normalized,matched_snapshot=paths[opposite],
      matched_line_start=texts[opposite].count('\n',0,location.start())+1,
      matched_line_end=texts[opposite].count('\n',0,location.end()-1)+1))
    else:remaining[side].append(paragraph)
  flagged=bool(matches);types={m['flag_type'] for m in matches}
  kind='both' if len(types)>1 else next(iter(types)) if types else 'none'
  pid=pair['pair_id'];review=reviews.get(pid,{})
  if flagged:assert review,'Flag requires manual review: '+pid
  residual_equal=normalize_alignment_text('\n\n'.join(remaining['before']))==normalize_alignment_text('\n\n'.join(remaining['after']))
  rows.append(dict(pair_id=pid,split='train' if pid in train_ids else 'test',notebook=pair['notebook'],
   merge_commit=pair['merge_commit'],development_pair=pid in dev_ids,rubric_source_pair=pid in rubric_ids,
   flag=flagged,flag_type=kind,matched_paragraph_count=len(matches),
   matched_paragraph_excerpt=' || '.join(m['paragraph'] for m in matches),
   matched_snapshot=' || '.join(m['matched_snapshot'] for m in matches),
   matches_json=json.dumps(matches,ensure_ascii=False),
   residual_whitespace_identical=residual_equal if flagged else None,
   real_rewrite_apart_from_moved_paragraph=review.get('real_rewrite','not reviewed'),
   review_reason=review.get('reason','Not flagged by the exact check; not manually certified.'),
   review_basis='Manual comparison of frozen pair and matched source paragraphs after results' if flagged else 'Not reviewed'))
 audit=pd.DataFrame(rows).sort_values(['split','pair_id']).reset_index(drop=True)
 assert set(audit[audit.flag].pair_id)==set(reviews)
 audit.to_csv(DATA/'alignment_audit.csv',index=False)
 counts=[]
 for split,g in [('all eligible',audit),('train',audit[audit.split=='train']),('test',audit[audit.split=='test']),
                 ('rubric / example pool',audit[audit.rubric_source_pair])]:
  counts.append(dict(split=split,pairs=len(g),flagged=int(g.flag.sum()),unflagged=int((~g.flag).sum()),
   kept_elsewhere=int((g.flag_type=='kept elsewhere').sum()),existed_before=int((g.flag_type=='existed before').sum()),
   both=int((g.flag_type=='both').sum()),real_rewrite_after_context_removed=int((g.real_rewrite_apart_from_moved_paragraph=='yes').sum()),
   boundary_artifact_only=int((g.real_rewrite_apart_from_moved_paragraph=='no').sum())))
 counts=pd.DataFrame(counts);counts.to_csv(DATA/'alignment_audit_summary.csv',index=False)
 return audit,counts

def alignment_sensitivity(judgments,audit):
 flagged=set(audit[audit.flag].pair_id);clean=judgments[~judgments.pair_id.isin(flagged)].copy()
 records=[]
 for sample,frame in [('All test pairs',judgments),('Clean test pairs',clean)]:
  scores=summarize(frame,['judge','method']).query("parser == 'strict'")
  for judge,g in frame.groupby('judge'):
   per=g.groupby(['pair_id','method']).strict_correct.mean().unstack('method')
   differences={}
   for method in ['M3','M2']:
    delta=per[method]-per['M0'];lo,hi=ci_boot(delta);prefix=method.lower()+'_minus_m0'
    differences.update({prefix:float(delta.mean()),prefix+'_ci_low':lo,prefix+'_ci_high':hi})
   for row in scores[scores.judge==judge].to_dict('records'):
    row.update(sample=sample,source_groups=frame.notebook.nunique(),exploratory_post_results=True,**differences)
    records.append(row)
 sensitivity=pd.DataFrame(records);named_table(sensitivity).to_csv(DATA/'sensitivity_clean_test.csv',index=False)
 clean_scores=sensitivity[sensitivity['sample']=='Clean test pairs']
 best=clean_scores.groupby('method').agreement.mean().sort_values(ascending=False,kind='stable').index[0]
 hard=clean[clean.method==best].assign(wrong=lambda g:g.strict_valid&~g.strict_correct,unreadable=lambda g:~g.strict_valid)
 hard=hard.groupby('pair_id').agg(correct=('strict_correct','sum'),wrong=('wrong','sum'),unreadable=('unreadable','sum'),
  calls=('strict_correct','size'),agreement=('strict_correct','mean')).reset_index()
 hard['method']=best;hard['notebook']=hard.pair_id.map(lambda p:LOOKUP[p]['notebook'])
 named_table(hard.sort_values(['agreement','pair_id'])).to_csv(DATA/'hard_pairs_clean.csv',index=False)
 return sensitivity,clean

def example_alignment_exposure(judgments,audit,draws):
 flagged_train=set(audit[(audit.split=='train')&audit.flag].pair_id)
 flagged_test=set(audit[(audit.split=='test')&audit.flag].pair_id)
 rubric=read_json('rubric_metadata.json');rubric_flagged=sorted(set(rubric['source_ids'])&flagged_train)
 save_json('rubric_alignment_audit.json',dict(source_pairs=len(rubric['source_ids']),flagged_source_pairs=len(rubric_flagged),
  flagged_source_ids=rubric_flagged,all_source_ids=rubric['source_ids'],exploratory_post_results=True,
  note='The frozen rubric and its source pairs are unchanged; all Distilled rubric prompts inherit this source exposure.'))
 rows=[];selected=set(judgments.pair_id)
 for prompt in read_jsonl('test_prompts.jsonl'):
  method=prompt['method'];pid=prompt['pair_id']
  if pid not in selected or method not in ['M2','M3','M5']:continue
  draw_type='retrieved' if method=='M3' else 'random';ids=draws[pid][draw_type];assert len(ids)==8 and len(set(ids))==8
  bad=[i for i in ids if i in flagged_train]
  rows.append(dict(pair_id=pid,method=method,order=prompt['order'],prompt_sha256=prompt['prompt_sha256'],
   draw_type=draw_type,examples=len(ids),flagged_example_count=len(bad),any_flagged_example=bool(bad),
   flagged_example_ids=json.dumps(bad),example_ids=json.dumps(ids),test_pair_flagged=pid in flagged_test,
   judgments_sharing_prompt=len(JUDGES),global_rubric_source_pairs=len(rubric['source_ids']),
   global_rubric_flagged_source_pairs=len(rubric_flagged),exploratory_post_results=True))
 exposure=pd.DataFrame(rows).sort_values(['method','pair_id','order']).reset_index(drop=True)
 named_table(exposure).to_csv(DATA/'flagged_examples_in_prompts.csv',index=False)
 exposure_summary=[]
 for method,g in exposure.groupby('method'):
  exposure_summary.append(dict(method=method,pairs=g.pair_id.nunique(),unique_prompts=len(g),examples_per_prompt=8,
   prompts_with_flagged_example=int(g.any_flagged_example.sum()),share_with_flagged_example=float(g.any_flagged_example.mean()),
   pairs_with_flagged_example=g[g.any_flagged_example].pair_id.nunique(),
   mean_flagged_examples=float(g.flagged_example_count.mean()),minimum_flagged_examples=int(g.flagged_example_count.min()),
   maximum_flagged_examples=int(g.flagged_example_count.max()),exploratory_post_results=True))
 exposure_summary=pd.DataFrame(exposure_summary)
 named_table(exposure_summary).to_csv(DATA/'flagged_example_summary.csv',index=False)
 joined=judgments[judgments.method.isin(['M2','M3','M5'])].merge(
  exposure[['pair_id','method','order','any_flagged_example']],on=['pair_id','method','order'],validate='many_to_one')
 joined['example_exposure']=np.where(joined.any_flagged_example,'At least one flagged example','Zero flagged examples')
 results=[]
 for sample,frame in [('All test pairs',joined),('Clean test pairs',joined[~joined.pair_id.isin(flagged_test)])]:
  scores=summarize(frame,['judge','method','example_exposure']).query("parser == 'strict'").copy()
  scores['sample']=sample;scores['exploratory_post_results']=True;results.append(scores)
 outcomes=pd.concat(results,ignore_index=True)
 named_table(outcomes).to_csv(DATA/'agreement_by_flagged_examples.csv',index=False)
 return exposure,exposure_summary,outcomes

def run_alignment_reporting(judgments,draws):
 audit,counts=audit_alignment_pairs()
 sensitivity,clean=alignment_sensitivity(judgments,audit)
 exposure,exposure_summary,exposure_agreement=example_alignment_exposure(judgments,audit,draws)
 print(f'Post-result alignment audit: {int(audit.flag.sum())}/{len(audit)} eligible pairs flagged; {clean.pair_id.nunique()} unflagged test pairs.')
 return audit,counts,sensitivity,exposure,exposure_summary,exposure_agreement
