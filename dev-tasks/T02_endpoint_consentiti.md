# T02 — Dichiarare gli endpoint consentiti nella conformità
Stato: fatto · Priorità: alta

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
**Fatto:**
- `models.yaml`: `deployment.allowed_endpoint_hosts: [gateway.keera.ch]` con commento; aggiunte le voci `apertus-v1-5-8b` e `apertus-v1-5-70b` (`stages: [development, evaluation]`, `open_weights: true`).
- `compliance.py`: nuova `is_allowed_host` (nome host esatto, senza maiuscole); un host in elenco dà ✓, gli altri host non locali restano avviso.
- Caso `-thinking`: le nuove voci non usano `match` (solo `id`, che è esatto), quindi `apertus-v1-5-8b-thinking` risulta "non dichiarato" (errore), come voluto finché non lo dichiariamo.
- 3 test nuovi in `tests/test_compliance.py`: host ammesso senza avviso; host sconosciuto e host ingannevoli (`gateway.keera.ch.evil.example`, `evil-gateway.keera.ch`, host diverso con il nome nel percorso) con avviso; modelli ospitati a corrispondenza esatta e `-thinking` non dichiarato.
- README (sezione conformità) aggiornato.

**Verificato:**
- `.venv/bin/python -m pytest -q` → 101 passati (98 + 3).
- `make compliance` → 0 errori, 1 avviso (architettura target non dichiarata, voluto).
- `agentbench compliance reference_runs/demo-oracle` → 0 errori.

**Non verificato / da sapere:**
- Licenza del 70B: "da verificare" (non ho controllato la scheda su Hugging Face, senza accesso alla rete in questa sessione). Nella voce 8B ho riusato Apache-2.0 dalla voce MLX esistente, anch'essa non ricontrollata sulla scheda.
- Versione esatta servita dal gateway: da verificare (si saprà solo con T12, dal 27 nov).
- Non ho scelto `deployment.target`: resta a Nikola.
