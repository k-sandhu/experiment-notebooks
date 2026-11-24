# Supplementary diagnostic specified after the transport outage was observed.
readable_pairs=[]
def add_readable_pair(a,b,parser,**meta):
 joined=a[['item_id',parser+'_unreadable_type']].merge(b[['item_id',parser+'_unreadable_type']],on='item_id',suffixes=('_a','_b'),validate='one_to_one')
 ids=joined.loc[joined[parser+'_unreadable_type_a'].eq('') & joined[parser+'_unreadable_type_b'].eq(''),'item_id']
 aa=a[a.item_id.isin(ids)];bb=b[b.item_id.isin(ids)]
 result=paired_record(aa,bb,parser,**meta) if len(ids) else dict(meta,parser=parser,n=0,accuracy_a=np.nan,accuracy_b=np.nan,difference_b_minus_a=np.nan,ci_low=np.nan,ci_high=np.nan,gains=0,losses=0,unchanged=0,exact_sign_p=np.nan)
 result.update(full_pair_count=len(joined),excluded_unreadable=len(joined)-len(ids),cohort='both_readable',analysis_status='Post-outage diagnostic; conditioning may change item mix. Primary analysis unchanged.')
 readable_pairs.append(result)
for parser in ['strict','lenient','complete_json']:
 for name in JUDGES:
  original=frame[(frame.judge==name)&(frame.variant=='original')]
  baseline=original[original.method=='exam_prompt']
  for method in METHODS:
   if method!='exam_prompt':add_readable_pair(baseline,original[original.method==method],parser,judge=name,comparison='method_vs_exam',method=method)
  for method in ['free_form','exam_prompt','item_checklist']:
   add_readable_pair(original[original.method==method],frame[(frame.judge==name)&(frame.variant=='polished')&(frame.method==method)],parser,judge=name,comparison='polished_vs_original',method=method)
readable_paired=pd.DataFrame(readable_pairs)
readable_paired.to_csv(OUT/'readable_paired.csv',index=False)
display(readable_paired.query("parser == 'lenient'"))
