# dev-tasks — compiti da svolgere con Claude Code

Un file per compito. Leggi prima `../CLAUDE.md` e `../../CLAUDE.md`: contengono le regole del hackathon e i limiti del progetto.

**Direzione attuale (10 nov 2026): Apertus Weight-Space Lab** — Weight-Space Programming su Apertus v1.5 8B, valutato su Text-to-SQL (DuckDB) contro l'originale e contro LoRA.
Il lavoro attivo è la **serie W**. La **serie T** è lo storico del progetto precedente (banco di prova agentico): non si riprende, salvo dove indicato.

## Come si lavora
1. Scegli un compito W con stato **pronto** (non "bloccato"), partendo dalla priorità più alta e rispettando "Serve".
2. Un compito alla volta; lavora in un ramo git.
3. Fai solo ciò che il compito chiede. Se serve altro, scrivilo nella sezione "Esito" come nuova proposta.
4. Alla fine: test passati, `make compliance` senza errori, documenti allineati.
5. Compila in fondo al file la sezione **Esito**: cosa hai fatto, cosa hai **verificato davvero** (comando e risultato) e cosa **non** hai potuto verificare. Cambia la riga `Stato:` in cima.
6. Non inventare risultati: se un comando non gira, scrivilo. **Mai scegliere modifiche ai pesi guardando il test set.**

## Serie W — attiva
| ID | Compito | Priorità | Stato | Serve |
| --- | --- | --- | --- | --- |
| W01 | Riorientare il repository (archiviare la suite agentica, nucleo pulito) | alta (primo) | **fatto** (rinomina in attesa di Nikola) | — |
| W02 | Dati e licenze: BIRD, DuckDB, dataset analitico, split dev/val/test | alta | **v0.1 fatto** (210 task reali CC0); resta revisione umana delle domande |  — |
| W03 | Ambiente Text-to-SQL: tool `run_sql` ed execution accuracy | alta | **fatto sui dati sintetici** (mai provato con Apertus reale) | W01, W02 |
| W04 | Protocollo di valutazione e nuova pre-registrazione | alta | **bozza v0.1 fatta**; punti [OPEN] da chiudere con la squadra | — |
| W05 | Baseline: Apertus 8B originale su dev e val | alta | pronto dopo W03 | W03, server MLX acceso |
| W06 | Strumenti di ispezione e modifica dei pesi | alta | **parziale**: strumenti sui pesi fatti (sintetici), PyTorch/HF Jobs no | ambiente PyTorch separato |
| W07 | Ciclo Weight-Space Programming | alta | **bloccato**: scheda dei metodi scritta, metodo da scegliere | W04, W05, W06 |
| W08 | Baseline LoRA con protocollo comparabile | alta | **bloccato**: protocollo e budget proposti, nessun LoRA | W02, W04 |
| W09 | Valutazione a tre condizioni, regressioni e costi | alta | **bloccato** | W05, W07, W08 |
| W10 | Applicazione dimostrativa di data analysis self-hosted | media-alta | **prima versione** (solo con modello finto) | W03, un checkpoint servibile |
| W11 | Architettura di deployment e conformità | alta | **parziale**: opzioni documentate, architettura da scegliere (Nikola) | scelta di Nikola |
| W12 | Rapporto tecnico (inglese) | alta | **bozza riscritta** (risultati TBD) | — |
| W13 | Misura di regressione su capacità non ottimizzate | media | **proposto** (36 item), da confermare | scelta del set |

Ordine consigliato: **W01 → W04 → W02 → W03 → W05**, in parallelo **W06** e **W12**; poi W07/W08 (quando i metodi sono decisi) → W09; **W10** e **W11** prima del 27 novembre.

## Serie T — storico (progetto agentico precedente)
| ID | Compito | Stato finale |
| --- | --- | --- |
| T01 | Repository git e pulizia | fatto (valido) |
| T02 | Endpoint consentiti (gateway CSCS/Keera) | fatto (valido) |
| T03 | Difetti noti della suite agentica | fatto (suite in archiviazione: W01) |
| T04 | Run reali e ripetibilità (suite agentica) | in corso in background; solo storico |
| T05 | Modalità con ragionamento (`enable_thinking`) | fatto: il server ragiona di default; flag `--thinking` |
| T06 | Confronto pesi originali/modificati | **sostituito da W09** |
| T07 | Docker sul Mac, senza rete | fatto (riusabile in W11) |
| T08 | Giudice open-weights | **obsoleto** (valutazione per esecuzione) |
| T09 | Estendere la suite agentica a 62 task | fatto (suite in archiviazione: W01) |
| T10 | BFCL tramite EvalScope | **obsoleto**, solo fattibilità scritta (`../docs/benchmark_esterni.md`) |
| T11 | AgentDojo e τ-bench | **obsoleto**, solo fattibilità scritta |
| T12 | Prova del gateway CSCS | da rivalutare (bloccato fino al 27 nov 08:00) |
| T13 | Bozza del rapporto tecnico | fatto (bozza vecchia: riscrittura in W12) |

## Messaggi in sospeso per Nikola (non sono compiti di codice)
- Scelta dell'**architettura di deployment** (on-premise / air-gapped / cloud sovrano svizzero) — serve per W11 e per il rapporto.
- Metodo concreto di WSP (layer, parametri, trasformazioni) e **protocollo LoRA** comparabile (dati, budget): bloccano W07 e W08.
- Condizione di ragionamento (`--thinking on|off`) per tutte le condizioni.
- Set di regressione (W13) e se rinominare la cartella `apertus-agent-harness` (W01).
- Risposta degli organizzatori su progetti personali e pesi propri. Da chiedere anche (10 nov 2026): **criteri di giuria dell'evento del 27 nov** (il confronto con i progetti
  di ottobre si basa sull'evento online, tracce 1A/1B/2A/2B: non è verificato che valgano a Zurigo) e **cosa si può preparare prima del 27 nov** (la chiave del gateway si sblocca alle 08:00).
- Direzione dati proposta il 10 nov: dataset Text-to-SQL su open data svizzeri, multilingue DE/FR/IT/EN, split per schema (W02); BIRD secondario. Da confermare dalla squadra.
- Modelli di sviluppo realmente usati oltre a Claude Sonnet 5.5 (es. "GPT-6 Astra" del documento): da dichiarare con versione e ruolo solo se usati.
