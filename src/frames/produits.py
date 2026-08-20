"""
produits.py — Gestion des produits / références de jus
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from config import MONNAIE, UNITE_DEFAULT


class ProduitsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.controller = controller
        self._build()

    def _build(self):
        # En-tête
        header = tk.Frame(self, bg="#f0f4f8")
        header.pack(fill="x", padx=30, pady=(25, 10))
        tk.Label(header, text="Produits & Stock", font=("Arial", 18, "bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(side="left")
        tk.Button(header, text="+ Nouveau produit", font=("Arial", 10, "bold"),
                  bg="#4a90d9", fg="white", relief="flat", padx=12, pady=6,
                  cursor="hand2", command=self._open_form).pack(side="right")

        # Tableau
        cols = ("ID", "Nom", "Description", "Unité", "Prix vente", "Stock actuel", "Stock min")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=15)
        widths = [40, 200, 200, 80, 100, 100, 100]
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=30, pady=5)
        self.tree.bind("<Double-1>", self._on_double_click)

        # Scrollbar
        sb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)

        # Boutons bas
        btn_frame = tk.Frame(self, bg="#f0f4f8")
        btn_frame.pack(fill="x", padx=30, pady=5)
        tk.Button(btn_frame, text="✏️ Modifier", font=("Arial", 9),
                  bg="#f39c12", fg="white", relief="flat", padx=10,
                  cursor="hand2", command=self._edit_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="🗑️ Supprimer", font=("Arial", 9),
                  bg="#e74c3c", fg="white", relief="flat", padx=10,
                  cursor="hand2", command=self._delete_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="🔄 Actualiser", font=("Arial", 9),
                  bg="#27ae60", fg="white", relief="flat", padx=10,
                  cursor="hand2", command=self.refresh).pack(side="right", padx=5)

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_connection()
        rows = conn.execute("SELECT id, nom, description, unite, prix_vente, stock_actuel, stock_minimum FROM produits ORDER BY nom").fetchall()
        conn.close()
        for r in rows:
            tag = "bas" if r[5] <= r[6] else ""
            self.tree.insert("", "end", values=(r[0], r[1], r[2] or "—", r[3], f"{r[4]:.2f}", r[5], r[6]), tags=(tag,))
        self.tree.tag_configure("bas", foreground="#e74c3c")

    def _open_form(self, produit_id=None):
        FormProduit(self, produit_id, on_save=self.refresh)

    def _on_double_click(self, event):
        sel = self.tree.selection()
        if sel:
            pid = self.tree.item(sel[0])["values"][0]
            self._open_form(pid)

    def _edit_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un produit d'abord.")
            return
        pid = self.tree.item(sel[0])["values"][0]
        self._open_form(pid)

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un produit d'abord.")
            return
        pid = self.tree.item(sel[0])["values"][0]
        nom = self.tree.item(sel[0])["values"][1]
        if messagebox.askyesno("Supprimer", f"Supprimer « {nom} » ? Cette action est irréversible."):
            conn = get_connection()
            conn.execute("DELETE FROM produits WHERE id=?", (pid,))
            conn.commit()
            conn.close()
            self.refresh()


class FormProduit(tk.Toplevel):
    def __init__(self, parent, produit_id=None, on_save=None):
        super().__init__(parent)
        self.produit_id = produit_id
        self.on_save = on_save
        self.title("Nouveau produit" if not produit_id else "Modifier produit")
        self.geometry("420x380")
        self.resizable(False, False)
        self.configure(bg="#f0f4f8")
        self.grab_set()
        self._build()
        if produit_id:
            self._load()

    def _build(self):
        fields = [
            ("Nom du produit *", "nom"),
            ("Description", "desc"),
            (f"Unité (ex: {UNITE_DEFAULT})", "unite"),
            (f"Prix de vente unitaire ({MONNAIE})", "prix"),
            ("Stock initial", "stock"),
            ("Stock minimum (alerte)", "stock_min"),
            ("Réduction : palier (nb paquets)", "reduction_palier"),
            ("Réduction : paquets offerts", "reduction_quantite"),
        ]
        self.vars = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(self, text=label, bg="#f0f4f8", font=("Arial", 9)).grid(
                row=i, column=0, sticky="w", padx=20, pady=6)
            var = tk.StringVar()
            self.vars[key] = var
            tk.Entry(self, textvariable=var, width=28, font=("Arial", 10)).grid(
                row=i, column=1, padx=10, pady=6)

        # Defaults
        self.vars["unite"].set(UNITE_DEFAULT)
        self.vars["prix"].set("0")
        self.vars["stock"].set("0")
        self.vars["stock_min"].set("10")
        self.vars["reduction_palier"].set("0")
        self.vars["reduction_quantite"].set("0")

        tk.Button(self, text="💾 Enregistrer", bg="#4a90d9", fg="white",
                  font=("Arial", 10, "bold"), relief="flat", padx=15, pady=6,
                  command=self._save).grid(row=len(fields), column=0, columnspan=2, pady=15)

    def _load(self):
        conn = get_connection()
        r = conn.execute("SELECT nom, description, unite, prix_vente, stock_actuel, stock_minimum, reduction_palier, reduction_quantite FROM produits WHERE id=?",
                         (self.produit_id,)).fetchone()
        conn.close()
        if r:
            self.vars["nom"].set(r[0])
            self.vars["desc"].set(r[1] or "")
            self.vars["unite"].set(r[2])
            self.vars["prix"].set(str(r[3]))
            self.vars["stock"].set(str(r[4]))
            self.vars["stock_min"].set(str(r[5]))
            self.vars["reduction_palier"].set(str(r[6] or 0))
            self.vars["reduction_quantite"].set(str(r[7] or 0))

    def _save(self):
        nom = self.vars["nom"].get().strip()
        if not nom:
            messagebox.showerror("Erreur", "Le nom est obligatoire.", parent=self)
            return
        try:
            prix = float(self.vars["prix"].get())
            stock = int(self.vars["stock"].get())
            stock_min = int(self.vars["stock_min"].get())
            palier = int(self.vars["reduction_palier"].get())
            red_qte = int(self.vars["reduction_quantite"].get())
        except ValueError:
            messagebox.showerror("Erreur", "Prix, stock et réduction doivent être des nombres.", parent=self)
            return

        conn = get_connection()
        if self.produit_id:
            conn.execute("""
                UPDATE produits SET nom=?, description=?, unite=?, prix_vente=?,
                stock_actuel=?, stock_minimum=?, reduction_palier=?, reduction_quantite=?
                WHERE id=?
            """, (nom, self.vars["desc"].get(), self.vars["unite"].get(), prix,
                  stock, stock_min, palier, red_qte, self.produit_id))
        else:
            conn.execute("""
                INSERT INTO produits (nom, description, unite, prix_vente, stock_actuel,
                stock_minimum, reduction_palier, reduction_quantite)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nom, self.vars["desc"].get(), self.vars["unite"].get(), prix,
                  stock, stock_min, palier, red_qte))
        conn.commit()
        conn.close()
        if self.on_save:
            self.on_save()
        self.destroy()
