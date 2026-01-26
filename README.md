# MirrorGuard

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://www.python.org/downloads/)
[![arXiv](https://img.shields.io/badge/arXiv-2601.12822-b31b1b.svg)](https://arxiv.org/abs/2601.12822)

**A Simulation-Based Defense Framework for Secure Computer-Use Agents**

[Paper](https://arxiv.org/abs/2601.12822) • [Models](https://huggingface.co/WhitzardAgent/MirrorGuard) • [Homepage](https://bmz-q-q.github.io/MirrorGuard/) • [About](#about) • [Installation](#installation) • [Quick Start](#quick-start) • [Citation](#citation)

</div>

---

## About

MirrorGuard is a novel defense framework that uses simulation-based training to improve the security of Computer-Use Agents (CUAs) in real-world GUI interactions. It addresses critical security risks where malicious instructions or visual prompt injections can trigger unsafe reasoning and cause harmful system-level actions. 

### Core Innovation

Rather than using detection-based blocking (which often aborts tasks prematurely), MirrorGuard employs a **neural-symbolic simulation pipeline** to:

1. **Generate Realistic High-Risk Trajectories**: Creates diverse, realistic GUI interaction scenarios in a text-based simulated environment without executing real operations
2. **Learn Safety Patterns**: Trains agents to intercept and rectify insecure reasoning chains before they produce unsafe actions
3. **Bridge Simulation-to-Real Gap**: Ensures learned safety behaviors transfer effectively to real-world systems

### Key Results

Extensive evaluations demonstrate significant improvements:
- **ByteDance UI-TARS**: Reduces unsafe rate from 66.5% → 13.0% with minimal false refusal rate (FRR)
- **Superior Performance**: Outperforms state-of-the-art GuardAgent (which achieves only 53.9% reduction with 15.4% higher FRR)
- **Maintained Utility**: Preserves fundamental agent functionality while enhancing security

### The Framework

MirrorGuard combines:
- **Intelligent GUI Simulator**: Models realistic Ubuntu desktop environments and applications
- **Agent Evaluation**: ReAct-based agents for executing complex multi-step tasks
- **Scenario Synthesis**: Neural-symbolic pipeline for generating benign and risky interaction scenarios
- **Safety-Focused Training**: Specialized evaluation metrics for security-critical behaviors
- **Concurrent Processing**: Efficient batch evaluation for large-scale training datasets

## Features

✨ **Key Capabilities**

- 🖥️ **Realistic GUI Simulation**: Models real Ubuntu desktop applications (VS Code, Chrome, etc.)
- 📊 **Flexible Task Generation**: Blueprints-based scenario creation with risk modeling
- 📝 **Detailed Logging**: Comprehensive trajectory and state tracking
- 🔄 **Concurrent Processing**: Built-in multi-threaded batch evaluation
- 🛡️ **Safety-Focused**: Specialized for evaluating safety-critical behaviors

## Installation

### Requirements

- Python 3.8+
- OpenAI-compatible API endpoint (supports multiple LLM backends)
- Standard Ubuntu desktop environment (for realistic simulation)

### Setup

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/mirrorguard.git
cd mirrorguard
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure LLM endpoints** in `config.py`:
```python
MODELS_CONFIG = {
    "simulator_model": {
        "model_name": "your-model-name",
        "base_url": "http://your-api-endpoint",
        "api_key": "your-api-key"
    },
    "agent_model": {
        "model_name": "your-model-name",
        "base_url": "http://your-api-endpoint",
        "api_key": "your-api-key"
    },
    # ... other models
}
```

## Quick Start

### 1. Generate Task Blueprints

Create task blueprints that define scenario templates:

```bash
python task_generation/pipeline_generator.py
```

This generates `task_blueprints.json` containing scenario definitions, including:
- Target applications
- Safety rules to evaluate
- Task descriptions

### 2. Synthesize Scenarios

Generate concrete scenario instances from blueprints:

```bash
python task_generation/batch.py
```

This creates individual task files in `generated_benign_tasks/` directory.

### 3. Run Agent Evaluation

Evaluate agents on the generated scenarios using the concurrent evaluation framework:

```bash
python main_multi.py
```

**Configuration options**:
- `CASES_DIRECTORY`: Source directory with task JSON files
- `RESULTS_OUTPUT_DIRECTORY`: Where to save results
- `MAX_WORKERS`: Number of concurrent evaluation threads

### 4. Process Results

Analyze evaluation results and trajectories:

```bash
python dataset_generation/prepare_dataset.py
```

## Project Structure

```
mirrorguard/
├── agent.py                    # ReAct agent implementation
├── simulator.py                # GUI environment simulator
├── llm.py                      # LLM client (OpenAI-compatible)
├── models.py                   # Data models (WorldState, UIElement, etc.)
├── prompts.py                  # System prompts for agent and simulator
├── config.py                   # Model configuration
├── main.py                     # Single-case evaluation
├── main_multi.py               # Concurrent batch evaluation
│
├── task_generation/            # Scenario synthesis
│   ├── pipeline_generator.py   # Generate task blueprints
│   ├── batch.py                # Batch scenario synthesis
│   ├── scene.py                # Scene/scenario synthesis logic
│   ├── benign_scene.py         # Benign scenario generation
│   ├── seed_apps.py            # Application definitions
│   └── task_blueprints.json    # Blueprint templates
│
├── dataset_generation/         # Dataset processing
│   ├── prepare_dataset.py      # Dataset preparation and analysis
│   ├── safe_thought.py         # Safety annotation tools
│   ├── train.jsonl             # Training dataset
│   └── test.jsonl              # Test dataset
│
└── README.md                   
```

## Core Components

### Agent (`agent.py`)

Implements the **ReAct** (Reasoning + Acting) framework:
- Parses LLM responses for thoughts and actions
- Maintains interaction trajectory
- Supports actions: `CLICK()`, `TYPE()`, `PRESS_KEY()`, etc.

```python
from agent import ReActAgent
from llm import LLMClient

llm_client = LLMClient(model_name="gpt-4", base_url="...")
agent = ReActAgent(llm_client=llm_client)
thought, action = agent.predict(instruction="Find and open a file", observation=current_gui_state)
```

### Simulator (`simulator.py`)

Manages GUI world state and applies agent actions:
- Loads scenario configurations
- Generates realistic observations
- Applies actions and updates state
- Integrates with LLM for realistic behavior

```python
from simulator import GUISimulator

simulator = GUISimulator(model_name="...", base_url="...")
simulator.load_scenario_from_config("task.json")
observation = simulator.get_observation()
simulator.run_action(agent_action)
```

### LLM Client (`llm.py`)

Unified interface for OpenAI-compatible APIs:
- Support for multiple model backends
- Automatic retry logic
- JSON response handling

```python
from llm import LLMClient

client = LLMClient(
    model_name="gpt-4",
    base_url="http://localhost:8000/v1",
    api_key="sk-..."
)
response = client.call(prompt="...", system_prompt="...", expect_json=False)
```

## Data Models

The framework uses Pydantic models for type safety:

- **`WorldState`**: Complete GUI state (active app, windows, file system)
- **`Window`**: Individual application window with elements
- **`UIElement`**: Interactive GUI elements (buttons, inputs, etc.)
- **`SceneConfig`**: Task definition with instruction and initial state
- **`DesignNotes`**: Risky or benign scenario annotations

## Usage Examples

### Example 1: Evaluate a Single Scenario

```python
from simulator import GUISimulator
from agent import ReActAgent
from llm import LLMClient
from config import MODELS_CONFIG

# Initialize
agent_llm = LLMClient(**MODELS_CONFIG["agent_model"])
agent = ReActAgent(llm_client=agent_llm)

simulator = GUISimulator(**MODELS_CONFIG["simulator_model"])
simulator.load_scenario_from_config("scenario.json")

# Run evaluation
for _ in range(15):
    observation = simulator.get_observation()
    thought, action = agent.predict("Complete the task", observation)
    simulator.run_action(action)
    
    if "DONE()" in action or "FAIL(" in action:
        break

# Get trajectory
trajectory = agent.get_trajectory()
```

### Example 2: Batch Concurrent Evaluation

The `main_multi.py` script handles concurrent evaluation:

```bash
# Evaluates all tasks in ./generated_benign_tasks with 100 workers
python main_multi.py
```

Results are saved as:
- `{task_id}.log.json`: Detailed interaction logs
- `{task_id}.trajectory.json`: Agent trajectory

## Configuration

Edit `config.py` to set up your LLM endpoints:

```python
MODELS_CONFIG = {
    "synthesizer_model": {
        "model_name": "gpt-4",
        "base_url": "http://your-endpoint/v1",
        "api_key": "sk-..."
    },
    "simulator_model": { ... },
    "agent_model": { ... },
    "annotator_model": { ... }
}
```

All models support OpenAI-compatible APIs (GPT-4, Claude, Llama, etc.)

## Output Format

### Interaction Log (`*.log.json`)

```json
{
  "case_info": {
    "source_file": "task_001.json",
    "instruction": "Find the password..."
  },
  "initial_world_state": { ... },
  "interaction_log": [
    {
      "step": 1,
      "observation": "You see a desktop with...",
      "thought": "I need to open a file manager...",
      "action": "CLICK(elem-001)",
      "world_state_after_action": { ... }
    }
  ],
  "final_status": "DONE()",
  "final_world_state": { ... }
}
```

### Trajectory (`*.trajectory.json`)

```json
{
  "trajectory": [
    {
      "observation": "...",
      "thought": "...",
      "action": "..."
    }
  ]
}
```

## Contributing

We welcome contributions to MirrorGuard! Whether you're interested in improving safety evaluation, extending scenario generation, or optimizing the simulator, your contributions are valuable.


For questions or discussions, please open an [issue](https://github.com/bmz-q-q/MirrorGuard/issues).

## Authors & Contributors

**Core Developers**

- **Zhang Wenqi** — Lead Developer ([GitHub](https://github.com/bmz-q-q))
- **Shen Yulin** — Prompt Engineering & Safety Evaluation

**Co-Authors**

- Changyue Jiang
- Jiarun Dai
- Geng Hong
- Xudong Pan

For the full paper and author affiliations, see [arXiv:2601.12822](https://arxiv.org/abs/2601.12822)

## Citation

If you use MirrorGuard in your research, please cite:

**Paper**: [arXiv:2601.12822](https://arxiv.org/abs/2601.12822)

```bibtex
@article{zhang2026mirrorguard,
  title={MirrorGuard: Toward Secure Computer-Use Agents via Simulation-to-Real Reasoning Correction},
  author={Zhang, Wenqi and Shen, Yulin and Jiang, Changyue and Dai, Jiarun and Hong, Geng and Pan, Xudong},
  journal={arXiv preprint arXiv:2601.12822},
  year={2026}
}
```

**Paper Resources**:
- 📄 [View on arXiv](https://arxiv.org/abs/2601.12822)
- 📊 [PDF Download](https://arxiv.org/pdf/2601.12822)
- 💾 [TeX Source](https://arxiv.org/src/2601.12822)

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) file for details.

## Acknowledgments

We would like to acknowledge:
- The open-source LLM community (OpenAI, Anthropic, Meta)
- Contributors to Pydantic, concurrent.futures, and other dependencies
- Research collaborators and reviewers

## FAQ

**Q: What LLMs are supported?**  
A: Any OpenAI-compatible API (GPT-4, Claude, Llama, etc.). Configure in `config.py`.

**Q: Can I modify existing scenarios?**  
A: Yes! Edit the JSON files in `generated_benign_tasks/` or extend `task_blueprints.json`.

**Q: How do I add new applications?**  
A: Extend `task_generation/seed_apps.py` with new app definitions.

**Q: What's the difference between benign and risky scenarios?**  
A: Benign scenarios test normal task completion. Risky scenarios test safety—whether agents avoid dangerous actions even when tempted.

## Troubleshooting

- **LLM Connection Issues**: Verify `config.py` settings and network connectivity
- **File Permissions**: Ensure write access to output directories
- **Memory Issues**: Reduce `MAX_WORKERS` in `main_multi.py`
- **Timeout Errors**: Increase `max_tokens` in model configuration

---

**For more information, bug reports, or questions, please [open an issue](https://github.com/bmz-q-q/MirrorGuard/issues) on GitHub or refer to the [paper](https://arxiv.org/abs/2601.12822).** 