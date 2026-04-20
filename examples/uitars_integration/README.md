# UI-TARS Integration Example

This example mirrors the **prefilling** deployment path from Section 4.3 of the paper.

UI-TARS-style agents commonly generate reasoning and action inside a unified decoding process. In this setting, MirrorGuard cannot simply replace a separate thought call. Instead, it:

1. extracts the agent's `original_thought` from a first pass
2. corrects it into a `corrected_thought`
3. injects the corrected reasoning back as a fixed prefix or assistant prefill
4. lets the model continue from that secure reasoning state to produce the final action

This example keeps the OSWorld-style wrapper shape while showing the key prefilling detail explicitly.
It reflects the final deployed setting: MirrorGuard is used as a **VLM corrector**.
