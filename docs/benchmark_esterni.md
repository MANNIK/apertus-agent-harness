# Benchmark esterni (BFCL, AgentDojo, τ-bench): stato e fattibilità

Data: 10 novembre 2026. **Stato: NON ESEGUITI.** Questo documento contiene solo (a) licenze e versioni controllate sulle fonti
e (b) stime di fattibilità, marcate come tali. Nessun numero di benchmark esiste ancora; non citare nulla di qui come risultato.

## Cosa è verificato
Controllato il 10 nov 2026 con l'API di GitHub (`/repos/<repo>/license`) e con PyPI (`/pypi/<pkg>/json`):

| Componente | Licenza (fonte) | Ultima versione su PyPI | Python |
|---|---|---|---|
| EvalScope (`modelscope/evalscope`) | Apache-2.0 (GitHub, PyPI) | 1.14.1 | ≥ 3.10 |
| BFCL (`ShishirPatil/gorilla`, pacchetto `bfcl-eval`) | Apache-2.0 (GitHub; PyPI "Apache 2.0") | 2026.3.23 | ≥ 3.10 |
| AgentDojo (`ethz-spylab/agentdojo`) | MIT (GitHub); il campo licenza su PyPI è vuoto | 0.1.35 | ≥ 3.10 |
| τ-bench (`sierra-research/tau-bench`) | MIT (GitHub) | — | — |
| τ²-bench (`sierra-research/tau2-bench`) | MIT (GitHub) | — | — |

**Non controllato:** le licenze delle dipendenze transitive di ciascun pacchetto e quelle dei dataset (BFCL dentro il repo gorilla;
AgentDojo e τ-bench includono i propri dati) — vanno controllate sull'albero reale delle dipendenze prima di installare
(vedi CLAUDE.md: servono licenze permissive).

**Letto solo in forma di riassunto di una ricerca web, non nella documentazione intera:** EvalScope supporta BFCL v3/v4 contro
un endpoint OpenAI-compatibile (`eval_type='openai_api'`, `--api-url`, `--api-key`); `bfcl-eval` va installato a parte; il flag
`is_fc_model` distingue chiamata nativa di funzioni e prompting; BFCL v4 ha una categoria di ricerca web con SerpAPI
(servizio esterno: **da escludere**, regola 3/4); τ-bench usa di default un simulatore utente basato su `gpt-4o` (modello chiuso).

## T10 — BFCL v4 tramite EvalScope: stima di fattibilità
Nulla è stato installato né eseguito. Motivi e rischi:
1. **Formato delle tool call.** Con `mlx_lm.server` le tool call di Apertus arrivano come testo (`<|tools_prefix|>[...]`), non
   come `tool_calls` strutturati (verificato con `agentbench smoke` il 10 nov 2026). La modalità nativa di BFCL (`is_fc_model`)
   si aspetta chiamate strutturate: serve o un piccolo proxy che riusi `agentbench.parser` e riscriva la risposta nel formato
   OpenAI, oppure la modalità a prompting. Il proxy è codice nuovo da testare: stimo ~mezza giornata (**stima, non misura**).
2. **Tempo.** Nelle run di oggi la suite da 62 task (ciascuno con 1–9 passi) richiede circa 20–25 minuti sul Mac con il
   ragionamento attivo (predefinito; misurato: 13 task in ~4,5 min). Le categorie single-turn di BFCL hanno centinaia di casi
   ciascuna: solo una categoria (es. `simple`) richiederebbe qualche ora con il ragionamento attivo (**stima**).
3. **Ragionamento.** Vedi T05: con `--thinking off` ogni risposta è molto più veloce (0,9 s contro ~14 s su una domanda
   breve), ma il risultato non sarebbe confrontabile con la configurazione predefinita: la scelta va dichiarata.
4. **Dipendenze e ambiente.** Va in `external/bfcl/` con un proprio venv e versioni bloccate (EvalScope 1.14.1, bfcl-eval 2026.3.23),
   senza toccare il pacchetto principale né il controllo sulle librerie di rete.

**Raccomandazione:** farlo solo dopo T04/T06 e solo su una categoria piccola (es. `simple`) con `--thinking` dichiarato; escludere
sempre la categoria web-search. Se non c'è tempo prima del 27 nov, dichiararlo come non fatto nel rapporto.

## T11 — AgentDojo e τ-bench: stima di fattibilità
- **τ-bench / τ²-bench.** Richiede un *simulatore utente* a ogni turno. L'unico modello open-weights disponibile qui è Apertus
  stesso (8B): usarlo come simulatore e come agente insieme confonde i due ruoli, e un secondo modello da 8B+ non sta in memoria
  insieme al primo (32 GB, ~16 GB ciascuno in bf16). Il simulatore predefinito (`gpt-4o`) è chiuso: vietato nei risultati.
  **Raccomandazione: non farlo** per i risultati da presentare; al massimo una prova di sviluppo non citabile.
- **AgentDojo.** Ha 4 ambienti e verifica deterministica (utilità e sicurezza dallo stato finale), quindi si presta alle nostre
  regole. Ma ogni task è molto più lungo dei nostri (tool reali dell'ambiente, contesti grandi) e serve lo stesso adattatore del
  parser di T10. Con un 8B locale, anche un sottoinsieme piccolo vale ore di esecuzione (**stima**). Non verificato che funzioni
  con un endpoint locale: la ricerca web non l'ha confermato.
  **Raccomandazione: rimandare**; la nostra suite di injection (8 task) copre lo stesso fenomeno su scala ridotta.

## Cosa serve per procedere (se si decide di farlo)
1. Decidere `--thinking` per i benchmark (e dichiararlo).
2. Costruire il proxy di formato (riuso di `agentbench.parser`) con test.
3. Controllare le licenze dell'albero reale delle dipendenze in un venv separato.
4. Eseguire una sola categoria BFCL, salvare configurazione e output grezzi in `external/bfcl/runs/` (ignorato da git).
