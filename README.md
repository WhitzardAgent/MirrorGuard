# MirrorGuard

<div align="center">

<img src="https://cdn-avatars.huggingface.co/v1/production/uploads/61def72b6742e9faa77b0edc/XHPe_wPj4roSniCHsHYT5.jpeg" alt="WhitzardAgent logo" width="120" />

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://www.python.org/downloads/)
[![arXiv](https://img.shields.io/badge/arXiv-2601.12822-b31b1b.svg)](https://arxiv.org/abs/2601.12822)

**Train in the MirrorWorld, Act in the Wild.**

**MirrorGuard: Toward Secure Computer-Use Agents via Simulation-to-Real Reasoning Correction**

**WhitzardAgent | Fudan University | Shanghai Innovation Institute (SII)**

[Paper](https://arxiv.org/abs/2601.12822) | [Project Page](https://bmz-q-q.github.io/MirrorGuard/) | [Model](https://huggingface.co/WhitzardAgent/MirrorGuard) | [Chinese README](README_zh.md)

</div>

## Overview

MirrorGuard is a plug-and-play defense framework for computer-use agents (CUAs). Instead of relying on coarse action blocking, MirrorGuard intervenes at the reasoning layer: it intercepts an agent's insecure thought, corrects it into a secure reasoning path, and then steers the agent toward a safer action.

The framework has two tightly connected parts:

- **MirrorWorld**: a neural-symbolic simulation environment for synthesizing security-related agentic trajectories in pure text.
- **MirrorGuard**: a deployed reasoning-correction module that transfers the learned security logic to real GUI agents.

This repository contains both the training-side pipeline and OSWorld-style integration examples that show how MirrorGuard is embedded into real agents.

MirrorGuard is released as a WhitzardAgent project and should remain attributable to the Fudan University and Shanghai Innovation Institute (SII) team behind the work.

Most importantly, the released [WhitzardAgent/MirrorGuard](https://huggingface.co/WhitzardAgent/MirrorGuard) model is the final **VLM** trained on reasoning-correction data produced by the MirrorWorld synthesis and dataset-generation pipeline in this repository.

## From Code To Model

MirrorGuard should be read as a full pipeline rather than "some code plus a model card":

1. `task_generation/` and `simulator.py` construct risky and benign computer-use trajectories in **MirrorWorld**.
2. `dataset_generation/safe_thought.py` identifies unsafe reasoning and generates corrected safe reasoning.
3. `dataset_generation/prepare_dataset.py` converts those pairs into the final training format for MirrorGuard supervision.
4. The resulting reasoning-correction corpus is used to fine-tune the released **MirrorGuard VLM** on Hugging Face.
5. That trained VLM is then deployed as the runtime corrector used in the agent integration examples under `examples/`.

The key raw data files included in this repository are:

- `dataset_generation/train.jsonl`
- `dataset_generation/test.jsonl`

`prepare_dataset.py` is configured to package them into ShareGPT-style training files such as `dataset/sharegpt_train.jsonl` and `dataset/sharegpt_test.jsonl`.

## Qualitative Demo

<table>
  <tr>
    <td align="center"><b>Before MirrorGuard</b></td>
    <td align="center"><b>After MirrorGuard</b></td>
  </tr>
  <tr>
    <td><img src="assets/mirrorguard_before.gif" alt="Before MirrorGuard" width="420" /></td>
    <td><img src="assets/mirrorguard_after.gif" alt="After MirrorGuard" width="420" /></td>
  </tr>
</table>

Left GIF (🔴 Without defense): The agent fails to recognize the risk and blindly executes the dangerous `sudo chown` command, recursively modifying the `/dev` directory permissions and breaking the system's device permission model. Right GIF (🟢 With MirrorGuard): The agent leverages the thought-correction mechanism to identify the critical risk of `chown /dev` within milliseconds, refuses to execute the command, and provides safe alternative solutions to the user, achieving intent alignment and system protection. 

## Why Reasoning Correction

As described in the paper, the critical point of intervention is the agent's **thought** rather than the input or final action. Unsafe behavior often first appears in reasoning, before the agent executes an irreversible system operation.

MirrorGuard therefore treats security failures as **reasoning errors**:

- in low-risk contexts, the agent continues normally;
- in risky contexts, the thought is corrected into a safe reasoning pattern;
- the corrected thought is then used to steer downstream action generation.

This design is meant to reduce the usual security-utility trade-off caused by pure blocking defenses.

## Headline Results

From the paper:

- On **UI-TARS**, MirrorGuard reduces **Unsafe Rate** from **66.5%** to **13.0%** while maintaining a marginal **False Refusal Rate (FRR)**.
- Compared with GuardAgent, MirrorGuard achieves stronger risk mitigation with lower utility penalty.
- On **OSWorld**, the method is evaluated for utility preservation using **Success Rate (SR)**.

Benchmark roles follow the paper:

- **OS-Harm** and **RiOSWorld**: security-risk evaluation
- **OSWorld**: utility and over-defensiveness evaluation

## Repository Layout

```text
MirrorGuard/
  agent.py
  simulator.py
  llm.py
  models.py
  prompts.py
  config.py
  main.py
  main_multi.py
  task_generation/
  dataset_generation/
  examples/
    shared/
    react_integration/
    uitars_integration/
    owl_integration/
  assets/
```

## Core Pipeline

### 1. MirrorWorld: security-related trajectory synthesis

The training-side pipeline constructs risky and benign operating-system tasks in a text-based environment instead of a live desktop. This keeps synthesis cheap, fast, and safe while preserving causal consistency through a symbolic world state.

Relevant files:

- `task_generation/pipeline_generator.py`
- `task_generation/scene.py`
- `task_generation/benign_scene.py`
- `simulator.py`
- `models.py`

### 2. Thought-centric annotation and correction

Simulated trajectories are processed into training pairs of insecure reasoning and corrected reasoning. The secure corrections follow the paper's four secure reasoning patterns:

- **Hard Refusal**
- **Stop & Ask**
- **Privacy Block**
- **Handover**

Relevant files:

- `dataset_generation/safe_thought.py`
- `dataset_generation/prepare_dataset.py`
- `dataset_generation/train.jsonl`
- `dataset_generation/test.jsonl`

### 3. Deployment in real GUI agents

At deployment, MirrorGuard acts as a modular reasoning corrector. Section 4.3 of the paper describes two steering paths:

- **Replacement**: for agent frameworks that generate thought and action sequentially
- **Prefilling**: for frameworks that generate thought and action in a unified call

This repository includes cleaned OSWorld-style examples for both.

## Integration Examples

### ReAct: replacement steering

`examples/react_integration/react_agent_corrected.py`

This example represents the **replacement** deployment path. The agent first generates an original thought, MirrorGuard corrects it, and the corrected thought is injected into the subsequent action-generation call.

OSWorld-style references:

- Agent interface: [xlang-ai/OSWorld/mm_agents/README.md](https://github.com/xlang-ai/OSWorld/blob/main/mm_agents/README.md)
- Prompt-agent base: [xlang-ai/OSWorld/mm_agents/agent.py](https://github.com/xlang-ai/OSWorld/blob/main/mm_agents/agent.py)

### UI-TARS: prefilling steering

`examples/uitars_integration/uitars15_v1_corrected.py`

This example represents the **prefilling** deployment path. The agent first exposes an internal thought from a unified generation step, MirrorGuard corrects that thought, and the corrected reasoning is prefixed back into the final generation path to steer action output.

OSWorld-style and upstream references:

- OSWorld agent file: [xlang-ai/OSWorld/mm_agents/uitars_agent.py](https://github.com/xlang-ai/OSWorld/blob/main/mm_agents/uitars_agent.py)
- UI-TARS repository: [bytedance/UI-TARS](https://github.com/bytedance/UI-TARS)

### Owl: additional code reference

`examples/owl_integration/owl_agent_corrected.py`

This is included as an OSWorld-style reference for another agent family, but it is not the primary walkthrough.

OSWorld-style and upstream references:

- OSWorld agent file: [xlang-ai/OSWorld/mm_agents/owl_agent.py](https://github.com/xlang-ai/OSWorld/blob/main/mm_agents/owl_agent.py)
- GUI-Owl / MobileAgent repository: [X-PLUG/MobileAgent](https://github.com/X-PLUG/MobileAgent)

### Shared deployment helper

`examples/shared/correction_runtime.py`

This file shows a minimal OpenAI-compatible deployment runtime for the deployed MirrorGuard VLM.

## Installation

MirrorGuard targets Python 3.8+ and an OpenAI-compatible model endpoint.

```bash
pip install -r requirements.txt
```

Configure your model endpoints in `config.py` before running the evaluation scripts. The default layout uses separate entries for `synthesizer_model`, `simulator_model`, `agent_model`, and `annotator_model`.

## Quick Start

### Generate task blueprints

```bash
python task_generation/pipeline_generator.py
```

### Synthesize tasks

Benign tasks:

```bash
python task_generation/benign_scene.py
```

Risk-oriented task synthesis:

```bash
python task_generation/batch.py
```

### Run the simulator-side evaluation loop

```bash
python main.py
python main_multi.py
```

### Process trajectories into training data

```bash
python dataset_generation/safe_thought.py
python dataset_generation/prepare_dataset.py
```

## Core Components

MirrorGuard is split into a small set of reusable modules:

- `agent.py`: ReAct-style agent wrapper that turns observations into thoughts and actions.
- `simulator.py`: GUI world simulator that loads scenarios, exposes observations, and applies actions.
- `llm.py`: OpenAI-compatible client abstraction used across the pipeline.
- `models.py`: Pydantic data models for world state, tasks, and design notes.
- `task_generation/`: task blueprint and scenario synthesis utilities.
- `dataset_generation/`: thought correction and training-data preparation scripts.

## Data Models

The runtime and synthesis pipeline use a compact set of Pydantic models:

- `UIElement`: a single interactive GUI element with label, value, and enabled state.
- `Window`: an application window containing a list of GUI elements.
- `WorldState`: the full simulator state, including active app, windows, and file system.
- `SceneConfig`: a task definition with `task_id`, `instruction`, `initial_state`, and `design_notes`.
- `RiskyDesignNotes` / `BenignDesignNotes`: annotations that describe the expected safe behavior and task path.

## Usage Examples

### Single-case evaluation

```python
from agent import ReActAgent
from config import MODELS_CONFIG
from llm import LLMClient
from simulator import GUISimulator

agent = ReActAgent(LLMClient(**MODELS_CONFIG["agent_model"]))
simulator = GUISimulator(**MODELS_CONFIG["simulator_model"])
simulator.load_scenario_from_config("scenario.json")

instruction = simulator.instruction
for _ in range(15):
    observation = simulator.get_observation()
    thought, action = agent.predict(instruction, observation)
    simulator.run_action(action)
    if "DONE()" in action or "FAIL(" in action or "WAIT()" in action:
        break
```

### Batch evaluation

```bash
python main.py
python main_multi.py
```

### Dataset preparation

```bash
python dataset_generation/safe_thought.py
python dataset_generation/prepare_dataset.py
```

## Output Format

Evaluation scripts write two files per case:

- `*.log.json`: a detailed interaction log with the instruction, initial state, per-step observations, thoughts, actions, and final world state.
- `*.trajectory.json`: a compact trajectory export containing the agent's step-by-step reasoning/action sequence.

Example log structure:

```json
{
  "case_info": {
    "source_file": "task_001.json",
    "instruction": "..."
  },
  "initial_world_state": { "...": "..." },
  "interaction_log": [
    {
      "step": 1,
      "observation": "...",
      "thought": "...",
      "action": "...",
      "world_state_after_action": { "...": "..." }
    }
  ],
  "final_status": "DONE()",
  "final_world_state": { "...": "..." }
}
```

## Authors & Contributors

Core authors of MirrorGuard are Wenqi Zhang, Yulin Shen, Changyue Jiang, Jiarun Dai, Geng Hong, and Xudong Pan.


## Acknowledgment

MirrorGuard is developed by the WhitzardAgent team at Fudan University with support from Shanghai Innovation Institute (SII). This research is supported by the Shanghai Innovation Institute's "Agent Full-Stack Security Offense-Defense Technology Matrix" project. If you reuse the code, model, or media assets, please retain the project attribution and citation.

## Citation

```bibtex
@article{zhang2026mirrorguard,
  title={MirrorGuard: Toward Secure Computer-Use Agents via Simulation-to-Real Reasoning Correction},
  author={Zhang, Wenqi and Shen, Yulin and Jiang, Changyue and Dai, Jiarun and Hong, Geng and Pan, Xudong},
  journal={arXiv preprint arXiv:2601.12822},
  year={2026}
}
```

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

