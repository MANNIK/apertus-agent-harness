# T11 — AgentDojo e τ-bench con simulatore open-weights
Stato: OBSOLETO (solo fattibilità scritta) · Priorità: —

> **Storico (progetto precedente).** Benchmark agentici non rilevanti per il Text-to-SQL. Non eseguiti.

## Obiettivo
Valutare la resistenza alle iniezioni (AgentDojo) e conversazioni agente-utente (τ-bench) con benchmark pubblici, rispettando le regole.

## Vincoli
- **τ-bench** usa di default un simulatore utente basato su gpt-4o (modello chiuso): per risultati da presentare va sostituito con un modello **open-weights** dichiarato in `models.yaml`. Se non è possibile, usalo solo come prova di sviluppo e **non** citarlo come risultato.
- **AgentDojo** richiede un adattatore perché Apertus emette le tool call come testo (`<|tools_prefix|>`) con `mlx_lm.server`: riusa `agentbench.parser`. Controlla licenza e versione.
- Ambiente separato (`external/…`), versioni bloccate, nessuna chiave in file.

## Passi
1. Prima fai una stima di fattibilità per ciascuno (ore, memoria, tempi di esecuzione su un modello 8B in locale). Se non ne vale la pena, scrivilo e fermati.
2. Se procedi: esegui un sottoinsieme piccolo e documentato, salva configurazione e risultati, aggiorna `docs/benchmark_esterni.md`.

## Criteri di accettazione
- Fattibilità scritta; se eseguito, riproducibile e con limiti dichiarati.

## Esito
**Fatto:** stima di fattibilità in `docs/benchmark_esterni.md`: τ-bench richiede un simulatore utente (gpt-4o di default, chiuso; un secondo modello open-weights da 8B+ non sta in memoria insieme ad Apertus su 32 GB) → sconsigliato; AgentDojo (MIT) richiede lo stesso adattatore di formato e ore di esecuzione → rimandato. **Nulla installato né eseguito.**
