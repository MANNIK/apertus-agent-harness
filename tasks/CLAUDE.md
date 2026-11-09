# tasks — la suite di prova (62 task, 11 gruppi)

Un file YAML per gruppo (i gruppi `injection` e `arguments` hanno due file): single_call, arguments, multi_step, error_recovery, abstention, injection, judge, multilingual, parallel, long_chain, ambiguity. Formato di un task: vedi `src/agentbench/tasks.py` e il README ("Scrivere un task").

Regole per scrivere o cambiare task:
- Deterministici: stato iniziale in `setup`, nessun valore casuale o dipendente dalla data.
- Controlli sullo **stato** (file, email, ticket) quando possibile, non solo sul testo; evita euristiche fragili.
- Un task non deve essere impossibile: aggiungi il percorso corretto in `tests/test_tasks_solvable.py` (altrimenti il test fallisce).
- Un task di injection deve *esercitare* l'attacco: se il modello non legge mai il documento avvelenato, il risultato è "non esercitato", non "resistito" (vedi compito T03).
- Nessun dato reale o personale nei prompt e nei file finti; indirizzi solo di dominio `.example`.
- Cambiare un task cambia il digest della suite: le run precedenti non sono più confrontabili. Dillo nel messaggio finale.
- Gli id sono stabili (`categoria_descrizione`): non rinominarli senza motivo, appaiono nei report e nei confronti.
