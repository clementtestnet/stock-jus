"""
historique.py — Historique des approvisionnements
"""

import tkinter as tk
from tkinter import ttk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection


class HistoriqueFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.controller = controller
        self._build()

    def _build(self):
        tk.Label(self, text="Historique des Approvisionnements", font=("Arial", 18, "bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(anchor="w", padx=30, pady=(25, 5))

        # Filtres
        filter_frame = tk.Frame(self, bg="#f0f4f8")
        filter_frame.pack(fill="x", padx=30, pady=5)

        tk.Label(filter_frame, text="Produit :", bg="#f0f4f8", font=("Arial", 9)).pack(side="left")
        self.filter_produit = tk.StringVar(value="Tous")
        self.cb_produit = ttk.Combobox(filter_frame, textvariable=self.filter_produit, width=20, state="readonly")
        self.cb_produit.pack(side="left", padx=5)

        tk.Label(filter_frame, text="Fournisseur :", bg="#f0f4f8", font=("Arial", 9)).pack(side="left", padx=(15, 0))
        self.filter_fourn = tk.StringVar(value="Tous")
        self.cb_fourn = ttk.Combobox(filter_frame, textvariable=self.filter_fourn, width=20, state="readonly")
        self.cb_fourn.pack(side="left", padx=5)

        tk.Button(filter_frame, text="🔍 Filtrer", font=("Arial", 9),
                  bg="#4a90d9", fg="white", relief="flat", padx=10,
                  cursor="hand2", command=self._load_data).pack(side="left", padx=10)
        tk.Button(filter_frame, text="🔄 Tout afficher", font=("Arial", 9),
                  bg="#667788", fg="white", relief="flat", padx=10,
                  cursor="hand2", command=self.refresh).pack(side="left")

        # Tableau
        cols = ("Date", "Produit", "Fournisseur", "Quantité", "Prix unitaire", "Prix total", "Notes")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        widths = [130, 160, 140, 80, 110, 110, 180]
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c, command=lambda _c=c: None)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=30, pady=5)

        # Total affiché
        self.lbl_total = tk.Label(self, text="Total affiché : 0.00 CDF", font=("Arial", 10, "bold"),
                                   bg="#f0f4f8", fg="#27ae60")
        self.lbl_total.pack(anchor="e", padx=30, pady=5)

    def refresh(self):
        conn = get_connection()
        produits = ["Tous"] + [r[0] for r in conn.execute("SELECT nom FROM produits ORDER BY nom").fetchall()]
        fournisseurs = ["Tous"] + [r[0] for r in conn.execute("SELECT nom FROM fournisseurs ORDER BY nom").fetchall()]
        conn.close()
        self.cb_produit["values"] = produits
        self.cb_fourn["values"] = fournisseurs
        self.filter_produit.set("Tous")
        self.filter_fourn.set("Tous")
        self._load_data()

    def _load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        query = """
            SELECT a.date_achat, p.nom, COALESCE(f.nom, '—'), a.quantite,
                   a.prix_unitaire, a.prix_total, COALESCE(a.notes, '—')
            FROM achats a
            JOIN produits p ON a.produit_id = p.id
            LEFT JOIN fournisseurs f ON a.fournisseur_id = f.id
        """
        filters = []
        params = []
        p_filter = self.filter_produit.get()
        f_filter = self.filter_fourn.get()
        if p_filter != "Tous":
            filters.append("p.nom = ?")
            params.append(p_filter)
        if f_filter != "Tous":
            filters.append("f.nom = ?")
            params.append(f_filter)
        if filters:
            query += " WHERE " + " AND ".join(filters)
        query += " ORDER BY a.date_achat DESC"

        conn = get_connection()
        rows = conn.execute(query, params).fetchall()
        conn.close()

        total = 0
        for r in rows:
            self.tree.insert("", "end", values=(
                str(r[0])[:16], r[1], r[2], r[3],
                f"{r[4]:.2f} CDF", f"{r[5]:.2f} CDF", r[6]
            ))
            total += r[5]

        self.lbl_total.config(text=f"Total affiché : {total:,.2f} CDF")
