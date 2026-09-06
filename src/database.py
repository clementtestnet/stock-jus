# database.py
import sqlite3, os, hashlib

# Chemin DB : respecte STOCK_JUS_DB si défini (mode .exe PyInstaller),
# sinon remonte d'un niveau depuis src/
_default_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "stock_jus.db")
DB_PATH = os.environ.get("STOCK_JUS_DB", _default_db)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def _h(p):
    return hashlib.sha256(p.encode()).hexdigest()

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS utilisateurs (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        nom      TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role     TEXT NOT NULL CHECK(role IN ('admin','employe')),
        actif    INTEGER DEFAULT 1
    )""")
    if c.execute("SELECT COUNT(*) FROM utilisateurs").fetchone()[0] == 0:
        c.executemany(
            "INSERT INTO utilisateurs (nom,username,password,role) VALUES (?,?,?,?)",
            [('Administrateur','admin',   _h('admin123'),'admin'),
             ('Employe 1',     'employe1',_h('employe1'),'employe'),
             ('Employe 2',     'employe2',_h('employe2'),'employe'),
             ('Employe 3',     'employe3',_h('employe3'),'employe')])

    c.execute("""CREATE TABLE IF NOT EXISTS produits (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        nom               TEXT NOT NULL,
        description       TEXT,
        unite             TEXT DEFAULT 'paquet',
        prix_vente        REAL DEFAULT 0,
        stock_actuel      REAL DEFAULT 0,
        stock_minimum     REAL DEFAULT 10,
        reduction_palier  INTEGER DEFAULT 0,
        reduction_quantite INTEGER DEFAULT 0,
        created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # ventes — produit_id nullable + snapshot nom
    c.execute("""CREATE TABLE IF NOT EXISTS ventes (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        produit_id      INTEGER,
        produit_nom     TEXT,
        quantite        REAL NOT NULL,
        prix_unitaire   REAL NOT NULL,
        prix_total      REAL NOT NULL,
        paquets_offerts REAL DEFAULT 0,
        date_vente      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        client          TEXT,
        notes           TEXT,
        FOREIGN KEY (produit_id) REFERENCES produits(id) ON DELETE SET NULL
    )""")

    # achats — produit_id nullable + snapshot nom
    c.execute("""CREATE TABLE IF NOT EXISTS achats (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        produit_id    INTEGER,
        produit_nom   TEXT,
        quantite      INTEGER NOT NULL,
        prix_unitaire REAL NOT NULL,
        prix_total    REAL NOT NULL,
        date_achat    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes         TEXT,
        FOREIGN KEY (produit_id) REFERENCES produits(id) ON DELETE SET NULL
    )""")

    # sorties — produit_id nullable + snapshot nom
    c.execute("""CREATE TABLE IF NOT EXISTS sorties (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        produit_id  INTEGER,
        produit_nom TEXT,
        quantite    INTEGER NOT NULL,
        destination TEXT NOT NULL,
        motif       TEXT,
        date_sortie TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes       TEXT,
        FOREIGN KEY (produit_id) REFERENCES produits(id) ON DELETE SET NULL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS mouvements (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        produit_id     INTEGER,
        type           TEXT NOT NULL CHECK(type IN ('entree','sortie','ajustement')),
        quantite       INTEGER NOT NULL,
        motif          TEXT,
        date_mouvement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (produit_id) REFERENCES produits(id) ON DELETE SET NULL
    )""")

    conn.commit()
    _migrate(conn)
    conn.close()


def _migrate(conn):
    """Ajoute les colonnes manquantes sur une DB existante."""
    c = conn.cursor()
    def add_col(table, col, typedef):
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typedef}")
            conn.commit()
        except Exception:
            pass
    add_col("ventes",  "produit_nom", "TEXT")
    add_col("achats",  "produit_nom", "TEXT")
    add_col("sorties", "produit_nom", "TEXT")
    add_col("sorties", "destination", "TEXT")
    # Backfill produit_nom depuis produits existants
    for tbl in ("ventes", "achats", "sorties"):
        c.execute(f"""
            UPDATE {tbl} SET produit_nom=(
                SELECT nom FROM produits WHERE produits.id={tbl}.produit_id)
            WHERE produit_nom IS NULL AND produit_id IS NOT NULL
        """)
    # Migration demi-paquet : stock_actuel et quantite passent en REAL
    # SQLite ne modifie pas le type des colonnes — on force via une valeur REAL
    # (SQLite stocke déjà en REAL si on insère un float, la migration est transparente)
    # On s'assure juste que stock_actuel accepte 0.5 en faisant un UPDATE no-op
    try:
        c.execute("UPDATE produits SET stock_actuel = CAST(stock_actuel AS REAL) WHERE 1=0")
    except Exception:
        pass
    conn.commit()
