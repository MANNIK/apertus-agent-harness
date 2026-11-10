# Metodi WSP candidati (W07) — scheda per la scelta della squadra

Stato: **proposta del 10 nov 2026, nessun metodo scelto.** La scelta spetta alla squadra (domanda aperta n. 1). Nessuno di questi metodi è stato provato: tutto ciò che segue sugli effetti è **ipotesi**.
I riferimenti alla letteratura sono dalla mia memoria e **non sono stati verificati** (andrebbero controllati prima di citarli nel rapporto).

## Il rischio da evitare
Se WSP è «un fine-tuning con un altro nome», il confronto con LoRA non dice nulla di nuovo. Un metodo è WSP in senso utile solo se ha un **meccanismo dichiarabile in una frase**,
un **registro di ciò che è stato toccato e perché** (Δθ reversibile) e un **controllo** che distingue l'ipotesi dal caso. In tutti i casi sotto, il controllo è lo stesso esperimento con **tensori/direzioni scelti a caso** a parità di budget.

## Regole comuni (dal piano di analisi)
- Ogni modifica proposta è registrata (anche se scartata): tensori toccati, numero e % di parametri, norma/rango di Δθ, punteggi dev/val, motivazione. Δθ reversibile (applica Δθ e −Δθ → tensore identico), sha256 prima/dopo.
- Si itera solo su dev/val; il test si guarda alla fine. Il modello di sviluppo (Claude Sonnet 5.5) non vede mai item, schemi o risultati del test.
- Il confronto con LoRA è a parità di parametri modificati/addestrabili (`docs/analysis_plan.md` §7); risultato centrale: curva accuratezza vs % di parametri vs regressioni (set di regressione `tasks/regression/`).

## Metodo A — Localizzazione guidata + modifica sparsa
- **Meccanismo (una frase):** individuare con attribuzione (gradiente/attivazioni sui dev) i pochi moduli (es. proiezioni di attenzione o MLP in alcuni layer) che contano per lo schema-linking e la SQL, e ottimizzare Δθ **solo lì**.
- **Cosa tocca:** poche matrici (per esempio da 1 a 10 tensori su centinaia): poche decine di milioni di parametri al massimo, di solito molti meno.
- **Costo atteso:** servono gradienti, quindi GPU (Hugging Face Jobs, vedi `docs/lora_budget.md`) o la memoria del Mac; poche run brevi. Strumenti: ispezione per layer (W06).
- **Controllo:** stessa ottimizzazione su moduli scelti a caso (stesso numero di parametri). Se i moduli «localizzati» non battono i casuali, l'ipotesi di localizzazione è falsa e va scritto.
- **Rischi:** è di fatto *sparse fine-tuning*; sovra-adattamento a soli 96 task di dev; la localizzazione su pochi dati può essere instabile.
- **Perché è interessante:** dà una storia interpretabile («quali moduli») e un registro chiaro per la giuria.

## Metodo B — Modifica in forma chiusa di rango basso (senza gradienti)
- **Meccanismo (una frase):** calcolare una **direzione** nelle attivazioni che separa i comportamenti corretti da quelli sbagliati (es. mappare «Quartier» ↔ «quartiere», trattare `NA` come mancante) e incorporarla nei pesi con un aggiornamento di rango 1–r di una proiezione scelta (`W' = W + α·u·vᵀ`), come uno *steering* «cotto» nei pesi.
- **Cosa tocca:** una o poche matrici, rango molto basso: **pochissimi parametri** (l'ordine di grandezza di un rango 1 è la somma delle due dimensioni, non il prodotto).
- **Costo atteso:** solo passaggi in avanti per raccogliere le attivazioni; nessun addestramento. È il più economico.
- **Controllo:** direzioni casuali della stessa norma; ablazione del segno (α negativo).
- **Rischi:** l'effetto può essere nullo o minimo su un compito complesso come la SQL; la ricerca di α e del layer è una forma di ottimizzazione su dev (da registrare). Richiede di agganciare le attivazioni (più semplice in PyTorch che in MLX).
- **Perché è interessante:** se funziona, è il caso più netto di «programmare» i pesi, ed è verificabile e reversibile.

## Metodo C — Potatura di un vettore di compito (task vector)
- **Meccanismo (una frase):** ottenere Δθ_pieno da un breve addestramento su dev e **tenerne solo una piccola frazione** (le componenti più grandi, o un troncamento a rango per tensore) misurando quanta parte basta a mantenere il guadagno.
- **Cosa tocca:** parametrico: si varia la percentuale (es. 0,1% / 1% / 10% / 100%) e si ottiene la curva accuratezza-contro-parametri.
- **Costo atteso:** un addestramento (come un LoRA) più valutazioni su val; poi la potatura è gratuita.
- **Controllo:** potatura casuale alla stessa percentuale.
- **Rischi:** dipende da un fine-tuning: può ridursi a «LoRA/fine-tuning più compresso»; il ruolo del modello di sviluppo si riduce a scegliere la politica di potatura.
- **Perché è interessante:** produce direttamente la curva centrale del piano di analisi e un numero onesto («quanto poco basta»).

## Confronto rapido
| | Gradienti | GPU | Parametri toccati | Interpretabilità | Rischio che sia «solo fine-tuning» |
|---|---|---|---|---|---|
| A | sì | sì (o Mac, lento) | pochi | media-alta | medio |
| B | no | no (forward) | pochissimi | alta | basso |
| C | sì (un addestramento) | sì | variabile (curva) | bassa | alto |

## Mia raccomandazione (non vincolante)
Un **pilota rapido con B** (costo minimo, una giornata) e **A con controllo a tensori casuali** come metodo principale; **C** come rete di sicurezza per avere comunque la curva e un risultato presentabile.
Prima di decidere: il **cancello di fattibilità** di W05 (baseline su dev/val) dice se c'è margine, e il tempo di esecuzione (circa 7 token/s misurati sul Mac) limita il numero di valutazioni su dev/val: ogni tentativo WSP costa circa 20–30 secondi per task per ogni valutazione.

## Prima di iniziare servono
1. La scelta del metodo e i criteri di accettazione in `docs/analysis_plan.md` §6 (Decisions log), **prima della prima run**.
2. Un ambiente PyTorch separato con licenze verificate (W06: `torch`, `transformers`, `safetensors`) e i pesi in formato Hugging Face per le modifiche (i pesi locali sono in formato MLX: la conversione e il percorso inverso vanno decisi).
3. La conferma che si possono usare **pesi propri** all'evento (domanda agli organizzatori, ancora aperta).
