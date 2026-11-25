"""Code embedded verbatim in notebook 43; execution never imports this file there."""
from pathlib import Path
import json, base64, random, re, itertools, struct, subprocess, hashlib, os

STREAM_DATA = Path('data/streams_v2')
N_STREAM_TASKS = 3
STREAM_FORMATS = ['elf_hex', 'assembly_program', 'c_program']
STREAM_PROTOCOL = 'streams-v2'
STREAM_SEED = 20261103432
STREAM_IMAGE_TAG = 'experiment43-toolchain:streams-v2'

def stream_save(name, value):
    path = STREAM_DATA / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def b64(value):
    return base64.b64encode(value).decode('ascii')

def unb64(value):
    return base64.b64decode(value)

def oracle(task, payload):
    if task == 'sorter':
        tokens = re.findall(rb'[^ \t\n]+', payload)
        good = len(tokens) <= 128 and all(re.fullmatch(rb'-?[0-9]+', x) for x in tokens)
        nums = [int(x) for x in tokens] if good else []
        good = good and all(-(1 << 31) <= x < (1 << 31) for x in nums)
        return ((b''.join(str(x).encode() + b'\n' for x in sorted(nums)), 0)
                if good else (b'ERR\n', 2))
    if task == 'rle':
        out = bytearray()
        for byte, group in itertools.groupby(payload):
            n = sum(1 for _ in group)
            while n:
                count = min(n, 255)
                out.extend([count, byte])
                n -= count
        return bytes(out), 0
    header = b'account,amount_cents\n'
    if not payload.startswith(header):
        return b'ERR\n', 2
    body = payload[len(header):]
    if not body:
        lines = []
    else:
        if body.endswith(b'\n'):
            body = body[:-1]
        lines = body.split(b'\n')
    if len(lines) > 128:
        return b'ERR\n', 2
    totals = {}
    for line in lines:
        m = re.fullmatch(rb'([0-9]+),(-?[0-9]+)', line)
        if not m:
            return b'ERR\n', 2
        account, amount = int(m[1]), int(m[2])
        if not 0 <= account <= 63 or not -1000000000 <= amount <= 1000000000:
            return b'ERR\n', 2
        totals[account] = totals.get(account, 0) + amount
    return b''.join(f'{k},{totals[k]}\n'.encode() for k in sorted(totals)), 0

