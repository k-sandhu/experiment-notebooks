"""Full 20-topic CLI-only collection. Saved conversations are never regenerated."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import re
import subprocess
import threading
import time

import smoke_study as s

ROOT = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
MAIN = ROOT / 'data' / 'main'
PROTOCOL = 'main-v1-high-conversation-short-followups'
N_TOPICS = 20
N_POSTS = 5
MODELS = s.MODELS.copy()
MAX_NEW_CALLS = 5  # The authorised complete run explicitly permits 400; ordinary defaults stay small.
N_WORKERS = 4
SEED = 20261101
SOURCES = [
('01-kimi','2026-10-23','model release','https://simonwillison.net/2026/Oct/23/kimi-k31-pro/'),
('02-tb-screening','2026-10-23','healthcare','https://research.google/blog/bringing-foundational-models-to-the-front-lines-of-tb-screening/'),
('03-gemini-carbon','2026-10-28','model release','https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-carbon/'),
('04-nemotron-speech','2026-10-28','speech','https://huggingface.co/blog/nvidia/nemotron-transcribe-granary'),
('05-enterprise-roi','2026-10-28','enterprise adoption','https://techcrunch.com/2026/10/28/anthropic-just-launched-tools-to-show-companies-what-their-ai-spending-is-buying/'),
('06-protostar','2026-10-29','scientific data','https://huggingface.co/blog/announcing-project-protostar'),
('07-apple-local-models','2026-10-29','on-device development','https://huggingface.co/blog/anydecisionmodel'),
('08-model-spec','2026-10-29','model behaviour','https://openai.com/index/updated-model-spec/'),
('09-misalignment-monitoring','2026-10-29','safety research','https://openai.com/index/how-we-detect-frontier-model-misalignment/'),
('10-reddit-login','2026-10-29','publishing and search','https://techcrunch.com/2026/10/29/as-search-traffic-dries-up-reddit-announces-its-shifting-to-a-logged-in-experience/'),
('11-thrive-adt','2026-10-29','acquisition','https://techcrunch.com/2026/10/29/openai-backed-thrive-holdings-acquires-adt/'),
('12-dartmouth-writing','2026-10-29','writing and accountability','https://abcnews.com/Technology/wireStory/dartmouth-provost-resigns-accusations-artificial-intelligence-writing-137686123'),
('13-cursor-extension','2026-10-30','software security','https://thehackernews.com/2026/10/official-claude-code-vs-code-extension.html'),
('14-seti','2026-10-30','scientific applications','https://blogs.nvidia.com/blog/ai-joins-the-search-for-extraterrestrial-signals/'),
('15-doordash-agents','2026-10-30','agent adoption','https://techcrunch.com/2026/10/30/doordash-said-its-only-received-several-hundred-orders-from-ai-agents/'),
('16-zest','2026-10-30','consumer applications','https://techcrunch.com/2026/10/30/zests-new-ai-agent-finds-restaurants-and-books-reservations-over-text/'),
('17-orbital-compute','2026-10-30','infrastructure','https://techcrunch.com/2026/10/30/googles-first-data-center-satellite-is-online-and-writing-poetry/'),
('18-wikimedia','2026-10-30','copyright','https://wikimediafoundation.org/news/2026/10/30/wikimedia-foundation-amicus-brief-new-york-times-v-open-ai-case/'),
('19-training-preferences','2026-10-30','publisher controls','https://openai.com/index/helping-websites-express-ai-training-preferences/'),
('20-community-safety','2026-10-30','consumer safeguards','https://openai.com/index/community-safety-report-and-new-protections-for-teens/'),
]


def extract_article(html, url):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.h1.get_text(' ', strip=True) if soup.h1 else soup.title.get_text(' ',strip=True)
    selectors = {
        'huggingface.co': '.blog-content > div.relative.overflow-clip',
        'techcrunch.com': '.entry-content',
        'thehackernews.com': '.post-body',
        'blogs.nvidia.com': '.entry-content',
        'simonwillison.net': '.entry',
        'abcnews.com': '.FITT_Article_main__body',
    }
    body, selector = None, None
    for domain, sel in selectors.items():
        if domain in url:
            body = soup.select_one(sel); selector = sel; break
    if body is None:
        for sel in ['[itemprop="articleBody"]', '.article-body', '.article__body',
                    '.article-content', '.article-body__content', 'article', 'main']:
            candidate=soup.select_one(sel)
            if candidate and len(candidate.get_text(' ',strip=True))>500:
                body,selector=candidate,sel;break
    assert body is not None, f'No article body: {url}'
    body=copy.copy(body)
    if 'simonwillison.net' in url:
        title=body.find('a').get_text(' ',strip=True)
    for tag in body.select('script,style,nav,aside,footer,form,button,.SVELTE_HYDRATER,.entry-footer,.newsletter-signup,.ad-unit,.related-posts,.share-buttons,.MobileContentPromo,.taboola,[aria-hidden="true"],.sr-only,.visually-hidden'):
        tag.decompose()
    if 'openai.com' in url:
        # Main includes navigation and related stories; start at headline and stop at author/related.
        h1=body.find('h1')
        elements=[];started=h1 is None
        for el in body.find_all(['h1','h2','h3','p','li','pre','blockquote','table']):
            if el is h1: started=True;continue
            if not started:continue
            if el.get_text(' ',strip=True) in ['Author','Keep reading']:break
            if el.find_parent(['li','pre','blockquote','table']) is not None:continue
            elements.append(el.get_text(' ',strip=True))
        text='\n\n'.join(x for x in elements if x)
    else:
        # Keep inline links inside their paragraphs; isolate block boundaries only.
        elements=[];h1=body.find('h1');started=h1 is None
        for el in body.find_all(['h1','h2','h3','p','li','pre','blockquote','table','figcaption']):
            if el is h1:started=True;continue
            if not started or el.find_parent(['li','pre','blockquote','table']):continue
            value=el.get_text(' ',strip=True) if el.name!='pre' else el.get_text('',strip=False).strip()
            if value in ['Recent articles','Monthly briefing','Read more:']:break
            if 'Found this article interesting?' in value:break
            if value in ['Popular Reads','Quick links','Posted in:','Share','SHARE']:continue
            if el.name in ['h2','h3'] and value.lower() in ['labels','related articles']:break
            elements.append(value)
        text='\n\n'.join(x for x in elements if x)
    # Only explicit non-article tail widgets, not measured article paragraphs.
    if 'simonwillison.net' in url:
        text=re.split(r'\n(?:Recent articles|Monthly briefing)\n',text)[0]
    if 'openai.com' in url:
        text=re.sub(r'(?:\n\n(?:Alignment|Policies and Procedures|2026))+$','',text)
    if 'research.google' in url:
        text=re.sub(r'(?:\n\n(?:Generative AI|Health & Bioscience|\u00d7))+$','',text)
    return title,text.strip(),selector


def prepare():
    import requests
    existing=MAIN/'articles.json'
    if existing.exists():
        articles=s.load(existing)
        for article in articles:
            path=ROOT/article['local_input']
            assert path.exists() and s.sha(path.read_text(encoding='utf-8'))==article['text_sha256']
        return articles
    input_root=ROOT/'data/local_inputs/main'; input_root.mkdir(parents=True,exist_ok=True)
    def fetch(source):
        item,date,category,url=source
        response=requests.get(url,timeout=60);response.raise_for_status()
        title,body,selector=extract_article(response.content,url)
        article=f'{title}\nPublished {date}\n\n{body}\n'
        assert len(s.words(body))>=100,(item,'Body too short',len(body))
        (input_root/f'{item}.txt').write_text(article,encoding='utf-8')
        return {'item_id':item,'publication_date':date,'event_date_note':
                {'12-dartmouth-writing':'Departure announced October 28.',
                 '13-cursor-extension':'Malicious distribution October 29.',
                 '16-zest':'Feature introduced October 29.',
                 '17-orbital-compute':'First model prompts sent during the publication week.'}.get(item,'Announcement/update reported on publication date.'),
                'category':category,'url':url,'resolved_url':response.url,'title':title,
                'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),
                'text_sha256':s.sha(article),'html_sha256':hashlib.sha256(response.content).hexdigest(),
                'words':len(s.words(article)),'characters':len(article),'selector':selector,
                'local_input':(input_root/f'{item}.txt').relative_to(ROOT).as_posix(),
                'redistribution':'Publisher retains rights; full input local/git-ignored; public URL and hashes retained.'}
    articles=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        tasks={pool.submit(fetch,source):source[0] for source in SOURCES}
        for task in as_completed(tasks):
            article=task.result();articles.append(article)
            print('SOURCE',article['item_id'],article['words'],article['selector'],flush=True)
    articles.sort(key=lambda a:a['item_id'])
    ids=[a['item_id'] for a in articles];random.Random(SEED).shuffle(ids)
    discovery=set(ids[:10])
    for a in articles:a['split']='discovery' if a['item_id'] in discovery else 'confirmation'
    s.save(existing,articles)
    return articles


def preregister():
    articles=prepare()
    path=MAIN/'preregistration.json'
    design={'protocol':PROTOCOL,'models':MODELS,'effort':'high','topics':N_TOPICS,
        'posts_per_conversation':N_POSTS,'planned_posts':N_TOPICS*N_POSTS*len(MODELS),
        'initial_prompt_template':s.PROMPT_TEMPLATE,'followup':s.FOLLOWUP_PROMPT,
        'article_manifest_sha256':s.sha(s.canonical(articles)),
        'lexicon_sha256':s.sha((ROOT/'data/prose_lexicon.json').read_text(encoding='utf-8')),
        'scheduling':'One worker per model; four model workers in parallel. Within each article/model block five turns sequential, one explicit conversation ID. Model-specific article order shuffled with fixed seed.',
        'discovery_rule':'2-8 word sequences, exact normalised tokens, outside source; at least 5/50 discovery posts across at least 3/10 discovery articles; confirm on at least 5/50 posts across at least 3/10 held-out articles. All other patterns exploratory.',
        'phrase_counts':'Posts containing phrase, occurrences, per 1000 words, distinct articles and zones; source occurrence flags. Fixed inventory includes zeroes.',
        'uncertainty':'95% percentile intervals from article-cluster bootstrap, 2000 draws; do not treat five sequential turns as independent topics.',
        'quality':'No gold post, engagement outcome or human judge ratings. Report readability/protocol outcomes separately from descriptive writing habits.',
        'smoke':'40 smoke outputs and all diagnostics retained separately, excluded from main 400. Mistral Large 4 smoke topic replaced by community safeguards announcement before main generation.',
        'failures':'No content retries, no substitutions and no quality-based regeneration. Stop an affected conversation after unreadable result; keep all raw evidence. Continue independent blocks. Interrupted starts require reconciliation before retry.',
        'retention':'Raw stdout/stderr streamed to disk before launch so interruptions can be reconciled. No secrets logged.',
        'cache':'Same context/CLI options within block; short followups only; cumulative Codex token counters and Claude cost counters differenced within session. Missing counters remain null.',
        'cost':'400-call cap, Claude $1 per invocation limit, CLI list-cost equivalents reported; no enforceable Codex dollar cap. Prior planning estimate US$10-40, not invoice; no paid judges.'}
    if path.exists():
        previous=s.load(path); assert all(previous[k]==v for k,v in design.items()),'Design changed after registration'
    else:
        s.save(path,{'registered_at_utc':datetime.now(timezone.utc).isoformat(),**design})
    return articles


def corrected(parsed, model, previous_usage, previous_cost):
    parsed=copy.deepcopy(parsed)
    if model.startswith('gpt'):
        native=parsed['raw_usage'];delta={k:v-previous_usage.get(k,0) for k,v in native.items() if isinstance(v,int)}
        assert all(v>=0 for v in delta.values()),'Session usage moved backward'
        parsed['raw_session_usage']=native;parsed['per_turn_usage']=delta
        for field,key in [('input_total','input_tokens'),('cache_read_tokens','cached_input_tokens'),
                          ('cache_write_tokens','cache_write_input_tokens'),('output_tokens','output_tokens')]:
            parsed[field]=delta.get(key)
        total,reads,writes=[parsed[k] for k in ['input_total','cache_read_tokens','cache_write_tokens']]
        parsed['uncached_input_tokens']=total-reads-writes if all(isinstance(v,int) for v in [total,reads,writes]) else None
        parsed['cache_read_fraction']=reads/total if isinstance(reads,int) and total else None
        parsed['usage_scope']='Codex native cumulative session usage differenced per turn'
    else:
        total=parsed.get('reported_session_cost_usd')
        parsed['reported_cost_usd']=total-previous_cost if total is not None and previous_cost is not None else None
        parsed['usage_scope']='Claude per-invocation token usage; cumulative session cost differenced'
    return parsed


def collect(max_new=MAX_NEW_CALLS):
    articles=preregister();lock=threading.Lock();counter={'new':0};events=[]
    cli_versions={name:subprocess.run([s.shutil.which(name+'.cmd') or s.shutil.which(name),'--version'],capture_output=True,text=True).stdout.strip() for name in ['codex','claude']}
    s.save(MAIN/'cli_versions.json',cli_versions)
    # Existing smoke verifies exact options. A model's five-turn block must retain a constant cwd.
    isolation=s.isolation_dir()
    # Keep immutable shared CLI context files from being rewritten by parallel workers.
    s.isolation_dir=lambda: isolation
    def worker(model):
        schedule=articles.copy();random.Random(SEED+MODELS.index(model)).shuffle(schedule)
        for article in schedule:
            folder=MAIN/'responses'/article['item_id']/model;folder.mkdir(parents=True,exist_ok=True)
            session=None;previous_usage={};previous_cost=0.0
            article_text=(ROOT/article['local_input']).read_text(encoding='utf-8')
            assert s.sha(article_text)==article['text_sha256']
            for turn in range(1,N_POSTS+1):
                stem=folder/f'{turn:02d}';record_path=stem.with_suffix('.json')
                prompt=s.PROMPT_TEMPLATE.format(article=article_text) if turn==1 else s.FOLLOWUP_PROMPT
                cmd=s.command(model,conversation=True,session_id=session)
                request={'protocol':PROTOCOL,'item_id':article['item_id'],'model':model,'turn':turn,
                    'effort':'high','source_sha256':article['text_sha256'],'prompt_sha256':s.sha(prompt),
                    'prompt_kind':'initial_article' if turn==1 else 'followup_only','command':cmd,
                    'prior_session_id':session,'lexicon_sha256':s.load(MAIN/'preregistration.json')['lexicon_sha256']}
                if record_path.exists():
                    saved=s.load(record_path)
                    assert saved['request_sha256']==s.sha(s.canonical(request)),'Saved request fingerprint differs'
                    if saved['status']!='ok':break
                    session=saved['session_id'];previous_usage=saved['raw_usage']
                    previous_cost=saved.get('reported_session_cost_usd');continue
                if stem.with_suffix('.started.json').exists():
                    with lock:events.append({'model':model,'article':article['item_id'],'error':'Unresolved started request; do not regenerate'})
                    break
                with lock:
                    if counter['new']>=max_new:raise RuntimeError('New generation cap reached')
                    counter['new']+=1
                started=datetime.now(timezone.utc).isoformat();tick=time.monotonic()
                s.save(stem.with_suffix('.started.json'),{'request':request,'started_at':started,'status':'started'})
                print(f"START {model} {article['item_id']} {turn}",flush=True)
                timed_out=False
                with stem.with_suffix('.jsonl').open('w',encoding='utf-8') as out,stem.with_suffix('.stderr.txt').open('w',encoding='utf-8') as err:
                    child=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=out,stderr=err,
                        cwd=s.isolation_dir(),env=s.clean_env(),text=True,encoding='utf-8',errors='replace',
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name=='nt' else 0)
                    try:child.communicate(prompt,timeout=s.TIMEOUT_SECONDS)
                    except subprocess.TimeoutExpired:
                        timed_out=True
                        if os.name=='nt':subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True,timeout=20)
                        else:child.kill()
                        child.wait(timeout=20)
                raw=stem.with_suffix('.jsonl').read_text(encoding='utf-8')
                parsed=corrected(s.parse_result(model,raw),model,previous_usage,previous_cost)
                status='ok' if child.returncode==0 and parsed['completed'] and parsed['text'] and not timed_out else 'unreadable_or_failed'
                if parsed['tool_events']:status='tool_protocol_violation'
                if any(cat.get('tools') or cat.get('mcp_servers') or cat.get('skills') for cat in parsed['catalogues']):status='catalogue_protocol_violation'
                if session is not None and parsed['session_id']!=session:status='session_protocol_violation'
                parsed.update({'status':status,'requested_model':model,'item_id':article['item_id'],
                    'turn':turn,'replicate':turn,'split':article['split'],'request':request,
                    'request_sha256':s.sha(s.canonical(request)),'started_at':started,
                    'seconds':time.monotonic()-tick,'exit_code':child.returncode,'timeout':timed_out,'local_replay':False})
                s.save(record_path,parsed);stem.with_suffix('.started.json').unlink()
                print(f"DONE {model} {article['item_id']} {turn} {status} input={parsed['input_total']} cached={parsed['cache_read_tokens']} seconds={parsed['seconds']:.1f}",flush=True)
                if status!='ok':
                    with lock:events.append({'model':model,'article':article['item_id'],'turn':turn,'status':status})
                    break
                session=parsed['session_id'];previous_usage=parsed['raw_usage'];previous_cost=parsed.get('reported_session_cost_usd')
    with ThreadPoolExecutor(max_workers=N_WORKERS) as pool:
        futures={pool.submit(worker,model):model for model in MODELS}
        for future in as_completed(futures):
            try:future.result()
            except Exception as exc:
                events.append({'model':futures[future],'exception':repr(exc)})
                print('WORKER ERROR',futures[future],repr(exc),flush=True)
    s.save(MAIN/'collection_events.json',events)
    print('COLLECTION RETURNED',counter,'events',events,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','register','collect'])
    parser.add_argument('--max-new',type=int,default=MAX_NEW_CALLS);args=parser.parse_args()
    if args.mode=='prepare':prepare()
    elif args.mode=='register':preregister()
    else:collect(args.max_new)
