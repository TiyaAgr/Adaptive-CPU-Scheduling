import sys, itertools; sys.path.insert(0,'src')  # run from repo root
import numpy as np
from workload_gen import generate
from sched_engine import simulate, ALGOS
seeds=range(1000,1010); kinds=("cpu","io","short","mixed")
W={(k,s):generate(k,200,s) for k in kinds for s in seeds}
base={}
for (k,s),w in W.items():
    for a,kw in ALGOS.items():
        if a=="ADAPT": continue
        r=simulate(w,**kw); base[(k,s,a)]=(r["avg_wait"],r["avg_resp"])
def score(ck):
    tot=[]
    for (k,s),w in W.items():
        r=simulate(w,"ADAPT",ctrl_kwargs=ck)
        bw=min(base[(k,s,a)][0] for a in ALGOS if a!="ADAPT"); br=min(base[(k,s,a)][1] for a in ALGOS if a!="ADAPT")
        tot.append(0.5*np.log(r["avg_wait"]/bw)+0.5*np.log(r["avg_resp"]/br))
    return float(np.exp(np.mean(tot)))
res=[]
for cv_lo,cv_hi,q_low,short_hi in itertools.product((0.3,0.5,0.7),(0.6,0.8,1.0),(1,2,4),(0.5,0.7,1.1)):
    if cv_lo>=cv_hi: continue
    ck=dict(cv_lo=cv_lo,cv_hi=cv_hi,q_low=q_low,short_hi=short_hi)
    res.append((score(ck),ck))
res.sort(key=lambda x:x[0])
print("default",score({}))
for sc,ck in res[:6]: print(round(sc,3),ck)
print("worst",round(res[-1][0],3),res[-1][1])
