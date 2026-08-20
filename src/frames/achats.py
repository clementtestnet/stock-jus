# achats.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from config import MONNAIE, UNITE_DEFAULT

class AchatsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.controller = controller
        self._produit_map = {}
        self._fourn_map   = {}
        self._build()

    def _build(self):
        tk.Label(self, text="Nouvel Achat / Approvisionnement",
                 font=("Arial",18,"bold"), bg="#f0f4f8", fg="#1a2940").pack(anchor="w",padx=30,pady=(20,3))
        tk.Label(self, text="Enregistrez une entree de stock",
                 font=("Arial",9), bg="#f0f4f8", fg="#667788").pack(anchor="w",padx=30,pady=(0,15))

        card = tk.Frame(self, bg="white", highlightbackground="#dde3ed", highlightthickness=1)
        card.pack(fill="x", padx=30, pady=5)

        fields = [
            ("Produit *","produit"), ("Fournisseur","fournisseur"),
            (f"Quantite ({UNITE_DEFAULT}s) *","quantite"),
            (f"Prix unitaire ({MONNAIE}) *","prix_unit"),
            ("Date","date"), ("Notes","notes"),
        ]
        self.vars = {}
        for i,(label,key) in enumerate(fields):
            tk.Label(card, text=label, font=("Arial",9,"bold"),
                     bg="white", fg="#334455").grid(row=i,column=0,sticky="w",padx=20,pady=8)
            if key == "produit":
                self.pvar = tk.StringVar(); self.vars[key]=self.pvar
                self.pcb  = ttk.Combobox(card, textvariable=self.pvar, width=35, state="readonly")
                self.pcb.grid(row=i,column=1,padx=10,pady=8,sticky="w")
            elif key == "fournisseur":
                self.fvar = tk.StringVar(); self.vars[key]=self.fvar
                self.fcb  = ttk.Combobox(card, textvariable=self.fvar, width=35, state="readonly")
                self.fcb.grid(row=i,column=1,padx=10,pady=8,sticky="w")
            else:
                var = tk.StringVar(); self.vars[key]=var
                e = tk.Entry(card, textvariable=var, width=37, font=("Arial",10))
                e.grid(row=i,column=1,padx=10,pady=8,sticky="w")
                if key=="date": var.set(datetime.now().strftime("%Y-%m-%d"))
                if key in ("quantite","prix_unit"): e.bind("<KeyRelease>",self._upd)

        tf = tk.Frame(card, bg="#eaf4fb")
        tf.grid(row=len(fields),column=0,columnspan=2,sticky="ew",padx=20,pady=8)
        tk.Label(tf,text="Prix total:",font=("Arial",11,"bold"),bg="#eaf4fb",fg="#1a2940").pack(side="left",padx=15,pady=8)
        self.total_lbl = tk.Label(tf,text=f"0 {MONNAIE}",font=("Arial",14,"bold"),bg="#eaf4fb",fg="#27ae60")
        self.total_lbl.pack(side="left")

        tk.Button(card, text="Enregistrer l'achat", font=("Arial",11,"bold"),
                  bg="#27ae60", fg="white", relief="flat", padx=20, pady=8,
                  cursor="hand2", command=self._save).grid(
                  row=len(fields)+1,column=0,columnspan=2,pady=15)

    def _upd(self, event=None):
        try:
            self.total_lbl.config(text=f"{int(self.vars['quantite'].get())*float(self.vars['prix_unit'].get()):,.0f} {MONNAIE}")
        except: self.total_lbl.config(text=f"0 {MONNAIE}")

    def refresh(self):
        conn = get_connection()
        self._produit_map = {r[1]:r[0] for r in conn.execute("SELECT id,nom FROM produits ORDER BY nom").fetchall()}
        self._fourn_map   = {r[1]:r[0] for r in conn.execute("SELECT id,nom FROM fournisseurs ORDER BY nom").fetchall()}
        conn.close()
        self.pcb["values"] = list(self._produit_map.keys())
        self.fcb["values"] = ["-Aucun-"] + list(self._fourn_map.keys())
        self.fcb.set("-Aucun-")

    def _save(self):
        pnom = self.vars["produit"].get()
        if not pnom or pnom not in self._produit_map:
            messagebox.showerror("Erreur","Selectionnez un produit."); return
        try:
            qty=int(self.vars["quantite"].get()); prix=float(self.vars["prix_unit"].get())
            if qty<=0 or prix<0: raise ValueError
        except ValueError:
            messagebox.showerror("Erreur","Quantite et prix invalides."); return
        pid   = self._produit_map[pnom]
        fnom  = self.vars["fournisseur"].get()
        fid   = self._fourn_map.get(fnom)
        total = qty * prix
        date  = self.vars["date"].get() or datetime.now().strftime("%Y-%m-%d")
        conn  = get_connection()
        conn.execute("INSERT INTO achats (produit_id,fournisseur_id,quantite,prix_unitaire,prix_total,date_achat,notes) VALUES (?,?,?,?,?,?,?)",
                     (pid,fid,qty,prix,total,date,self.vars["notes"].get()))
        conn.execute("UPDATE produits SET stock_actuel=stock_actuel+? WHERE id=?", (qty,pid))
        conn.execute("INSERT INTO mouvements (produit_id,type,quantite,motif) VALUES (?,?,?,?)",
                     (pid,"entree",qty,f"Achat du {date}"))
        conn.commit(); conn.close()
        messagebox.showinfo("Succes", f"{pnom}: +{qty} {UNITE_DEFAULT}s\nTotal: {total:,.0f} {MONNAIE}")
        self.vars["quantite"].set(""); self.vars["prix_unit"].set("")
        self.vars["notes"].set(""); self.total_lbl.config(text=f"0 {MONNAIE}")
