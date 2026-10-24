"""
BB84 quantum key distribution with a measure-and-resend eavesdropper (Qiskit AerSimulator).

Parties: Advik (sender), Bhaskar (receiver), Ekta (eavesdropper).

Usage:
    python bb84_sim.py                # full Monte Carlo of the paper (takes several minutes)
    python bb84_sim.py --quick        # a few runs per n, only to check that everything works
    python bb84_sim.py --out results  # folder for the CSV files (default: results)

Output:
    <out>/monte_carlo_runs.csv     one row per session (n, channel, run, QBER, sifted length)
    <out>/table_x_summary.csv      summary per n for the attacked channel (Table X of the paper)
"""
import argparse
import os
import time

import numpy as np
import pandas as pd
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

SEED = 2026
ABORT_THRESHOLD = 15.0                      # abort when QBER > 15 %
N_VALUES = [10, 20, 30, 40, 50, 100, 200, 500, 1000]
RUNS_SMALL, RUNS_LARGE = 1000, 333          # runs per n: 1000 for n <= 100, 333 for n >= 200


def run_bb84(n, attack, rng, sim):
    """One BB84 session with n qubits and a single shot.

    Returns (QBER in %, sifted length m), or None when no position survives sifting.
    """
    bits = rng.integers(0, 2, n)            # Advik's bits
    a_bases = rng.integers(0, 2, n)         # 0 = '+' (rectilinear), 1 = 'x' (diagonal)
    e_bases = rng.integers(0, 2, n)         # Ekta's bases
    b_bases = rng.integers(0, 2, n)         # Bhaskar's bases

    qc = QuantumCircuit(n, n)
    for i in range(n):
        if bits[i]:                         # Stage 1: state preparation
            qc.x(i)
        if a_bases[i]:
            qc.h(i)
        if attack:                          # Stage 2: measure and resend
            if e_bases[i]:
                qc.h(i)
            qc.measure(i, i)
            if e_bases[i]:
                qc.h(i)
        if b_bases[i]:                      # Stage 3: Bhaskar measures
            qc.h(i)
        qc.measure(i, i)

    seed = int(rng.integers(0, 2**31 - 1))
    memory = sim.run(qc, shots=1, memory=True, seed_simulator=seed).result().get_memory()[0]
    b_bits = np.frombuffer(memory[::-1].encode(), dtype=np.uint8) - 48   # index i = qubit i

    keep = a_bases == b_bases               # Stage 4: sifting
    m = int(keep.sum())
    if m == 0:
        return None
    errors = int((bits[keep] != b_bits[keep]).sum())
    return 100.0 * errors / m, m


def main():
    parser = argparse.ArgumentParser(description="BB84 Monte Carlo simulation with an eavesdropper")
    parser.add_argument("--quick", action="store_true", help="few runs per n (for a fast check)")
    parser.add_argument("--out", default="results", help="output folder for the CSV files")
    args = parser.parse_args()

    runs_small, runs_large = (40, 15) if args.quick else (RUNS_SMALL, RUNS_LARGE)
    os.makedirs(args.out, exist_ok=True)

    sim = AerSimulator(method="stabilizer")
    rng = np.random.default_rng(SEED)

    records, summary = [], []
    start = time.time()
    for n in N_VALUES:
        runs = runs_small if n <= 100 else runs_large
        attacked_qber, excluded = [], 0
        for channel, attack in (("secure", False), ("attacked", True)):
            for run in range(runs):
                result = run_bb84(n, attack, rng, sim)
                if result is None:
                    if attack:
                        excluded += 1
                    continue
                qber, m = result
                records.append({"n": n, "channel": channel, "run": run, "qber_percent": qber, "sifted_length": m})
                if attack:
                    attacked_qber.append(qber)
        a = np.array(attacked_qber)
        summary.append({
            "n": n,
            "runs": len(a),
            "excluded_runs": excluded,
            "mean_qber_percent": round(a.mean(), 2),
            "sd_percent": round(a.std(ddof=1), 2),
            "range_95_low": round(np.percentile(a, 2.5), 1),
            "range_95_high": round(np.percentile(a, 97.5), 1),
            "aborted_percent": round(100 * np.mean(a > ABORT_THRESHOLD), 1),
        })
        s = summary[-1]
        print(f"n={n:5d} runs={s['runs']:5d} mean={s['mean_qber_percent']:6.2f}% sd={s['sd_percent']:6.2f} "
              f"aborted={s['aborted_percent']:5.1f}%  [{time.time() - start:5.0f} s]")

    pd.DataFrame(records).to_csv(os.path.join(args.out, "monte_carlo_runs.csv"), index=False)
    pd.DataFrame(summary).to_csv(os.path.join(args.out, "table_x_summary.csv"), index=False)
    print(f"Saved results to '{args.out}/'")


if __name__ == "__main__":
    main()
