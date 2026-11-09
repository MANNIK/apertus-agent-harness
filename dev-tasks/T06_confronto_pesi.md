# T06 — Pipeline di confronto: pesi originali contro pesi modificati
Stato: SOSTITUITO da W09 (e W06–W08) · Priorità: —

> **Storico (progetto precedente).** La pipeline di confronto pesi originali/modificati è ora il cuore del progetto: vedi **W09**. Il collega non serve più per la tecnica: il metodo WSP lo costruiamo noi (W06–W07).

## Cosa serve dal collega (Nikola le chiede)
1. Tecnica di modifica. 2. Formato dei pesi (safetensors completi? adattatore LoRA?). 3. Intensità e strati modificati. 4. Hardware usato.

## Obiettivo (quando si sblocca)
Servire pesi originali e modificati **allo stesso modo** (stesso server, stessa precisione, stessi parametri) e lanciare la stessa suite su entrambi, poi confrontare con `agentbench compare`, seguendo `docs/analysis_plan.md`.

## Passi previsti
1. Convertire i pesi modificati in formato MLX se serve (controlla la sintassi con `.venv/bin/python -m mlx_lm convert --help`; non assumerla).
2. Mettere i modelli in `../../models/<nome>/` (mai nel repository). Con 32 GB di memoria **non servire due modelli bf16 insieme**: uno alla volta (`MODEL_DIR=… scripts/serve_mlx.sh`).
3. Aggiungere a `Makefile` e README un flusso `make compare-weights BASE=… MOD=…` che per ciascun modello ricorda i passi (serve, run, stop), salva le run con nomi chiari e produce il confronto. Dichiarare entrambi i modelli in `models.yaml` (il modificato come "Apertus adattato", con tecnica e versione).
4. Aggiungere i controlli di sanità previsti in `docs/analysis_plan.md` §5 (il modello modificato non è semplicemente rotto) con pochi prompt non agentici.
5. Classificare i fallimenti dell'originale in "ostacolo" (passività, formato) e "capacità" (calcolo, strumento sbagliato), come da piano.

## Criteri di accettazione
- Un comando documentato produce il confronto; le due run hanno la stessa configurazione tranne i pesi (`compare` lo mostra).
- Nessuna conclusione scritta senza guardare intervalli e McNemar.

## Da non fare
- Non scegliere tu la tecnica o i parametri del collega. Non modificare il piano di analisi dopo aver visto i dati (usa "Deviations").

## Esito
(da compilare)
