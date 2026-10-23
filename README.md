# quantum-catching-the-spy-qkd
A Python-based simulation of the BB84 Quantum Key Distribution (QKD) protocol using IBM's Qiskit. Features a custom software pipeline evaluating secure state preparation, a measure-and-resend eavesdropping attack simulation (featuring Advik, Bhaskar, and Ekta), and quantitative analysis of the Quantum Bit Error Rate (QBER) to abort compromised keys

# Quantum Catching the Spy: Eavesdropper Detection Analysis in Quantum Key Distribution Networks Using Qiskit

[![arXiv](https://shields.io)](https://arxiv.org)
[![License: MIT](https://shields.io)](https://opensource.org)
[![Framework: Qiskit](https://shields.io)](https://qiskit.org)
[![Python: 3.10+](https://shields.io)](https://python.org)
[![Status: Preprint](https://shields.io)]

A comprehensive, software-defined simulation pipeline evaluating secure state preparation, measure-and-resend eavesdropping vulnerabilities, and quantitative anomaly detection metrics under the BB84 protocol using IBM's Qiskit.

---

## 💻 1. Installation & Environment Setup

Configure the simulation environment locally by executing the following commands sequentially in your terminal:

```bash
# Clone the repository
git clone https://github.com
cd quantum-catching-the-spy-qkd

# Create a clean virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install required dependencies
pip install qiskit qiskit-aer matplotlib numpy
```

[Quantum Channel: Photon Stream Transfer Transmission]
o o o o o o o o o o o o o o o o o o o o o o 🡪
/                                             
┌───────────────────────────┐                 ┌───────────────────────────┐
│       Advik (Sender)      │                 │     Bhaskar (Receiver)    │
│  ┌─────────────────────┐  │                 │  ┌─────────────────────┐  │
│  │    Advik Encoder    │  │                 │  │ Measurement Backend │  │
│  └─────────────────────┘  │                 │  └─────────────────────┘  │
└───────────────────────────┘                 └───────────────────────────┘
🡩        \                                   /        🡩
│         \                                 /         │
(Intrusion        🡪 o o o o o o o o o o o o o o o 🡨       (Basis Matching
Detected)          [Classical Internet Channel]          Reconciliation)
│           (Public Basis Reconciliation)             │
│                                                     │
└─────────────────────── 🡩 ───────────────────────────┘
│
(State Collapse via Intrusion)
│
┌───────────────────────────┐
│    Ekta (Spy/Intruder)    │
│    [Measure & Resend]     │
└───────────────────────────┘

### Technical Diagram Mapping Guide (For Draw.io / BioRender)
To build a high-resolution, publication-ready schematic for your paper without copyright infringement, reconstruct the workflow manually using Draw.io or BioRender matching these structural guidelines:
*   **Left Node (Advik):** Place a male user icon labeled **Advik (Key Sender)** enclosing the **Advik Encoder** system block. Draw an upward-curving dotted blue arrow representing the **Quantum Channel (Photon Stream Transfer Transmission)**, annotated with *"Sends Stream of Photons"*.
*   **Right Node (Bhaskar):** Place a male user icon labeled **Bhaskar (Key Receiver)**. Connect the upper channel arriving from the top through a beam splitter component block, annotated with *"Uses Beam Splitter to Read Photons"*.
*   **Classical Channel (Center Line):** Route a straight horizontal arrow representing the authenticated public classical internet channel between Advik and Bhaskar. Annotate the left-to-right axis as *"Informs Which Photons Were Read Correctly"* and the right-to-left axis as *"Tells Advik Which Polarizer Used"*.
*   **Intruder Axis (Bottom Node):** Place a female user icon at the absolute bottom center labeled **Ekta (Eavesdropper)**. Route a thick vertical red arrow upwards to intercept the upper channel, overlaid with an eye symbol labeled *"Attempts to Intercept Key"* and *"Alters State of Photons"*. Extend a horizontal red line from this junction point terminating in a warning burst labeled *"Detects Eavesdropping"*.

---

## 📜 3. Complete Simulation Source Code

This repository contains the complete production pipeline written in Python using the Qiskit framework. Save this code as `qkd_simulation.py`:

```python
import random
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

num_bits = 20
qber_without_ekta = 0
qber_with_ekta = 0

print("--- BB84 क्वांटम की डिस्ट्रीब्यूशन सिमुलेशन शुरू ---")
print(f"अद्विक (Sender) {num_bits} क्वांटम बिट्स तैयार कर रहा है...\n")

advik_bits = [random.randint(0, 1) for _ in range(num_bits)]
advik_bases = [random.choice(['+', 'x']) for _ in range(num_bits)]
bhaskar_bases = [random.choice(['+', 'x']) for _ in range(num_bits)]
ekta_bases = [random.choice(['+', 'x']) for _ in range(num_bits)]

# CASE A: Secure Channel
circuits_no_ekta = []
for i in range(num_bits):
    qc = QuantumCircuit(1, 1)
    if advik_bits[i] == 1:
        qc.x(0)
    if advik_bases[i] == 'x':
        qc.h(0)
    if bhaskar_bases[i] == 'x':
        qc.h(0)
    qc.measure(0, 0)
    circuits_no_ekta.append(qc)

sim = AerSimulator()
bhaskar_bits_no_ekta = []
for qc in circuits_no_ekta:
    result = sim.run(qc, shots=1, memory=True).result()
    bhaskar_bits_no_ekta.append(int(result.get_memory()))

# CASE B: Intercepted Channel (Measure-and-Resend)
circuits_with_ekta = []
for i in range(num_bits):
    qc = QuantumCircuit(1, 1)
    if advik_bits[i] == 1:
        qc.x(0)
    if advik_bases[i] == 'x':
        qc.h(0)
    if ekta_bases[i] == 'x':
        qc.h(0)
    qc.measure(0, 0)
    if ekta_bases[i] == 'x':
        qc.h(0)
    if bhaskar_bases[i] == 'x':
        qc.h(0)
    qc.measure(0, 0)
    circuits_with_ekta.append(qc)

bhaskar_bits_with_ekta = []
for qc in circuits_with_ekta:
    result = sim.run(qc, shots=1, memory=True).result()
    bhaskar_bits_with_ekta.append(int(result.get_memory()))

# Classical Post-Processing (Key Sifting using Wikipedia Terminology)
# Extracting the matching sifted key from conjugate states and computational bases
advik_sifted_key = []
bhaskar_sifted_key_no_ekta = []
bhaskar_sifted_key_with_ekta = []

for i in range(num_bits):
    if advik_bases[i] == bhaskar_bases[i]:
        advik_sifted_key.append(advik_bits[i])
        bhaskar_sifted_key_no_ekta.append(bhaskar_bits_no_ekta[i])
        bhaskar_sifted_key_with_ekta.append(bhaskar_bits_with_ekta[i])

errors_no_ekta = sum(1 for a, b in zip(advik_sifted_key, bhaskar_sifted_key_no_ekta) if a != b)
errors_with_ekta = sum(1 for a, b in zip(advik_sifted_key, bhaskar_sifted_key_with_ekta) if a != b)

qber_no_ekta = (errors_no_ekta / len(advik_sifted_key)) * 100 if advik_sifted_key else 0
qber_with_ekta = (errors_with_ekta / len(advik_sifted_key)) * 100 if advik_sifted_key else 0

print("--- सिमुलेशन रिजल्ट डेटा टेबल ---")
print(f"अद्विक के ओरिजिनल बिट्स: {advik_bits}")
print(f"अद्विक के बेसिस:        {advik_bases}")
print(f"भास्कर के बेसिस:        {bhaskar_bases}")
print(f"एकता के बेसिस:        {ekta_bases}")
print(f"\nअद्विक की फाइनल सिफ्टेड चाबी:          {advik_sifted_key}")
print(f"भास्कर की चाबी (बिना एकता के):         {bhaskar_sifted_key_no_ekta}")
print(f"भास्कर की चाबी (जब एकता ने ताका):       {bhaskar_sifted_key_with_ekta}")
print(f"\n[परिणाम 1] बिना एकता के क्वांटम एरर रेट (QBER): {qber_no_ekta:.2f}%")
print(f"[परिणाम 2] जब एकता ने बीच में ताका, तो एरर रेट (QBER): {qber_with_ekta:.2f}%")

# Generate Performance Visuals
categories = ['Secure Channel\n(No Ekta)', 'Intercepted Channel\n(With Ekta)']
error_rates = [qber_no_ekta, qber_with_ekta]
plt.figure(figsize=(7, 5))
bars = plt.bar(categories, error_rates, color=['#4CAF50', '#F44336'], width=0.4)
plt.ylabel('Quantum Bit Error Rate (QBER) %')
plt.title('Eavesdropper Detection Analysis using BB84 Protocol')
plt.ylim(0, 40)
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1, f"{yval:.1f}%", ha='center', va='bottom', fontweight='bold')
plt.tight_layout()
plt.savefig('qber_comparison_plot.png')

circuits_with_ekta[-1].draw(output='mpl', filename='quantum_circuit_pipeline.png')

🔮 5. Future Work & Extensions

• Channel Decoupling: Integrating simulated Gaussian thermal channel noise to analyze shifts in thresholds.
• Error Correction Cascades: Deploying classical reconciliation algorithms (e.g., Cascade protocol) to process noisy channel keys.
• Entanglement Models: Scaling the current framework into multi-party entanglement-based architectures utilizing the E91 protocol.

📜 6. License & Citations

This repository is licensed under the MIT License. Feel free to leverage the pipeline configurations for subsequent academic preprint drafts or structural optimization models.
This is for informational purposes only. For medical advice or diagnosis, consult a professional. AI responses may include mistakes.

---

## 🛠️ 2. System Architecture & Workflow

The network architecture deploys a dual-channel configuration, processing communication across nodes through four explicit execution phases:

