"""
Autonomous Quantum Security Agent powered by NVIDIA Llama-3.1-Nemotron-70B-Instruct
hosted on Nebius AI Cloud.

This module exposes a single public coroutine, 'analyze_channel_security',
which sends real-time QBER telemetry to the cloud model and returns a
structured verdict.  Every external failure path (network, rate-limit,
malformed JSON) is caught and mapped to a deterministic fallback defence
so the calling simulation pipeline never crashes.
"""

import asyncio
import json
import logging
import re
from typing import Any, Dict

import openai

from config import (
    API_MAX_TOKENS,
    API_TEMPERATURE,
    API_TIMEOUT_SECONDS,
    FALLBACK_ATTACK_PROBABILITY,
    FALLBACK_MITIGATION,
    FALLBACK_STATUS,
    MODEL_ID,
    NEBIUS_API_KEY,
    NEBIUS_BASE_URL,
    QBER_ABORT_THRESHOLD,
    QBER_ANOMALY_THRESHOLD,
    QBER_THEORETICAL_ATTACK,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Structured system prompt for the Nemotron security guard persona
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = (
    "You are an autonomous Quantum Channel Security Guard deployed inside a "
    "BB84 Quantum Key Distribution network.\n\n"
    "Your responsibilities:\n"
    "1. Analyse the measured Quantum Bit Error Rate (QBER) and sifted key "
    "length provided by the operator.\n"
    "2. Distinguish between normal background noise and an active "
    "Measure-and-Resend eavesdropping attack (performed by an adversary "
    "named 'Ekta').\n"
    "3. Issue a structured security verdict.\n\n"
    "Decision boundaries:\n"
    f"- QBER = 0.00%%: channel is perfectly SECURE.\n"
    f"- 0 < QBER <= {QBER_ANOMALY_THRESHOLD}%%: minor ANOMALY, likely noise.\n"
    f"- {QBER_ANOMALY_THRESHOLD}%% < QBER <= {QBER_ABORT_THRESHOLD}%%: "
    "significant ANOMALY, possible partial interception.\n"
    f"- QBER > {QBER_ABORT_THRESHOLD}%%: CRITICAL_ATTACK detected, "
    "session must be aborted.\n"
    f"- Theoretical full interception QBER is approximately "
    f"{QBER_THEORETICAL_ATTACK}%%.\n\n"
    "You MUST reply with exactly one JSON object (no extra text) containing:\n"
    '  "status": one of "SECURE", "ANOMALY", "CRITICAL_ATTACK"\n'
    '  "attack_probability": float between 0.0 and 1.0\n'
    '  "reasoning": a concise explanation (one or two sentences)\n'
    '  "mitigation_action": one of "ROTATE_BASES", "ABORT_SESSION", '
    '"INJECT_DECOY_KEYS"\n'
)


def _build_user_message(
    measured_qber: float, sifted_key_length: int
) -> str:
    """Construct the operator telemetry message sent to the model."""
    return (
        f"Channel telemetry report:\n"
        f"  Measured QBER: {measured_qber:.4f}%\n"
        f"  Sifted key length: {sifted_key_length} bits\n\n"
        f"Analyse this data and return your JSON verdict."
    )


def _fallback_verdict(reason: str) -> Dict[str, Any]:
    """Return a deterministic defence verdict when the cloud agent fails."""
    logger.warning(
        "Cloud agent unavailable; activating deterministic fallback. "
        "Reason: %s",
        reason,
    )
    return {
        "status": FALLBACK_STATUS,
        "attack_probability": FALLBACK_ATTACK_PROBABILITY,
        "reasoning": (
            f"Fallback defence activated because the cloud security agent "
            f"could not be reached. Reason: {reason}. "
            f"Treating channel as potentially compromised."
        ),
        "mitigation_action": FALLBACK_MITIGATION,
    }


def _extract_json(raw_text: str) -> Dict[str, Any]:
    """Parse the model output, extracting the JSON object even if surrounded by commentary."""
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", raw_text, re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1).strip()
    else:
        brace_match = re.search(r"(\{.*\})", raw_text, re.DOTALL)
        candidate = brace_match.group(1).strip() if brace_match else raw_text.strip()

    try:
        payload: Dict[str, Any] = json.loads(candidate, strict=False)
    except Exception:
        status_m = re.search(r'"status"\s*:\s*"([A-Z_]+)"', raw_text)
        prob_m = re.search(r'"attack_probability"\s*:\s*([0-9.]+)', raw_text)
        action_m = re.search(r'"mitigation_action"\s*:\s*"([A-Z_]+)"', raw_text)
        reason_m = re.search(r'"reasoning"\s*:\s*"(.*?)"(?:\s*,\s*"|\s*\})', raw_text, re.DOTALL)

        if not (status_m and action_m):
            raise ValueError(f"Unable to parse JSON payload from response: {raw_text[:120]}")

        payload = {
            "status": status_m.group(1),
            "attack_probability": float(prob_m.group(1)) if prob_m else 0.85,
            "mitigation_action": action_m.group(1),
            "reasoning": reason_m.group(1) if reason_m else "Threat identified based on QBER deviation.",
        }

    # Validate required fields
    required = {"status", "attack_probability", "reasoning", "mitigation_action"}
    missing = required - set(payload.keys())
    if missing:
        raise ValueError(f"Model response missing required fields: {missing}")

    valid_statuses = {"SECURE", "ANOMALY", "CRITICAL_ATTACK"}
    if payload["status"] not in valid_statuses:
        if "ATTACK" in payload["status"] or "CRITICAL" in payload["status"]:
            payload["status"] = "CRITICAL_ATTACK"
        elif "ANOMALY" in payload["status"] or "SUSPICIOUS" in payload["status"]:
            payload["status"] = "ANOMALY"
        elif "SECURE" in payload["status"] or "CLEAN" in payload["status"]:
            payload["status"] = "SECURE"
        else:
            payload["status"] = "CRITICAL_ATTACK"

    valid_actions = {"ROTATE_BASES", "ABORT_SESSION", "INJECT_DECOY_KEYS"}
    if payload["mitigation_action"] not in valid_actions:
        payload["mitigation_action"] = "ABORT_SESSION"

    return payload


def analyze_channel_security_sync(
    measured_qber: float,
    sifted_key_length: int,
) -> Dict[str, Any]:
    """Synchronous channel security analysis for UI dashboards (avoids event loop conflicts)."""
    clean_key = (NEBIUS_API_KEY or "").strip()
    clean_url = "".join(c for c in (NEBIUS_BASE_URL or "").strip() if c.isprintable() and not c.isspace()).rstrip("/")
    clean_model = (MODEL_ID or "").strip()

    if not clean_key:
        return _fallback_verdict("NEBIUS_API_KEY environment variable is not set")

    try:
        client = openai.OpenAI(
            api_key=clean_key,
            base_url=clean_url,
            timeout=API_TIMEOUT_SECONDS,
        )
        response = client.chat.completions.create(
            model=clean_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": _build_user_message(measured_qber, sifted_key_length),
                },
            ],
            max_tokens=API_MAX_TOKENS,
            temperature=API_TEMPERATURE,
        )
        msg = response.choices[0].message
        raw_content = msg.content or getattr(msg, "reasoning_content", "") or ""
        if not raw_content:
            raise ValueError("Model returned empty content payload")
        logger.debug("Raw model response: %s", raw_content)

        verdict = _extract_json(raw_content)
        logger.info(
            "Security agent verdict: status=%s, probability=%.2f, action=%s",
            verdict["status"],
            verdict["attack_probability"],
            verdict["mitigation_action"],
        )
        return verdict

    except openai.APIConnectionError as exc:
        return _fallback_verdict(f"API connection failure: {exc}")
    except openai.RateLimitError as exc:
        return _fallback_verdict(f"Rate limit exceeded: {exc}")
    except openai.APITimeoutError as exc:
        return _fallback_verdict(f"API request timed out: {exc}")
    except openai.APIStatusError as exc:
        return _fallback_verdict(f"API returned error status {exc.status_code}: {exc.message}")
    except (json.JSONDecodeError, ValueError) as exc:
        return _fallback_verdict(f"Failed to parse model output: {exc}")
    except Exception as exc:
        return _fallback_verdict(f"Unexpected error: {type(exc).__name__}: {exc}")


