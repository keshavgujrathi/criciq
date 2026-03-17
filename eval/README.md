## Evaluation Methodology

10 test cases drawn from real Cricbuzz match data via the live API. Cases span international and domestic cricket across T20, ODI, and Test formats.

Each case is run through applicable modes (match_analyst and/or tactical). Three passes per case at the same temperature measure structural consistency — whether required output sections appear reliably across runs.

### Metrics

**Format compliance** — binary check. All required section headers must be present in response. Checked programmatically by `engine/validator.py`.

**Hallucination risk** — heuristic. Any number appearing in the response but not in the input context is flagged as ungrounded. This overfires on analytical projections (e.g., outcome range estimates) but reliably catches fabricated statistics. See `engine/validator.py:check_hallucination_risk()` for implementation.

**Structural consistency** — 3-pass check at fixed temperature. Measures whether section headers are present across all three runs. Does not measure semantic consistency — that would require a second LLM evaluation pass.

### Known Limitations

- Hallucination metric conflates predictions with fabrications
- Consistency check is structural only, not semantic
- 10 cases is a small sample — patterns are indicative, not statistically significant
- Rate limits on Groq free tier mean large eval runs require batching with sleep intervals
