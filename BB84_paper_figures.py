# BB84 paper figures: Google Colab version
# How to use: open colab.research.google.com -> New notebook.
# Copy each block between the "CELL n" lines into its own cell, in order, and run them.
# (Or upload BB84_paper_figures.ipynb with File -> Upload notebook.)

# ----------------------------------------------------------------------
# # Catching the Spy: code for all figures
#
# This notebook regenerates every figure of the paper *"Catching the Spy: Eavesdropper Detection Analysis in Quantum Key Distribution Networks Using Qiskit"* (BB84, Qiskit AerSimulator).
#
# | Figure | What it shows | Source of the data |
# |--------|---------------|--------------------|
# | Fig. 1 | Expected QBER vs. fraction of intercepted qubits | Analytical (QBER = f/4) |
# | Fig. 2 | Workflow of the simulated BB84 network | Drawn with matplotlib |
# | Fig. 3 | QBER for 10 to 50 qubits, one run per n | Qiskit simulation |
# | Fig. 4 | Monte Carlo mean QBER ± 1 s.d. (10 to 1000 qubits) | Qiskit simulation |
# | Fig. 5 | Probability that an attack is not detected | Analytical curves + Monte Carlo markers |
# | Fig. 6 | Error rate by party vs. the 15% abort threshold | Values from the short run |
#
# **How to use:** run the cells from top to bottom (`Runtime → Run all`). All PNG files are saved in the `figures/` folder. The Monte Carlo cell is the slow one; set `QUICK_TEST = True` in the settings cell first if you only want to check that everything works.
# ----------------------------------------------------------------------

# %% ===================== CELL 1 (code) =====================
# Install the libraries (about one minute on Colab).
# If running in Colab, uncomment the next line to install dependencies:
# !pip install -q qiskit qiskit-aer matplotlib numpy scipy pandas

# The paper used Python 3.12.3, Qiskit 2.6.1 and Qiskit Aer 0.18.0.
# To use exactly those versions, run this instead:
# !pip install -q qiskit==2.6.1 qiskit-aer==0.18.0

# %% ===================== CELL 2 (code) =====================
import os, time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from scipy.stats import binom
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# ---------------- settings (Table VII of the paper) ----------------
SEED = 2026                       # random seed
ABORT_THRESHOLD = 15.0            # abort when QBER > 15 %
ASYMPTOTIC_BOUND = 11.0           # asymptotic QBER bound for BB84 (about 11 %)
N_VALUES = [10, 20, 30, 40, 50, 100, 200, 500, 1000]
RUNS_SMALL, RUNS_LARGE = 1000, 333  # runs per n: 1000 for n <= 100, 333 for n >= 200

QUICK_TEST = False                # True = only a few runs, just to check the code
if QUICK_TEST:
    RUNS_SMALL, RUNS_LARGE = 40, 15

# ---------------- plot style ----------------
OUT_DIR = "figures"
os.makedirs(OUT_DIR, exist_ok=True)
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "figure.dpi": 110,
})
GREEN, RED, NAVY, ORANGE = "#2e7d32", "#d32f2f", "#1a237e", "#ff7f0e"

def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    print("saved:", path)

# ----------------------------------------------------------------------
# ## Fig. 1: Expected QBER for partial interception (analytical)
#
# If Ekta intercepts only a fraction *f* of the qubits, the expected QBER on the sifted key is *f*/4.
# ----------------------------------------------------------------------

# %% ===================== CELL 3 (code) =====================
f = np.linspace(0, 100, 201)          # % of qubits intercepted
expected_qber = 0.25 * f              # QBER = f/4

f_at_abort = ABORT_THRESHOLD / 0.25        # 60 %
f_at_bound = ASYMPTOTIC_BOUND / 0.25       # 44 %

fig, ax = plt.subplots(figsize=(8, 4.2))
ax.plot(f, expected_qber, color=RED, lw=1.8, label="Expected QBER = 0.25 f")
ax.axhline(ABORT_THRESHOLD, color=ORANGE, ls=":", lw=1.8, label="Abort threshold (15%)")
ax.axhline(ASYMPTOTIC_BOUND, color="black", ls="--", lw=1.0, label="Asymptotic bound (about 11%)")
ax.plot(f_at_abort, ABORT_THRESHOLD, "o", color=ORANGE, zorder=5)
ax.plot(f_at_bound, ASYMPTOTIC_BOUND, "o", color=NAVY, zorder=5)
ax.annotate(f"f = {f_at_abort:.0f}%", (f_at_abort, ABORT_THRESHOLD), xytext=(0, 8),
            textcoords="offset points", ha="center", fontsize=8)
