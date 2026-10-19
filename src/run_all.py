"""Runs every experiment and writes one tidy CSV (one row per algorithm x workload x seed)."""
import sys, os, csv, time
sys.path.insert(0, os.path.dirname(__file__))
from workload_gen import generate
from sched_engine import simulate, ALGOS

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "results.csv")
KINDS = ("cpu", "io", "short", "mixed")
rows = []

def one(exp, kind, n, seed, rho=0.85, arrival="poisson", cs=0.5, algos=None, ck=None, label=None):
    w = generate(kind, n, seed, rho=rho, arrival=arrival)
    for a, kw in (algos or ALGOS).items():
        kw = dict(kw)
        if a == "ADAPT" and ck:
            kw["ctrl_kwargs"] = ck
        r = simulate(w, cs=cs, **kw)
        r.update(experiment=exp, workload=kind, n=n, seed=seed, rho=rho, arrival=arrival,
                 cs=cs, algo=label or a)
        rows.append(r)

t0 = time.time()
S = range(30)
for kind in KINDS:                                    # E1 principal
    for n in (50, 200, 1000):
        for s in S: one("principal", kind, n, s)
print("E1", round(time.time() - t0), "s", flush=True)
for n in (50, 100, 200, 500, 1000, 2000, 5000):       # E2 scalability
    for s in range(10): one("scalability", "mixed", n, s)
print("E2", round(time.time() - t0), "s", flush=True)
for rho in (0.5, 0.7, 0.85, 0.95):                    # E3 robustness: load x arrival pattern
    for arr in ("poisson", "bursty"):
        for s in S: one("robust_load", "mixed", 200, s, rho=rho, arrival=arr)
for kind in KINDS:                                    # E3b bursty arrivals, all workloads
    for s in S: one("robust_bursty", kind, 200, s, arrival="bursty")
print("E3", round(time.time() - t0), "s", flush=True)
only = {"ADAPT": ALGOS["ADAPT"]}
for wdw in (50, 100, 200, 400, 800):                  # E4 sensitivity
    for s in S: one("sens_window", "mixed", 200, s, algos=only, ck=dict(window=float(wdw)), label=f"window={wdw}")
for k in (1, 2, 3, 4):
    for s in S: one("sens_k", "mixed", 200, s, algos=only, ck=dict(k=k), label=f"k={k}")
for cs in (0.1, 0.5, 1.0, 2.0):                       # E5 context-switch cost, all algorithms
    for s in S: one("cs_cost", "mixed", 200, s, cs=cs)
print("E4/E5", round(time.time() - t0), "s", flush=True)
keys = sorted({k for r in rows for k in r})
with open(OUT, "w", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=keys); wr.writeheader(); wr.writerows(rows)
print("rows", len(rows))