def freeze_stream_cases():
    target = STREAM_DATA / 'cases.json'
    if target.exists():
        return json.loads(target.read_text(encoding='utf-8'))
    rng = random.Random(STREAM_SEED)
    cases = []
    def add(task, payload, group, description):
        out, status = oracle(task, payload)
        index = sum(c['task'] == task for c in cases)
        assert len(payload) <= 4096
        cases.append({'id': f'{task}-{index:03}', 'task': task, 'group': group,
                      'description': description, 'input_b64': b64(payload),
                      'expected_b64': b64(out), 'expected_exit': status,
                      'input_bytes': len(payload), 'output_bytes': len(out)})
    bounds = [b'', b' \t\n', b'3 -1 3 0\n', b'-2147483648 2147483647 0\n',
              b'-3 -2 -1 -3', b'0 -0 00 -000\n', b'00012 -0007 2',
              b' '.join(str(i).encode() for i in range(127, -1, -1)),
              b'\t'.join([b'2147483647'] * 128), b'\n'.join([b'-2147483648'] * 128),
              b'1', b'-1', b'1\t2\n3 4\n', b'5 5 5 5', b'9\n8\n7\n6\n', b'  -8\t9']
    for i, value in enumerate(bounds):
        add('sorter', value, 'boundary', f'Planned boundary {i}')
    invalid = [b'+1', b'-', b'12x', b'2147483648', b'-2147483649', b'1,2', b'1\r\n',
               b'1\x002', b'--2', b'2.0', b'0x10', b'9'*80,
               b' '.join([b'0']*129), b'1\v2', b'1\f2', b'\xff']
    for i, value in enumerate(invalid): add('sorter', value, 'malformed', f'Malformed token/count {i}')
    for i in range(96):
        n = rng.randint(0, 128)
        values = [rng.randint(-(1<<31), (1<<31)-1) for _ in range(n)]
        if i % 4 == 0 and values: values = [rng.choice([-17, 0, 19])] * n
        if i % 4 == 1: values.sort(reverse=True)
        separator = rng.choice([b' ', b'\t', b'\n', b' \n\t'])
        payload = separator.join(str(v).encode() for v in values)
        if i % 2: payload += b'\n'
        add('sorter', payload, 'generated_valid', 'Seeded variable-length integer list')

    rle_bounds = [b'', b'A', b'AAAABB', b'\x00', b'\xff'*2, b'A'*254, b'A'*255, b'A'*256,
                  b'A'*510, b'A'*511, bytes(range(256)), b'\x00\xff'*2048,
                  b'Z'*4096, bytes(range(256))*16, b'AAAABAAAAC', b'\n'*256+b'\x00'*256]
    for i, value in enumerate(rle_bounds): add('rle', value, 'boundary', f'Run/binary boundary {i}')
    for i in range(112):
        n = rng.randint(0, 4096)
        if i % 3 == 0:
            value = bytes(rng.randrange(256) for _ in range(n))
        else:
            value = bytearray()
            while len(value) < n:
                byte = rng.randrange(256)
                count = rng.choice([1, 2, 254, 255, 256, 511, rng.randint(1, 700)])
                value.extend([byte] * min(count, n-len(value)))
            value = bytes(value)
        add('rle', value, 'generated_valid', 'Seeded binary stream with variable runs')

    h = b'account,amount_cents\n'
    tx_bounds = [h, h+b'17,1250\n42,-300\n17,275\n', h+b'0,0\n', h+b'63,-1000000000',
                 h+b'63,1000000000\n63,-1000000000\n', h+b'0017,00025\n17,-0005',
                 h+b'42,-3\n17,10', h+b'0,-0\n', h+b'0,1000000000\n'*128,
                 h+b'63,-1000000000\n'*128,
                 h+b''.join(f'{i},1\n'.encode() for i in range(64)),
                 h+b''.join(f'{i},-1\n'.encode() for i in range(63,-1,-1)),
                 h+b'3,15\n3,15\n3,15', h+b'1,-8\n2,9\n1,8', h+b'0,1', h+b'63,1\n0,2\n']
    for i, value in enumerate(tx_bounds): add('transactions', value, 'boundary', f'Total/account boundary {i}')
    tx_bad = [b'', b'account,amount_cents', b'Account,amount_cents\n', h+b'64,1\n', h+b'-1,1',
              h+b'1,1000000001', h+b'1,-1000000001', h+b'1,+2', h+b'1,', h+b'\n',
              h+b'1,2,3', h+b'1,2\r\n', h+b'1,2\n\n', h+b' 1,2', h+b'1,2\n'*129,
              h+b'1,2\n2,bad\n']
    for i, value in enumerate(tx_bad): add('transactions', value, 'malformed', f'Malformed record/header {i}')
    for i in range(96):
        n = rng.randint(0,128)
        rows = [(rng.randrange(64),rng.randint(-1000000000,1000000000)) for _ in range(n)]
        if i % 5 == 0: rows = [(17, amount) for _,amount in rows]
        payload = h + b'\n'.join(f'{a},{v}'.encode() for a,v in rows)
        if rows and i % 2: payload += b'\n'
        add('transactions', payload, 'generated_valid', 'Seeded account records and integer amounts')
    assert all(sum(c['task']==t for c in cases)==128 for t in ['sorter','rle','transactions'])
    obj = {'protocol': STREAM_PROTOCOL, 'seed': STREAM_SEED, 'created_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
           'provenance':'Python-generated fresh input instances with deterministic exact byte oracles; no model generated the evaluation data. Familiar task families may be present in training.',
           'cutoff':'2026-04-30', 'cutoff_source':'https://developers.openai.com/api/docs/models/gpt-6.1-sol',
           'date_filter':'Created after the documented cutoff; algorithmic novelty is not asserted.', 'cases':cases}
    stream_save('cases.json',obj)
    return obj

