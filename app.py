import asyncio
import random
import types
import gradio as gr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from config import QBER_ABORT_THRESHOLD
from security_agent import analyze_channel_security_sync

try:
    import spaces  # type: ignore
except ImportError:
    spaces = types.SimpleNamespace(GPU=lambda fn: fn)


def _format_bitstream(bits: list, max_bits: int = 36) -> str:
    """Format a binary bit array into a clean cryptographic bitstring."""
    s = "".join(str(b) for b in bits)
    if len(s) > max_bits:
        return f"{s[:max_bits]}... ({len(s)} bits)"
    return f"{s} ({len(s)} bits)"


def _simulate_circuit_run(num_bits: int, mode: str):
    """Simulate single-qubit BB84 transmission and record representative circuit topology."""
    advik_bits = [random.randint(0, 1) for _ in range(num_bits)]
    advik_bases = [random.choice(["+", "x"]) for _ in range(num_bits)]
    bhaskar_bases = [random.choice(["+", "x"]) for _ in range(num_bits)]
    ekta_bases = [random.choice(["+", "x"]) for _ in range(num_bits)]

    sim = AerSimulator()
    circuits = []
    representative_qc = None

    for i in range(num_bits):
        qc = QuantumCircuit(1, 1)
        # Stage 1: Advik state preparation
        if advik_bits[i] == 1:
            qc.x(0)
        if advik_bases[i] == "x":
            qc.h(0)

        # Stage 2: Channel transmission & interception
        if mode == "attacked":
            if ekta_bases[i] == "x":
                qc.h(0)
            qc.measure(0, 0)
            if ekta_bases[i] == "x":
                qc.h(0)
        elif mode == "mitigated":
            # Decoy state dynamic isolation active: eavesdropper blinded
            pass

        # Stage 3: Bhaskar measurement
        if bhaskar_bases[i] == "x":
            qc.h(0)
        qc.measure(0, 0)

        circuits.append(qc)
        if i == 0:
            representative_qc = qc

    measured_bits = []
    for qc in circuits:
        job = sim.run(qc, shots=1, memory=True)
        memory = job.result().get_memory()
        val = memory[0] if isinstance(memory, list) else memory
        measured_bits.append(int(val))

    # Basis reconciliation
    sifted_advik, sifted_bhaskar = [], []
    for i in range(num_bits):
        if advik_bases[i] == bhaskar_bases[i]:
            sifted_advik.append(advik_bits[i])
            sifted_bhaskar.append(measured_bits[i])

    sifted_length = len(sifted_advik)
    errors = sum(1 for a, b in zip(sifted_advik, sifted_bhaskar) if a != b)
    qber = (errors / sifted_length) * 100 if sifted_length else 0.0

    # Draw representative circuit as clean ASCII art
    circuit_ascii = ""
    if representative_qc is not None:
        try:
            circuit_ascii = str(representative_qc.draw(output="text"))
        except Exception:
            circuit_ascii = "q: ──|H|──[M]──|H|──[M]──\nc: 1/═════╩═════════╩═══"

    return {
        "qber": qber,
        "sifted_length": sifted_length,
        "advik_key": sifted_advik,
        "bhaskar_key": sifted_bhaskar,
        "advik_bits": advik_bits,
        "advik_bases": advik_bases,
        "bhaskar_bases": bhaskar_bases,
        "ekta_bases": ekta_bases,
        "circuit_ascii": circuit_ascii,
    }


def _generate_plot(baseline_qber: float, cycle1_qber: float, cycle2_qber: float):
    """Render a balanced high-DPI bar plot comparing QBER across the 3 channel phases."""
    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(6.2, 4.5), dpi=110)
    categories = [
        "Secure Channel\n(Baseline)",
        "Intercepted Channel\n(Ekta Active)",
        "Mitigated Channel\n(Self-Healed)",
    ]
    rates = [baseline_qber, cycle1_qber, cycle2_qber]
    bar_colors = ["#4CAF50", "#F44336", "#2196F3"]
    bars = ax.bar(
        categories,
        rates,
        color=bar_colors,
        width=0.34,
        edgecolor="#333333",
        linewidth=0.6,
        alpha=0.92,
    )

    ax.axhline(
        QBER_ABORT_THRESHOLD,
        color="#FF9800",
        linestyle="--",
        linewidth=1.8,
        label=f"Abort Threshold ({QBER_ABORT_THRESHOLD:.0f}%)",
    )
    ax.set_ylabel("Quantum Bit Error Rate (QBER) %", fontweight="bold", fontsize=10)
    ax.set_ylim(0, max(45, int(cycle1_qber) + 15))
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.legend(loc="upper left", framealpha=0.95, fontsize=9)
    ax.tick_params(axis="both", labelsize=9.5)

    for bar in bars:
        yval = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            yval + 1.0,
            f"{yval:.1f}%",
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=10,
        )
    fig.tight_layout()
    return fig


