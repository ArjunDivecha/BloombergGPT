# llmchat session — Bloomberg ASKB API Discovery Skill

Date: 2026-06-14
Agent: ChatGPT
Topic: Bloomberg Terminal, ASKB, Codex/Claude computer use, and API-first Bloomberg data discovery
User: Arjun Divecha

## Summary

We discussed how to use Codex and Claude Code with Bloomberg Terminal running inside a Windows VM via Parallels on a Mac. The primary objective is not to scrape Bloomberg Terminal or automate GUI workflows, but to use Bloomberg’s internal LLM, ASKB, as a Bloomberg-native data/function discovery assistant.

The central conclusion:

Codex should be able to use computer-use functionality inside the Windows VM to ask ASKB questions. ASKB should then return Bloomberg-native guidance, ideally including BQL, field mnemonics, securities, functions, overrides, and API-accessible examples. Codex or Claude should convert that ASKB response into a validated BLPAPI / BQL / BDP / BDH / BDS implementation recipe.

The skill should be explicitly API-first. Terminal navigation instructions are supporting context only. The deliverable is a programmatic data-access recipe.

## Core architecture

Preferred architecture:

```text
ChatGPT / Claude / Codex
  -> Bloomberg ASKB API Discovery Skill / AGENTS.md instructions
  -> Codex computer use inside Windows VM
  -> Bloomberg Terminal / ASKB
  -> ASKB answer with functions, fields, BQL, overrides, screens
  -> local Bloomberg broker / BLPAPI / BQL / BDP / BDH validation
  -> saved Bloomberg field dictionary / reusable recipe
```

The goal is:

- Use ASKB for Bloomberg-native discovery.
- Use BLPAPI/BQL/API routes for actual data access.
- Avoid relying on GUI clicking for repeatable data extraction.

## Parallels / Windows VM / Codex decision

Decision:

Install the Codex app inside the Windows VM that runs Bloomberg Terminal.

Reason:

Running Codex directly inside the Windows VM is cleaner than running Codex on macOS and trying to control the Parallels window. It avoids unnecessary failure points: window focus, Retina scaling, keyboard mapping, clipboard transfer, Bloomberg hotkeys, and Parallels boundary issues.

Recommended setup:

- Bloomberg Terminal runs inside the Windows VM.
- Codex app also runs inside the same Windows VM.
- Codex computer use is allowed only for ASKB research.
- Codex should not be allowed to navigate trade-entry or execution screens.
- Codex should use ASKB to discover API-accessible fields/functions.
- Final validation must happen through BLPAPI/BQL/local broker, not by trusting ASKB blindly.

## Claude Code vs Codex

Codex is the better primary tool for driving ASKB inside the Windows VM because it can operate the Windows desktop directly when installed in the VM.

Claude Code can still be useful for implementation, repo edits, broker code, skill-writing, and validation logic. However, Claude Code computer-use control may be more constrained for financial/trading platforms and may be less reliable for directly controlling Bloomberg Terminal.

Recommended division of labor:

- Codex: drive ASKB inside Windows VM, capture Bloomberg-native answers.
- Claude Code: implement, refactor, validate, and maintain the Bloomberg API broker and skill files.
- ChatGPT: design protocols, prompts, skill instructions, validation workflows, and research plans.

## ASKB role

ASKB should be treated as Bloomberg’s native conversational research layer. For this project, the best use of ASKB is not general market analysis. The best use is:

Ask ASKB how Bloomberg itself would access a dataset, function, field, screen, BQL query, or workflow, then convert the answer into validated BLPAPI / BQL / BDP / BDH / BDS instructions.

ASKB is useful for:

- Discovering the right Bloomberg function for a data request.
- Finding API-accessible field mnemonics.
- Getting BQL examples.
- Finding BDP / BDH / BDS equivalents.
- Understanding Bloomberg security syntax.
- Identifying required overrides, date settings, currency settings, periodicity, adjustment flags, sources, and entitlement limitations.
- Discovering whether data is available through BLPAPI, BQL, Bloomberg Excel, BQuant, PORT, RMS, or only a Terminal screen.
- Asking follow-up questions when an initial Bloomberg field/query fails.

ASKB should not be used as the final source of truth without API validation.

## Important distinction

Bad target answer:

```text
Go to function X in Terminal and click Y.
```

Good target answer:

```text
Use this BQL query / BLPAPI field-security-override recipe / BDP-BDH-BDS formula with this exact security syntax, date handling, periodicity, currency, and entitlement caveat.
```

