class ScheduledGate:
 def __init__(self,*gates):self.gates=gates
 def __enter__(self):
  self.acquired=[]
  try:
   for gate in self.gates:gate.acquire();self.acquired.append(gate)
  except BaseException:
   for gate in reversed(self.acquired):gate.release()
   raise
  return self
 def __exit__(self,*exc):
  for gate in reversed(self.acquired):gate.release()

sol_request_gate=threading.Semaphore(1)
