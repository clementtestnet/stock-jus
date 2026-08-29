# frames/dashboard.py
import customtkinter as ctk
import tkinter.ttk as ttk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from config import MONNAIE, BOUTIQUE_NOM
import datetime as dt


def _apply_tree_style():
    s = ttk.Style()
    s.configure("Dark.Treeview",
        background="#2b2b2b", foreground="white",
        fieldbackground="#2b2b2b", rowheight=28, font=("Arial",11))
    s.configure("Dark.Treeview.Heading",
        background="#1a1a2e", foreground="#7EB3FF",
        font=("Arial",11,"bold"), relief="flat")
    s.map("Dark.Treeview", background=[("selected","#1f6aa5")])


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.controller = controller
        _apply_tree_style()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Tableau de bord",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(22,2))
        ctk.CTkLabel(self, text=f"Bienvenue sur {BOUTIQUE_NOM}",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(
            anchor="w", padx=30, pady=(0,18))

        # ── Cartes ────────────────────────────────────────────
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=30)
        CARDS = [
            ("Produits",       "0", "#1565C0", "📦"),
            ("Total en stock", "0", "#1b7a34", "📊"),
            ("Stock bas",      "0", "#b71c1c", "⚠️"),
            ("Ventes du jour", "0", "#6a1b9a", "💰"),
        ]
        self._card_vals = []
        for title, val, color, icon in CARDS:
            card = ctk.CTkFrame(row, corner_radius=14, fg_color=(color, color))
            card.pack(side="left", expand=True, fill="x", padx=8, pady=8)
            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=24),
                         text_color="white").pack(pady=(16,4))
            lv = ctk.CTkLabel(card, text=val,
                              font=ctk.CTkFont(size=32, weight="bold"),
                              text_color="white")
            lv.pack()
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=12),
                         text_color="white").pack(pady=(2,16))
            self._card_vals.append(lv)

        # ── Derniers approvisionnements ────────────────────────
        ctk.CTkLabel(self, text="Derniers approvisionnements",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(
            anchor="w", padx=30, pady=(18,4))
        self.tree1 = self._mktree(
            ("Date","Produit","Quantité","Total"), (130,220,90,150), 7)

        # ── Produits stock bas ─────────────────────────────────
        ctk.CTkLabel(self, text="Produits en stock bas",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color="#e74c3c").pack(anchor="w", padx=30, pady=(14,4))
        self.tree2 = self._mktree(
            ("Produit","Stock actuel","Minimum"), (220,140,140), 4)

    def _mktree(self, cols, widths, height):
        t = ttk.Treeview(self, columns=cols, show="headings",
                          height=height, style="Dark.Treeview")
        for c, w in zip(cols, widths):
            t.heading(c, text=c); t.column(c, width=w, anchor="center")
        t.pack(fill="x", padx=30, pady=4)
        return t

    def refresh(self):
        conn = get_connection()
        nb_p  = conn.execute("SELECT COUNT(*) FROM produits").fetchone()[0]
        total = conn.execute("SELECT COALESCE(SUM(stock_actuel),0) FROM produits").fetchone()[0]
        alrt  = conn.execute(
            "SELECT COUNT(*) FROM produits WHERE stock_actuel<=stock_minimum").fetchone()[0]
        today = dt.date.today().strftime("%Y-%m-%d")
        vj    = conn.execute(
            "SELECT COUNT(*) FROM ventes WHERE DATE(date_vente)=?", (today,)).fetchone()[0]
        for lv, v in zip(self._card_vals, [nb_p, total, alrt, vj]):
            lv.configure(text=str(v))

        for r in self.tree1.get_children(): self.tree1.delete(r)
        for r in conn.execute("""
            SELECT a.date_achat,
                   COALESCE(p.nom, a.produit_nom, '[supprimé]'),
                   a.quantite, a.prix_total
            FROM achats a LEFT JOIN produits p ON a.produit_id=p.id
            ORDER BY a.date_achat DESC LIMIT 8
        """).fetchall():
            self.tree1.insert("","end", values=(
                str(r[0])[:16], r[1], r[2], f"{r[3]:,.0f} {MONNAIE}"))

        for r in self.tree2.get_children(): self.tree2.delete(r)
        for r in conn.execute(
            "SELECT nom,stock_actuel,stock_minimum FROM produits "
            "WHERE stock_actuel<=stock_minimum ORDER BY nom"
        ).fetchall():
            self.tree2.insert("","end", values=(r[0], r[1], r[2]))
        conn.close()