Terminal directions are not the deliverable. They are supporting evidence.

The deliverable is a programmatic data-access recipe.

## Skill name

Recommended skill name:

Bloomberg ASKB API Discovery

Alternative names:

- Bloomberg API Discovery via ASKB
- ASKB-to-BLPAPI Translator
- Bloomberg Data Access Discovery
- ASKB BQL Field Finder

Preferred name:

Bloomberg ASKB API Discovery

## Skill mission

Use Bloomberg ASKB to translate natural-language data requests into precise, testable API access instructions for BLPAPI, BQL, BDP, BDH, BDS, Bloomberg Excel formulas, BQuant, and related Bloomberg-accessible APIs.

Prefer programmatic access paths over Terminal screen navigation.

The skill should use ASKB only for Bloomberg-native discovery and translation. It should ask ASKB for functions, field mnemonics, BQL, BDP/BDH/BDS equivalents, security syntax, overrides, entitlements, and minimal test examples.

ASKB output must be treated as advisory until validated through BQL, BDP, BDH, BDS, BLPAPI, or the local Bloomberg broker.

The skill must never use ASKB or computer use for order entry, trade tickets, bulk GUI scraping, or unattended sensitive workflows.

## API-first priority order

The skill should follow this priority order:

1. BQL query
2. BLPAPI-compatible field/security/override recipe
3. BDP / BDH / BDS formula
4. Bloomberg Excel equivalent
5. BQuant example
6. Terminal screen/function only as a diagnostic aid
7. GUI navigation only if no API route exists

## Completion criteria

The skill should not mark a task complete unless it has at least one of:

- BQL query present
- BDP / BDH / BDS formula present
- BLPAPI recipe present, including security + field + overrides
- Clear statement that no API route exists
- Clear closest programmatic alternative if no direct API route exists

If ASKB provides only Terminal screen navigation, the skill must ask a follow-up requesting API access details.

## Default ASKB prompt template

Use this prompt when asking ASKB:

```text
I want to access the following Bloomberg data programmatically, preferably through BLPAPI, BQL, Bloomberg Excel formulas, BDP, BDH, BDS, or BQuant.

Data request:
[USER QUESTION]

Please do not only tell me which Terminal screen to use.

Please provide:

1. Exact BQL query, if available.
2. Exact Bloomberg field mnemonics.
3. Exact security, index, country, curve, or universe syntax.
4. BDP / BDH / BDS formula equivalents.
5. Required overrides, parameters, periodicity, dates, currency, source, and adjustment settings.
6. Whether this works through BLPAPI.
7. Whether this works through Bloomberg Excel or BQuant.
8. One minimal reproducible example.
9. Known entitlement, licensing, history, point-in-time, or coverage limitations.
10. If no API route exists, say that clearly and explain the closest programmatic alternative.

Prioritize BQL, Bloomberg API, Excel, and BQuant access over manual Terminal navigation.
```

## Mandatory follow-up prompt

Use this if ASKB answers with screen navigation rather than API instructions:

```text
That is useful for Terminal navigation, but I need API access.

Please translate this into BQL, BDP, BDH, BDS, Bloomberg Excel, or BLPAPI instructions with exact field mnemonics, exact security syntax, required overrides, and one minimal test example.
```

## ASKB extraction schema

After ASKB answers, extract the following:

- Original user question
- Bloomberg concept / data target
- Recommended Bloomberg functions
- Recommended Terminal screens
- API route: BQL / BDP / BDH / BDS / BLPAPI / Excel / BQuant / other
- Exact security or universe syntax
- Exact field mnemonics
- Full BQL query, if provided
- BDP / BDH / BDS formulas, if provided
- Required overrides
- Date handling
- Periodicity
- Currency settings
- Adjustment settings
- Source settings
- Entitlement constraints
- Data coverage limitations
- Point-in-time limitations
- Known failure modes
- Minimal reproducible example
- Validation status
- Confidence level
- Reusable note for field dictionary

## Standard output format from the skill

The skill should produce outputs in this structure:

```text
Summary

- Data request:
- Best API route:
- Confidence:
- Validation status:

API recipe

- Bloomberg service/API:
- Query type:
- Security/universe:
- Fields:
- Overrides:
- Date handling:
- Periodicity:
- Currency/source/adjustments:
- Entitlements:

Minimal test

- One-security example:
- Expected result shape:
- Expected fields/columns:
- Common failure modes:

Terminal reference

- Relevant Terminal functions/screens:
- Use only for validation/discovery, not extraction.

Next validation step

- Test through local Bloomberg broker.
- If it fails, ask ASKB a targeted follow-up using the exact error.
```

