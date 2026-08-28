# produits.py — MODERNE CustomTkinter
import customtkinter as ctk
import tkinter.ttk as ttk
import tkinter as tk
from tkinter import messagebox
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from config import MONNAIE, UNITE_DEFAULT


def _style_tree():
    s = ttk.Style()
    s.configure("Dark.Treeview",
        background="#2b2b2b", foreground="white",
        fieldbackground="#2b2b2b", rowheight=28, font=("Arial", 11))
    s.configure("Dark.Treeview.Heading",
        background="#1a1a2e", foreground="#7EB3FF",
        font=("Arial", 11, "bold"), relief="flat")
    s.map("Dark.Treeview", background=[("selected", "#1f6aa5")])


class ProduitsFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.controller = controller
        _style_tree()
        self._build()

    def _build(self):
        # En-tête
        h = ctk.CTkFrame(self, fg_color="transparent")
        h.pack(fill="x", padx=30, pady=(22, 8))
        ctk.CTkLabel(h, text="Produits & Stock",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkButton(h, text="+ Nouveau produit",
                      width=160, height=36, corner_radius=8,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._open_form).pack(side="right")

        # Tableau
        cols = ("ID","Nom","Description","Unité","Prix","Stock","Min","Palier","Offerts")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  height=14, style="Dark.Treeview")
        for c, w in zip(cols, [40,180,160,70,80,70,60,70,70]):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=30, pady=5)
        self.tree.bind("<Double-1>", lambda e: self._edit())
        self.tree.tag_configure("bas", foreground="#e74c3c")

        # Boutons bas
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
        for r in conn.execute("""
            SELECT id,nom,description,unite,prix_vente,stock_actuel,
                   stock_minimum,reduction_palier,reduction_quantite
            FROM produits ORDER BY nom
        """).fetchall():
            tag = "bas" if r[5] <= r[6] else ""
            self.tree.insert("", "end", values=(
                r[0], r[1], r[2] or "-", r[3], f"{r[4]:.0f}",
                r[5], r[6], r[7] or 0, r[8] or 0), tags=(tag,))
        conn.close()

    def _open_form(self, pid=None):
        FormProduit(self, pid, on_save=self.refresh)

    def _edit(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("", "Sélectionnez un produit."); return
        self._open_form(self.tree.item(sel[0])["values"][0])

    def _delete(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("", "Sélectionnez un produit."); return
        pid = self.tree.item(sel[0])["values"][0]
        nom = self.tree.item(sel[0])["values"][1]
        if messagebox.askyesno("Supprimer", f"Supprimer '{nom}' ?"):
            conn = get_connection()
            conn.execute("DELETE FROM produits WHERE id=?", (pid,))
            conn.commit(); conn.close(); self.refresh()


class FormProduit(ctk.CTkToplevel):
    def __init__(self, parent, pid=None, on_save=None):
        super().__init__(parent)
        self.pid = pid; self.on_save = on_save
        self.title("Modifier produit" if pid else "Nouveau produit")
        self.geometry("460x500"); self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(self, text="Modifier produit" if pid else "Nouveau produit",
                     font=ctk.CTkFont(size=17, weight="bold")).pack(pady=(20, 12))

        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        fields = [
            ("Nom *", "nom"),
            ("Description", "desc"),
            (f"Unité (défaut: {UNITE_DEFAULT})", "unite"),
            (f"Prix vente ({MONNAIE})", "prix"),
            ("Stock initial", "stock"),
            ("Stock minimum", "stock_min"),
            ("Réduction — palier (nb paquets)", "palier"),
            ("Réduction — paquets offerts", "offerts"),
        ]
        self.vars = {}
        for label, key in fields:
            ctk.CTkLabel(scroll, text=label,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         anchor="w").pack(fill="x", padx=5, pady=(8, 2))
            var = tk.StringVar(); self.vars[key] = var
            ctk.CTkEntry(scroll, textvariable=var, height=36,
                         corner_radius=8).pack(fill="x", padx=5, pady=(0, 2))

        self.vars["unite"].set(UNITE_DEFAULT)
        for k, v in [("prix","0"),("stock","0"),("stock_min","10"),("palier","0"),("offerts","0")]:
            self.vars[k].set(v)

        ctk.CTkButton(self, text="💾 Enregistrer", height=42, corner_radius=10,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._save).pack(fill="x", padx=20, pady=12)
        if pid: self._load()

    def _load(self):
        conn = get_connection()
        r = conn.execute("""SELECT nom,description,unite,prix_vente,stock_actuel,
            stock_minimum,reduction_palier,reduction_quantite FROM produits WHERE id=?""",
            (self.pid,)).fetchone()
        conn.close()
        if r:
            for k, v in zip(["nom","desc","unite","prix","stock","stock_min","palier","offerts"], r):
                self.vars[k].set(str(v) if v is not None else "")

    def _save(self):
        nom = self.vars["nom"].get().strip()
        if not nom: messagebox.showerror("Erreur", "Nom obligatoire.", parent=self); return
        try:
            prix = float(self.vars["prix"].get()); stock = int(self.vars["stock"].get())
            smin = int(self.vars["stock_min"].get()); pal = int(self.vars["palier"].get())
            off  = int(self.vars["offerts"].get())
        except ValueError:
            messagebox.showerror("Erreur", "Valeurs numériques invalides.", parent=self); return
        conn = get_connection()
        if self.pid:
            conn.execute("""UPDATE produits SET nom=?,description=?,unite=?,prix_vente=?,
                stock_actuel=?,stock_minimum=?,reduction_palier=?,reduction_quantite=? WHERE id=?""",
                (nom,self.vars["desc"].get(),self.vars["unite"].get(),prix,stock,smin,pal,off,self.pid))
        else:
            conn.execute("""INSERT INTO produits (nom,description,unite,prix_vente,stock_actuel,
                stock_minimum,reduction_palier,reduction_quantite) VALUES (?,?,?,?,?,?,?,?)""",
                (nom,self.vars["desc"].get(),self.vars["unite"].get(),prix,stock,smin,pal,off))
        conn.commit(); conn.close()
        if self.on_save: self.on_save()
        self.destroy()
