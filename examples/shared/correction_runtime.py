"""OpenAI-compatible MirrorGuard VLM deployment helper for public examples."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency for import safety
    OpenAI = None  # type: ignore[assignment]

logger = logging.getLogger("mirrorguard.examples.runtime")


@dataclass(frozen=True)
class MirrorGuardRuntimeConfig:
    mirrorguard_model: str = os.getenv("MIRRORGUARD_MODEL", "mirrorguard")
    mirrorguard_api_base_url: str = os.getenv(
        "MIRRORGUARD_API_BASE_URL", "http://127.0.0.1:6006/v1"
    )
    mirrorguard_api_key: str = os.getenv("MIRRORGUARD_API_KEY", "EMPTY")
    mirrorguard_max_new_tokens: int = int(
        os.getenv("MIRRORGUARD_MAX_NEW_TOKENS", "2048")
    )


SYSTEM_PROMPT = """You are MirrorGuard, an expert AI Safety Thought Corrector for computer-use agents.
Your task is to correct an agent's thought based on the provided instruction, history, and current GUI observation.
You must follow these rules:
1. If the thought is already safe, helpful, and logical for the given context, you MUST output the thought verbatim, without any changes.
2. If the thought is unsafe, ignores risks, or is illogical, you MUST correct it into a safe, helpful, and logical thought that still aims to solve the user's goal safely.
3. If the instruction is unsafe, you MUST refuse to continue."""


def _make_client(base_url: str, api_key: str):
    if OpenAI is None:
        return None
    return OpenAI(base_url=base_url, api_key=api_key)


def run_mirrorguard(
    instruction: str,
    history: str,
    screenshot_b64: str,
    thought: str,
    *,
    config: Optional[MirrorGuardRuntimeConfig] = None,
) -> str:
    """Correct an insecure thought using the deployed MirrorGuard VLM."""

    cfg = config or MirrorGuardRuntimeConfig()
    client = _make_client(cfg.mirrorguard_api_base_url, cfg.mirrorguard_api_key)
    if client is None or not screenshot_b64:
        return thought

    user_content = [
        {
            "type": "text",
            "text": f"### Context ###\nInstruction: {instruction}\nHistory:\n{history}\n<observation>\n",
        },
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{screenshot_b64}"},
        },
        {
            "type": "text",
            "text": f"\n</observation>\n\n### Original Thought ###\n{thought}",
        },
    ]

    try:
        response = client.chat.completions.create(
            model=cfg.mirrorguard_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=cfg.mirrorguard_max_new_tokens,
            temperature=0.0,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:  # pragma: no cover - networked runtime
        logger.warning("MirrorGuard call failed, returning original thought: %s", exc)
        return thought
