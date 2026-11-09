# T02 — Dichiarare gli endpoint consentiti nella conformità
Stato: pronto · Priorità: alta

## Obiettivo
`agentbench compliance` avvisa oggi per ogni endpoint non locale. L'endpoint ufficiale CSCS/Keera (`https://gateway.keera.ch/api/v1`) è ammesso (cloud sovrano svizzero, regola 5): serve poterlo dichiarare in `models.yaml` e far sparire l'avviso solo per quello.

## Passi
1. In `models.yaml` aggiungi, sotto `deployment`, un elenco `allowed_endpoint_hosts` (es. `["gateway.keera.ch"]`) con un commento che spiega perché.
2. In `src/agentbench/compliance.py` fai in modo che `_run_findings` tratti come "ammesso" un host in elenco (messaggio ✓ con nome host), e come avviso gli altri host non locali. Gli host nell'elenco valgono solo per corrispondenza esatta del nome host (non per sottostringa).
3. Aggiungi in `models.yaml` le voci dei modelli ospitati: `apertus-v1-5-8b` (pesi ufficiali `swiss-ai/Apertus-v1.5-8B`) e `apertus-v1-5-70b`, `stages: [development, evaluation]`, `open_weights: true`. Per la licenza del 70B scrivi "da verificare" se non la trovi con certezza (controlla la scheda su Hugging Face).
4. Attenzione al campo `match`: `apertus-v1-5-8b` è sottostringa di `apertus-v1-5-8b-thinking`. Gestisci i due casi (voci separate o corrispondenza esatta) con un test.
5. Test in `tests/test_compliance.py`: host ammesso → nessun avviso; host sconosciuto → avviso; sottostringa ingannevole (`gateway.keera.ch.evil.example`) → avviso.
6. Aggiorna README (sezione conformità) e `docs/analysis_plan.md` solo se serve.

## Criteri di accettazione
- Test nuovi e vecchi passano. `make compliance` su `reference_runs/demo-oracle` resta senza errori.
- L'avviso sulla regola 5 "architettura target non dichiarata" resta finché Nikola non sceglie l'architettura: non scegliere tu al suo posto.

## Da non fare
- Non mettere chiavi o credenziali in `models.yaml`.

## Esito
(da compilare)
