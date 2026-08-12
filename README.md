# 🧃 Logiciel de Gestion de Stock — Jus en Bouteille

Application desktop Windows pour gérer le stock d'une boutique de jus.

## 📁 Structure

```
stock-jus/
├── src/
│   ├── main.py               ← Point d'entrée
│   ├── database.py           ← Base de données SQLite
│   └── frames/
│       ├── dashboard.py      ← Tableau de bord
│       ├── produits.py       ← Gestion produits
│       ├── achats.py         ← Nouvel achat
│       ├── fournisseurs.py   ← Gestion fournisseurs
│       ├── historique.py     ← Historique achats
│       └── rapports.py       ← Rapports & stats
├── lancer.bat                ← Lancer l'app (double-clic)
└── stock_jus.db              ← Base de données (créée automatiquement)
```

## ▶️ Lancement

### Prérequis
- Python 3.8+ installé sur Windows
- Tkinter (inclus avec Python)

### Lancer l'application
1. Double-cliquer sur `lancer.bat`
2. **OU** ouvrir un terminal dans ce dossier et taper :
   ```
   python src\main.py
   ```

## 🔧 Fonctionnalités

| Module | Description |
|--------|-------------|
| 🏠 Tableau de bord | Vue d'ensemble : stats, derniers achats, alertes stock bas |
| 📦 Produits & Stock | Ajouter/modifier/supprimer des références de jus |
| 🛒 Nouvel Achat | Enregistrer un approvisionnement, calcul automatique du total |
| 🏭 Fournisseurs | Gérer la liste des fournisseurs |
| 📋 Historique | Voir tous les achats passés avec filtres |
| 📊 Rapports | État du stock, dépenses par période, top produits |

## 📦 Packager en .exe (optionnel)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "StockJus" src/main.py
```
Le fichier `.exe` sera dans le dossier `dist/`.
