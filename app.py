import gradio as gr
import random
import matplotlib
matplotlib.use('Agg')  # Configures headless rendering backend for remote servers
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import spaces  # Mandatory integration framework for Hugging Face ZeroGPU alignment

@spaces.GPU  # Allocates ZeroGPU hardware dynamically during runtime pipeline execution
def run_quantum_pipeline(num_bits):
    num_bits = int(num_bits)
    
    # Step 1: Classical bit generation and random measurement basis assignment
    advik_bits = [random.randint(0, 1) for _ in range(num_bits)]
    advik_bases = [random.choice(['+', 'x']) for _ in range(num_bits)]
    bhaskar_bases = [random.choice(['+', 'x']) for _ in range(num_bits)]
    ekta_bases = [random.choice(['+', 'x']) for _ in range(num_bits)]

    sim = AerSimulator()

    # Scenario A: Execution pipeline across a secure communication channel
    circuits_no_ekta = []
    for i in range(num_bits):
        qc = QuantumCircuit(1, 1)
        # Advik encodes binary digits into conjugate quantum states
        if advik_bits[i] == 1: qc.x(0)
        if advik_bases[i] == 'x': qc.h(0)
        # Bhaskar measures the incoming qubits using a random polarizations pipeline
        if bhaskar_bases[i] == 'x': qc.h(0)
        qc.measure(0, 0)
        circuits_no_ekta.append(qc)
    
    bhaskar_bits_no_ekta = []
    for qc in circuits_no_ekta:
        job = sim.run(qc, shots=1, memory=True)
        bhaskar_bits_no_ekta.append(int(job.result().get_memory()))

    # Scenario B: Execution pipeline under an active measure-and-resend interception attack
    circuits_with_ekta = []
    for i in range(num_bits):
        qc = QuantumCircuit(1, 1)
        # Advik's initial state preparation configuration
        if advik_bits[i] == 1: qc.x(0)
        if advik_bases[i] == 'x': qc.h(0)
        
        # Ekta's unauthorized non-orthogonal measurement intervention (Forces wavefunction collapse)
        if ekta_bases[i] == 'x': qc.h(0)
        qc.measure(0, 0)
        if ekta_bases[i] == 'x': qc.h(0)
        
        # Bhaskar's final state sampling pipeline on the perturbed qubits
        if bhaskar_bases[i] == 'x': qc.h(0)
        qc.measure(0, 0)
        circuits_with_ekta.append(qc)
        
    bhaskar_bits_with_ekta = []
    for qc in circuits_with_ekta:
        job = sim.run(qc, shots=1, memory=True)
        bhaskar_bits_with_ekta.append(int(job.result().get_memory()))

    # Step 2: Classical reconciliation phase (Extracting the matching sifted key sequence)
    advik_sifted_key, bhaskar_sifted_no_ekta, bhaskar_sifted_with_ekta = [], [], []
    for i in range(num_bits):
        if advik_bases[i] == bhaskar_bases[i]:
            advik_sifted_key.append(advik_bits[i])
            bhaskar_sifted_no_ekta.append(bhaskar_bits_no_ekta[i])
            bhaskar_sifted_with_ekta.append(bhaskar_bits_with_ekta[i])

    # Step 3: Statistical evaluation of the Quantum Bit Error Rate (QBER) telemetry metrics
    errors_no_ekta = sum(1 for a, b in zip(advik_sifted_key, bhaskar_sifted_no_ekta) if a != b)
    errors_with_ekta = sum(1 for a, b in zip(advik_sifted_key, bhaskar_sifted_with_ekta) if a != b)
    
    qber_no_ekta = (errors_no_ekta / len(advik_sifted_key)) * 100 if advik_sifted_key else 0
    qber_with_ekta = (errors_with_ekta / len(advik_sifted_key)) * 100 if advik_sifted_key else 0

    # Step 4: Structuring factual execution vectors using grounded Wikipedia terminology
    telemetry = (
        f"Advik's Original Bits:   {advik_bits}\n"
        f"Advik's Encoding Bases:  {advik_bases}\n"
        f"Bhaskar's Reading Bases: {bhaskar_bases}\n"
        f"Ekta's Intercept Bases:  {ekta_bases}\n\n"
        f"Advik's Sifted Key:        {advik_sifted_key}\n"
        f"Bhaskar's Key (Secure):    {bhaskar_sifted_no_ekta}\n"
        f"Bhaskar's Key (Intercept): {bhaskar_sifted_with_ekta}\n\n"
        f"[Result 1] QBER Baseline (Secure Channel): {qber_no_ekta:.2f}%\n"
        f"[Result 2] QBER Anomaly (Intercepted Channel): {qber_with_ekta:.2f}%\n"
    )
    
    # Algorithmic check to trigger authentication success or immediate session key abortion
    if qber_with_ekta > 15:
        telemetry += "\nALERT: Severe Anomaly Detected! Intercept attack by Ekta identified. Compromised session keys aborted."
    else:
        telemetry += "\nSUCCESS: Verification metrics optimal. Secure session key established."

    # Step 5: Visual graphics plot rendering pipeline via Matplotlib canvas
    fig, ax = plt.subplots(figsize=(6, 4.5))
    categories = ['Secure Channel\n(No Ekta)', 'Intercepted Channel\n(With Ekta)']
    rates = [qber_no_ekta, qber_with_ekta]
    bars = ax.bar(categories, rates, color=['#4CAF50', '#F44336'], width=0.4)
    ax.set_ylabel('Quantum Bit Error Rate (QBER) %')
    ax.set_ylim(0, 45)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 1, f"{yval:.1f}%", ha='center', va='bottom', fontweight='bold')
    plt.tight_layout()
    
    return telemetry, fig

# Step 6: Instantiating the unified Gradio Web GUI dashboard framework
with gr.Blocks(title="Quantum Catching the Spy") as demo:
    gr.Markdown("# Quantum Catching the Spy: BB84 QKD Simulator")
    gr.Markdown("An interactive dashboard simulating prepare-and-measure conjugate state protocols using IBM Qiskit.")
    with gr.Row():
        with gr.Column():
            slider = gr.Slider(minimum=10, maximum=50, value=20, step=5, label="Qubits to Transmit")
            btn = gr.Button("Run Quantum Pipeline Simulation", variant="primary")
        with gr.Column():
            output_text = gr.Textbox(label="Execution Telemetry & Vector Analysis", lines=12)
            output_plot = gr.Plot(label="QBER Comparison Metric Graph")
    btn.click(fn=run_quantum_pipeline, inputs=slider, outputs=[output_text, output_plot])

demo.launch()
