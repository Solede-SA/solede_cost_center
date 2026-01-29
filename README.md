# Solede Cost Center

App Frappe/ERPNext per importare Cost Center da CSV/Excel con supporto per ID personalizzati.

## Caratteristiche

- **Import da CSV/Excel** - Importa strutture gerarchiche di Cost Center da file
- **ID personalizzato** - Ogni Cost Center ha un ID univoco (es. `ENG-PROG-001`) che diventa il nome del documento
- **Preview ad albero** - Visualizza l'anteprima della struttura prima dell'import
- **Eliminazione forzata GL Entries** - Opzione per eliminare le GL Entry esistenti con Cost Center (utile per reimportare)
- **Titolo nei link** - I link mostrano il nome descrittivo invece dell'ID tecnico

## Requisiti

- Frappe Framework >= 15.0
- ERPNext >= 15.0

## Installazione

### Da GitHub

```bash
# Scarica l'app
bench get-app https://github.com/Solede-SA/solede_cost_center

# Installa sul sito
bench --site [nome-sito] install-app solede_cost_center

# Esegui migrate
bench --site [nome-sito] migrate
```

### Aggiornamento

```bash
bench update --apps solede_cost_center
bench --site [nome-sito] migrate
```

## Utilizzo

### 1. Accedi al Cost Center Importer

Vai a: **Accounting > Cost Center Importer**

Oppure cerca "Cost Center Importer" nella barra di ricerca.

### 2. Seleziona la Company

Seleziona la company per cui vuoi importare i Cost Center.

> **Nota**: Se esistono GL Entry con Cost Center per questa company, apparirà un avviso. Puoi abilitare "Force Delete GL Entries" per eliminarle e procedere con l'import.

### 3. Prepara il file CSV/Excel

Il file deve avere 4 colonne:

| Colonna | Descrizione |
|---------|-------------|
| **ID** | Identificativo univoco del Cost Center (diventa il `name` del documento) |
| **Cost Center Name** | Nome descrittivo visualizzato |
| **Parent Cost Center** | ID del Cost Center padre (vuoto per il root) |
| **Is Group** | `1` se gruppo, `0` se ledger |

Puoi scaricare un template cliccando su **Download Template**.

### 4. Carica il file

Carica il file CSV o Excel. Apparirà una preview ad albero della struttura.

### 5. Importa

Clicca su **Import** per creare i Cost Center.

> **Attenzione**: L'import elimina tutti i Cost Center esistenti per la company selezionata e li ricrea dal file.

## Esempio CSV

```csv
ID,Cost Center Name,Parent Cost Center,Is Group
ENG,Societa Ingegneria,,1
ENG-DIR,Direzione,ENG,1
ENG-DIR-GEN,Direzione Generale,ENG-DIR,0
ENG-DIR-AMM,Direzione Amministrativa,ENG-DIR,0
ENG-PROG,Progettazione,ENG,1
ENG-PROG-CIV,Progettazione Civile,ENG-PROG,1
ENG-PROG-CIV-STR,Strutture,ENG-PROG-CIV,0
ENG-PROG-CIV-GEO,Geotecnica,ENG-PROG-CIV,0
ENG-PROG-IMP,Progettazione Impianti,ENG-PROG,1
ENG-PROG-IMP-ELE,Impianti Elettrici,ENG-PROG-IMP,0
ENG-PROG-IMP-MEC,Impianti Meccanici,ENG-PROG-IMP,0
ENG-AMM,Amministrazione,ENG,1
ENG-AMM-CON,Contabilita,ENG-AMM,0
ENG-AMM-HR,Risorse Umane,ENG-AMM,0
```

Questo crea la seguente struttura:

```
Societa Ingegneria (ENG)
├── Direzione (ENG-DIR)
│   ├── Direzione Generale (ENG-DIR-GEN)
│   └── Direzione Amministrativa (ENG-DIR-AMM)
├── Progettazione (ENG-PROG)
│   ├── Progettazione Civile (ENG-PROG-CIV)
│   │   ├── Strutture (ENG-PROG-CIV-STR)
│   │   └── Geotecnica (ENG-PROG-CIV-GEO)
│   └── Progettazione Impianti (ENG-PROG-IMP)
│       ├── Impianti Elettrici (ENG-PROG-IMP-ELE)
│       └── Impianti Meccanici (ENG-PROG-IMP-MEC)
└── Amministrazione (ENG-AMM)
    ├── Contabilita (ENG-AMM-CON)
    └── Risorse Umane (ENG-AMM-HR)
```

## Comportamento ID

- L'**ID** diventa il `name` del documento Cost Center nel database
- Il **Cost Center Name** viene mostrato come titolo nei link e nella UI
- Il campo **ID** nel form del Cost Center è editabile

Esempio:
- URL: `/app/cost-center/ENG-PROG-CIV-STR`
- Titolo visualizzato: "Strutture"
- Nei campi Link: appare "Strutture" ma il valore salvato è `ENG-PROG-CIV-STR`

## Disinstallazione

```bash
bench --site [nome-sito] uninstall-app solede_cost_center
bench remove-app solede_cost_center
```

## Licenza

AGPL-3.0 - Vedi [LICENSE](LICENSE)

## Autore

[Solede SA](https://www.solede.ch)
