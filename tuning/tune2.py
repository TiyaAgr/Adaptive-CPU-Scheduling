import sys; sys.path.insert(0,'src')  # run from repo root
import numpy as np
from workload_gen import generate
from sched_engine import simulate, AdaptiveController
import statistics
# record features at each window for diagnosis
import sched_engine as se
orig=se.AdaptiveController.desired
log=[]
def dbg(self,rems):
    r=orig(self,rems); Q=len(rems)
    if Q>0:
        m=sum(rems)/Q; cv=statistics.pstdev(rems)/m if m>0 else 0
        h=self.hist; sh=sum(1 for x in h if x<=self.short_thr)/len(h) if h else 0
        log.append((Q,cv,sh,r[0]))
    return r
se.AdaptiveController.desired=dbg
for kind in ("cpu","io","short","mixed"):
    log.clear()
    for s in range(1000,1005): simulate(generate(kind,200,s),"ADAPT")
    a=np.array([(x[0],x[1],x[2]) for x in log]); modes=[x[3] for x in log]
    from collections import Counter
    print(kind,"windows",len(log),"Q med",np.median(a[:,0]),"cv med %.2f p10 %.2f p90 %.2f"%(np.median(a[:,1]),*np.percentile(a[:,1],[10,90])),"short med %.2f"%np.median(a[:,2]),dict(Counter(modes)))