## Validation workflow

The skill should enforce this loop:

1. Ask ASKB using the API-first prompt.
2. Extract functions, fields, BQL, securities, and overrides.
3. Ask the mandatory API-access follow-up if ASKB gives only screen guidance.
4. Test the smallest possible query through the local Bloomberg broker.
5. If the query fails, ask ASKB:
   “This field/query failed with this error: [ERROR]. What is the correct API-accessible version?”
6. Save the final working recipe to the reusable Bloomberg field dictionary.
7. Mark confidence as high only after successful API validation.

## Local field dictionary

Create or maintain a reusable field dictionary with entries like:

- Request name
- Bloomberg concept
- Working API route
- BQL query
- Field mnemonics
- Securities/universe syntax
- Overrides
- Date handling
- Entitlements
- Example output shape
- Validation date
- Validation result
- Failure modes
- ASKB notes

The point is to avoid repeatedly asking ASKB the same question.

## Guardrails

Strict guardrails:

- ASKB only unless explicitly approved.
- No order-entry workflows.
- No EMSX, FXGO, BUY, SELL, trade tickets, or execution screens.
- No unattended workflows that could affect portfolio state.
- No bulk data extraction through the GUI.
- No treating ASKB conclusions as investment recommendations.
- No accepting ASKB output as final until validated through API.
- No storing Bloomberg proprietary bulk data in embeddings or RAG unless explicitly permitted by license and workflow.
- Use ASKB for discovery, not scraping.
- Use BLPAPI/BQL/API for repeatable access.

## Good use cases

Excellent use cases for this skill:

- “How do I get India foreign equity portfolio flows through Bloomberg API?”
- “What BQL query gives ETF shares outstanding history?”
- “How do I access VIXEQ or implied correlation through Bloomberg API?”
- “Which Bloomberg fields track ETF creations/redemptions?”
- “What field gives country-level earnings revisions for MSCI country indices?”
- “How do I get economic surprise data programmatically?”
- “What API-accessible data exists for portfolio flows, FDI, balance of payments, or foreign equity ownership?”
- “How do I retrieve Bloomberg Intelligence estimates through BQL?”
- “What is the BLPAPI route for a dataset that ASKB says exists in a Terminal screen?”

## Poor use cases

Poor use cases:

- Bulk downloading via GUI.
- Blind GUI clicking through Bloomberg functions.
- Trading or order entry.
- Accepting ASKB’s market view without validation.
- Treating ASKB output as a final investment signal.
- Running unattended Bloomberg GUI workflows.

## Recommended repo files

Suggested project structure:

```text
BloombergGPT/
  AGENTS.md
  llmchat.md
  skills/
    bloomberg-askb-api-discovery/
      SKILL.md
  bloomberg_knowledge/
    field_dictionary.json
    askb_sessions/
      YYYY-MM-DD-topic.md
```

## Codex instruction snippet

Add to AGENTS.md or equivalent Codex instructions:

```text
When working on Bloomberg data-access questions, use the Bloomberg ASKB API Discovery workflow.

Your primary job is to obtain API-accessible Bloomberg data instructions, not Terminal navigation instructions.

Use Bloomberg ASKB only for discovery and translation. Always ask for exact BQL, BDP, BDH, BDS, Bloomberg Excel, BQuant, or BLPAPI instructions. Terminal functions and screens are supporting references only.

Always request:
- Exact BQL query if available
- Exact Bloomberg field mnemonics
- Exact security or universe syntax
- BDP / BDH / BDS equivalents
- Required overrides and parameters
- Date, currency, periodicity, adjustment, and source options
- Whether the data is available through BLPAPI
- Whether the data is available through BQuant or Bloomberg Excel
- Known entitlement or licensing limitations
- One minimal reproducible test query

If ASKB gives only Terminal screen instructions, ask a follow-up:
“How do I access the same data programmatically through BQL, Bloomberg Excel formulas, or BLPAPI? Please give exact field names, security syntax, overrides, and one minimal example.”

Do not use computer use for order-entry, execution, EMSX, FXGO, trade tickets, bulk GUI scraping, or unattended sensitive workflows.

Do not consider an ASKB answer complete until it has an API-accessible route or explicitly states that no API route exists.
```

## Skill draft: SKILL.md core

