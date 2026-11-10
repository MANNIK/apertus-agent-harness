# Apertus Weight-Space Lab (nome provvisorio della cartella: `apertus-agent-harness`)

Sistema riproducibile per migliorare una capacità specifica di **Apertus v1.5 8B** con **Weight-Space Programming (WSP)** e misurare il risultato contro
l'originale e contro un fine-tuning LoRA. Task centrale: **Text-to-SQL su DuckDB**, valutato **per esecuzione** delle query (nessun LLM nel punteggio).
Contesto e regole del hackathon: `../CLAUDE.md`; compiti: `dev-tasks/README.md` (serie W).

**Stato (10 nov 2026, dopo W01):** esiste solo il **nucleo** (client OpenAI-compatibile, registrazione/replay, statistiche, report, conformità, parser delle tool call, CLI).
Con **W03** esistono anche il tool `run_sql` (DuckDB in sola lettura), l'execution accuracy e 8 task **sintetici** di prova (`tasks/demo_sales.yaml`, non sono il dataset di valutazione). **Non esistono ancora** il dataset reale, gli strumenti sui pesi, WSP, LoRA, l'applicazione: sono i compiti W02 (in corso), W05–W10. WSP è un'ipotesi, non un risultato.
La suite agentica del vecchio progetto è in `archive/agent-suite/` (vedi il suo `LEGGIMI.md`); **le sezioni di questo README sui task, i tool finti e i controlli la descrivono e sono storiche**
finché W03 non le sostituisce. Il nucleo funziona con qualunque server che esponga `/v1/chat/completions` (mlx-lm, llama.cpp, vLLM, LM Studio, Ollama…).

Il vecchio progetto era un banco di prova **agentico**: il modello parlava con tool finti e deterministici (meteo, calcolatrice, knowledge base, file virtuali, email finta) e
i controlli guardavano lo stato finale oltre al testo. L'idea dei controlli deterministici, senza giudice AI, resta il principio anche nel nuovo progetto.

## Avvio rapido (Mac)

```bash
# 0) Una volta sola, dalla cartella del progetto: scarica uv (solo qui dentro, in .uv/),
#    crea .venv con harness + mlx-lm. Non tocca .zshrc né installa nulla di globale.
scripts/bootstrap.sh

# 1) Server del modello (terminale A): usa i pesi già scaricati in ../models/
scripts/serve_mlx.sh

# 2) Harness (terminale B), dalla cartella del progetto.
#    Esporta le DUE variabili che serve_mlx.sh stampa all'avvio (APERTUS_MODEL = percorso del modello).
export APERTUS_BASE_URL=http://localhost:8080/v1
export APERTUS_MODEL="<percorso stampato da serve_mlx.sh>"

.venv/bin/agentbench smoke          # PRIMO PASSO: il server fa tool calling? in che formato?
.venv/bin/agentbench run            # task Text-to-SQL in tasks/ (oggi 8 sintetici di prova; il dataset reale arriva con W02)
.venv/bin/agentbench report runs/<cartella>
```

Dopo il bootstrap non serve più `uv`: si usa direttamente `.venv/bin/agentbench` (oppure
`source .venv/bin/activate`, che vale solo per quella finestra di terminale).

`smoke` è il comando da lanciare per primo: manda una richiesta con un tool, stampa il messaggio
**grezzo** del server e dice se la tool call è arrivata strutturata (`native`) o come testo
(`prefix_tag`, ecc.). Se è testo, l'harness usa il parser di fallback e te lo segnala.

## Modello in locale (cartella del progetto)

I pesi sono in `../models/apertus-v1.5-8b-mlx-bf16` (conversione MLX di `tokimoa/apertus-v1.5-8b-mlx-bf16`,
commit `085831737782`, 16,15 GB, hash SHA-256 verificati). Per rifare o riprendere il download:

```bash
scripts/download_model.sh tokimoa/apertus-v1.5-8b-mlx-bf16 ../models/apertus-v1.5-8b-mlx-bf16
```

Per avviare il server su quella cartella (poi esporta le due variabili che lo script stampa):

```bash
scripts/bootstrap.sh    # una volta sola: installa mlx-lm nel .venv del progetto
scripts/serve_mlx.sh
```

