# Baseline: Apertus v1.5 8B originale su `zurich-sql` v0.1 (W05)

Eseguito il **10 nov 2026** (16:18–19:21) sul Mac della squadra. Tutti i numeri sotto vengono da `scripts/summarize_run.py` sulle run ricalcolate per replay; tabelle per task in `reference_runs/baseline-original/`.
Le run grezze (`runs/baseline-orig-*`, con `calls.jsonl`) esistono **solo su quel Mac** (`runs/` non è su GitHub e `meta.json` contiene il percorso locale). Sono **dev e val**: il test set non è stato toccato.

## Configurazione (identica per tutte le run)
`mlx_lm.server` 0.32.2, pesi `apertus-v1.5-8b-mlx-bf16` (conversione MLX di terzi), **`--thinking off`** (scelta provvisoria, vedi sotto), temperatura 0, max_tokens 1024, timeout 600 s, `max_steps` 6, prompt di sistema `SQL_SYSTEM`, schema con 3 righe d'esempio nel messaggio dell'utente, tool `run_sql` (DuckDB sola lettura). Tool call in formato testo `<|tools_prefix|>`, estratte dal parser di fallback.
Task set: `tasks/zurich/dev` (digest `3e8e1eca4d7a`) e `tasks/zurich/val` (digest `aca29adfd919`). Punteggio: definizione corrente (primario = `sql_result_match` rigida; il resto diagnostico). Le run sono state **ricalcolate per replay** dalle risposte registrate perché la definizione di `completed` è cambiata a metà baseline (decisione §13 (c) del piano, presa prima di analizzare i risultati).

## Risultati (verificati: letti dalle run)
| | Primario: execution accuracy rigida | Rilassata (diagnostica) | Conclusi con risposta finale | Numero finale giusto |
|---|---|---|---|---|
| **dev** (96 task, 7 schemi) | **46/96 = 48% (IC 95% 38–58%)** | 63/96 = 66% (56–74%) | 86/96 = 90% | 43/69 = 62% |
| **val** (30 task, 2 schemi) | **9/30 = 30% (IC 95% 17–48%)** | 10/30 = 33% (19–51%) | 27/30 = 90% | 9/24 = 38% |

Tempo: dev 2,15 h (mediano 53 s per task, p90 165 s, max 370 s); val 0,62 h (mediano 61 s). Dev e val hanno schemi diversi: non sono confrontabili tra loro come stima della stessa quantità.

**Determinismo (verificato):** a temperatura 0 due passate identiche sui primi 10 task di val danno lo **stesso esito, la stessa prima query, la stessa sequenza completa di query e lo stesso testo finale in 10 task su 10**. Limite: quei 10 task sono tutti dello schema `abfl` (9 falliti, 1 passato), quindi il campione è piccolo e poco vario.

## Per lingua, schema, trappola e categoria (dev; tabelle complete in `reference_runs/baseline-original/summary_dev-r1.md`)
- **Lingua (n = 24 ciascuna):** DE 12 (50%), EN 13 (54%), FR 10 (42%), IT 11 (46%): gli intervalli si sovrappongono molto, **nessuna differenza dimostrabile** tra lingue.
- **Schema:** `bevk` 10/15, `bevc` 7/12, `motg` 7/12, `whgz` 7/12, `sozh` 7/15, `bevq` 8/18, **`miet` 0/12** (anche la rilassata 0/12). Val: `eink` 5/15, `abfl` 4/15.
- **Trappola:** `domain_codes` 0/12 (è `miet`), `text_numbers` 0/6, `trailing_whitespace` (val) 1/12, `cross_lingual_schema` 6/9 e `missing_value_marker` 3/3 (campioni minuscoli).
- **Categoria:** aggregation 15/18, lookup 15/21, filter_count 8/15, arithmetic 3/12, ranking 0/3, **argmax 2/21** (rilassata 13/21), argmin 0/3.

## Cosa mostrano i dati e cosa NO
**Verificato dai dati:**
1. **Il divario rigida/rilassata viene solo dal numero di colonne**: in tutte le 17 bocciature del dev (e nell'unica del val) che la misura rilassata perdona il motivo è «numero di colonne diverso». 11 su 17 sono domande «quale X ha il massimo?» (argmax), in cui il modello restituisce anche il valore. Quindi su `argmax` la misura rigida (2/21) misura soprattutto lo **stile** della risposta, quella rilassata (13/21) più la capacità.
2. **`miet` va a zero** (12/12 falliti, anche in versione rilassata). Gli errori sui nomi di colonna sono solo una parte (`gemeinnützig_sort` invece di `GemeinnuetzigSort`, 3 volte); in 4 task il risultato ha una colonna in più, in altri valori o righe sbagliati. Lo schema ha 29 colonne con nomi in codice (`qu50`, `GemeinnuetzigLang`…).
3. In 9 task del dev su 96 e 2 del val su 30 il modello **ripete la stessa query fino a `max_steps`** (visto ad esempio in `bevq_total_2`, dopo aver già ottenuto il risultato giusto; la proporzione dei casi simili non è stata contata); in 5 del dev e 3 del val **non scrive nessuna query**; 1 task del dev e 1 del val si sono fermati con un **errore** (nel dev: HTTP 404 del server dopo una tool call malformata; la causa nel val non è stata esaminata). Il protocollo del runner resta congelato (uguale per tutte le condizioni).

**Ipotesi, NON verificate:**
- Una semplice istruzione nel prompt (restituisci solo le colonne richieste) potrebbe recuperare gran parte del divario rigida/rilassata **senza toccare i pesi**: va misurata come condizione di controllo prima di attribuire miglioramenti a WSP o LoRA.
- Il fallimento su `miet` potrebbe dipendere dall'ampiezza dello schema più che dalla lingua o dalla semantica; non è stato provato.
- Il basso punteggio di `argmax` rigido potrebbe essere in parte dovuto alla formulazione italiana/francese/tedesca delle domande (generate dal modello di sviluppo, non riviste).

## Cancello di fattibilità (W05, soglie PROPOSTE nel piano: limite superiore di Wilson < 15% o inferiore > 85% sul val)
Val: IC 17–48% → **non scatta**; dev: IC 38–58% → **non scatta**. C'è margine in entrambe le direzioni; **il cancello è superato** con le soglie proposte (che restano da confermare dalla squadra). Il margine più chiaro è dove il modello oggi fallisce del tutto (`miet`, numeri salvati come testo, spazi finali, categorie di calcolo e di classifica).

## Decisioni provvisorie usate (da confermare)
- **`--thinking off`:** scelto da Claude, non dalla squadra. Nel pilota il blocco di ragionamento non è mai comparso con i tool attivi, in nessuna delle due modalità (0 su 41 risposte), quindi con i tool la scelta sembra non cambiare i risultati; **non è stato misurato su dev**.
- **k = 1 ripetizione:** il determinismo a temperatura 0 è confermato sul campione sopra; resta il limite di quel campione.
- **Punteggio primario rigido** come da piano; la rilassata è riportata a fianco. Il peso del divario (circa 18 punti su dev) rende la scelta importante: va decisa dalla squadra **prima** di qualunque run WSP/LoRA.

## Limiti
Un solo modello (8B, conversione MLX), una sola configurazione, un solo seme (deterministico); dataset da modelli di domanda e non riletto da madrelingua; velocità bassa (circa 7–8 token/s) che limita il numero di esperimenti; il modello gira su pesi MLX di terzi, non sul gateway ufficiale (differenze non misurate). Nessun risultato su WSP o LoRA esiste.
