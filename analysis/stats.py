import pandas as pd, numpy as np, os
from scipy import stats
D=pd.read_csv(os.path.join(os.path.dirname(__file__),"..","data","raw","results.csv"))
ALG=["FCFS","SJF","SRTF","RR-4","RR-16","PRIO","ADAPT"]
def ci(x):
    x=np.asarray(x); return stats.t.ppf(.975,len(x)-1)*x.std(ddof=1)/np.sqrt(len(x))
def summary(df,metrics):
    g=df.groupby(["workload","n","algo"])[metrics].agg(["mean",ci]); return g
def paired(df,metric,a="ADAPT"):
    """Paired Wilcoxon (two-sided) of ADAPT vs each baseline over seeds; returns dataframe."""
    out=[]
    for (wl,n),g in df.groupby(["workload","n"]):
        pv=g.pivot(index="seed",columns="algo",values=metric)
        for b in ALG[:-1]:
            d=pv[a]-pv[b]
            if np.allclose(d,0): p=1.0
            else: p=stats.wilcoxon(pv[a],pv[b]).pvalue
            out.append(dict(workload=wl,n=n,baseline=b,metric=metric,mean_adapt=pv[a].mean(),mean_base=pv[b].mean(),
                            rel_change_pct=100*(pv[a].mean()/pv[b].mean()-1),p=p,dz=d.mean()/d.std(ddof=1) if d.std(ddof=1)>0 else 0.0))
    r=pd.DataFrame(out); r["p_bonf"]=np.minimum(1,r.p*len(r)); return r
if __name__=="__main__":
    P=D[D.experiment=="principal"]
    pd.set_option("display.width",250); pd.set_option("display.max_columns",30)
    for n in (50,200,1000):
        print("\n=== N=",n)
        t=P[P.n==n].groupby(["workload","algo"])[["avg_wait","avg_resp","throughput","ctx_switches","cs_overhead_pct","p95_wait","jain"]].mean().round(2)
        for wl in ("cpu","io","short","mixed"):
            print(wl); print(t.loc[wl].loc[ALG])
    allp=pd.concat([paired(P,m) for m in ("avg_wait","avg_resp","throughput","ctx_switches","p95_wait")])
    allp.to_csv(os.path.join(os.path.dirname(__file__),"..","data","wilcoxon_adapt_vs_baselines.csv"),index=False)
    sig=allp[allp.p_bonf<0.05]
    print("\nSignificant (Bonferroni within metric) counts: better(ADAPT lower wait/resp/ctx/p95, higher thr) vs worse")
    for m in allp.metric.unique():
        s=allp[(allp.metric==m)]
        lower_better = m!="throughput"
        sg=s[s.p_bonf<0.05]
        better=(sg.rel_change_pct<0) if lower_better else (sg.rel_change_pct>0)
        print(m,"total",len(s),"sig",len(sg),"adapt better",int(better.sum()),"adapt worse",int((~better).sum()))
