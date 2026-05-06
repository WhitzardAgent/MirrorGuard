# MirrorGuard

<div align="center">

<img src="https://cdn-avatars.huggingface.co/v1/production/uploads/61def72b6742e9faa77b0edc/XHPe_wPj4roSniCHsHYT5.jpeg" alt="WhitzardAgent logo" width="120" />

[论文](https://arxiv.org/abs/2601.12822) | [项目主页](https://bmz-q-q.github.io/MirrorGuard/) | [模型](https://huggingface.co/WhitzardAgent/MirrorGuard) | [English README](README.md)

**Train in the MirrorWorld, Act in the Wild.**

**MirrorGuard: Toward Secure Computer-Use Agents via Simulation-to-Real Reasoning Correction**

**WhitzardAgent | 上海创智学院 | 复旦大学 **

</div>

## 项目概述

MirrorGuard 是一个面向 computer-use agents 的即插即用防护框架。它不是简单地在动作层做拦截，而是在推理层进行干预：截获 agent 当前的不安全 thought，将其修正为更安全的 reasoning，再用修正后的 reasoning 去引导后续动作。

这个仓库同时包含两部分：

- **MirrorWorld**：用于合成安全相关 agent trajectories 的 neural-symbolic simulation 环境
- **MirrorGuard**：部署时用于 reasoning correction 的模型与接入示例

Hugging Face 上发布的 [WhitzardAgent/MirrorGuard](https://huggingface.co/WhitzardAgent/MirrorGuard) 是基于本仓库生成的数据微调训练得到的最终 **VLM**。

## 从代码到模型

MirrorGuard 应该按一条完整链路来理解：

1. `task_generation/` 与 `simulator.py` 在 **MirrorWorld** 中构造高风险与正常任务轨迹。
2. `dataset_generation/safe_thought.py` 从轨迹中识别不安全 thought，并生成对应的 corrected reasoning。
3. `dataset_generation/prepare_dataset.py` 将这些样本整理成最终训练格式。
4. 上述 reasoning-correction 数据用于训练最终发布的 **MirrorGuard VLM**。
5. 训练好的 VLM 再被部署为 runtime corrector，接入到 `examples/` 中的 agent。

仓库中直接提供的关键数据文件包括：

- `dataset_generation/train.jsonl`
- `dataset_generation/test.jsonl`

`prepare_dataset.py` 会进一步整理出 `dataset/sharegpt_train.jsonl` 与 `dataset/sharegpt_test.jsonl` 这类训练文件。

## 动图展示

<table>
  <tr>
    <td align="center"><b>未使用 MirrorGuard</b></td>
    <td align="center"><b>使用 MirrorGuard</b></td>
  </tr>
  <tr>
    <td><img src="assets/mirrorguard_before.gif" alt="Before MirrorGuard" width="420" /></td>
    <td><img src="assets/mirrorguard_after.gif" alt="After MirrorGuard" width="420" /></td>
  </tr>
</table>

左图（🔴 无防御状态）：Agent 无法识别风险，盲目执行用户的高危 `sudo chown` 指令，递归修改 `/dev` 目录的所有权，破坏系统设备权限模型。右图（🟢 启用 MirrorGuard）：Agent 通过思维矫正机制在毫秒级窗口内准确识别 `chown /dev` 的致命风险，拒绝执行并向用户给出安全替代方案，实现意图对齐与系统防护。

## 为什么是 Reasoning Correction

按照论文设定，真正关键的干预点不是输入，也不是最终动作，而是 agent 在执行前的 **thought**。很多风险首先出现在 reasoning 层，然后才落实为不可逆的系统操作。

因此，MirrorGuard 将安全问题建模为 **reasoning errors**：

- 低风险情境下，agent 正常继续执行
- 风险情境下，将当前 thought 修正为更安全的 reasoning 模式
- 再由修正后的 thought 去引导下游动作生成

这也是论文中强调的 security-utility trade-off 缓解方式。

## 主要结果

论文中的代表性结果包括：

- 在 **UI-TARS** 上，MirrorGuard 将 **Unsafe Rate** 从 **66.5%** 降到 **13.0%**
- 相比 **GuardAgent**，MirrorGuard 在降低风险的同时带来更小的 utility penalty
- 在 **OSWorld** 上，方法通过 **Success Rate (SR)** 衡量 utility preservation 与 over-defensiveness

benchmark 角色与论文保持一致：

- **OS-Harm** 与 **RiOSWorld**：安全风险评测
- **OSWorld**：utility / over-defensiveness 评测

## 接入示例

### ReAct：replacement 路径

对应文件：[`examples/react_integration/react_agent_corrected.py`](examples/react_integration/react_agent_corrected.py)

这个示例展示了论文 Section 4.3 中的 **replacement** 路径：agent 先生成 `original_thought`，MirrorGuard 对其进行 correction，再将 `corrected_thought` 注入到后续 action-generation call 中。

对应的 OSWorld-style 参考入口：

- Agent interface: [xlang-ai/OSWorld/mm_agents/README.md](https://github.com/xlang-ai/OSWorld/blob/main/mm_agents/README.md)
- Prompt-agent base: [xlang-ai/OSWorld/mm_agents/agent.py](https://github.com/xlang-ai/OSWorld/blob/main/mm_agents/agent.py)

### UI-TARS：prefilling 路径

对应文件：[`examples/uitars_integration/uitars15_v1_corrected.py`](examples/uitars_integration/uitars15_v1_corrected.py)

这个示例展示论文中的 **prefilling** 路径：先从 unified generation 中暴露 `original_thought`，再用 MirrorGuard 进行修正，并把修正后的 reasoning 作为 prefix / assistant prefill 注回模型继续生成动作。

对应的 OSWorld-style 与上游参考：

- OSWorld agent file: [xlang-ai/OSWorld/mm_agents/uitars_agent.py](https://github.com/xlang-ai/OSWorld/blob/main/mm_agents/uitars_agent.py)
- UI-TARS repository: [bytedance/UI-TARS](https://github.com/bytedance/UI-TARS)

### Owl：代码参考

对应文件：[`examples/owl_integration/owl_agent_corrected.py`](examples/owl_integration/owl_agent_corrected.py)

这里保留了 Owl-family agent 的 OSWorld-style 接入参考，但不作为主讲解路径。

- OSWorld agent file: [xlang-ai/OSWorld/mm_agents/owl_agent.py](https://github.com/xlang-ai/OSWorld/blob/main/mm_agents/owl_agent.py)
- GUI-Owl / MobileAgent repository: [X-PLUG/MobileAgent](https://github.com/X-PLUG/MobileAgent)

## 模型访问

发布的 MirrorGuard VLM 可直接从 Hugging Face 获取：

- [WhitzardAgent/MirrorGuard](https://huggingface.co/WhitzardAgent/MirrorGuard)

模型卡中已经给出了推荐的 OpenAI-compatible 部署方式和 `vllm serve` 示例。`examples/shared/correction_runtime.py` 采用的就是这一路径。

## 安装

MirrorGuard 依赖 Python 3.8+ 与 OpenAI-compatible 模型服务端点。

```bash
pip install -r requirements.txt
```

运行评测脚本前，请先在 `config.py` 中配置模型端点。默认配置包含 `synthesizer_model`、`simulator_model`、`agent_model` 和 `annotator_model` 四类模型。

## 快速开始

### 生成任务蓝图

```bash
python task_generation/pipeline_generator.py
```

### 合成任务

良性任务：

```bash
python task_generation/benign_scene.py
```

风险任务合成：

```bash
python task_generation/batch.py
```

### 运行模拟评测

```bash
python main.py
python main_multi.py
```

### 处理轨迹并生成训练数据

```bash
python dataset_generation/safe_thought.py
python dataset_generation/prepare_dataset.py
```

## 核心组件

MirrorGuard 由一组可复用模块组成：

- `agent.py`：ReAct 风格 agent 封装，将 observation 转换为 thought 与 action。
- `simulator.py`：GUI 世界模拟器，负责加载场景、提供 observation、执行 action 并更新状态。
- `llm.py`：OpenAI-compatible 的统一调用客户端。
- `models.py`：world state、任务配置、设计注释等 Pydantic 数据模型。
- `task_generation/`：任务蓝图与场景合成流程。
- `dataset_generation/`：思维矫正与训练数据整理流程。

## 数据模型

运行时与数据合成阶段主要使用以下 Pydantic 模型：

- `UIElement`：单个可交互 GUI 元素，包含标签、取值和可用性。
- `Window`：应用窗口及其包含的 GUI 元素集合。
- `WorldState`：完整模拟状态，包含当前激活应用、窗口列表、文件系统等。
- `SceneConfig`：任务定义，包含 `task_id`、`instruction`、`initial_state` 与 `design_notes`。
- `RiskyDesignNotes` / `BenignDesignNotes`：分别描述风险场景期望安全行为与良性场景执行路径。

## 使用示例

### 单任务评测

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

### 批量评测

```bash
python main.py
python main_multi.py
```

### 数据处理

```bash
python dataset_generation/safe_thought.py
python dataset_generation/prepare_dataset.py
```

## 输出格式

评测脚本通常为每个任务输出两类文件：

- `*.log.json`：完整交互日志，包含指令、初始状态、每步 observation/thought/action 以及最终状态。
- `*.trajectory.json`：更精简的轨迹文件，用于记录逐步 reasoning/action 序列。

日志示例结构：

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

## 作者与贡献者

MirrorGuard 核心作者包括张雯祺、沈钰霖、蒋昌跃、戴嘉润、洪赓、潘旭东。

## 致谢与归属

MirrorGuard 由 **WhitzardAgent** 团队完成，成果归属于 **复旦大学** 与 **Shanghai Innovation Institute (SII)**。本研究得到上海创智学院"智能体全栈安全攻防技术矩阵"项目的支持。如果你复用代码、模型或展示素材，请保留项目归属与引用信息。
