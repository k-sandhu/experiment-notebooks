def plot_results(judgments,summaries,by_type,baseline,comparisons,orders,reasons):
 import textwrap
 markers=['o','s','^','D']
 labels=[textwrap.fill(METHOD_NAMES[m],18) for m in METHODS]
 def ticks(ax,methods=METHODS):
  ax.set_xticks(range(len(methods)),[textwrap.fill(METHOD_NAMES[m],18) for m in methods],rotation=25,ha='right')
  ax.set_xlabel('Guidance method')
 def save(fig,name):
  fig.tight_layout();fig.savefig(FIG/name);plt.close(fig)
 fig,axes=plt.subplots(2,2,figsize=(13,10),sharey=True)
 for ax,judge in zip(axes.flat,JUDGES):
  for parser,marker,ls in [('strict','o','-'),('lenient','x','--')]:
   g=summaries[(summaries.judge==judge)&(summaries.parser==parser)].set_index('method').loc[METHODS]
   ax.errorbar(range(6),100*g.agreement,yerr=[100*(g.agreement-g.ci_low),100*(g.ci_high-g.agreement)],fmt=marker,ls=ls,capsize=3,label=parser.capitalize())
  ax.axhline(50,color='#777',ls=':',label='50% reference')
  ax.set(title=judge,ylim=(0,105),ylabel='Agreement with accepted text (%)');ticks(ax)
 axes.flat[0].legend(fontsize=10,loc='lower left')
 fig.suptitle('Similar past choices raised Opus 5.5 and GPT-6.1 Sol agreement;\nHaiku and Qwen stayed near chance',fontsize=15)
 save(fig,'agreement.png')
 fig,ax=plt.subplots(figsize=(12,6))
 g=comparisons[(comparisons.parser=='strict')&(comparisons.reference=='M0')]
 for i,(judge,marker) in enumerate(zip(JUDGES,markers)):
  s=g[g.judge==judge].set_index('method').loc[METHODS[1:]];x=np.arange(5)+(i-1.5)*.12
  ax.errorbar(x,100*s.delta,yerr=[100*(s.delta-s.ci_low),100*(s.ci_high-s.delta)],fmt=marker,capsize=3,label=judge)
 ax.axhline(0,color='black',ls='--');ticks(ax,METHODS[1:])
 ax.set(ylabel='Change versus No guidance (percentage points)',title='Clear gains from past choices were confined to Opus 5.5 and Sol')
 ax.legend(fontsize=10);save(fig,'paired_changes.png')
 fig,axes=plt.subplots(2,2,figsize=(11,9),sharey=True)
 for ax,judge in zip(axes.flat,JUDGES):
  for method,marker,ls in [('M0','o','-'),('M3','s','--')]:
   g=length_agreement[(length_agreement.judge==judge)&(length_agreement.method==method)].set_index('length_direction').reindex(['shorter','longer'])
   ax.errorbar([0,1],100*g.agreement,yerr=[100*(g.agreement-g.ci_low),100*(g.ci_high-g.agreement)],fmt=marker,ls=ls,capsize=4,label=METHOD_NAMES[method])
  ax.plot([0,1],[100,0],marker='X',ls=':',color='#555',label='Pick the shorter version')
  counts=text_features.length_direction.value_counts()
  ax.set(title=judge,xticks=[0,1],xticklabels=[f'Accepted shorter\n({counts.get("shorter",0)} pairs)',f'Accepted longer\n({counts.get("longer",0)} pairs)'],
   ylim=(-5,105),ylabel='Strict agreement, both orders (%)',xlabel='Accepted version relative to earlier version')
 axes.flat[0].legend(fontsize=9,loc='lower left')
 fig.suptitle('All four judges agreed more often when the accepted passage was longer\nunder No guidance and 8 similar past choices',fontsize=14)
 save(fig,'length_direction.png')
 fig,axes=plt.subplots(1,2,figsize=(14,6))
 for judge,marker in zip(JUDGES,markers):
  g=orders[(orders.judge==judge)&(orders.parser=='strict')].set_index('method').loc[METHODS]
  axes[0].plot(range(6),100*g.consistency_on_readable,marker=marker,label=judge)
  axes[1].plot(range(6),100*(1-g.choose_A_rate),marker=marker,label=judge)
 axes[0].set(title='Opus 5.5 and Sol usually kept their choice\nwhen the order flipped',ylabel='Same text in both readable orders (%)',ylim=(0,105))
 axes[1].axhline(50,color='#777',ls=':')
 axes[1].set(title='Haiku and Qwen favoured\nthe second version shown',ylabel='Second version chosen among readable replies (%)',ylim=(0,100))
 for ax in axes:ticks(ax)
 axes[0].legend(fontsize=9,loc='lower left');save(fig,'order_bias.png')
 reason_mean=reasons.groupby('method')[list(REASON_CATEGORIES)].mean().reindex(METHODS)
 fig,ax=plt.subplots(figsize=(12,5));im=ax.imshow(reason_mean.T*100,vmin=0,vmax=100,cmap='Blues',aspect='auto')
 for i in range(len(REASON_CATEGORIES)):
  for j in range(6):
   value=100*reason_mean.iloc[j,i];ax.text(j,i,f'{value:.0f}%',ha='center',va='center',color='white' if value>65 else 'black')
 ax.set(yticks=range(len(REASON_CATEGORIES)),yticklabels=[x.replace('_',' ') for x in REASON_CATEGORIES],title='Judges most often cited plain wording and structure');ticks(ax)
 fig.colorbar(im,ax=ax,label='Readable reasons mentioning category (%)');save(fig,'reason_categories.png')
 fig,axes=plt.subplots(1,2,figsize=(14,6))
 for judge,marker in zip(JUDGES,markers):
  g=method_cost[method_cost.judge==judge].set_index('method').loc[METHODS]
  axes[0].plot(range(6),g.mean_prompt_tokens,marker=marker,label=judge)
  axes[1].plot(range(6),g.dollars_per_100_judgments,marker=marker,label=judge)
 axes[0].set(ylabel='Mean prompt tokens per judgment')
 axes[1].set(ylabel='List-price dollars per 100 judgments\n(USD, known cost; log scale)',yscale='log')
 for ax in axes:ticks(ax)
 axes[0].legend(fontsize=9);axes[1].legend(fontsize=9)
 fig.suptitle('Examples lengthened prompts; Opus had the highest cost per judgment',fontsize=15)
 save(fig,'method_time.png')
 example_titles={
  'p35_013acf7a7ae6e42b':'Opus and Sol chose the accepted passage in both orders',
  'p35_247121cf9fd8fe1e':'Opus and Haiku chose the accepted passage in both orders',
  'p35_423116db367e7c1c':'All three CLI judges preferred the earlier caption in both orders'}
 for ex in read_json('worked_examples.json')[:3]:
  p=ex['pair'];g=judgments[(judgments.pair_id==p['pair_id'])&(judgments.method==ex['best_method'])]
  counts=g.groupby('judge').strict_correct.sum()
  texts=['\n\n'.join(textwrap.fill(re.sub(r'\s+',' ',s),56) for s in p[side].split('\n\n')) for side in ['before','after']]
  lines=max(t.count('\n')+1 for t in texts);height=max(2.2,lines*.235+1.05)
  fig=plt.figure(figsize=(14,height))
  axes=[fig.add_axes([left,.37/height,.465,(height-1.05)/height]) for left in [.015,.52]]
  for ax,side,text in zip(axes,['before','after'],texts):
   ax.text(0,1,text,ha='left',va='top',fontsize=14,transform=ax.transAxes)
   ax.set_title('Earlier version' if side=='before' else 'Accepted version',fontsize=14);ax.axis('off')
  fig.suptitle(p['pair_id']+': '+example_titles.get(p['pair_id'],f'Accepted passage chosen in both orders by {int((counts==2).sum())} of four judges'),fontsize=14)
  fig.text(.05,.01,'8 similar past choices; accepted choices out of 2 orders: '+'; '.join(f'{j}: {int(counts.get(j,0))}/2' for j in JUDGES),fontsize=11)
  fig.savefig(FIG/('example_'+p['pair_id']+'.png'));plt.close(fig)
 print('Saved nine reporting figures; display cells appear beside their sections.')
