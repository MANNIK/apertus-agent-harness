# W07 — Ciclo Weight-Space Programming
Stato: bloccato dal metodo (domanda aperta n. 1) · Priorità: alta · Serve: W04, W05, W06

## Obiettivo
Far proporre al modello di sviluppo modifiche ai pesi, valutarle **solo su dev/val** e conservare solo quelle che superano criteri fissati prima.

## Contesto
Il documento descrive il ciclo: analisi errori → statistiche/sottospazi → ipotesi su componenti → trasformazioni PyTorch → valutazione → conservare se valida. Quali layer, come individuare i parametri e quali trasformazioni usare è **ancora da decidere**. Modello di sviluppo dichiarato: Claude Sonnet 5.5 (non entra nel runtime).

## Passi
0. **Scheda dei metodi candidati (aggiunta il 10 nov 2026):** prima di implementare, prepara una scheda di 2–3 metodi WSP, ciascuno con meccanismo, quali tensori/parametri tocca,
   costo atteso, rischio e cosa lo distingue da un fine-tuning. Il rischio principale è che WSP sembri "un fine-tuning con un altro nome": il meccanismo deve essere dichiarabile in una frase.
   Esempio da valutare (non da scegliere tu): localizzare con attribuzione/attivazioni i tensori rilevanti per schema-linking/SQL e applicare una modifica sparsa, con Δθ registrato.
   La scelta spetta alla squadra.
1. Concorda con Nikola il metodo concreto e i criteri di accettazione; scrivili in W04 prima di iniziare.
2. Implementa il ciclo con registro **completo**: ogni modifica proposta, accettata o scartata, con motivazione, parametri toccati e punteggi dev/val.
3. Congela il checkpoint finale (hash) e dichiaralo in `models.yaml` (base, tecnica, versione, ruolo, fase).
4. Esegui i controlli di sanità previsti nel piano.

## Criteri di accettazione
- Un checkpoint WSP con hash, registro delle modifiche e numero/% di parametri modificati; nessuna scelta presa guardando il test.

## Da non fare
- Non guardare il test set. Non scegliere tu la tecnica al posto della squadra. Non scrivere che migliora senza intervalli e test.

## Esito
(da compilare)
