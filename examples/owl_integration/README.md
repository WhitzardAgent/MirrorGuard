# Owl Integration Reference

This directory contains an additional OSWorld-style code reference for an Owl-family agent.

It is included to show that the same reasoning-correction logic also transfers to a tool-calling, XML-heavy agent style. Unlike the ReAct and UI-TARS examples, this reference is not the main walkthrough for the public release.

The important point is that MirrorGuard still operates at the reasoning layer:

- extract thought
- correct thought
- steer downstream action generation

The surrounding prompt and output format can change, but the reasoning-correction principle stays the same.
This reference also uses the deployed **MirrorGuard VLM** path directly.
