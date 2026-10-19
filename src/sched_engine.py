"""Discrete-event CPU scheduling simulator (single CPU, I/O overlapped).

One engine runs every policy so all algorithms see identical mechanics:
  FCFS  non-preemptive, arrival order
  SJF   non-preemptive, shortest next CPU burst
  SRTF  preemptive SJF (re-evaluated on every arrival / I/O completion)
  RR    round robin, fixed quantum
  PRIO  preemptive priority (1 = highest) with linear aging
  ADAPT adaptive selector (see AdaptiveController)
Waiting time = total time spent in the ready queue (incl. context-switch
time charged to the dispatched process). A context switch costs `cs` time
units whenever the dispatched process differs from the last one that ran.
"""
import heapq
import statistics

INF = float("inf")


class AdaptiveController:
    """Window-based policy selector with hysteresis and a dynamic quantum.

    Observable features (sampled every `window` time units):
      Q      ready-queue length
      cv     coefficient of variation of remaining CPU bursts in the queue
      short  fraction of CPU bursts completed in the window that were <= short_thr
      med    median length of those completed bursts
    Rules (first match wins):
      Q <= q_low        -> FCFS   (no contention: avoid switches)
      Q >= q_high       -> ASJF   (congestion: non-preemptive aged SJF, fewest switches)
      cv >= cv_hi       -> ASRTF  (SRTF with aging: short jobs first, bounded starvation)
      cv <  cv_lo       -> FCFS   (near-uniform bursts: preemption buys nothing)
      short >= short_hi -> RR, quantum 1.5*med clamped to [2, 8]
      otherwise         -> RR, quantum 2*med clamped to [4, 32]
    A new policy must win `k` consecutive windows before a switch (hysteresis).
    """

    def __init__(self, window=200.0, k=2, q_low=1, cv_hi=0.6, cv_lo=0.3,
                 short_thr=5.0, short_hi=0.5, q_high=10):
        self.window, self.k = window, k
        self.q_low, self.cv_hi, self.cv_lo, self.q_high = q_low, cv_hi, cv_lo, q_high
        self.short_thr, self.short_hi = short_thr, short_hi
        self.next_eval = window
        self.hist = []
        self.pending, self.streak = None, 0
        self.timeline = []

    def note_burst(self, length):
        self.hist.append(length)

    def desired(self, rems):
        Q = len(rems)
        if Q <= self.q_low:
            return "FCFS", None
        if Q >= self.q_high:
            return "ASJF", None
        mean = sum(rems) / Q
        cv = statistics.pstdev(rems) / mean if mean > 0 else 0.0
        if cv >= self.cv_hi:
            return "ASRTF", None
        if cv < self.cv_lo:
            return "FCFS", None
        h = self.hist
        if len(h) >= 3:
            med = statistics.median(h)
            short = sum(1 for x in h if x <= self.short_thr) / len(h)
        else:
            med, short = 8.0, 0.0
        if short >= self.short_hi:
            return "RR", min(8.0, max(2.0, 1.5 * med))
        return "RR", min(32.0, max(4.0, 2.0 * med))

    def step(self, t, rems, cur_mode):
        if t < self.next_eval:
            return None
        self.next_eval = t + self.window
        want, q = self.desired(rems)
        self.hist = []
        if want == cur_mode:
            self.pending, self.streak = None, 0
            return want, q
        if want == self.pending:
            self.streak += 1
        else:
            self.pending, self.streak = want, 1
        if self.streak >= self.k:
            self.pending, self.streak = None, 0
            self.timeline.append((t, want))
            return want, q
        return None