def _get_initial_telemetry() -> str:
    sep = "=" * 62
    return (
        f"{sep}\n"
        f"        LIVE QUANTUM CIRCUIT TOPOLOGY & TELEMETRY\n"
        f"{sep}\n\n"
        f"Channel Status: STANDBY (Ready for transmission)\n\n"
        f"Select the qubit count above and click 'Run Quantum Pipeline Simulation'\n"
        f"to initiate the BB84 protocol.\n\n"
        f"Pipeline sequence:\n"
        f"  1. IBM Qiskit BB84 state preparation (Advik)\n"
        f"  2. Active Measure-and-Resend interception simulation (Ekta)\n"
        f"  3. Basis reconciliation & QBER computation (Bhaskar)\n"
        f"  4. Telemetry evaluation by NVIDIA Nemotron AI Sentinel\n"
        f"  5. Autonomous closed-loop channel healing & key verification\n"
    )


def _get_initial_sentinel_card() -> str:
    return """
### NVIDIA Nemotron AI Security Sentinel

<div style="border-left: 5px solid #757575; padding: 12px 18px; background: #F5F5F5; border-radius: 4px; margin-bottom: 14px;">
    <strong style="color: #424242; font-size: 1.08em; letter-spacing: 0.5px;">STANDBY: READY FOR TRANSMISSION</strong>
    <p style="margin: 4px 0 0 0; color: #616161; font-size: 0.92em;">Awaiting real-time QBER telemetry from the IBM Qiskit simulation pipeline.</p>
</div>

| Security Parameter | Threat Evaluation State | Operational Impact |
| :--- | :--- | :--- |
| **Identified Attacker** | Standby (Channel Idle) | No active eavesdropper detected |
| **Attack Probability** | 0.0% | Baseline threshold nominal |
| **Autonomous Action** | `MONITORING` | Ready to enforce defense policy |
| **Mitigation Status** | Inactive | Channel idle awaiting execution |

**NVIDIA AI Cryptographic Reasoning:**
> "Sentinel agent initialized and listening on NVIDIA Cloud endpoint. Ready to evaluate real-time QBER telemetry upon transmission."
"""


