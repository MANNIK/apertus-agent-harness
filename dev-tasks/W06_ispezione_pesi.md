# W06 — Strumenti di ispezione e modifica dei pesi
Stato: pronto (ricerca) · Priorità: alta · Serve: ambiente PyTorch separato; GPU solo per i pesi veri

## Obiettivo
Costruire gli strumenti con cui il modello di sviluppo analizza Apertus 8B e applica modifiche **controllate e reversibili**.

## Contesto
Apertus 8B ha miliardi di parametri: non si possono dare tutti i tensori a un LLM. Servono strumenti di ispezione selettiva: statistiche di pesi e attivazioni, analisi per layer, decomposizioni a basso rango, identificazione di componenti rilevanti, checkpoint intermedi. HF Jobs è ammesso solo per lo sviluppo (regola 2).

## Passi
1. Ambiente separato (`external/wsp/` o extra) con versioni bloccate; licenze di PyTorch/transformers/safetensors verificate.
2. Funzioni di ispezione per layer/tensore (statistiche, norme, rango effettivo, attivazioni su un piccolo campione di dev) che producono sintesi **piccole** da dare al modello di sviluppo.
3. Applicazione di Δθ **reversibile** (applica Δθ e −Δθ → tensore identico), conteggio esatto dei parametri modificati, hash sha256 prima/dopo, registro JSON di ogni modifica.
4. Test su tensori sintetici piccoli (mai sui pesi veri nei test).
5. Script per Hugging Face Jobs (token da variabile d'ambiente, mai su file); registra costi e durata.

## Criteri di accettazione
- Test verdi; una modifica è sempre annullabile; il registro dice quali tensori e quanti parametri sono toccati.

## Da non fare
- Nessun token in file/log. Non modificare i pesi in `../models/` sul posto: lavora su copie.

## Esito
(da compilare)
