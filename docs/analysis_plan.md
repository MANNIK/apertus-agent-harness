# Analysis plan — Weight-Space Programming vs LoRA vs original, Apertus v1.5 8B, multilingual Text-to-SQL (DuckDB)

**Status: v0.1, written 2026-11-10, before any WSP or LoRA data exists (pre-registration).** The previous plan (agentic suite) is archived in `docs/archive/analysis_plan_agentic_suite.md`.

Rules for changing this document:
- Items marked **[OPEN]** are decisions the team has not taken yet. They must be closed, dated and committed in the *Decisions log* (section 13) **before the first WSP or LoRA run**.
  Closing an [OPEN] item before that point is not a deviation.
- After the first run of a modified model, any change goes into *Deviations* (section 14) with date and reason. Never edited silently.
- Every number in a report must come from a saved run (`runs/…`, folder cited) or from a script in this repository. Verified and assumed are always kept apart.
- WSP is a **hypothesis**. A null or negative result is reported with the same prominence as a positive one.

## 1. Questions and hypotheses
All tests are two-sided. We do not pre-commit to a direction.

| ID | Hypothesis | Role |
|---|---|---|
| H1 | Execution accuracy of **WSP** differs from that of the **original** on the held-out test set | primary |
| H2 | Execution accuracy of **LoRA** differs from that of the **original** | secondary |
| H3 | Execution accuracy of **WSP** differs from that of **LoRA** at a matched budget (section 7) | secondary |

Descriptive (no test, no claim of success): number and percentage of modified parameters, adaptation cost, latency, memory, regression rate, per-language and per-category results.

## 2. Conditions
| | Weights | Notes |
|---|---|---|
| A — original | Apertus v1.5 8B, unmodified, MLX bf16 | reference |
| B — WSP | A + a targeted weight change θ' = θ + Δθ, proposed with a development model and kept only if it passes the acceptance rule (section 6) | the only intended difference is the weights |
| C — LoRA | A + LoRA adapter trained under the protocol of section 7, fused into the same MLX format | conventional baseline |

