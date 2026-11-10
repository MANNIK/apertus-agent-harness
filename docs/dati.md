# Dati e licenze (compito W02)

Aggiornato il **10 nov 2026**. Stato: **licenze verificate solo in parte; nessun dataset Text-to-SQL costruito; nessuno split creato.**
Legenda: **verificato** = letto sulla fonte ufficiale; **parziale** = riportato da un riassunto di ricerca o da una pagina secondaria, non letto in originale; **non verificato** = non si è riusciti a leggerlo.
Regola del progetto: nessun dato entra nel repository o in un addestramento prima del controllo di licenza.

## 1. Licenze
| Fonte | Licenza trovata | Stato | Come / dove | Uso previsto |
| --- | --- | --- | --- | --- |
| **Swissvotes** (Univ. Berna / Année Politique Suisse) | **CC BY 4.0** per dataset e codebook | **verificato** | pagina `https://swissvotes.ch/page/dataset`: «Der Swissvotes-Datensatz und das Codebuch sind unter der Lizenz "Creative Commons Attribution 4.0 International" (CC BY 4.0) verfügbar.» (10 nov 2026). Il testo di citazione raccomandato sta nei documenti scaricati, non sulla pagina: **non letto**. Una fonte secondaria (repository dell'Università di Berna) indica il codebook come CC0: discrepanza da chiarire, non blocca l'uso del dataset | **candidato principale** |
| **DuckDB** | MIT | **verificato sul pacchetto** (10 nov 2026) | `duckdb 2.0.0` installato: `METADATA` con classifier «License :: OSI Approved :: MIT License» e file `licenses/LICENSE` («Copyright 2018-2026 Stichting DuckDB Foundation», testo MIT). Il FAQ `duckdb.org/faq` conferma MIT solo via riassunto di ricerca | motore SQL locale (extra `sql`) |
| **BIRD** (Text-to-SQL) | **CC BY-SA 4.0** (dati) | **verificato sulle fonti ufficiali, con riserve** | sito `bird-bench.github.io`: «Due to large volume of requests, we now modify the license of our data to CC BY-SA 4.0» (27 apr 2024); README di `DAMO-ConvAI/bird`: stessa dicitura. Il `LICENSE` alla radice del repository è MIT e copre il software, non è detto i dati. Il **paper originale (2023)** secondo un riassunto di ricerca indicava CC BY-NC 4.0: **non verificato** (il PDF non era leggibile dallo strumento). 95 database, 33,4 GB in totale; dimensione del solo dev set **non trovata** | **solo valutazione, set secondario, in attesa di decisione** (vedi 3) |
| **Spider** (Yale) | CC BY-SA 4.0 | **parziale** | scheda Hugging Face `xlangai/spider` e script di caricamento, via ricerca; repository `taoyds/spider` non letto | non pianificato |
| **opendata.swiss / BFS** | **dipende dal singolo dataset** (categorie di «terms of use»: uso libero, con obbligo di citare la fonte, con permesso per uso commerciale, ecc.) | **non verificato** | la pagina `opendata.swiss/en/terms-of-use` e le pagine dei dataset rifiutano le richieste automatiche (**HTTP 403**). Le categorie qui sopra vengono da un riassunto di ricerca, e le etichette dei dataset BFS da pagine di un ambiente di prova: fonti deboli | **nessun uso finché una persona non legge la pagina del dataset nel browser** (vedi 4) |
| **OpenParlData** | sito CC BY 4.0 e software MIT (riassunto di ricerca); **licenza dei dati non trovata** | **non verificato** | `openparldata.ch` è una pagina JavaScript senza testo leggibile dallo strumento; il repository GitHub è stato spostato su GitLab (`gitlab.com/opendata.ch/openparldatach`, **non letto**) | nessun uso finché non è chiarita |

Dipendenze Python: `duckdb` verificata (vedi sopra). Ancora da verificare in W06/W08: `peft`, `transformers`, `torch` (e le loro dipendenze).

## 2. Swissvotes: cosa c'è davvero (verificato scaricando il file il 10 nov 2026)
- `https://swissvotes.ch/page/dataset/swissvotes_dataset.csv`: **2.736.956 byte**, sha256 `52a2d219521d5e03768084f1aff5ee20ab624ce9d3f8118e0ba3fa1290c3066e`, UTF-8 con BOM, separatore `;`, fine riga CRLF.
- **719 righe (votazioni) × 874 colonne**; circa il **54% delle celle è vuoto**. Una sola tabella larga, nessun join.
- Nomi di colonna in **tedesco abbreviato** (`anr`, `datum`, `rechtsform`, `zh-japroz`…), con alcune varianti `_d`/`_f`/`_e` per i titoli (DE/FR/EN) e colonne `-de`/`-fr` per link. Le date sono testo `gg.mm.aaaa`. I codici numerici (es. `rechtsform`) si capiscono solo col **codebook** (PDF in tedesco, non letto).
- Struttura: **210 colonne con prefisso cantonale** (8 per cantone: `berecht`, `stimmen`, `bet`, `gultig`, `ja`, `nein`, `japroz`, `annahme`) e **441 colonne `pdev-…`** (partito + cantone nel nome): da questi gruppi si possono derivare tabelle in formato lungo (votazione × cantone) da unire a una tabella dei cantoni.
  **I significati (aventi diritto, partecipazione, voti validi, % sì, indicazioni di voto dei partiti…) sono dedotti da me dai nomi, non verificati col codebook.**
- **L'ultima riga è una votazione futura (28.02.2027)**: le domande devono escluderla o trattarla come dato incompleto.
- Download con `scripts/fetch_swissvotes.sh` (verifica lo sha256 e fallisce se il file è stato aggiornato); il file va in `data/raw/` (ignorato da git, 2,7 MB). **Non ho committato il file**: decidere se tenerne una copia versionata (CC BY 4.0 lo consente con attribuzione) per la riproducibilità.

## 3. Problema aperto: lo split per schema con una sola fonte
Il piano (`docs/analysis_plan.md`) vuole schemi del test **mai visti** in dev/val e negli addestramenti. Da Swissvotes si possono derivare più schemi (votazioni, risultati per cantone, indicazioni dei partiti), ma restano **lo stesso dominio e gli stessi valori**: è una generalizzazione debole e non è equivalente a schemi di altri domini.
Opzioni (decisione della squadra):
1. **Aggiungere 1–2 fonti di altri domini** (es. statistiche BFS, dati comunali) dopo la lettura umana della licenza; il test usa le fonti non viste in addestramento. È la scelta più solida.
2. Usare solo schemi derivati da Swissvotes e **dichiarare** il limite nel rapporto (generalizzazione intra-dominio).
3. BIRD come set di generalizzazione esterno, **solo valutazione**, con avviso di possibile contaminazione (non sappiamo se è nei dati di Apertus) e senza addestrarci sopra. Motivo: la licenza è share-alike (CC BY-SA) e **non è stabilito** se si estenda ai pesi di un modello addestrato sui dati; finché non è chiarito non lo usiamo per LoRA/WSP. Non è una consulenza legale.

## 4. Cosa deve fare una persona (la squadra) a mano
- Aprire **nel browser** la pagina di ogni dataset opendata.swiss/BFS candidato e copiare qui l'etichetta dei termini d'uso (e la pagina `terms-of-use` per il significato delle categorie, in particolare per uso di ricerca/AI). Un dataset senza uso libero e senza ridistribuzione consentita non entra.
- Leggere `https://gitlab.com/opendata.ch/openparldatach` (file LICENSE e termini dei dati) solo se si vuole usare OpenParlData.
- Aprire il codebook di Swissvotes (nel PDF) per la citazione raccomandata e il significato dei codici.

## 5. Progetto del dataset (da fare dopo le licenze)
Caratteristiche decise in `dev-tasks/W02_dati_e_licenze.md` (ipotesi da confermare sui dati reali): domande in DE/FR/IT/EN con lingua registrata per task; schema-linking tra lingue diverse; «trappole» di formato svizzere (date `gg.mm.aaaa`, numeri con apostrofo, CHF, valori mancanti, caratteri accentati) etichettate; domande su dati che i modelli ricordano male (es. esiti di votazioni) con risposta dall'esecuzione; query gold eseguibili e verificate; split per schema con id e sha256; nessun dato personale.
Dimensione obiettivo: 200–500 task indipendenti in totale; la parte di **test sarà più piccola** (vedi le tabelle di potenza in `docs/analysis_plan.md`). Il processo di scrittura delle query gold (a mano, con revisione di un secondo membro della squadra; eventuale aiuto di Claude dichiarato come strumento di sviluppo) va fissato prima di iniziare.

## 6. Non ancora fatto
Split dev/val/test e relative impronte; scelta delle fonti oltre Swissvotes; verifica delle licenze delle dipendenze Python; stima dello spazio per BIRD (dimensione del dev set non trovata).
