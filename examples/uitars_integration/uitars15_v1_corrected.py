"""Benchmark-style UI-TARS integration example for MirrorGuard."""

from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from examples.shared.correction_runtime import run_mirrorguard

logger = logging.getLogger("mirrorguard.examples.uitars")


@dataclass
class UITARSObservation:
    screenshot: Optional[bytes] = None


class UITARS15V1AgentCorrected:
    """Unified-generation example using MirrorGuard prefilling."""

    def __init__(
        self,
        vlm_client: Any,
        model: str,
        *,
        prompt_template: str,
        max_tokens: int = 1500,
        temperature: float = 0.0,
        top_p: float = 1.0,
        enable_correction: bool = True,
    ) -> None:
        self.vlm = vlm_client
        self.model = model
        self.prompt_template = prompt_template
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.enable_correction = enable_correction
        self.history_responses: List[str] = []
        self.observations: List[UITARSObservation] = []

    def reset(self) -> None:
        self.history_responses = []
        self.observations = []

    def _build_history_text(self) -> str:
        history_parts: List[str] = []
        for response in self.history_responses:
            match = re.search(r"Thought: (.*?)(?=\s*Action:|$)", response, re.DOTALL)
            if match:
                history_parts.append(f"Thought: {match.group(1).strip()}")
        return "\n".join(history_parts)

    @staticmethod
    def _to_image_b64(image: Optional[bytes]) -> str:
        if not image:
            return ""
        if isinstance(image, str):
            return image
        return base64.b64encode(image).decode("utf-8")

    def _build_messages(self, user_prompt: str, observation: UITARSObservation) -> List[Dict[str, Any]]:
        content: List[Dict[str, Any]] = [{"type": "text", "text": user_prompt}]
        image_b64 = self._to_image_b64(observation.screenshot)
        if image_b64:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                }
            )
        return [
            {"role": "system", "content": [{"type": "text", "text": "You are a helpful assistant."}]},
            {"role": "user", "content": content},
        ]

    def _chat(self, messages: Sequence[Dict[str, Any]], **extra_body: Any) -> str:
        response = self.vlm.chat.completions.create(
            model=self.model,
            messages=list(messages),
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p,
            **({"extra_body": extra_body} if extra_body else {}),
        )
        return response.choices[0].message.content.strip()

    @staticmethod
    def _extract_thought(response_text: str) -> str:
        match = re.search(r"Thought: (.*?)(?=\s*Action:|$)", response_text, re.DOTALL)
        return match.group(1).strip() if match else response_text.strip()

    def predict(self, instruction: str, observation: Dict[str, Any]) -> Tuple[str, str, str]:
        current_observation = UITARSObservation(
            screenshot=observation.get("screenshot"),
        )
        self.observations.append(current_observation)

        user_prompt = self.prompt_template.format(instruction=instruction)
        messages_stage_1 = self._build_messages(user_prompt, current_observation)
        response_stage_1 = self._chat(messages_stage_1)
        original_thought = self._extract_thought(response_stage_1)

        history_text = self._build_history_text()
        image_b64 = self._to_image_b64(current_observation.screenshot)
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

        prefill_content = f"Thought: {corrected_thought}\nAction:"
        messages_stage_2 = self._build_messages(user_prompt, current_observation)
        messages_stage_2.append({"role": "assistant", "content": [{"type": "text", "text": prefill_content}]})

        response_stage_2 = self._chat(
            messages_stage_2,
            continue_final_message=True,
            add_generation_prompt=False,
        )
        final_response = f"{prefill_content} {response_stage_2}"

        logger.info("Original thought: %s", original_thought)
        logger.info("Corrected thought: %s", corrected_thought)

        self.history_responses.append(final_response)
        return original_thought, corrected_thought, final_response
