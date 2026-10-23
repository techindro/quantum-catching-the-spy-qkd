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

---

## 🛠️ 2. System Architecture & Workflow

The network architecture deploys a dual-channel configuration, processing communication across nodes through four explicit execution phases:

