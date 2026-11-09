# W13 — Misura di regressione su capacità non ottimizzate
Stato: da decidere · Priorità: media · Serve: decisione di Nikola sul set

## Obiettivo
Poter dire se WSP o LoRA peggiorano capacità diverse dal Text-to-SQL (la 'Regression Rate' del documento), ora che la suite agentica non c'è più.

## Contesto
Il set di regressione non è stato scelto. Servono pochi item deterministici o con risposta verificabile, in lingue e domini diversi, con licenza permissiva; un giudice, se serve, deve essere open-weights (regola 4).

## Passi
1. Proponi 2–3 opzioni (es. piccolo set a risposta verificabile creato da noi, o sottoinsieme di un benchmark open con licenza controllata) con costi, tempi e rischi.
2. Fissa il set e il criterio di 'regressione' in W04 prima di vedere i risultati.
3. Implementa la valutazione con le stesse regole di registrazione/replay.

## Criteri di accettazione
- Set e criterio dichiarati; licenze verificate; esecuzione riproducibile.

## Da non fare
- Non scegliere il set guardando cosa fa peggiorare o migliorare i modelli.

## Esito
(da compilare)
