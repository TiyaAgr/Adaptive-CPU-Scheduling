import sys; sys.path.insert(0,'src')  # run from repo root
import numpy as np
from workload_gen import generate
from sched_engine import simulate, ALGOS
seeds=range(1000,1006); kinds=("cpu","io","short","mixed"); sizes=(200,600)
W={(k,n,s):generate(k,n,s) for k in kinds for n in sizes for s in seeds}
base={}
for key,w in W.items():
    for a,kw in ALGOS.items():
        if a=="ADAPT": continue
        r=simulate(w,**kw); base[key+(a,)]=(r["avg_wait"],r["avg_resp"])
def score(ck):
    tot={k:[] for k in kinds}
    for (k,n,s),w in W.items():
        r=simulate(w,"ADAPT",ctrl_kwargs=ck)
        bw=min(base[(k,n,s,a)][0] for a in ALGOS if a!="ADAPT"); br=min(base[(k,n,s,a)][1] for a in ALGOS if a!="ADAPT")
        tot[k].append(0.5*np.log(r["avg_wait"]/bw)+0.5*np.log(r["avg_resp"]/br))
    return float(np.exp(np.mean([np.mean(v) for v in tot.values()]))), {k:round(float(np.exp(np.mean(v))),2) for k,v in tot.items()}
base_ck=dict(cv_lo=0.3,cv_hi=0.6,q_low=1,short_hi=0.5)
for qh in (1e9,10,20,40,80):
    print("q_high",qh,score(dict(base_ck,q_high=qh)))
