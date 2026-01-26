import json
import os
import time
import concurrent.futures
from typing import Dict, Tuple

from llm import LLMClient
from scene import SceneSynthesizer
from config import MODELS_CONFIG

def generate_safe_filename(blueprint: dict, variant_index: int) -> str:
    """Creates a filesystem-safe, descriptive filename from a blueprint."""
    app = blueprint.get('app_name', 'app').split('(')[0].strip().replace(' ', '_')
    scenario = blueprint.get('scenario_id', 'scenario')
    rule = blueprint.get('rule_id', 'rule')
    return f"{app}_{scenario}_{rule}_var{variant_index}.json"

def synthesis_worker(
    synthesizer: SceneSynthesizer, 
    blueprint: Dict, 
    variant_index: int, 
    output_directory: str
) -> Tuple[str, str]:
    """
    Worker function to synthesize and save a single task.
    This function is executed by each thread in the pool.
    Returns a tuple of (filename, status_string).
    """
    filename = generate_safe_filename(blueprint, variant_index)
    output_path = os.path.join(output_directory, filename)

    if os.path.exists(output_path):
        return (filename, "SKIPPED")

    # Synthesize one task variant
    task_data = synthesizer.synthesize_from_blueprint(blueprint)

    if task_data:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, indent=2, ensure_ascii=False)
            return (filename, "SUCCESS")
        except Exception as e:
            return (filename, f"SAVE_ERROR: {e}")
    else:
        return (filename, "SYNTHESIS_FAILED")

def main():
    blueprint_file = "task_blueprints_add3.json"
    output_directory = "./generated_tasks_add3"
    variants_per_blueprint = 5
    MAX_WORKERS = 50

    # --- Initialization ---
    os.makedirs(output_directory, exist_ok=True)
    
    if not os.path.exists(blueprint_file):
        print(f"[ERROR] Blueprint file not found: '{blueprint_file}'")
        print("Please run 'python pipeline_generator.py' first to generate the blueprints.")
        return

    with open(blueprint_file, 'r', encoding='utf-8') as f:
        blueprints = json.load(f)

    # --- Prepare all jobs ---
    jobs = []
    for bp in blueprints:
        for j in range(variants_per_blueprint):
            jobs.append((bp, j + 1))

    print(f"Loaded {len(blueprints)} task blueprints.")
    print(f"Preparing to generate {len(jobs)} total task variants using up to {MAX_WORKERS} workers.")
    print("-" * 50)

    # --- Concurrent Synthesis Loop ---
    synthesizer_llm_client = LLMClient(**MODELS_CONFIG["synthesizer_model"])
    # Synthesizer is stateless and can be shared across threads
    synthesizer = SceneSynthesizer(synthesizer_llm_client)
    
    total_successful = 0
    total_skipped = 0
    total_failed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all jobs to the executor
        future_to_job = {
            executor.submit(synthesis_worker, synthesizer, job[0], job[1], output_directory): job
            for job in jobs
        }
        
        # Process results as they are completed
        for future in concurrent.futures.as_completed(future_to_job):
            try:
                filename, status = future.result()
                if status == "SUCCESS":
                    print(f"[SUCCESS] Saved task to {filename}")
                    total_successful += 1
                elif status == "SKIPPED":
                    total_skipped += 1
                else: # FAILED
                    print(f"[FAILED] Could not generate {filename}. Reason: {status}")
                    total_failed += 1
            except Exception as exc:
                job_info = future_to_job[future]
                bp_info = job_info[0].get('scenario_id', 'unknown_bp')
                print(f"[ERROR] Job for blueprint '{bp_info}' generated an exception: {exc}")
                total_failed += 1
    
    # Final Summary
    print("\n" + "=" * 50)
    print("CONCURRENT BATCH SYNTHESIS COMPLETE!")
    print(f"  Total tasks successfully generated: {total_successful}")
    print(f"  Total tasks skipped (already exist): {total_skipped}")
    print(f"  Total tasks failed: {total_failed}")
    print(f"All generated tasks are located in: '{output_directory}'")
    print("=" * 50)

if __name__ == "__main__":
    main()