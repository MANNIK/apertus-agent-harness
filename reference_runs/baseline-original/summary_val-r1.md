## rescored-baseline-orig-val-r1

- modello `apertus-v1.5-8b-mlx-bf16` (percorso locale omesso) · extra_body `{'chat_template_kwargs': {'enable_thinking': False}}` · temperatura 0.0 · max_tokens 1024 · task-set digest `aca29adfd919` · 30 task
- **Punteggio primario (execution accuracy rigida): 9/30 = 30% (IC 95% 17–48%)**
- Rilassata (colonne in più ammesse, diagnostica): 10/30 = 33% (IC 95% 19–51%) · Conclusi con risposta finale (diagnostica): 27/30 = 90% (IC 95% 74–97%)
- Numero della risposta finale giusto (diagnostica, solo task con risposta numerica): 9/24 = 38% (IC 95% 21–57%)
- Tempo per task: mediano 61 s · p90 131 s · max 194 s · totale 0.62 h
- Chiamate a `run_sql`: 44 · errori di parsing delle tool call: 1 · task senza alcuna query: 3
- Motivi di stop: {'max_steps': 2, 'final': 27, 'error': 1} · tipi di errore dei tool: {'bad_args': 1, 'tool_error': 1}

**Per lingua della domanda**

| gruppo | n | primaria (rigida) | rilassata | conclusi |
|---|---:|---|---:|---:|
| de | 8 | 3/8 = 38% (IC 95% 14–69%) | 3/8 | 7/8 |
| en | 7 | 3/7 = 43% (IC 95% 16–75%) | 4/7 | 5/7 |
| fr | 8 | 2/8 = 25% (IC 95% 7–59%) | 2/8 | 8/8 |
| it | 7 | 1/7 = 14% (IC 95% 3–51%) | 1/7 | 7/7 |

**Per schema**

| gruppo | n | primaria (rigida) | rilassata | conclusi |
|---|---:|---|---:|---:|
| abfl | 15 | 4/15 = 27% (IC 95% 11–52%) | 4/15 | 13/15 |
| eink | 15 | 5/15 = 33% (IC 95% 15–58%) | 6/15 | 14/15 |

**Per trappola**

| gruppo | n | primaria (rigida) | rilassata | conclusi |
|---|---:|---|---:|---:|
| cross_lingual_schema | 3 | 3/3 = 100% (IC 95% 44–100%) | 3/3 | 3/3 |
| nessuna | 15 | 5/15 = 33% (IC 95% 15–58%) | 6/15 | 14/15 |
| trailing_whitespace | 12 | 1/12 = 8% (IC 95% 1–35%) | 1/12 | 10/12 |

**Per categoria**

| gruppo | n | primaria (rigida) | rilassata | conclusi |
|---|---:|---|---:|---:|
| aggregation | 6 | 1/6 = 17% (IC 95% 3–56%) | 1/6 | 5/6 |
| argmax | 6 | 0/6 = 0% (IC 95% 0–39%) | 1/6 | 6/6 |
| arithmetic | 6 | 1/6 = 17% (IC 95% 3–56%) | 1/6 | 5/6 |
| filter_count | 3 | 1/3 = 33% (IC 95% 6–79%) | 1/3 | 3/3 |
| lookup | 9 | 6/9 = 67% (IC 95% 35–88%) | 6/9 | 8/9 | 

