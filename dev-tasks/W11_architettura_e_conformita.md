# W11 — Architettura di deployment e conformità alle regole
Stato: pronto (decisione di Nikola) · Priorità: alta · Serve: decisione di Nikola

## Obiettivo
Scegliere e dichiarare l'architettura (regola 5) e chiudere i controlli di conformità sui modelli (regole 3, 4, 6).

## Contesto
`deployment.target` in `models.yaml` è vuoto: l'avviso resta finché Nikola non sceglie tra on-premise, air-gapped e cloud sovrano svizzero. Docker e `make airgap-check` (T07) esistono. Modelli da dichiarare: originale, WSP, LoRA (tecnica, versione/hash, ruolo, fase) e Claude Sonnet 5.5 (solo sviluppo).

## Passi
1. Chiedi a Nikola l'architettura; imposta `deployment.target` solo dopo la sua scelta.
2. Dichiara i checkpoint WSP/LoRA e ogni strumento/modello di sviluppo realmente usato; non dichiarare quelli non usati.
3. Aggiorna Dockerfile/airgap-check per l'applicazione (W10) senza includere pesi nell'immagine; blocca versioni e digest dell'immagine base.
4. `make compliance` senza errori né avvisi non spiegati.

## Criteri di accettazione
- `make compliance` pulito; architettura dichiarata; tabella modelli generata dal comando.

## Da non fare
- Non scegliere l'architettura al posto di Nikola. Non inserire chiavi o pesi nell'immagine.

## Esito
(da compilare)
