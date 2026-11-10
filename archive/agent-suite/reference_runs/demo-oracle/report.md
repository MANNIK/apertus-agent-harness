## Agent harness · `demo-oracle-synthetic`

62 task × 1 ripetizioni · temperatura 0.0 · history `openai` · suite `4006e5bc3371` · 2026-11-09T23:35:40+00:00

| Categoria | Task | Pass@1 | Task sempre passati |
|---|---:|---:|---:|
| abstention | 4 | 100% | 100% |
| ambiguity | 5 | 100% | 100% |
| arguments | 9 | 100% | 100% |
| error_recovery | 4 | 100% | 100% |
| injection | 8 | 100% | 100% |
| judge | 6 | 100% | 100% |
| long_chain | 4 | 100% | 100% |
| multi_step | 6 | 100% | 100% |
| multilingual | 7 | 100% | 100% |
| parallel | 3 | 100% | 100% |
| single_call | 6 | 100% | 100% |
| **Totale** | 62 | **100%** | |

Esecuzioni passate: 62/62 (100%, IC 95% 94–100%). L'intervallo di Wilson assume esecuzioni indipendenti: con più ripetizioni dello stesso task è ottimistico.

### Salute delle tool call

| Metrica | Valore |
|---|---|
| Tool call totali | 86 |
| Chiamate valide (tool esistente, argomenti conformi) | 100% |
| Origine del parsing | native: 86 |
| Errori: tool inventato / argomenti errati / errori del tool | 0 / 0 / 6 |
| Latenza mediana per task | 0.0s |
| Passi medi per task | 2.3 |

### Fallimenti (0 esecuzioni)

Nessun fallimento.

### Controlli diagnostici (non contano nel punteggio)

| Task | Controllo | Soddisfatto |
|---|---|---:|
| `er_file_missing` | called | 1/1 |
| `er_file_missing` | final_asks_question | 0/1 |
| `par_emails_three` | calls_in_one_step | 1/1 |
| `par_fx_three` | calls_in_one_step | 1/1 |
| `par_weather_three` | calls_in_one_step | 1/1 |
