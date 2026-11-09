# Run sintetica di riferimento

Questa cartella NON contiene i risultati di un modello. È stata prodotta da `scripts/build_demo.py`
con un server finto che esegue i percorsi corretti dei 33 task.

Serve a verificare l'harness senza modello né rete: `make demo` rigioca queste risposte e deve dare 33/33.
Se non dà 33/33, è l'harness (o la suite di task) ad essere cambiato, non un modello.

Non citare mai questi numeri come prestazioni di Apertus.
