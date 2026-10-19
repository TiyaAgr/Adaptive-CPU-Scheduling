import sys, time; sys.path.insert(0,'src')  # run from repo root
import numpy as np
from workload_gen import generate
from sched_engine import simulate, ALGOS
def run(kind,n,seeds,metric,ck=None):
    res={a:[] for a in ALGOS}
    for s in seeds:
        w=generate(kind,n,s)
        for a,kw in ALGOS.items():
            kw=dict(kw); 
            if a=="ADAPT" and ck: kw["ctrl_kwargs"]=ck
            res[a].append(simulate(w,**kw)[metric])
    return {a:np.mean(v) for a,v in res.items()}
t=time.time()
for metric in ("avg_wait","avg_resp"):
    print(metric)
    for kind in ("cpu","io","short","mixed"):
        r=run(kind,200,range(1000,1008),metric)
        print(f"{kind:6s}"," ".join(f"{a}={v:8.2f}" for a,v in r.items()))
print("time",time.time()-t)
