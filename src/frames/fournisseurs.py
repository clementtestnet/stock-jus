"""
fournisseurs.py — Gestion des fournisseurs
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection


class FournisseursFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.controller = controller
        self._build()

    def _build(self):
        header = tk.Frame(self, bg="#f0f4f8")
        header.pack(fill="x", padx=30, pady=(25, 10))
        tk.Label(header, text="Fournisseurs", font=("Arial", 18, "bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(side="left")
        tk.Button(header, text="+ Nouveau fournisseur", font=("Arial", 10, "bold"),
                  bg="#f39c12", fg="white", relief="flat", padx=12, pady=6,
                  cursor="hand2", command=self._open_form).pack(side="right")

        cols = ("ID", "Nom", "Téléphone", "Adresse", "Email", "Notes")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=16)
        widths = [40, 180, 130, 180, 150, 180]
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=30, pady=5)
        self.tree.bind("<Double-1>", self._on_double_click)

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
        rows = conn.execute("SELECT id, nom, telephone, adresse, email, notes FROM fournisseurs ORDER BY nom").fetchall()
        conn.close()
        for r in rows:
            self.tree.insert("", "end", values=(r[0], r[1], r[2] or "—", r[3] or "—", r[4] or "—", r[5] or "—"))

    def _open_form(self, fid=None):
        FormFournisseur(self, fid, on_save=self.refresh)

    def _on_double_click(self, event):
        sel = self.tree.selection()
        if sel:
            fid = self.tree.item(sel[0])["values"][0]
            self._open_form(fid)

    def _edit_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un fournisseur d'abord.")
            return
        fid = self.tree.item(sel[0])["values"][0]
        self._open_form(fid)

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un fournisseur d'abord.")
            return
        fid = self.tree.item(sel[0])["values"][0]
        nom = self.tree.item(sel[0])["values"][1]
        if messagebox.askyesno("Supprimer", f"Supprimer « {nom} » ?"):
            conn = get_connection()
            conn.execute("DELETE FROM fournisseurs WHERE id=?", (fid,))
            conn.commit()
            conn.close()
            self.refresh()


class FormFournisseur(tk.Toplevel):
    def __init__(self, parent, fid=None, on_save=None):
        super().__init__(parent)
        self.fid = fid
        self.on_save = on_save
        self.title("Nouveau fournisseur" if not fid else "Modifier fournisseur")
        self.geometry("400x320")
        self.resizable(False, False)
        self.configure(bg="#f0f4f8")
        self.grab_set()
        self._build()
        if fid:
            self._load()

    def _build(self):
        fields = [
            ("Nom *", "nom"),
            ("Téléphone", "tel"),
            ("Adresse", "adresse"),
            ("Email", "email"),
            ("Notes", "notes"),
        ]
        self.vars = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(self, text=label, bg="#f0f4f8", font=("Arial", 9)).grid(
                row=i, column=0, sticky="w", padx=20, pady=7)
            var = tk.StringVar()
            self.vars[key] = var
            tk.Entry(self, textvariable=var, width=28, font=("Arial", 10)).grid(
                row=i, column=1, padx=10, pady=7)

        tk.Button(self, text="💾 Enregistrer", bg="#f39c12", fg="white",
                  font=("Arial", 10, "bold"), relief="flat", padx=15, pady=6,
                  command=self._save).grid(row=len(fields), column=0, columnspan=2, pady=15)

    def _load(self):
        conn = get_connection()
        r = conn.execute("SELECT nom, telephone, adresse, email, notes FROM fournisseurs WHERE id=?",
                         (self.fid,)).fetchone()
        conn.close()
        if r:
            keys = ["nom", "tel", "adresse", "email", "notes"]
            for k, v in zip(keys, r):
                self.vars[k].set(v or "")

    def _save(self):
        nom = self.vars["nom"].get().strip()
        if not nom:
            messagebox.showerror("Erreur", "Le nom est obligatoire.", parent=self)
            return
        conn = get_connection()
        if self.fid:
            conn.execute("""
                UPDATE fournisseurs SET nom=?, telephone=?, adresse=?, email=?, notes=? WHERE id=?
            """, (nom, self.vars["tel"].get(), self.vars["adresse"].get(),
                  self.vars["email"].get(), self.vars["notes"].get(), self.fid))
        else:
            conn.execute("""
                INSERT INTO fournisseurs (nom, telephone, adresse, email, notes) VALUES (?, ?, ?, ?, ?)
            """, (nom, self.vars["tel"].get(), self.vars["adresse"].get(),
                  self.vars["email"].get(), self.vars["notes"].get()))
        conn.commit()
        conn.close()
        if self.on_save:
            self.on_save()
        self.destroy()