async def analyze_channel_security(
    measured_qber: float,
    sifted_key_length: int,
) -> Dict[str, Any]:
    """Send QBER telemetry to the Nemotron security agent and return a verdict (async)."""
    clean_key = (NEBIUS_API_KEY or "").strip()
    clean_url = "".join(c for c in (NEBIUS_BASE_URL or "").strip() if c.isprintable() and not c.isspace()).rstrip("/")
    clean_model = (MODEL_ID or "").strip()

    if not clean_key:
        return _fallback_verdict("NEBIUS_API_KEY environment variable is not set")

    client = None
    try:
        client = openai.AsyncOpenAI(
            api_key=clean_key,
            base_url=clean_url,
            timeout=API_TIMEOUT_SECONDS,
        )
        response = await client.chat.completions.create(
            model=clean_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": _build_user_message(measured_qber, sifted_key_length),
                },
            ],
            max_tokens=API_MAX_TOKENS,
            temperature=API_TEMPERATURE,
        )
        msg = response.choices[0].message
        raw_content = msg.content or getattr(msg, "reasoning_content", "") or ""
        if not raw_content:
            raise ValueError("Model returned empty content payload")
        logger.debug("Raw model response: %s", raw_content)

        verdict = _extract_json(raw_content)
        logger.info(
            "Security agent verdict: status=%s, probability=%.2f, action=%s",
            verdict["status"],
            verdict["attack_probability"],
            verdict["mitigation_action"],
        )
        return verdict

    except openai.APIConnectionError as exc:
        return _fallback_verdict(f"API connection failure: {exc}")
    except openai.RateLimitError as exc:
        return _fallback_verdict(f"Rate limit exceeded: {exc}")
    except openai.APITimeoutError as exc:
        return _fallback_verdict(f"API request timed out: {exc}")
    except openai.APIStatusError as exc:
        return _fallback_verdict(f"API returned error status {exc.status_code}: {exc.message}")
    except (json.JSONDecodeError, ValueError) as exc:
        return _fallback_verdict(f"Failed to parse model output: {exc}")
    except Exception as exc:
        return _fallback_verdict(f"Unexpected error: {type(exc).__name__}: {exc}")
    finally:
        if client is not None:
            await client.close()
