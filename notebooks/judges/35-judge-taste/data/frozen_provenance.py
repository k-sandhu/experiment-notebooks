import json,re,hashlib,subprocess,collections
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'data';REPO=ROOT.parents[2]
def git(*args):return subprocess.check_output(['git',*args],cwd=REPO).decode('utf-8','replace')
def readl(name):return [json.loads(s) for s in (DATA/name).read_text(encoding='utf-8').splitlines()]
def save(name,x):(DATA/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def writel(name,rows):(DATA/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
commits={};INTRODUCTIONS={}
def meta(sha):
 if sha not in commits:
  text=git('show','-s','--format=%aI%x1f%an%x1f%B',sha);date,author,body=text.split('\x1f',2)
  co=re.findall(r'Co-Authored-By:\s*(.+)',body,re.I)
  branch=INTRODUCTIONS.get(sha,'')
  evidence=body+' '+branch
  vendor='Claude' if re.search('claude|anthropic',evidence,re.I) else ('Codex' if re.search('codex/|codex|openai|gpt-',evidence,re.I) else 'unknown')
  commits[sha]=dict(commit=sha,date=date,commit_author=author,coauthors=co,vendor=vendor,message=body.strip(),introducing_merge=branch)
 return commits[sha]

def blame(rev,path):
 out=git('blame','--line-porcelain',rev,'--',path);rows=[];sha=None
 for line in out.splitlines():
  m=re.match(r'^([0-9a-f]{40}) \d+ \d+',line)
  if m:sha=m[1]
  if line.startswith('\t'):rows.append(dict(text=line[1:],commit=sha))
 return rows

def locate(passage,lines):
 if '\n\n' in passage:
  found=[]
  for piece in passage.split('\n\n'):found.extend(locate(piece,lines))
  return found
 target=re.sub(r'\s+',' ',passage).strip()
 # Paragraph groups can skip blank lines, but cannot skip words.
 normalized='';spans=[]
 for i,line in enumerate(lines):
  text=re.sub(r'\s+',' ',line['text']).strip()
  if text:
   start=len(normalized);normalized+=(' ' if normalized else '')+text;spans.append((start,len(normalized),i))
 pos=normalized.find(target)
 if pos<0:return []
 return [lines[i] for start,end,i in spans if start<pos+len(target) and end>pos]

def run():
 for line in git('log','origin/main','--first-parent','--merges','--reverse','--format=%H%x1f%P%x1f%s').splitlines():
  merge,parents,subject=line.split('\x1f',2);ps=parents.split()
  if len(ps)<2:continue
  for origin in git('rev-list',ps[1],'--not',ps[0]).splitlines():INTRODUCTIONS.setdefault(origin,subject)
 rows=readl('pairs.jsonl');cache={};items=[]
 for r in rows:
  if not r['eligible']:continue
  for side,rev in [('before',r['parent']),('after',r['merge_commit'])]:
   key=(rev,r['path'])
   if key not in cache:cache[key]=blame(*key)
   lines=locate(r[side],cache[key]);counts=collections.Counter(x['commit'] for x in lines)
   assert counts,(r['pair_id'],side)
   authors=[dict(**meta(k),lines=n) for k,n in counts.most_common()]
   vendors={x['vendor'] for x in authors}
   vendor=next(iter(vendors)) if len(vendors)==1 else 'mixed'
   if side+'_file_author' not in r:r[side+'_file_author']=r[side+'_author']
   r[side+'_author']={**authors[0],'vendor':vendor,'blame_commits':authors,
    'attribution':'Git blame of passage lines; model attribution from commit coauthors or introducing branch, not proof of who wrote each token'}
   r[side+'_creation_dates']=sorted({x['date'][:10] for x in authors})
  items.append(dict(pair_id=r['pair_id'],notebook=r['notebook'],before_creation_dates=r['before_creation_dates'],
   after_creation_dates=r['after_creation_dates'],merge_date=r['date'],date_source='git blame original line commits'))
 lookup={r['pair_id']:r for r in rows}
 writel('pairs.jsonl',rows)
 for name in ['train_pairs.jsonl','test_pairs.jsonl','dev_pairs.jsonl']:writel(name,[lookup[r['pair_id']] for r in readl(name)])
 models=[
 dict(name='Claude Opus 5.5',pinned_version='claude-opus-5-5',catalog_permaslug='anthropic/claude-opus-5.5-20260921',provider='Anthropic',access='claude -p',size='not published',precision='not published',effort='medium',training_cutoff='2026-06-30',release_date='2026-09-22',source='https://platform.claude.com/docs/en/models/overview',why='Top Anthropic judge and one-time rubric distiller; accepted text often has Claude coauthor attribution.'),
 dict(name='Claude Haiku 5.5',pinned_version='claude-haiku-5-5',catalog_permaslug='anthropic/claude-haiku-5.5-20261007',provider='Anthropic',access='claude -p',size='not published',precision='not published',effort='medium',training_cutoff='2026-06-30',release_date='2026-10-07',source='https://platform.claude.com/docs/en/models/overview',why='Fast, inexpensive judge from the same vendor as Opus.'),
 dict(name='GPT-6.1 Sol',pinned_version='gpt-6.1-sol',catalog_permaslug='openai/gpt-6.1-sol-20260929',provider='OpenAI',access='codex exec (npm CLI)',size='not published',precision='not published',effort='medium',training_cutoff='2026-04-30',release_date='2026-09-29',source='https://developers.openai.com/api/docs/models/gpt-6.1-sol',why='Cross-vendor top judge; earlier text may have Codex attribution.'),
 dict(name='Qwen3.5-9B',pinned_version='qwen/qwen3.5-9b-20260310',provider='PrimeIntellect BF16 via OpenRouter; fallbacks disabled',access='OpenRouter chat/completions',hugging_face_id='Qwen/Qwen3.5-9B',hugging_face_revision=json.loads((DATA/'qwen_hf.json').read_text())['sha'],size='9B language-model parameters; model card',precision='BF16 (pinned provider)',licence='Apache-2.0',effort='medium',temperature=0,max_tokens=8192,retry_max_tokens=16384,training_cutoff=None,release_date='2026-03-10',source='https://openrouter.ai/api/v1/models',model_card='https://huggingface.co/Qwen/Qwen3.5-9B',why='Small open-weight judge with low per-token cost; independent of the two CLI vendors.')]
 save('models.json',models)
 min_date=min(d for i in items for side in ['before_creation_dates','after_creation_dates'] for d in i[side])
 save('date_provenance.json',dict(recorded_at=datetime.now(timezone.utc).isoformat(),models=models,licence='MIT',repository_licence=git('show','origin/main:LICENSE'),
   filter_applied='Main rewrite merges 2026-10-27 through 2026-10-30; before and after file revisions in October 2026. Eligible passage original-line dates checked after extraction; must be after the latest published cutoff (2026-06-30) and Qwen release proxy (2026-03-10).',
   latest_cutoff='2026-06-30',earliest_passage_line_date=min_date,all_passage_lines_after_cutoff=min_date>'2026-06-30',items=items,
   caveat='Git records when lines entered the repository, not when an unpublished draft was composed. Closed-model cutoff dates are vendor statements; they cannot prove absence from later training updates.'))
 assert min_date>'2026-06-30',min_date
 save('authorship_commits.json',commits)
 print('Blame checked',len(items),'pairs;',len(commits),'origin commits; earliest line',min_date)
 print(collections.Counter((r['before_author']['vendor'],r['after_author']['vendor']) for r in rows if r['eligible']))
if __name__=='__main__':run()