```markdown
# Bloomberg ASKB API Discovery

## Purpose

Use Bloomberg ASKB to translate natural-language Bloomberg data requests into exact, testable API-access instructions for BLPAPI, BQL, BDP, BDH, BDS, Bloomberg Excel, BQuant, or other programmatic Bloomberg routes.

This skill is API-first. Terminal directions are supporting context, not the deliverable.

## Operating principle

The deliverable is a programmatic data-access recipe.

Do not stop at Terminal navigation. If ASKB provides only screen/function guidance, ask a follow-up requesting API-accessible fields, BQL, formulas, security syntax, overrides, and a minimal test.

## Required ASKB prompt

I want to access the following Bloomberg data programmatically, preferably through BLPAPI, BQL, Bloomberg Excel formulas, BDP, BDH, BDS, or BQuant.

Data request:
[USER QUESTION]

Please do not only tell me which Terminal screen to use.

Please provide:
1. Exact BQL query, if available.
2. Exact Bloomberg field mnemonics.
3. Exact security, index, country, curve, or universe syntax.
4. BDP / BDH / BDS formula equivalents.
5. Required overrides, parameters, periodicity, dates, currency, source, and adjustment settings.
6. Whether this works through BLPAPI.
7. Whether this works through Bloomberg Excel or BQuant.
8. One minimal reproducible example.
9. Known entitlement, licensing, history, point-in-time, or coverage limitations.
10. If no API route exists, say that clearly and explain the closest programmatic alternative.

Prioritize BQL, Bloomberg API, Excel, and BQuant access over manual Terminal navigation.

## Mandatory follow-up

If ASKB gives only Terminal screen instructions, ask:

That is useful for Terminal navigation, but I need API access.

Please translate this into BQL, BDP, BDH, BDS, Bloomberg Excel, or BLPAPI instructions with exact field mnemonics, exact security syntax, required overrides, and one minimal test example.

## Output format

Summary
- Data request:
- Best API route:
- Confidence:
- Validation status:

API recipe
- Bloomberg service/API:
- Query type:
- Security/universe:
- Fields:
- Overrides:
- Date handling:
- Periodicity:
- Currency/source/adjustments:
- Entitlements:

Minimal test
- One-security example:
- Expected result shape:
- Expected fields/columns:
- Common failure modes:

Terminal reference
- Relevant Terminal functions/screens:
- Use only for validation/discovery, not extraction.

Next validation step
- Test through local Bloomberg broker.
- If it fails, ask ASKB a targeted follow-up using the exact error.

## Guardrails

- ASKB only unless explicitly approved.
- No order-entry workflows.
- No EMSX, FXGO, BUY, SELL, trade tickets, or execution screens.
- No unattended workflows that could affect portfolio state.
- No bulk data extraction through the GUI.
- No accepting ASKB output as final until validated through API.
- Use ASKB for discovery, not scraping.
- Use BLPAPI/BQL/API routes for repeatable access.
```

## Implementation phases

Recommended implementation path:

### Phase 1 — Manual MVP

- Install Codex inside the Windows VM.
- Keep Bloomberg Terminal open and logged in.
- Ask ASKB manually or through Codex computer use.
- Copy/paste ASKB answers into Codex/Claude.
- Extract API recipe manually.
- Validate through local broker.

### Phase 2 — Semi-automated

- Codex uses computer use only to open ASKB, paste the question, and capture the answer.
- Codex/Claude converts the answer into an API recipe.
- Broker validates the query.
- Working recipes are written to field_dictionary.json.

### Phase 3 — Fully automated ASKB helper

Build a small controlled helper or MCP server with functions such as:

```text
ask_askb(question) -> structured ASKB answer
extract_api_recipe(answer) -> JSON recipe
validate_bloomberg_recipe(recipe) -> pass/fail + result shape
save_recipe(recipe) -> field dictionary entry
```

Do not build Phase 3 until 20–50 ASKB examples have been collected. Examples are needed to understand answer formats, copy behavior, BQL code block reliability, and common failure modes.

## Final decision record

- Install Codex inside the Windows VM.
- Use computer use for ASKB research only.
- Make the Bloomberg ASKB skill API-first.
- Treat Terminal directions as secondary.
- Convert ASKB answers into BQL / BLPAPI / BDP / BDH / BDS recipes.
- Validate through local Bloomberg broker.
- Save reusable discoveries into a field dictionary.
- Never use this workflow for trade entry or unattended sensitive Bloomberg actions.