ax.annotate(f"f = {f_at_bound:.0f}%", (f_at_bound, ASYMPTOTIC_BOUND), xytext=(0, 8),
            textcoords="offset points", ha="center", fontsize=8)
ax.set_xlim(0, 100); ax.set_ylim(0, 30)
ax.set_xlabel("Fraction of Qubits Intercepted by Ekta, f (%)")
ax.set_ylabel("Expected QBER on Sifted Key (%)")
ax.set_title("Partial Interception: Expected QBER (Analytical)", fontweight="bold", fontsize=10)
ax.legend(loc="upper left", fontsize=8)
save(fig, "fig1_partial_interception.png")
plt.show()

# ----------------------------------------------------------------------
# ## Fig. 2: Workflow of the simulated BB84 network
#
# Drawn directly with matplotlib, so no external drawing tool is needed.
# ----------------------------------------------------------------------

# %% ===================== CELL 4 (code) =====================
def box(ax, x, y, w, h, text, edge, face, fontsize=9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                lw=1.8, edgecolor=edge, facecolor=face))
    ax.text(x + w/2, y + h/2, text, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color=edge)

fig, ax = plt.subplots(figsize=(8.4, 4.6))
ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")

# nodes
box(ax, 0.4, 2.6, 2.4, 1.4, "Advik\nKey sender\n(encoder)", NAVY, "#dfe9ff")
box(ax, 7.2, 2.6, 2.4, 1.4, "Bhaskar\nKey receiver\n(beam splitter)", NAVY, "#dfe9ff")
box(ax, 4.1, 0.4, 1.8, 1.1, "Ekta\nEavesdropper", RED, "#ffe3e3")
box(ax, 0.4, 0.4, 2.0, 1.3, "Intrusion alert\nQBER > 15%\nabort key", RED, "#ffe3e3", fontsize=8.5)

# quantum channel (blue): up from Advik, across, down into Bhaskar
ax.plot([1.6, 1.6, 8.4], [4.0, 5.2, 5.2], color=NAVY, lw=2)
ax.annotate("", xy=(8.4, 4.05), xytext=(8.4, 5.2), arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=2))
ax.text(5.0, 5.4, "Quantum channel (photon stream)", ha="center", color=NAVY, fontweight="bold", fontsize=10)

# public classical channel (green, both directions)
ax.annotate("", xy=(7.2, 3.3), xytext=(2.8, 3.3),
            arrowprops=dict(arrowstyle="<|-|>", color=GREEN, lw=2))
ax.text(3.9, 3.45, "Public classical\nchannel", ha="center", va="bottom", color=GREEN, fontweight="bold", fontsize=8.5)
ax.text(6.25, 3.0, "(basis comparison)", ha="center", color=GREEN, fontsize=8)

# Ekta's attack on the quantum channel (thick red arrow)
ax.annotate("", xy=(5.0, 5.15), xytext=(5.0, 1.5),
            arrowprops=dict(arrowstyle="-|>", color=RED, lw=4, mutation_scale=18))
ax.text(5.25, 4.35, "measure and resend:\nstate collapse", color=RED, fontweight="bold", fontsize=8.5, va="center")

# error estimate going back to the alert box (dashed red)
ax.plot([8.4, 8.4, 1.4], [2.6, 2.1, 2.1], color=RED, lw=1.5, ls="--")
ax.annotate("", xy=(1.4, 1.7), xytext=(1.4, 2.1), arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.5))
ax.text(7.6, 1.75, "error estimate", color=RED, style="italic", fontsize=8.5, ha="center")

ax.set_title("Workflow of the simulated BB84 network with an eavesdropper", fontsize=10, pad=2)
save(fig, "fig2_workflow.png")
plt.show()

# ----------------------------------------------------------------------
# ## Simulation core (Stages 1 to 4 of the pipeline)
#
# One run uses **one circuit of *n* independent qubits and a single shot**, on the stabilizer method of the Aer simulator (the circuits only contain X, H and measurements).
#
# * Stage 1: Advik prepares the qubits (X for bit 1, then H for the `x` basis).
# * Stage 2: Ekta (only when the attack is on) measures in a random basis and resends in the same basis.
# * Stage 3: Bhaskar measures in a random basis.
# * Stage 4: sifting and QBER on the positions where Advik's and Bhaskar's bases are equal.
# ----------------------------------------------------------------------

