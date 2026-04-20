"""Benchmark-style Owl integration reference for MirrorGuard."""

from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from examples.shared.correction_runtime import run_mirrorguard

logger = logging.getLogger("mirrorguard.examples.owl")


@dataclass
class OwlObservation:
    screenshot: Optional[bytes] = None


class OwlAgentCorrected:
    """Reference implementation for an Owl-style tool-calling agent."""

    def __init__(
        self,
        chat_client: Any,
        model: str,
        *,
        prompt_builder: Any,
        max_tokens: int = 2048,
        temperature: float = 0.0,
        top_p: float = 1.0,
        enable_correction: bool = True,
    ) -> None:
        self.client = chat_client
        self.model = model
        self.prompt_builder = prompt_builder
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.enable_correction = enable_correction
        self.thought_history: List[str] = []

    def _chat(self, messages: List[Dict[str, Any]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
        )
        return response.choices[0].message.content.strip()

    @staticmethod
    def _parse_thought(text: str) -> str:
        if "<thinking>" in text and "</thinking>" in text:
            return text.split("<thinking>")[-1].split("</thinking>")[0].strip()
        return text.strip()

    @staticmethod
    def _to_image_b64(image: Optional[bytes]) -> str:
        if not image:
            return ""
        if isinstance(image, str):
            return image
        return base64.b64encode(image).decode("utf-8")

    def predict(self, instruction: str, observation: Dict[str, Any]) -> Tuple[str, str, str]:
        current_observation = OwlObservation(screenshot=observation.get("screenshot"))
        messages = self.prompt_builder(instruction=instruction, history=self.thought_history)
        image_b64 = self._to_image_b64(current_observation.screenshot)

        if image_b64:
            messages[-1]["content"].append(
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
            )

        response_stage_1 = self._chat(messages)
        original_thought = self._parse_thought(response_stage_1)

        history_text = "\n".join(f"<thought>{item}</thought>" for item in self.thought_history)
        corrected_thought = (
            run_mirrorguard(
                instruction,
                history_text,
                image_b64,
                original_thought,
            )
            if self.enable_correction and image_b64
            else original_thought
        )

        injected_messages = self.prompt_builder(instruction=instruction, history=self.thought_history)
        injected_messages[-1]["content"][0]["text"] += (
            "\nYou must follow this reasoning and continue with the tool call only:\n"
            f"<thinking>{corrected_thought}</thinking>"
        )
        if image_b64:
            injected_messages[-1]["content"].append(
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
            )

        action_response = self._chat(injected_messages)
        logger.info("Original thought: %s", original_thought)
        logger.info("Corrected thought: %s", corrected_thought)

        self.thought_history.append(corrected_thought)
        return original_thought, corrected_thought, action_response
