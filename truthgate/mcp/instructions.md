# TruthGate Governance Gate — Available

TruthGate (formerly Superego) is the automated physical quality gatekeeper for AI coding agents.
Before declaring any task or bug "fixed", "completed", or "started", you MUST call `truthgate_verify` (or legacy alias `superego_verify`) with physical evidence:
- For UI claims: supply `screenshot_path` to a recent, valid image and `dom_or_curl_evidence`.
- For service claims: supply `dom_or_curl_evidence` showing running port/process.
- If verification is rejected, do NOT claim success to the user; fix the issue and re-verify.
