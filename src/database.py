"""
database.py — Initialisation et accès à la base de données SQLite
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stock_jus.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Table : Produits (références de jus)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            description TEXT,
            unite TEXT DEFAULT 'bouteille',
            prix_vente REAL DEFAULT 0,
            stock_actuel INTEGER DEFAULT 0,
            stock_minimum INTEGER DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table : Fournisseurs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fournisseurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            telephone TEXT,
            adresse TEXT,
            email TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table : Achats / Approvisionnements
    cur.execute("""
        CREATE TABLE IF NOT EXISTS achats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produit_id INTEGER NOT NULL,
            fournisseur_id INTEGER,
            quantite INTEGER NOT NULL,
            prix_unitaire REAL NOT NULL,
            prix_total REAL NOT NULL,
            date_achat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (produit_id) REFERENCES produits(id),
            FOREIGN KEY (fournisseur_id) REFERENCES fournisseurs(id)
        )
    """)

    # Table : Ventes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produit_id INTEGER NOT NULL,
            quantite INTEGER NOT NULL,
            prix_unitaire REAL NOT NULL,
            prix_total REAL NOT NULL,
            date_vente TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            client TEXT,
            notes TEXT,
            FOREIGN KEY (produit_id) REFERENCES produits(id)
        )
    """)

    # Table : Mouvements de stock (entrées/sorties)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mouvements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produit_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('entree', 'sortie', 'ajustement')),
            quantite INTEGER NOT NULL,
            motif TEXT,
            date_mouvement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produit_id) REFERENCES produits(id)
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Base de données initialisée.")


if __name__ == "__main__":
    init_db()
