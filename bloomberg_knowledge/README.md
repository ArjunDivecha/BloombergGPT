# Bloomberg Knowledge

This folder stores reusable Bloomberg ASKB discovery artifacts.

## Files

- `field_dictionary.json`: append-only catalog of validated ASKB-to-API recipes.
- `askb_sessions/`: concise session notes from ASKB research, including prompts, useful answers,
  failed API attempts, and the final validation status.

## Rules

- Save recipes only when they identify an API-accessible path or clearly establish that none exists.
- Treat ASKB as advisory until an API, Bloomberg Excel, BQuant, or broker validation succeeds.
- Do not store bulk proprietary Bloomberg data here. Store recipes, metadata, and result shapes.
- On Bloomberg quota/capacity errors, stop rather than retry.