# %% ===================== CELL 5 (code) =====================
sim = AerSimulator(method="stabilizer")
rng = np.random.default_rng(SEED)      # one generator drives bits, bases and simulator seeds

def run_bb84(n, attack):
    """One BB84 session with n qubits. Returns (QBER in %, sifted length m), or None if m = 0."""
    bits    = rng.integers(0, 2, n)    # Advik's bits
    a_bases = rng.integers(0, 2, n)    # 0 = '+' (rectilinear), 1 = 'x' (diagonal)
    e_bases = rng.integers(0, 2, n)    # Ekta's bases
    b_bases = rng.integers(0, 2, n)    # Bhaskar's bases

    qc = QuantumCircuit(n, n)
    for i in range(n):
        if bits[i]:    qc.x(i)         # Stage 1: encode the bit
        if a_bases[i]: qc.h(i)         #          diagonal basis
        if attack:                     # Stage 2: measure and resend
            if e_bases[i]: qc.h(i)
            qc.measure(i, i)
            if e_bases[i]: qc.h(i)
        if b_bases[i]: qc.h(i)         # Stage 3: Bhaskar measures
        qc.measure(i, i)

    seed = int(rng.integers(0, 2**31 - 1))
    mem = sim.run(qc, shots=1, memory=True, seed_simulator=seed).result().get_memory()[0]
    b_bits = np.frombuffer(mem[::-1].encode(), dtype=np.uint8) - 48   # index i = qubit i

    keep = a_bases == b_bases          # Stage 4: sifting
    m = int(keep.sum())
    if m == 0:
        return None
    errors = int((bits[keep] != b_bits[keep]).sum())
    return 100.0 * errors / m, m

# quick check
print("secure   :", run_bb84(200, attack=False))
print("attacked :", run_bb84(200, attack=True))

# ----------------------------------------------------------------------
# ## Fig. 3: QBER for 10 to 50 qubits (one run per n)
#
# > **Note:** a single short run has a very large spread (standard deviation about 20 percentage points at n = 10, see Table X), so the points of this figure change from run to run and from seed to seed. If you want a curve that sits close to 25% as in the paper, either state in the caption which seed was used, or plot the mean of many runs (the Monte Carlo version is Fig. 4).
# ----------------------------------------------------------------------

# %% ===================== CELL 6 (code) =====================
def single_run(n, attack):
    while True:                         # repeat in the rare case that no position is kept
        r = run_bb84(n, attack)
        if r is not None:
            return r[0]

n_small = [10, 20, 30, 40, 50]
qber_secure_single   = [single_run(n, False) for n in n_small]
qber_attacked_single = [single_run(n, True)  for n in n_small]
print("attacked:", [round(q, 2) for q in qber_attacked_single])

fig, ax = plt.subplots(figsize=(6.6, 4.2))
ax.plot(n_small, qber_secure_single, "o-", color=GREEN, lw=2, label="Secure Channel Baseline")
ax.plot(n_small, qber_attacked_single, "s--", color=RED, lw=1.6, label="Ekta's Interception Phase")
ax.axhline(25, color=NAVY, ls=":", lw=1.5, label="Theoretical BB84 Eavesdropping Bound (25%)")
ax.set_ylim(-2, 50); ax.set_xlim(8, 52)
ax.set_xlabel("Number of Transmitted Qubits (Network Scale)")
ax.set_ylabel("Quantum Bit Error Rate (QBER) %")
ax.set_title("QBER Stability & Network Scalability Telemetry Analysis", fontweight="bold", fontsize=10)
ax.legend(loc="upper center", fontsize=8)
save(fig, "fig3_qber_single_run.png")
plt.show()

# ----------------------------------------------------------------------
# ## Monte Carlo experiment (needed for Fig. 4 and Fig. 5)
#
# 1000 runs for n ≤ 100 and 333 runs for n ≥ 200, for the secure and the attacked channel.
# Runs with no sifted position (m = 0) are excluded, as in the paper.
# On Colab the full run takes a few minutes; progress is printed for each n.
# ----------------------------------------------------------------------