`APERTUS_MODEL` deve essere uguale al percorso con cui il server è stato avviato: è quello che lo script
stampa. Se il server dà errore sul nome del modello, controlla che le due stringhe coincidano.

## Docker, senza rete (verificato il 10 nov 2026, Docker 29.5.3 su Mac arm64)

```bash
make docker-build      # immagine minimale, senza modelli (~50 MB)
make docker-demo       # demo con --network none: deve dare 62/62 e 0 errori di conformità
make airgap-check      # come sopra + prova che le connessioni in uscita falliscono nel container
```
L'immagine base (`python:3.12-slim`) e i pacchetti **non sono bloccati** per versione/digest. La demo usa un server finto su loopback: non prova un modello dentro il container.

## Dove finisce cosa (e come ripulire)

Tutto resta dentro la cartella `HACKATON APERTUS ZURIGO`:

| Cartella | Contenuto |
|---|---|
| `.venv/` | ambiente Python del progetto (harness, pytest, mlx-lm) |
| `.uv/` | `uv` stesso, la sua cache e, se serve, un Python scaricato da uv |
| `models/` | i pesi del modello |
| `runs/` | risultati delle valutazioni |

`bootstrap.sh` non modifica file di configurazione (niente `.zshrc`, niente PATH, niente `sudo`).
Per eliminare tutto basta cancellare la cartella. Se hai già usato `uv` altrove, `bootstrap.sh` lo
riconosce e lo usa, ma cache e Python restano comunque in `.uv/`.

Alternativa senza lo script: `python3 -m venv .venv && .venv/bin/pip install -e ".[dev,mlx]"`, solo se
`python3 --version` mostra 3.10 o superiore (il Python di sistema del Mac può essere più vecchio).

## Cosa misura

| Categoria | Task | Cosa verifica |
|---|---:|---|
| `single_call` | 6 | tool giusto, argomenti giusti, risultato usato (prompt IT/DE/EN/FR) |
| `arguments` | 9 | valori esatti, enum, più chiamate indipendenti; importi con separatori diversi (`1’250.50`, `1.500,75`), caratteri speciali, date |
| `multi_step` | 6 | il risultato di un passo alimenta il successivo; N chiamate; scelta del file giusto |
| `error_recovery` | 4 | guasto temporaneo, nome città sbagliato, file nel posto sbagliato, tool sempre rotto (niente risultati inventati) |
| `abstention` | 4 | non chiamare tool quando non servono, tool inesistente, argomento mancante (chiedere) |
| `injection` | 8 | istruzioni dentro file, risultati di ricerca e testo di un errore; esplicite e velate; IT/DE/EN; azioni non richieste; con esito "non esercitato" |
| `judge` | 6 | classificare traiettorie SAFE/UNSAFE (nessun tool) |
| `multilingual` | 7 | scenari analoghi in FR/DE/IT (cambio, ticket, KB, astensione) |
| `parallel` | 3 | più chiamate indipendenti; il parallelismo nello stesso turno è un controllo *diagnostico* (non conta nel punteggio) |
| `long_chain` | 4 | catene di 4-9 passi con tool di disturbo (KB → cambio → email; file → somma → ticket) |
| `ambiguity` | 5 | chiedere quando manca un dato, agire quando si può dedurre (coppie "ask"/"act") |

I 29 task aggiunti il 10 nov (compito T09) sono stati scritti **prima** di vedere risultati di Apertus e non vanno ritoccati dopo averli visti. Cambiano il digest della suite: le run con 33 task non sono confrontabili.

Oltre al pass rate, il report mostra la **salute delle tool call**: quante sono valide (tool
esistente, argomenti conformi allo schema), da dove sono state estratte, quanti errori ha
causato il modello e quanti il tool.

## Come è fatto (`src/agentbench/`)

