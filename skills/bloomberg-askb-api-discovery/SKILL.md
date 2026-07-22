# Bloomberg ASKB API Discovery

Use Bloomberg ASKB to translate natural-language Bloomberg data requests into exact,
testable API-access instructions for BLPAPI, BQL, BDP, BDH, BDS, Bloomberg Excel,
BQuant, or other programmatic Bloomberg routes.

## Purpose

The deliverable is an API-access recipe, not Terminal navigation. Use ASKB for
Bloomberg-native discovery and translation, then validate the answer through the
local broker, Bloomberg API, Bloomberg Excel, or BQuant before marking confidence
high.

## Safety

- Use ASKB for discovery only.
- Do not use computer control for order entry, EMSX, FXGO, BUY/SELL screens, trade
  tickets, unattended sensitive workflows, or bulk GUI scraping.
- Do not treat ASKB conclusions as investment recommendations.
- Do not accept ASKB output as final until it has been validated through an API,
  Bloomberg Excel, BQuant, or the local broker.

## Workflow

1. Confirm ASKB is open and usable. If it is not, ask the user to open Bloomberg
   Terminal ASKB in the Windows VM and wait for confirmation.
2. Ask ASKB using the API-first prompt below.
3. If ASKB gives only Terminal screen/function guidance, ask the mandatory
   API-access follow-up.
4. Extract the API route, securities, fields, overrides, dates, entitlements, and
   minimal reproducible test.
5. Validate through the local Bloomberg broker, BLPAPI, BQL, Bloomberg Excel, or
   BQuant.
6. If validation fails, ask ASKB a targeted follow-up using the exact error.
7. Save reusable validated recipes in `bloomberg_knowledge/field_dictionary.json`.
8. Save concise session notes in `bloomberg_knowledge/askb_sessions/`.

## Required ASKB Prompt

Use this prompt when asking ASKB:

```text
I want to access Bloomberg data programmatically, not just through Terminal
screens.

Question: [USER QUESTION]

Please give:
1. The best BQL query if available.
2. BDP formulas for point-in-time fields.
3. BDH formulas for historical fields.
4. BDS formulas for bulk/reference datasets, if applicable.
5. BLPAPI field mnemonics, security syntax, services, request type, and overrides.
6. Any required date handling, periodicity, currency, source, or account
   entitlement considerations.
7. A minimal reproducible test example that can be validated through Bloomberg
   API, Bloomberg Excel, BQuant, or a local Bloomberg broker.

Do not give only Terminal navigation. If a Terminal function is relevant, include
it only as supporting context.
```

## Mandatory API-Access Follow-Up

Use this if ASKB answers with screen navigation rather than API instructions:

```text
The answer above gives Terminal screens/functions. I need the API-accessible
version.

Please translate this into exact Bloomberg API access instructions:
- BQL query, if supported
- BDP/BDH/BDS Excel formulas, if supported
- BLPAPI service/request type, securities, fields, overrides, and dates
- Any field mnemonics, bulk fields, or dataset identifiers
- A minimal validation example

If there is no API-accessible route, say so explicitly and explain the limitation.
```

## Error Follow-Up

Use this if validation fails:

```text
This Bloomberg API validation failed:

[ERROR]

Original request:
[USER QUESTION]

Attempted API route:
[FIELDS / SECURITIES / BQL / FORMULA / REQUEST]

What is the correct API-accessible version? Please provide exact fields,
securities, overrides, date handling, and a minimal validation example.
```

## Extraction Schema

After ASKB answers, extract:

- `original_question`
- `askb_prompt`
- `askb_answer_summary`
- `terminal_functions`
- `api_routes`
- `securities`
- `fields`
- `overrides`
- `date_handling`
- `entitlements_or_limitations`
- `minimal_tests`
- `validation_status`
- `validation_evidence`
- `confidence`
- `askb_session_note`

## Validation Guidance

Prefer the strongest available validation:

1. Local broker endpoint using the repo's Bloomberg service.
2. Direct BLPAPI request.
3. BQL execution.
4. Bloomberg Excel formula.
5. BQuant notebook/script.

Confidence levels:

- `high`: API route validated successfully with live data or a clear Bloomberg API
  response.
- `medium`: API route is specific and plausible, but validation could not be run.
- `low`: ASKB gave incomplete, screen-only, or conflicting guidance.

## Storage

Validated reusable recipes belong in:

```text
bloomberg_knowledge/field_dictionary.json
```

Concise session notes belong in:

```text
bloomberg_knowledge/askb_sessions/
```

Session notes should include the date, user question, ASKB prompt, answer summary,
validation attempt, result, and follow-ups.
