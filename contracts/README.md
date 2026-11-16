# Contracts: the agreed interfaces between stages

These JSON Schemas are the **single source of truth** for what one stage hands to the next.
If your stage's output does not validate, the integration tests fail.

| Schema | Producer | Consumer |
|---|---|---|
| `stage1_output` | Stage 1 (AI threat prediction) | Stage 2, orchestrator |
| `stage2_output` | Stage 2 (`secure_channel()`) | Stage 3, orchestrator |
| `stage3_command` | Stage 3 (signed with Stage 2's `CommandSigner`) | nodes, orchestrator |
| `pipeline_event` | orchestrator | Stage 4 dashboard |

**Changing a contract:** open a pull request that edits the schema AND the examples, bump `contract_version`, and get approval from **all four members** (see `.github/CODEOWNERS`). Never change a contract by surprise.

## Additive changes in v1.0 (no version bump, nothing removed)
`pipeline_event` gained the decision value `pending_human_approval` and these OPTIONAL fields:
`pending_approval`, `node_status`, `rekeyed`, `policy`, `node_applied`. Old consumers keep working.
