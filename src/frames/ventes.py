"""
ventes.py — Enregistrer une vente / sortie de stock
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection


class VentesFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.controller = controller
        self._produit_map = {}
        self._build()

    def _build(self):
        tk.Label(self, text="Enregistrer une Vente", font=("Arial", 18, "bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(anchor="w", padx=30, pady=(25, 5))
        tk.Label(self, text="Enregistrez une sortie de stock (vente au client)",
                 font=("Arial", 10), bg="#f0f4f8", fg="#667788").pack(anchor="w", padx=30, pady=(0, 15))

        # Carte formulaire
        card = tk.Frame(self, bg="white", highlightbackground="#dde3ed", highlightthickness=1)
        card.pack(fill="x", padx=30, pady=5)

        fields = [
            ("Produit *", "produit"),
            ("Quantité vendue *", "quantite"),
            ("Prix de vente unitaire (CDF) *", "prix_unit"),
            ("Date de vente", "date"),
            ("Client (optionnel)", "client"),
            ("Notes", "notes"),
        ]
        self.vars = {}

        for i, (label, key) in enumerate(fields):
            tk.Label(card, text=label, font=("Arial", 9, "bold"),
                     bg="white", fg="#334455").grid(row=i, column=0, sticky="w", padx=20, pady=8)
            if key == "produit":
                self.produit_var = tk.StringVar()
                self.produit_cb = ttk.Combobox(card, textvariable=self.produit_var, width=35, state="readonly")
                self.produit_cb.grid(row=i, column=1, padx=10, pady=8, sticky="w")
                self.produit_cb.bind("<<ComboboxSelected>>", self._on_produit_change)
                self.vars[key] = self.produit_var
            else:
                var = tk.StringVar()
                self.vars[key] = var
                entry = tk.Entry(card, textvariable=var, width=37, font=("Arial", 10))
                entry.grid(row=i, column=1, padx=10, pady=8, sticky="w")
                if key == "date":
                    var.set(datetime.now().strftime("%Y-%m-%d"))
                if key in ("quantite", "prix_unit"):
                    entry.bind("<KeyRelease>", self._update_total)

        # Stock dispo affiché
        self.lbl_stock = tk.Label(card, text="Stock disponible : —", font=("Arial", 9, "italic"),
                                   bg="white", fg="#667788")
        self.lbl_stock.grid(row=0, column=2, padx=10, sticky="w")

        # Total
        total_frame = tk.Frame(card, bg="#fef9e7")
        total_frame.grid(row=len(fields), column=0, columnspan=2, sticky="ew", padx=20, pady=10)
        tk.Label(total_frame, text="Total vente :", font=("Arial", 11, "bold"),
                 bg="#fef9e7", fg="#1a2940").pack(side="left", padx=15, pady=8)
        self.total_label = tk.Label(total_frame, text="0.00 CDF", font=("Arial", 14, "bold"),
                                     bg="#fef9e7", fg="#f39c12")
        self.total_label.pack(side="left")

        tk.Button(card, text="💰 Enregistrer la vente", font=("Arial", 11, "bold"),
                  bg="#f39c12", fg="white", relief="flat", padx=20, pady=8,
                  cursor="hand2", command=self._save).grid(
                      row=len(fields)+1, column=0, columnspan=2, pady=15)

        # ─── Historique ventes du bas ───────────────────────────────
        tk.Label(self, text="Dernières ventes", font=("Arial", 13, "bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(anchor="w", padx=30, pady=(15, 5))

        cols = ("Date", "Produit", "Qté", "Prix unit.", "Total", "Client", "Notes")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=7)
        widths = [130, 160, 60, 110, 110, 130, 160]
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="x", padx=30, pady=5)

    def _on_produit_change(self, event=None):
        nom = self.produit_var.get()
        pid = self._produit_map.get(nom)
        if pid:
            conn = get_connection()
            row = conn.execute("SELECT stock_actuel, prix_vente FROM produits WHERE id=?", (pid,)).fetchone()
            conn.close()
            if row:
                self.lbl_stock.config(text=f"Stock disponible : {row[0]} bouteilles",
                                       fg="#27ae60" if row[0] > 0 else "#e74c3c")
                if not self.vars["prix_unit"].get():
                    self.vars["prix_unit"].set(str(row[1]))
                self._update_total()

    def _update_total(self, event=None):
        try:
            qty = float(self.vars["quantite"].get())
            prix = float(self.vars["prix_unit"].get())
            self.total_label.config(text=f"{qty * prix:,.2f} CDF")
        except ValueError:
            self.total_label.config(text="—")

    def refresh(self):
        conn = get_connection()
        produits = conn.execute("SELECT id, nom FROM produits WHERE stock_actuel > 0 ORDER BY nom").fetchall()
        conn.close()
        self._produit_map = {p[1]: p[0] for p in produits}
        self.produit_cb["values"] = list(self._produit_map.keys())
        self._load_recent()

    def _load_recent(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_connection()
        rows = conn.execute("""
            SELECT v.date_vente, p.nom, v.quantite, v.prix_unitaire, v.prix_total,
                   COALESCE(v.client, '—'), COALESCE(v.notes, '—')
            FROM ventes v JOIN produits p ON v.produit_id = p.id
            ORDER BY v.date_vente DESC LIMIT 15
        """).fetchall()
        conn.close()
        for r in rows:
            self.tree.insert("", "end", values=(
                str(r[0])[:16], r[1], r[2],
                f"{r[3]:.2f}", f"{r[4]:.2f} CDF", r[5], r[6]
            ))

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
        conn = get_connection()
        stock_actuel = conn.execute("SELECT stock_actuel FROM produits WHERE id=?", (produit_id,)).fetchone()[0]

        if qty > stock_actuel:
            messagebox.showerror("Stock insuffisant",
                                  f"Stock disponible : {stock_actuel} bouteilles\nVous essayez de vendre : {qty}")
            conn.close()
            return

        prix_total = qty * prix_unit
        date_vente = self.vars["date"].get() or datetime.now().strftime("%Y-%m-%d")

        conn.execute("""
            INSERT INTO ventes (produit_id, quantite, prix_unitaire, prix_total, date_vente, client, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (produit_id, qty, prix_unit, prix_total, date_vente,
              self.vars["client"].get() or None, self.vars["notes"].get() or None))

        conn.execute("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE id=?", (qty, produit_id))
        conn.execute("""
            INSERT INTO mouvements (produit_id, type, quantite, motif)
            VALUES (?, 'sortie', ?, ?)
        """, (produit_id, qty, f"Vente du {date_vente}"))
        conn.commit()
        conn.close()

        messagebox.showinfo("✅ Vente enregistrée",
                             f"{produit_nom} : -{qty} bouteilles\nTotal : {prix_total:,.2f} CDF")
        self.vars["quantite"].set("")
        self.vars["prix_unit"].set("")
        self.vars["client"].set("")
        self.vars["notes"].set("")
        self.total_label.config(text="0.00 CDF")
        self.lbl_stock.config(text="Stock disponible : —")
        self.refresh()
