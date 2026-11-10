# Baseline LoRA: protocollo proposto e stima del budget (W08)

Stato: **proposta del 10 nov 2026, non decisa e non eseguita.** Nessun LoRA è stato addestrato; i tempi sono stime, non misure.

## Prezzi di Hugging Face Jobs (letti il 10 nov 2026)
Dalla documentazione ufficiale (`huggingface.co/docs/hub/jobs-pricing`, tramite risultato di ricerca; pagina non riletta direttamente):
| Hardware | Memoria GPU | Prezzo orario dichiarato |
|---|---|---|
| a10g-small | 24 GB | 1,00 $ |
| a100-large | 80 GB | 2,50 $ |
Un riepilogo di terze parti riportava cifre molto più alte (circa 3–4 $ per A10G e 8–12 $ per A100): **non coincidono con la documentazione ufficiale**; prima di spendere va letta la pagina dei prezzi aggiornata.
**Non è verificato** che la squadra abbia davvero 10 $ di crediti (informazione di Nikola, non controllata).

## Memoria necessaria (stime da fonti generiche, non verificate)
LoRA a 16 bit su un modello da 8B: circa 17–22 GB (stretto su una A10G da 24 GB, comodo su A100). QLoRA a 4 bit: circa 6–17 GB. La memoria dipende da lunghezza delle sequenze, batch, rango e gradient checkpointing: va misurata alla prima run.

## Opzione 1 — Hugging Face Jobs
- Pesi in formato HF `swiss-ai/Apertus-v1.5-8B` (da scaricare dal Hub; l'accesso e le condizioni vanno controllati); poi **conversione dell'adattatore/del modello fuso verso MLX** per servirlo sul Mac (percorso da verificare).
- Stima di una run: dati di dev ~96 esempi (fino a qualche centinaio se si rigenerano istanze con `--n-dev`), ~1.500 token ciascuno ⇒ ~0,15 M token per epoca; con 3 epoche circa 0,5 M token. Se un A10G elabora qualche migliaio di token al secondo (**ipotesi**), una run dura minuti, cioè **meno di 1 $**; con 10 $ si avrebbero circa dieci run o poche ore di GPU.
- Vantaggi: veloce, il Mac resta libero. Svantaggi: costo, conversione dei formati, token HF (solo da variabile d'ambiente).

## Opzione 2 — addestramento locale con MLX (`mlx_lm.lora`)
- Nessun costo e nessuna conversione (i pesi sono già in formato MLX; `mlx_lm.fuse` produce il modello da servire). Rischi: memoria del Mac da 32 GB (8B bf16 occupa circa 16 GB e l'addestramento ne aggiunge altri), tempi lunghi (inferenza misurata ~7 token/s), e il Mac non può servire il modello mentre si addestra.
- Non provato.

## Protocollo proposto (da confermare)
- **Dati:** solo split `dev` (mai val/test né schemi del test). Ogni esempio = conversazione con il prompt di sistema SQL, schema + domanda, chiamata `run_sql` con la query gold e risposta finale; formato identico a quello della valutazione. La risposta finale testuale va generata da un modello a regole (non da un LLM) o scelta a mano.
- **Parametri addestrabili:** LoRA con rango scelto in modo che i parametri addestrabili siano **≤ quelli modificati da WSP** (`docs/analysis_plan.md` §7), più un LoRA «convenzionale» di riferimento (es. rango 16 su proiezioni di attenzione).
- **Iperparametri proposti (non provati):** learning rate dell'ordine di 1e-4–2e-4, 2–3 epoche, ottimizzatore AdamW; stessa quantità di valutazioni su val consentite a WSP e LoRA, e contate.
- **Registro:** ore GPU o di Mac, costo in dollari, parametri addestrabili, configurazione completa, sha256 del checkpoint, dichiarazione in `models.yaml` **prima** di usarlo in una run.
- **Costo di adattamento da riportare:** ore di calcolo, costo, token del modello di sviluppo usati (per WSP).

## Da decidere
1. Opzione 1 o 2 (o entrambe). 2. Rango/i e dati (solo dev attuale, o più istanze generate). 3. Se il budget da 10 $ basta (leggere il saldo reale).
