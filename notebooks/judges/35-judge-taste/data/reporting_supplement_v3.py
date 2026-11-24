# Reporting intervals do not change judgments, parsers, prompts or agreement scores.
consistency_intervals=orders.copy()
bounds=[wilson(int(r.consistent),int(r.both_readable)) for r in consistency_intervals.itertuples()]
consistency_intervals['consistency_ci_low']=[x[0] for x in bounds]
consistency_intervals['consistency_ci_high']=[x[1] for x in bounds]
consistency_intervals.to_csv(DATA/'order_consistency_intervals.csv',index=False)
reason_intervals=[]
for (judge,method),g in reasons.groupby(['judge','method']):
 for category in REASON_CATEGORIES:
  by_item=g.groupby('pair_id')[category].agg(['sum','count']).to_numpy()
  rng=np.random.default_rng(SEED);ix=rng.integers(0,len(by_item),size=(BOOTSTRAPS,len(by_item)));z=by_item[ix].sum(axis=1)
  lo,hi=np.quantile(z[:,0]/z[:,1],[.025,.975])
  reason_intervals.append(dict(judge=judge,method=method,category=category,pairs=len(by_item),readable_calls=len(g),
                               coded_calls=int(g[category].sum()),share=float(g[category].mean()),ci_low=lo,ci_high=hi))
pd.DataFrame(reason_intervals).to_csv(DATA/'reason_category_intervals.csv',index=False)
ranking=summaries.copy()
ranking['agreement_rank']=ranking.groupby(['judge','parser']).agreement.rank(ascending=False,method='min')
ranking['readable_rank']=ranking.groupby(['judge','parser']).readable_agreement.rank(ascending=False,method='min')
ranking[['judge','method','parser','agreement','readable_agreement','agreement_rank','readable_rank']].to_csv(DATA/'parser_ranking.csv',index=False)
both_outcomes=summaries[['judge','method','parser','pairs','right_both','both_readable']].copy()
both_outcomes['unreadable_pairs']=both_outcomes.pairs-both_outcomes.both_readable
both_outcomes['wrong_pairs']=both_outcomes.both_readable-both_outcomes.right_both
assert (both_outcomes.right_both+both_outcomes.unreadable_pairs+both_outcomes.wrong_pairs==both_outcomes.pairs).all()
both_outcomes.to_csv(DATA/'both_order_outcomes.csv',index=False)
sample=[]
for (judge,failure),g in judgments[~judgments.strict_valid].groupby(['judge','strict_failure']):
 r=g.iloc[0];rec=CACHE[r.key]
 sample.append(dict(pair_id=r.pair_id,judge=judge,method=r.method,order=r.order,strict_failure=failure,
                    lenient_valid=bool(r.lenient_valid),lenient_correct=bool(r.lenient_correct),raw_reply=r.raw_reply,
                    key=r.key,attempts=[{k:a.get(k) for k in ['max_tokens','finish_reason','error','latency_s','reported_usd']} for a in rec['attempts']]))
save_json('unreadable_examples_by_type.json',sample)
print('Supplementary reporting intervals and parser rankings saved; frozen scores unchanged.')
