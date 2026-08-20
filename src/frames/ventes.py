# ventes.py — Frame ventes pour l'admin
import tkinter as tk
from tkinter import ttk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from config import MONNAIE, UNITE_DEFAULT

class VentesFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.controller = controller
        self._build()

    def _build(self):
        tk.Label(self, text="Historique des Ventes", font=("Arial",18,"bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(anchor="w",padx=30,pady=(20,5))

        ff = tk.Frame(self, bg="#f0f4f8"); ff.pack(fill="x",padx=30,pady=5)
        tk.Label(ff,text="Produit:",bg="#f0f4f8",font=("Arial",9)).pack(side="left")
        self.fp = tk.StringVar(value="Tous")
        self.cbp = ttk.Combobox(ff,textvariable=self.fp,width=20,state="readonly")
        self.cbp.pack(side="left",padx=5)
        tk.Button(ff,text="Filtrer",bg="#4a90d9",fg="white",relief="flat",padx=10,
                  cursor="hand2",command=self._load).pack(side="left",padx=10)
        tk.Button(ff,text="Tout afficher",bg="#667788",fg="white",relief="flat",padx=10,
                  cursor="hand2",command=self.refresh).pack(side="left")

        cols = ("Date","Produit","Quantite","Offerts","Prix unit.","Total","Client","Notes")
        self.tree = ttk.Treeview(self,columns=cols,show="headings",height=16)
        for c,w in zip(cols,[130,160,75,65,100,120,130,160]):
            self.tree.heading(c,text=c); self.tree.column(c,width=w,anchor="center")
        self.tree.pack(fill="both",expand=True,padx=30,pady=5)

        self.lbl = tk.Label(self,text="Total recettes: 0",font=("Arial",10,"bold"),bg="#f0f4f8",fg="#27ae60")
        self.lbl.pack(anchor="e",padx=30,pady=5)

    def refresh(self):
        conn = get_connection()
        self.cbp["values"] = ["Tous"]+[r[0] for r in conn.execute("SELECT nom FROM produits ORDER BY nom").fetchall()]
        conn.close(); self.fp.set("Tous"); self._load()

    def _load(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        q = """SELECT v.date_vente,p.nom,v.quantite,COALESCE(v.paquets_offerts,0),
                      v.prix_unitaire,v.prix_total,COALESCE(v.client,'-'),COALESCE(v.notes,'-')
               FROM ventes v JOIN produits p ON v.produit_id=p.id"""
        filters=[]; params=[]
        if self.fp.get()!="Tous": filters.append("p.nom=?"); params.append(self.fp.get())
        if filters: q+=" WHERE "+" AND ".join(filters)
        q+=" ORDER BY v.date_vente DESC"
        conn = get_connection(); rows=conn.execute(q,params).fetchall(); conn.close()
        total=0
        for r in rows:
            self.tree.insert("","end",values=(str(r[0])[:16],r[1],r[2],
                f"+{r[3]}" if r[3]>0 else "-",f"{r[4]:.0f}",f"{r[5]:,.0f} {MONNAIE}",r[6],r[7]))
            total+=r[5]
        self.lbl.config(text=f"Total recettes: {total:,.0f} {MONNAIE}")
