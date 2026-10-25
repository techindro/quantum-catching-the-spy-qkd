"""
Centralized configuration for the Quantum Security Agent pipeline.

All sensitive credentials are loaded exclusively from environment variables.
Default simulation thresholds and API parameters are defined here to maintain
a single source of truth across the pipeline.
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Nebius AI Cloud credentials (OpenAI-compatible endpoint)
# ---------------------------------------------------------------------------
def _sanitize_str(val: str, default: str = "") -> str:
    s = (val or default).strip()
    return "".join(c for c in s if c.isprintable() and not c.isspace())

NEBIUS_API_KEY: str = _sanitize_str(os.environ.get("NEBIUS_API_KEY", ""))
_raw_url = os.environ.get("NEBIUS_BASE_URL", "https://api.nebius.ai/v1")
NEBIUS_BASE_URL: str = _sanitize_str(_raw_url, "https://api.nebius.ai/v1").rstrip("/")

if not NEBIUS_API_KEY:
    logger.warning(
        "NEBIUS_API_KEY is not set. The security agent will operate "
        "in deterministic fallback mode for every request."
    )

# ---------------------------------------------------------------------------
# NVIDIA model identifier (Nemotron family)
# ---------------------------------------------------------------------------
MODEL_ID: str = _sanitize_str(
    os.environ.get("MODEL_ID", "nvidia/nemotron-3.5-lightning-30b-a3b")
)

# ---------------------------------------------------------------------------
# API request parameters
# ---------------------------------------------------------------------------
API_TIMEOUT_SECONDS: float = float(
    os.environ.get("API_TIMEOUT_SECONDS", "30.0")
)
API_MAX_TOKENS: int = int(os.environ.get("API_MAX_TOKENS", "2048"))
API_TEMPERATURE: float = float(os.environ.get("API_TEMPERATURE", "0.1"))

# ---------------------------------------------------------------------------
# BB84 simulation thresholds
# ---------------------------------------------------------------------------
QBER_ABORT_THRESHOLD: float = 15.0   # percent; abort key above this value
QBER_ANOMALY_THRESHOLD: float = 5.0  # percent; flag for further analysis
QBER_THEORETICAL_ATTACK: float = 25.0  # expected QBER under full intercept

# ---------------------------------------------------------------------------
# Fallback defence defaults (used when the cloud agent is unreachable)
# ---------------------------------------------------------------------------
FALLBACK_STATUS: str = "UNKNOWN_POTENTIAL_ATTACK"
FALLBACK_MITIGATION: str = "ROTATE_BASES"
FALLBACK_ATTACK_PROBABILITY: float = 0.75