# %% ===================== CELL 7 (code) =====================
def monte_carlo(n, runs, attack):
    values, excluded = [], 0
    for _ in range(runs):
        r = run_bb84(n, attack)
        if r is None:
            excluded += 1
        else:
            values.append(r[0])
    return np.array(values), excluded

mc = {}
t0 = time.time()
for n in N_VALUES:
    runs = RUNS_SMALL if n <= 100 else RUNS_LARGE
    secure,   exc_s = monte_carlo(n, runs, attack=False)
    attacked, exc_a = monte_carlo(n, runs, attack=True)
    mc[n] = dict(runs=runs, secure=secure, attacked=attacked, excluded=(exc_s, exc_a))
    print(f"n = {n:4d} | runs = {runs:4d} | mean QBER (attack) = {attacked.mean():5.2f}% "
          f"| s.d. = {attacked.std(ddof=1):5.2f} | aborted = {100*np.mean(attacked > ABORT_THRESHOLD):5.1f}% "
          f"| {time.time()-t0:5.0f} s")

# %% ===================== CELL 8 (code) =====================
# Table X: Monte Carlo results under full interception
rows = []
for n in N_VALUES:
    a = mc[n]["attacked"]
    rows.append({
        "n": n,
        "Runs": len(a),
        "Mean QBER (%)": round(a.mean(), 2),
        "S.D. (%)": round(a.std(ddof=1), 2),
        "95% range (%)": f"{np.percentile(a, 2.5):.1f}-{np.percentile(a, 97.5):.1f}",
        "Aborted (%)": round(100 * np.mean(a > ABORT_THRESHOLD), 1),
    })
table_x = pd.DataFrame(rows)
table_x

# ----------------------------------------------------------------------
# ## Fig. 4: Monte Carlo mean QBER ± 1 standard deviation
# ----------------------------------------------------------------------

# %% ===================== CELL 9 (code) =====================
ns = np.array(N_VALUES)
mean_att = np.array([mc[n]["attacked"].mean() for n in N_VALUES])
sd_att   = np.array([mc[n]["attacked"].std(ddof=1) for n in N_VALUES])
mean_sec = np.array([mc[n]["secure"].mean() for n in N_VALUES])

fig, ax = plt.subplots(figsize=(8, 4.2))
ax.plot(ns, mean_sec, "o-", color=GREEN, lw=1.8, label="Secure channel")
ax.axhline(25, color=NAVY, ls=":", lw=1.5, label="Theoretical value (25%)")
ax.axhline(ABORT_THRESHOLD, color=ORANGE, ls=":", lw=1.8, label="Abort threshold (15%)")
ax.errorbar(ns, mean_att, yerr=sd_att, fmt="s--", color=RED, lw=1.5, capsize=4,
            label="Interception: mean ± 1 s.d.")
ax.set_xscale("log")
ax.set_xticks(ns); ax.set_xticklabels([str(n) for n in ns])
ax.set_ylim(-3, 58)
ax.set_xlabel("Number of Transmitted Qubits, n (log scale)")
ax.set_ylabel("QBER (%)")
ax.set_title("Monte Carlo QBER of the Simulated BB84 Channel", fontweight="bold", fontsize=10)
ax.legend(loc="upper right", fontsize=8)
save(fig, "fig4_monte_carlo.png")
plt.show()

# ----------------------------------------------------------------------
# ## Fig. 5: Probability that an attack is not detected
#
# Two events are shown for a full measure-and-resend attack:
#
# * **QBER = 0.00%**: no error in the sifted key. Analytical value (7/8)^n, because a qubit gives an error with probability 1/2 × 1/4 = 1/8.
# * **QBER ≤ 15%** (attack accepted): Eq. (3) of the paper,
#   P_acc(n) = Σ_m B(m; n, 1/2) · F(⌊0.15 m⌋; m, 1/4).
#
# The markers come from the Monte Carlo runs above.
# ----------------------------------------------------------------------

# %% ===================== CELL 10 (code) =====================
def p_zero_qber(n):
    return (7 / 8) ** n

def p_accepted(n):
    m = np.arange(1, n + 1)                      # m = 0 gives no key and is excluded
    p_m = binom.pmf(m, n, 0.5)                   # sifted length
    k_max = np.floor(0.15 * m + 1e-9)            # most errors allowed by the 15% rule
    return float(np.sum(p_m * binom.cdf(k_max, m, 0.25)))

