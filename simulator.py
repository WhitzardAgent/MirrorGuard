import json
import re
import time
import openai
from typing import Dict, Any, List, Optional
from models import WorldState, SceneConfig
from prompts import get_simulator_sys_prompt

class GUISimulator:
    """
    A self-contained GUI simulator that encapsulates state management, LLM communication, and conversation history.
    """
    def __init__(
        self,
        model_name: str,
        base_url: str,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: int = 5,
        temperature: float = 0.0,
        max_tokens: int = 4096
    ):
        """
        Initializes the simulator and the internal LLM client.

        Args:
            model_name (str): The name of the model to use.
            base_url (str): The API endpoint for the LLM service.
            api_key (Optional[str], optional): The API key.
            max_retries (int, optional): Maximum number of retries on request failure.
            retry_delay (int, optional): Wait time between retries in seconds.
            temperature (float, optional): The temperature parameter for the LLM.
            max_tokens (int, optional): The maximum number of output tokens for the LLM.
        """
        # LLM Configuration
        self.model_name = model_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Simulator State
        self.world_state: WorldState = WorldState()
        self.init_world_state: WorldState = WorldState()
        self.instruction: str = ""
        
        # Conversation History Management
        self.system_prompt: str = ""
        self.history: List[Dict[str, str]] = []

        try:
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
            print(f"GUISimulator initialized with LLM '{self.model_name}' at endpoint '{base_url}'")
        except Exception as e:
            print(f"Error initializing OpenAI client with base_url '{base_url}': {e}")
            raise

    def load_scenario_from_config(self, config_path: str):
        """Loads a scenario from a config file and resets the simulator state and history."""
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        scene_config = SceneConfig(**config_data)
        
        self.world_state = WorldState(**scene_config.initial_state)
        self.init_world_state = WorldState(**scene_config.initial_state)
        self.instruction = scene_config.instruction
        
        self.system_prompt = self._construct_system_prompt()
        self.reset_history()
        
        print("Scenario loaded and simulator reset.")

    def get_observation(self) -> str:
        """
        Formats the current world state into a natural language observation for the agent.
        This version lists all window IDs and provides details for all active windows and their elements.
        """
        if not self.world_state.windows:
            return "There are no open windows on the screen."

        all_window_ids = [w.window_id for w in self.world_state.windows]
        obs = f"All open window IDs are: {', '.join(all_window_ids)}.\n"

        active_windows = self._get_active_windows()

        if active_windows:
            # Loop through each active window and describe it
            for active_window in active_windows:
                obs += f"\nAn active application is '{active_window.app_name}' with window title '{active_window.title}'.\n"
                
                if active_window.elements:
                    obs += "Visible interactive elements are:\n"
                    for elem in active_window.elements:
                        desc = f"- A {elem.type} with ID '{elem.element_id}'"
                        if elem.label:
                            desc += f" and label '{elem.label}'"
                        if elem.value:
                            desc += f". Current value is '{elem.value}'"
                        obs += desc + ".\n"
                else:
                    obs += "The active window has no interactive elements.\n"
        else:
            obs += "There is currently no active window."

        return obs

    def reset_history(self):
        """Resets the conversation history back to just the system prompt."""
        if not self.system_prompt:
            print("Warning: System prompt is not set. Cannot reset history.")
            return
        self.history = [{"role": "system", "content": self.system_prompt}]
        print("--- Conversation history has been reset. ---")

    def _construct_system_prompt(self) -> str:
        return get_simulator_sys_prompt(self.instruction,self.init_world_state)

    def _construct_user_prompt(self, action_str: str) -> str:
        prompt = f"""
        [AGENT'S ACTION]:
        {action_str}
        """
        return prompt

    def _call_llm_with_history(self, user_prompt: str) -> Optional[Dict[str, Any]]:
        """
        Internal method: sends a new prompt with history and gets a JSON response.
        """
        self.history.append({"role": "user", "content": user_prompt})

        for attempt in range(self.max_retries):
            try:
              
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=self.history,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"}
                )
                
                content = completion.choices[0].message.content
                self.history.append({"role": "assistant", "content": content})

                parsed_json = json.loads(content)
                return parsed_json

            except Exception as e:
                print(f"An error occurred on attempt {attempt + 1}: {e}")
                if isinstance(e, json.JSONDecodeError):
                    print(f"LLM did not return valid JSON. Response: {content[:200] if 'content' in locals() else 'N/A'}")

                if attempt == self.max_retries - 1:
                    if self.history[-1]["role"] == "assistant":
                        self.history.pop()
                    if self.history[-1]["role"] == "user":
                        self.history.pop()
                    print("--- LLM call failed after all retries. ---")
                    return None
                
                print(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)

        return None

    def run_action(self, action_str: str):
        """
        Core external function: takes an action and drives the LLM to update the world state.
        """
        action_type, params = self._parse_action(action_str) # Reuse previous parsing function
    
        if action_type in ["DONE", "FAIL", "WAIT"]:
            print(f"SIMULATOR_LOG (Rule-based): Agent performed '{action_type}'. No state change.")
            return
     
        user_prompt = self._construct_user_prompt(action_str)
        
        new_state_data = self._call_llm_with_history(user_prompt)

        if new_state_data:
            try:
                self.world_state = WorldState(**new_state_data)
                #print("--- World state successfully updated by LLM. ---")
            except Exception as e:
                print(f"SIMULATOR_ERROR: LLM returned invalid WorldState structure. Error: {e}")
        else:
            print("SIMULATOR_ERROR: LLM call failed. The world state remains unchanged.")

    def _parse_action(self, action_str: str) -> (str, dict):
        """Parses 'CLICK(element_id="elem-01")' into ('CLICK', {'element_id': 'elem-01'})"""
        match = re.match(r'(\w+)\((.*)\)', action_str)
        if not match:
            return action_str, {} # For parameter-less actions like DONE(), FAIL()

        action_type = match.group(1).upper()
        params_str = match.group(2)
        
        try:
            # This handles 'key="value"' or 'key=value'
            params = dict(re.findall(r'(\w+)\s*=\s*["\'](.*?)["\']', params_str))
        except:
            params = {}
            
        return action_type, params

    def _get_active_windows(self) -> List:
        """Gets a list of all currently active windows."""
        return [w for w in self.world_state.windows if w.is_active]
