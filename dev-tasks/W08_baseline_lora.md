# W08 — Baseline LoRA con protocollo comparabile
Stato: bloccato dal protocollo (domanda aperta n. 4) · Priorità: alta · Serve: W02, W04

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
(da compilare)
