"""
rapports.py — Rapports et tableaux de bord
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection


class RapportsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.controller = controller
        self._build()

    def _build(self):
        tk.Label(self, text="Rapports & Statistiques", font=("Arial", 18, "bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(anchor="w", padx=30, pady=(25, 5))

        # Onglets
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=30, pady=10)

        # Onglet 1 : Résumé stock
        self.tab_stock = tk.Frame(notebook, bg="#f0f4f8")
        notebook.add(self.tab_stock, text="📦 État du stock")

        # Onglet 2 : Achats par période
        self.tab_achats = tk.Frame(notebook, bg="#f0f4f8")
        notebook.add(self.tab_achats, text="🛒 Achats par période")

        # Onglet 3 : Top produits achetés
        self.tab_top = tk.Frame(notebook, bg="#f0f4f8")
        notebook.add(self.tab_top, text="🏆 Top produits")

        self._build_stock_tab()
        self._build_achats_tab()
        self._build_top_tab()

    # ─── Tab 1 : État du stock ──────────────────────────────────────
    def _build_stock_tab(self):
        tk.Button(self.tab_stock, text="🔄 Actualiser", font=("Arial", 9),
                  bg="#4a90d9", fg="white", relief="flat", padx=10,
                  cursor="hand2", command=self._load_stock).pack(anchor="ne", padx=10, pady=10)

        cols = ("Produit", "Unité", "Stock actuel", "Stock min", "Prix vente", "Valeur stock", "Statut")
        self.tree_stock = ttk.Treeview(self.tab_stock, columns=cols, show="headings", height=12)
        widths = [180, 80, 100, 90, 110, 120, 100]
        for c, w in zip(cols, widths):
            self.tree_stock.heading(c, text=c)
            self.tree_stock.column(c, width=w, anchor="center")
        self.tree_stock.pack(fill="both", expand=True, padx=10, pady=5)
        self.tree_stock.tag_configure("bas", foreground="#e74c3c")
        self.tree_stock.tag_configure("ok", foreground="#27ae60")

        self.lbl_valeur_totale = tk.Label(self.tab_stock, text="Valeur totale du stock : 0.00 CDF",
                                           font=("Arial", 11, "bold"), bg="#f0f4f8", fg="#1a2940")
        self.lbl_valeur_totale.pack(anchor="e", padx=15, pady=8)

    def _load_stock(self):
        for row in self.tree_stock.get_children():
            self.tree_stock.delete(row)
        conn = get_connection()
        rows = conn.execute("""
            SELECT nom, unite, stock_actuel, stock_minimum, prix_vente
            FROM produits ORDER BY nom
        """).fetchall()
        conn.close()
        total_val = 0
        for r in rows:
            val = r[2] * r[4]
            total_val += val
            statut = "⚠️ Bas" if r[2] <= r[3] else "✅ OK"
            tag = "bas" if r[2] <= r[3] else "ok"
            self.tree_stock.insert("", "end", values=(
                r[0], r[1], r[2], r[3], f"{r[4]:.2f}", f"{val:,.2f}", statut
            ), tags=(tag,))
        self.lbl_valeur_totale.config(text=f"Valeur totale du stock : {total_val:,.2f} CDF")

    # ─── Tab 2 : Achats par période ─────────────────────────────────
    def _build_achats_tab(self):
        filter_f = tk.Frame(self.tab_achats, bg="#f0f4f8")
        filter_f.pack(fill="x", padx=10, pady=10)

        tk.Label(filter_f, text="Du :", bg="#f0f4f8", font=("Arial", 9)).pack(side="left")
        self.date_debut = tk.StringVar(value=f"{date.today().year}-01-01")
        tk.Entry(filter_f, textvariable=self.date_debut, width=12).pack(side="left", padx=5)

        tk.Label(filter_f, text="Au :", bg="#f0f4f8", font=("Arial", 9)).pack(side="left", padx=(10, 0))
        self.date_fin = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        tk.Entry(filter_f, textvariable=self.date_fin, width=12).pack(side="left", padx=5)

        tk.Button(filter_f, text="📊 Calculer", font=("Arial", 9),
                  bg="#27ae60", fg="white", relief="flat", padx=10,
                  cursor="hand2", command=self._load_achats).pack(side="left", padx=15)

        cols = ("Produit", "Nb achats", "Quantité totale", "Dépense totale", "Prix moyen/unité")
        self.tree_achats = ttk.Treeview(self.tab_achats, columns=cols, show="headings", height=12)
        widths = [200, 90, 120, 130, 130]
        for c, w in zip(cols, widths):
            self.tree_achats.heading(c, text=c)
            self.tree_achats.column(c, width=w, anchor="center")
        self.tree_achats.pack(fill="both", expand=True, padx=10)

        self.lbl_total_depenses = tk.Label(self.tab_achats, text="Total dépenses : 0.00 CDF",
                                            font=("Arial", 11, "bold"), bg="#f0f4f8", fg="#e74c3c")
        self.lbl_total_depenses.pack(anchor="e", padx=15, pady=8)

    def _load_achats(self):
        for row in self.tree_achats.get_children():
            self.tree_achats.delete(row)
        conn = get_connection()
        rows = conn.execute("""
            SELECT p.nom, COUNT(a.id), SUM(a.quantite), SUM(a.prix_total),
                   ROUND(SUM(a.prix_total)/SUM(a.quantite), 2)
            FROM achats a JOIN produits p ON a.produit_id = p.id
            WHERE a.date_achat BETWEEN ? AND ?
            GROUP BY p.id ORDER BY SUM(a.prix_total) DESC
        """, (self.date_debut.get(), self.date_fin.get() + " 23:59:59")).fetchall()
        conn.close()
        total = 0
        for r in rows:
            self.tree_achats.insert("", "end", values=(r[0], r[1], r[2], f"{r[3]:,.2f} CDF", f"{r[4]:.2f} CDF"))
            total += r[3]
        self.lbl_total_depenses.config(text=f"Total dépenses : {total:,.2f} CDF")

    # ─── Tab 3 : Top produits ───────────────────────────────────────
    def _build_top_tab(self):
        tk.Button(self.tab_top, text="🔄 Actualiser", font=("Arial", 9),
                  bg="#4a90d9", fg="white", relief="flat", padx=10,
                  cursor="hand2", command=self._load_top).pack(anchor="ne", padx=10, pady=10)

        cols = ("Rang", "Produit", "Total acheté (bouteilles)", "Total dépensé (CDF)", "Dernière livraison")
        self.tree_top = ttk.Treeview(self.tab_top, columns=cols, show="headings", height=12)
        widths = [60, 220, 160, 160, 150]
        for c, w in zip(cols, widths):
            self.tree_top.heading(c, text=c)
            self.tree_top.column(c, width=w, anchor="center")
        self.tree_top.pack(fill="both", expand=True, padx=10, pady=5)

    def _load_top(self):
        for row in self.tree_top.get_children():
            self.tree_top.delete(row)
        conn = get_connection()
        rows = conn.execute("""
            SELECT p.nom, SUM(a.quantite), SUM(a.prix_total), MAX(a.date_achat)
            FROM achats a JOIN produits p ON a.produit_id = p.id
            GROUP BY p.id ORDER BY SUM(a.quantite) DESC LIMIT 20
        """).fetchall()
        conn.close()
        for i, r in enumerate(rows, 1):
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else str(i)
            self.tree_top.insert("", "end", values=(medal, r[0], r[1], f"{r[2]:,.2f}", str(r[3])[:10]))

    def refresh(self):
        self._load_stock()
        self._load_top()
