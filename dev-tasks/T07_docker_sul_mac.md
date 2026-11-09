# T07 — Docker sul Mac e verifica "senza rete"
Stato: fatto · Priorità: media

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
**Fatto:** Docker Desktop era installato ma spento: l'ho avviato (`open -a Docker`). Immagine costruita, demo eseguita con `--network none`, aggiunto `make airgap-check`. Il `Dockerfile` non ha richiesto correzioni.

**Verificato (output reale, 10 nov 2026, Docker 29.5.3, Mac arm64):**
- `make docker-build` → immagine `apertus-agent-harness:latest` (50 MB, arm64, Python 3.12.16). Ultime righe: `naming to docker.io/library/apertus-agent-harness:latest done`.
- `make docker-demo` (`docker run --rm --network none …`) → `62/62 esecuzioni passate`, poi `✓ [regola 6] [demo] modello dichiarato: demo-oracle-synthetic`, `✓ [regola 3/5] nessuna libreria di rete importata oltre a httpx in client.py`, `0 errori, 1 avvisi` (l'avviso è l'architettura target non dichiarata).
- Prova che la rete è davvero bloccata: `docker run --network none --entrypoint python … urllib.request.urlopen('http://example.com')` → `URLError: Temporary failure in name resolution`.
- `make airgap-check` → `✓ demo passata e connessioni in uscita bloccate (--network none)`, codice di uscita 0.
- Pacchetti installati nell'immagine (da `pip freeze`): httpx 0.28.1, httpcore 1.0.9, h11 0.16.0, anyio 4.16.0, idna 3.20, certifi 2026.10.23, PyYAML 6.0.3, typing_extensions 4.16.0.

**Non fatto / limiti:**
- **Nessuna versione è bloccata**: l'immagine base `python:3.12-slim` non è fissata per digest e i pacchetti non sono a versione esatta; sono quelli risolti al momento della build (elencati sopra). Per un rapporto riproducibile conviene fissarli (proposta, non fatta).
- La demo in container usa il server finto su `127.0.0.1` (la loopback funziona con `--network none`): prova l'assenza di rete esterna, non il funzionamento con un modello vero.
- Nessuna prova con un modello dentro/accanto al container.