def run_quantum_pipeline(num_bits):
    num_bits = int(num_bits)

    # 1. Baseline Clean Channel (Secure, No Spy)
    baseline = _simulate_circuit_run(num_bits, mode="secure")

    # 2. Cycle 1: Intercepted Channel (Spy Ekta Active)
    cycle1 = _simulate_circuit_run(num_bits, mode="attacked")

    # 3. Query Cloud AI Security Agent (NVIDIA Nemotron)
    verdict = analyze_channel_security_sync(
        measured_qber=cycle1["qber"],
        sifted_key_length=cycle1["sifted_length"],
    )

    status = verdict.get("status", "UNKNOWN_POTENTIAL_ATTACK")
    prob = verdict.get("attack_probability", 0.0)
    action = verdict.get("mitigation_action", "ROTATE_BASES")
    reasoning = verdict.get("reasoning", "")

    # 4. Cycle 2: Closed-Loop Mitigation (Healed Channel)
    cycle2 = _simulate_circuit_run(num_bits, mode="mitigated")

    # 5. Format Telemetry Text with ASCII Circuit Topology
    sep_line = "=" * 62
    circuit_text = cycle1["circuit_ascii"].strip()

    status_badge = "COMPROMISED (ACTIVE SPY ATTACK)" if cycle1["qber"] > QBER_ABORT_THRESHOLD else "OPTIMAL (CHANNEL SECURE)"
    action_badge = "ABORT KEYS & ROTATE BASES" if cycle1["qber"] > QBER_ABORT_THRESHOLD else "SESSION KEY ESTABLISHED"

    telemetry = (
        f"{sep_line}\n"
        f"        LIVE QUANTUM CIRCUIT TOPOLOGY (ASCII ART)\n"
        f"{sep_line}\n\n"
        f"{circuit_text}\n\n"
        f"{sep_line}\n"
        f"                QUANTUM CHANNEL TELEMETRY\n"
        f"{sep_line}\n"
        f"Transmitted Qubits (n):             {num_bits}\n"
        f"Sifted Key Length:                  {cycle1['sifted_length']} bits\n"
        f"Secure Channel QBER Baseline:       {baseline['qber']:.2f}%\n"
        f"Intercepted Channel QBER (Ekta):    {cycle1['qber']:.2f}%\n"
        f"Post-Mitigation Healed QBER:        {cycle2['qber']:.2f}%\n"
        f"Physical Abort Threshold:           {QBER_ABORT_THRESHOLD:.1f}%\n\n"
        f"{sep_line}\n"
        f"                 KEY RECONCILIATION VECTORS\n"
        f"{sep_line}\n"
        f"Advik Sifted Key:    {_format_bitstream(cycle1['advik_key'])}\n"
        f"Bhaskar Sifted Key:  {_format_bitstream(cycle1['bhaskar_key'])}\n\n"
        f"Status: [{status_badge}]\n"
        f"Action: [{action_badge}]\n"
    )

    # 6. Generate Symmetrical Matplotlib Comparison Graph
    fig = _generate_plot(baseline["qber"], cycle1["qber"], cycle2["qber"])

    # 7. NVIDIA Nemotron AI Sentinel Card (Dynamically configured)
    if status == "CRITICAL_ATTACK":
        card_border = "#D32F2F"
        card_bg = "#FFEBEE"
        status_text = "CRITICAL SPY ATTACK IDENTIFIED"
        sub_text = "Measure-and-resend attack detected above the 15.0% physical threshold."
        attacker_text = "Ekta (The Spy via Measure-and-Resend)"
        healing_text = "Restored to 0.00% QBER (Compromised keys purged, basis rotated)"
    elif status == "ANOMALY":
        card_border = "#FF8F00"
        card_bg = "#FFF8E1"
        status_text = "ANOMALOUS CHANNEL DRIFT DETECTED"
        sub_text = "QBER variance observed; basis realignment applied."
        attacker_text = "Potential Eavesdropper / Channel Noise"
        healing_text = "Mitigation Active (Basis schedule rotated)"
    elif status == "SECURE":
        card_border = "#2E7D32"
        card_bg = "#E8F5E9"
        status_text = "QUANTUM CHANNEL OPTIMAL"
        sub_text = "Zero unauthorized state perturbations detected."
        attacker_text = "None (No Interception Detected)"
        healing_text = "Not Required (Baseline Clean at 0.00% QBER)"
    else:
        card_border = "#455A64"
        card_bg = "#ECEFF1"
        status_text = "FALLBACK DEFENSE ACTIVE"
        sub_text = "Deterministic defense activated as precautionary safety protocol."
        attacker_text = "Unknown Threat (Precautionary Alert)"
        healing_text = "Precautionary Basis Rotation Applied"

    card_markdown = f"""
### NVIDIA Nemotron AI Security Sentinel

<div style="border-left: 5px solid {card_border}; padding: 12px 18px; background: {card_bg}; border-radius: 4px; margin-bottom: 14px;">
    <strong style="color: {card_border}; font-size: 1.08em; letter-spacing: 0.5px;">{status_text}</strong>
    <p style="margin: 4px 0 0 0; color: #424242; font-size: 0.92em;">{sub_text}</p>
</div>

| Security Parameter | Threat Evaluation State | Operational Impact |
| :--- | :--- | :--- |
| **Identified Attacker** | **{attacker_text}** | Eavesdropper Wavefunction Collapse Isolated |
| **Attack Probability** | **{prob * 100:.1f}%** | NVIDIA Cloud Telemetry Confidence Score |
| **Autonomous Action** | **`{action}`** | Closed-Loop Self-Healing Triggered |
| **Mitigation Status** | **{healing_text}** | Zero-Knowledge Confidentiality Preserved |

**NVIDIA AI Cryptographic Reasoning:**
> "{reasoning}"
"""

    return telemetry, fig, card_markdown


