# Flawed API fixture (training/evaluation only)

This fixture describes a deliberately unsafe hypothetical API. It is not executable application code.

Expected review findings:
- Authorization is checked only in the client.
- User-controlled identifier is trusted without ownership verification.
- Error responses leak internal exception details.
- No negative tests cover cross-user access.

A good Aether audit should identify the risks, explain concrete impact, and recommend server-side authorization and tests.
