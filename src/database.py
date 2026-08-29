# database.py — Base de données SQLite
# produit_id NULLABLE dans ventes/achats/sorties/mouvements → historique conservé même après suppression

import sqlite3, os, hashlib

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stock_jus.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def h(p):
    return hashlib.sha256(p.encode()).hexdigest()

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS utilisateurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin','employe')),
        actif INTEGER DEFAULT 1
    )""")

    if c.execute("SELECT COUNT(*) FROM utilisateurs").fetchone()[0] == 0:
        c.executemany("INSERT INTO utilisateurs (nom,username,password,role) VALUES (?,?,?,?)", [
            ('Administrateur', 'admin',    h('admin123'), 'admin'),
            ('Employe 1',      'employe1', h('employe1'), 'employe'),
            ('Employe 2',      'employe2', h('employe2'), 'employe'),
            ('Employe 3',      'employe3', h('employe3'), 'employe'),
        ])

    c.execute("""CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        description TEXT,
        unite TEXT DEFAULT 'paquet',
        prix_vente REAL DEFAULT 0,
        stock_actuel INTEGER DEFAULT 0,
        stock_minimum INTEGER DEFAULT 10,
        reduction_palier INTEGER DEFAULT 0,
        reduction_quantite INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS fournisseurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        telephone TEXT,
        adresse TEXT,
        email TEXT,
        notes TEXT
    )""")

    # ── achats : produit_id nullable → historique conservé après suppression produit ──
    c.execute("""CREATE TABLE IF NOT EXISTS achats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produit_id INTEGER,
        produit_nom TEXT,
        fournisseur_id INTEGER,
        quantite INTEGER NOT NULL,
        prix_unitaire REAL NOT NULL,
        prix_total REAL NOT NULL,
        date_achat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (produit_id) REFERENCES produits(id) ON DELETE SET NULL,
        FOREIGN KEY (fournisseur_id) REFERENCES fournisseurs(id) ON DELETE SET NULL
    )""")

    # ── ventes : produit_id nullable + produit_nom snapshot ─────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produit_id INTEGER,
        produit_nom TEXT,
        quantite INTEGER NOT NULL,
        prix_unitaire REAL NOT NULL,
        prix_total REAL NOT NULL,
        paquets_offerts INTEGER DEFAULT 0,
        date_vente TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        client TEXT,
        notes TEXT,
        FOREIGN KEY (produit_id) REFERENCES produits(id) ON DELETE SET NULL
    )""")

    # ── sorties : idem ───────────────────────────────────────────────────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS sorties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produit_id INTEGER,
        produit_nom TEXT,
        quantite INTEGER NOT NULL,
        destination TEXT NOT NULL,
        motif TEXT,
        date_sortie TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (produit_id) REFERENCES produits(id) ON DELETE SET NULL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS mouvements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produit_id INTEGER,
        type TEXT NOT NULL CHECK(type IN ('entree','sortie','ajustement')),
        quantite INTEGER NOT NULL,
        motif TEXT,
        date_mouvement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (produit_id) REFERENCES produits(id) ON DELETE SET NULL
    )""")

    conn.commit()

    # ── Migrations sur DB existante ──────────────────────────────────────────────────
    _migrate(conn)
    conn.close()


def _migrate(conn):
    """Ajoute les colonnes manquantes sur une base déjà existante."""
    c = conn.cursor()

    def add_col(table, col, typedef):
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typedef}")
            conn.commit()
        except Exception:
            pass   # colonne déjà présente

    # produit_nom snapshot dans ventes / achats / sorties
    add_col("ventes",   "produit_nom", "TEXT")
    add_col("achats",   "produit_nom", "TEXT")
    add_col("sorties",  "produit_nom", "TEXT")
    add_col("sorties",  "destination", "TEXT")

    # Remplir produit_nom sur les lignes existantes qui l'ont à NULL
    for table in ("ventes", "achats", "sorties"):
        c.execute(f"""
            UPDATE {table}
            SET produit_nom = (
                SELECT nom FROM produits WHERE produits.id = {table}.produit_id
            )
            WHERE produit_nom IS NULL AND produit_id IS NOT NULL
        """)
    conn.commit()
