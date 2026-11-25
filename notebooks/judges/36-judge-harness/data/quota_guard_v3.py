def error_diagnostics(out):
 parts=[]
 def add(value):
  if value:
   parts.append(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,default=str))
 def envelope(value):
  if isinstance(value,list):
   for event in value:envelope(event)
  elif isinstance(value,dict):
   kind=value.get('type')
   if kind in ('error','turn.failed') or value.get('is_error') is True:
    add(value)
   elif value.get('subtype') and value['subtype']!='success':
    add(value)
   elif kind and isinstance(value.get('item'),dict) and value['item'].get('type')=='error':
    add(value['item'])
   elif value.get('error'):
    add(value['error'])
 add(out.get('stderr'))
 add(out.get('error'))
 raw=out.get('raw')
 envelope(raw)
 for line in str(out.get('stdout') or '').splitlines():
  try:envelope(json.loads(line))
  except (ValueError,TypeError):pass
 if out.get('status',200)>=400 and isinstance(raw,dict):
  add(raw.get('error') or raw.get('message') or raw.get('unparsed_body'))
 return '\n'.join(parts)

def usage_limit_message(out):
 diagnostic=error_diagnostics(out);match=QUOTA_PATTERN.search(diagnostic)
 return diagnostic[max(0,match.start()-150):match.end()+1200] if match else None

def cli_rate_limit_message(out):
 if not isinstance(out.get('raw'),list):return None
 diagnostic=error_diagnostics(out)
 match=re.search(r'exceeded\s+retry\s+limit[^\n]{0,200}\b429\b',diagnostic,re.I)
 return diagnostic[max(0,match.start()-150):match.end()+1200] if match else None

def quota_message(out):
 return usage_limit_message(out) or cli_rate_limit_message(out)
