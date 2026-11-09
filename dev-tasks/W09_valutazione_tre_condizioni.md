# W09 — Valutazione a tre condizioni, regressioni e costi
Stato: bloccato (servono W05, W07, W08) · Priorità: alta · Serve: W05, W07, W08

## Obiettivo
Confrontare originale, WSP e LoRA con la stessa configurazione, il test set una sola volta, e riportare anche regressioni e costi.

## Contesto
Sostituisce T06. Su 32 GB si serve **un solo modello bf16 alla volta**: per ciascuna condizione serve, esegui, spegni. I pesi modificati vanno convertiti in MLX (controlla `mlx_lm convert --help`, non assumere la sintassi). Il gateway CSCS può servire l'originale ufficiale (dal 27 nov 08:00).

## Passi
1. Flusso documentato (`make compare-weights`): serve → run → stop, con nomi di run `base|wsp|lora-test-…`.
2. Esegui il test set per ciascuna condizione; confronti a coppie con intervalli di Wilson, McNemar e correzione per confronti multipli (come da W04).
3. Riporta metriche secondarie: latenza, VRAM, parametri modificati, costo di adattamento, regression rate (W13), generalizzazione (schemi nuovi).
4. Classifica i fallimenti dell'originale in 'ostacolo' (formato, passività) e 'capacità' (ragionamento sui dati), come da piano.
5. Aggiorna `models.yaml` e `make compliance`.

## Criteri di accettazione
- Un comando documentato produce il confronto; le run differiscono solo per i pesi (`compare` lo mostra); nessuna conclusione senza guardare intervalli e test.

## Da non fare
- Non rifare il test dopo aver visto i risultati per 'sistemare' qualcosa. Non servire due modelli bf16 insieme.

## Esito
(da compilare)
