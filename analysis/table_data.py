import json, os, sys
sys.path.insert(0,os.path.dirname(__file__)); from stats import D, ALG
P=D[D.experiment=="principal"]; rows=[]
for wl in ("cpu","io","short","mixed"):
    for n in (50,200,1000):
        g=P[(P.workload==wl)&(P.n==n)].groupby("algo")[["avg_wait","avg_resp"]].mean()
        bw,br=g.avg_wait.min(),g.avg_resp.min()
        rows.append(dict(wl=wl,n=n,cells=[dict(w=round(g.loc[a,"avg_wait"],1),r=round(g.loc[a,"avg_resp"],1),
                         wb=bool(abs(g.loc[a,"avg_wait"]-bw)<1e-9),rb=bool(abs(g.loc[a,"avg_resp"]-br)<1e-9)) for a in ALG]))
json.dump(rows,open(os.path.join(os.path.dirname(__file__),"..","data","table1.json"),"w"))
print("ok",len(rows))
