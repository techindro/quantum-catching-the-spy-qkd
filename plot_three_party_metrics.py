# Google Colab की स्क्रीन पर लाइव ग्राफ़ डिस्प्ले करने के लिए आवश्यक मैजिक कमांड
%matplotlib inline

import matplotlib.pyplot as plt
import numpy as np

# Setting up professional academic plot style parameters
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 10

# Data extracted from your real-time quantum network nodes
nodes = ['Advik\n(Sender Base)', 'Bhaskar\n(Receiver Sync)', 'Ekta\n(Spy Intrusion)']
actual_rates = [0.00, 25.00, 36.36]  # Exact simulated benchmarks for labels

# CRITICAL FIX: Assigning a tiny baseline height (2%) to Advik so the green color becomes visible at zero
visual_rates = [2.00 if x == 0.00 else x for x in actual_rates]

# Initializing canvas: 100 DPI for screen view, 300 DPI inside savefig for paper
fig, ax = plt.subplots(figsize=(7, 4.5), dpi=100)

# Colors assigned logically based on your precise threat mapping rules
colors = ['#2E7D32', '#1A237E', '#C62828']
bars = ax.bar(nodes, visual_rates, color=colors, width=0.4, edgecolor='black', linewidth=1.2)

# Grid layout configurations for precise quantitative reference
ax.set_ylabel('Quantum Telemetry State Deviation & Error Rate %', fontweight='bold')
ax.set_ylim(0, 60)
ax.grid(axis='y', linestyle='--', alpha=0.5)
ax.set_axisbelow(True)

# Annotating the strict actual mathematical values (0.00%) on top of the visual bars
for bar, actual_val in zip(bars, actual_rates):
    yval = bar.get_height()
    # If it is Advik's adjusted bar, we position the text slightly higher for alignment
    text_y = yval + 1.5 if actual_val != 0.00 else actual_val + 3.5
    ax.text(
        bar.get_x() + bar.get_width()/2.0, 
        text_y, 
        f"{actual_val:.2f}%", 
        ha='center', 
        va='bottom', 
        fontweight='bold',
        color='black'
    )

# Structuring explicit threat detection threshold line (15% Alert Limit)
ax.axhline(y=15, color='#EF6C00', linestyle=':', linewidth=1.8, label='Abortion Threshold (15%)')
ax.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='none')

plt.title('Multi-Party Telemetry Grid (Threat Attribution Analysis)', fontsize=11, fontweight='bold', pad=12)
plt.tight_layout()

# Saving publication-ready vector image asset directly to Colab disk in full 300 DPI quality
output_filename = "quantum_threat_attribution_fixed_chart.png"
plt.savefig(output_filename, bbox_inches='tight', dpi=300)

# Google Colab की स्क्रीन पर चित्र को तुरंत दिखाने के लिए आवश्यक कमांड
plt.show()

print(f"Saved: {output_filename}")
