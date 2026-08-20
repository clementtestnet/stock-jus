# rapports.py
import tkinter as tk
from tkinter import ttk
from datetime import date
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from config import MONNAIE

class RapportsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.controller = controller
        self._build()

    def _build(self):
        tk.Label(self, text="Rapports & Statistiques", font=("Arial",18,"bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(anchor="w",padx=30,pady=(20,5))
        nb = ttk.Notebook(self)
        nb.pack(fill="both",expand=True,padx=30,pady=10)

        self.t1 = tk.Frame(nb, bg="#f0f4f8"); nb.add(self.t1, text="Etat du stock")
        self.t2 = tk.Frame(nb, bg="#f0f4f8"); nb.add(self.t2, text="Achats par periode")
        self.t3 = tk.Frame(nb, bg="#f0f4f8"); nb.add(self.t3, text="Top produits")
        self._build_t1(); self._build_t2(); self._build_t3()

    def _build_t1(self):
        tk.Button(self.t1,text="Actualiser",bg="#4a90d9",fg="white",relief="flat",padx=10,
                  cursor="hand2",command=self._load_t1).pack(anchor="ne",padx=10,pady=10)
        cols=("Produit","Unite","Stock","Min","Prix","Valeur","Statut")
        self.tr1=ttk.Treeview(self.t1,columns=cols,show="headings",height=13)
        for c,w in zip(cols,[180,70,80,70,100,120,80]):
            self.tr1.heading(c,text=c); self.tr1.column(c,width=w,anchor="center")
        self.tr1.pack(fill="both",expand=True,padx=10,pady=5)
        self.tr1.tag_configure("bas",foreground="#e74c3c"); self.tr1.tag_configure("ok",foreground="#27ae60")
        self.lbl_t1=tk.Label(self.t1,text="",font=("Arial",10,"bold"),bg="#f0f4f8",fg="#1a2940")
        self.lbl_t1.pack(anchor="e",padx=15,pady=5)

    def _load_t1(self):
        for r in self.tr1.get_children(): self.tr1.delete(r)
        conn=get_connection()
        rows=conn.execute("SELECT nom,unite,stock_actuel,stock_minimum,prix_vente FROM produits ORDER BY nom").fetchall()
        conn.close(); total=0
        for r in rows:
            val=r[2]*r[4]; total+=val; ok=r[2]>r[3]
            self.tr1.insert("","end",values=(r[0],r[1],r[2],r[3],f"{r[4]:.0f}",f"{val:,.0f}","OK" if ok else "Bas"),tags=("ok",) if ok else ("bas",))
        self.lbl_t1.config(text=f"Valeur totale stock: {total:,.0f} {MONNAIE}")

    def _build_t2(self):
        ff=tk.Frame(self.t2,bg="#f0f4f8"); ff.pack(fill="x",padx=10,pady=10)
        tk.Label(ff,text="Du:",bg="#f0f4f8",font=("Arial",9)).pack(side="left")
        self.d1=tk.StringVar(value=f"{date.today().year}-01-01")
        tk.Entry(ff,textvariable=self.d1,width=12).pack(side="left",padx=5)
        tk.Label(ff,text="Au:",bg="#f0f4f8",font=("Arial",9)).pack(side="left",padx=(10,0))
        self.d2=tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        tk.Entry(ff,textvariable=self.d2,width=12).pack(side="left",padx=5)
        tk.Button(ff,text="Calculer",bg="#27ae60",fg="white",relief="flat",padx=10,
                  cursor="hand2",command=self._load_t2).pack(side="left",padx=15)
        cols=("Produit","Nb achats","Quantite totale","Total depense","Prix moyen")
        self.tr2=ttk.Treeview(self.t2,columns=cols,show="headings",height=13)
        for c,w in zip(cols,[200,90,120,140,120]):
            self.tr2.heading(c,text=c); self.tr2.column(c,width=w,anchor="center")
        self.tr2.pack(fill="both",expand=True,padx=10)
        self.lbl_t2=tk.Label(self.t2,text="",font=("Arial",10,"bold"),bg="#f0f4f8",fg="#e74c3c")
        self.lbl_t2.pack(anchor="e",padx=15,pady=5)

    def _load_t2(self):
        for r in self.tr2.get_children(): self.tr2.delete(r)
        conn=get_connection()
        rows=conn.execute("""SELECT p.nom,COUNT(a.id),SUM(a.quantite),SUM(a.prix_total),
            ROUND(SUM(a.prix_total)/SUM(a.quantite),2) FROM achats a JOIN produits p ON a.produit_id=p.id
            WHERE a.date_achat BETWEEN ? AND ? GROUP BY p.id ORDER BY SUM(a.prix_total) DESC""",
            (self.d1.get(), self.d2.get()+" 23:59:59")).fetchall()
        conn.close(); total=0
        for r in rows:
            self.tr2.insert("","end",values=(r[0],r[1],r[2],f"{r[3]:,.0f} {MONNAIE}",f"{r[4]:.0f}"))
            total+=r[3]
        self.lbl_t2.config(text=f"Total depenses: {total:,.0f} {MONNAIE}")

    def _build_t3(self):
        tk.Button(self.t3,text="Actualiser",bg="#4a90d9",fg="white",relief="flat",padx=10,
                  cursor="hand2",command=self._load_t3).pack(anchor="ne",padx=10,pady=10)
        cols=("Rang","Produit","Total achete","Total depense","Derniere livraison")
        self.tr3=ttk.Treeview(self.t3,columns=cols,show="headings",height=13)
        for c,w in zip(cols,[60,220,140,160,140]):
            self.tr3.heading(c,text=c); self.tr3.column(c,width=w,anchor="center")
        self.tr3.pack(fill="both",expand=True,padx=10,pady=5)

    def _load_t3(self):
        for r in self.tr3.get_children(): self.tr3.delete(r)
        conn=get_connection()
        rows=conn.execute("""SELECT p.nom,SUM(a.quantite),SUM(a.prix_total),MAX(a.date_achat)
            FROM achats a JOIN produits p ON a.produit_id=p.id
            GROUP BY p.id ORDER BY SUM(a.quantite) DESC LIMIT 20""").fetchall()
        conn.close()
        for i,r in enumerate(rows,1):
            m=["1er","2eme","3eme"][i-1] if i<=3 else str(i)
            self.tr3.insert("","end",values=(m,r[0],r[1],f"{r[2]:,.0f} {MONNAIE}",str(r[3])[:10]))

    def refresh(self):
        self._load_t1(); self._load_t3()
