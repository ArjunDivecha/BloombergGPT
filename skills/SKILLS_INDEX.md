# Project Skills Index

This repository uses project-local skill fallbacks so Codex can work even when
global user-managed skill paths are not mounted inside the active Windows/VM
session.

## Bloomberg ASKB API Discovery

- Skill: `skills/bloomberg-askb-api-discovery/SKILL.md`
- Purpose: turn Bloomberg ASKB answers into validated BQL, BLPAPI, BDP, BDH,
  BDS, Bloomberg Excel, or BQuant recipes.
- Outputs:
  - `bloomberg_knowledge/field_dictionary.json`
  - `bloomberg_knowledge/askb_sessions/`
- Canonical global path, when mounted:
  `/Users/arjundivecha/.claude/skills/bloomberg-askb-api-discovery/SKILL.md`

Use the project-local skill path whenever the canonical global path is not
readable from the current Codex session.
