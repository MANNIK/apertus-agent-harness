## Agent harness · `demo-oracle-synthetic`

33 task × 1 ripetizioni · temperatura 0.0 · history `openai` · suite `a444657e6e9d` · 2026-11-09T22:39:03+00:00

| Categoria | Task | Pass@1 | Task sempre passati |
|---|---:|---:|---:|
| abstention | 4 | 100% | 100% |
| arguments | 4 | 100% | 100% |
| error_recovery | 4 | 100% | 100% |
| injection | 3 | 100% | 100% |
| judge | 6 | 100% | 100% |
| multi_step | 6 | 100% | 100% |
| single_call | 6 | 100% | 100% |
| **Totale** | 33 | **100%** | |

Esecuzioni passate: 33/33 (100%, IC 95% 90–100%). L'intervallo di Wilson assume esecuzioni indipendenti: con più ripetizioni dello stesso task è ottimistico.

### Salute delle tool call

| Metrica | Valore |
|---|---|
| Tool call totali | 38 |
| Chiamate valide (tool esistente, argomenti conformi) | 100% |
| Origine del parsing | native: 38 |
| Errori: tool inventato / argomenti errati / errori del tool | 0 / 0 / 5 |
| Latenza mediana per task | 0.0s |
| Passi medi per task | 2.2 |

### Fallimenti (0 esecuzioni)

Nessun fallimento.

### Controlli diagnostici (non contano nel punteggio)

| Task | Controllo | Soddisfatto |
|---|---|---:|
| `er_file_missing` | called | 1/1 |
| `er_file_missing` | final_asks_question | 0/1 |
