# T07 — Docker sul Mac e verifica "senza rete"
Stato: pronto (se Docker è installato) · Priorità: media

## Obiettivo
Il `Dockerfile` non è mai stato costruito. Provarlo, correggerlo, e dimostrare che la demo gira **senza rete**.

## Passi
1. Verifica che Docker sia installato e acceso (`docker --version`, `docker info`). Se manca, scrivi "bloccato: Docker assente" nell'Esito e fermati.
2. `make docker-build`, poi `make docker-demo` (usa `--network none`): deve stampare 33/33 e nessun errore di conformità.
3. Correggi ciò che non funziona (file mancanti nel `COPY`, `.dockerignore`, versione di Python). Tieni l'immagine minimale e **senza modelli**.
4. Aggiungi al README i comandi verificati. Se hai bloccato versioni (immagine base per digest, pacchetti con versione esatta), scrivi quali.
5. Facoltativo: un controllo `make airgap-check` che esegue la demo con `--network none` e fallisce se il comando tenta connessioni.

## Criteri di accettazione
- Output reale di build e demo incollato nell'Esito (le ultime righe).

## Esito
(da compilare)
