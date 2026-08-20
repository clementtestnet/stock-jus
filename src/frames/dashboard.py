# dashboard.py
import tkinter as tk
from tkinter import ttk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from config import MONNAIE, BOUTIQUE_NOM

class DashboardFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.controller = controller
        self._build()

    def _build(self):
        tk.Label(self, text="Tableau de bord", font=("Arial", 18, "bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(anchor="w", padx=30, pady=(20,3))
        tk.Label(self, text=f"Bienvenue sur {BOUTIQUE_NOM}", font=("Arial", 10),
                 bg="#f0f4f8", fg="#667788").pack(anchor="w", padx=30, pady=(0,15))

        self.cards_frame = tk.Frame(self, bg="#f0f4f8")
        self.cards_frame.pack(fill="x", padx=30)
        self.c_produits    = self._card(self.cards_frame, "Produits",          "0", "#4a90d9", "Produits")
        self.c_stock       = self._card(self.cards_frame, f"Total en stock",   "0", "#27ae60", "Stock")
        self.c_alertes     = self._card(self.cards_frame, "Stock bas",         "0", "#e74c3c", "Alertes")
        self.c_fournisseurs= self._card(self.cards_frame, "Fournisseurs",      "0", "#f39c12", "Fourn.")
        for c in [self.c_produits, self.c_stock, self.c_alertes, self.c_fournisseurs]:
            c.pack(side="left", padx=8, pady=8, expand=True, fill="x")

        tk.Label(self, text="Derniers approvisionnements", font=("Arial", 13, "bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(anchor="w", padx=30, pady=(15,5))
        cols = ("Date","Produit","Fournisseur","Quantite","Total")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=7)
        for c, w in zip(cols, [130,180,150,90,130]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="x", padx=30, pady=3)

        tk.Label(self, text="Produits en stock bas", font=("Arial", 12, "bold"),
                 bg="#f0f4f8", fg="#e74c3c").pack(anchor="w", padx=30, pady=(12,5))
        cols2 = ("Produit","Stock actuel","Minimum")
        self.tree2 = ttk.Treeview(self, columns=cols2, show="headings", height=4)
        for c, w in zip(cols2, [220,140,140]):
            self.tree2.heading(c, text=c); self.tree2.column(c, width=w, anchor="center")
        self.tree2.pack(fill="x", padx=30, pady=3)
        self.tree2.tag_configure("bas", foreground="#e74c3c")

    def _card(self, parent, title, value, color, icon):
        f = tk.Frame(parent, bg=color)
        tk.Label(f, text=icon, font=("Arial", 11), bg=color, fg="white").pack(pady=(10,0))
        lv = tk.Label(f, text=value, font=("Arial", 20, "bold"), bg=color, fg="white")
        lv.pack()
        tk.Label(f, text=title, font=("Arial", 8), bg=color, fg="#e8f4fd").pack(pady=(0,10))
        f._val = lv
        return f

    def refresh(self):
        conn = get_connection()
        nb_p   = conn.execute("SELECT COUNT(*) FROM produits").fetchone()[0]
        total  = conn.execute("SELECT SUM(stock_actuel) FROM produits").fetchone()[0] or 0
        alrt   = conn.execute("SELECT COUNT(*) FROM produits WHERE stock_actuel<=stock_minimum").fetchone()[0]
        nb_f   = conn.execute("SELECT COUNT(*) FROM fournisseurs").fetchone()[0]
        self.c_produits._val.config(text=str(nb_p))
        self.c_stock._val.config(text=str(total))
        self.c_alertes._val.config(text=str(alrt))
        self.c_fournisseurs._val.config(text=str(nb_f))

        for r in self.tree.get_children(): self.tree.delete(r)
        for r in conn.execute("""
            SELECT a.date_achat,p.nom,COALESCE(f.nom,'-'),a.quantite,a.prix_total
            FROM achats a JOIN produits p ON a.produit_id=p.id
            LEFT JOIN fournisseurs f ON a.fournisseur_id=f.id
            ORDER BY a.date_achat DESC LIMIT 8
        """).fetchall():
            self.tree.insert("","end", values=(str(r[0])[:16],r[1],r[2],r[3],f"{r[4]:,.0f} {MONNAIE}"))

        for r in self.tree2.get_children(): self.tree2.delete(r)
        for r in conn.execute(
            "SELECT nom,stock_actuel,stock_minimum FROM produits WHERE stock_actuel<=stock_minimum"
        ).fetchall():
            self.tree2.insert("","end", values=(r[0],r[1],r[2]), tags=("bas",))
        conn.close()
