# historique.py — MODERNE CustomTkinter
import customtkinter as ctk
import tkinter.ttk as ttk
import tkinter as tk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from config import MONNAIE


def _style_tree():
    s = ttk.Style()
    s.configure("Dark.Treeview",
        background="#2b2b2b", foreground="white",
        fieldbackground="#2b2b2b", rowheight=28, font=("Arial",11))
    s.configure("Dark.Treeview.Heading",
        background="#1a1a2e", foreground="#7EB3FF",
        font=("Arial",11,"bold"), relief="flat")
    s.map("Dark.Treeview", background=[("selected","#1f6aa5")])


class HistoriqueFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.controller = controller
        _style_tree()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Historique des Approvisionnements",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(22,8))

        # Filtres
        ff = ctk.CTkFrame(self, fg_color="transparent")
        ff.pack(fill="x", padx=30, pady=5)
        ctk.CTkLabel(ff, text="Produit :", font=ctk.CTkFont(size=12)).pack(side="left")
        self.fp = tk.StringVar(value="Tous")
        self.cbp = ttk.Combobox(ff, textvariable=self.fp, width=20, state="readonly")
        self.cbp.pack(side="left", padx=6)
        ctk.CTkLabel(ff, text="Fournisseur :", font=ctk.CTkFont(size=12)).pack(side="left", padx=(12,0))
        self.ff2 = tk.StringVar(value="Tous")
        self.cbf = ttk.Combobox(ff, textvariable=self.ff2, width=20, state="readonly")
        self.cbf.pack(side="left", padx=6)
        ctk.CTkButton(ff, text="🔍 Filtrer", width=100, height=32,
                      command=self._load).pack(side="left", padx=8)
        ctk.CTkButton(ff, text="🔄 Tout", width=90, height=32,
                      fg_color="gray40", hover_color="gray30",
                      command=self.refresh).pack(side="left", padx=4)

        # Tableau
        cols = ("Date","Produit","Fournisseur","Quantité","Prix unit.","Total","Notes")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  height=15, style="Dark.Treeview")
        for c, w in zip(cols, [130,160,140,80,110,120,180]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=30, pady=5)

        self.lbl = ctk.CTkLabel(self, text="Total: 0",
                                 font=ctk.CTkFont(size=13, weight="bold"),
                                 text_color="#27ae60")
        self.lbl.pack(anchor="e", padx=30, pady=6)

    def refresh(self):
        conn = get_connection()
        self.cbp["values"] = ["Tous"]+[r[0] for r in conn.execute(
            "SELECT nom FROM produits ORDER BY nom").fetchall()]
        self.cbf["values"] = ["Tous"]+[r[0] for r in conn.execute(
            "SELECT nom FROM fournisseurs ORDER BY nom").fetchall()]
        conn.close(); self.fp.set("Tous"); self.ff2.set("Tous"); self._load()

    def _load(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        q = """SELECT a.date_achat,
                      COALESCE(p.nom, a.produit_nom, '[produit supprime]'),
                      COALESCE(f.nom,'-'),a.quantite,
                      a.prix_unitaire,a.prix_total,COALESCE(a.notes,'-')
               FROM achats a LEFT JOIN produits p ON a.produit_id=p.id
               LEFT JOIN fournisseurs f ON a.fournisseur_id=f.id"""
        filters=[]; params=[]
        if self.fp.get()!="Tous": filters.append("COALESCE(p.nom, a.produit_nom)=?"); params.append(self.fp.get())
        if self.ff2.get()!="Tous": filters.append("f.nom=?"); params.append(self.ff2.get())
        if filters: q+=" WHERE "+" AND ".join(filters)
        q+=" ORDER BY a.date_achat DESC"
        conn = get_connection(); rows=conn.execute(q,params).fetchall(); conn.close()
        total=0
        for r in rows:
            self.tree.insert("","end", values=(
                str(r[0])[:16],r[1],r[2],r[3],f"{r[4]:.0f}",f"{r[5]:,.0f} {MONNAIE}",r[6]))
            total+=r[5]
        self.lbl.configure(text=f"💰 Total: {total:,.0f} {MONNAIE}")
