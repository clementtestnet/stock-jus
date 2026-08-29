# 🧃 Stock Jus — v5.0

Application de gestion de stock pour boutique de jus en bouteille.
Interface moderne **CustomTkinter** (thème sombre), base de données SQLite locale.

---

## 🚀 Installation rapide (mode Python)

1. Télécharger le ZIP → extraire
2. Double-cliquer **`INSTALLER_ET_LANCER.bat`**
3. C'est tout — l'appli se lance !

> Requiert Python 3.9+ installé sur le PC.  
> Télécharger Python : https://python.org

---

## 📦 Créer un .EXE Windows (sans Python requis)

### Étape 1 — Compiler

Double-cliquer **`COMPILER_EXE.bat`**

Ce script :
- Installe PyInstaller automatiquement
- Compile tout le code en un seul dossier `dist\StockJus\`
- Le résultat : **`dist\StockJus\StockJus.exe`**

> ⏱ La compilation prend 2 à 5 minutes la première fois.

### Étape 2 — Distribuer

**Option A — Copier le dossier** (simple)
```
Copier le dossier dist\StockJus\ sur n'importe quel PC Windows
Lancer StockJus.exe
```

**Option B — Créer un installateur** (professionnel)
1. Installer **Inno Setup** : https://jrsoftware.org/isdl.php
2. Double-cliquer **`CREER_INSTALLATEUR.bat`**
3. Résultat : `installer\StockJus_Setup_v5.exe`
4. Distribuer ce fichier → l'installation crée un raccourci sur le Bureau

---

## 🔑 Comptes par défaut

| Utilisateur | Mot de passe | Rôle |
|---|---|---|
| admin | admin123 | Administrateur |
| employe1 | employe1 | Employé |
| employe2 | employe2 | Employé |
| employe3 | employe3 | Employé |

---

## 📋 Fonctionnalités

- ✅ **Vente rapide** — Recherche live, panier multi-produits, prix fixe
- ✅ **Réductions automatiques** — Palier configurable par produit
- ✅ **Factures PDF** — Générées automatiquement après chaque vente
- ✅ **Historique conservé** — Même si un produit est supprimé
- ✅ **Stock sécurisé** — Jamais négatif
- ✅ **Rapports PDF** — Stock, achats, ventes par période
- ✅ **Multi-utilisateurs** — Admin + Employés avec espaces séparés

---

## 🗂️ Structure

```
stock-jus/
├── INSTALLER_ET_LANCER.bat   ← Démarrage rapide Python
├── COMPILER_EXE.bat          ← Crée le .exe Windows
├── CREER_INSTALLATEUR.bat    ← Crée Setup.exe (Inno Setup requis)
├── stock_jus.spec            ← Config PyInstaller
├── stock_jus_setup.iss       ← Config Inno Setup
├── assets/
│   └── icon.ico              ← Icône de l'application
└── src/
    ├── main.py               ← Point d'entrée Admin
    ├── app_employe.py        ← Interface Employé
    ├── database.py           ← Base SQLite
    ├── config.py             ← Nom boutique, monnaie...
    ├── facture.py            ← PDF factures
    ├── pdf_export.py         ← PDF rapports
    ├── reduction.py          ← Calcul réductions
    └── frames/               ← Tous les écrans
```
