# file: main.py (Concurrent Version)

import os
import json
import concurrent.futures
from pathlib import Path
from typing import Optional, Dict, Any

from simulator import GUISimulator
from agent import ReActAgent
from llm import LLMClient
from config import MODELS_CONFIG

def save_json_log(data: Dict, output_path: Path):
    try:
        with open(output_path, 'w', encoding='utf-8') as f:  
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[ERROR] Failed to save file to {output_path}: {e}")

def run_single_case(case_path: str, agent: ReActAgent, output_directory: str, max_steps: int = 15):
    case_path_obj = Path(case_path)
    output_dir_obj = Path(output_directory)
    output_dir_obj.mkdir(parents=True, exist_ok=True)
    base_filename = case_path_obj.stem
    detailed_log_output_path = output_dir_obj / f"{base_filename}.log.json"
    trajectory_output_path = output_dir_obj / f"{base_filename}.trajectory.json"

 
    print(f"\n{'='*20} RUNNING CASE: {case_path_obj.name} {'='*20}")
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

        for i in range(max_steps):
            step_number = i + 1
 
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
          
            if "DONE()" in agent_action or "FAIL(" in agent_action or "WAIT()" in agent_action:
                final_status = agent_action
                print(f"--- Task finished for case {base_filename} with status: {final_status} ---")
                break
        else:
            final_status = f"Max steps reached ({max_steps})"
    
        full_log_data["final_status"] = final_status
        if full_log_data["interaction_log"]:
            full_log_data["final_world_state"] = full_log_data["interaction_log"][-1]["world_state_after_action"]

    except Exception as e:
        print(f"[ERROR] An unexpected error occurred while running case {base_filename}: {e}")
        if "case_info" in full_log_data:
            full_log_data["final_status"] = f"Error: {str(e)}"
    
    finally:
        if full_log_data:
            save_json_log(full_log_data, detailed_log_output_path)
        
        trajectory_data = agent.get_trajectory()
        if trajectory_data:
            save_json_log({"trajectory": trajectory_data}, trajectory_output_path)
            
    return f"Case {base_filename} completed with status: {final_status}"


def run_case_worker(case_path: str, agent_llm_client: LLMClient, output_directory: str) -> str:
    agent = ReActAgent(llm_client=agent_llm_client)
    return run_single_case(case_path, agent, output_directory)


def eval_batch_concurrent(
    cases_directory: str, 
    agent_llm_client: LLMClient, 
    output_directory: str,
    max_cases: Optional[int] = None,
    max_workers: int = 4
):
    print(f"\n--- Starting Concurrent Batch Evaluation for directory: {cases_directory} ---")
    print(f"--- Using a maximum of {max_workers} concurrent workers ---")
    
    p = Path(cases_directory)
    if not p.is_dir():
        print(f"[ERROR] Directory not found: {cases_directory}")
        return
        
    all_case_files = sorted(list(p.glob("*.json")))
    
    cases_to_run_paths = []
    for case_path in all_case_files:
        base_filename = case_path.stem
        detailed_log_output_path = Path(output_directory) / f"{base_filename}.log.json"
        trajectory_output_path = Path(output_directory) / f"{base_filename}.trajectory.json"
        if detailed_log_output_path.exists() and trajectory_output_path.exists():
            print(f"[SKIP] {base_filename}: Log and trajectory files already exist.")
        else:
            cases_to_run_paths.append(case_path)

    if max_cases is not None and max_cases > 0:
        cases_to_run = cases_to_run_paths[:max_cases]
        print(f"Found {len(all_case_files)} total cases, {len(cases_to_run_paths)} remaining. Running the first {len(cases_to_run)}.")
    else:
        cases_to_run = cases_to_run_paths
        print(f"Found {len(all_case_files)} total cases. Running all {len(cases_to_run)} remaining cases.")

    if not cases_to_run:
        print("No new cases to run.")
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
     
        future_to_case = {
            executor.submit(run_case_worker, str(case_path), agent_llm_client, output_directory): case_path
            for case_path in cases_to_run
        }
        
     
        for future in concurrent.futures.as_completed(future_to_case):
            case_path = future_to_case[future]
            try:
                result = future.result()
                print(f"[RESULT] {result}")
            except Exception as exc:
                print(f"[ERROR] Case '{case_path.name}' generated an exception: {exc}")

def main():
    print("--- Initializing LLM Clients from config.py ---")
  
    agent_llm_client = LLMClient(**MODELS_CONFIG["agent_model"])

    CASES_DIRECTORY = "./generated_benign_tasks" 
    RESULTS_OUTPUT_DIRECTORY = "./benign"

    MAX_WORKERS = 100

    if not os.path.exists(CASES_DIRECTORY):
        os.makedirs(CASES_DIRECTORY)
        print(f"Created a sample directory: {CASES_DIRECTORY}")

    eval_batch_concurrent(
        cases_directory=CASES_DIRECTORY,
        agent_llm_client=agent_llm_client,
        output_directory=RESULTS_OUTPUT_DIRECTORY,
        max_cases=None,  
        max_workers=MAX_WORKERS
    )

if __name__ == "__main__":
    main()