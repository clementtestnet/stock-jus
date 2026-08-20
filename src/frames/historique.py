# historique.py
import tkinter as tk
from tkinter import ttk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from config import MONNAIE

class HistoriqueFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.controller = controller
        self._build()

    def _build(self):
        tk.Label(self, text="Historique des Approvisionnements",
                 font=("Arial",18,"bold"), bg="#f0f4f8", fg="#1a2940").pack(anchor="w",padx=30,pady=(20,5))

        ff = tk.Frame(self, bg="#f0f4f8"); ff.pack(fill="x",padx=30,pady=5)
        tk.Label(ff,text="Produit:",bg="#f0f4f8",font=("Arial",9)).pack(side="left")
        self.fp = tk.StringVar(value="Tous")
        self.cbp = ttk.Combobox(ff,textvariable=self.fp,width=20,state="readonly")
        self.cbp.pack(side="left",padx=5)
        tk.Label(ff,text="Fournisseur:",bg="#f0f4f8",font=("Arial",9)).pack(side="left",padx=(15,0))
        self.ff2 = tk.StringVar(value="Tous")
        self.cbf = ttk.Combobox(ff,textvariable=self.ff2,width=20,state="readonly")
        self.cbf.pack(side="left",padx=5)
        tk.Button(ff,text="Filtrer",bg="#4a90d9",fg="white",relief="flat",padx=10,
                  cursor="hand2",command=self._load).pack(side="left",padx=10)
        tk.Button(ff,text="Tout afficher",bg="#667788",fg="white",relief="flat",padx=10,
                  cursor="hand2",command=self.refresh).pack(side="left")

        cols = ("Date","Produit","Fournisseur","Quantite","Prix unit.","Total","Notes")
        self.tree = ttk.Treeview(self,columns=cols,show="headings",height=15)
        for c,w in zip(cols,[130,160,140,80,110,120,180]):
            self.tree.heading(c,text=c); self.tree.column(c,width=w,anchor="center")
        self.tree.pack(fill="both",expand=True,padx=30,pady=5)

        self.lbl = tk.Label(self,text="Total: 0",font=("Arial",10,"bold"),bg="#f0f4f8",fg="#27ae60")
        self.lbl.pack(anchor="e",padx=30,pady=5)

    def refresh(self):
        conn = get_connection()
        self.cbp["values"] = ["Tous"]+[r[0] for r in conn.execute("SELECT nom FROM produits ORDER BY nom").fetchall()]
        self.cbf["values"] = ["Tous"]+[r[0] for r in conn.execute("SELECT nom FROM fournisseurs ORDER BY nom").fetchall()]
        conn.close(); self.fp.set("Tous"); self.ff2.set("Tous"); self._load()

    def _load(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        q = """SELECT a.date_achat,p.nom,COALESCE(f.nom,'-'),a.quantite,
                      a.prix_unitaire,a.prix_total,COALESCE(a.notes,'-')
               FROM achats a JOIN produits p ON a.produit_id=p.id
               LEFT JOIN fournisseurs f ON a.fournisseur_id=f.id"""
        filters=[]; params=[]
        if self.fp.get()!="Tous": filters.append("p.nom=?"); params.append(self.fp.get())
        if self.ff2.get()!="Tous": filters.append("f.nom=?"); params.append(self.ff2.get())
        if filters: q+=" WHERE "+" AND ".join(filters)
        q+=" ORDER BY a.date_achat DESC"
        conn = get_connection(); rows=conn.execute(q,params).fetchall(); conn.close()
        total=0
        for r in rows:
            self.tree.insert("","end",values=(str(r[0])[:16],r[1],r[2],r[3],f"{r[4]:.0f}",f"{r[5]:,.0f} {MONNAIE}",r[6]))
            total+=r[5]
        self.lbl.config(text=f"Total: {total:,.0f} {MONNAIE}")