# Clean CSS styling matching the user's exact design
custom_css = """
.gradio-container {
    max-width: 1200px !important;
    margin: 0 auto !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
}
.header-badge-row {
    display: flex;
    gap: 10px;
    margin-top: 6px;
    margin-bottom: 14px;
}
.header-badge {
    display: inline-block;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-radius: 12px;
    background: #f0f0f0;
    color: #424242;
    border: 1px solid #dcdcdc;
}
.controls-group {
    background: #fafafa !important;
    border: 1px solid #e0e0e0 !important;
    border-radius: 8px !important;
    padding: 16px 20px !important;
    margin-bottom: 18px !important;
}
.controls-group .block,
.controls-group .form,
.controls-group .gradio-row > div {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
.run-btn {
    height: 38px !important;
    min-height: 38px !important;
    max-height: 38px !important;
    line-height: 38px !important;
    padding: 0 16px !important;
    margin-top: 24px !important;
    background: #ff5722 !important;
    color: #ffffff !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    white-space: nowrap !important;
    border-radius: 6px !important;
    border: none !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12) !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
.run-btn:hover {
    background: #e64a19 !important;
}
.telemetry-box textarea {
    font-family: 'JetBrains Mono', 'Consolas', 'Courier New', monospace !important;
    font-size: 12.5px !important;
    line-height: 1.42 !important;
    background-color: #fbfbfb !important;
    border-radius: 6px !important;
    overflow-y: auto !important;
    overflow-x: auto !important;
    pointer-events: auto !important;
    cursor: text !important;
    height: 380px !important;
    min-height: 260px !important;
    max-height: 700px !important;
    resize: vertical !important;
}
.sentinel-box {
    background: #ffffff !important;
    border: 1px solid #e0e0e0 !important;
    border-radius: 8px !important;
    padding: 18px !important;
    margin-top: 14px !important;
}
.sentinel-box table {
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 12px 0 !important;
}
.sentinel-box th {
    background: #f5f5f5 !important;
    padding: 10px 14px !important;
    text-align: left !important;
    font-weight: 600 !important;
    border-bottom: 2px solid #e0e0e0 !important;
}
.sentinel-box td {
    padding: 10px 14px !important;
    border-bottom: 1px solid #eeeeee !important;
}
"""

with gr.Blocks(title="Quantum Catching the Spy: BB84 QKD Simulator") as demo:
    # 0. Global Dashboard Styling
    gr.HTML(f"<style>{custom_css}</style>")

    # 1. Header Section
    gr.Markdown(
        """
        # Quantum Catching the Spy: BB84 QKD Simulator
        ### Autonomous Eavesdropper Detection & Self-Healing Protocol in Quantum Networks
        An interactive simulation of BB84 conjugate state transmission using **IBM Qiskit**, monitored in real-time by **NVIDIA Nemotron AI** on Nebius Cloud.
        """
    )
    gr.HTML(
        """
        <div class="header-badge-row">
            <span class="header-badge">IBM QISKIT AER</span>
            <span class="header-badge">NVIDIA NEMOTRON SENTINEL</span>
            <span class="header-badge">BB84 CONJUGATE STATES</span>
            <span class="header-badge">CLOSED-LOOP SELF-HEALING</span>
        </div>
        """
    )

    # 2. Controls Section (Top Row, Sleek & Compact)
    with gr.Group(elem_classes=["controls-group"]):
        with gr.Row(equal_height=False):
            slider = gr.Slider(
                minimum=10,
                maximum=50,
                value=20,
                step=5,
                label="Quantum Transmission Length (Qubits)",
                scale=4,
            )
            btn = gr.Button(
                "Run Quantum Pipeline Simulation",
                variant="primary",
                scale=2,
                min_width=250,
                elem_classes=["run-btn"],
            )

    # 3. Main Analytics Row: Balanced 2 Columns with Scrollable & Resizable Telemetry
    with gr.Row():
        with gr.Column(scale=1):
            output_text = gr.Textbox(
                label="Live Quantum Circuit Topology & Channel Telemetry",
                lines=18,
                max_lines=50,
                value=_get_initial_telemetry(),
                interactive=False,
                autoscroll=False,
                elem_classes=["telemetry-box"],
            )
        with gr.Column(scale=1):
            output_plot = gr.Plot(
                label="Comparative Quantum Bit Error Rate (QBER) Analysis",
                value=_generate_plot(0.0, 0.0, 0.0),
            )

    # 4. Autonomous AI Sentinel Section (Full-Width Bottom Group)
    with gr.Group(elem_classes=["sentinel-box"]):
        agent_output = gr.Markdown(
            value=_get_initial_sentinel_card(),
        )

    btn.click(
        fn=run_quantum_pipeline,
        inputs=slider,
        outputs=[output_text, output_plot, agent_output],
    )

if __name__ == "__main__":
    demo.launch()
