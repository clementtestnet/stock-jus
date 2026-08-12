"""
achats.py — Enregistrer un achat / approvisionnement
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection


class AchatsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.controller = controller
        self._build()

    def _build(self):
        tk.Label(self, text="Nouvel Achat / Approvisionnement", font=("Arial", 18, "bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(anchor="w", padx=30, pady=(25, 5))
        tk.Label(self, text="Enregistrez une entrée de marchandise dans le stock",
                 font=("Arial", 10), bg="#f0f4f8", fg="#667788").pack(anchor="w", padx=30, pady=(0, 20))

        # Formulaire dans une carte blanche
        card = tk.Frame(self, bg="white", relief="flat", bd=0,
                        highlightbackground="#dde3ed", highlightthickness=1)
        card.pack(fill="x", padx=30, pady=10)

        fields = [
            ("Produit *", "produit"),
            ("Fournisseur", "fournisseur"),
            ("Quantité (bouteilles) *", "quantite"),
            ("Prix unitaire d'achat (CDF) *", "prix_unit"),
            ("Date d'achat", "date"),
            ("Notes", "notes"),
        ]

        self.vars = {}
        self.produit_cb = None
        self.fourn_cb = None

        for i, (label, key) in enumerate(fields):
            tk.Label(card, text=label, font=("Arial", 9, "bold"),
                     bg="white", fg="#334455").grid(row=i, column=0, sticky="w", padx=20, pady=8)
            if key == "produit":
                self.produit_var = tk.StringVar()
                self.produit_cb = ttk.Combobox(card, textvariable=self.produit_var, width=35, state="readonly")
                self.produit_cb.grid(row=i, column=1, padx=10, pady=8, sticky="w")
                self.vars[key] = self.produit_var
            elif key == "fournisseur":
                self.fourn_var = tk.StringVar()
                self.fourn_cb = ttk.Combobox(card, textvariable=self.fourn_var, width=35, state="readonly")
                self.fourn_cb.grid(row=i, column=1, padx=10, pady=8, sticky="w")
                self.vars[key] = self.fourn_var
            else:
                var = tk.StringVar()
                self.vars[key] = var
                entry = tk.Entry(card, textvariable=var, width=37, font=("Arial", 10))
                entry.grid(row=i, column=1, padx=10, pady=8, sticky="w")
                if key == "date":
                    var.set(datetime.now().strftime("%Y-%m-%d"))
                if key in ("quantite", "prix_unit"):
                    entry.bind("<KeyRelease>", self._update_total)

        # Total calculé
        total_frame = tk.Frame(card, bg="#eaf4fb")
        total_frame.grid(row=len(fields), column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        tk.Label(total_frame, text="Prix total :", font=("Arial", 11, "bold"),
                 bg="#eaf4fb", fg="#1a2940").pack(side="left", padx=15, pady=8)
        self.total_label = tk.Label(total_frame, text="0.00 CDF", font=("Arial", 14, "bold"),
                                     bg="#eaf4fb", fg="#27ae60")
        self.total_label.pack(side="left")

        tk.Button(card, text="✅ Enregistrer l'achat", font=("Arial", 11, "bold"),
                  bg="#27ae60", fg="white", relief="flat", padx=20, pady=8,
                  cursor="hand2", command=self._save).grid(
                      row=len(fields)+1, column=0, columnspan=2, pady=15)

    def _update_total(self, event=None):
        try:
            qty = float(self.vars["quantite"].get())
            prix = float(self.vars["prix_unit"].get())
            self.total_label.config(text=f"{qty * prix:,.2f} CDF")
        except ValueError:
            self.total_label.config(text="—")

    def refresh(self):
        """Recharge les listes déroulantes produits et fournisseurs."""
        conn = get_connection()
        produits = conn.execute("SELECT id, nom FROM produits ORDER BY nom").fetchall()
        fournisseurs = conn.execute("SELECT id, nom FROM fournisseurs ORDER BY nom").fetchall()
        conn.close()

        self._produit_map = {p[1]: p[0] for p in produits}
        self._fourn_map = {f[1]: f[0] for f in fournisseurs}

        self.produit_cb["values"] = list(self._produit_map.keys())
        self.fourn_cb["values"] = ["— Aucun —"] + list(self._fourn_map.keys())
        self.fourn_cb.set("— Aucun —")

    def _save(self):
        produit_nom = self.vars["produit"].get()
        if not produit_nom or produit_nom not in self._produit_map:
            messagebox.showerror("Erreur", "Sélectionnez un produit valide.")
            return
        try:
            qty = int(self.vars["quantite"].get())
            prix_unit = float(self.vars["prix_unit"].get())
            if qty <= 0 or prix_unit < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Quantité et prix doivent être des nombres positifs.")
            return

        produit_id = self._produit_map[produit_nom]
        fourn_nom = self.vars["fournisseur"].get()
        fourn_id = self._fourn_map.get(fourn_nom)
        prix_total = qty * prix_unit
        date_achat = self.vars["date"].get() or datetime.now().strftime("%Y-%m-%d")
        notes = self.vars["notes"].get()

        conn = get_connection()
        conn.execute("""
            INSERT INTO achats (produit_id, fournisseur_id, quantite, prix_unitaire, prix_total, date_achat, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (produit_id, fourn_id, qty, prix_unit, prix_total, date_achat, notes))

        # Mettre à jour le stock
        conn.execute("UPDATE produits SET stock_actuel = stock_actuel + ? WHERE id=?", (qty, produit_id))

        # Enregistrer le mouvement
        conn.execute("""
            INSERT INTO mouvements (produit_id, type, quantite, motif)
            VALUES (?, 'entree', ?, ?)
        """, (produit_id, qty, f"Achat du {date_achat}"))

        conn.commit()
        conn.close()

        messagebox.showinfo("Succès", f"✅ Achat enregistré !\n{produit_nom} : +{qty} bouteilles\nTotal : {prix_total:,.2f} CDF")
        # Reset form
        self.vars["quantite"].set("")
        self.vars["prix_unit"].set("")
        self.vars["notes"].set("")
        self.total_label.config(text="0.00 CDF")
