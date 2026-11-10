# apertus-agent-harness (provvisorio: ex banco di prova agentico, ora base di "Apertus Weight-Space Lab")

Contesto del progetto e regole del hackathon: `../CLAUDE.md` (leggilo). In breve: modificare i pesi di Apertus v1.5 8B (WSP) e confrontarli con
l'originale e con LoRA su **Text-to-SQL (DuckDB)**, con valutazione per esecuzione e statistica onesta.

## Stato del repo (aggiornato il 10 nov 2026, sera; riprendiamo **giovedì 12 nov**)
Lavoro su `main` (Nikola ha fatto il merge il 10 nov); un commit e un push per compito. Dettagli e esiti di ogni compito: `dev-tasks/` (serie W attiva; serie T = storico).

**Esiste ed è testato** (tutto con test; ultimo conteggio completo: **246 passati**, `make compliance` 0 errori e 1 avviso sull'architettura):
- **Nucleo:** client OpenAI-compatibile, registrazione/replay, statistiche (Wilson, McNemar), report, conformità, parser delle tool call, CLI.
- **Ambiente Text-to-SQL (W03):** `sql_env.py` (DuckDB **in sola lettura**, file/rete bloccati, una SELECT per chiamata, timeout, schema nel prompt), `sql_eval.py` (regole di confronto), controlli `sql_result_match` (primario, rigido) e `sql_result_projection` (rilassato, diagnostico).
- **Dataset reale (W02):** `zurich-sql` v0.1 = 210 task su 15 dataset **CC0** della Città di Zurigo (`data/zurich/`, `tasks/zurich/{dev,val,test}/`, DE/FR/IT/EN, split per schema: dev 96 / val 30 / test 84). Generati da `scripts/zurich_spec.py` + `build_zurich_tasks.py` (deterministico). Il CLI **rifiuta** i task `test` e `regression_final` senza `--final-test`.
- **Set di regressione (W13, proposta):** `tasks/regression/` 36 item (11 sanity + 25 final). **App (W10):** `app/analyst.py` (`make app`), provata solo con modello finto. **Strumenti sui pesi (W06, parte indipendente dal metodo):** `wsp.py`, solo tensori sintetici.
- **Documenti di proposta:** `docs/wsp_candidate_methods.md` (3 metodi WSP), `docs/lora_budget.md`, `docs/deployment_options.md`, `docs/dati.md`, `docs/analysis_plan.md` (pre-registrazione v0.1), `docs/technical_report.md` (bozza in inglese, risultati TBD).
- **Baseline di Apertus originale (W05, fatto il 10 nov 2026; `--thinking off`, temp 0):** execution accuracy **rigida** dev **46/96 = 48% (IC 95% 38–58%)**, val **9/30 = 30% (17–48%)**; **rilassata** dev 66%, val 33%; determinismo 10/10 su 10 task di val (campione di un solo schema); cancello di fattibilità superato (soglie proposte). Il divario rigida/rilassata è **solo il numero di colonne** (18 casi su 18); `miet` (schema largo con codici) **0/12**.
  Dettagli e limiti: `docs/baseline_original.md`; tabelle per task: `reference_runs/baseline-original/`. Le run grezze (`runs/baseline-orig-*`, `runs/rescored-*`) sono **solo sul Mac** (`runs/` non è su GitHub e contiene il percorso locale): per un altro PC rifare le run o copiarle a mano. `scripts/summarize_run.py RUN` riproduce i numeri.

**NON esiste** (non descriverlo come funzionante): nessun checkpoint WSP né LoRA, nessun metodo WSP scelto, nessuna misura di Apertus con WSP/LoRA, ambiente PyTorch, script Hugging Face Jobs, immagine Docker del nuovo progetto, revisione delle domande da parte di madrelingua.

**Decisioni di Nikola da prendere / chiedere (non deciderle al posto suo):** metodo WSP (scheda: `docs/wsp_candidate_methods.md`); protocollo e opzione LoRA (`docs/lora_budget.md`, saldo reale dei crediti HF); architettura di deployment (`docs/deployment_options.md`); regole di confronto in `sql_eval.py` (**colonne in più: rigida = primaria oggi, rilassata = secondaria; pesa ~18 punti sul dev e va decisa PRIMA di ogni run WSP/LoRA**); **condizione di controllo «solo prompt»** (istruzione di restituire solo le colonne richieste: potrebbe recuperare il divario senza toccare i pesi); `--thinking` (proposta: spento; con i tool attivi il blocco di ragionamento non è mai comparso in 41+ risposte, dato del pilota); set di regressione; rinomina della cartella;
**domande agli organizzatori:** criteri di giuria del 27 nov, uso di pesi propri, cosa si può preparare prima (la chiave del gateway si sblocca il 27 nov alle 08:00).

**Come riprendere giovedì (ordine consigliato):** (1) leggi `docs/baseline_original.md` (margine c'è: dove fallisce del tutto? `miet`, numeri come testo, spazi finali, calcolo e classifiche); (2) chiudi con la squadra i punti [OPEN] di `docs/analysis_plan.md` §13 (regole di confronto, `--thinking`, soglie, set di regressione); (3) scegli il metodo WSP e il protocollo LoRA (W07/W08); (4) fai rivedere le domande a madrelingua (campione ≥10% per lingua); (5) prova l'app con Apertus reale (`make app`); (6) estendi il Dockerfile (W11) quando Docker è acceso.
**Attenzioni pratiche:** il server MLX (`scripts/serve_mlx.sh`) occupa ~16 GB e il Mac ha 32 GB: **un solo modello alla volta**, spegnilo quando non serve (`pkill -f mlx_lm.server`); misurata ~7–8 token/s e ~1 minuto per task (task con schemi larghi fino a 5 minuti): 100 task ≈ 1–2 ore; durante le run lunghe usa `caffeinate -i -m -w <pid>` e non chiudere il coperchio. Ogni run valida usa la stessa configurazione (`--thinking off`, temperatura 0, max_tokens 1024, `--timeout 600`).

## Principi non negoziabili
- **Punteggio ufficiale deterministico, per esecuzione.** Le query SQL si eseguono su DuckDB e si confrontano i risultati con la query gold. Nessun LLM nel
  calcolo del punteggio. Un giudice (`agentbench judge`) è solo uno strumento di taratura, open-weights e dichiarato.
- **Mai selezionare modifiche ai pesi guardando il test set.** Dev e val per iterare, test solo alla fine; split fissi, versionati con impronta.
  Ogni modifica ai pesi tentata va registrata (anche quelle scartate): altrimenti i risultati sono selezionati a posteriori.
- **Niente rete oltre il client.** `compliance.scan_network_imports` (AST) vieta `requests, urllib3, aiohttp, socket, smtplib, ftplib,
  http.client, urllib.request, websockets`; `httpx` è ammesso **solo** in `client.py`. Non aggirarlo. Gli strumenti pesanti (PyTorch,
  transformers, peft) vivono in un **ambiente/extra separato**, non nel pacchetto principale.
- **Riproducibilità.** Ogni run salva `results.jsonl`, `calls.jsonl`, `meta.json` con sha256; `agentbench run --replay RUN` rigioca i punteggi senza modello.
  Per i pesi: hash di ogni checkpoint, elenco dei tensori modificati, numero/% di parametri toccati, configurazione completa.
- **Punteggio primario = solo `sql_result_match` (execution accuracy rigida).** `completed`, `sql_result_projection` e `final_number` sono diagnostici (registrati, non contati): il baseline si ricalcola per replay quando cambia la definizione (decisioni datate in `docs/analysis_plan.md` §13).
- **Ogni task deve essere risolvibile**: ogni task SQL ha la query gold eseguibile in un test.
- **Onestà dei risultati.** Intervalli di Wilson e McNemar sono già nel report. Con tre condizioni i confronti sono a coppie: dichiara la correzione per confronti
  multipli. Non scrivere "migliora" senza guardare gli intervalli, e non descrivere una differenza non significativa come "nessun effetto".
- **WSP è un'ipotesi.** Finché non ci sono run salvate, scrivi "da verificare", non "migliora Apertus".

## Mappa del codice (`src/agentbench/`)
| File | Ruolo | Stato nel nuovo progetto |
| --- | --- | --- |
| `cli.py` | Comandi: `smoke run report compare list-tasks compliance manifest judge` (`run` ha `--thinking`, `--ablate`) | riusato, da estendere |
| `client.py` | Unico punto che parla in rete (httpx); registra le chiamate (`record_to`) | riusato |
| `bench.py` / `runner.py` | Ciclo di una run / ciclo di un task (conversazione, tool, step massimi) | riusato; il tool `run_sql` si innesta qui |
| `parser.py` | Estrae le tool call (native, `<|tools_prefix|>`, ecc.) e toglie il ragionamento `<|inner_prefix|>…<|inner_suffix|>` | riusato |
| `recording.py` / `replay.py` | Registrazione e rigioco (chiavi indipendenti da nome modello e id casuali) | riusato |
| `report.py` / `stats.py` | Report Markdown, confronto, Wilson, McNemar, kappa | riusato; confronto a 3 condizioni da aggiungere |
| `compliance.py` | Registro modelli (`models.yaml`), controlli delle regole 3/4/5/6, manifest (`--lang en`) | riusato; checkpoint modificati da dichiarare |
| `judge.py` | Giudice open-weights opzionale e accordo con i controlli | riusato solo se serve |
| `sql_env.py` | `SqlBox`: DuckDB in sola lettura, tool `run_sql`, schema nel prompt, `SQL_SYSTEM` | **nuovo (W03)**, extra `sql` |
| `sql_eval.py` | Regole del confronto dei risultati (execution accuracy), funzioni pure | **nuovo (W03)** |
| `wsp.py` | Strumenti sui pesi: impronte, ispezione, modifica **reversibile** (annullamento bit a bit), registro JSONL, safetensors (extra `wsp`, non importato dal resto) | **nuovo (W06, parziale)**, solo tensori sintetici |
| `tools.py` | Tool finti (meteo, calcolatrice, KB, file, email, ticket) | **legacy del vecchio progetto**, ancora importato da `runner`/`bench`/`cli`; il nuovo progetto non lo usa (pulizia futura da proporre a Nikola) |
| `checks.py` / `tasks.py` | Controlli sulle chiamate/testo/stato e caricamento dei task YAML | infrastruttura riusata (W03 vi ha aggiunto `sql_result_match` e `Task.meta`); i controlli agentici sono **legacy** |

## Comandi (dalla cartella `apertus-agent-harness/`)
```
scripts/bootstrap.sh              # una volta: uv, Python, dipendenze (tutto dentro .uv/ e .venv/)
.venv/bin/python -m pytest -q     # test (nessun modello, ~1 minuto; NON lanciarli mentre una run di valutazione misura i tempi)
make data | make zurich-tasks     # riscarica i dati CC0 / rigenera i task (deterministico)
make app                          # app dimostrativa su http://127.0.0.1:8765 (serve il modello acceso)
.venv/bin/agentbench run --thinking off --tasks tasks/zurich/dev --out runs/<nome>   # valutazione su dev (val: tasks/zurich/val; test solo con --final-test)
make help                         # elenco comandi; make demo = replay della demo sintetica Text-to-SQL (oracolo, deve dare il 100%)
scripts/serve_mlx.sh              # server del modello locale (porta 8080), stampa le variabili da esportare
.venv/bin/agentbench smoke        # primo test contro il modello (LLM_BASE_URL, LLM_NAME, LLM_API_KEY, oppure APERTUS_*)
make run | make compare A=… B=… | make compliance | make manifest | make judge RUN=… | make docker-build docker-demo airgap-check
```
Il server MLX con il chat template di Apertus **ragiona per impostazione predefinita** (verificato il 10 nov 2026): per fissare la condizione usa
`--thinking on|off` (passa `chat_template_kwargs.enable_thinking`) e dichiaralo sempre nella run.

## Definition of done (per ogni modifica)
1. `.venv/bin/python -m pytest -q` passa. Scrivi o aggiorna i test insieme al codice.
2. `make compliance` non dà ERRORI (gli avvisi vanno spiegati).
3. Se cambi dati, split, formato dei file di una run o il prompt: aggiorna test e documenti; le vecchie run non sono più confrontabili — dillo nel messaggio finale.
4. Ogni modello o checkpoint nuovo è dichiarato in `models.yaml` (versione/hash, tecnica, ruolo, fase) prima di essere usato.
5. README e documenti allineati; segna chiaramente cosa è verificato e cosa no.

## Cosa NON fare
- Non modificare né cancellare `runs/` e `archive/agent-suite/reference_runs/` a mano (sono dati).
- Non citare `archive/agent-suite/reference_runs/demo-oracle` come risultato di Apertus: è un copione sintetico della vecchia suite.
- Non chiamare modelli chiusi dal codice della soluzione o dalle valutazioni; non aggiungere chiamate di rete fuori da `client.py`.
- Non usare il test set per decidere cosa modificare nei pesi; non aggirare `--final-test`.
- Non aggirare i 403 di opendata.swiss (blocca i programmi): la licenza si legge a mano nel browser. Non cambiare il protocollo del runner o il punteggio dopo aver visto risultati senza registrarlo in `docs/analysis_plan.md` §13/§14.
- Non avviare il server MLX da 16 GB senza controllare la RAM libera e senza dirlo; non lasciarlo acceso.
- Non usare `--force`/azioni distruttive su git senza chiedere; non toccare `../models/`; non committare pesi, `.env` o token.
- Non fidarti di quello che "dovrebbe" fare `mlx_lm.server`: se non l'hai provato, scrivilo come non verificato.

## Compiti da svolgere
Cartella `dev-tasks/`: parti da `dev-tasks/README.md` (tabella con lo stato di ogni compito W). Serie T = storico.
