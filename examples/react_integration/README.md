# ReAct Integration Example

This example mirrors the **replacement** deployment path from Section 4.3 of the paper.

It represents agent frameworks where **thought generation** and **action generation** happen in two separate calls:

1. the base agent produces an `original_thought`
2. MirrorGuard corrects it into a `corrected_thought`
3. the corrected thought is injected into the action-generation call

This is the most direct example of reasoning replacement before execution.

The code intentionally keeps the OSWorld-style wrapper structure instead of being rewritten into a generic adapter abstraction.
It directly calls the deployed **MirrorGuard VLM**.
