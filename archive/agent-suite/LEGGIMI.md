# Suite agentica del vecchio progetto (archiviata il 10 nov 2026, compito W01)

## Cosa è
Il banco di prova del progetto precedente: 62 task su tool finti (meteo, calcolatrice, base di conoscenza, file, email, ticket), i controlli sulle chiamate, un giudice
open-weights opzionale e una run sintetica di riferimento (`reference_runs/demo-oracle`, un copione scritto a mano, **non** un risultato di Apertus).

## Perché è archiviata
Il 10 nov 2026 la direzione è cambiata: Weight-Space Programming su Apertus 8B valutato su Text-to-SQL (DuckDB). Nikola ha deciso di togliere la suite dal percorso principale,
senza tenerla come controllo di regressione.

## Cosa NON fare con questa cartella
- Non citare i suoi punteggi né `demo-oracle` come risultati del nuovo progetto: task, controlli e prompt sono diversi e **le run non sono confrontabili**.
- Non estenderla e non aggiungere test.
- `tests/` qui dentro **non è eseguibile così com'è** (i percorsi puntano alla radice del vecchio layout); `pytest` raccoglie solo la cartella `tests/` principale.

## Contenuto
| Percorso | Cosa |
| --- | --- |
| `tasks/` | 62 task YAML + `CLAUDE.md` della suite |
| `reference_runs/demo-oracle/` | run sintetica di riferimento (integrità sha256) |
| `prompts/`, `rubrics/` | prompt di sistema e rubrica del giudice agentico |
| `scripts/build_demo.py` | genera `demo-oracle` |
| `tests/` | test della suite: risolvibilità, demo, difetti noti (T03), estensione (T09) |

## Dove resta usata
I moduli `src/agentbench/{tools,checks,tasks}.py` stanno ancora nel pacchetto perché `runner`, `bench` e `cli` li importano: **W03 li sostituisce** con `run_sql` ed execution accuracy.
Fino ad allora alcuni test del nucleo (`e2e`, `replay`, `judge`, `compliance`, `thinking_flag`) leggono `archive/agent-suite/tasks/` solo come **dati di prova** del meccanismo, non come obiettivo.
