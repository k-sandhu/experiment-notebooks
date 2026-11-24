# Nonfinal transport overhead is separate from final-reply resources.
def transport_resource_tables():
 usage=pd.read_csv(OUT/'request_usage.csv')
 usage.groupby(['model','purpose','disposition'],dropna=False).agg(attempts=('key','size'),estimated_list_usd=('cli_estimated_list_usd','sum'),seconds=('seconds','sum')).reset_index().to_csv(OUT/'transport_attempt_resources.csv',index=False)
 resources=pd.read_csv(OUT/'resources.csv')
 overhead=[];inverse={spec['model']:name for name,spec in JUDGES.items()}
 for row in NONFINAL:
  req=row['request'];parts=req.get('purpose','').split(':')
  if req['model'] not in inverse or len(parts)<3 or parts[0]!='test':continue
  overhead.append(dict(judge=inverse[req['model']],method=parts[1],variant=parts[2],attempts=1,seconds=row['response'].get('latency_s',0),list_usd=float(cli_estimate(row)[0] or 0)))
 if overhead:
  grouped=pd.DataFrame(overhead).groupby(['judge','method','variant']).agg(nonfinal_attempts=('attempts','sum'),nonfinal_seconds=('seconds','sum'),nonfinal_list_usd=('list_usd','sum')).reset_index()
  resources=resources.merge(grouped,on=['judge','method','variant'],how='left')
 for column in ['nonfinal_attempts','nonfinal_seconds','nonfinal_list_usd']:
  if column not in resources:resources[column]=0
  resources[column]=resources[column].fillna(0)
 resources['calls_including_nonfinal_per_item']=resources.calls_per_item+resources.nonfinal_attempts/resources.n
 resources['judge_seconds_including_nonfinal_per_item']=resources.judge_seconds_per_item+resources.nonfinal_seconds/resources.n
 resources['list_usd_including_nonfinal_per_item']=resources.list_usd_per_item+resources.nonfinal_list_usd/resources.n
 resources.to_csv(OUT/'resources_with_transport_overhead.csv',index=False)
 return resources

transport_resources=transport_resource_tables()
