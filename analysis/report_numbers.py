import pandas as pd, numpy as np, sys, os
sys.path.insert(0,os.path.dirname(__file__)); from stats import D, ALG, ci, paired
pd.set_option("display.width",250); pd.set_option("display.max_columns",30)
P=D[D.experiment=="principal"]
for m in ("avg_wait","avg_resp"):
    print("\n",m,"means (rows workload,N)")
    t=P.groupby(["workload","n","algo"])[m].mean().unstack()[ALG].round(1); t["ADAPT_rank"]=t.rank(axis=1).ADAPT; print(t)
print("\nthroughput x1000 & ctx & overhead N=200 mixed/cpu"); 
print((P[P.n==1000].groupby(["workload","algo"])["throughput"].mean().unstack()[ALG]*1000).round(2))
print(P[P.n==200].groupby(["workload","algo"])["cs_overhead_pct"].mean().unstack()[ALG].round(1))
print("\nADAPT mean rank (wait) across 12 cells:", P.groupby(["workload","n","algo"])["avg_wait"].mean().unstack()[ALG].rank(axis=1).mean().round(2).to_dict())
print("ADAPT mean rank (resp):", P.groupby(["workload","n","algo"])["avg_resp"].mean().unstack()[ALG].rank(axis=1).mean().round(2).to_dict())
print("ADAPT mean rank (p95):", P.groupby(["workload","n","algo"])["p95_wait"].mean().unstack()[ALG].rank(axis=1).mean().round(2).to_dict())
print("ADAPT mean rank (jain, high=better):", P.groupby(["workload","n","algo"])["jain"].mean().unstack()[ALG].rank(axis=1,ascending=False).mean().round(2).to_dict())
w=pd.read_csv("data/wilcoxon_adapt_vs_baselines.csv")
for m in ("avg_wait","avg_resp"):
    x=w[w.metric==m]; print("\n",m,"ADAPT vs baseline: cells where ADAPT sig better / sig worse / n.s. (of 12)")
    for b in ALG[:-1]:
        s=x[x.baseline==b]; print(b, int(((s.p_bonf<.05)&(s.rel_change_pct<0)).sum()), int(((s.p_bonf<.05)&(s.rel_change_pct>0)).sum()), int((s.p_bonf>=.05).sum()))
print("\nADAPT vs FCFS mean rel change wait by cell"); print(w[(w.metric=='avg_wait')&(w.baseline=='FCFS')][["workload","n","rel_change_pct","p_bonf","dz"]].round(3))
print("\nADAPT vs RR-16 wait"); print(w[(w.metric=='avg_wait')&(w.baseline=='RR-16')][["workload","n","rel_change_pct","p_bonf","dz"]].round(3))
print("\nADAPT vs SRTF/SJF wait mixed"); print(w[(w.metric=='avg_wait')&(w.baseline.isin(['SJF','SRTF']))&(w.workload=='mixed')][["baseline","n","rel_change_pct","p_bonf","dz"]].round(3))
S=D[D.experiment=="scalability"]
print("\nscalability wait"); print(S.groupby(["n","algo"])["avg_wait"].mean().unstack()[ALG].round(0))
print(S.groupby(["n","algo"])["cs_overhead_pct"].mean().unstack()[ALG].round(1))
R=D[D.experiment=="robust_load"]
print("\nrobust wait"); print(R.groupby(["arrival","rho","algo"])["avg_wait"].mean().unstack()[ALG].round(0))
print(R.groupby(["arrival","rho","algo"])["avg_resp"].mean().unstack()[ALG].round(0))
B=D[D.experiment=="robust_bursty"]; print("\nbursty wait"); print(B.groupby(["workload","algo"])["avg_wait"].mean().unstack()[ALG].round(0))
C=D[D.experiment=="cs_cost"]; print("\ncs cost wait"); print(C.groupby(["cs","algo"])["avg_wait"].mean().unstack()[ALG].round(0))
print(C.groupby(["cs","algo"])["avg_resp"].mean().unstack()[ALG].round(0))
print("\nsens"); 
for e in ("sens_window","sens_k"): print(D[D.experiment==e].groupby("algo")[["avg_wait","avg_resp","ctx_switches"]].mean().round(1))
