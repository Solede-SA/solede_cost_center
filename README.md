# Solede Cost Center

App Frappe per importare Cost Center da CSV/Excel con supporto per naming personalizzato.

## Funzionalita

1. **Cost Center Importer** - Interfaccia per importare Cost Center da file CSV/Excel
2. **Naming personalizzato** - Permette di definire il name del Cost Center senza concatenazione forzata con l'abbreviazione company

## Installazione

```bash
bench get-app solede_cost_center
bench --site [site-name] install-app solede_cost_center
```

## Template CSV

```csv
ID,Cost Center Name,Parent Cost Center,Is Group
ROOT001,Azienda Principale,,1
COMM001,Commerciale,ROOT001,1
VEND001,Vendite Italia,COMM001,0
```

- **ID**: Diventa il `name` del Cost Center nel database (es. "ROOT001")
- **Cost Center Name**: Nome visualizzato del Cost Center
- **Parent Cost Center**: ID del Cost Center padre (lasciare vuoto per root)
- **Is Group**: 1 se e un gruppo, 0 se e un ledger

## Licenza

AGPL-3.0
