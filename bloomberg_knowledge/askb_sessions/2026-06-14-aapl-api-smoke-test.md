# ASKB Session Note: AAPL API Smoke Test

- Date: 2026-06-14
- User request: Test the Bloomberg ASKB API Discovery skill environment.
- Skill used: `skills/bloomberg-askb-api-discovery/SKILL.md`

## ASKB Status

- Bloomberg ASKB window detected:
  - `ASKB (Beta)`
  - `ASKB ASKB (Beta) by Bloomberg AI`
- ASKB GUI automation status: visible but not accepting pasted or typed input
  through the current low-level Windows automation route.
- Screenshot evidence:
  - `outputs/askb_skill_test.png`
  - `outputs/askb_skill_test_after_submit.png`
  - `outputs/askb_skill_test_after_type.png`

## API Validation

- Validation route: direct BLPAPI.
- Service: `//blp/refdata`
- Request type: `ReferenceDataRequest`
- Security: `AAPL US Equity`
- Fields: `PX_LAST`, `NAME`
- Validation command: `python test_blpapi_simple.py`

## Result

The live Bloomberg API request succeeded.

Returned field values:

- `PX_LAST`: `291.130000`
- `NAME`: `APPLE INC`

## Conclusion

The project-local skill is readable and usable. Bloomberg Terminal and BLPAPI are
reachable. The API validation path works. The remaining gap is ASKB text entry:
ASKB is open and visible, but this Codex session's Windows automation route did
not successfully focus the ASKB input box.
