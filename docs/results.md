# Results Overview

This repository follows the metrics and benchmark roles defined in the paper.

## Benchmark Roles

- **OS-Harm**: evaluates resilience against actionable harm, including explicit misuse, prompt injection, and spontaneous unsafe behavior.
- **RiOSWorld**: evaluates multimodal agent security in dynamic GUI environments.
- **OSWorld**: evaluates utility preservation and over-defensiveness on benign tasks.

## Main Metrics

- **Unsafe Rate**: how often the agent still takes unsafe paths
- **False Refusal Rate (FRR)**: how often the defense unnecessarily blocks or derails benign execution
- **Success Rate (SR)**: task completion on benign utility benchmarks

## Headline Numbers From The Paper

- On **UI-TARS**, MirrorGuard reduces **Unsafe Rate** from **66.5%** to **13.0%**.
- Compared with **GuardAgent**, MirrorGuard achieves stronger risk mitigation with a lower utility penalty.
- On **OSWorld**, utility is measured using **Success Rate (SR)** to quantify over-defensiveness after secure correction.

## Qualitative Release Material

For the public release, this directory is intended to be paired with:

- selected case studies from real benchmark rollouts
- short demo GIFs or clips
- compact summary figures for README and project-page use

The current release workspace already includes two rollout comparison GIFs under `assets/`, which can be used as before/after qualitative demos after final captioning and renaming.

The repository intentionally keeps the public result narrative consistent with the paper instead of introducing a second, inconsistent reporting scheme.
