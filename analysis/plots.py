import pandas as pd, numpy as np, os, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0,os.path.dirname(__file__)); from stats import D, ALG, ci
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","src"))
FIG=os.path.join(os.path.dirname(__file__),"..","figures"); os.makedirs(FIG,exist_ok=True)
COL={"FCFS":"#7f7f7f","SJF":"#1f77b4","SRTF":"#17becf","RR-4":"#ff7f0e","RR-16":"#bcbd22","PRIO":"#8c564b","ADAPT":"#d62728"}
plt.rcParams.update({"font.size":8,"axes.spines.top":False,"axes.spines.right":False})
P=D[D.experiment=="principal"]
KINDS=["cpu","io","short","mixed"]
# Fig1: grouped bars, wait & response at N=200
fig,ax=plt.subplots(1,2,figsize=(7.2,2.6))
for a_i,(m,t) in enumerate((("avg_wait","Average waiting time"),("avg_resp","Average response time"))):
    for j,al in enumerate(ALG):
        g=P[(P.n==200)&(P.algo==al)].groupby("workload")[m]
        mu=[g.get_group(k).mean() for k in KINDS]; er=[ci(g.get_group(k)) for k in KINDS]
        ax[a_i].bar(np.arange(4)+(j-3)*0.12,mu,0.12,yerr=er,color=COL[al],label=al,error_kw=dict(lw=.6))
    ax[a_i].set_xticks(range(4)); ax[a_i].set_xticklabels(KINDS); ax[a_i].set_title(t+" (N=200)"); ax[a_i].set_ylabel("time units")
ax[0].legend(ncol=2,fontsize=6,frameon=False)
plt.tight_layout(); plt.savefig(f"{FIG}/fig1_bars_n200.png",dpi=200); plt.close()
# Fig2: scalability lines
S=D[D.experiment=="scalability"]
fig,ax=plt.subplots(1,3,figsize=(7.2,2.3))
for a_i,(m,t) in enumerate((("avg_wait","Avg waiting time"),("avg_resp","Avg response time"),("cs_overhead_pct","Switch overhead (%)"))):
    for al in ALG:
        g=S[S.algo==al].groupby("n")[m]; mu=g.mean(); er=g.apply(ci)
        ax[a_i].errorbar(mu.index,mu.values,yerr=er.values,color=COL[al],label=al,marker="o",ms=2,lw=1,capsize=1)
    ax[a_i].set_xscale("log"); ax[a_i].set_title(t); ax[a_i].set_xlabel("processes N (mixed)")
    if m!="cs_overhead_pct": ax[a_i].set_yscale("log")
ax[0].legend(fontsize=5.5,frameon=False,ncol=2)
plt.tight_layout(); plt.savefig(f"{FIG}/fig2_scalability.png",dpi=200); plt.close()
# Fig3: box plots, mixed N=200 waiting time
fig,ax=plt.subplots(1,2,figsize=(7.2,2.3))
for a_i,m in enumerate(("avg_wait","avg_resp")):
    d=[P[(P.n==200)&(P.workload=="mixed")&(P.algo==al)][m] for al in ALG]
    bp=ax[a_i].boxplot(d,tick_labels=ALG,patch_artist=True,flierprops=dict(ms=2),medianprops=dict(color="k"))
    for p,al in zip(bp["boxes"],ALG): p.set_facecolor(COL[al]); p.set_alpha(.7)
    ax[a_i].set_title(f"{m} spread over 30 seeds (mixed, N=200)"); ax[a_i].tick_params(axis="x",labelsize=6)
plt.tight_layout(); plt.savefig(f"{FIG}/fig3_boxplots.png",dpi=200); plt.close()
# Fig4: robustness to load and arrival pattern (mixed N=200) avg_wait
R=D[D.experiment=="robust_load"]
fig,ax=plt.subplots(1,2,figsize=(7.2,2.3),sharey=True)
for a_i,arr in enumerate(("poisson","bursty")):
    for al in ALG:
        g=R[(R.arrival==arr)&(R.algo==al)].groupby("rho")["avg_wait"]; mu=g.mean(); er=g.apply(ci)
        ax[a_i].errorbar(mu.index,mu.values,yerr=er.values,color=COL[al],label=al,marker="o",ms=2,lw=1,capsize=1)
    ax[a_i].set_title(f"{arr} arrivals (mixed, N=200)"); ax[a_i].set_xlabel("offered load rho"); ax[a_i].set_yscale("log")
ax[0].set_ylabel("avg waiting time"); ax[0].legend(fontsize=5.5,frameon=False,ncol=2)
plt.tight_layout(); plt.savefig(f"{FIG}/fig4_robustness.png",dpi=200); plt.close()
# Fig5: policy timeline for one mixed run + sensitivity
from workload_gen import generate
from sched_engine import simulate
r=simulate(generate("mixed",200,3),"ADAPT",want_timeline=True)
tl=r["timeline"]; names=["FCFS","RR","ASRTF","ASJF"]; ymap={n:i for i,n in enumerate(names)}
fig,ax=plt.subplots(1,3,figsize=(7.2,2.2),gridspec_kw=dict(width_ratios=[1.3,1,1]))
ts=[x[0] for x in tl]+[r["makespan"]]
for (a,m),b in zip(tl,ts[1:]): ax[0].hlines(ymap[m],a,b,color=COL["ADAPT"],lw=4)
ax[0].set_yticks(range(4)); ax[0].set_yticklabels(names); ax[0].set_xlabel("simulated time"); ax[0].set_title("Adaptive policy timeline (seed 3)")
W=D[D.experiment=="sens_window"]; K=D[D.experiment=="sens_k"]
for a_i,(df,t,lab) in enumerate(((W,"window length","window="),(K,"hysteresis k","k="))):
    g=df.groupby("algo")[["avg_wait","avg_resp"]]; xs=[float(x.replace(lab,"")) for x in g.mean().index]
    o=np.argsort(xs)
    ax[a_i+1].plot(np.array(xs)[o],g.mean()["avg_wait"].values[o],"o-",ms=3,color=COL["ADAPT"],label="wait")
    ax2=ax[a_i+1].twinx(); ax2.plot(np.array(xs)[o],g.mean()["avg_resp"].values[o],"s--",ms=3,color="k",label="resp")
    ax[a_i+1].set_xlabel(t); ax[a_i+1].set_title("Sensitivity (mixed, N=200)"); ax[a_i+1].set_ylabel("wait",color=COL["ADAPT"]); ax2.set_ylabel("resp")
    ax2.spines["top"].set_visible(False)
plt.tight_layout(); plt.savefig(f"{FIG}/fig5_timeline_sensitivity.png",dpi=200); plt.close()
print("figures done")
