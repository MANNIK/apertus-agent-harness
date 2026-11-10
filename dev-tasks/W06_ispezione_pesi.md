# W06 — Strumenti di ispezione e modifica dei pesi
Stato: **parziale: strumenti indipendenti dal metodo fatti e testati su tensori sintetici; PyTorch e script per Hugging Face Jobs non fatti** · Priorità: alta · Serve: ambiente PyTorch separato; GPU solo per i pesi veri

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
Stato: **parziale (10 nov 2026).**
**Fatto** — `src/agentbench/wsp.py` (extra `wsp`: numpy, ml_dtypes; safetensors solo per il test di compatibilità), indipendente dal metodo WSP:
- impronte sha256 (tensore e checkpoint), ispezione per tensore (forma, tipo, statistiche, norme, rango stabile) con sintesi piccole da dare al modello di sviluppo;
- `apply_delta` / `revert`: modifica in-place con **annullamento bit a bit** (conserva i valori originali; in bf16 «aggiungi e sottrai Δ» NON è esatto, dimostrato da un test), conteggio dei parametri **davvero cambiati dopo l'arrotondamento** (numero e %), norma di Δ, hash prima/dopo, registro JSONL append-only che include le modifiche scartate;
- lettore/scrittore safetensors minimale con bf16 e lettura per nome via mmap, compatibile in entrambe le direzioni con la libreria ufficiale (verificato).
**Verificato:** `tests/test_wsp.py` (15 test, solo tensori sintetici piccoli, float32/float16/bfloat16). Licenze lette dai `METADATA` installati: numpy BSD-3-Clause (e altre permissive), ml_dtypes Apache-2.0, safetensors Apache-2.0.
**Non fatto / non verificato:** (1) mai eseguito su pesi veri (regola: non toccare i `.safetensors` locali senza copia; non aperti da Claude); (2) ambiente PyTorch/transformers separato e relative licenze: non creato; (3) script per Hugging Face Jobs (token solo da variabile d'ambiente, costi e durata registrati): non scritto, dipende da W07/W08; (4) prestazioni su tensori reali da miliardi di parametri (SVD/potenza su matrici 4096×14336): non misurate; (5) `uv.lock` non ancora aggiornato con l'extra `wsp` (da fare con `uv sync --extra wsp` quando il Mac non è occupato dal baseline).

