# Architettura di deployment (regola 5): opzioni e stato (W11)

Stato: **la scelta spetta a Nikola** (`deployment.target` in `models.yaml` resta vuoto di proposito; `agentbench compliance` dà un avviso finché non è impostato). Questo documento elenca fatti e conseguenze.

La regola 5 chiede che la soluzione **possa girare** in UNA tra: on-premise, air-gapped, cloud sovrano svizzero (da dichiarare).

## Cosa esiste oggi (verificato dove indicato)
- Codice della soluzione: nessuna libreria di rete oltre a `httpx` in `client.py` (controllo AST, **verificato** da `make compliance`). Il database SQL è DuckDB **locale in sola lettura**, con file e rete disabilitati per le query del modello (**verificato** da test).
- Modello servito in locale con `mlx_lm.server` su un Mac (**verificato** il 10 nov 2026: avvio, smoke test, due pilota e baseline). Nessuna chiamata a modelli chiusi a runtime o nelle valutazioni.
- Dati: CSV locali CC0 in `data/zurich/`, nessun download a runtime.
- Docker: per il vecchio progetto un'immagine senza modello girava con `--network none` (T07, verificato il 10 nov 2026). **Non è stata riprovata** per il nuovo progetto: l'immagine non contiene DuckDB né i dati, e il comando predefinito è solo `agentbench compliance`.

## Opzioni
| | On-premise | Air-gapped | Cloud sovrano svizzero |
|---|---|---|---|
| Idea | un server nostro (qui un Mac) con il modello e i dati | come on-premise, ma **senza alcuna rete** verso l'esterno, con prova | modello e app su infrastruttura svizzera (es. CSCS/Keera, o un cloud svizzero) |
| Pesi modificati (WSP/LoRA) | serviti da noi | serviti da noi | **non servibili dal gateway ufficiale** (serve i pesi originali, ipotesi da confermare): serve un nostro server nel cloud |
| Prova di sovranità | rete interna | `--network none`, sonda di uscita, nessuna dipendenza esterna a runtime | dichiarazione + localizzazione dell'infrastruttura |
| Cosa manca | documentare l'hardware | immagine con DuckDB, dati e client; il modello resta fuori dall'immagine (endpoint locale) e va provato in rete interna | un nostro endpoint nel cloud, chiavi, costi |
| Fatica | bassa | media | alta |

## Considerazione (non vincolante)
**Air-gapped/on-premise su un Mac** è l'opzione più vicina a ciò che esiste già (MLX locale, controllo di conformità, DuckDB in sola lettura) e la più forte per il racconto «dati che non escono». Il prezzo: la prestazione del Mac (circa 7 token/s misurati) e l'obbligo di dimostrare l'assenza di rete.
Il cloud sovrano è la scelta naturale per l'originale via gateway (dalla chiave del 27 nov 08:00), ma non per i pesi modificati.

## Per chiudere W11 servono
1. La scelta di Nikola (e l'ok degli organizzatori su pesi propri). 2. Estendere `Dockerfile` con l'extra `sql`, i dati e i task, senza pesi né chiavi nell'immagine, con versioni e digest bloccati; poi `make airgap-check` (richiede Docker acceso). 3. Dichiarare i checkpoint WSP/LoRA in `models.yaml` quando esistono. 4. `make compliance` pulito, senza avvisi non spiegati.
