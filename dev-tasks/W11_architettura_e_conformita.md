# W11 — Architettura di deployment e conformità alle regole
Stato: **parziale: opzioni documentate, architettura da scegliere (Nikola)** · Priorità: alta · Serve: decisione di Nikola

## Obiettivo
Scegliere e dichiarare l'architettura (regola 5) e chiudere i controlli di conformità sui modelli (regole 3, 4, 6).

## Contesto
`deployment.target` in `models.yaml` è vuoto: l'avviso resta finché Nikola non sceglie tra on-premise, air-gapped e cloud sovrano svizzero. Docker e `make airgap-check` (T07) esistono. Modelli da dichiarare: originale, WSP, LoRA (tecnica, versione/hash, ruolo, fase) e Claude Sonnet 5.5 (solo sviluppo).

## Passi
1. Chiedi a Nikola l'architettura; imposta `deployment.target` solo dopo la sua scelta. Elemento per la decisione (10 nov 2026): **air-gapped/on-premise su un Mac** è l'opzione più
   vicina a ciò che esiste già (MLX locale, Docker senza rete, `airgap-check`); i progetti premiati dimostravano la deployabilità sovrana con prove (rete interna, sonda di uscita). È un suggerimento, non una scelta.
2. Dichiara i checkpoint WSP/LoRA e ogni strumento/modello di sviluppo realmente usato; non dichiarare quelli non usati.
3. Aggiorna Dockerfile/airgap-check per l'applicazione (W10) senza includere pesi nell'immagine; blocca versioni e digest dell'immagine base.
4. `make compliance` senza errori né avvisi non spiegati.

## Criteri di accettazione
- `make compliance` pulito; architettura dichiarata; tabella modelli generata dal comando.

## Da non fare
- Non scegliere l'architettura al posto di Nikola. Non inserire chiavi o pesi nell'immagine.

## Esito
Stato: **parziale (10 nov 2026): documento delle opzioni scritto; architettura NON scelta; Dockerfile non esteso.**
- `docs/deployment_options.md`: fatti verificati, tre opzioni a confronto (on-premise, air-gapped, cloud sovrano svizzero), conseguenze per i pesi modificati (il gateway ufficiale serve probabilmente solo i pesi originali: ipotesi da confermare), considerazione non vincolante a favore dell'air-gapped su Mac.
- `models.yaml`: ruoli e versioni aggiornati al nuovo progetto (Apertus 8B sotto test, Claude Sonnet 5.5 come strumento di sviluppo, oracolo della demo, gateway). `deployment.target` resta vuoto; `make compliance`: 0 errori, 1 avviso (architettura).
- **Non fatto:** scelta dell'architettura (spetta a Nikola); Dockerfile con DuckDB, dati e task; `make airgap-check` (richiede Docker acceso); dichiarazione dei checkpoint WSP/LoRA (non esistono).

