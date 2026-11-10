## rescored-baseline-orig-dev-r1

- modello `apertus-v1.5-8b-mlx-bf16` (percorso locale omesso) · extra_body `{'chat_template_kwargs': {'enable_thinking': False}}` · temperatura 0.0 · max_tokens 1024 · task-set digest `3e8e1eca4d7a` · 96 task
- **Punteggio primario (execution accuracy rigida): 46/96 = 48% (IC 95% 38–58%)**
- Rilassata (colonne in più ammesse, diagnostica): 63/96 = 66% (IC 95% 56–74%) · Conclusi con risposta finale (diagnostica): 86/96 = 90% (IC 95% 82–94%)
- Numero della risposta finale giusto (diagnostica, solo task con risposta numerica): 43/69 = 62% (IC 95% 51–73%)
- Tempo per task: mediano 53 s · p90 165 s · max 370 s · totale 2.15 h
- Chiamate a `run_sql`: 155 · errori di parsing delle tool call: 1 · task senza alcuna query: 5
- Motivi di stop: {'final': 86, 'max_steps': 9, 'error': 1} · tipi di errore dei tool: {'tool_error': 30, 'bad_args': 1}

**Per lingua della domanda**

| gruppo | n | primaria (rigida) | rilassata | conclusi |
|---|---:|---|---:|---:|
| de | 24 | 12/24 = 50% (IC 95% 31–69%) | 17/24 | 22/24 |
| en | 24 | 13/24 = 54% (IC 95% 35–72%) | 16/24 | 21/24 |
| fr | 24 | 10/24 = 42% (IC 95% 24–61%) | 16/24 | 22/24 |
| it | 24 | 11/24 = 46% (IC 95% 28–65%) | 14/24 | 21/24 |

**Per schema**

| gruppo | n | primaria (rigida) | rilassata | conclusi |
|---|---:|---|---:|---:|
| bevc | 12 | 7/12 = 58% (IC 95% 32–81%) | 9/12 | 11/12 |
| bevk | 15 | 10/15 = 67% (IC 95% 42–85%) | 13/15 | 15/15 |
| bevq | 18 | 8/18 = 44% (IC 95% 25–66%) | 14/18 | 13/18 |
| miet | 12 | 0/12 = 0% (IC 95% 0–24%) | 0/12 | 11/12 |
| motg | 12 | 7/12 = 58% (IC 95% 32–81%) | 10/12 | 12/12 |
| sozh | 15 | 7/15 = 47% (IC 95% 25–70%) | 7/15 | 13/15 |
| whgz | 12 | 7/12 = 58% (IC 95% 32–81%) | 10/12 | 11/12 |

**Per trappola**

| gruppo | n | primaria (rigida) | rilassata | conclusi |
|---|---:|---|---:|---:|
| cross_lingual_schema | 9 | 6/9 = 67% (IC 95% 35–88%) | 6/9 | 9/9 |
| domain_codes | 12 | 0/12 = 0% (IC 95% 0–24%) | 0/12 | 11/12 |
| missing_value_marker | 3 | 3/3 = 100% (IC 95% 44–100%) | 3/3 | 3/3 |
| nessuna | 66 | 37/66 = 56% (IC 95% 44–67%) | 54/66 | 59/66 |
| text_numbers | 6 | 0/6 = 0% (IC 95% 0–39%) | 0/6 | 4/6 |

**Per categoria**

| gruppo | n | primaria (rigida) | rilassata | conclusi |
|---|---:|---|---:|---:|
| aggregation | 18 | 15/18 = 83% (IC 95% 61–94%) | 15/18 | 17/18 |
| argmax | 21 | 2/21 = 10% (IC 95% 3–29%) | 13/21 | 21/21 |
| argmin | 3 | 0/3 = 0% (IC 95% 0–56%) | 2/3 | 3/3 |
| arithmetic | 12 | 3/12 = 25% (IC 95% 9–53%) | 4/12 | 7/12 |
| filter_count | 15 | 8/15 = 53% (IC 95% 30–75%) | 8/15 | 12/15 |
| lookup | 21 | 15/21 = 71% (IC 95% 50–86%) | 15/21 | 21/21 |
| ranking | 3 | 0/3 = 0% (IC 95% 0–56%) | 3/3 | 2/3 |
| subquery | 3 | 3/3 = 100% (IC 95% 44–100%) | 3/3 | 3/3 | 

