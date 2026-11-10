# W03 — Ambiente Text-to-SQL: tool `run_sql` e execution accuracy
Stato: **fatto sui dati sintetici** (10 nov 2026); il dataset reale dipende da W02 · Priorità: alta · Serve: W01, W02

## Obiettivo
Far eseguire ad Apertus query su DuckDB e valutare i risultati in modo deterministico (execution accuracy e correttezza della risposta finale).

## Contesto
Il punteggio ufficiale non usa nessun LLM: si eseguono la query del modello e la query gold e si confrontano i risultati. DuckDB è eseguito in locale (memoria/file), mai in rete; sta in un extra opzionale.

## Passi
1. Aggiungi DuckDB come **extra opzionale** (licenza verificata in W02) senza rompere `scan_network_imports`.
2. Implementa il tool `run_sql` (solo lettura, timeout e limite di righe dichiarati) e il caricamento dello schema nel prompt o come tool di ispezione.
3. Implementa il controllo di execution accuracy: regole su ordine, duplicati, NULL, tipi e arrotondamenti dichiarate una volta e valide per tutte le condizioni; più il controllo sulla risposta finale (numeri/valori).
   Le regole vanno scritte **prima** di vedere risultati di modelli e coprire esplicitamente: ordine delle righe (solo se la domanda lo richiede), nomi/ordine delle colonne, NULL,
   duplicati, tipi numerici e tolleranza di arrotondamento. Gold con più risposte valide: documentale come casi noti, non ammorbidire il confronto dopo.
4. Scrivi `tests/` con DuckDB in memoria: ogni task ha la query gold in un test di risolvibilità; query sbagliate (colonne/righe in più, ordine, NULL) devono fallire.
5. Crea una demo sintetica (oracolo che esegue le query gold) per `make demo`, con le stesse regole di `demo-oracle`: non è un risultato di Apertus.
6. Aggiorna `src/agentbench/CLAUDE.md`, `tasks/CLAUDE.md` e `tests/CLAUDE.md` con quanto imparato.

## Criteri di accettazione
- Test verdi; demo al 100%; `make compliance` senza errori.
- Un test mostra che l'execution accuracy non dipende dal testo della query.

## Da non fare
- Nessun LLM nel punteggio. Nessuna rete. Non ammorbidire i confronti per far salire i punteggi.

## Esito
Stato: **ambiente e controlli fatti e testati su 8 task sintetici; mai provato con Apertus reale** (10 nov 2026, ramo `riorientamento`).

**Fatto**
- Extra opzionale `sql` (`duckdb`, **2.0.0** installato; licenza **MIT** letta dal `METADATA` e dal file `licenses/LICENSE` del pacchetto). `uv.lock` aggiornato; `bootstrap.sh` installa l'extra. `import duckdb` solo dentro `SqlBox`.
- `src/agentbench/sql_env.py`: `SqlBox` (sottoclasse di `ToolBox`). Il DB si costruisce da `setup.sql_init` con una connessione normale, poi si **riapre in sola lettura**; accesso a file e rete disabilitato, estensioni non installabili, configurazione bloccata,
  **una sola istruzione SELECT** per chiamata (WITH/FROM/DESCRIBE/SHOW ammessi), timeout con `interrupt` (10 s), memoria 512 MB, 1 thread, righe mostrate 50, risultato memorizzato fino a 100.000 righe. Schema (tabelle, tipi, 3 righe d'esempio) aggiunto al messaggio dell'utente, uguale per ogni condizione. `SQL_SYSTEM`: prompt di sistema scelto dal CLI se tutti i task usano `run_sql`.
- `src/agentbench/sql_eval.py`: regole del confronto, **dichiarate una sola volta** (vedi il docstring): multiinsieme di righe (duplicati contano), ordine solo con `order_matters`, colonne per posizione e numero (nomi ignorati), NULL=NULL, tolleranza numerica rel 1e-9 / abs 1e-6, stringhe esatte, tipi distinti (data≠testo, bool≠int).
- Controllo `sql_result_match` in `checks.py` (conta l'**ultima `run_sql` riuscita**); `Task.meta` salvato in `results.jsonl`; la risposta finale si controlla con i `final_number` / `final_contains_*` già esistenti.
- `tasks/demo_sales.yaml` (8 task sintetici DE/FR/IT/EN, trappole: formato data, NULL, schema-linking tra lingue), demo con oracolo (`scripts/build_demo_sql.py`, `reference_runs/demo-oracle-sql`, `make demo`), `tasks/CLAUDE.md`, `reference_runs/CLAUDE.md`.
- Test nuovi: `test_sql_eval.py`, `test_sql_env.py`, `test_sql_tasks.py`, `test_demo_sql.py`.

**Verificato (comandi eseguiti il 10 nov 2026)**
- `.venv/bin/python -m pytest -q`: **170 passati** (101 prima, 69 nuovi). `make demo`: 8/8. `make compliance`: 0 errori, 1 avviso (architettura non scelta).
- Provato a mano e nei test: INSERT/UPDATE/DELETE/CREATE/DROP, `COPY`, `ATTACH`, `read_csv` su file locale e su URL, `SET`, `PRAGMA`, `INSTALL`, due istruzioni insieme: tutti rifiutati senza modificare il DB né creare file. Una query lunga viene interrotta in ~0,5 s e la connessione resta utilizzabile.
- Il test "il risultato non dipende dal testo della query" passa (commenti, spazi, query equivalenti, nomi di colonna diversi); colonna in più, nessuna riga, righe duplicate, NULL contato come 0 e formato data letto male falliscono.

**Non verificato / aperto**
- **Mai eseguito con Apertus reale**: non so come il modello risponde al prompt (schema nel messaggio dell'utente + `SQL_SYSTEM`), se usa `run_sql` in modo corretto né con che formato di tool call. Va provato in W05 (server MLX acceso).
- **Le regole di confronto sono scelte mie** (colonne per posizione, duplicati che contano, tolleranze, "ultima query riuscita"): da rivedere e confermare con la squadra **prima** delle run di W05; dopo, modifiche solo in `docs/analysis_plan.md` → Deviations.
- Con `order_matters: true` il gold deve avere un ordinamento totale: non c'è un controllo automatico di questa regola.
- Docker non è stato provato (assente su questo Mac): l'immagine non contiene ancora DuckDB né i task (da W11).
- I tool finti e i controlli agentici del vecchio progetto restano nel pacchetto come legacy; la loro rimozione è una proposta per Nikola (toccherebbe diversi test del nucleo).
- Task reali (dataset svizzero) e split: W02, non ancora.