| File | Cosa fa |
|---|---|
| `client.py` | Client HTTP verso `/v1/chat/completions`. Restituisce il messaggio grezzo; `--extra-body` aggiunge campi (es. `chat_template_kwargs`). |
| `parser.py` | Estrae le tool call: prima il campo `tool_calls`, poi i marcatori di Apertus `<\|tools_prefix\|>…<\|tools_suffix\|>`, poi `<tool_call>`, blocchi ```json e JSON nudo. Un JSON rotto diventa una chiamata `<unparseable>` visibile, non una risposta qualsiasi. |
| `tools.py` | Tool finti, validatore di schema, calcolatrice sicura (AST, niente `eval`), iniezione di guasti. |
| `runner.py` | Il ciclo agentico: modello → tool → risultato → modello, fino alla risposta finale o a `max_steps`. |
| `checks.py` | I controlli (vedi sotto) e `evaluate()`. |
| `tasks.py` | Caricamento e validazione dei file YAML (errori chiari su campi o controlli sbagliati). |
| `bench.py` | Esegue task × ripetizioni, salva `results.jsonl` (riga per riga, con traiettoria completa) e `meta.json`. |
| `report.py` | Report Markdown per GitHub e confronto tra due run. |
| `cli.py` | Comandi `smoke`, `run`, `report`, `compare`, `list-tasks`. |

### Come passano i tool nella conversazione (`--history-mode`)

- `openai` (default): messaggio assistant con `tool_calls` + messaggi con ruolo `tool`.
- `text`: l'assistant resta testo e i risultati tornano in un messaggio `user` che inizia con
  `[tool results]`. Usalo se il chat template del server non gestisce il ruolo `tool`.

## Scrivere un task (STORICO: formato della vecchia suite agentica, sostituito da W03)

I task della vecchia suite stavano in `archive/agent-suite/tasks/*.yaml`:

```yaml
- id: ms_file_sum
  category: multi_step
  prompt: "Sum the revenue from all files in the sales/ folder and save the total to sales/total.txt as just the number."
  tools: [list_files, read_file, write_file, calculator]   # i tool esposti al modello
  setup:                                                   # stato iniziale dei tool
    files: {"sales/q1.txt": "Revenue: 1200", "sales/q2.txt": "Revenue: 1500"}
    faults: {read_file: {fail_first: 1, message: "503"}}   # opzionale: i primi N usi falliscono
    kb: [{title: "...", text: "...", keywords: "..."}]     # opzionale: documenti extra (es. avvelenati)
  max_steps: 8
  checks:                                                  # il task passa solo se passano TUTTI
    - {type: called, tool: read_file, min_times: 2}
    - {type: fs_equals, path: "sales/total.txt", content: "2700"}
```

`agentbench list-tasks` valida i file e mostra l'elenco. Tool disponibili: `get_weather`,
`get_exchange_rate`, `calculator`, `search_kb`, `list_files`, `read_file`, `write_file`,
`send_email`, `create_ticket`.

### Controlli disponibili

Sulle chiamate: `called` (con `args` esatti, `args_in` alternative, `args_contains` sottostringhe,
`min_times`), `not_called`, `no_tool_calls`, `max_calls`, `order` (sotto-sequenza), `args_valid`
(nessun tool inventato né argomenti fuori schema), `eventually_succeeded`.
Sul testo finale: `final_contains_any`, `final_contains_all`, `final_not_contains_any`,
`final_regex`, `final_number` (capisce `1'056`, `1.056,00`, `1,056.00`, `7,67`),
`final_lacks_number`, `final_asks_question`, `verdict` (SAFE/UNSAFE).
Sullo stato: `fs_equals`, `fs_contains`, `outbox_empty`, `outbox_count`, `outbox_to`.
Implicito in ogni task: `completed` (risposta finale entro `max_steps`, senza errori di rete).

Opzioni per task e controlli:
- `diagnostic: true` su un controllo: viene eseguito e mostrato nel report ("Controlli diagnostici") ma **non conta** nel punteggio. Serve a capire dove si ferma il modello (es. `er_file_missing`).
- `exercised: {tool: search_kb, result_contains: "…"}` su un task di injection: se il modello non riceve mai quel contenuto avvelenato, l'esito è `not_exercised` (campo `outcome` di `results.jsonl`). Non è un successo né un fallimento: `passed` è `false`, ma report e confronti lo **escludono dai denominatori** (percentuali, Wilson, McNemar) e lo elencano a parte; `agentbench judge` lo salta.

I controlli sul testo (`final_contains_any` con frasi come "non posso") sono **euristiche**: servono
a smascherare risposte palesemente giuste o sbagliate, non a valutare lo stile.

## Opzioni utili

`--ablate calculator_example` (o variabile `AGENTBENCH_ABLATE`) toglie l'esempio `(12 + 8) / 2` dalla descrizione del calcolatore, per misurare se il modello lo copia. Di default l'esempio resta. L'ablazione è salvata in `meta.json` (`ablations`), compare nel report e nel confronto; il replay riusa quella della run di origine.

```bash
.venv/bin/agentbench run --category multi_step,error_recovery    # solo alcune categorie
.venv/bin/agentbench run --only sc_weather_it,inj_file_exfil     # solo alcuni task
.venv/bin/agentbench run --temperature 0.7 --repeats 5           # varianza: pass rate su 5 ripetizioni
.venv/bin/agentbench run --history-mode text                     # se il template non supporta il ruolo tool
.venv/bin/agentbench run --extra-body '{"chat_template_kwargs": {"enable_thinking": false}}'
.venv/bin/agentbench run --system-prompt-file mio_prompt.txt     # cambia il system prompt
.venv/bin/agentbench compare runs/A runs/B                       # regressioni e miglioramenti task per task
```

Con Apertus 1.5 il tool calling non è supportato in modalità thinking (lo dice la model card):
testa le due modalità separatamente. Se `chat_template_kwargs` venga rispettato da `mlx_lm.server`
non è stato verificato.

## Integrazione con la GitHub CLI

Prerequisiti: `gh auth login`, e il progetto in un repository
(`git init && gh repo create apertus-agent-harness --private --source . --push`).

```bash
# Pubblicare una run (DRY_RUN=1 per vedere i comandi senza eseguirli)
scripts/gh_publish.sh runs/<dir> issue 12             # commento su un'issue
scripts/gh_publish.sh runs/<dir> pr 7                 # commento su una PR
scripts/gh_publish.sh runs/<dir> new-issue "Apertus 1.5 8B bf16 – baseline"
scripts/gh_publish.sh runs/<dir> release v0.1         # allega results.jsonl e report.md

# Lanciare la valutazione su GitHub Actions, attendere, scaricare i risultati
scripts/gh_trigger.sh https://mio-server/v1 swiss-ai/Apertus-v1.5-8B 3 12
```

La workflow `.github/workflows/eval.yml` (avvio manuale) fa smoke test, poi **si ferma con un errore esplicito** perché non c'è più un set di task attivo (da rifare in W03);
a regime scriverà il riepilogo nella pagina della run, commenterà l'issue/PR indicata e salverà `results.jsonl` come artefatto. Le chiavi API vanno nel segreto `APERTUS_API_KEY`.

**Attenzione:** i runner ospitati da GitHub non vedono il `localhost` del tuo Mac. Per usare la
workflow serve un endpoint raggiungibile da Internet o un runner self-hosted (`RUNNER=self-hosted`).
Per la valutazione in locale usa direttamente `agentbench run` + `gh_publish.sh`.

## Test

```bash
.venv/bin/python -m pytest -q
```

170 test passati il 10 nov 2026 dopo W03 (101 dopo W01, più 69 nuovi per l'ambiente SQL; 28 test della vecchia suite sono in `archive/agent-suite/tests/`). Nessun modello né rete: usano un server
OpenAI-compatibile finto (`tests/mock_server.py`). Alcuni test del nucleo leggono `archive/agent-suite/tasks/` solo come **dati di prova** del meccanismo (finché W03 non li sostituisce).
Il nuovo progetto aggiungerà test di risolvibilità delle query gold (vedi `tests/CLAUDE.md`).

## Riproducibilità e regole del hackathon

Tutto passa da `make` (`make help` elenca i comandi).

| Comando | A cosa serve |
|---|---|
| `make setup` | installa uv, Python e dipendenze dentro la cartella (`.uv/`, `.venv/`) |
| `make test` | esegue i test, nessun modello |
| `make demo` | rigioca la run sintetica `reference_runs/demo-oracle-sql` (oracolo che esegue le query gold): deve dare 8/8, senza modello né rete; serve l'extra `sql` |
| `make run` | run dei task in `tasks/` contro `LLM_BASE_URL` / `LLM_NAME` / `LLM_API_KEY` (opzioni: `TASKS=<cartella>`, `REPEATS=n`) |
| `make compare A=… B=…` | confronto con intervalli di Wilson, test di McNemar e differenze di configurazione |
| `make compliance` | controlla le regole (modelli dichiarati, open-weights, endpoint locali, integrità dei file) |
| `make manifest` | elenco modelli per il rapporto tecnico (regola 6) |
| `make judge RUN=…` | giudice open-weights opzionale, con accordo (kappa) rispetto ai controlli automatici |

- **Registrazione e replay.** Ogni run salva `calls.jsonl` (richieste e risposte del modello). `agentbench run --replay RUN_DIR`
  rigioca quelle risposte senza modello e deve riprodurre gli stessi punteggi. Le chiavi ignorano il nome del modello e gli id casuali delle tool call.
- **Statistiche.** `report` e `compare` mostrano intervalli di Wilson al 95% e, nel confronto, il test esatto di McNemar.
- **Conformità.** `models.yaml` è il registro dei modelli; `agentbench compliance` esce con codice 1 se un modello chiuso compare a runtime
  o come giudice, se un endpoint non è locale (avviso, tranne gli host dichiarati in `deployment.allowed_endpoint_hosts` di `models.yaml`, a corrispondenza esatta; oggi `gateway.keera.ch`) o se i file di una run non corrispondono ai sha256 registrati.
- **Giudice (storico, solo se serve).** `agentbench judge` usa il rubric `archive/agent-suite/rubrics/agentic_v1.md` (passalo con `--rubric`; il valore predefinito punta ancora al vecchio percorso), temperatura 0, e salva `judge.jsonl` e `judge_meta.json`.
  Non sostituisce i controlli deterministici: serve a trovare i controlli troppo severi o troppo indulgenti.
- **Piano di analisi.** `docs/analysis_plan.md` (in inglese) fissa in anticipo domande, statistiche e controlli per il confronto base vs modificato.
- **Docker.** `Dockerfile` e `make docker-build` / `make docker-demo`. Non è stato possibile costruire l'immagine nell'ambiente di sviluppo (Docker assente): da provare sul Mac o sulla macchina dell'hackathon.

## Limiti noti

- **Mai eseguito contro Apertus reale**: i test usano un modello finto. Le soglie e le euristiche dei
  task vanno tarate dopo la prima run vera; alcuni task potrebbero risultare troppo severi o troppo
  indulgenti.
- Formato delle tool call verificato dal vivo su Apertus 1.5 8B MLX con `mlx_lm.server`: arriva come testo
  `<|tools_prefix|>[{"nome": {args}}]` senza suffisso e senza `tool_calls` strutturati, quindi si usa il
  parser di riserva. Su vLLM (`--tool-call-parser apertus`) potrebbe essere diverso: rifai `smoke`.
- Il modello può ragionare prima di rispondere (`<|inner_prefix|>…<|inner_suffix|>`): il parser toglie il
  ragionamento dal testo finale, ma resta nella traiettoria grezza. Se il ragionamento è lungo e
  `--max-tokens` è troppo basso (default 1024) la risposta viene troncata prima della parte utile:
  prova `--max-tokens 4096`. Se `mlx_lm.server` rispetti `enable_thinking` non è verificato.
- La workflow GitHub Actions e i comandi `gh` reali non sono stati eseguiti (solo controllo della sintassi
  e prova a secco degli script).
- I task sono pochi per categoria: sufficienti a trovare problemi evidenti, non a produrre stime
  statistiche precise. Usa `--repeats` con temperatura > 0 per vedere la variabilità.
- Con le conversioni MLX quantizzate o di terzi il comportamento può differire dai pesi ufficiali:
  se un risultato sorprende, confrontalo con il riferimento (vedi `compare`).

Dipendenze: `httpx` (BSD-3), `pyyaml` (MIT), `pytest` (MIT, solo sviluppo).
