# frames/achats.py — Approvisionnement avec support demi-paquet
import customtkinter as ctk
import tkinter.ttk as ttk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from config import MONNAIE, UNITE_DEFAULT


def fq(q):
    q = float(q)
    return str(int(q)) if q == int(q) else str(q)


class AchatsFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.controller   = controller
        self._produit_map = {}
        self._qty_entry   = None
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Nouvel Achat / Approvisionnement",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(22,2))
        ctk.CTkLabel(self, text="Entrez la quantité reçue (ex: 10 ou 0.5 pour demi-paquet)",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(
            anchor="w", padx=30, pady=(0,14))

        card = ctk.CTkFrame(self, corner_radius=14)
        card.pack(fill="x", padx=30, pady=5)

        # Produit
        r0 = ctk.CTkFrame(card, fg_color="transparent")
        r0.pack(fill="x", padx=20, pady=(16,4))
        ctk.CTkLabel(r0, text="Produit *",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     width=220, anchor="w").pack(side="left")
        self.pvar = tk.StringVar()
        self.pcb  = ttk.Combobox(r0, textvariable=self.pvar, width=30, state="readonly")
        self.pcb.pack(side="left", padx=8)
        self.pcb.bind("<<ComboboxSelected>>", self._on_produit)
        self.lbl_stock = ctk.CTkLabel(r0, text="",
                                       font=ctk.CTkFont(size=11),
                                       text_color="#27ae60", width=200, anchor="w")
        self.lbl_stock.pack(side="left", padx=8)

        self.vars = {"produit": self.pvar}
        for label, key in [
            (f"Quantité ({UNITE_DEFAULT}s) *  ex: 1 ou 0,5", "quantite"),
            (f"Prix unitaire ({MONNAIE})",                    "prix_unit"),
            ("Date",                                           "date"),
            ("Notes",                                          "notes"),
        ]:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(row, text=label,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         width=280, anchor="w").pack(side="left")
            var = tk.StringVar(); self.vars[key] = var
            e = ctk.CTkEntry(row, textvariable=var, width=240, height=34, corner_radius=8)
            e.pack(side="left", padx=8)
            if key == "date":
                var.set(datetime.now().strftime("%Y-%m-%d"))
            if key == "quantite":
                self._qty_entry = e
                e.bind("<KeyRelease>", self._on_qty_key)
            if key == "prix_unit":
                e.bind("<KeyRelease>", self._upd)
                ctk.CTkLabel(row, text="(prédéfini, modifiable)",
                             font=ctk.CTkFont(size=10), text_color="gray").pack(side="left", padx=4)

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
                      command=self._save).pack(fill="x", padx=20, pady=(8,18))

    # ── helpers ──────────────────────────────────────────────────────────────

    def _on_qty_key(self, _=None):
        val = self.vars["quantite"].get()
        if ',' in val:
            pos = self._qty_entry.index('insert')
            self.vars["quantite"].set(val.replace(',', '.'))
            try: self._qty_entry.icursor(pos)
            except: pass
        self._upd()

    def _parse_qty(self):
        try:
            q = round(float(self.vars["quantite"].get().replace(',', '.')), 1)
            return q if q > 0 else None
        except (ValueError, TypeError):
            return None

    def _on_produit(self, _=None):
        info = self._produit_map.get(self.pvar.get())
        if not info: return
        self.vars["prix_unit"].set(f"{info['prix']:.0f}")
        stock = float(info["stock"])
        color = "#27ae60" if stock > 0 else "#e74c3c"
        self.lbl_stock.configure(
            text=f"Stock actuel: {fq(stock)} {UNITE_DEFAULT}s", text_color=color)
        self._upd()

    def _upd(self, _=None):
        qty = self._parse_qty()
        try:
            if qty is None: raise ValueError
            v = qty * float(self.vars["prix_unit"].get())
            self.total_lbl.configure(text=f"{v:,.0f} {MONNAIE}")
        except (ValueError, TypeError):
            self.total_lbl.configure(text=f"0 {MONNAIE}")

    def refresh(self):
        conn = get_connection()
        rows = conn.execute(
            "SELECT id,nom,prix_vente,stock_actuel FROM produits ORDER BY nom").fetchall()
        conn.close()
        self._produit_map = {r[1]:{"id":r[0],"prix":r[2],"stock":r[3]} for r in rows}
        self.pcb["values"] = list(self._produit_map.keys())

    def _save(self):
        pnom = self.vars["produit"].get()
        if not pnom or pnom not in self._produit_map:
            messagebox.showerror("Erreur","Sélectionnez un produit."); return
        qty = self._parse_qty()
        if qty is None:
            messagebox.showerror("Erreur","Quantité invalide (ex: 1 ou 0.5)."); return
        try:
            prix = float(self.vars["prix_unit"].get())
            if prix < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erreur","Prix invalide."); return

        pid   = self._produit_map[pnom]["id"]
        total = qty * prix
        date  = self.vars["date"].get() or datetime.now().strftime("%Y-%m-%d")
        conn  = get_connection()
        conn.execute(
            "INSERT INTO achats "
            "(produit_id,produit_nom,quantite,prix_unitaire,prix_total,date_achat,notes) "
            "VALUES (?,?,?,?,?,?,?)",
            (pid, pnom, qty, prix, total, date, self.vars["notes"].get()))
        conn.execute(
            "UPDATE produits SET stock_actuel=stock_actuel+? WHERE id=?", (qty, pid))
        conn.execute(
            "INSERT INTO mouvements (produit_id,type,quantite,motif) VALUES (?,?,?,?)",
            (pid, "entree", qty, f"Achat du {date}"))
        conn.commit(); conn.close()
        messagebox.showinfo("Succès",
            f"✅ {pnom}: +{fq(qty)} {UNITE_DEFAULT}s\nTotal: {total:,.0f} {MONNAIE}")
        self.vars["quantite"].set(""); self.vars["notes"].set("")
        self.lbl_stock.configure(text="")
        self.total_lbl.configure(text=f"0 {MONNAIE}")
        self.refresh()
