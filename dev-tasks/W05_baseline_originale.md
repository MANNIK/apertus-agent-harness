# W05 — Baseline: Apertus 8B originale su dev e val
Stato: **fatto (10 nov 2026): baseline dell'originale su dev e val; cancello di fattibilità superato con le soglie proposte** · Priorità: alta · Serve: W03, server MLX acceso

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
Stato: **fatto.** Dettagli, tabelle e limiti in **`docs/baseline_original.md`**; tabelle per task e riassunti in `reference_runs/baseline-original/`.
**Risultati (verificati, run ricalcolate per replay con la definizione corrente; `--thinking off`, temperatura 0):**
- dev: **46/96 = 48% (IC 95% 38–58%)** execution accuracy rigida; rilassata 63/96 = 66%; conclusi 86/96. val: **9/30 = 30% (17–48%)**; rilassata 10/30.
- **Determinismo:** due passate identiche su 10 task di val → esito, query e testo finale uguali in 10 su 10 (campione tutto dello schema `abfl`).
- **Divario rigida/rilassata = solo numero di colonne** (18 casi su 18); 11 su 17 nel dev sono domande argmax. `miet` 0/12. Il modello ripete a volte la stessa query fino a `max_steps`.
- **Cancello di fattibilità (soglie proposte, da confermare):** superato (né limite superiore < 15% né inferiore > 85%).
**Come è andata (onestà):** una prima partenza è stata **scartata dopo 6 task** (`runs/ABANDONED-20261110-dev-r1-partial-scorer-bug`) per un difetto dell'estrattore di numeri («81 839»); a metà della seconda ho cambiato la definizione di `completed` (diagnostico nei task SQL) e ho ricalcolato per replay; entrambe le decisioni sono registrate in `docs/analysis_plan.md` §13 **prima** di analizzare i risultati, e nessun risultato WSP/LoRA esiste.
**Non verificato / aperto:** `--thinking off` non è stato confrontato su dev (solo pilota); un solo seme; velocità ~7–8 token/s (dev 2,15 h); run grezze solo sul Mac (`runs/` non è su GitHub); regole di confronto e controllo «solo prompt» da decidere con la squadra.

