import logging
import re
from typing import List, Dict, Tuple, Optional
from prompts import ABSTRACT_REACT_SYSTEM_PROMPT

from llm import LLMClient
from models import UIElement, Window, WorldState 

logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ReActAgent:
    def __init__(
        self,
        llm_client: LLMClient,
        max_trajectory_length: int = 15,
        **kwargs 
    ):

        self.llm_client = llm_client
        self.max_trajectory_length = max_trajectory_length

        self.system_message_template = ABSTRACT_REACT_SYSTEM_PROMPT
        self.reset()

    def reset(self):
        self.trajectory: List[Dict] = []
        #logger.info("ReActAgent has been reset.")
        
    def get_trajectory(self) -> List[Dict]:
        return self.trajectory

    def _build_prompt(self, instruction: str, observation: str) -> Tuple[str, str]:
        
        system_prompt = self.system_message_template + f"\n\n### CURRENT TASK ###\n{instruction}"

        history = ""
        for turn in self.trajectory:
            history += f"Previous Thought: {turn['thought']}\n"
            history += f"Previous Action: {turn['action']}\n"
            
        
        user_prompt = f"""
        Here is the history of your previous thoughts and actions:
        <history>
        {history if history else "This is the first step."}
        </history>

        Here is the current observation of the GUI:
        <observation>
        {observation}
        </observation>

        Based on the history and current observation, please provide your next thought and action.
        """
        return system_prompt, user_prompt.strip()

    def predict(self, instruction: str, observation: str) -> Tuple[str, str]:
        if len(self.trajectory) >= self.max_trajectory_length:
            logger.warning("Maximum trajectory length reached. Forcing FAIL action.")
            return "Max steps reached", "FAIL(reason='Max steps reached')"

        system_prompt, user_prompt = self._build_prompt(instruction, observation)

        response_text = self.llm_client.call(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.0, 
            max_tokens=1024,
            expect_json=False
        )

        if not response_text:
            logger.error("LLM call failed or returned empty response.")
            return "LLM call failed.", "FAIL(reason='LLM did not respond')"

        #logger.info(f"LLM Raw Response:\n{response_text}")

        thought = self._parse_thought(response_text)
        action_str = self._parse_action(response_text)
        

        self.trajectory.append({
            "observation": observation, 
            "thought": thought,
            "action": action_str,
        })

        return thought, action_str

    def _parse_thought(self, response: str) -> str:
        match = re.search(r'<thought>(.*?)</thought>', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        logger.warning("Could not parse <thought> from LLM response.")
        return "No thought found in the response."

    def _parse_action(self, response: str) -> str:
        match = re.search(r'<action>(.*?)</action>', response, re.DOTALL)
        if match:
            action_content = match.group(1).strip()
            return action_content
        logger.error("Could not parse <action> tag from LLM response.")
        return "FAIL(reason='No action tag found')"