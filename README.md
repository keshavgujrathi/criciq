# CricIQ — AI Cricket Intelligence Platform

A Streamlit web app that generates structured analytical commentary for live and recent cricket matches using LLaMA 3.3-70B via Groq. Three distinct prompt architectures handle match situation analysis, player intelligence reporting, and tactical prediction. Built to explore prompt engineering as a disciplined practice — versioned prompts, structured outputs, and a small evaluation suite with real numbers.

**Live:** [add Streamlit Cloud URL after deployment]

---

## Architecture

```
Cricbuzz API → fetcher.py → formatter.py → prompt_loader.py → llm_client.py → Streamlit UI
                                                    ↓
                                            validator.py ← eval_runner.py
```

**Data layer** (`data/`): `CricbuzzFetcher` pulls live and recent matches from Cricbuzz RapidAPI endpoint, merges both feeds, and deduplicates by match ID. Separate methods handle scorecards, commentary, match info, and player stats. `formatter.py` converts raw JSON into prompt-injectable strings — flat, readable, no nested structure passed to model.

**Prompt engine** (`engine/`): YAML-based prompt files with explicit versioning. `prompt_loader.py` handles file resolution, version listing, and template variable substitution. `llm_client.py` wraps Groq SDK with separate `complete()` and `stream_complete()` methods. `validator.py` checks output structure compliance and runs a heuristic hallucination scan.

**Eval layer** (`eval/`): 10 test cases drawn from real match data across multiple series and formats. `eval_runner.py` runs each case through LLM, validates output, and runs 3 consistency passes per case to measure structural variance at temperature 0.3.

---

## The Three Prompt Architectures

Each mode is a different analytical problem requiring a different prompt design.

**Mode 1 — Match Analyst** (`match_analyst_v1/v2.yaml`)
Role-conditioned as a senior analyst with a fixed 5-section output schema. Temperature 0.3. The schema enforcement is explicit — headers are named in system prompt and model is told to follow them exactly. v2 adds a pressure index score to MOMENTUM section and probability weights to OUTCOME RANGE. The v1→v2 diff is visible in app's Compare Versions feature.

**Mode 2 — Player Intel** (`player_intel_v1.yaml`)
Demonstrates RAG-lite pattern: player stats are fetched separately and injected as context alongside current match situation. The prompt is structured around a different 5-section schema focused on profiling rather than narrative. Temperature 0.3. The key design difference from Mode 1 is dual-context injection — match state and player history are kept as separate blocks in user prompt so the model can reason about each distinctly.

**Mode 3 — Tactical Predictor** (`tactical_v1.yaml`)
The most structurally demanding mode. The system prompt instructs chain-of-thought reasoning before producing a ranked 3-option output with expected value and risk ratings per option. Temperature raised to 0.4 to allow more varied tactical suggestions. The schema requires 8 distinct sections — more than either other mode — which makes format compliance a stricter test.

---

## Prompt Design Decisions

**Why role conditioning:** Framing the model as a "senior analyst with 20 years of experience" consistently produced more specific, less hedged outputs than a neutral framing. The model references specific players and overs rather than speaking in generalities.

**Why fixed output schemas:** Structured outputs are easier to validate programmatically and easier to render cleanly in the UI. Free-form responses from a sports analysis prompt tend toward verbose narrative — schemas force concision and make each section independently scannable.

**Why temperature 0.3 not 0:** Deterministic outputs (temperature 0) produced noticeably repetitive phrasing across runs. 0.3 preserves some variation in expression while keeping analytical conclusions stable. The consistency evaluation confirms this — 62.5% structural consistency means sections are reliably present even if language varies.

**Why YAML prompt files:** Treating prompts as versioned artifacts rather than hardcoded strings makes iteration traceable. Each file has a `notes` field documenting what changed and why. The app exposes version selection directly in the UI so design decisions are visible, not buried in code.

---

## Evaluation Results

10 test cases drawn from real Cricbuzz match data — 6 international matches, 4 domestic, across T20 and ODI formats. Each case run through applicable modes with 3 consistency passes per case.

| Metric | Result |
|---|---|
| Total test runs attempted | 17 |
| Completed runs | 16 |
| Format compliance | 16/16 (100%) |
| No hallucination risk (heuristic) | 2/16 (12.5%) |
| Structural consistency (3-pass) | 10/16 (62.5%) |
| Mean response time | ~1,990ms |
| Rate limit errors | 1 (tc_010 tactical, Groq TPD cap) |

**On hallucination metric:** 12.5% "no risk" rate is misleading at face value. The validator flags any number in response that doesn't appear verbatim in input context. Outcome range predictions ("best case 180 runs") are flagged as ungrounded because they are model inferences, not input facts — which is expected and correct behavior for a predictive mode. A more precise hallucination check would distinguish between factual claims (player statistics, match results) and analytical projections. The current heuristic is a useful first pass but overfires on predictive content. Both clean cases (tc_002 tactical and tc_006 tactical) were completed matches with minimal scorecard data, which is a confound in the metric.

**On consistency:** 62.5% structural consistency at temperature 0.3–0.4 indicates model reliably produces required sections but occasionally merges or relabels them across runs. The tactical mode showed the most variance, which aligns with its higher temperature setting and more complex output schema.

**One rate limit hit** on the final test case due to Groq's free tier TPD cap. The runner handles this with a descriptive error rather than a silent failure.

---

## Key Findings

**Chain-of-thought in the tactical prompt produced more internally consistent reasoning** — REASONING sections referenced SITUATION ASSESSMENT rather than restating the scorecard. Direct instruction prompting (no CoT) in an earlier draft produced three options that were sometimes contradictory. The tradeoff is token usage: tactical mode runs ~40% longer responses than match analyst mode.

**The v1→v2 diff on match_analyst is worth showing in a demo.** v2's pressure index forces the model to commit to a specific number, which produces sharper MOMENTUM sections. v1 tends toward "both teams have momentum in different phases" hedging. One schema constraint changed analytical quality noticeably.

**Commentary absence doesn't degrade output quality significantly.** Most test cases used completed matches with no live commentary. The model worked from scorecard data alone and produced coherent analysis. The MOMENTUM and KEY BATTLEGROUND sections were slightly more generic without commentary but remained structurally sound.

**100% format compliance across all completed runs suggests fixed-schema prompting is reliable at temperature 0.3–0.4 for this model.** The one failure mode observed was structural inconsistency across 3-pass runs (62.5% consistent), concentrated in the tactical mode where higher temperature and 8-section schema create more surface area for variation.

---

## What I'd Build Next

- **Player embedding search:** embed career stats for top 200 players and retrieve the 3 most similar historical players to any current performer. Inject as additional context into Mode 2.
- **Series RAG:** chunk and embed match reports from a full series so the model can reason about cumulative patterns ("this is the third time in this series that South Africa have lost a powerplay").
- **Evaluation expansion:** replace the number-grounding heuristic with a claim extraction pass — use a second LLM call to identify factual claims in the response and verify each against the input context.

---

## Stack

- **Inference:** LLaMA 3.3-70B via Groq API
- **Data:** Cricbuzz via RapidAPI
- **UI:** Streamlit
- **Prompt management:** YAML with version control
- **Evaluation:** custom validator + eval runner

---

## Running Locally

```bash
git clone <repo>
cd criciq
pip install -r requirements.txt
cp .env.example .env
# Add RAPIDAPI_KEY and GROQ_API_KEY to .env
streamlit run app.py
```