STREAM_SPECS = {
 'sorter': '''Read stdin as an ASCII integer list. Input is at most 4096 bytes. Delimiters are ONLY space (0x20), tab (0x09), and LF (0x0a); any number may occur before, between or after tokens. A token is an optional '-' followed by one or more ASCII digits. Leading zeroes and negative zero are allowed; '+' is forbidden. There may be 0 through 128 tokens, each in [-2147483648,2147483647]. Sort all integers in signed ascending order, retaining duplicates. Write each value in canonical decimal (no leading zeroes, zero is '0'), followed by LF. Empty/whitespace-only input gives empty output. Any invalid token, out-of-range value or excess token count must produce exactly 'ERR\\n' and exit status 2, without partial sorted output. Valid input exits 0. Example stdin bytes '3 -1 3 0\\n' produce '-1\\n0\\n3\\n3\\n'.''',
 'rle': '''Read stdin as arbitrary binary bytes, length 0 through 4096 inclusive. Run-length encode it as binary pairs [count,value]. Count is one unsigned byte 1 through 255. Each maximal run of equal bytes must be emitted as zero or more [255,value] pairs followed by one [remaining,value] pair if a remainder exists. Do not emit zero-count pairs. Empty input produces empty output. Write ONLY these pairs, no header or length prefix, and exit 0. All byte values 0 through 255 are ordinary input data. Example ASCII 'AAAABB' produces hex 04 41 02 42. A run of 256 'A' bytes produces ff 41 01 41. The maximum possible output length is 8192 bytes. All inputs in the stated length range are valid.''',
 'transactions': '''Read a restricted ASCII CSV stream of at most 4096 bytes. The header must be exactly 'account,amount_cents\\n'. Then there are 0 through 128 records. Each record has one unsigned decimal account ID, one comma, and one decimal signed amount in cents. IDs are 0 through 63 inclusive. Amounts are [-1000000000,1000000000]. Amount syntax is optional '-' and one or more digits; '+' is forbidden. Leading zeroes and negative zero are allowed. No whitespace, CR, quotes, extra fields, blank records or other characters are allowed. Records are separated by LF; the last record's LF is optional. Header-only input is valid and produces empty output. Sum amounts per account using sufficient integer width. Output one line 'account,total\\n' for EVERY account that appeared, including total zero, in increasing numeric ID order; use canonical decimal. No output header. Valid input exits 0. Any malformed header, record, out-of-range field or excess record count must produce exactly 'ERR\\n' and exit 2 without partial totals. Example header plus '17,1250\\n42,-300\\n17,275\\n' produces '17,1525\\n42,-300\\n'.''' }

def stream_prompt(task, fmt):
    common = ('Implement this complete Linux x86-64 command-line program.\n' + STREAM_SPECS[task] + '\n'
              'The test uses a regular stdin file and EOF; each process handles one file. Stderr must always be empty. '
              'No files, network, external commands, testing, compiler, assembler or other tool use during generation. '
              'One final artifact only; no Markdown fences, explanations or placeholders.\n')
    if fmt == 'elf_hex':
        return common + ('Return the ENTIRE executable file as a plain hexadecimal string, whitespace allowed, at most 8192 bytes after decoding. '
          'Supply every ELF64 header, program header, instruction and any initialised data byte yourself. No wrapper, linker, assembler, fixup or added header will be provided. '
          'Use ET_EXEC, baseline integer x86-64, no interpreter or dynamic libraries. Linux read=0, write=1, exit=60; use only these syscalls. '
          'Use the stack or your own loadable writable segment for working buffers. A normal base such as 0x400000 and omitted section headers are allowed. '
          'All process-entry registers except RSP are unspecified. Return actual hex bytes only, including all zeroes.')
    if fmt == 'assembly_program':
        return common + ('Return complete NASM x86-64 source for the whole program, at most 32768 characters. '
          'Include global _start and any sections/data you need. The evaluator runs nasm -f elf64 then ld -m elf_x86_64 -e _start. '
          'No libc or external functions. Use baseline integer x86-64 and Linux read=0, write=1, exit=60 only. '
          'The assembler/linker will encode instructions, resolve labels and construct the ELF. Return source only.')
    return common + ('Return complete C11 source with main, at most 32768 characters. '
          'Standard libc and POSIX read/write are available. No inline assembly, embedded executable bytes, external files or commands. '
          'The evaluator compiles with gcc -std=c11 -O2 -fno-pie -no-pie. Return source only.')

def freeze_stream_requests(model='gpt-6.1-sol'):
    requests=[]
    for task in list(STREAM_SPECS)[:N_STREAM_TASKS]:
        for fmt in STREAM_FORMATS:
            req={'protocol':STREAM_PROTOCOL,'task':task,'format':fmt,'model':model,
                 'effort':'high','service_tier':'default','neutral_instruction':NEUTRAL,
                 'cli':'codex exec','cli_version':'0.160.1','tool_policy':'disabled and audited',
                 'prompt':stream_prompt(task,fmt)}
            req['key']=sha(canonical(req)); requests.append(req)
    path=STREAM_DATA/'requests.json'
    if path.exists(): assert load(path)==requests,'Frozen stream requests changed'
    else: stream_save('requests.json',requests)
    return requests

