# T10 — Benchmark da paper: BFCL v4 tramite EvalScope
Stato: OBSOLETO (solo fattibilità scritta) · Priorità: —

> **Storico (progetto precedente).** BFCL misura il tool calling, non il Text-to-SQL. Non eseguito. Fattibilità, licenze e rischi: `docs/benchmark_esterni.md`.

## Obiettivo
Avere almeno un numero comparabile con la letteratura sul tool calling (Berkeley Function Calling Leaderboard), accanto alla nostra suite, senza mescolare i due.

## Vincoli (regole del hackathon)
- A runtime e nelle valutazioni presentate: solo Apertus e modelli open-weights, nessun servizio AI chiuso. La categoria di **ricerca web** di BFCL usa SerpAPI (servizio esterno): **escludila**, e dichiaralo.
- Ambiente separato (cartella `external/bfcl/` con proprio venv): non aggiungere dipendenze pesanti al pacchetto principale né rompere il controllo sulle librerie di rete.
- Controlla le **licenze** di EvalScope, del dataset e di ogni dipendenza prima di installarli; elencale in `docs/`.

## Passi
1. Leggi la documentazione ufficiale attuale di EvalScope per BFCL e annota la versione che usi (blocca le versioni).
2. Punta il benchmark all'endpoint locale (`LLM_BASE_URL`, `LLM_NAME`). Verifica prima, con `agentbench smoke`, il formato delle tool call: se il server restituisce testo con `<|tools_prefix|>`, serve un adattatore; descrivi cosa hai fatto.
3. Esegui le categorie compatibili, salva output grezzi e configurazione in `external/bfcl/runs/…` (ignorato da git o committa solo i riassunti).
4. Scrivi `docs/benchmark_esterni.md` con: versione, categorie, cosa escluso e perché, risultati, limiti.

## Criteri di accettazione
- Comando riproducibile documentato; risultati con la configurazione esatta; modelli dichiarati in `models.yaml` se ne usi altri.
- Dichiarazione chiara se non sei riuscito a farlo girare (e perché).

## Esito
**Fatto:** solo la verifica di licenze/versioni e una stima di fattibilità in `docs/benchmark_esterni.md` (10 nov 2026). Licenze controllate con l'API di GitHub: EvalScope Apache-2.0, BFCL/gorilla Apache-2.0. **Nulla installato né eseguito.** Dichiarato non eseguito, con i motivi (formato delle tool call come testo con `mlx_lm.server`, tempi, ragionamento attivo di default).
