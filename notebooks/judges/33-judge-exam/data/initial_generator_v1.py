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
 if level>=2:
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
 return dict(task=task,specification=desc,reference=source,mutation=bad,hidden_tests=tests,template_id=f'code_{k:02d}')
def run_trusted(source,inp):
 ns={};exec(source,ns);return ns['solve'](copy.deepcopy(inp))

def code_check(source,tests):
 try:
  ast.parse(source)
 except (SyntaxError,TypeError): return dict(readable=False,passed=0,total=len(tests),error='syntax')
 # Isolated cwd; no API credentials, no user site, restricted imports, one process per candidate.
 runner="""import json,sys,builtins
request=json.load(sys.stdin)
real_import=builtins.__import__
allowed={'math','decimal','fractions','collections','itertools','functools','datetime','calendar','re','statistics','bisect','heapq','operator','string','typing','copy'}
def guarded(name,*a,**kw):
 if name.split('.')[0] not in allowed: raise ImportError('blocked import')
 return real_import(name,*a,**kw)
b=dict(vars(builtins));b['__import__']=guarded
for k in ['open','input','eval','exec','compile','breakpoint']:b.pop(k,None)
ns={'__builtins__':b}
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
  stages={1:4,2:7,3:10}[level]
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
 if level>=3:body=body+' '+body
 paras=r.choice([2,3]);chunks=body.split('. ')
 text=opening+'\n\n'+body+'\n\n'+closing if paras==3 else opening+' '+body+'\n\n'+closing
 count=len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",text));pad=0 if level>=2 else 2
 rules=dict(min_words=count-pad,max_words=count+pad,required=required,forbidden=forbidden,paragraphs=paras,opening=opening,closing=closing)
 constraint=k%7
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
  bad=text.replace('The group','The 8roup')
 task=(f'Write a short team message with these seven constraints: (1) {rules["min_words"]} to {rules["max_words"]} words inclusive; '
  "a word is a match of [A-Za-z]+(?:'[A-Za-z]+)?, so punctuation is not a word. "
  f'(2) Include the whole word "{required}" ignoring case. (3) Do not use the whole word "{forbidden}" ignoring case. '
  f'(4) No digits. (5) Exactly {paras} nonempty paragraphs separated by a blank line. (6) Begin exactly "{opening}". (7) End exactly "{closing}".')
 assert all(instruction_checks(text,rules)[0].values())
 assert sum(not v for v in instruction_checks(bad,rules)[0].values())==1
 return dict(task=task,specification=task,rules=rules,reference=text,mutation=bad,template_id=f'instructions_{constraint:02d}')

def grounded_spec(k,r,level):
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
 if family=='code':x=code_spec(i%12,r,level)
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
def acceptable_bad(item,result):
 if not result['readable'] or result['correct']:return False
 if item['family']=='code':return result['passed']>=result['total']/2 and result.get('runtime_errors',0)==0
 if item['family']=='instructions':return sum(not v for v in result['checks'].values())==1
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
  return None,None
 if family=='instructions':
  rules=item['rules'];which=int(item['template_id'].split('_')[-1]);candidate=text
  if which==0:
   wc=instruction_checks(text,rules)[1];n=rules['max_words']-wc+1
   candidate=text.replace(rules['closing'],' '.join(['also']*n)+' '+rules['closing'])
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

def build_item(item):
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
  if result['correct']:passing.append(cand)
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
  if not result['correct']:
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
   changed=item['mutation'];mutation_info=dict(kind='generator_operator_mutation',base='reference')
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
 else:subtlety=dict(distractor_type=item['distractor_type'] if error_source=='mutation' else 'natural_wrong_value')
 out=copy.deepcopy(item);out.update(candidates=candidates,better=better,error_source=error_source,tags=dict(trap=trap,subtlety=subtlety),writer_attempts=attempts)
 save(DATA/'items'/(item['item_id']+'.json'),out)
 return out
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

