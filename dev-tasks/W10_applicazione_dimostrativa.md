# W10 — Applicazione dimostrativa di data analysis self-hosted
Stato: pronto (da definire) · Priorità: media-alta · Serve: W03 (tool), un checkpoint servibile

## Obiettivo
Dimostrare che Apertus (modificato) svolge il compito centrale in un'applicazione concreta (regola 1), girando in locale.

## Contesto
Un semplice benchmark potrebbe non bastare per il requisito del core AI task. L'app deve usare solo Apertus e componenti open-weights/deterministici (DuckDB), senza API proprietarie a runtime.

## Passi
1. Definisci con Nikola interfaccia e workflow (es. CLI o piccola web app locale): domanda in linguaggio naturale → schema → SQL generato da Apertus → esecuzione DuckDB → risposta.
2. Dataset di esempio con licenza verificata (W02).
3. Gira senza rete verso l'esterno (solo l'endpoint del modello locale); prova con `--network none` per tutto tranne il modello.
4. Elenca nel rapporto cosa fa Apertus e cosa fa il codice deterministico.

## Criteri di accettazione
- Demo riproducibile in locale; nessuna chiamata a servizi AI proprietari (verificato dal controllo di conformità).

## Da non fare
- Nessuna API AI chiusa a runtime. Non presentare come risultato scientifico ciò che è una demo.

## Esito
(da compilare)
