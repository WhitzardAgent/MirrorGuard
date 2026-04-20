# Integration Overview

MirrorGuard is designed as a deployment-time reasoning corrector rather than a one-off evaluation workaround.

Across the agents we tested, the integration logic is stable:

1. expose or extract the agent's current reasoning
2. build a correction context from instruction, history, and the current screenshot
3. run the MirrorGuard corrector
4. steer downstream action generation with the corrected reasoning

## Two Deployment Paths

Following Section 4.3 of the paper, there are two main steering strategies.

### Replacement

Used when the agent generates thought and action in separate steps.

Typical flow:

1. agent generates `original_thought`
2. MirrorGuard produces `corrected_thought`
3. the original thought is discarded
4. the corrected thought is passed into the action-generation call

This is the path illustrated by the ReAct example.

### Prefilling

Used when the agent generates thought and action within a unified decoding process.

Typical flow:

1. run a first pass to surface the thought
2. correct the thought with MirrorGuard
3. inject the corrected reasoning as a fixed prefix or assistant prefill
4. continue generation from that secure reasoning state

This is the path illustrated by the UI-TARS example.

## Benchmark Transfer

Although the experiments span OS-Harm, RiOSWorld, and OSWorld, the deployment layer is not tied to one benchmark implementation. The surrounding evaluation harness changes, but the reasoning-correction mechanism remains the same:

- a current observation
- a running history
- a victim agent
- a corrector

That is why this repository exposes OSWorld-style code examples rather than benchmark forks.
