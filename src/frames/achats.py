# achats.py — MODERNE CustomTkinter
import customtkinter as ctk
import tkinter.ttk as ttk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from config import MONNAIE, UNITE_DEFAULT


class AchatsFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.controller   = controller
        self._produit_map = {}
        self._fourn_map   = {}
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Nouvel Achat / Approvisionnement",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=30, pady=(22,2))
        ctk.CTkLabel(self, text="Enregistrez une entrée de stock",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", padx=30, pady=(0,14))

        card = ctk.CTkFrame(self, corner_radius=14)
        card.pack(fill="x", padx=30, pady=5)

        # Produit
        r0 = ctk.CTkFrame(card, fg_color="transparent")
        r0.pack(fill="x", padx=20, pady=(16,4))
        ctk.CTkLabel(r0, text="Produit *", font=ctk.CTkFont(size=12, weight="bold"),
                     width=200, anchor="w").pack(side="left")
        self.pvar = tk.StringVar()
        self.pcb  = ttk.Combobox(r0, textvariable=self.pvar, width=32, state="readonly")
        self.pcb.pack(side="left", padx=8)

        # Fournisseur
        r1 = ctk.CTkFrame(card, fg_color="transparent")
        r1.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(r1, text="Fournisseur", font=ctk.CTkFont(size=12, weight="bold"),
                     width=200, anchor="w").pack(side="left")
        self.fvar = tk.StringVar()
        self.fcb  = ttk.Combobox(r1, textvariable=self.fvar, width=32, state="readonly")
        self.fcb.pack(side="left", padx=8)

        self.vars = {"produit": self.pvar, "fournisseur": self.fvar}
        input_fields = [
            (f"Quantité ({UNITE_DEFAULT}s) *", "quantite"),
            (f"Prix unitaire ({MONNAIE}) *",   "prix_unit"),
            ("Date",                            "date"),
            ("Notes",                           "notes"),
        ]
        for label, key in input_fields:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12, weight="bold"),
                         width=200, anchor="w").pack(side="left")
            var = tk.StringVar(); self.vars[key] = var
            e = ctk.CTkEntry(row, textvariable=var, width=280, height=34, corner_radius=8)
            e.pack(side="left", padx=8)
            if key == "date": var.set(datetime.now().strftime("%Y-%m-%d"))
            if key in ("quantite","prix_unit"): e.bind("<KeyRelease>", self._upd)

        # Total
        tf = ctk.CTkFrame(card, corner_radius=10, fg_color=("#e8f8f0","#0d2e1c"))
        tf.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(tf, text="Prix total :",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=15, pady=10)
        self.total_lbl = ctk.CTkLabel(tf, text=f"0 {MONNAIE}",
                                       font=ctk.CTkFont(size=18, weight="bold"),
                                       text_color="#27ae60")
        self.total_lbl.pack(side="left")

        ctk.CTkButton(card, text="✅ Enregistrer l'achat",
                      height=44, corner_radius=10,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color="#1e8449", hover_color="#145a32",
                      command=self._save).pack(fill="x", padx=20, pady=(8, 18))

    def _upd(self, _=None):
        try:
            v = int(self.vars["quantite"].get()) * float(self.vars["prix_unit"].get())
            self.total_lbl.configure(text=f"{v:,.0f} {MONNAIE}")
        except:
            self.total_lbl.configure(text=f"0 {MONNAIE}")

    def refresh(self):
        conn = get_connection()
        self._produit_map = {r[1]:r[0] for r in conn.execute(
            "SELECT id,nom FROM produits ORDER BY nom").fetchall()}
        self._fourn_map   = {r[1]:r[0] for r in conn.execute(
            "SELECT id,nom FROM fournisseurs ORDER BY nom").fetchall()}
        conn.close()
        self.pcb["values"] = list(self._produit_map.keys())
        self.fcb["values"] = ["-Aucun-"] + list(self._fourn_map.keys())
        self.fcb.set("-Aucun-")

    def _save(self):
        pnom = self.vars["produit"].get()
        if not pnom or pnom not in self._produit_map:
            messagebox.showerror("Erreur","Sélectionnez un produit."); return
        try:
            qty  = int(self.vars["quantite"].get())
            prix = float(self.vars["prix_unit"].get())
            if qty <= 0 or prix < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erreur","Quantité et prix invalides."); return
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
        messagebox.showinfo("Succès", f"✅ {pnom}: +{qty} {UNITE_DEFAULT}s\nTotal: {total:,.0f} {MONNAIE}")
        self.vars["quantite"].set(""); self.vars["prix_unit"].set("")
        self.vars["notes"].set(""); self.total_lbl.configure(text=f"0 {MONNAIE}")
