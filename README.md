# Adaptive Multi-Level CPU Scheduling

**Author:** Tiya Agrawal  
**Registration Number:** 24BDS0004  
**Course / Project:** Operating Systems – Discrete-Event CPU Scheduling Study

---

## Overview

Traditional CPU scheduling policies represent a rigid commitment to particular workload assumptions:
* **FCFS** minimizes context switching overhead but causes head-of-line blocking for short jobs (convoy effect).
* **SJF / SRTF** mathematically minimize mean waiting time, but require perfect burst-length knowledge and risk starving longer jobs.
* **Round Robin (RR)** delivers rapid initial response times but incurs significant context-switching penalties.
* **Priority with Aging** allows starvation mitigation, but random priority assignments degrade waiting efficiency.

**ADAPT** is a two-level adaptive scheduler where a **slow policy selector** sits on top of a **fast dispatcher**. It monitors runtime queue statistics in fixed observation windows and dynamically transitions between scheduling disciplines (FCFS, Aged SJF, Aged SRTF, Dynamic Round Robin) to balance waiting time, response time, and context-switch overhead across changing workload regimes.

---

## Key Features

* **Deterministic Discrete-Event Engine:** High-performance, reproducible simulation clock tracking process arrival, CPU execution, I/O blocking, and context switches.
* **Shared Simulation Core:** All policies share an identical event loop and mechanics to eliminate simulation artifacts.
* **Realistic Cost Model:** Context switches charge an explicit penalty ($cs = 0.5$ time units) only when the CPU transitions between different processes.
* **Starvation Mitigation ($O(1)$ Aging):**
  * Linear Priority aging (1 priority level gained per 20 wait units).
  * Aging for SJF modes ($\text{key} = \text{remaining burst} - 0.1 \times \text{time waited}$) using enqueue timestamp offsets to avoid $O(n)$ queue scans.
* **Stabilized Controller Architecture:**
  * **Hysteresis ($k=2$):** A candidate policy must dominate for 2 consecutive evaluation windows before triggering a switch.
  * **Congestion Guard:** Shifts to non-preemptive Aged SJF under high queue pressure ($Q \ge 10$) to prevent context-switch saturation.
  * **Dynamic Slicing:** Dynamically tunes RR quanta to median recent burst lengths ($1.5 \times$ or $2 \times$).

---

## ADAPT Policy Selection Rules

The controller samples features every window of **200 time units** ($Q$ = ready queue length, $cv$ = coefficient of variation of remaining bursts, burst distribution percentiles). Rules are evaluated in strict priority order (first match wins):

| Priority | Condition | Selected Policy | Rationale |
| :---: | :--- | :--- | :--- |
| **1** | $Q \le 1$ | **FCFS** | No contention; context switching provides zero benefit. |
| **2** | $Q \ge 10$ | **ASJF** (Aged SJF, non-preemptive) | Congestion control; minimizes switch overhead when capacity is scarce. |
| **3** | $cv \ge 0.6$ | **ASRTF** (SRTF + aging) | High burst variance; short jobs served first while aging caps starvation. |
| **4** | $cv < 0.3$ | **FCFS** | Near-uniform bursts; preemption incurs overhead without reducing wait. |
| **5** | $\ge 50\%$ bursts $\le 5$ | **RR** ($q = \text{clamp}(1.5 \cdot \text{med}, 2, 8)$) | Interactive bursts; delivers fast first service. |
| **6** | Default / Otherwise | **RR** ($q = \text{clamp}(2.0 \cdot \text{med}, 4, 32)$) | Moderate variance; slices near typical burst duration. |

---

## Repository Structure

```text
CS1_repo_NEW/
├── configs/
│   └── experiments.yaml         # Configuration parameters for all 6,640 runs
├── src/
│   ├── sched_engine.py          # Discrete-event engine, baselines & ADAPT controller
│   ├── workload_gen.py          # Synthetic workload generator (CPU, IO, Short, Mixed)
│   └── run_all.py               # Master experiment runner (produces results.csv)
├── tuning/
│   ├── tune.py                  # Initial baseline profiling
│   ├── tune2.py                 # Feature distribution profiling
│   ├── tune3.py                 # Grid search on tuning seeds 1000–1009
│   └── tune4.py                 # Congestion threshold search (q_high)
├── analysis/
│   ├── stats.py                 # Paired Wilcoxon signed-rank tests & Bonferroni adjustments
│   ├── plots.py                 # Generates publication-ready figures
│   ├── table_data.py            # Generates aggregated cell statistics (table1.json)
│   ├── mode_share.py            # Analyzes ADAPT internal state breakdown
│   └── report_numbers.py        # Summarizes key numerical metrics and rankings
├── data/
│   ├── raw/results.csv          # Raw evaluation data (6,640 rows)
│   ├── table1.json              # Formatted waiting and response times
│   ├── mode_share.json          # Percentage of time spent in each mode
│   ├── stats_output.txt         # Statistical analysis summaries
│   └── wilcoxon_adapt_vs_baselines.csv
├── figures/                     # Generated charts and diagrams
├── tests/
│   └── tests_sanity.py          # Hand-calculated analytical verification checks
└── README.md                    # Project documentation
```

---

## Reproduction Guide

### 1. Requirements

The project uses standard Python data science libraries:
```bash
pip install numpy scipy pandas matplotlib pyyaml
```

### 2. Run Sanity Checks
Verify engine mechanics against hand-computed analytical solutions for a 3-process workload (FCFS, SJF, SRTF, RR):
```bash
python tests/tests_sanity.py
```
*Expected output: `ALL SANITY CHECKS PASSED`*

### 3. Run Full Simulation Suite (6,640 Runs)
Executes all experimental sweeps (Principal study, Scalability up to $N=5000$, Load & Arrival patterns, Sensitivity studies, Switch-cost sweeps):
```bash
python src/run_all.py
```
*Writes results directly to `data/raw/results.csv` (~1 minute on standard multicore).*

### 4. Statistical Analysis & Plots
Generate Wilcoxon tests, effect sizes, summary tables, and plots:
```bash
python analysis/stats.py > data/stats_output.txt
python analysis/table_data.py
python analysis/mode_share.py
python analysis/plots.py
```
*All generated charts are saved to the `figures/` directory.*

---

## Summary of Results

* **Heterogeneous Workloads:** On `mixed` workloads, ADAPT reduces mean waiting time by **19–21%** compared to FCFS and by **24–31%** compared to RR-16 ($p < 0.001$, Bonferroni-corrected), maintaining a low context switch overhead (~6.9% vs. 12.3% for RR-4).
* **Homogeneous Workloads:** On `cpu` and `short` workloads, ADAPT naturally reduces to FCFS for 85–91% of execution time, preventing wasteful preemptions.
* **Tail Latency & Starvation:** By maintaining an aged key in shortest-job modes, ADAPT achieves the **second lowest 95th-percentile waiting time** across the benchmark suite (surpassing pure SJF and SRTF).
* **Scalability:** ADAPT switch overhead remains steady at ~7% as $N$ grows from 50 to 5,000 processes, avoiding the saturation failure seen in small-quantum Round Robin.

---

## Experimental Rigor

* **Disjoint Seed Protocol:** Controller thresholds were tuned exclusively on tuning seeds (`1000–1009`). All reported experimental evaluations were conducted across disjoint evaluation seeds (`0–29`).
* **Normalized Load:** Offered load is normalized to $\rho = 0.85$ across all workload types by scaling arrival rate $\lambda = \rho / E[D]$.
* **Statistical Testing:** Paired Wilcoxon signed-rank tests across shared seeds with Bonferroni correction for all 72 operating point comparisons.
