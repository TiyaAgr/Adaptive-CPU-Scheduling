"""Seeded workload generator for the CPU-scheduling study.

A workload is a dict with parallel lists: arr, cpu (list of CPU bursts per
process), io (list of I/O waits between bursts, len = len(cpu)-1), prio.
Offered CPU load rho is enforced by scaling the arrival rate to the sampled
mean CPU demand, so every workload type is compared at the same utilisation.
"""
import random

KINDS = ("cpu", "io", "short", "mixed")


def _proc(kind, rng):
    if kind == "cpu":           # long, near-uniform bursts, rare I/O
        nb = 1 if rng.random() < 0.8 else 2
        cpu = [max(2.0, rng.gauss(40, 10)) for _ in range(nb)]
        io = [rng.expovariate(1 / 5.0) for _ in range(nb - 1)]
    elif kind == "io":          # many tiny bursts separated by long waits
        nb = rng.randint(6, 12)
        cpu = [0.5 + rng.expovariate(1 / 3.0) for _ in range(nb)]
        io = [rng.expovariate(1 / 15.0) for _ in range(nb - 1)]
    else:                       # short: single burst U(1,5)
        cpu, io = [rng.uniform(1, 5)], []
    return cpu, io


def generate(kind, n, seed, rho=0.85, arrival="poisson"):
    rng = random.Random(seed)
    cpus, ios = [], []
    for _ in range(n):
        k = kind
        if kind == "mixed":
            k = rng.choices(["io", "cpu", "short"], [0.4, 0.4, 0.2])[0]
        c, i = _proc(k, rng)
        cpus.append(c)
        ios.append(i)
    demand = sum(sum(c) for c in cpus) / n
    lam = rho / demand
    arr = []
    t = 0.0
    if arrival == "poisson":
        for _ in range(n):
            t += rng.expovariate(lam)
            arr.append(t)
    else:                        # bursty: batches of geometric size (mean 8)
        while len(arr) < n:
            t += rng.expovariate(lam / 8.0)
            size = 1
            while rng.random() < 7 / 8:
                size += 1
            for _ in range(min(size, n - len(arr))):
                arr.append(t + rng.random() * 0.5)
    prio = [rng.randint(1, 5) for _ in range(n)]
    return {"arr": arr, "cpu": cpus, "io": ios, "prio": prio}
