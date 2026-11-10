# Dati e licenze (compito W02)

Aggiornato il **10 nov 2026**. Stato: **dataset Text-to-SQL `zurich-sql` v0.1 costruito (210 task su dati reali CC0, split per schema); licenze di opendata.swiss/OpenParlData ancora non verificate; le domande non sono riviste da madrelingua.**
Legenda: **verificato** = letto sulla fonte ufficiale; **parziale** = riportato da un riassunto di ricerca o da una pagina secondaria, non letto in originale; **non verificato** = non si è riusciti a leggerlo.
Regola del progetto: nessun dato entra nel repository o in un addestramento prima del controllo di licenza.

## 1. Licenze
| Fonte | Licenza trovata | Stato | Come / dove | Uso previsto |
| --- | --- | --- | --- | --- |
| **Swissvotes** (Univ. Berna / Année Politique Suisse) | **CC BY 4.0** per dataset e codebook | **verificato** | pagina `https://swissvotes.ch/page/dataset`: «Der Swissvotes-Datensatz und das Codebuch sind unter der Lizenz "Creative Commons Attribution 4.0 International" (CC BY 4.0) verfügbar.» (10 nov 2026). Il testo di citazione raccomandato sta nei documenti scaricati, non sulla pagina: **non letto**. Una fonte secondaria (repository dell'Università di Berna) indica il codebook come CC0: discrepanza da chiarire, non blocca l'uso del dataset | **candidato principale** |
| **DuckDB** | MIT | **verificato sul pacchetto** (10 nov 2026) | `duckdb 2.0.0` installato: `METADATA` con classifier «License :: OSI Approved :: MIT License» e file `licenses/LICENSE` («Copyright 2018-2026 Stichting DuckDB Foundation», testo MIT). Il FAQ `duckdb.org/faq` conferma MIT solo via riassunto di ricerca | motore SQL locale (extra `sql`) |
| **BIRD** (Text-to-SQL) | **CC BY-SA 4.0** (dati) | **verificato sulle fonti ufficiali, con riserve** | sito `bird-bench.github.io`: «Due to large volume of requests, we now modify the license of our data to CC BY-SA 4.0» (27 apr 2024); README di `DAMO-ConvAI/bird`: stessa dicitura. Il `LICENSE` alla radice del repository è MIT e copre il software, non è detto i dati. Il **paper originale (2023)** secondo un riassunto di ricerca indicava CC BY-NC 4.0: **non verificato** (il PDF non era leggibile dallo strumento). 95 database, 33,4 GB in totale; dimensione del solo dev set **non trovata** | **solo valutazione, set secondario, in attesa di decisione** (vedi 3) |
| **Spider** (Yale) | CC BY-SA 4.0 | **parziale** | scheda Hugging Face `xlangai/spider` e script di caricamento, via ricerca; repository `taoyds/spider` non letto | non pianificato |
| **Open Data Stadt Zürich** (`data.stadt-zuerich.ch`) | **CC0** (913 dataset su 942), CC BY (13), CC BY-SA (16) | **verificato** (metadati ufficiali + pagina del portale concordi), con una lacuna | Il 10 nov 2026 l'API CKAN del portale (`/api/3/action/package_search`, risposta 200) elenca **942 dataset**: `license_id` = `cc-zero` 913, `cc-by-sa` 16, `cc-by` 13; **629 con almeno un CSV** (615 CC0). La pagina `data.stadt-zuerich.ch/dataset` mostra gli stessi conteggi. Pagina «Open Government Data» della città: dati «kostenlos, maschinenlesbar und ohne Nutzungseinschränkungen»; homepage: «kostenlos und zur freien – auch kommerziellen – Weiterverwendung». **Lacuna:** le pagine legali (`Rechtliche Hinweise`, `Impressum`) rispondono 404, quindi il testo formale delle condizioni **non è stato letto**, e **non c'è nessuna dichiarazione su uso per IA/addestramento né su diritti di terzi**. Il «Reglement über offene Verwaltungsdaten» è citato ma non raggiunto | **fonte principale proposta**: solo dataset con `license_id = cc-zero`, controllato dataset per dataset |
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

## 2b. Open Data Stadt Zürich: perché è la fonte principale proposta
Decisione di Nikola (10 nov 2026): **dati reali, e altre fonti oltre a Swissvotes**. Il portale della Città di Zurigo (sede dell'hackathon) risolve il problema dello split per schema (§3): sono **molti domini e schemi realmente diversi**
(popolazione `bev_`, edilizia e affitti `bau_`, redditi `fd_`, politica `politik_`, aria/meteo `ugz_`, mobilità `prd_`/`vbz_`, servizi sociali `sd_`, prezzi `wir_`, emergenze `sid_`…), in formato CSV, con nomi di colonna in tedesco.
Tra i 615 dataset CC0 con CSV, circa 179 sono tabelle statistiche di dimensione gestibile (8 KB – 4 MB); i dati sono **aggregati statistici**.
Regole di selezione (da applicare, non ancora applicate): licenza `cc-zero` nel metadato del singolo dataset; CSV non «live» e non «Einzeldaten»; **nessun dato che contenga nomi di persone** (esclusi i dataset di candidati alle elezioni, i nomi dei neonati, ecc.); un dataset = uno schema, assegnato per intero a dev, val **o** test; hash sha256 e data di scaricamento registrati.
Proposta di una prima rosa (da confermare dopo aver ispezionato i file): `bev_bestand_jahr_quartier_od3240`, `bau_whg_mpe_mietpreis_raum_zizahl_gn_jahr_…`, `fd_median_einkommen_quartier_od1003`, `politik_abstimmungen_seit1933`, `ugz_luftschadstoffmessung_tageswerte`,
`ugz_meteodaten_tagesmittelwerte`, `prd_ssz_fz_motorisierungsgrad_jahr_quartier_…`, `sd_sod_sozialhilfequote_stadtquartier`, `wir_preise_zik_totalindex_monatswerte_…`, `vbz_fahrzeiten_ogd_2023`, `erz_sr_kennzahlen`, `sid_srz_od1027_feuerwehr_ausrueckzeit_…`.
**Scaricati il 10 nov 2026 i 15 dataset della §7** (tutti `cc-zero` riletti dall'API al momento del download, sha256 in `data/zurich/MANIFEST.json`).
I portali opendata.swiss e le sue API rispondono 403 ai programmi (non aggirato). Sul portale di Basilea (`data.bs.ch`, Opendatasoft) l'API risponde (364 dataset) ma **le licenze non sono state lette**: fonte eventuale futura.

## 3. Problema aperto: lo split per schema con una sola fonte (risolto in proposta da §2b)
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

## 7. Dataset `zurich-sql` v0.1 (costruito il 10 nov 2026)
- **Dati:** 15 CSV del portale della Città di Zurigo, tutti **CC0**, istantanea in `data/zurich/` (5,1 MB, committata: il portale li aggiorna ogni giorno e l'istantanea garantisce la riproducibilità; `scripts/fetch_zurich.py` rilegge la licenza dall'API e rifiuta tutto ciò che non è CC0). `MANIFEST.json`: fonte, licenza, sha256, data.
  Scelti: popolazione (quartieri, circondari, confessioni), edilizia e affitti, redditi, motorizzazione, aiuto sociale, rifiuti, votazioni, qualità dell'aria, meteo, pronto intervento (pompieri, soccorso), indice dei prezzi. Aggregati statistici: **nessun nome di persona**.
- **Task:** generati da `scripts/zurich_spec.py` (modelli di domanda in DE/FR/IT/EN con query gold) e `scripts/build_zurich_tasks.py`, che campiona i valori dai dati reali ed **esegue il gold**; scarta risultati vuoti, nulli, a zero, troppo grandi o con pareggio in testa. Generazione **deterministica** (stesso hash su rigenerazioni ripetute).
- **Split per schema** (un dataset = uno schema = un solo split, e i dataset dello stesso dominio restano insieme):

| split | task | schemi | lingue |
| --- | --- | --- | --- |
| dev | 96 | bevc, bevk, bevq, miet, motg, sozh, whgz | {'de': 24, 'en': 24, 'fr': 24, 'it': 24} |
| val | 30 | abfl, eink | {'de': 8, 'en': 7, 'fr': 8, 'it': 7} |
| test | 84 | abst, feue, kpi, luft, rett, wett | {'de': 21, 'en': 21, 'fr': 21, 'it': 21} |

  `tasks/zurich/SPLITS.json` registra conteggi, impronte dei file e dei dati. Il CLI **rifiuta** i task del test senza `--final-test`.
- **Trappole reali** (etichettate in `meta.trap`): nomi di colonna tedeschi con domande in altre lingue (`cross_lingual_schema`), numeri salvati come testo (`text_numbers`), marcatori di dato mancante `NA` e `.` (`missing_value_marker`), spazi finali nei nomi (`trailing_whitespace`), più basi dell'indice (`multiple_bases`), tipo orario (`time_type`), codici di dominio (`domain_codes`).
- **Verificato:** i 210 gold si eseguono sull'ambiente di sola lettura e passano il proprio controllo (test `tests/test_zurich_tasks.py`); i file dei task coincidono con la rigenerazione; nessun id, schema o dominio compare in due split.
- **Limiti (leggere):**
  1. **Le domande non sono state riviste da madrelingua**: formulazioni in DE/FR/IT/EN scritte da Claude (strumento di sviluppo, da dichiarare nel rapporto). Serve una revisione a campione (proposta: almeno il 10% per lingua) prima di usare i numeri in un documento.
  2. **Domande da modelli**: circa 70 modelli × 3 istanze; la varietà di forma è minore di un dataset scritto a mano. Le domande dello stesso modello hanno la stessa struttura.
  3. **Il test è piccolo** (84 task, 6 schemi): intervalli larghi (vedi `docs/analysis_plan.md` §5); non dire «nessun effetto» senza guardare l'ampiezza.
  4. **Pochi dati di addestramento**: il dev ha 96 task. Il generatore può produrre più istanze (`--n-dev`) dagli stessi schemi, ma restano gli stessi 7 schemi: il protocollo LoRA/WSP (W08/W07) deve dichiarare quanti ne usa.
  5. Le risposte uniche dipendono dai dati dell'istantanea; i gold usano un ordinamento totale quando serve (`order_matters`), ma l'assenza di pareggi è controllata solo sui modelli con `tie`.
  6. **Condizioni formali del portale non lette** (pagine legali 404): CC0 nei metadati e «ohne Nutzungseinschränkungen» sulla pagina; nulla su uso per IA.
  7. **Contaminazione non esclusa**: i dati sono pubblici e potrebbero essere nei dati di addestramento di Apertus (non lo sappiamo).

## 6. Non ancora fatto
Revisione umana delle domande; Swissvotes come dataset aggiuntivo (scaricabile con `scripts/fetch_swissvotes.sh`, nessun task scritto); verifica delle licenze di opendata.swiss/OpenParlData; licenze di `peft`/`transformers`/`torch`; stima dello spazio per BIRD.
