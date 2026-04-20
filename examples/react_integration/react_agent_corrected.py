"""Benchmark-style ReAct integration example for MirrorGuard."""

from __future__ import annotations
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from examples.shared.correction_runtime import run_mirrorguard

logger = logging.getLogger("mirrorguard.examples.react")


THOUGHT_SYSTEM_PROMPT = """You are a meticulous AI agent controlling a desktop computer.
You will be given a screenshot and an instruction. Your goal is to first think about the current situation and plan your next action.
Output only your analysis and reasoning inside a <thought> block.
"""

ACTION_SYSTEM_PROMPT = """You are an agent that performs desktop computer tasks.
Given the screenshot and the required thought process, produce the next action only.
"""


@dataclass
class Observation:
    screenshot_b64: Optional[str] = None


class ReActAgentCorrected:
    """Two-stage ReAct example using MirrorGuard replacement steering."""

    def __init__(
        self,
        client: Any,
        model: str,
        *,
        thought_system_prompt: str = THOUGHT_SYSTEM_PROMPT,
        action_system_prompt: str = ACTION_SYSTEM_PROMPT,
        max_tokens: int = 1500,
        temperature: float = 0.0,
        enable_correction: bool = True,
    ) -> None:
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.enable_correction = enable_correction
        self.thought_system_prompt = thought_system_prompt
        self.action_system_prompt = action_system_prompt
        self.thought_history: List[str] = []
        self.observations: List[Observation] = []

    def reset(self) -> None:
        self.thought_history = []
        self.observations = []

    def _call_llm(self, messages: Sequence[Dict[str, Any]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=list(messages),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content

    def _build_thought_messages(self, instruction: str, observation: Observation) -> List[Dict[str, Any]]:
        user_text = "Think about the current GUI state and provide the next reasoning step."
        content: List[Dict[str, Any]] = [{"type": "text", "text": user_text}]
        if observation.screenshot_b64:
            content.append(
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{observation.screenshot_b64}"}}
            )
        return [
            {"role": "system", "content": self.thought_system_prompt + f"\nThe high-level task is: {instruction}"},
            {"role": "user", "content": content},
        ]

    def _build_action_messages(
        self,
        instruction: str,
        observation: Observation,
        corrected_thought: str,
    ) -> List[Dict[str, Any]]:
        user_text = (
            f"The high-level task is: {instruction}\n"
            f"Based on the screenshot, please perform the next action.\n"
            f"Your required thought process is: '{corrected_thought}'"
        )
        content: List[Dict[str, Any]] = [{"type": "text", "text": user_text}]
        if observation.screenshot_b64:
            content.append(
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{observation.screenshot_b64}"}}
            )
        return [
            {"role": "system", "content": self.action_system_prompt},
            {"role": "user", "content": content},
        ]

    @staticmethod
    def _parse_thought(response_text: str) -> str:
        match = re.search(r"<thought>(.*?)</thought>", response_text, re.DOTALL)
        return match.group(1).strip() if match else response_text.strip()

    def predict(self, instruction: str, observation: Dict[str, Any]) -> Tuple[str, str, str]:
        """Return original thought, corrected thought, and final action text."""

        current_observation = Observation(
            screenshot_b64=observation.get("screenshot_b64") or observation.get("screenshot"),
        )
        self.observations.append(current_observation)

        thought_messages = self._build_thought_messages(instruction, current_observation)
        original_thought = self._parse_thought(self._call_llm(thought_messages))

        history_str = "\n".join(f"<thought>{item}</thought>" for item in self.thought_history)
        corrected_thought = (
            run_mirrorguard(
                instruction,
                history_str,
                current_observation.screenshot_b64 or "",
                original_thought,
            )
            if self.enable_correction and current_observation.screenshot_b64
            else original_thought
        )

        action_messages = self._build_action_messages(instruction, current_observation, corrected_thought)
        action_text = self._call_llm(action_messages).strip()

        logger.info("Original thought: %s", original_thought)
        logger.info("Corrected thought: %s", corrected_thought)

        self.thought_history.append(original_thought)
        return original_thought, corrected_thought, action_text
