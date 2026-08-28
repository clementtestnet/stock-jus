# dashboard.py — MODERNE CustomTkinter
import customtkinter as ctk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from config import MONNAIE, BOUTIQUE_NOM


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.controller = controller
        self._build()

    def _build(self):
        # Titre
        ctk.CTkLabel(self, text="Tableau de bord",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(22, 2))
        ctk.CTkLabel(self, text=f"Bienvenue sur {BOUTIQUE_NOM}",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(
            anchor="w", padx=30, pady=(0, 18))

        # Cartes stats
        self.cards_row = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_row.pack(fill="x", padx=30)

        card_data = [
            ("Produits",      "0", ("#1565C0","#1f6aa5"), "📦"),
            ("Total en stock","0", ("#1e7e34","#1e8449"), "📊"),
            ("Stock bas",     "0", ("#b71c1c","#c0392b"), "⚠️"),
            ("Ventes du jour","0", ("#6a1b9a","#7d3c98"), "💰"),
        ]
        self._card_vals = []
        for title, val, colors, icon in card_data:
            card = ctk.CTkFrame(self.cards_row, corner_radius=14,
                                fg_color=colors)
            card.pack(side="left", expand=True, fill="x", padx=8, pady=8)
            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=22)).pack(pady=(16, 4))
            lv = ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=28, weight="bold"))
            lv.pack()
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11),
                         text_color="gray").pack(pady=(2, 14))
            self._card_vals.append(lv)

        # Derniers approvisionnements
        ctk.CTkLabel(self, text="Derniers approvisionnements",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(
            anchor="w", padx=30, pady=(18, 4))
        self.tree1 = self._make_table(
            ("Date","Produit","Fournisseur","Quantité","Total"),
            (130, 180, 150, 90, 140), height=7)

        # Produits stock bas
        ctk.CTkLabel(self, text="Produits en stock bas",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color="#e74c3c").pack(
            anchor="w", padx=30, pady=(14, 4))
        self.tree2 = self._make_table(
            ("Produit","Stock actuel","Minimum"),
            (220, 140, 140), height=4)

    def _make_table(self, cols, widths, height=6):
        import tkinter.ttk as ttk
        import tkinter as tk
        style = ttk.Style()
        style.configure("Dark.Treeview",
            background="#2b2b2b", foreground="white",
            fieldbackground="#2b2b2b", rowheight=28,
            font=("Arial", 11))
        style.configure("Dark.Treeview.Heading",
            background="#1a1a2e", foreground="#7EB3FF",
            font=("Arial", 11, "bold"), relief="flat")
        style.map("Dark.Treeview", background=[("selected","#1f6aa5")])

        tree = ttk.Treeview(self, columns=cols, show="headings",
                            height=height, style="Dark.Treeview")
        for c, w in zip(cols, widths):
            tree.heading(c, text=c)
            tree.column(c, width=w, anchor="center")
        tree.pack(fill="x", padx=30, pady=4)
        return tree

    def refresh(self):
        conn = get_connection()
        nb_p  = conn.execute("SELECT COUNT(*) FROM produits").fetchone()[0]
        total = conn.execute("SELECT SUM(stock_actuel) FROM produits").fetchone()[0] or 0
        alrt  = conn.execute(
            "SELECT COUNT(*) FROM produits WHERE stock_actuel<=stock_minimum").fetchone()[0]
        today = __import__('datetime').date.today().strftime("%Y-%m-%d")
        ventes_j = conn.execute(
            "SELECT COUNT(*) FROM ventes WHERE DATE(date_vente)=?", (today,)).fetchone()[0]
        for lv, val in zip(self._card_vals, [nb_p, total, alrt, ventes_j]):
            lv.configure(text=str(val))

        for r in self.tree1.get_children(): self.tree1.delete(r)
        for r in conn.execute("""
            SELECT a.date_achat,p.nom,COALESCE(f.nom,'-'),a.quantite,a.prix_total
            FROM achats a JOIN produits p ON a.produit_id=p.id
            LEFT JOIN fournisseurs f ON a.fournisseur_id=f.id
            ORDER BY a.date_achat DESC LIMIT 8
        """).fetchall():
            self.tree1.insert("", "end", values=(
                str(r[0])[:16], r[1], r[2], r[3], f"{r[4]:,.0f} {MONNAIE}"))

        for r in self.tree2.get_children(): self.tree2.delete(r)
        for r in conn.execute(
            "SELECT nom,stock_actuel,stock_minimum FROM produits WHERE stock_actuel<=stock_minimum"
        ).fetchall():
            self.tree2.insert("", "end", values=(r[0], r[1], r[2]))
        conn.close()