STREAM_RUNNER = r"""
import base64,json,os,resource,subprocess,tempfile,hashlib
from pathlib import Path
job=json.loads(Path('/job.json').read_text())
def b64(x): return base64.b64encode(x).decode()
def limits():
    resource.setrlimit(resource.RLIMIT_CPU,(1,1))
    resource.setrlimit(resource.RLIMIT_AS,(128*1024*1024,128*1024*1024))
    resource.setrlimit(resource.RLIMIT_FSIZE,(32768,32768))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
result={'build_ok':False,'build_log':'','answers':[],'binary_b64':None,'commands':[]}
with tempfile.TemporaryDirectory(dir='/tmp') as work:
    work=Path(work); exe=work/'program'; fmt=job['format']
    if fmt=='elf_hex':
        exe.write_bytes(base64.b64decode(job['artifact_b64'])); result['build_ok']=True
    else:
        source=work/('program.asm' if fmt=='assembly_program' else 'program.c')
        source.write_text(job['source'])
        commands=([['nasm','-f','elf64',str(source),'-o',str(work/'program.o')],
                   ['ld','-m','elf_x86_64','-e','_start','-o',str(exe),str(work/'program.o')]]
                  if fmt=='assembly_program' else
                  [['gcc','-std=c11','-O2','-fno-pie','-no-pie',str(source),'-o',str(exe)]])
        result['commands']=commands
        result['build_ok']=True
        for command in commands:
            try:
                p=subprocess.run(command,cwd=work,capture_output=True,timeout=30)
                result['build_log']+=(p.stdout+p.stderr).decode('utf-8','replace')[:30000]
                if p.returncode:
                    result['build_ok']=False; break
            except Exception as exc:
                result['build_log']+=str(exc); result['build_ok']=False; break
    if result['build_ok']:
        exe.chmod(0o500)
        binary=exe.read_bytes(); result['binary_b64']=b64(binary); result['binary_sha256']=hashlib.sha256(binary).hexdigest()
        for case in job['cases']:
            inf,outf,errf=work/'input',work/'output',work/'stderr'
            inf.write_bytes(base64.b64decode(case['input_b64']))
            answer={'id':case['id'],'stdout_b64':'','stderr_b64':'','exit':None,'error':''}
            try:
                with inf.open('rb') as fi,outf.open('wb') as fo,errf.open('wb') as fe:
                    p=subprocess.run([str(exe)],stdin=fi,stdout=fo,stderr=fe,timeout=1,
                                     env={},cwd=work,preexec_fn=limits)
                answer.update(stdout_b64=b64(outf.read_bytes()),stderr_b64=b64(errf.read_bytes()),exit=p.returncode)
                if p.returncode<0: answer['error']='signal '+str(-p.returncode)
            except Exception as exc: answer['error']=type(exc).__name__+': '+str(exc)
            result['answers'].append(answer)
print(json.dumps(result))
"""

def parse_stream_artifact(row):
    text,fmt=row['text'],row['request']['format']
    if not row['completed'] or row['returncode']:
        return None,'incomplete CLI request'
    if not text or '```' in text:
        return None,'empty reply or forbidden fence'
    if fmt=='elf_hex':
        if not re.fullmatch(r'[0-9a-fA-F\s]+',text): return None,'not plain hex'
        try: code=bytes.fromhex(text)
        except ValueError as exc: return None,str(exc)
        if not 1<=len(code)<=8192: return None,'byte length outside limit'
        return code,''
    if len(text)>32768: return None,'source length outside limit'
    return text,''

def run_stream_artifact(row,cases,image):
    artifact,error=parse_stream_artifact(row)
    if error: return {'parse_ok':False,'parse_error':error,'build_ok':False,'answers':[]}
    req=row['request']; slot=req['task']+'-'+req['format']
    job={'format':req['format'],'cases':[{'id':c['id'],'input_b64':c['input_b64']} for c in cases]}
    if isinstance(artifact,bytes): job['artifact_b64']=b64(artifact)
    else: job['source']=artifact
    stream_save('tmp/job.json',job)
    runner=STREAM_DATA/'tmp/runner.py'; runner.write_text(STREAM_RUNNER,encoding='utf-8')
    mounts=[]
    for host,container in [(STREAM_DATA/'tmp/job.json','/job.json'),(runner,'/runner.py')]:
        mounts += ['--mount','type=bind,source='+str(host.resolve())+',target='+container+',readonly']
    command=['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL',
             '--security-opt','no-new-privileges','--pids-limit','32','--memory','512m','--cpus','1',
             '--user','65534:65534','--tmpfs','/tmp:rw,exec,nosuid,size=32m',*mounts,image,'python','/runner.py']
    p=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    if p.returncode: raise RuntimeError('Evaluator container failure, not a model score: '+p.stderr)
    result=json.loads(p.stdout); result.update(parse_ok=True,parse_error='')
    if result.get('binary_b64'):
        binary=unb64(result['binary_b64'])
        outdir=STREAM_DATA/'artifacts'; outdir.mkdir(exist_ok=True)
        # Hex is portable in Git; native execution stays in the container.
        (outdir/(slot+'.hex')).write_text(binary.hex()+'\n',encoding='utf-8')
        if isinstance(artifact,str):
            (outdir/(slot+('.asm' if req['format']=='assembly_program' else '.c'))).write_text(artifact+'\n',encoding='utf-8')
    stream_save('runs/'+slot+'.json',result)
    return result

