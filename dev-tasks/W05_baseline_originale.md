# W05 — Baseline: Apertus 8B originale su dev e val
Stato: pronto dopo W03 · Priorità: alta · Serve: W03, server MLX acceso (`scripts/serve_mlx.sh`)

## Obiettivo
Misurare l'originale con registrazione completa e quantificare ripetibilità e condizione di ragionamento.

## Contesto
Con `mlx_lm.server` il modello **ragiona per impostazione predefinita** (T05, 10 nov 2026): 0,9 s senza ragionamento contro ~14 s con, su una domanda breve. La scelta incide su tempo, costo e risultato e va dichiarata. Il gateway CSCS (da 27 nov 08:00) serve i pesi originali ufficiali.

## Passi
1. Avvia il server (un solo modello alla volta) e fai `agentbench smoke`.
2. Decidi con Nikola `--thinking on|off` per tutte le condizioni (stessa scelta per originale, WSP, LoRA); scrivila nel piano (W04).
3. Esegui dev (e val) due volte con la stessa configurazione: se i risultati differiscono, la temperatura 0 non è deterministica su MLX; annota quanti task e quali.
4. Replay di ogni run: stessi punteggi. `make compliance` senza errori.
5. Nota in `docs/` con punteggi, intervalli di Wilson e differenze tra le due run identiche.
6. **Cancello di fattibilità (aggiunto il 10 nov 2026):** applica la soglia fissata in W04. Se su dev/val la baseline è così alta da non lasciare margine, o così bassa che una
   modifica mirata non può bastare, **fermati e segnalalo a Nikola** prima di investire in W07/W08: potrebbe servire un altro dataset (W02). Riporta anche i punteggi per lingua della domanda.

## Criteri di accettazione
- Run con `calls.jsonl` e sha256 coerenti; replay uguale.
- Solo numeri letti dalle run, con la cartella citata.

## Da non fare
- Non simulare risultati se il server non risponde. Non usare il test set.

## Esito
(da compilare)
