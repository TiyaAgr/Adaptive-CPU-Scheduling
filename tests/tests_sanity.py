import sys; sys.path.insert(0,'src')  # run from repo root
from sched_engine import simulate
# P0 arr0 burst 5 ; P1 arr1 burst 3 ; P2 arr2 burst 1   (no I/O, cs=0)
w={"arr":[0,1,2],"cpu":[[5],[3],[1]],"io":[[],[],[]],"prio":[3,2,1]}
# FCFS hand: finish 5,8,9 ; wait 0,4,6 -> avg 3.333 ; resp same; TAT 5,7,7 -> 6.333
r=simulate(w,"FCFS",cs=0); print("FCFS",r["avg_wait"],r["avg_tat"],r["avg_resp"]); assert abs(r["avg_wait"]-10/3)<1e-9 and abs(r["avg_tat"]-19/3)<1e-9
# SJF hand: P0 0-5, then P2 (1) 5-6, then P1 6-9 : wait 0,5,3 =8/3 ; TAT 5,8,4=17/3
r=simulate(w,"SJF",cs=0); print("SJF",r["avg_wait"],r["avg_tat"]); assert abs(r["avg_wait"]-8/3)<1e-9
# SRTF hand: t0-1 P0(rem4); t1 P1(3) < 4 -> run P1 to? t2 P2(1)<2 -> P2 2-3; then P1 3-5 (rem2) ; P0 5-9
# finish P2=3, P1=5, P0=9 -> TAT 9,4,1 = 14/3 ; wait = TAT-burst = 4,1,0 = 5/3
r=simulate(w,"SRTF",cs=0); print("SRTF",r["avg_wait"],r["avg_tat"]); assert abs(r["avg_wait"]-5/3)<1e-9 and abs(r["avg_tat"]-14/3)<1e-9
# RR q=2 hand: t0-2 P0(3 left); t2 queue: P1(arr1),P2(arr2),P0 ; P1 2-4(1 left), P2 4-5 done, P0 5-7(1 left), P1 7-8 done, P0 8-9 done
# TAT: P0 9, P1 7, P2 3 = 19/3 ; wait = 4,4,2 = 10/3
r=simulate(w,"RR",q=2,cs=0); print("RR",r["avg_wait"],r["avg_tat"]); assert abs(r["avg_wait"]-10/3)<1e-9 and abs(r["avg_tat"]-19/3)<1e-9
# priority(1=highest), arrival tie handling: P2 prio1 arrives at 2 preempts P1 etc.
r=simulate(w,"PRIO",cs=0); print("PRIO",r["avg_wait"],r["avg_tat"])
# with cs=1: FCFS 3 dispatches
r=simulate(w,"FCFS",cs=1); print("FCFS cs=1 switches",r["ctx_switches"], r["cs_overhead_pct"])
print("ALL SANITY CHECKS PASSED")
