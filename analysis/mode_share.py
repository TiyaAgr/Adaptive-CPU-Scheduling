import sys, os; sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","src"))
from workload_gen import generate; from sched_engine import simulate
from collections import defaultdict
import json
out={}
for kind in ("cpu","io","short","mixed"):
    for n in (200,1000):
        tot=defaultdict(float); T=0
        for s in range(30):
            r=simulate(generate(kind,n,s),"ADAPT",want_timeline=True); tl=r["timeline"]+[(r["makespan"],"end")]
            for (a,m),(b,_) in zip(tl,tl[1:]): tot[m]+=b-a
            T+=r["makespan"]
        out[f"{kind}-{n}"]={m:round(100*v/T,1) for m,v in tot.items()}
        print(kind,n,out[f"{kind}-{n}"])
json.dump(out,open(os.path.join(os.path.dirname(__file__),"..","data","mode_share.json"),"w"),indent=1)
