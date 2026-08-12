"""
dashboard.py — Tableau de bord principal
"""

import tkinter as tk
from tkinter import ttk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection


class DashboardFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.controller = controller
        self._build()

    def _build(self):
        # Titre
        tk.Label(self, text="Tableau de bord", font=("Arial", 18, "bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(anchor="w", padx=30, pady=(25, 5))
        tk.Label(self, text="Vue d'ensemble de votre stock", font=("Arial", 10),
                 bg="#f0f4f8", fg="#667788").pack(anchor="w", padx=30, pady=(0, 20))

        # Cartes de statistiques
        self.cards_frame = tk.Frame(self, bg="#f0f4f8")
        self.cards_frame.pack(fill="x", padx=30)

        self.card_produits = self._make_card(self.cards_frame, "Produits", "0", "#4a90d9", "📦")
        self.card_stock = self._make_card(self.cards_frame, "Bouteilles en stock", "0", "#27ae60", "🧃")
        self.card_alertes = self._make_card(self.cards_frame, "Alertes stock bas", "0", "#e74c3c", "⚠️")
        self.card_fournisseurs = self._make_card(self.cards_frame, "Fournisseurs", "0", "#f39c12", "🏭")

        for c in [self.card_produits, self.card_stock, self.card_alertes, self.card_fournisseurs]:
            c.pack(side="left", padx=10, pady=10, expand=True, fill="x")

        # Derniers achats
        tk.Label(self, text="Derniers approvisionnements", font=("Arial", 13, "bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(anchor="w", padx=30, pady=(20, 5))

        cols = ("Date", "Produit", "Fournisseur", "Quantité", "Prix Total")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=8)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=160, anchor="center")
        self.tree.pack(fill="x", padx=30, pady=5)

        # Alerte stock bas
        tk.Label(self, text="⚠️ Produits en stock bas", font=("Arial", 13, "bold"),
                 bg="#f0f4f8", fg="#e74c3c").pack(anchor="w", padx=30, pady=(15, 5))
        cols2 = ("Produit", "Stock actuel", "Minimum requis")
        self.tree_alertes = ttk.Treeview(self, columns=cols2, show="headings", height=4)
        for c in cols2:
            self.tree_alertes.heading(c, text=c)
            self.tree_alertes.column(c, width=200, anchor="center")
        self.tree_alertes.pack(fill="x", padx=30, pady=5)

    def _make_card(self, parent, title, value, color, icon):
        frame = tk.Frame(parent, bg=color, relief="flat", bd=0)
        frame.configure(highlightbackground=color, highlightthickness=2)
        tk.Label(frame, text=icon, font=("Arial", 22), bg=color, fg="white").pack(pady=(12, 0))
        lbl_val = tk.Label(frame, text=value, font=("Arial", 20, "bold"), bg=color, fg="white")
        lbl_val.pack()
        tk.Label(frame, text=title, font=("Arial", 9), bg=color, fg="#e8f4fd").pack(pady=(0, 12))
        frame._value_label = lbl_val
        return frame

    def refresh(self):
        conn = get_connection()
        cur = conn.cursor()

        # Stats
        nb_produits = cur.execute("SELECT COUNT(*) FROM produits").fetchone()[0]
        total_stock = cur.execute("SELECT SUM(stock_actuel) FROM produits").fetchone()[0] or 0
        alertes = cur.execute("SELECT COUNT(*) FROM produits WHERE stock_actuel <= stock_minimum").fetchone()[0]
        nb_fourn = cur.execute("SELECT COUNT(*) FROM fournisseurs").fetchone()[0]

        self.card_produits._value_label.config(text=str(nb_produits))
        self.card_stock._value_label.config(text=str(total_stock))
        self.card_alertes._value_label.config(text=str(alertes))
        self.card_fournisseurs._value_label.config(text=str(nb_fourn))

        # Derniers achats
        for row in self.tree.get_children():
            self.tree.delete(row)
        rows = cur.execute("""
            SELECT a.date_achat, p.nom, COALESCE(f.nom, '—'), a.quantite, a.prix_total
            FROM achats a
            JOIN produits p ON a.produit_id = p.id
            LEFT JOIN fournisseurs f ON a.fournisseur_id = f.id
            ORDER BY a.date_achat DESC LIMIT 10
        """).fetchall()
        for r in rows:
            self.tree.insert("", "end", values=(
                str(r[0])[:16], r[1], r[2], r[3], f"{r[4]:.2f} CDF"
            ))

        # Alertes stock bas
        for row in self.tree_alertes.get_children():
            self.tree_alertes.delete(row)
        alertes_rows = cur.execute("""
            SELECT nom, stock_actuel, stock_minimum FROM produits
            WHERE stock_actuel <= stock_minimum ORDER BY stock_actuel ASC
        """).fetchall()
        for r in alertes_rows:
            self.tree_alertes.insert("", "end", values=(r[0], r[1], r[2]),
                                     tags=("alerte",))
        self.tree_alertes.tag_configure("alerte", foreground="#e74c3c")

        conn.close()
