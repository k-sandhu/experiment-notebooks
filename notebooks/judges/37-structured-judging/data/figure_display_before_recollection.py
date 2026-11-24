# Display-only correction after visual inspection.
def make_accuracy_display(tables):
 summary=tables['summary'];s=summary[(summary.variant=='original')&(summary.parser=='lenient')]
 fig,axes=plt.subplots(1,3,figsize=(15,5.2),sharey=True)
 for ax,name in zip(axes,JUDGES):
  g=s[s.judge==name].set_index('method').reindex(METHODS);x=np.arange(len(g));ax.bar(x,g.accuracy,color=COLORS[name],hatch='//',edgecolor='white');ax.errorbar(x,g.accuracy,yerr=[g.accuracy-g.ci_low,g.ci_high-g.accuracy],fmt='o',color='black',capsize=3,markersize=3)
  for xx,(_,r) in zip(x,g.iterrows()):ax.text(xx,r.ci_high+.02,f'{r.correct:.0f}/{r.n:.0f}',ha='center',fontsize=8)
  ax.set(title=name,xticks=x,xticklabels=[('Own requirements\n(instructions only)' if m=='own_requirements' else METHOD_LABEL[m]) for m in METHODS],ylim=(0,1.15));ax.tick_params(axis='x',rotation=48)
 ranges='; '.join(f'{name} {s[s.judge==name].accuracy.min():.0%}-{s[s.judge==name].accuracy.max():.0%}' for name in JUDGES)
 axes[0].set_ylabel('Accuracy (unreadable and undecided count as failures)');fig.suptitle('Sol rate-limit failures confound instruction comparisons; see readable-only results',x=.06,ha='left');fig.tight_layout();fig.savefig(FIG/'accuracy.png');plt.close(fig)

make_accuracy_display(tables)
