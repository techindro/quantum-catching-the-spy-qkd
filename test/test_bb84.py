"""Small sanity checks for bb84_sim.py.

Run with:  pytest            (or)   python tests/test_bb84.py
"""
import os
import sys

import numpy as np
from qiskit_aer import AerSimulator

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from bb84_sim import run_bb84  # noqa: E402

SIM = AerSimulator(method="stabilizer")


def qber_values(n, attack, runs, seed=2026):
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(runs):
        result = run_bb84(n, attack, rng, SIM)
        if result is not None:
            values.append(result[0])
    return np.array(values)


def test_secure_channel_has_zero_qber():
    # Ideal channel and no spy: Advik and Bhaskar always agree on the sifted key.
    assert np.all(qber_values(100, attack=False, runs=20) == 0.0)


def test_attack_gives_about_25_percent_qber():
    # Full measure-and-resend attack: expected QBER is 25 % (mean over many runs).
    mean_qber = qber_values(200, attack=True, runs=60).mean()
    assert 22.0 < mean_qber < 28.0


def test_attack_is_detected_with_long_key():
    # With 500 qubits the 15 % abort rule should reject every attacked session.
    assert np.all(qber_values(500, attack=True, runs=10) > 15.0)


if __name__ == "__main__":
    test_secure_channel_has_zero_qber()
    test_attack_gives_about_25_percent_qber()
    test_attack_is_detected_with_long_key()
    print("All tests passed")
