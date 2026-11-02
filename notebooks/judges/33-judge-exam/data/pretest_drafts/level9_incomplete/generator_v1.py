def hard_audit_overlay(r,level):
 modulus=r.choice([7,11,13]);phase=r.randrange(modulus);seed=r.randrange(modulus);factor=r.choice([3,5])
 desc=(f'Before the main rule, perform this audit scan in ORIGINAL zero-based order. For an integer row its weight is that integer. For a log-string row its weight is the signed integer between pipes. For a list row its weight is the sum of integer fields excluding booleans plus the lengths of all string fields. Start state at {seed}. Keep a row if (state + weight + original_index) modulo {modulus} is not {phase}, or if it is the last original row. After deciding, update state for EVERY row, including omitted rows: reset to {seed} if its weight is zero; otherwise set state to ({factor}*state + weight) modulo {modulus}. Finally rotate the kept list LEFT by final_state modulo kept_length; empty stays empty. Then apply the following main rule: ')
 source=f'''
_core_solve=solve
def solve(rows):
 state={seed}
 kept=[]
 for i,row in enumerate(rows):
  if type(row) is int: weight=row
  elif isinstance(row,str): weight=int(row.split('|')[1])
  else: weight=sum(v for v in row if type(v) is int)+sum(len(v) for v in row if isinstance(v,str))
  if (state+weight+i)%{modulus}!={phase} or i==len(rows)-1: kept.append(row)
  state={seed} if weight==0 else ({factor}*state+weight)%{modulus}
 if kept:
  shift=state%len(kept)
  kept=kept[shift:]+kept[:shift]
 return _core_solve(kept)
'''
 return desc,source,dict(modulus=modulus,phase=phase,seed=seed,factor=factor)

