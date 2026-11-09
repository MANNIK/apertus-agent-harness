# T08 — Giudice open-weights con un vero modello
Stato: OBSOLETO · Priorità: —

> **Storico (progetto precedente).** Il Text-to-SQL si valuta per esecuzione, senza giudice. Si riprende solo se in W13 o W10 servisse un giudice open-weights. Nulla è stato scaricato.

## Obiettivo
`agentbench judge` è provato solo con un server finto. Provarlo con un vero modello open-weights e misurare l'accordo con i controlli deterministici.

## Vincoli
- Il giudice deve essere **open-weights** e dichiarato in `models.yaml` con `stages` che include `evaluation`, versione e licenza (regole 4 e 6).
- Con 32 GB di memoria il modello da testare (bf16, ~16 GB) e il giudice **non** stanno insieme se il giudice è grande: prima fai girare la suite (le risposte sono registrate), spegni il server, poi avvia il giudice. Scegli un giudice che stia in memoria (verifica la dimensione prima di scaricare; una versione quantizzata può bastare) e controlla la licenza.
- Non usare Claude né altri modelli chiusi come giudice.

## Passi
1. Scegli il modello (spiega i motivi), scarica con `scripts/download_model.sh` (con verifica sha256), servilo sulla porta 8081 (è il valore predefinito di `agentbench judge`).
2. `agentbench judge runs/<run> --judge-model <nome>`; leggi `judge_report.md`.
3. **Leggi a mano** tutti i disaccordi (controlli PASS/giudice FAIL e viceversa) e scrivi, per ciascuno, chi aveva ragione. Questo decide se i controlli sono troppo severi o troppo indulgenti.
4. Se il giudice dà risposte non analizzabili (`UNPARSEABLE`), migliora il rubric `rubrics/agentic_v1.md` **senza guardare gli esiti dei compiti da cambiare**, e riporta le versioni.

## Criteri di accettazione
- `judge.jsonl`, `judge_meta.json`, `judge_report.md` per almeno una run; `make compliance` senza errori; nota in `docs/` con l'audit a mano.

## Esito
(da compilare)