def simulate(w, algo, q=4.0, cs=0.5, aging=20.0, alpha=0.1, ctrl_kwargs=None,
             want_timeline=False):
    n = len(w["arr"])
    arr, cpu, io, prio = w["arr"], w["cpu"], w["io"], w["prio"]
    order = sorted(range(n), key=lambda i: arr[i])
    ai = 0
    wake = []
    bi = [0] * n
    rem = [cpu[i][0] for i in range(n)]
    rs = [0.0] * n
    wait = [0.0] * n
    first = [None] * n
    fin = [0.0] * n
    ready = []
    seq = 0

    ctrl = AdaptiveController(**(ctrl_kwargs or {})) if algo == "ADAPT" else None
    mode = "FCFS" if algo == "ADAPT" else algo
    curq = q
    if ctrl:
        ctrl.timeline.append((0.0, mode))

    def mk(i):
        nonlocal seq
        seq += 1
        if mode in ("FCFS", "RR"):
            return (0.0, seq, i)
        if mode in ("SJF", "SRTF"):
            return (rem[i], seq, i)
        if mode in ("ASRTF", "ASJF"):
            return (rem[i] + alpha * rs[i], seq, i)   # rem - alpha*(t - rs) up to a constant
        return (prio[i] + rs[i] / aging, seq, i)       # PRIO with linear aging

    def push(i, tm):
        rs[i] = tm
        heapq.heappush(ready, mk(i))

    def admit(upto):
        nonlocal ai
        while True:
            ta = arr[order[ai]] if ai < n else INF
            tw = wake[0][0] if wake else INF
            if min(ta, tw) > upto:
                return
            if ta <= tw:
                push(order[ai], ta)
                ai += 1
            else:
                tm, i = heapq.heappop(wake)
                push(i, tm)

    def next_event():
        ta = arr[order[ai]] if ai < n else INF
        tw = wake[0][0] if wake else INF
        return min(ta, tw)

    t = 0.0
    last = -1
    busy = 0.0
    cs_n = 0
    done = 0
    t0 = min(arr)
    while done < n:
        admit(t)
        if not ready:
            t = next_event()
            continue
        if ctrl:
            res = ctrl.step(t, [rem[e[2]] for e in ready], mode)
            if res:
                newmode, nq = res
                if nq:
                    curq = nq
                if newmode != mode:
                    mode = newmode
                    items = sorted((e[2] for e in ready), key=lambda x: rs[x])
                    ready.clear()
                    for x in items:
                        ready.append(mk(x))
                    heapq.heapify(ready)
        e = heapq.heappop(ready)
        i = e[2]
        if i != last:
            t += cs
            cs_n += 1
            admit(t)
        wait[i] += t - rs[i]
        if first[i] is None:
            first[i] = t
        r = rem[i]
        if mode == "RR":
            run = min(curq, r)
        elif mode in ("SRTF", "PRIO", "ASRTF"):
            ne = next_event()
            run = min(r, ne - t) if ne > t else r
        else:
            run = r
        t += run
        busy += run
        rem[i] = r - run
        last = i
        if rem[i] <= 1e-9:
            if ctrl:
                ctrl.note_burst(cpu[i][bi[i]])
            bi[i] += 1
            if bi[i] == len(cpu[i]):
                fin[i] = t
                done += 1
            else:
                rem[i] = cpu[i][bi[i]]
                heapq.heappush(wake, (t + io[i][bi[i] - 1], i))
        else:
            admit(t)
            push(i, t)

    makespan = t - t0
    tat = [fin[i] - arr[i] for i in range(n)]
    resp = [first[i] - arr[i] for i in range(n)]
    svc = [sum(cpu[i]) + sum(io[i]) for i in range(n)]
    x = [svc[i] / tat[i] for i in range(n)]
    jain = sum(x) ** 2 / (n * sum(v * v for v in x))
    ws = sorted(wait)
    out = {
        "avg_wait": sum(wait) / n,
        "p95_wait": ws[min(n - 1, int(0.95 * n))],
        "avg_tat": sum(tat) / n,
        "avg_resp": sum(resp) / n,
        "throughput": n / makespan,
        "cpu_util": busy / makespan,
        "ctx_switches": cs_n,
        "cs_overhead_pct": 100.0 * cs_n * cs / makespan,
        "jain": jain,
        "makespan": makespan,
    }
    if ctrl and want_timeline:
        out["timeline"] = ctrl.timeline
    return out


ALGOS = {
    "FCFS": dict(algo="FCFS"),
    "SJF": dict(algo="SJF"),
    "SRTF": dict(algo="SRTF"),
    "RR-4": dict(algo="RR", q=4.0),
    "RR-16": dict(algo="RR", q=16.0),
    "PRIO": dict(algo="PRIO"),
    "ADAPT": dict(algo="ADAPT"),
}
