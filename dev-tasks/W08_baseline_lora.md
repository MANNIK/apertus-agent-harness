# W08 — Baseline LoRA con protocollo comparabile
Stato: **protocollo e budget proposti; nessun LoRA addestrato (decisione della squadra)** · Priorità: alta · Serve: W02, W04

## Obiettivo
Ottenere un LoRA addestrato in condizioni paragonabili a WSP (dati disponibili, budget, costo) per confrontare miglioramento e costo.

## Contesto
Il confronto è sensato solo se dati, budget di calcolo e numero di parametri addestrabili sono dichiarati e confrontabili. I dati di addestramento non devono contenere schemi del test.

## Passi
0. **Stima del budget (aggiunta il 10 nov 2026):** prima di fissare il protocollo, stima ore GPU e costo di LoRA su 8B con i crediti HF disponibili (10 $ secondo le informazioni
   della squadra: **non verificato** che bastino per LoRA + WSP). Se non bastano, dillo a Nikola con le alternative invece di ridurre in silenzio il protocollo.
1. Definisci con Nikola dati, rango, iperparametri, budget GPU e durata; scrivili in W04. Il numero di parametri addestrabili deve essere confrontabile con quello di WSP (vedi W04, punto 8).
2. Addestra su dev (o su dati separati dichiarati); registra ore GPU, costo e parametri addestrati.
3. Unisci/converti il checkpoint, calcola l'hash e dichiaralo in `models.yaml`.
4. Verifica la licenza di `peft` e delle altre dipendenze.

## Criteri di accettazione
- Checkpoint LoRA con hash, configurazione completa e costo di adattamento misurato.

## Da non fare
- Non addestrare sul test né su schemi del test. Non stampare il token HF.

## Esito
Stato: **protocollo e stima del budget proposti (10 nov 2026); nessun LoRA addestrato.**
- `docs/lora_budget.md`: prezzi ufficiali di Hugging Face Jobs letti da risultato di ricerca (a10g-small 1,00 $/h con 24 GB, a100-large 2,50 $/h con 80 GB; cifre di terze parti molto più alte non coincidono con la documentazione), stime di memoria per LoRA su 8B, due opzioni (Hugging Face Jobs oppure `mlx_lm.lora` sul Mac), protocollo proposto (solo dev, parametri ≤ WSP, registro del costo) e decisioni da prendere.
- **Non verificato:** i 10 $ di crediti (informazione di Nikola, saldo non controllato); tempi e costi per run sono **stime**, non misure; il percorso di conversione HF↔MLX non è provato; la pagina dei prezzi non è stata riletta direttamente.
- **Blocca ancora:** la scelta dell'opzione, del rango e dei dati; W04 (parità di budget) e la decisione su WSP.