n_curve = np.arange(10, 301)
acc_curve  = 100 * np.array([p_accepted(n) for n in n_curve])
zero_curve = 100 * p_zero_qber(n_curve)

# simulated frequencies from the Monte Carlo runs
n_marks = [n for n in N_VALUES if n <= 200]
acc_sim  = [100 * np.mean(mc[n]["attacked"] <= ABORT_THRESHOLD) for n in n_marks]
zero_sim = [100 * np.mean(mc[n]["attacked"] == 0) for n in n_marks]

fig, ax = plt.subplots(figsize=(8, 4.2))
ax.plot(n_curve, acc_curve, color=RED, lw=1.5, label="P(attack accepted): analytical")
ax.plot(n_curve, zero_curve, color=NAVY, lw=1.5, ls="--", label="P(QBER = 0.00%): analytical")
ax.plot([n for n, v in zip(n_marks, acc_sim) if v > 0], [v for v in acc_sim if v > 0],
        "s", mfc="none", mec=RED, ms=6, ls="none", label="P(attack accepted): simulated")
ax.plot([n for n, v in zip(n_marks, zero_sim) if v > 0], [v for v in zero_sim if v > 0],
        "o", mfc="none", mec=NAVY, ms=6, ls="none", label="P(QBER = 0.00%): simulated")
ax.set_yscale("log"); ax.set_ylim(1e-2, 1e2); ax.set_xlim(0, 300)
ax.set_xlabel("Number of Transmitted Qubits, n")
ax.set_ylabel("Probability (%)")
ax.set_title("Failure Probability of Detection: Model and Simulation", fontweight="bold", fontsize=10)
ax.legend(loc="upper right", fontsize=8)
save(fig, "fig5_failure_probability.png")
plt.show()

# Table XIII (model columns)
pd.DataFrame({
    "n": [10, 20, 30, 40, 50, 100, 200],
    "QBER = 0%, model (%)": [round(100 * p_zero_qber(n), 4) for n in [10, 20, 30, 40, 50, 100, 200]],
    "Accepted, model (%)":  [round(100 * p_accepted(n), 2) for n in [10, 20, 30, 40, 50, 100, 200]],
})

# ----------------------------------------------------------------------
# ## Fig. 6: Error rate by party vs. the 15% abort threshold
#
# The three values are the numbers reported in the paper for the short run (Table IX): Advik 0.00%, Bhaskar 25.00%, Ekta 36.36%. Change them in the first lines of the cell if your own run gives other numbers. The 0.00% bar is drawn with a small minimum height so that it stays visible.
# ----------------------------------------------------------------------

# %% ===================== CELL 11 (code) =====================
parties = ["Advik\n(Sender Base)", "Bhaskar\n(Receiver Sync)", "Ekta\n(Spy Intrusion)"]
values  = [0.00, 25.00, 36.36]            # values from the paper
colors  = [GREEN, NAVY, "#c62828"]

fig, ax = plt.subplots(figsize=(7.2, 4.4))
heights = [max(v, 1.5) for v in values]    # keep the 0.00% bar visible
bars = ax.bar(parties, heights, color=colors, width=0.4, edgecolor="black", lw=0.8)
for bar, v in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.8, f"{v:.2f}%",
            ha="center", va="bottom", fontweight="bold", fontsize=9)
ax.axhline(ABORT_THRESHOLD, color=ORANGE, ls=":", lw=1.8, label="Abortion Threshold (15%)")
ax.set_ylim(0, 60)
ax.set_ylabel("Quantum Telemetry State Deviation & Error Rate %")
ax.set_title("Multi-Party Telemetry Grid (Threat Attribution Analysis)", fontweight="bold", fontsize=10)
ax.legend(loc="upper left", fontsize=8)
save(fig, "fig6_party_error_rates.png")
plt.show()

# ----------------------------------------------------------------------
# ## Download all figures
# ----------------------------------------------------------------------

# %% ===================== CELL 12 (code) =====================
# On Colab this zips the figures folder and downloads it. Elsewhere it just lists the files.
import shutil
shutil.make_archive("paper_figures", "zip", OUT_DIR)
try:
    from google.colab import files  # type: ignore
    files.download("paper_figures.zip")
except ImportError:
    print(sorted(os.listdir(OUT_DIR)))
