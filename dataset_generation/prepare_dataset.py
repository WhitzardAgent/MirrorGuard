import json
import os
import random
import math

SAFE_SAMPLES_FILE = "" # "dataset/safe_samples.jsonl"
UNSAFE_SAMPLES_FILE = "" #"dataset/unsafe_samples.jsonl"


OUTPUT_TRAIN_FILE = "dataset/sharegpt_train.jsonl"
OUTPUT_TEST_FILE = "dataset/sharegpt_test.jsonl"

TEST_SET_RATIO = 0.1
RANDOM_SEED = 42

SYSTEM_PROMPT = """You are an expert AI Safety Thought Corrector.
Your task is to correct an agent's thought based on the provided instruction, history, and observation.
You must follow these rules:
1. If the thought is already safe, helpful, and logical for the given context, you MUST output the thought verbatim, without any changes.
2. If the thought is unsafe, ignores risks, or is illogical, you MUST correct it into a safe, helpful, and logical thought that still aims to solve the user's goal safely."""


USER_QUERY_TEMPLATE = """### Context ###
Instruction: {instruction}
{history_block}
<observation>
{observation}
</observation>

### Original Thought ###
{original_thought}"""


def load_samples(filepath: str) -> list:
    if not os.path.exists(filepath):
        print(f"[ERROR] Input file not found: {filepath}")
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

def parse_question(question: str) -> dict:
    parts = {}
    try:
        parts['instruction'] = question.split('\n')[0].strip()
        obs_start = question.find('<observation>')
        obs_end = question.find('</observation>')
        if obs_start != -1 and obs_end != -1:
            parts['observation'] = question[obs_start+len('<observation>'):obs_end].strip()
        else:
            parts['observation'] = "No observation provided."
        hist_start = question.find('History:')
        if hist_start != -1:
            hist_end = obs_start if obs_start != -1 else len(question)
            history_text = question[hist_start:hist_end].strip()
            parts['history_block'] = f"History:\n{history_text.replace('History:', '').strip()}"
        else:
            parts['history_block'] = "History:\nThis is the first step."
        return parts
    except Exception as e:
        print(f"Warning: Failed to parse question string. Using fallbacks. Error: {e}\nQuestion: {question[:100]}...")
        return {'instruction': 'N/A', 'history_block': 'History:\nN/A', 'observation': 'N/A'}

def create_sharegpt_format(context_parts: dict, original_thought: str, corrected_thought: str) -> dict:
    user_content = USER_QUERY_TEMPLATE.format(
        instruction=context_parts['instruction'],
        history_block=context_parts['history_block'],
        observation=context_parts['observation'],
        original_thought=original_thought
    )
    
    conversations = [
        {
            "from": "human",
            "value": user_content
        },
        {
            "from": "gpt",
            "value": corrected_thought
        }
    ]
    
    return {
        "system": SYSTEM_PROMPT,
        "conversations": conversations
    }


def save_samples_to_file(filepath: str, samples: list):
    with open(filepath, 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    print(f"Successfully saved {len(samples)} samples to: {filepath}")


def main():
    print("--- Starting ShareGPT Data Preparation Script (V2 - Standard Format) ---")
    random.seed(RANDOM_SEED)

    safe_samples = load_samples(SAFE_SAMPLES_FILE)
    unsafe_samples = load_samples(UNSAFE_SAMPLES_FILE)

    if not safe_samples and not unsafe_samples:
        print("[ERROR] Both input files are empty or not found. Exiting.")
        return
        
    print(f"Loaded {len(safe_samples)} safe samples and {len(unsafe_samples)} unsafe samples.")
    
    all_formatted_samples = []
    all_samples = [("unsafe", s) for s in unsafe_samples] + [("safe", s) for s in safe_samples]

    for sample_type, sample in all_samples:
        context_parts = parse_question(sample['question'])
        original_thought = sample['answer']
        assistant_thought = sample['correction'] if sample_type == "unsafe" else sample['answer']

        sharegpt_sample = create_sharegpt_format(context_parts, original_thought, assistant_thought)
        all_formatted_samples.append(sharegpt_sample)
        
    print("\nShuffling all samples...")
    random.shuffle(all_formatted_samples)
    
    total_samples = len(all_formatted_samples)
    print(f"Total formatted samples: {total_samples}")

    test_set_size = math.ceil(total_samples * TEST_SET_RATIO)
    test_samples = all_formatted_samples[:test_set_size]
    train_samples = all_formatted_samples[test_set_size:]

    print(f"\nSplitting data with a {TEST_SET_RATIO*100:.1f}% test set ratio...")
    print(f"  - Training set size: {len(train_samples)}")
    print(f"  - Testing set size:  {len(test_samples)}")

    if train_samples:
        save_samples_to_file(OUTPUT_TRAIN_FILE, train_samples)
    else:
        print("Warning: Training set is empty. No train file will be created.")

    if test_samples:
        save_samples_to_file(OUTPUT_TEST_FILE, test_samples)
    else:
        print("Warning: Test set is empty. No test file will be created.")
            
    print("\n--- Data Preparation Complete! ---")

if __name__ == "__main__":
    main()