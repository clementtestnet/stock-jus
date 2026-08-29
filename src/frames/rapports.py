# frames/rapports.py — LEFT JOIN partout, pas de perte si produit supprimé
import customtkinter as ctk
import tkinter.ttk as ttk
import tkinter as tk
from datetime import date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from config import MONNAIE


def _apply_tree_style():
    s = ttk.Style()
    s.configure("Dark.Treeview",
        background="#2b2b2b", foreground="white",
        fieldbackground="#2b2b2b", rowheight=28, font=("Arial",11))
    s.configure("Dark.Treeview.Heading",
        background="#1a1a2e", foreground="#7EB3FF",
        font=("Arial",11,"bold"), relief="flat")
    s.map("Dark.Treeview", background=[("selected","#1f6aa5")])


class RapportsFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.controller = controller
        _apply_tree_style()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Rapports & Statistiques",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(22,10))
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=30, pady=5)
        self.t1 = ctk.CTkFrame(nb, corner_radius=0)
        self.t2 = ctk.CTkFrame(nb, corner_radius=0)
        self.t3 = ctk.CTkFrame(nb, corner_radius=0)
        nb.add(self.t1, text="  État du stock  ")
        nb.add(self.t2, text="  Achats par période  ")
        nb.add(self.t3, text="  Top produits  ")
        self._build_t1(); self._build_t2(); self._build_t3()

    def _mktree(self, parent, cols, widths, height=13):
        t = ttk.Treeview(parent, columns=cols, show="headings",
                          height=height, style="Dark.Treeview")
        for c, w in zip(cols, widths):
            t.heading(c, text=c); t.column(c, width=w, anchor="center")
        t.pack(fill="both", expand=True, padx=10, pady=5)
        return t

    # ── Onglet 1 : Stock ─────────────────────────────────────────────────
    def _build_t1(self):
        ctk.CTkButton(self.t1, text="🔄 Actualiser", width=120, height=32,
                      command=self._load_t1).pack(anchor="ne", padx=10, pady=8)
        self.tr1 = self._mktree(self.t1,
            ("Produit","Unité","Stock","Min","Prix","Valeur","Statut"),
            [180,70,80,70,100,120,80])
        self.tr1.tag_configure("bas", foreground="#e74c3c")
        self.tr1.tag_configure("ok",  foreground="#27ae60")
        self.lbl_t1 = ctk.CTkLabel(self.t1, text="",
                                    font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_t1.pack(anchor="e", padx=15, pady=4)

    def _load_t1(self):
        for r in self.tr1.get_children(): self.tr1.delete(r)
        conn = get_connection()
        rows = conn.execute(
            "SELECT nom,unite,stock_actuel,stock_minimum,prix_vente "
            "FROM produits ORDER BY nom").fetchall()
        conn.close()
        total = 0
        for r in rows:
            val = r[2]*r[4]; total += val
            ok  = r[2] > r[3]
            self.tr1.insert("","end", values=(
                r[0],r[1],r[2],r[3],f"{r[4]:.0f}",
                f"{val:,.0f}","OK" if ok else "Bas"),
                tags=("ok",) if ok else ("bas",))
        self.lbl_t1.configure(
            text=f"💰 Valeur totale stock: {total:,.0f} {MONNAIE}")

    # ── Onglet 2 : Achats par période ────────────────────────────────────
    def _build_t2(self):
        ff = ctk.CTkFrame(self.t2, fg_color="transparent")
        ff.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(ff, text="Du :", font=ctk.CTkFont(size=12)).pack(side="left")
        self.d1 = tk.StringVar(value=f"{date.today().year}-01-01")
        ctk.CTkEntry(ff, textvariable=self.d1, width=110, height=32).pack(
            side="left", padx=5)
        ctk.CTkLabel(ff, text="Au :", font=ctk.CTkFont(size=12)).pack(
            side="left", padx=(10,0))
        self.d2 = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        ctk.CTkEntry(ff, textvariable=self.d2, width=110, height=32).pack(
            side="left", padx=5)
        ctk.CTkButton(ff, text="📊 Calculer", width=110, height=32,
                      fg_color="#1e8449", hover_color="#145a32",
                      command=self._load_t2).pack(side="left", padx=12)
        self.tr2 = self._mktree(self.t2,
            ("Produit","Nb achats","Qté totale","Total dépensé","Prix moyen"),
            [200,90,120,140,120])
        self.lbl_t2 = ctk.CTkLabel(self.t2, text="",
                                    font=ctk.CTkFont(size=12, weight="bold"),
                                    text_color="#e74c3c")
        self.lbl_t2.pack(anchor="e", padx=15, pady=4)

    def _load_t2(self):
        for r in self.tr2.get_children(): self.tr2.delete(r)
        conn = get_connection()
        # LEFT JOIN — inclure achats même si produit supprimé
        rows = conn.execute("""
            SELECT COALESCE(p.nom, a.produit_nom, '[supprimé]'),
                   COUNT(a.id), SUM(a.quantite), SUM(a.prix_total),
                   ROUND(SUM(a.prix_total)/SUM(a.quantite),2)
            FROM achats a LEFT JOIN produits p ON a.produit_id=p.id
            WHERE a.date_achat BETWEEN ? AND ?
            GROUP BY COALESCE(p.nom, a.produit_nom)
            ORDER BY SUM(a.prix_total) DESC
        """, (self.d1.get(), self.d2.get()+" 23:59:59")).fetchall()
        conn.close()
        total = 0
        for r in rows:
            self.tr2.insert("","end", values=(
                r[0],r[1],r[2],f"{r[3]:,.0f} {MONNAIE}",f"{r[4]:.0f}"))
            total += r[3]
        self.lbl_t2.configure(
            text=f"💸 Total dépenses: {total:,.0f} {MONNAIE}")

    # ── Onglet 3 : Top produits ──────────────────────────────────────────
    def _build_t3(self):
        ctk.CTkButton(self.t3, text="🔄 Actualiser", width=120, height=32,
                      command=self._load_t3).pack(anchor="ne", padx=10, pady=8)
        self.tr3 = self._mktree(self.t3,
            ("Rang","Produit","Total acheté","Total dépensé","Dernière livraison"),
            [60,220,140,160,140])

    def _load_t3(self):
        for r in self.tr3.get_children(): self.tr3.delete(r)
        conn = get_connection()
        # LEFT JOIN — inclure même si produit supprimé
        rows = conn.execute("""
            SELECT COALESCE(p.nom, a.produit_nom, '[supprimé]'),
                   SUM(a.quantite), SUM(a.prix_total), MAX(a.date_achat)
            FROM achats a LEFT JOIN produits p ON a.produit_id=p.id
            GROUP BY COALESCE(p.nom, a.produit_nom)
            ORDER BY SUM(a.quantite) DESC LIMIT 20
        """).fetchall()
        conn.close()
        medals = ["🥇","🥈","🥉"]
        for i, r in enumerate(rows, 1):
            m = medals[i-1] if i <= 3 else str(i)
            self.tr3.insert("","end", values=(
                m, r[0], r[1], f"{r[2]:,.0f} {MONNAIE}", str(r[3])[:10]))

    def refresh(self):
        self._load_t1(); self._load_t3()