Frozen and identical for A, B and C (recorded in each run's `meta.json`; `agentbench compare` warns if more than one setting differs): serving stack (local `mlx_lm.server`, one model loaded at a time on the 32 GB Mac),
precision, system prompt, schema serialisation, `run_sql` tool limits (read-only, timeout, row cap), temperature, max_tokens, seed, history mode, task-set digest.
- **Reasoning mode (`--thinking on|off`): [OPEN]** — one value for all three conditions. The server reasons by default (checked 2026-11-10), which changes time and result.
- If a modified checkpoint cannot be served exactly like the original, the confound is stated.
- **Development models** (not runtime): Claude Sonnet 5.5 proposes and analyses weight changes. Declared in `models.yaml` as development-only. The tokens/cost used are reported as part of the adaptation cost. No other development model is declared until it is actually used.
- Runtime and any judge: only Apertus and open-weights models. The official score uses **no LLM**.

## 3. Data and splits (details in `docs/dati.md`, task W02)
- Roles: **dev** (iterate), **val** (choose between variants), **test** (look once, at the end). Fixed split files with sha256 fingerprints.
- Split **by schema**: schemas in test appear neither in dev/val nor in any LoRA/WSP training or analysis data. The question language (DE/FR/IT/EN) and the trap category (format traps, cross-lingual schema linking) are recorded per task and used as strata.
- Target size: 200–500 independent tasks overall (W02). **The test set is only a part of that**, so the power figures below (section 5) are optimistic for it; the actual test size is declared in `docs/dati.md` and the table is recomputed with `scripts/power_table.py`.
- Contamination: we do **not** know whether public Text-to-SQL sets (e.g. BIRD, Spider) are in Apertus' training data. They are treated as a secondary set with that caveat. For the Swiss open-data set we check overlap with public query collections (W02).

## 4. Outcomes
**Primary:** execution accuracy on test = share of tasks whose query result matches the gold query result under the comparison rules of W03 (row order only when the question needs it, column names/order, NULL, duplicates, numeric types and tolerance). The rules are written **before** any model result is seen and apply to all conditions.

**Secondary (reported, not used to declare success):**
- **relaxed execution accuracy** (`sql_result_projection`, `sql_eval.compare_projection`): like the primary but extra columns and any column order are accepted (the gold must be an ordered projection of the model's result). It separates "wrong query" from "added a useful column"; it is never stricter than the primary and is **not** a substitute for it;
- answer correctness of the final natural-language answer (values only, deterministic matching; `final_number`, recorded as a diagnostic check, not part of the primary score);
- accuracy by question language, by schema-language pair and by trap category;
- share of executable queries (syntax/execution errors);
- **regression rate** on capabilities not optimised (task W13): items the original gets right and the modified model gets wrong, and the reverse. **Set and scoring: [OPEN]**;
- median and p95 latency per task (with the reasoning setting), peak memory on the Mac;
- modified/trainable parameters (exact count and % of the model), adaptation cost: GPU-hours and currency for training/search, wall-clock, development-model tokens.

## 5. Statistics
- Per condition: Wilson 95% interval (`agentbench.stats.wilson`).
- Pairs: exact McNemar on tasks paired by id (`mcnemar_exact`), with counts improved/worsened.
- **Multiple comparisons:** H1–H3 form one family; **Holm** correction at family-wise α = 0.05. Raw and adjusted p-values are both reported.
- Per-language / per-category numbers are descriptive and not corrected; they do not support a success claim.
- **Dependence:** tasks from the same schema are not independent, so Wilson and McNemar are optimistic. As a sensitivity analysis we resample **schemas** (cluster bootstrap) and report the interval; if it changes the conclusion we say so.
- **Determinism:** at temperature 0 MLX may still not be deterministic. W05 measures this on the original (two identical runs). If tasks flip, each condition is run k times and analysed per task as clustered data; **k: [OPEN]**.
- A non-significant difference is never described as "no effect"; we state the interval width next to every claim.

Computed with `scripts/power_table.py` on 2026-11-10 (properties of the tests, not results):

| Wilson half-width, pp | p = 30% | p = 50% | p = 70% |
|---|---|---|---|
| n = 200 | 6.3 | 6.9 | 6.3 |
| n = 300 | 5.2 | 5.6 | 5.2 |
| n = 500 | 4.0 | 4.4 | 4.0 |

Smallest net improvement (percentage points of N) that reaches p < threshold with exact McNemar, given the share of discordant tasks:

| N | discordant | p < 0.05 | p < 0.0167 (Holm, first step) |
|---|---|---|---|
| 200 | 10% | 5.0 | 6.0 |
| 200 | 20% | 7.0 | 8.0 |
| 300 | 10% | 4.0 | 4.7 |
| 300 | 20% | 6.0 | 6.7 |
| 500 | 10% | 3.2 | 3.6 |
| 500 | 20% | 4.4 | 5.2 |

Reading: with a few hundred test tasks only improvements of several points are detectable; smaller effects will come out as "not detectable at this sample size".

## 6. Anti-overfitting protocol
- dev/val for iterating, test **once per condition**, after the final checkpoint and configuration are frozen and hashed. No change after looking at test.
- **Log of every attempt**: each proposed WSP change and each LoRA configuration, accepted or discarded, with rationale, tensors touched, parameter count and dev/val scores (`runs/…`, append-only). The report includes the discarded ones.
- **Acceptance rule for a WSP change** (fixed before W07 starts): **[OPEN]** — e.g. a minimum improvement on val with its interval, no failure of the sanity checks (section 9). The same number of val evaluations/trials is allowed for WSP and LoRA, and counted, so neither gets more tuning freedom. **Trial budget: [OPEN]**.
- The number of val evaluations is recorded to bound adaptive overfitting on val.
- The development model never sees test items, test schemas or test results.

## 7. Matched-budget comparison (WSP vs LoRA)
**Proposed default, to be confirmed: [OPEN]** — report the exact number of modified parameters of WSP (P_wsp) and compare it with (a) a LoRA whose trainable parameters ≤ P_wsp and (b) one conventional LoRA configuration as reference, both with the same training data, the same trial budget and the same val-evaluation budget. If at least three points are available, also report accuracy vs % of parameters modified (curve). If WSP does not use training data, that is stated and the data advantage of LoRA is reported, not hidden. LoRA data, rank, hyperparameters and GPU budget: **[OPEN]** (task W08; the HF credit budget has not been checked against this protocol).

## 8. Feasibility gate (task W05)
Before investing in WSP/LoRA we measure the original on **val** (never test). **Proposed thresholds, to be confirmed by Nikola before the first W05 run: [OPEN]**: if the Wilson 95% upper bound of the baseline is < 15%, the task is too hard for a targeted change to plausibly help; if the lower bound is > 85%, there is no headroom.
In either case we stop and report; changing dataset is a recorded decision (allowed before modified runs), not a deviation. Per-language baselines are reported too, since headroom may exist only in some languages; the target is never chosen by looking at test.

## 9. Sanity checks of the modified models
A small fixed set of non-SQL prompts in DE/FR/IT/EN (the regression set, W13) plus the executable-query rate on dev. A modified model is flagged "degraded" if it answers in the wrong language, produces degenerate/empty output, or its executable-query rate drops below a limit. **Set and limits: [OPEN]**.
A degraded checkpoint is **reported**, not hidden, and is not interpreted as a capability change.

## 10. Reproducibility
- Each run saves `results.jsonl`, `calls.jsonl`, `meta.json` with sha256; `agentbench run --replay RUN_DIR` regenerates scores without a model.
- For weights: sha256 of every checkpoint, list of modified tensors, exact parameter counts, full configuration. Models, versions, roles and licences in `models.yaml`; `agentbench compliance` checks the rules; `agentbench manifest` builds the model list for the report.
- The gateway (from 2026-11-27 08:00) most likely serves only the original weights; modified checkpoints are served by us. Results obtained through the gateway and through local MLX are not mixed in one comparison.

## 11. What would change our conclusion
- Intervals of A, B and C overlap heavily and Holm-adjusted p > 0.05: we report "no detectable difference at this sample size".
- The schema-cluster bootstrap contradicts the task-level test: we report the effect as not robust to schema dependence.
- A modified checkpoint fails the sanity checks: its comparison is reported as degraded, not as a capability result.
- The baseline fails the feasibility gate: the experiment is re-scoped before any modification is made.

## 12. Known limitations
One 8B model; small test set, with tasks clustered by schema; one seed (unless k > 1); serving through MLX may differ numerically from the official gateway (not verified); the reasoning setting influences the outcome;
Swiss public data may not represent enterprise databases; weight changes are designed with a development model, so they are not blind to the method's design; the regression set covers only a few capabilities.
Nothing here has been measured yet: no WSP, LoRA or baseline numbers exist.

## 13. Decisions log
- **2026-11-10 (before any baseline or modified-weights result existed):** (a) primary score = strict execution accuracy only (`sql_result_match`); relaxed execution accuracy and final-number correctness are diagnostic checks (recorded, not scored); (b) the number extractor now merges space/NBSP-separated thousands groups ("81 839"): found in the first 6 tasks of an aborted baseline run (`runs/ABANDONED-20261110-dev-r1-partial-scorer-bug`, discarded, not analysed beyond this bug). Tasks regenerated; no result of the original, WSP or LoRA conditions had been recorded.
- **2026-11-10 (during the first valid baseline, dev/val of the original only; no WSP/LoRA result exists):** (c) in SQL tasks the implicit `completed` check ("wrote a final answer within max_steps") is **diagnostic**, not part of the primary score. Reason: in the first ~55 dev tasks Apertus often obtained the correct result and then repeated the same query until max_steps (`runs/baseline-orig-dev-r1`), which the old rule counted as a SQL failure. The completion rate is still recorded and reported. The baseline is **re-scored by replay** (`agentbench run --replay`) so all runs use the same definition; the runner protocol (conversation format, max_steps = 6, malformed tool calls handled as before) is **frozen as it was in the baseline** for all conditions: a malformed tool call can end a task with a server error (HTTP 404), counted as a failure in every condition.
- **2026-11-10 (after the first valid baseline of the original model on dev/val; no WSP/LoRA result exists):** (d) baseline run with `--thinking off` (provisional choice by the development model, **not yet confirmed by the team**); (e) temperature-0 determinism checked on 10 val tasks (all outcomes, queries and final texts identical): k = 1 repetition for now (small, single-schema sample); (f) feasibility gate with the *proposed* thresholds: passed (val 9/30 = 30%, Wilson 17–48%; dev 46/96 = 48%, 38–58%); numbers and caveats in `docs/baseline_original.md`; (g) **proposal, not a decision:** add a *prompt-only control* (original weights with a system-prompt instruction to return only the requested columns), because in the baseline all 18 strict-only failures that the relaxed score accepts are column-count differences (`docs/baseline_original.md`) and a prompt change could recover them without touching weights. The strict-vs-relaxed choice for the primary score is still **open** and must be closed before any WSP/LoRA run.
*(still open, one dated line each when closed: reasoning mode, k repeats, regression set and limits, acceptance rule, trial budget, matched-budget rule, LoRA protocol, gate thresholds, test size)*

## 14. Deviations
*(empty — started 2026-11-10; any change after the first modified-weights run goes here with date and reason)*
