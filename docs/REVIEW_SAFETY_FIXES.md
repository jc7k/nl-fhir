# Safety review fixes

These changes address the review of commit `654f1d9`.

## FHIR execution authorization

`POST /fhir/pipeline` with `execute_bundle=true` now requires a dedicated
`FHIR_EXECUTION_TOKEN` configured in the server environment and the same value in
the `Authorization: Bearer <token>` header. Generate a strong random secret and
store it in your deployment's secret manager. Do not reuse `SECRET_KEY` or an LLM
API key. Rotate the credential by replacing it in the environment and restarting
the service. Anyone holding this credential has FHIR execution permission; it is
a service credential, not a per-user identity or a replacement for an organization's
identity provider and patient-level access policy.

Execution is disabled (503) when the token is absent. Missing authentication
returns 401; an incorrect token returns 403. Execution also requires
`validate_bundle=true` (422 otherwise). These checks occur before pipeline
initialization or any write. Read-only pipeline requests retain their existing
behavior. Use HTTPS for the bearer credential.

## Conversion behavior

- Medication instructions are scoped to a clause and bounded by other extracted
  medication names. Dose parsing prefers the closest following dose and supports
  an immediately preceding dose. Frequency abbreviations must match full tokens.
- Conversion omits unknown birth dates and supplies the medication name and
  typed references required by the active resource factory. The factory preserves
  the parsed frequency and route alongside dose text, including as-needed intent.
- Local validation failures survive remote and fallback validation. A remote
  validation failure can reject a locally valid bundle. HAPI fallback validates
  individual resources locally and identifies itself as fallback, not remote
  validation.
- Conversion logs record events and request IDs without patient names, patient
  references, clinical entity text, or raw exception messages.
- MedSpaCy ConText extension flags survive the entity adapter and later extraction
  tiers for matching mentions. Negated, historical, hypothetical, and family
  mentions remain in extracted results but do not create active medication,
  condition, or service-request resources.

The context change preserves detected assertions; it does not guarantee detection
when a model is unavailable or fails to recognize an assertion. Ambiguous and
multi-part medication regimens still require clinical review.

## Regression tests

Run `uv run pytest tests/test_review_safety_regressions.py -q --no-cov` in the
project's Python 3.10 environment. Tests use synthetic text and mock external NLP
and FHIR boundaries; they do not contact clinical services.
