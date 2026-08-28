# sorties.py — Transfert de produits vers une autre boutique

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from config import MONNAIE, UNITE_DEFAULT, BOUTIQUE_NOM


class SortiesFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.controller    = controller
        self._produit_map  = {}
        self._build()

    def _build(self):
        tk.Label(self, text="Sorties — Transfert Boutique",
                 font=("Arial", 18, "bold"), bg="#f0f4f8", fg="#1a2940").pack(anchor="w", padx=30, pady=(20, 3))
        tk.Label(self, text="Produits transferes vers une autre boutique (pas vendus au client)",
                 font=("Arial", 9), bg="#f0f4f8", fg="#667788").pack(anchor="w", padx=30, pady=(0, 15))

        # Formulaire
        card = tk.Frame(self, bg="white", highlightbackground="#dde3ed", highlightthickness=1)
        card.pack(fill="x", padx=30, pady=5)

        fields = [
            ("Produit *",                       "produit"),
            (f"Quantite ({UNITE_DEFAULT}s) *",  "quantite"),
            ("Boutique destinataire *",          "destination"),
            ("Motif (ex: approvisionnement)",    "motif"),
            ("Date",                             "date"),
            ("Notes",                            "notes"),
        ]
        self.vars = {}

        for i, (label, key) in enumerate(fields):
            tk.Label(card, text=label, font=("Arial", 9, "bold"),
                     bg="white", fg="#334455").grid(row=i, column=0, sticky="w", padx=20, pady=8)
            if key == "produit":
                self.pvar = tk.StringVar()
                self.pcb  = ttk.Combobox(card, textvariable=self.pvar, width=32, state="readonly")
                self.pcb.grid(row=i, column=1, padx=10, pady=8, sticky="w")
                self.pcb.bind("<<ComboboxSelected>>", self._on_produit)
                self.vars[key] = self.pvar
            else:
                var = tk.StringVar(); self.vars[key] = var
                tk.Entry(card, textvariable=var, width=34, font=("Arial", 10)).grid(
                    row=i, column=1, padx=10, pady=8, sticky="w")
                if key == "date":
                    var.set(datetime.now().strftime("%Y-%m-%d"))

        # Stock dispo
        self.lbl_stock = tk.Label(card, text="Stock: -", font=("Arial", 9, "italic"),
                                   bg="white", fg="#667788")
        self.lbl_stock.grid(row=0, column=2, padx=10, sticky="w")

        # Bouton
        tk.Button(card, text="Enregistrer la sortie", font=("Arial", 11, "bold"),
                  bg="#9b59b6", fg="white", relief="flat", padx=20, pady=8,
                  cursor="hand2", command=self._save).grid(
                  row=len(fields), column=0, columnspan=3, pady=15)

        # Historique sorties
        tk.Label(self, text="Historique des sorties", font=("Arial", 13, "bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(anchor="w", padx=30, pady=(15, 5))

        cols = ("Date", "Produit", "Quantite", "Destination", "Motif", "Notes")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=8)
        for c, w in zip(cols, [130, 160, 80, 160, 160, 160]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="x", padx=30, pady=5)

        self.status_lbl = tk.Label(self, text="", font=("Arial", 9, "italic"),
                                    bg="#f0f4f8", fg="#9b59b6")
        self.status_lbl.pack(anchor="w", padx=30, pady=5)

        self.refresh()

    def _on_produit(self, event=None):
        pid = self._produit_map.get(self.pvar.get())
        if pid:
            conn = get_connection()
            row  = conn.execute("SELECT stock_actuel FROM produits WHERE id=?", (pid,)).fetchone()
            conn.close()
            if row:
                fg = "#27ae60" if row[0] > 0 else "#e74c3c"
                self.lbl_stock.config(text=f"Stock: {row[0]} {UNITE_DEFAULT}s", fg=fg)

    def refresh(self):
        conn = get_connection()
        self._produit_map = {r[1]: r[0] for r in conn.execute(
            "SELECT id, nom FROM produits WHERE stock_actuel > 0 ORDER BY nom").fetchall()}
        conn.close()
        self.pcb["values"] = list(self._produit_map.keys())
        self._load_historique()

    def _load_historique(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        conn = get_connection()
        rows = conn.execute("""
            SELECT s.date_sortie, p.nom, s.quantite, s.destination,
                   COALESCE(s.motif, '-'), COALESCE(s.notes, '-')
            FROM sorties s JOIN produits p ON s.produit_id = p.id
            ORDER BY s.date_sortie DESC LIMIT 30
        """).fetchall()
        conn.close()
        for r in rows:
            self.tree.insert("", "end", values=(str(r[0])[:16], r[1], r[2], r[3], r[4], r[5]))

    def _save(self):
        nom = self.pvar.get()
        if not nom or nom not in self._produit_map:
            messagebox.showerror("Erreur", "Selectionnez un produit valide."); return

        dest = self.vars["destination"].get().strip()
        if not dest:
            messagebox.showerror("Erreur", "Indiquez la boutique destinataire."); return

        try:
            qty = int(self.vars["quantite"].get())
            if qty <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Quantite invalide."); return

        pid  = self._produit_map[nom]
        conn = get_connection()
        stock = conn.execute("SELECT stock_actuel FROM produits WHERE id=?", (pid,)).fetchone()[0]
        if qty > stock:
            messagebox.showerror("Stock insuffisant", f"Stock: {stock}  Demande: {qty}")
            conn.close(); return

        date  = self.vars["date"].get() or datetime.now().strftime("%Y-%m-%d")
        motif = self.vars["motif"].get() or "Transfert boutique"

        conn.execute("""
            INSERT INTO sorties (produit_id, quantite, destination, motif, date_sortie, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pid, qty, dest, motif, date, self.vars["notes"].get() or None))

        conn.execute("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE id=?", (qty, pid))
        conn.execute("""
            INSERT INTO mouvements (produit_id, type, quantite, motif)
            VALUES (?, 'sortie', ?, ?)
        """, (pid, qty, f"Transfert vers {dest}"))
        conn.commit(); conn.close()

        self.status_lbl.config(text=f"Sortie enregistree: {qty} {UNITE_DEFAULT}s -> {dest}")
        for k in ("quantite", "destination", "motif", "notes"): self.vars[k].set("")
        self.lbl_stock.config(text="Stock: -")
        self.refresh()
        messagebox.showinfo("Succes", f"{qty} {UNITE_DEFAULT}s transferes vers {dest}")