def hard_worked_tail(task,steps,x,r,level):
 steps=steps+[f'Base result before further adjustments: {x}.']
 adjustments=[];correct=[];wrong=[];old=x;bad=x;n_adjustments=7+2*(level-4);slip_index=n_adjustments-3;delta=Fraction(r.choice([-1,1]) if level>=7 else 1,10000)
 for j in range(n_adjustments):
  pct=r.randint(3,19);fee=r.randint(3,27);kind='discount after adding' if j%2==0 else 'surcharge before subtracting'
  if j%2==0:
   old=(old+fee)*(1-Fraction(pct,100));bad=(bad+fee)*(1-Fraction(pct,100))
   operation=f'add {fee} credits, then discount the whole amount by {pct}%'
  else:
   old=old*(1+Fraction(pct,100))-fee;bad=bad*(1+Fraction(pct,100))-fee
   operation=f'apply a {pct}% surcharge, then subtract {fee} credits'
  if j==slip_index:
   if level>=8:delta=Fraction(delta.numerator*10**(len(str(abs(old.numerator)))//2),old.denominator)
   bad+=delta
  adjustments.append(f'Adjustment {j+1}: {operation}.')
  correct.append(f'Amount after adjustment {j+1}: {old}.')
  wrong.append(f'Amount after adjustment {j+1}: {bad}.')
 task+=' After computing that result, apply these further settlement adjustments IN ORDER, with no rounding:\n'+'\n'.join(adjustments)
 solve_task=task
 task+='\nShow intermediate steps, with one line for each follow-on stage in the form Amount after adjustment <n>: <exact value>. End with Final answer: <reduced fraction, or integer if its denominator is one>.'
 reference='\n'.join(steps+correct)+f'\nFinal answer: {old}'
 mutation='\n'.join(steps+wrong)+f'\nFinal answer: {bad}'
 replacements=[[a,b] for a,b in zip(correct,wrong) if a!=b]+[[f'Final answer: {old}',f'Final answer: {bad}']]
 return dict(task=task,solve_task=solve_task,specification=task,exact_answer=str(old),reference=reference,mutation=mutation,carried_slip=dict(adjustment_index=slip_index+1,delta=str(delta),mechanism='middle_numerator_digit' if level>=8 else 'fixed_absolute_slip',replacements=replacements),adjustments=adjustments)

def hard_instruction_body(required,r,level):
 clauses=[
  "The well-tested plan isn't ready for a final sign-off until the team's review is complete.",
  "Please re-check the hand-written notes and keep the follow-up record beside the sample tray.",
  "A careful cross-check can prevent an out-of-date copy from reaching the next review group.",
  "The co-owner's brief message should explain why the pre-approved materials remain on the shelf.",
  "Each team member can read the plain-language summary before choosing an after-lunch meeting slot.",
  "We shouldn't replace the working copy with a draft whose check-in notes haven't been reviewed.",
  "An up-to-date list will help the day-shift staff prepare for the next hand-over meeting.",
  "The re-usable folders belong beside the front-desk register while the meeting room is closed.",
  "A short pause gives the note-taker time to compare the room's layout with the written plan.",
  "This week's follow-through depends on a clear statement from the review team's co-ordinator.",
  "Leave the blue-green label on the sample box so that the evening crew can find it.",
  "An easy-to-read note can describe the changes without repeating every step in yesterday's message.",
  "We can ask the group's point-person to gather the left-over papers after the final check.",
  "The back-up record belongs in the shared folder rather than the personal note-book on the desk.",
  "A well-timed reminder gives everyone a chance to re-read the agreement before the hand-off.",
  "Please keep the meeting's pre-work separate from the notes that still need a second check.",
 ]
 if level>=7:
  chosen=[];target=LONG_MESSAGE_WORD_TARGETS[level]
  while len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",' '.join(chosen)))<target:
   block=clauses.copy();r.shuffle(block)
   for clause in block:
    chosen.append(clause)
    if len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",' '.join(chosen)))>=target:break
  return 'The '+required+' sample remains on the review table. '+' '.join(chosen)
 r.shuffle(clauses);n=min(len(clauses),8+2*(level-4)+r.randrange(3))
 return 'The '+required+' sample remains on the review table. '+' '.join(clauses[:n])

def grounded_hard_spec(k,r,level):
 entities=['Marlow East','Marlow West','Marley East','Marlow Annex'];target=entities[k%4];cutoff='2026-09-30'
 events=[];seq=r.randint(100,199)
 def event(entity,field,value,day,signed=True,future=False):
  nonlocal seq
  seq+=1;e=dict(id=f'A-{seq}',site=entity,service='filter replacement',field=field,value=value,effective=f'2026-09-{day:02d}' if not future else '2026-10-01',signed=signed,revision=seq)
  events.append(e);return e
 for entity in entities:
  for field in ['rate','units','credit']:
   start=r.randint(200,850) if field=='rate' else r.randint(12,31) if field=='units' else r.randint(8,39)
   days=[2,13,24];r.shuffle(days)
   for j,day in enumerate(days):event(entity,field,start+j*(r.randint(3,9) if field=='rate' else 2),day)
 # Withdrawal is a separate signed notice, not a warning attached to its target entry.
 target_rates=[e for e in events if e['site']==target and e['field']=='rate'];withdrawn=max(target_rates,key=lambda e:(e['effective'],e['revision']))
 withdrawal=dict(id=f'W-{seq+1}',target_id=withdrawn['id'],signed=True,effective='2026-09-29')
 proposal=event(target,'rate',withdrawn['value']+7,28,signed=False)
 future=event(target,'units',r.randint(32,39),30,future=True)
 def applicable(entity,field):
  rows=[e for e in events if e['site']==entity and e['field']==field and e['signed'] and e['effective']<=cutoff and e['id']!=withdrawal['target_id']]
  return max(rows,key=lambda e:(e['effective'],e['revision']))
 current={f:applicable(target,f) for f in ['rate','units','credit']};rate=current['rate']['value'];units=current['units']['value'];credit=current['credit']['value'];exact=units*rate-credit
 old_units=sorted([e for e in events if e['site']==target and e['field']=='units' and e['signed'] and e['effective']<=cutoff],key=lambda e:(e['effective'],e['revision']))[-2]
 neighbor=applicable(entities[(k+1)%4],'credit')
 alternatives=dict(withdrawn_rate=units*withdrawn['value']-credit,superseded_units=old_units['value']*rate-credit,neighbor_credit=units*rate-neighbor['value'],unsigned_rate=units*proposal['value']-credit)
 alternatives={key:value for key,value in alternatives.items() if value!=exact};dtype=list(alternatives)[k%len(alternatives)];wrong=alternatives[dtype]
 choices={'withdrawn_rate':('rate',withdrawn),'superseded_units':('units',old_units),'neighbor_credit':('credit',neighbor),'unsigned_rate':('rate',proposal)}
 field,bad_event=choices[dtype];bad_fields=copy.deepcopy(current);bad_fields[field]=bad_event
 def justification(fields):
  u,rr,c=fields['units'],fields['rate'],fields['credit']
  return f'Use {u["id"]} for {u["value"]} eligible units, {rr["id"]} for the {rr["value"]}-credit unit rate, and {c["id"]} for the {c["value"]}-credit service credit, giving {u["value"]} * {rr["value"]} - {c["value"]}.'
 intro=(f'Fictional contract register, review date {cutoff}. Rates and credits use integer credits. For each exact site, service and field separately, take the SIGNED amendment with the latest effective date on or before review; break effective-date ties by the larger revision. Signature dates also must be on or before review. Unsigned proposals and future-effective entries do not apply. A signed withdrawal effective on or before review removes only the named amendment, so the next applicable version of that field remains in force. Compute net charge as eligible units times unit rate minus service credit. Fields not named in an entry do not change. All documents below are fictional.')
 paragraphs=[]
 for e in events:
  field_label={'rate':'unit rate','units':'eligible units','credit':'service credit'}[e['field']]
  signature='SIGNED on 2026-09-27' if e['signed'] else 'UNSIGNED proposal'
  p=(f'Entry {e["id"]}; revision {e["revision"]}; {signature}; effective {e["effective"]}. Site {e["site"]}; service {e["service"]}; field {field_label}; replacement value {e["value"]}. Procurement keeps this version with the service papers. Dispatch uses a separate scheduling copy. The registrar retains original and revised documents. No other field changes.')
  paragraphs.append(p)
 paragraphs.append(f'Notice {withdrawal["id"]}; SIGNED on 2026-09-29; effective 2026-09-29. Withdraw entry {withdrawal["target_id"]} in full. This withdrawal names only that entry and has no effect on other amendments, other sites, or other services. The original document remains in the register for audit; its continued physical presence does not restore its authority. The registrar recorded the notice with the same contract file.')
 r.shuffle(paragraphs);source=intro+'\n\n'+'\n\n'.join(paragraphs)
 # The register is compact enough to keep all generated amendments, not sampled to a word target.
 assert 1500<=len(source.split())<=2500,len(source.split())
 question=f'At review date {cutoff}, what is the net filter replacement charge for {target}? Use this exact justification form with the selected IDs and integer values: Use <units ID> for <units> eligible units, <rate ID> for the <rate>-credit unit rate, and <credit ID> for the <credit>-credit service credit, giving <units> * <rate> - <credit>. Then end Final answer: <integer>.'
 ref=justification(current)+f'\nFinal answer: {exact}'
 bad=justification(bad_fields)+f'\nFinal answer: {wrong}'
 return dict(task=source+'\n\nQUESTION: '+question,source=source,specification=question,exact_answer=str(exact),reference=ref,mutation=bad,distractor_type=dtype,distractor_answers={a:str(b) for a,b in alternatives.items()},distractor_fields={key:dict(field=choices[key][0],event=choices[key][1]) for key in alternatives},ground_mutation=dict(field=field,old_value=current[field]['value'],new_value=bad_event['value'],old_entry=current[field]['id'],new_entry=bad_event['id'],wrong_answer=str(wrong)),source_events=events,withdrawals=[withdrawal],oracle_fields=current,template_id=f'grounded_hard_{k%4:02d}',source_words=len(source.split()))

def rng_for(split,family,index,level=1): return random.Random(int(digest([SEED,split,family,index,level])[:16],16))
def code_spec(k,r,level):
 a=r.randint(3,9); b=r.randint(11,19)
 templates=[]
 templates.append((f'Aggregate rows [key, amount, void]. Ignore void rows and amounts whose absolute value is below {a}; sum signed amounts by key. Return sorted [key,total] lists, dropping zero totals.',
  f"def solve(rows):\n d={{}}\n for key,v,void in rows:\n  if not void and abs(v)>={a}: d[key]=d.get(key,0)+v\n return [[k,v] for k,v in sorted(d.items()) if v!=0]",(f'abs(v)>={a}',f'abs(v)>{a}'),
  lambda: [[r.choice(['a','b','c']),r.choice([-b,-a,-a+1,0,a-1,a,b]),r.random()<.15] for _ in range(r.randint(0,12))]))
 templates.append((f'Rows [start,end] are integer half-open intervals. Discard empty or reversed intervals. Merge overlapping intervals, but do not merge intervals that only touch. Return sorted merged lists.',
  'def solve(rows):\n out=[]\n for s,e in sorted(rows):\n  if s>=e: continue\n  if out and s<out[-1][1]: out[-1][1]=max(out[-1][1],e)\n  else: out.append([s,e])\n return out',('s<out[-1][1]','s<=out[-1][1]'),
  lambda: [[x,x+r.randint(-1,6)] for x in [r.randint(0,20) for _ in range(r.randint(0,10))]]))
 templates.append((f'Rows are nonnegative integer quantities. Each order independently costs {a} cents per unit for its first {b} units and {a-1} thereafter. Cap each order at {a*b+13} cents before adding the orders. Return integer cents.',
  f'def solve(rows):\n return sum(min({a*b+13},min(q,{b})*{a}+max(0,q-{b})*{a-1}) for q in rows)',
  (f'min(q,{b})*{a}+max(0,q-{b})*{a-1}',f'min(q,{b})*{a}+max(0,q-{b})*{a}'),lambda:[r.randint(0,b+8) for _ in range(r.randint(0,8))]))
 templates.append((f'Parse log rows "key|integer|status". Keys contain letters only. Status is OK or VOID. Ignore VOID; for each key keep the LAST OK value, even if zero or negative. Return sorted [key,value] lists.',
  "def solve(rows):\n d={}\n for row in rows:\n  k,v,s=row.split('|')\n  if s=='OK': d[k]=int(v)\n return [[k,v] for k,v in sorted(d.items())]",("if s=='OK':","if s=='OK' and int(v):"),
  lambda:[f"{r.choice(['a','b','c'])}|{r.choice([0,0,-a,b])}|{r.choice(['OK','OK','VOID'])}" for _ in range(r.randint(0,10))]))
 templates.append((f'Rows [day, lifetime] use integer days; day zero is Monday. An item expires at day+lifetime. Move that expiry forward past Saturday/Sunday (remainders 5,6). Return the expiry days in input order.',
  'def solve(rows):\n out=[]\n for d,n in rows:\n  x=d+n\n  while x%7 in (5,6): x+=1\n  out.append(x)\n return out',('while x%7 in (5,6):','while x%7 in (4,5):'),lambda:[[r.randint(0,30),r.randint(0,15)] for _ in range(r.randint(0,8))]))
 templates.append((f'Rows [group,score,timestamp,name]. Choose highest score in each group, then EARLIEST timestamp, then lexicographically GREATEST name. Return [group,name] sorted by group. Duplicates allowed.',
  'def solve(rows):\n d={}\n for g,s,t,n in rows:\n  rank=(s,-t,n)\n  if g not in d or rank>d[g][0]: d[g]=(rank,n)\n return [[g,v[1]] for g,v in sorted(d.items())]',('rank=(s,-t,n)','rank=(s,t,n)'),
  lambda:[[r.choice(['a','b']),r.randint(0,3),r.randint(0,3),r.choice(['amy','bea','cal'])] for _ in range(r.randint(0,12))]))
 templates.append((f'Rows [kind,value] update a running balance starting at zero. add increases it, reset replaces it. After EACH row clamp balance to [-{b},{b}]. Return every resulting balance.',
  f"def solve(rows):\n x=0; out=[]\n for kind,v in rows:\n  x=v if kind=='reset' else x+v\n  x=max(-{b},min({b},x))\n  out.append(x)\n return out",(f'max(-{b},min({b},x))',f'max(0,min({b},x))'),lambda:[[r.choice(['add','add','reset']),r.randint(-b-5,b+5)] for _ in range(r.randint(0,10))]))
 templates.append((f'Rows are [capacity,request] with nonnegative integers. Process sequentially, with a starting shared budget of {b}. Each allocation is min(capacity,request,remaining budget). Return allocations; never replenish budget.',
  f'def solve(rows):\n left={b}; out=[]\n for cap,req in rows:\n  v=min(cap,req,left);out.append(v);left-=v\n return out',('v=min(cap,req,left)','v=min(cap,req,max(1,left))'),lambda:[[r.randint(0,9),r.randint(0,9)] for _ in range(r.randint(0,12))]))
 templates.append((f'Rows [expiry,quantity] describe lots. Today is day {b}. Include a lot only if expiry is STRICTLY later than today. Return total quantity and the earliest eligible expiry as [quantity,expiry], using null expiry if none.',
  f'def solve(rows):\n good=[(e,q) for e,q in rows if e>{b}]\n return [sum(q for e,q in good),min((e for e,q in good),default=None)]',(f'e>{b}',f'e>={b}'),lambda:[[r.choice([b-1,b,b+1,b+4]),r.randint(0,9)] for _ in range(r.randint(0,9))]))
 templates.append((f'Rows are integer event times. Sort and deduplicate them. A new session begins only when the gap is GREATER than {a}. Return sessions as [first,last,count]. Empty input returns [].',
  f'def solve(rows):\n out=[]\n for t in sorted(set(rows)):\n  if out and t-out[-1][1]<={a}: out[-1][1]=t;out[-1][2]+=1\n  else:out.append([t,t,1])\n return out',(f't-out[-1][1]<={a}',f't-out[-1][1]<{a}'),lambda:[r.randint(0,30) for _ in range(r.randint(0,15))]))
 templates.append((f'Rows [price,discount] are nonnegative integer cents. For each row apply discount capped at {a} cents, then floor the resulting price at zero. Return total payable cents.',
  f'def solve(rows):\n return sum(max(0,p-min(d,{a})) for p,d in rows)',(f'max(0,p-min(d,{a}))',f'max(0,p-d)'),lambda:[[r.randint(0,15),r.randint(0,12)] for _ in range(r.randint(0,8))]))
 templates.append((f'Rows [day,is_blackout] are proposed days. Exclude blackout rows and days divisible by {a}. Return the earliest {b%4+2} DISTINCT eligible days sorted; fewer if unavailable.',
  f'def solve(rows):\n return sorted({{d for d,black in rows if not black and d%{a}!=0}})[:{b%4+2}]',(f'd%{a}!=0',f'd%{a}==0'),lambda:[[r.randint(0,25),r.random()<.2] for _ in range(r.randint(0,15))]))
 desc,source,mutation,draw=templates[k]
 audit_config=None
 if level>=4:
  extra,overlay,audit_config=hard_audit_overlay(r,level);source+=overlay;desc=extra+desc
 elif level>=2:
  period=r.randint(3,5);phase=r.randrange(period);shift=r.randint(1,3)
  overlay=(f'\n_core_solve=solve\ndef solve(rows):\n filtered=[row for i,row in enumerate(rows) if i%{period}!={phase} or i==len(rows)-1]\n'
   f' if filtered:\n  shift={shift}%len(filtered)\n  filtered=filtered[shift:]+filtered[:shift]\n return _core_solve(filtered)')
  source+=overlay
  desc=(f'First apply an audit filter to the ORIGINAL input positions, indexed from zero: omit positions whose index modulo {period} equals {phase}, except always retain the last input position. '
   f'Rotate the retained rows LEFT by {shift} positions modulo the retained length (empty stays empty). Apply the following rules to that transformed list: '+desc)
 ns={};exec(source,ns)
 bad=source.replace(*mutation)
 badns={};exec(bad,badns)
 pools={True:[],False:[]};seen=set()
 nfail=8 if level==1 else 2
 for _ in range(20000):
  inp=draw();key=canonical(inp)
  if key in seen:continue
  seen.add(key);expected=ns['solve'](copy.deepcopy(inp));same=expected==badns['solve'](copy.deepcopy(inp))
  pools[same].append(dict(input=inp,expected=expected))
  if len(pools[True])>=64-nfail and len(pools[False])>=nfail:break
 assert len(pools[True])>=64-nfail and len(pools[False])>=nfail,k
 tests=pools[True][:64-nfail]+pools[False][:nfail];r.shuffle(tests)
 task='Write Python 3 function solve(rows). '+desc+'\nReturn the requested value, without printing. Inputs follow the types specified. Do not mutate the input. Standard library is allowed.'
 if level>=4:task=task.rsplit('Standard library is allowed.',1)[0]+'The execution environment permits built-ins and these standard-library modules: math, decimal, fractions, collections, itertools, functools, datetime, calendar, re, statistics, bisect, heapq, operator, string, typing, copy, json, ast, dataclasses, numbers and unicodedata. No file/network I/O is needed.'
 if level>=7:source=ast.unparse(ast.parse(source));bad=ast.unparse(ast.parse(bad))
 return dict(task=task,specification=desc,reference=source,mutation=bad,hidden_tests=tests,template_id=f'code_{k:02d}',audit_config=audit_config)
def run_trusted(source,inp):
 ns={};exec(source,ns);return ns['solve'](copy.deepcopy(inp))

def code_check(source,tests):
 try:
  ast.parse(source)
 except (SyntaxError,TypeError): return dict(readable=False,passed=0,total=len(tests),error='syntax')
 # Isolated cwd; no API credentials, no user site, restricted imports, one process per candidate.
 runner="""import json,sys,builtins,types
request=json.load(sys.stdin)
real_import=builtins.__import__
allowed={'math','decimal','fractions','collections','itertools','functools','datetime','calendar','re','statistics','bisect','heapq','operator','string','typing','copy','json','ast','dataclasses','numbers','unicodedata'}
def guarded(name,*a,**kw):
 if name.split('.')[0] not in allowed: raise ImportError('blocked import')
 return real_import(name,*a,**kw)
b=dict(vars(builtins));b['__import__']=guarded
for k in ['open','input','eval','exec','compile','breakpoint']:b.pop(k,None)
module=types.ModuleType('candidate');module.__dict__['__builtins__']=b;sys.modules['candidate']=module;ns=module.__dict__
try:
 exec(request['source'],ns)
 results=[];runtime_errors=0
 for t in request['tests']:
  try:
   before=json.dumps(t['input'],sort_keys=True)
   value=ns['solve'](t['input'])
   results.append(value==t['expected'] and before==json.dumps(t['input'],sort_keys=True))
  except Exception: results.append(False);runtime_errors+=1
 print(json.dumps({'readable':True,'passed':sum(results),'total':len(results),'checks':results,'runtime_errors':runtime_errors,'error':''}))
except Exception as e: print(json.dumps({'readable':False,'passed':0,'total':len(request['tests']),'error':type(e).__name__}))
"""
 try:
  with tempfile.TemporaryDirectory(prefix='nb33_code_') as tmp:
   env={'SYSTEMROOT':os.environ.get('SYSTEMROOT','C:\\Windows'),'NO_COLOR':'1'}
   p=subprocess.run([sys.executable,'-I','-c',runner],input=json.dumps(dict(source=source,tests=tests)),capture_output=True,text=True,encoding='utf-8',cwd=tmp,env=env,timeout=4)
  return json.loads(p.stdout)
 except subprocess.TimeoutExpired: return dict(readable=False,passed=0,total=len(tests),error='timeout')
 except (ValueError,OSError): return dict(readable=False,passed=0,total=len(tests),error='subprocess')

def numeric_answer(text):
 lines=re.findall(r'Final answer:\s*([^\n]*)',text,re.I)
 if not lines:return None
 m=re.fullmatch(r'([-+]?\d[\d,]*(?:\.\d+)?(?:/\d+)?)(?:\s+(?:credits?|litres?|units?|cents))?\.?',lines[-1].strip(),re.I)
 if not m:return None
 try:return Fraction(m.group(1).replace(',',''))
 except (ValueError,ZeroDivisionError):return None
def worked_spec(k,r,level):
 n=r.randint(1700,9700);a=r.randint(11,23);b=r.randint(27,49);c=r.randint(3,9)
 if k==0:
  stages={1:4,2:7,3:10}.get(level,7)
  rates=[Fraction(r.randint(3,17),100) for _ in range(stages)]
  x=Fraction(n);steps=[f'Starting charge is {n}.']
  for i,p in enumerate(rates):x=x*(1-p)+c;steps.append(f'After stage {i+1}, amount is {x}.')
  task=f'A fictional invoice starts at {n} credits. Apply these discounts in order: '+', '.join(str(100*p)+'%' for p in rates)+f'. After EACH discount add a fixed {c}-credit handling fee. Do not round intermediate amounts. What is the exact final charge?'
 elif k==1:
  x=Fraction(n)*Fraction(a,100)*(1-Fraction(b,100))+Fraction(n-c)*Fraction(c,100)
  task=f'A fund holds {n} credits. Its first grant is {a}% of that original balance. Return {b}% of this grant to the fund, so that portion is not spent. A second grant is {c}% of the original balance minus {c} credits (the {c} credits are subtracted BEFORE taking the percentage). What is total spending after the returned portion? Give an exact answer.'
  steps=[f'Net first grant is {Fraction(n)*Fraction(a,100)*(1-Fraction(b,100))}.',f'Second grant is {Fraction(n-c)*Fraction(c,100)}.']
 elif k==2:
  x=Fraction(n)*Fraction(a,b);x=(x-c)*Fraction(b-c,b)+c
  task=f'A tank has {n} litres. Transfer {a}/{b} of it to a smaller tank. Remove {c} litres from the smaller tank, then drain {c}/{b} of what remains there, and finally add {c} litres. What exact volume is now in the smaller tank?'
  steps=[f'Transfer is {Fraction(n)*a/b}.',f'After removal and proportional drain, add {c}.']
 elif k==3:
  x=Fraction(min(n,3000))*a/100+Fraction(max(0,n-3000))*b/100
  x=max(Fraction(0),x-c)*Fraction(107,100)
  task=f'A levy charges {a}% on the first 3000 credits of a {n}-credit bill and {b}% on the remainder. Subtract a {c}-credit rebate from the levy (floor at zero), then apply a 7% surcharge to that reduced levy. What is the exact final levy? No rounding.'
  steps=['Compute each marginal band separately.',f'Apply rebate before surcharge.']
 elif k==4:
  x=(Fraction(n)*a+Fraction(n+c)*b-Fraction(n)*c)/Fraction(a+b-c)
  task=f'A store buys {a} units at {n} credits each and {b} units at {n+c} credits each. It returns {c} units from the FIRST batch at their original unit cost. What is the exact weighted average cost of the remaining units?'
  steps=[f'Remaining units: {a+b-c}.',f'Net cost: {n*a+(n+c)*b-n*c}.']
 else:
  x=Fraction(n)*(1-Fraction(a,100));x=x/(1+Fraction(b,100));x=x+Fraction(c,100)*n
  task=f'A gross settlement of {n} credits is reduced by {a}%. The reduced figure includes a {b}% fee measured on its fee-free base; remove that included fee by division. Then add {c}% of the ORIGINAL gross settlement. What is the exact result? Do not round.'
  steps=['Remove the percentage reduction first.','Remove included fee by division, then add the original-base allowance.']
 if level>=4:
  out=hard_worked_tail(task,steps,x,r,level);out['template_id']=f'worked_{k:02d}';return out
 delta=Fraction(1,10**(4 if level>=2 else 2))
 ref='\n'.join(steps)+f'\nFinal answer: {x}'
 bad='\n'.join(steps)+f'\nThe combined calculation gives {x+delta}.\nFinal answer: {x+delta}'
 return dict(task=task,specification=task,exact_answer=str(x),reference=ref,mutation=bad,template_id=f'worked_{k:02d}')

def instruction_checks(text,rules):
 words=re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",text)
 lower=[w.lower() for w in words]
 checks=dict(word_count=rules['min_words']<=len(words)<=rules['max_words'],required=rules['required'] in lower,
  forbidden=rules['forbidden'] not in lower,no_digits=not bool(re.search(r'\d',text)),
  paragraphs=len([p for p in re.split(r'\n\s*\n',text.strip()) if p.strip()])==rules['paragraphs'],
  opening=text.startswith(rules['opening']),closing=text.endswith(rules['closing']))
 return checks,len(words)
def instructions_spec(k,r,level):
 required=r.choice(['copper','maple','harbor','linen']);forbidden=r.choice(['urgent','perfect','always'])
 opening='Dear team,';closing='Kind regards.'
 body=('Please keep the '+required+' sample beside the window while the review is in progress. '+
  'The group can compare the notes after lunch and choose a clear plan for the next meeting. '+
  'A short written record will help everyone follow the decision and prepare the materials with care. '+
  'We can share the update when the checks are complete and the room is ready for visitors.')
 if level>=4:body=hard_instruction_body(required,r,level)
 elif level>=3:body=body+' '+body
 paras=r.choice([2,3]);chunks=body.split('. ')
 text=opening+'\n\n'+body+'\n\n'+closing if paras==3 else opening+' '+body+'\n\n'+closing
 count=len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",text));pad=0 if level>=2 else 2
 rules=dict(min_words=count-pad,max_words=count+pad,required=required,forbidden=forbidden,paragraphs=paras,opening=opening,closing=closing)
 constraint=(0 if r.random() < min(.9,.7+.1*(level-4)) else r.randint(1,6)) if level>=4 else k%7
 if constraint==0:bad=text.replace(' written record',' brief written record') if level>=2 else text.replace(' written record',' very clear and brief written record')
 elif constraint==1:bad=text.replace(required,'paper')
 elif constraint==2:bad=text.replace('clear plan',forbidden+' plan')
 elif constraint==3:bad=text.replace('next meeting','next meeting on 8 May')
 elif constraint==4:bad=text.replace('\n\n','\n',1)
 elif constraint==5:bad=text.replace('Dear team,','Dear group,',1)
 else:bad=text.replace('Kind regards.','Warm regards.')
 if constraint==3: # Keep word-count constraint satisfied while violating digits only.
  bad=text.replace('short written record','short written record 8').replace('with care','carefully')
 checks,wc=instruction_checks(bad,rules)
 if sum(not v for v in checks.values())!=1:
  bad=text.replace(opening,'Dear group,',1)
 task=(f'Write a short team message with these seven constraints: (1) {rules["min_words"]} to {rules["max_words"]} words inclusive; '
  "a word is a match of [A-Za-z]+(?:'[A-Za-z]+)?, so punctuation is not a word. "
  f'(2) Include the whole word "{required}" ignoring case. (3) Do not use the whole word "{forbidden}" ignoring case. '
  f'(4) No digits. (5) Exactly {paras} nonempty paragraphs separated by a blank line. (6) Begin exactly "{opening}". (7) End exactly "{closing}".')
 if level>=7:task=task.replace('Write a short team message','Write a team update')
 assert all(instruction_checks(text,rules)[0].values())
 assert sum(not v for v in instruction_checks(bad,rules)[0].values())==1
 return dict(task=task,specification=task,rules=rules,reference=text,mutation=bad,template_id=f'instructions_{constraint:02d}')

def grounded_spec(k,r,level):
 if level>=4:return grounded_hard_spec(k,r,level)
 entities=['Marlow East','Marlow West','Marley East','Marlow Annex']
 target=entities[k%4]; cutoff='2026-09-30';base=r.randint(110,890);new=base+r.randint(2,19);units=r.randint(7,29);credit=r.randint(3,35)
 lines=[f'Fictional maintenance contract register. Review date {cutoff}. Amounts are integer credits. Only signed amendments effective on or before the review date supersede a baseline. An unsigned proposal never changes a term. Changes apply only to the exact named site and named service. Final amount equals eligible units times the applicable unit rate minus the applicable service credit.']
 records=[]
 for entity in entities:
  rate=base if entity==target else base+31
  records.append(f'Entry B-{len(records)+1:03d}, signed 2026-04-02, effective 2026-04-01. Site {entity}; service filter replacement. Baseline unit rate {rate} credits. Eligible units {units if entity==target else units+2}. Baseline service credit {credit} credits. This entry establishes the annual maintenance terms; separate inspections use a separate cost centre and are excluded from replacement invoices.')
 good_id='A-'+str(r.randint(100,899))
 records.extend([
  f'Entry {good_id}, signed 2026-08-26, effective 2026-09-01. Site {target}; service filter replacement. Replace the unit rate with {new} credits. All other terms, including eligible units, remain as in baseline B-{entities.index(target)+1:03d}. This signed amendment replaces earlier rates for this exact service only. The service credit is governed separately by entry C-721.',
  f'Entry C-721, signed 2026-09-02, effective 2026-09-15. Site {target}; service filter replacement. Replace the service credit with {credit+4} credits. This changes no rate and no eligible-unit count. Approval was completed by the contract registrar. This entry is valid at the review date. The earlier baseline credit is retained in the archive for audit comparison only.',
  f'Entry P-841, unsigned proposal dated 2026-09-27, proposed effective 2026-09-28. Site {target}; service filter replacement. Proposed unit rate {new+2} credits and proposed service credit {credit+9} credits. This draft remains unsigned at review and is not binding. The planning team requested estimates, but no signed acceptance was received by the registrar.',
  f'Entry F-506, signed 2026-09-29, effective 2026-10-01. Site {target}; service filter replacement. New unit rate {new+5} credits. Eligible units stay unchanged. The start date follows the review date, so the historical September invoice uses the preceding valid rate. This entry is stored here because it affects scheduling for the next maintenance cycle.'
 ])
 for j in range(27 if level==1 else 30):
  entity=entities[(j+1)%4];service=r.choice(['roof inspection','door adjustment','air sampling','pump calibration'])
  records.append(f'Entry M-{j+100:03d}, logged 2026-09-{j%28+1:02d}. Site {entity}; service {service}. The crew recorded {r.randint(2,9)} observations and assigned ticket {r.randint(1000,9999)} to the maintenance desk. The supervisor requested a second review after the next scheduled visit. These observations concern operational scheduling only. They change no filter replacement rate, no eligible-unit count and no contractual service credit. Supporting photographs remain in the fictional archive.')
 r.shuffle(records);lines.extend(records)
 source='\n\n'.join(lines)
 if level>=2:
  for phrase in ['This entry is valid at the review date. ', 'This draft remains unsigned at review and is not binding. ', 'The start date follows the review date, so the historical September invoice uses the preceding valid rate. ']:source=source.replace(phrase,'')
 exact=units*new-(credit+4);dtype=['superseded_rate','unsigned_proposal','future_rate','neighbor_units'][k%4]
 wrong={'superseded_rate':units*base-(credit+4),'unsigned_proposal':units*(new+2)-(credit+9),'future_rate':units*(new+5)-(credit+4),'neighbor_units':(units+2)*new-(credit+4)}[dtype]
 task=source+f'\n\nQUESTION: At review date {cutoff}, what is the net filter replacement charge for {target}? Give a short answer and one-sentence justification, ending "Final answer: <integer>".'
 ref=f'The valid signed rate is {new}; baseline eligible units are {units}, and valid credit is {credit+4}. Thus {units} times {new} minus {credit+4} gives the net charge.\nFinal answer: {exact}'
 bad=f'The register supports the applicable rate and service credit for {target}; combining the recorded units with those terms gives this net charge.\nFinal answer: {wrong}'
 return dict(task=task,source=source,specification=task.split('QUESTION:')[-1],exact_answer=str(exact),reference=ref,mutation=bad,distractor_type=dtype,template_id=f'grounded_{k%4:02d}',source_words=len(source.split()))

def generate_task(split,family,i,level=1):
 r=rng_for(split,family,i,level)
 if family=='code':
  templates=list(range(12))
  if level>=7:rng_for(split,'code-template-order',0,level).shuffle(templates)
  x=code_spec(templates[i%12],r,level)
 elif family=='worked':x=worked_spec(i%6,r,level)
 elif family=='instructions':x=instructions_spec(i%7,r,level)
 else:x=grounded_spec(i,r,level)
 x.update(item_id=f'{split}-{family}-{i:03d}',split=split,family=family,creation_date=AUTHORED_ON,generator_level=level)
 return x
def check_answer(item,text):
 if item['family']=='code':
  code=text.strip()
  if code.startswith('```'):code=re.sub(r'^```(?:python)?\s*','',code).rsplit('```',1)[0].strip()
  out=code_check(code,item['hidden_tests']);out['correct']=out['readable'] and out['passed']==out['total'];out['normalized']=code
  return out
 if item['family']=='instructions':
  checks,wc=instruction_checks(text,item['rules']);return dict(correct=all(checks.values()),readable=True,checks=checks,word_count=wc,normalized=text)
 value=numeric_answer(text)
 return dict(correct=value==Fraction(item['exact_answer']),readable=value is not None,value=str(value) if value is not None else None,normalized=text)
def ground_sentence(fields):
 u,r,c=fields['units'],fields['rate'],fields['credit']
 return f'Use {u["id"]} for {u["value"]} eligible units, {r["id"]} for the {r["value"]}-credit unit rate, and {c["id"]} for the {c["value"]}-credit service credit, giving {u["value"]} * {r["value"]} - {c["value"]}.'

def ground_fields_present(text,fields):
 body=re.split(r'Final answer:',text,flags=re.I)[0]
 return ' '.join(body.split()).casefold()==ground_sentence(fields).casefold()

def canonical_worked_final(item,text):
 value=numeric_answer(text)
 if value is None:return False
 lines=re.findall(r'Final answer:\s*([^\n]*)',text,re.I)
 return bool(lines) and lines[-1].strip().rstrip('.')==str(value)

def acceptable_bad(item,result):
 if not result['readable'] or result['correct']:return False
 if item['family']=='code':return result['passed']>=result['total']*(.9 if item['generator_level']>=4 else .5) and result.get('runtime_errors',0)==0
 if item['family']=='instructions':
  if sum(not v for v in result['checks'].values())!=1:return False
  if item['generator_level']>=4 and not result['checks']['word_count']:
   return max(item['rules']['min_words']-result['word_count'],result['word_count']-item['rules']['max_words'])<=1
  return True
 if item['generator_level']>=4 and item['family']=='worked':
  value=Fraction(result['value']);gold=Fraction(item['exact_answer'])
  return candidate_quality_eligible(item,result['normalized']) and canonical_worked_final(item,result['normalized']) and abs(value-gold)/max(abs(gold),1)<=Fraction(1,10000) and len(str(abs(value.numerator)))>=len(str(abs(gold.numerator)))-2 and len(str(value.denominator))>=len(str(gold.denominator))-2
 if item['generator_level']>=4 and item['family']=='grounded':
  for kind,value in item['distractor_answers'].items():
   if Fraction(result['value'])==Fraction(value):
    fields=copy.deepcopy(item['oracle_fields']);change=item['distractor_fields'][kind];fields[change['field']]=change['event']
    if ground_fields_present(result['normalized'],fields):return True
  return False
 return True

def mutate_passing(item,good):
 text=good['text'];family=item['family']
 if family=='code':
  tree=ast.parse(text);nodes=list(ast.walk(tree));flips={ast.Lt:ast.LtE,ast.LtE:ast.Lt,ast.Gt:ast.GtE,ast.GtE:ast.Gt,ast.Eq:ast.NotEq,ast.NotEq:ast.Eq}
  for index,node in enumerate(nodes):
   if isinstance(node,ast.Compare) and len(node.ops)==1 and type(node.ops[0]) in flips:
    new=copy.deepcopy(tree);target=list(ast.walk(new))[index];target.ops[0]=flips[type(node.ops[0])]()
   elif isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.USub):
    new=copy.deepcopy(tree);target=list(ast.walk(new))[index];target.op=ast.UAdd()
   else:continue
   candidate=ast.unparse(new);result=check_answer(item,candidate)
   if acceptable_bad(item,result):return candidate,dict(kind='single_ast_operator',node_index=index,before=ast.dump(node),after=ast.dump(target))
  if ast.dump(tree)==ast.dump(ast.parse(item['reference'])):
   candidate=ast.unparse(ast.parse(item['mutation']));result=check_answer(item,candidate)
   if acceptable_bad(item,result):return candidate,dict(kind='known_template_mutation_on_writer_ast',parent_ast_sha256=digest(ast.dump(tree)),mutated_ast_sha256=digest(ast.dump(ast.parse(candidate))),note='Actual writer answer has the same AST as the generated reference; apply the generator template bug to that actual parent. No passing candidate substitution.')
  return None,None
 if family=='worked' and item.get('carried_slip'):
  replacements=item['carried_slip']['replacements']
  if not all(old in text for old,new in replacements):return None,None
  candidate=text
  for old,new in replacements:candidate=candidate.replace(old,new,1)
  return candidate,dict(kind='carried_arithmetic_slip',adjustment_index=item['carried_slip']['adjustment_index'],delta=item['carried_slip']['delta'])
 if family=='grounded' and item.get('ground_mutation'):
  mutation=item['ground_mutation'];field=mutation['field'];old_fields=item['oracle_fields'];new_fields=copy.deepcopy(old_fields)
  new_fields[field]=dict(new_fields[field],id=mutation['new_entry'],value=mutation['new_value'])
  if not ground_fields_present(text,old_fields):return None,None
  old_sentence=ground_sentence(old_fields);new_sentence=ground_sentence(new_fields)
  pattern=r'\s+'.join(re.escape(word) for word in old_sentence.split())
  candidate=re.sub(pattern,lambda m:new_sentence,text,count=1,flags=re.I)
  candidate=re.sub(r'(Final answer:\s*)'+re.escape(item['exact_answer'])+r'(?=\s*(?:\.|$))',lambda m:m.group(1)+mutation['wrong_answer'],candidate,flags=re.I)
  return candidate,dict(kind='distractor_field_substitution',**mutation)
 if family=='instructions':
  rules=item['rules'];which=int(item['template_id'].split('_')[-1]);candidate=text
  if which==0 and item['generator_level']>=4 and int(digest(item['item_id'])[:4],16)%2:
   words=list(re.finditer(r"[A-Za-z]+(?:'[A-Za-z]+)?",text))
   optional={'final','careful','brief','next','working','short','clear','shared','written'}
   eligible=[m for m in words if m.start()>len(rules['opening']) and m.end()<len(text)-len(rules['closing']) and m.group().lower()!=rules['required']]
   preferred=[m for m in eligible if m.group().lower() in optional and text[m.start()-1:m.start()]!='-' and text[m.end():m.end()+1]!='-']
   target=(preferred or eligible)[0];end=target.end()+int(text[target.end():target.end()+1]==' ')
   candidate=text[:target.start()]+text[end:]
  elif which==0:
   wc=instruction_checks(text,rules)[1];n=rules['max_words']-wc+1
   if item['generator_level']>=4:
    target=next(m for m in re.finditer(r'\b'+rules['required']+r'\b',text,re.I) if m.start()>len(rules['opening']))
    candidate=text[:target.start()]+'updated '+text[target.start():]
   else:candidate=text.replace(rules['closing'],' '.join(['also']*n)+' '+rules['closing'])
  elif which==1:candidate=re.sub(r'\b'+rules['required']+r'\b','paper',text,flags=re.I)
  elif which==2:
   words=list(re.finditer(r'[A-Za-z]+',text))
   target=next(m for m in words if m.start()>len(rules['opening']) and m.end()<len(text)-len(rules['closing']) and m.group().lower()!=rules['required'])
   candidate=text[:target.start()]+rules['forbidden']+text[target.end():]
  elif which==3:candidate=text.replace(rules['closing'],'8'+rules['closing'])
  elif which==4:candidate=re.sub(r'\n\s*\n','\n',text,count=1)
  elif which==5:candidate=text.replace(rules['opening'],'Dear group,',1)
  else:candidate=text[:-len(rules['closing'])]+'Warm regards.'
  if not acceptable_bad(item,check_answer(item,candidate)):
   candidate=text.replace(rules['opening'],'Dear group,',1);which=5
  return candidate,dict(kind='single_constraint_mutation',constraint_index=which,before_sha256=digest(text),after_sha256=digest(candidate))
 correct=Fraction(item['exact_answer']);wrong=numeric_answer(item['mutation'])
 if family=='worked':wrong=correct+Fraction(1,10000 if item['generator_level']>=2 else 100)
 m=re.search(r'Final answer:\s*([-+]?\d[\d,]*(?:\.\d+)?(?:/\d+)?)',text,re.I)
 assert m
 candidate=text[:m.start(1)]+str(wrong)+text[m.end(1):]
 # Carry the changed final value through any exact identical numeric expressions.
 candidate=candidate.replace('= '+str(correct),'= '+str(wrong))
 return candidate,dict(kind='final_numeric_substitution',before=str(correct),after=str(wrong),note='Final numeric substitution; intermediate derivation otherwise retained.')

def candidate_quality_eligible(item,text):
 if item['family']=='grounded' and item['generator_level']>=4:return ground_fields_present(text,item['oracle_fields'])
 if item['family']=='worked' and item['generator_level']>=4:
  return canonical_worked_final(item,text) and len([line for line in text.splitlines() if line.strip()])>=3 and len(re.findall(r'[A-Za-z]+',text))>=25
 return True

def build_item_initial(item):
 attempts=[];passing=[];failing=[]
 for a,(name,spec) in enumerate(WRITERS.items()):
  hint=''
  p=WRITER_TEMPLATE.format(task=item['task'],hint=hint)
  row=ask(spec,p,'writer:'+item['item_id']+':'+str(a),budget=1800,temperature=.7)
  try: text=first_json(row['response']['text'])['answer'];assert isinstance(text,str)
  except (ValueError,KeyError,AssertionError,TypeError):text=''
  result=check_answer(item,text)
  cand=dict(text=result['normalized'],writer_model=spec['model'],writer_name=name,cache_key=row['key'],check=result,construction='natural')
  attempts.append(dict(candidate=cand,attempt_keys=row['attempt_keys']))
  cand['format_eligible']=candidate_quality_eligible(item,cand['text'])
  if result['correct'] and cand['format_eligible']:passing.append(cand)
  elif acceptable_bad(item,result):failing.append(cand)
 if not passing:
  name='Gemma 27B';spec=WRITERS[name]
  p=WRITER_TEMPLATE.format(task=item['task'],hint='For this verified solution, reproduce its complete content exactly, preserving all values, logic, and line breaks. Do not add a code fence.\nVERIFIED SOLUTION\n'+item['reference'])
  row=ask(spec,p,'writer:'+item['item_id']+':reference-assisted',budget=2200,temperature=0)
  try:text=first_json(row['response']['text'])['answer']
  except (ValueError,KeyError,TypeError):text=''
  result=check_answer(item,text)
  cand=dict(text=result['normalized'],writer_model=spec['model'],writer_name=name,cache_key=row['key'],check=result,construction='reference_assisted')
  attempts.append(dict(candidate=cand,attempt_keys=row['attempt_keys']))
  if not result['correct'] or not candidate_quality_eligible(item,cand['text']):
   # Preserve the writer attempt and disclose the deterministic repair.
   cand.update(text=item['reference'],check=check_answer(item,item['reference']),construction='reference_repair')
  passing.append(cand)
 good=passing[0]
 if failing:bad=failing[0];error_source='natural'
 else:
  changed,mutation_info=mutate_passing(item,good)
  if changed is None:
   # This fallback is a disclosed deterministic reference repair before mutation.
   good=copy.deepcopy(good);good.update(text=item['reference'],check=check_answer(item,item['reference']),construction='reference_repair_for_mutation')
   changed=item['mutation'];mutation_info=dict(kind='generator_mutation',base='reference')
  bad=dict(text=changed,writer_model=good['writer_model'],writer_name=good['writer_name'],cache_key=good['cache_key'],construction='verified_mutation',mutation_parent_text=good['text'],mutation=mutation_info)
  bad['check']=check_answer(item,bad['text']);error_source='mutation'
  assert acceptable_bad(item,bad['check']), (item['item_id'],bad['check'])
 better=rng_for(item['split'],item['family'],int(item['item_id'].split('-')[-1]),99).choice(['A','B'])
 candidates={better:good,('B' if better=='A' else 'A'):bad}
 fmt=lambda s:len(re.findall(r'(?m)^\s*(?:#|[-*]|\d+\.)',s))
 trap=len(bad['text'])>=1.3*len(good['text']) or fmt(bad['text'])>fmt(good['text'])
 if item['family']=='code':subtlety=dict(failed_share=1-bad['check']['passed']/bad['check']['total'])
 elif item['family']=='instructions':subtlety=dict(broken=[k for k,v in bad['check']['checks'].items() if not v],word_count=bad['check']['word_count'],word_distance=max(item['rules']['min_words']-bad['check']['word_count'],bad['check']['word_count']-item['rules']['max_words'],0))
 elif item['family']=='worked':subtlety=dict(relative_error=float(abs(Fraction(bad['check']['value'])-Fraction(item['exact_answer']))/max(abs(Fraction(item['exact_answer'])),Fraction(1))))
 else:
  kind=item['distractor_type'] if error_source=='mutation' else 'natural_wrong_value'
  if error_source=='natural' and item.get('distractor_answers'):
   kind=next(name for name,value in item['distractor_answers'].items() if Fraction(value)==Fraction(bad['check']['value']))
  subtlety=dict(distractor_type=kind)
 out=copy.deepcopy(item);out.update(candidates=candidates,better=better,error_source=error_source,tags=dict(trap=trap,subtlety=subtlety),writer_attempts=attempts)
 save(DATA/'items'/(item['item_id']+'.json'),out)
 return out
def finish_writer_pair(item,good,bad,error_source,attempts):
 assert good['check']['correct'] and acceptable_bad(item,bad['check'])
 assert good['construction'] in ('natural','reference_assisted','reference_assisted_chunks')
 better=rng_for(item['split'],item['family'],int(item['item_id'].split('-')[-1]),99).choice(['A','B'])
 candidates={better:good,('B' if better=='A' else 'A'):bad}
 fmt=lambda text:len(re.findall(r'(?m)^\s*(?:#|[-*]|\d+\.)',text))
 trap=len(bad['text'])>=1.3*len(good['text']) or fmt(bad['text'])>fmt(good['text'])
 if item['family']=='code':subtlety=dict(failed_share=1-bad['check']['passed']/bad['check']['total'])
 elif item['family']=='instructions':subtlety=dict(broken=[k for k,v in bad['check']['checks'].items() if not v],word_count=bad['check']['word_count'],word_distance=max(item['rules']['min_words']-bad['check']['word_count'],bad['check']['word_count']-item['rules']['max_words'],0))
 elif item['family']=='worked':subtlety=dict(relative_error=float(abs(Fraction(bad['check']['value'])-Fraction(item['exact_answer']))/max(abs(Fraction(item['exact_answer'])),Fraction(1))))
 else:
  kind=item['distractor_type']
  if error_source=='natural':
   for name,value in item['distractor_answers'].items():
    fields=copy.deepcopy(item['oracle_fields']);change=item['distractor_fields'][name];fields[change['field']]=change['event']
    if Fraction(value)==Fraction(bad['check']['value']) and ground_fields_present(bad['text'],fields):kind=name;break
  subtlety=dict(distractor_type=kind)
 out=copy.deepcopy(item);out.update(candidates=candidates,better=better,error_source=error_source,tags=dict(trap=trap,subtlety=subtlety),writer_attempts=attempts,candidate_policy='Passing text comes from normalized cached writer replies or verified returned chunks joined with recorded whitespace separators; deterministic mutation is allowed only for worse answers.')
 save(DATA/'items'/(item['item_id']+'.json'),out)
 return out

def assemble_writer_transcription(item,attempts):
 name=list(WRITERS)[-1];spec=WRITERS[name];targets=[]
 for paragraph in item['reference'].split('\n\n'):
  blocks=[];current=''
  for sentence in re.split(r'(?<=\.) ',paragraph):
   if current and len(current)+1+len(sentence)>MAX_TRANSCRIPTION_CHARS:blocks.append(current);current=''
   current=(current+' '+sentence) if current else sentence
  if current:blocks.append(current)
  for index,block in enumerate(blocks):targets.append(dict(separator_before=('' if not targets else '\n\n') if index==0 else ' ',target=block))
 assert ''.join(t['separator_before']+t['target'] for t in targets)==item['reference']
 chunks=[]
 for index,target in enumerate(targets):
  for attempt in range(MAX_CHUNK_ATTEMPTS):
   prompt=WRITER_COPY_TEMPLATE.format(reference_json=json.dumps({'answer':target['target']},ensure_ascii=False))
   row=ask(spec,prompt,'writer:'+item['item_id']+':reference-assisted-chunk-'+str(index)+'-'+str(attempt),budget=1600,temperature=0 if attempt==0 else .2 if attempt<4 else .4)
   try:raw=first_json(row['response']['text'])['answer'];assert isinstance(raw,str)
   except (ValueError,KeyError,AssertionError,TypeError):raw=''
   normalized=raw.strip();exact=normalized==target['target']
   attempts.append(dict(construction='reference_assisted_chunk',chunk_index=index,copy_attempt=attempt,cache_key=row['key'],attempt_keys=row['attempt_keys'],writer_model=spec['model'],writer_name=name,exact_copy=exact))
   if exact:
    chunks.append(dict(separator_before=target['separator_before'],writer_raw_answer=raw,normalized=normalized,expected_sha256=digest(normalized),cache_key=row['key'],attempt_keys=row['attempt_keys']))
    break
  else:raise RuntimeError('No exact writer transcription for chunk '+str(index)+' of '+item['item_id']+'; no reference substitution.')
 text=''.join(c['separator_before']+c['normalized'] for c in chunks);check=check_answer(item,text)
 assert check['correct'] and text==item['reference']
 return dict(text=text,writer_model=spec['model'],writer_name=name,cache_key=chunks[0]['cache_key'],cache_keys=[c['cache_key'] for c in chunks],writer_chunks=chunks,check=check,construction='reference_assisted_chunks',format_eligible=True)

def build_verified_writer_item(item):
 attempts=[];passing=[];failing=[]
 def record(name,spec,tag,hint,budget,temperature,construction):
  prompt=WRITER_COPY_TEMPLATE.format(reference_json=json.dumps({'answer':item['reference']},ensure_ascii=False)) if construction=='reference_assisted' else WRITER_TEMPLATE.format(task=item['task'],hint=hint)
  row=ask(spec,prompt,'writer:'+item['item_id']+':'+tag,budget=budget,temperature=temperature)
  try:raw_answer=first_json(row['response']['text'])['answer'];assert isinstance(raw_answer,str)
  except (ValueError,KeyError,AssertionError,TypeError):raw_answer=''
  result=check_answer(item,raw_answer)
  cand=dict(text=result['normalized'],writer_raw_answer=raw_answer,writer_model=spec['model'],writer_name=name,cache_key=row['key'],check=result,construction=construction,format_eligible=candidate_quality_eligible(item,result['normalized']))
  attempts.append(dict(candidate=copy.deepcopy(cand),attempt_keys=row['attempt_keys']))
  if result['correct'] and cand['format_eligible']:passing.append(cand)
  elif acceptable_bad(item,result):failing.append(cand)
 writer_budget=min(6400,max(1800,math.ceil(len(item['reference'])/3)+400)) if item['generator_level']>=7 else 1800
 for index,(name,spec) in enumerate(WRITERS.items()):record(name,spec,str(index),'',writer_budget,.7,'natural')
 if item['family']=='instructions' and item['generator_level']>=8 and not passing:
  assembled=assemble_writer_transcription(item,attempts);passing.append(assembled);attempts.append(dict(candidate=copy.deepcopy(assembled),attempt_keys=[k for c in assembled['writer_chunks'] for k in c['attempt_keys']]))
 for repair in range(MAX_WRITER_ASSISTED_ATTEMPTS+1):
  if passing and failing:
   if item['family']=='worked':good,bad=min(itertools.product(passing,failing),key=lambda pair:abs(math.log(max(1,len(pair[0]['text']))/max(1,len(pair[1]['text'])))))
   else:good,bad=passing[0],failing[0]
   return finish_writer_pair(item,good,bad,'natural',attempts)
  for good in passing:
   changed,mutation=mutate_passing(item,good)
   if changed is None:continue
   check=check_answer(item,changed)
   if not acceptable_bad(item,check):continue
   bad=dict(text=changed,writer_model=good['writer_model'],writer_name=good['writer_name'],cache_key=good['cache_key'],check=check,construction='verified_mutation',mutation_parent_text=good['text'],mutation=mutation)
   return finish_writer_pair(item,good,bad,'mutation',attempts)
  if repair==MAX_WRITER_ASSISTED_ATTEMPTS:break
  writer_names=list(reversed(WRITERS));name=writer_names[repair%len(writer_names)];spec=WRITERS[name]
  feedback=''
  if attempts:
   c=attempts[-1]['candidate'];r=c['check']
   feedback=f'Previous attempt: correct={r["correct"]}, readable={r["readable"]}, required worked/grounded form={c["format_eligible"]}. '
   if item['family']=='code':feedback+=f'Passed {r.get("passed",0)} of {r.get("total",64)} independent checks. '
  hint=('A verified complete answer follows. Reproduce its content exactly inside the answer JSON string, preserving every value, entry ID, line break, Python operator and punctuation mark. Do not add a fence or commentary. '+feedback+'\nVERIFIED SOLUTION\n'+item['reference'])
  record(name,spec,'reference-assisted-copy-v2-'+str(repair),hint,max(3200,writer_budget),0 if repair<2 else .2,'reference_assisted')
 raise RuntimeError('No writer-derived verified pair after '+str(MAX_WRITER_ASSISTED_ATTEMPTS)+' reference-assisted attempts: '+item['item_id']+'; no generated reference was substituted.')

def build_item(item):
 return build_verified_writer_item(item) if item['generator_level']>=4 else build_item_initial(item)

def build_exam(split,n,level=1):
 (DATA/'items').mkdir(exist_ok=True)
 tasks=[generate_task(split,f,i,level) for f in FAMILIES for i in range(n)]
 def work(t):
  p=DATA/'items'/(t['item_id']+'.json')
  if p.exists():
   saved=load(p);assert saved['task']==t['task'];return saved
  if not LIVE:raise RuntimeError('Missing frozen item '+t['item_id'])
  return build_item(t)
 with ThreadPoolExecutor(8) as pool:
  futures={pool.submit(work,t):t for t in tasks};out=[]
  for f in as_completed(futures):
   out.append(f.result())
   if len(out)%12==0 or len(out)==len(tasks):print('items',split,len(out),'/',len(tasks),flush=True)
 return sorted(out,key=lambda x:x['item_id'])

