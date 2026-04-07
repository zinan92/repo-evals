# Verdict Buckets

## `unusable`

Use this when the repo does not reliably deliver its core promised outcome.

Typical signs:

- The main scenario fails
- Outputs are too poor to use
- Results are wildly inconsistent
- Failure modes are misleading

## `usable`

Use this when the repo can complete its core path, but confidence is still limited.

Typical signs:

- One or two basic scenarios work
- Edge cases are shaky
- Repeatability is only partially proven
- The support layer may be strong, but the core user-facing layer is still only lightly tested

## `reusable`

Use this when the repo works across multiple realistic scenarios with acceptable consistency.

Typical signs:

- Core scenarios pass repeatedly
- Inputs vary and results remain acceptable
- Failure boundaries are becoming clear
- The actual user-facing layer has been validated, not just supporting scripts or packaging

## `recommendable`

Use this only when the repo is strong enough that you would recommend it to another person without heavy caveats.

Typical signs:

- Broad scenario coverage
- Stable repeated performance
- Clear boundaries and known failure cases
- Documentation and behavior mostly match

## Ceiling Rules

- Weak plan + all-pass does not automatically justify a strong verdict
- Untested core layer caps the overall verdict at `usable`
- Strong support-layer evidence can still appear in the narrative, even when the final bucket stays conservative
