import ast, copy, gzip, hashlib, itertools, json, math, os, platform, random, re, shutil, subprocess, sys, tempfile, threading, time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from IPython.display import display

ROOT = Path.cwd()
DATA, FIG = ROOT/'data', ROOT/'figures'
DATA.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
LIVE = os.environ.get('NB_LIVE') == '1'
if not LIVE:
 def offline_network_guard(*args,**kwargs):raise RuntimeError('Network disabled in notebook replay')
 requests.sessions.Session.request=offline_network_guard
PROFILE = os.environ.get('NB_PROFILE', 'smoke' if LIVE else 'full')
N_BATCH_PER_FAMILY = 30 if PROFILE == 'full' else 1
N_BATCHES_MAX = 4 if PROFILE == 'full' else 1
TARGET_DISAGREEMENTS = 80
WEAK = ['Haiku','Luna','Granite 8B','DeepSeek 763B']
STRONG = ['Opus','Sol']
THIRD = ['Muse','Sonnet']
METHODS = ['alone','reasons','revise','confidence','trust','coin','human']
N_DEV_PER_FAMILY = 6
MAX_WRITER_ASSISTED_ATTEMPTS = 8
MAX_TRANSCRIPTION_CHARS = 2200
MAX_CHUNK_ATTEMPTS = 8
LONG_MESSAGE_WORD_TARGETS = {7:1000, 8:1600, 9:2400, 10:700, 11:1000, 12:1400}
SEED = 3410302026
AUTHORED_ON = '2026-10-30'
MAX_OPENROUTER_USD = 5.00
MAX_NEW_CALLS = 16000
BOOTSTRAPS = 5000
PROTOCOL = 'judge-exam-v1.0'
JUDGES = {
 'Opus': dict(backend='claude', model='claude-opus-5-5'),
 'Sonnet': dict(backend='claude', model='claude-sonnet-5-5'),
 'Haiku': dict(backend='claude', model='claude-haiku-5-5'),
 'Sol': dict(backend='codex', model='gpt-6.1-sol'),
 'Luna': dict(backend='codex', model='gpt-6-luna'),
 'Muse': dict(backend='muse', model='muse-wonder-full-1.0'),
 'Granite 8B': dict(backend='openrouter', model='ibm-granite/granite-4.2-8b-20260831', provider='coreweave/bf16', rate_in=.06, rate_out=.15, reasoning='none', json_mode=True),
 'DeepSeek 763B': dict(backend='openrouter', model='deepseek/deepseek-v4.1-flash-20261017', provider='deepinfra/fp8', rate_in=.098, rate_out=.294, reasoning='low', json_mode=True),
 'Decisions': dict(backend='decisions', model='openai/gpt-6-luna-decisions-20261006', provider='openai', rate_in=.15, rate_out=.60),
}
WRITERS = {
 'Gemma 4B': dict(backend='openrouter',model='google/gemma-3-4b-it',provider='parasail/bf16',rate_in=.04,rate_out=.05),
 'Gemma 27B': dict(backend='openrouter',model='google/gemma-3-27b-it',provider='deepinfra/fp8',rate_in=.08,rate_out=.16),
}
FAMILIES = ['code','worked','instructions','grounded']
CODEX_OPTIONS = ['exec','--skip-git-repo-check','--ephemeral','--ignore-user-config','--sandbox','read-only',
 '--disable','shell_tool','--disable','unified_exec','--disable','apps','--disable','plugins','--disable','multi_agent',
 '--disable','browser_use','--disable','computer_use','--disable','image_generation','--disable','code_mode',
 '--disable','code_mode_host','--disable','shell_snapshot','-c','web_search="disabled"',
 '-c','model_reasoning_effort="medium"','--json']
CLAUDE_OPTIONS = ['-p','--tools','','--safe-mode','--no-session-persistence','--output-format','json','--effort','medium']
MUSE_OPTIONS = ['exec','--preset','empty','--no-session-log','--disable-web-tools','--disable-reminders',
 '--disable-request-user-input','--no-foreign-personal-context','--disable-write','--disable-shell',
 '--reasoning-effort','medium','--max-model-steps','1']
OPTIONS = dict(claude=CLAUDE_OPTIONS,codex=CODEX_OPTIONS,muse=MUSE_OPTIONS)
plt.rcParams.update({'figure.dpi':110,'savefig.dpi':160,'savefig.bbox':'tight','axes.spines.top':False,
 'axes.spines.right':False,'axes.grid':True,'grid.alpha':.16,'axes.axisbelow':True,'axes.titlelocation':'left',
 'font.size':10,'figure.facecolor':'white','axes.prop_cycle':plt.cycler(color=['#315f9c','#ac5832','#34816b','#8654a2'])})
pd.set_option('display.max_colwidth',100)
def canonical(x): return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def digest(x): return hashlib.sha256(canonical(x).encode()).hexdigest()
def filehash(p): return hashlib.sha256(Path(p).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def save(p,x): Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def now(): return datetime.now(timezone.utc).isoformat()
def log(event,**kw):
 if LIVE:
  with (DATA/'run_log.jsonl').open('a',encoding='utf-8') as f: f.write(canonical(dict(at=now(),event=event,**kw))+'\n')
def first_json(s):
 for m in re.finditer(r'\{',s):
  try: return json.JSONDecoder().raw_decode(s[m.start():])[0]
  except ValueError: pass
 raise ValueError('No complete JSON object')
print('Mode:', 'live' if LIVE else 'replay', '| Profile:', PROFILE, '| Batch pairs per family:',N_BATCH_PER_FAMILY)
display(pd.DataFrame(load(DATA/'models.json'))[['name','pinned_version','provider','access','size','precision','settings','date','why_included']])