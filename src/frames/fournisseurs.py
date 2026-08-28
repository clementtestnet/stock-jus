# fournisseurs.py — MODERNE CustomTkinter
import customtkinter as ctk
import tkinter.ttk as ttk
import tkinter as tk
from tkinter import messagebox
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection


def _style_tree():
    s = ttk.Style()
    s.configure("Dark.Treeview",
        background="#2b2b2b", foreground="white",
        fieldbackground="#2b2b2b", rowheight=28, font=("Arial",11))
    s.configure("Dark.Treeview.Heading",
        background="#1a1a2e", foreground="#7EB3FF",
        font=("Arial",11,"bold"), relief="flat")
    s.map("Dark.Treeview", background=[("selected","#1f6aa5")])


class FournisseursFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.controller = controller
        _style_tree()
        self._build()

    def _build(self):
        h = ctk.CTkFrame(self, fg_color="transparent")
        h.pack(fill="x", padx=30, pady=(22,8))
        ctk.CTkLabel(h, text="Fournisseurs",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkButton(h, text="+ Nouveau fournisseur",
                      width=180, height=36, corner_radius=8,
                      fg_color="#d68910", hover_color="#b7770d",
                      command=self._open_form).pack(side="right")

        cols = ("ID","Nom","Téléphone","Adresse","Email","Notes")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  height=16, style="Dark.Treeview")
        for c, w in zip(cols, [40,200,130,180,150,180]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=30, pady=5)
        self.tree.bind("<Double-1>", lambda e: self._edit())

        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(fill="x", padx=30, pady=6)
        ctk.CTkButton(bf, text="✏️ Modifier", width=110, height=34,
                      fg_color="#d68910", hover_color="#b7770d",
                      command=self._edit).pack(side="left", padx=5)
        ctk.CTkButton(bf, text="🗑 Supprimer", width=110, height=34,
                      fg_color="#c0392b", hover_color="#96281b",
                      command=self._delete).pack(side="left", padx=5)
        ctk.CTkButton(bf, text="🔄 Actualiser", width=110, height=34,
                      fg_color="#1e8449", hover_color="#145a32",
                      command=self.refresh).pack(side="right", padx=5)

    def refresh(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        conn = get_connection()
        for r in conn.execute(
            "SELECT id,nom,telephone,adresse,email,notes FROM fournisseurs ORDER BY nom"
        ).fetchall():
            self.tree.insert("","end", values=(r[0],r[1],r[2] or "-",r[3] or "-",r[4] or "-",r[5] or "-"))
        conn.close()

    def _open_form(self, fid=None):
        FormFournisseur(self, fid, on_save=self.refresh)

    def _edit(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("","Sélectionnez un fournisseur."); return
        self._open_form(self.tree.item(sel[0])["values"][0])

    def _delete(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("","Sélectionnez un fournisseur."); return
        fid = self.tree.item(sel[0])["values"][0]
        nom = self.tree.item(sel[0])["values"][1]
        if messagebox.askyesno("Supprimer", f"Supprimer '{nom}' ?"):
            conn = get_connection()
            conn.execute("DELETE FROM fournisseurs WHERE id=?", (fid,))
            conn.commit(); conn.close(); self.refresh()


class FormFournisseur(ctk.CTkToplevel):
    def __init__(self, parent, fid=None, on_save=None):
        super().__init__(parent)
        self.fid = fid; self.on_save = on_save
        self.title("Modifier fournisseur" if fid else "Nouveau fournisseur")
        self.geometry("440x400"); self.resizable(False,False)
        self.grab_set()

        ctk.CTkLabel(self, text="Modifier fournisseur" if fid else "Nouveau fournisseur",
                     font=ctk.CTkFont(size=17, weight="bold")).pack(pady=(20,12))

        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        fields = [("Nom *","nom"),("Téléphone","tel"),("Adresse","adresse"),("Email","email"),("Notes","notes")]
        self.vars = {}
        for label, key in fields:
            ctk.CTkLabel(scroll, text=label,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         anchor="w").pack(fill="x", padx=5, pady=(8,2))
            var = tk.StringVar(); self.vars[key] = var
            ctk.CTkEntry(scroll, textvariable=var, height=36,
                         corner_radius=8).pack(fill="x", padx=5, pady=(0,2))

        ctk.CTkButton(self, text="💾 Enregistrer", height=42, corner_radius=10,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color="#d68910", hover_color="#b7770d",
                      command=self._save).pack(fill="x", padx=20, pady=12)
        if fid: self._load()

    def _load(self):
        conn = get_connection()
        r = conn.execute("SELECT nom,telephone,adresse,email,notes FROM fournisseurs WHERE id=?",
                          (self.fid,)).fetchone()
        conn.close()
        if r:
            for k, v in zip(["nom","tel","adresse","email","notes"], r):
                self.vars[k].set(v or "")

    def _save(self):
        nom = self.vars["nom"].get().strip()
        if not nom: messagebox.showerror("Erreur","Nom obligatoire.",parent=self); return
        conn = get_connection()
        if self.fid:
            conn.execute("UPDATE fournisseurs SET nom=?,telephone=?,adresse=?,email=?,notes=? WHERE id=?",
                         (nom,self.vars["tel"].get(),self.vars["adresse"].get(),
                          self.vars["email"].get(),self.vars["notes"].get(),self.fid))
        else:
            conn.execute("INSERT INTO fournisseurs (nom,telephone,adresse,email,notes) VALUES (?,?,?,?,?)",
                         (nom,self.vars["tel"].get(),self.vars["adresse"].get(),
                          self.vars["email"].get(),self.vars["notes"].get()))
        conn.commit(); conn.close()
        if self.on_save: self.on_save()
        self.destroy()
