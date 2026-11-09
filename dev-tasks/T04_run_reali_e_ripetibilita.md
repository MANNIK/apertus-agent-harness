# T04 — Rieseguire le prove reali con registrazione e misurare la ripetibilità
Stato: in corso, storico (3 run della suite agentica avviate il 10 nov; non verranno usate per il nuovo progetto)

> **Storico (progetto precedente).** Misurano la **vecchia suite agentica**. Le tre run (`runs/base-default-a`, `base-default-b`, `base-persistent-a`) sono in esecuzione sul server MLX; restano come storico (ripetibilità del server a temperatura 0) e **non** sono confrontabili con le nuove. Per il nuovo progetto la stessa misura di ripetibilità si rifà in W05 su Text-to-SQL.

## Obiettivo
Le due run reali del 6 nov (27/33 con il prompt normale, 30/33 con `prompts/persistent.txt`) non hanno `calls.jsonl`, quindi non si possono rigiocare. Rifarle con la registrazione e capire quanto è ripetibile il modello a temperatura 0.

## Passi
1. Chiedi a Nikola di avviare `scripts/serve_mlx.sh` in un altro terminale ed esportare le variabili che stampa. Verifica con `.venv/bin/agentbench smoke`.
2. Lancia la suite **due volte** con la stessa configurazione (prompt normale), cartelle `runs/base-default-a` e `runs/base-default-b` (`--out`), poi una volta con `--system-prompt-file prompts/persistent.txt` → `runs/base-persistent-a`.
3. Confronta le due run identiche con `agentbench compare`: se differiscono, la temperatura 0 **non** è deterministica su MLX. Annota quanti task cambiano e quali.
4. Per ogni run: `agentbench run --replay <run> --out runs/replay-check-…` deve dare gli stessi punteggi della run di origine.
5. `make compliance` sulle nuove run (nessun errore).
6. Scrivi una nota in `docs/` (`nota_ripetibilita.md`, italiano) con i numeri **solo** di queste run, senza interpretazioni non supportate.

## Criteri di accettazione
- Tre cartelle di run con `calls.jsonl` e `meta.json` coerenti (sha256).
- Replay = stessi punteggi.
- Nota con: punteggi, intervalli di Wilson, differenze tra le due run identiche.

## Da non fare
- Non cancellare le run del 6 nov. Non modificare i file delle run a mano.
- Se il server non risponde, fermati e dillo: non simulare i risultati.

## Esito
(da compilare)