def score_streams(rows,case_data,image):
    summaries,details=[] ,[]
    for row in rows:
        req=row['request']; cases=[c for c in case_data['cases'] if c['task']==req['task']]
        result=run_stream_artifact(row,cases,image)
        answers={a['id']:a for a in result.get('answers',[])}
        loader_failure=bool(answers) and all(a['error'].startswith(('OSError:','FileNotFoundError:','PermissionError:')) for a in answers.values())
        readable=result['parse_ok'] and result['build_ok'] and not loader_failure
        per=[]
        for case in cases:
            answer=answers.get(case['id'],{'stdout_b64':'','stderr_b64':'','exit':None,'error':'artifact unreadable or build failed'})
            correct=(readable and not answer['error'] and answer['stdout_b64']==case['expected_b64']
                     and not answer['stderr_b64'] and answer['exit']==case['expected_exit'])
            runtime=readable and bool(answer['error'])
            rec={**case,'format':req['format'],'observed_b64':answer['stdout_b64'],
                 'observed_stderr_b64':answer['stderr_b64'],'observed_exit':answer['exit'],
                 'execution_error':answer['error'],'readable':readable,'correct':correct,'runtime_failure':runtime}
            details.append(rec); per.append(rec)
        u=row['usage']; binary=unb64(result['binary_b64']) if result.get('binary_b64') else b''
        summaries.append({'task':req['task'],'format':req['format'],'model':req['model'],'interface':'complete executable',
          'readable':readable,'parse_ok':result['parse_ok'],'build_ok':result['build_ok'],'loader_failure':loader_failure,
          'parse_error':result['parse_error'],'build_log':result.get('build_log',''),
          'n_inputs':len(cases),'correct_inputs':sum(c['correct'] for c in per),'program_pass':all(c['correct'] for c in per),
          'runtime_errors':sum(c['runtime_failure'] for c in per),'wrong_outputs':sum(readable and not c['runtime_failure'] and not c['correct'] for c in per),
          'valid_inputs':sum(c['expected_exit']==0 for c in per),'correct_valid':sum(c['expected_exit']==0 and c['correct'] for c in per),
          'invalid_inputs':sum(c['expected_exit']!=0 for c in per),'correct_invalid':sum(c['expected_exit']!=0 and c['correct'] for c in per),
          'bytes':len(binary) if binary else None,'input_tokens':u.get('input_tokens'),
          'cached_input_tokens':u.get('cached_input_tokens',0),'output_tokens':u.get('output_tokens'),
          'reasoning_output_tokens':u.get('reasoning_output_tokens'),
          'artifact_output_tokens':u.get('output_tokens',0)-u.get('reasoning_output_tokens',0),
          'seconds':row['seconds'],'api_equivalent_usd':row['api_equivalent_usd'],
          'observed_tool_calls':len(row['tool_events']),'cache_key':row['key']})
    stream_save('results.json',summaries); stream_save('case_results.json',details)
    return summaries,details

def stream_oracle_checks():
    assert oracle('sorter',b'3 -1 3 0\n')==(b'-1\n0\n3\n3\n',0)
    assert oracle('sorter',b'2147483648')==(b'ERR\n',2)
    assert oracle('sorter',b'\r')==(b'ERR\n',2)
    assert oracle('rle',b'A'*256)==(bytes.fromhex('ff410141'),0)
    assert oracle('transactions',b'account,amount_cents\n17,1250\n42,-300\n17,275\n')==(b'17,1525\n42,-300\n',0)
    assert oracle('transactions',b'account,amount_cents\n1,2\n2,bad\n')==(b'ERR\n',2)
    assert oracle('transactions',b'account,amount_cents\n1,2\n\n')==(b'ERR\n',2)
    assert oracle('transactions',b'account,amount_cents\n\n')==(b'ERR\n',2)
    return True
