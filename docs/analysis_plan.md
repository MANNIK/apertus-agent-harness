# Analysis plan — agentic behaviour of Apertus v1.5 8B, base vs. modified weights

Status: **draft, written before any base-vs-modified data exists** (pre-registration). Open items are marked TBD
and will be filled once the organisers and the weight-modification colleague answer. Any change after the first
modified-weights run must be recorded in the "Deviations" section at the bottom, not silently applied.

## 1. Question
Does a given modification of Apertus' weights change its behaviour as a tool-using agent, and in which direction?

Primary hypothesis (H1): the modification changes the pass rate of the agentic suite relative to the base model.
It is two-sided: we do not pre-commit to "improves". Modification technique, direction, strength and layers: TBD (colleague).

## 2. Conditions
| Condition | Weights | Prompt | Notes |
|---|---|---|---|
| A (base) | Apertus v1.5 8B, unmodified, same format/precision as B | `prompts/default` | reference |
| B (modified) | same model with the modification applied | same | the only intended difference is the weights |
| A', B' (optional) | as above | `prompts/persistent.txt` | tests whether the effect survives a different prompt |

Everything else is frozen and compared automatically by `agentbench compare` (config diff): endpoint type, precision,
temperature 0, max_tokens, seed, history mode, task-suite digest. If more than one setting differs the report warns.
If the modified weights need a different server or precision, that confound is stated and, where possible, controlled
by also serving the base weights the same way.

## 3. Outcomes
- **Primary:** overall pass rate on the 33-task suite (deterministic state-based checks, no LLM judge).
- **Secondary (reported, not used to declare success):** pass rate per category (single call, argument fidelity,
  multi-step, error recovery, abstention, injection resistance, judge tasks); valid tool-call format rate;
  mean steps and tool calls per task; latency.
- **Safety-relevant:** injection tasks and abstention tasks are always reported separately, never averaged away.

## 4. Statistics
- Per-condition pass rate with 95% Wilson interval.
- A vs B: exact McNemar test on tasks paired by id (discordant pairs only), plus the counts improved/worsened.
- With temperature 0 and one sample per task the unit is the task; n=33 detects only large effects. We state the
  interval width next to every claim and do not describe a non-significant difference as "no effect".
- If sampling is used, repeats are treated as clustered within task, not as independent observations.
- No multiple-comparison correction is applied to the secondary per-category numbers; they are descriptive.

## 5. Controls
1. **Solvability:** every task has a scripted correct path (`tests/test_tasks_solvable.py`); a failing task is a model result, not a broken task.
2. **Checker validation:** hand audit of all disagreements between the deterministic checks and the optional open-weights judge (`agentbench judge`), with Cohen's kappa reported.
3. **Prompt sensitivity:** the same model under two prompts already flips ~5/33 tasks, so effects smaller than that cannot be attributed to the weights without the A'/B' comparison.
4. **Capability vs. obstacle:** weight edits can remove an obstacle but not add a missing ability; we therefore also report which failures of A are of "obstacle" type (passive refusal, format) vs. "ability" type (wrong arithmetic, wrong tool).
5. **Sanity of the modification:** a few non-agentic prompts to check that B is not simply broken (TBD with colleague).

## 6. Reproducibility
- Every run records full trajectories (`results.jsonl`), every model request/response (`calls.jsonl`), parameters (`meta.json`) and sha256 of both.
- `agentbench run --replay RUN_DIR` regenerates the scores from the recorded responses without any model.
- `make demo` verifies the harness itself on a synthetic oracle run (33/33).
- Models, versions, roles and licences live in `models.yaml`; `agentbench compliance` checks the hackathon rules; `agentbench manifest` produces the model list for the technical report.
- Only Apertus and open-weights models are used at runtime and as judges; closed models (development assistant) are declared as development-only.

## 7. What would change our conclusion
- Intervals of A and B overlap heavily and McNemar p > 0.05: we report "no detectable effect at this sample size".
- B differs from A mainly in tasks that also flip with the prompt: we report the effect as confounded by prompt sensitivity.
- B fails the sanity check (5): the comparison is void.

## 8. Known limitations
Synthetic fake tools, not real services; 33 tasks; one deterministic sample; a single 8B model; text-format tool calls
parsed by our own fallback parser (`prefix_tag`); the thinking mode is not covered because the model card says it does not support tool calling.

## Deviations
(none yet)
