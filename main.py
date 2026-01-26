import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from simulator import GUISimulator
from agent import ReActAgent
from llm import LLMClient
from config import MODELS_CONFIG

def save_json_log(data: Dict, output_path: Path):
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Log/Trajectory successfully saved to: {output_path}")
    except Exception as e:
        print(f"[ERROR] Failed to save file to {output_path}: {e}")

def run_single_case(case_path: str, agent: ReActAgent, output_directory: str, max_steps: int = 15):
    case_path_obj = Path(case_path)
    output_dir_obj = Path(output_directory)
    output_dir_obj.mkdir(parents=True, exist_ok=True)
    base_filename = case_path_obj.stem
    detailed_log_output_path = output_dir_obj / f"{base_filename}.log.json"
    trajectory_output_path = output_dir_obj / f"{base_filename}.trajectory.json"

    if detailed_log_output_path.exists() and trajectory_output_path.exists():
        print(f"[SKIP] {base_filename}")
        return

    print(f"\n{'='*20} RUNNING CASE: {case_path} {'='*20}")
    agent.reset()

    simulator = GUISimulator(**MODELS_CONFIG["simulator_model"])
    final_status = "Unknown: Initialization failed"
    full_log_data = {}

    try:
        simulator.load_scenario_from_config(case_path)
        instruction = simulator.instruction
        initial_state = simulator.world_state.model_dump()

        full_log_data = {
            "case_info": {
                "source_file": case_path_obj.name,
                "instruction": instruction,
            },
            "initial_world_state": initial_state,
            "interaction_log": [],
            "final_status": "In Progress...",
            "final_world_state": None
        }
        
        print(f"AGENT's instruction: {instruction}")

        for i in range(max_steps):
            step_number = i + 1
            print(f"\n--- Step {step_number} ---")
            
            observation = simulator.get_observation()
            
            agent_thought, agent_action = agent.predict(instruction, observation)
           
            simulator.run_action(agent_action)
            
            state_after_action = simulator.world_state.model_dump()
           
            full_log_data["interaction_log"].append({
                "step": step_number,
                "observation": observation,
                "thought": agent_thought,
                "action": agent_action,
                "world_state_after_action": state_after_action
            })
            
            print(f"AGENT outputs action: {agent_action}")
          
            if "DONE()" in agent_action or "FAIL(" in agent_action or "WAIT()" in agent_action:
                final_status = agent_action
                print(f"--- Task finished for case {case_path_obj.name} with status: {final_status} ---")
                break
        else:
            final_status = f"Max steps reached ({max_steps})"
            print(f"--- {final_status} for case {case_path_obj.name} ---")

        full_log_data["final_status"] = final_status
     
        if full_log_data["interaction_log"]:
            full_log_data["final_world_state"] = full_log_data["interaction_log"][-1]["world_state_after_action"]

    except Exception as e:
        print(f"[ERROR] An unexpected error occurred while running case {case_path_obj.name}: {e}")
        if "case_info" in full_log_data:
            full_log_data["final_status"] = f"Error: {e}"
    
    finally:
        if full_log_data:
            print(f"--- Saving detailed log for case {case_path_obj.name} ---")
            save_json_log(full_log_data, detailed_log_output_path)
        else:
            print(f"--- No detailed log data was generated. Nothing to save. ---")

        trajectory_data = agent.get_trajectory()
        if trajectory_data:
            print(f"--- Saving trajectory file for case {case_path_obj.name} ---")
            save_json_log(trajectory_data, trajectory_output_path)

def eval_batch(
    cases_directory: str, 
    # simulator_llm_client: LLMClient, 
    agent_llm_client: LLMClient, 
    output_directory: str,
    max_cases: Optional[int] = None
):
    print(f"\n--- Starting Batch Evaluation for directory: {cases_directory} ---")
   
    p = Path(cases_directory)
    if not p.is_dir():
        print(f"[ERROR] Directory not found: {cases_directory}")
        return
   
    all_case_files = sorted(list(p.glob("*.json")))
    
    if max_cases is not None and max_cases > 0:
        cases_to_run = all_case_files[:max_cases]
        print(f"Found {len(all_case_files)} cases. Running the first {len(cases_to_run)}.")
    else:
        cases_to_run = all_case_files
        print(f"Found {len(all_case_files)} cases. Running all of them.")

    if not cases_to_run:
        print("No .json cases found to run.")
        return

    agent = ReActAgent(llm_client=agent_llm_client)

    for case_path in cases_to_run:
        base_filename = case_path.stem
        detailed_log_output_path = Path(output_directory) / f"{base_filename}.log.json"
        trajectory_output_path = Path(output_directory) / f"{base_filename}.trajectory.json"
        if detailed_log_output_path.exists() and trajectory_output_path.exists():
            print(f"[SKIP] {base_filename}")
            continue
        run_single_case(str(case_path), agent, output_directory)

def main():
  
    print("--- Initializing LLM Clients from config.py ---")
    agent_llm_client = LLMClient(**MODELS_CONFIG["agent_model"])

    CASES_DIRECTORY = "./generated_tasks" 
    RESULTS_OUTPUT_DIRECTORY = "./try_log"
    
    if not os.path.exists(CASES_DIRECTORY):
        os.makedirs(CASES_DIRECTORY)
        print(f"Created a sample directory: {CASES_DIRECTORY}")

    eval_batch(
        cases_directory=CASES_DIRECTORY,
        agent_llm_client=agent_llm_client,
        output_directory=RESULTS_OUTPUT_DIRECTORY,
        max_cases=None
    )

if __name__ == "__main__":
    main()