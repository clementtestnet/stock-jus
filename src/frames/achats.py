# achats.py — MODERNE CustomTkinter (sans fournisseur, prix prédéfini)
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
        self._produit_map = {}   # nom -> {id, prix_vente}
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Nouvel Achat / Approvisionnement",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(22, 2))
        ctk.CTkLabel(self, text="Enregistrez une entrée de stock",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(
            anchor="w", padx=30, pady=(0, 14))

        card = ctk.CTkFrame(self, corner_radius=14)
        card.pack(fill="x", padx=30, pady=5)

        # ── Produit ────────────────────────────────────────────
        r0 = ctk.CTkFrame(card, fg_color="transparent")
        r0.pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkLabel(r0, text="Produit *",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     width=200, anchor="w").pack(side="left")
        self.pvar = tk.StringVar()
        self.pcb  = ttk.Combobox(r0, textvariable=self.pvar, width=32, state="readonly")
        self.pcb.pack(side="left", padx=8)
        self.pcb.bind("<<ComboboxSelected>>", self._on_produit_select)

        self.lbl_stock = ctk.CTkLabel(r0, text="",
                                       font=ctk.CTkFont(size=11),
                                       text_color="#27ae60", width=180, anchor="w")
        self.lbl_stock.pack(side="left", padx=8)

        # ── Champs ────────────────────────────────────────────
        self.vars = {"produit": self.pvar}
        input_fields = [
            (f"Quantité ({UNITE_DEFAULT}s) *", "quantite"),
            (f"Prix unitaire ({MONNAIE})",     "prix_unit"),  # prédéfini
            ("Date",                            "date"),
            ("Notes",                           "notes"),
        ]
        self._prix_entry = None
        for label, key in input_fields:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(row, text=label,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         width=200, anchor="w").pack(side="left")
            var = tk.StringVar(); self.vars[key] = var
            e = ctk.CTkEntry(row, textvariable=var, width=280, height=34, corner_radius=8)
            e.pack(side="left", padx=8)
            if key == "date":
                var.set(datetime.now().strftime("%Y-%m-%d"))
            if key in ("quantite", "prix_unit"):
                e.bind("<KeyRelease>", self._upd)
            if key == "prix_unit":
                self._prix_entry = e
                # Label indicatif
                self.prix_info = ctk.CTkLabel(row, text="(prédéfini, modifiable si besoin)",
                                               font=ctk.CTkFont(size=10),
                                               text_color="gray")
                self.prix_info.pack(side="left", padx=4)

        # ── Total ─────────────────────────────────────────────
        tf = ctk.CTkFrame(card, corner_radius=10, fg_color=("#e8f8f0", "#0d2e1c"))
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

    # ── Callbacks ─────────────────────────────────────────────

    def _on_produit_select(self, _=None):
        nom = self.pvar.get()
        info = self._produit_map.get(nom)
        if not info:
            return
        # Prix prédéfini automatiquement
        self.vars["prix_unit"].set(f"{info['prix']:.0f}")
        # Affichage stock
        color = "#27ae60" if info["stock"] > 0 else "#e74c3c"
        self.lbl_stock.configure(
            text=f"Stock actuel: {info['stock']} {UNITE_DEFAULT}s", text_color=color)
        self._upd()

    def _upd(self, _=None):
        try:
            v = int(self.vars["quantite"].get()) * float(self.vars["prix_unit"].get())
            self.total_lbl.configure(text=f"{v:,.0f} {MONNAIE}")
        except:
            self.total_lbl.configure(text=f"0 {MONNAIE}")

    def refresh(self):
        conn = get_connection()
        rows = conn.execute(
            "SELECT id,nom,prix_vente,stock_actuel FROM produits ORDER BY nom").fetchall()
        conn.close()
        self._produit_map = {r[1]: {"id": r[0], "prix": r[2], "stock": r[3]} for r in rows}
        self.pcb["values"] = list(self._produit_map.keys())

    def _save(self):
        pnom = self.vars["produit"].get()
        if not pnom or pnom not in self._produit_map:
            messagebox.showerror("Erreur", "Sélectionnez un produit."); return
        try:
            qty  = int(self.vars["quantite"].get())
            prix = float(self.vars["prix_unit"].get())
            if qty <= 0 or prix < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Quantité et prix invalides."); return

        pid   = self._produit_map[pnom]["id"]
        total = qty * prix
        date  = self.vars["date"].get() or datetime.now().strftime("%Y-%m-%d")
        conn  = get_connection()
        conn.execute(
            "INSERT INTO achats (produit_id, produit_nom, fournisseur_id, quantite, prix_unitaire, prix_total, date_achat, notes) VALUES (?,?,?,?,?,?,?,?)",
            (pid, pnom, None, qty, prix, total, date, self.vars["notes"].get()))
        conn.execute("UPDATE produits SET stock_actuel=stock_actuel+? WHERE id=?", (qty, pid))
        conn.execute("INSERT INTO mouvements (produit_id,type,quantite,motif) VALUES (?,?,?,?)",
                     (pid, "entree", qty, f"Achat du {date}"))
        conn.commit(); conn.close()

        messagebox.showinfo("Succès",
                            f"✅ {pnom}: +{qty} {UNITE_DEFAULT}s\nTotal: {total:,.0f} {MONNAIE}")
        self.vars["quantite"].set("")
        self.vars["notes"].set("")
        self.lbl_stock.configure(text="")
        self.total_lbl.configure(text=f"0 {MONNAIE}")
        self.refresh()
