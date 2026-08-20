# produits.py
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
        h = tk.Frame(self, bg="#f0f4f8")
        h.pack(fill="x", padx=30, pady=(20,10))
        tk.Label(h, text="Produits & Stock", font=("Arial", 18, "bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(side="left")
        tk.Button(h, text="+ Nouveau produit", font=("Arial", 10, "bold"),
                  bg="#4a90d9", fg="white", relief="flat", padx=12, pady=6,
                  cursor="hand2", command=self._open_form).pack(side="right")

        cols = ("ID","Nom","Description","Unite","Prix","Stock","Min","Palier","Offerts")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        for c, w in zip(cols, [40,180,160,70,80,70,60,70,70]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=30, pady=5)
        self.tree.bind("<Double-1>", lambda e: self._edit())
        self.tree.tag_configure("bas", foreground="#e74c3c")

        bf = tk.Frame(self, bg="#f0f4f8")
        bf.pack(fill="x", padx=30, pady=5)
        tk.Button(bf, text="Modifier", bg="#f39c12", fg="white", relief="flat",
                  padx=10, cursor="hand2", command=self._edit).pack(side="left", padx=5)
        tk.Button(bf, text="Supprimer", bg="#e74c3c", fg="white", relief="flat",
                  padx=10, cursor="hand2", command=self._delete).pack(side="left", padx=5)
        tk.Button(bf, text="Actualiser", bg="#27ae60", fg="white", relief="flat",
                  padx=10, cursor="hand2", command=self.refresh).pack(side="right", padx=5)

    def refresh(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        conn = get_connection()
        for r in conn.execute("""
            SELECT id,nom,description,unite,prix_vente,stock_actuel,
                   stock_minimum,reduction_palier,reduction_quantite
            FROM produits ORDER BY nom
        """).fetchall():
            tag = "bas" if r[5] <= r[6] else ""
            self.tree.insert("","end", values=(
                r[0],r[1],r[2] or "-",r[3],f"{r[4]:.0f}",r[5],r[6],r[7] or 0,r[8] or 0
            ), tags=(tag,))
        conn.close()

    def _open_form(self, pid=None):
        FormProduit(self, pid, on_save=self.refresh)

    def _edit(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("", "Selectionnez un produit."); return
        self._open_form(self.tree.item(sel[0])["values"][0])

    def _delete(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("", "Selectionnez un produit."); return
        pid = self.tree.item(sel[0])["values"][0]
        nom = self.tree.item(sel[0])["values"][1]
        if messagebox.askyesno("Supprimer", f"Supprimer '{nom}' ?"):
            conn = get_connection()
            conn.execute("DELETE FROM produits WHERE id=?", (pid,))
            conn.commit(); conn.close(); self.refresh()


class FormProduit(tk.Toplevel):
    def __init__(self, parent, pid=None, on_save=None):
        super().__init__(parent)
        self.pid = pid; self.on_save = on_save
        self.title("Modifier produit" if pid else "Nouveau produit")
        self.geometry("430x420"); self.resizable(False,False)
        self.configure(bg="#f0f4f8"); self.grab_set()
        fields = [
            ("Nom *", "nom"), ("Description", "desc"),
            (f"Unite (defaut: {UNITE_DEFAULT})", "unite"),
            (f"Prix vente ({MONNAIE})", "prix"), ("Stock initial", "stock"),
            ("Stock minimum", "stock_min"),
            ("Reduction - palier (nb paquets)", "palier"),
            ("Reduction - paquets offerts", "offerts"),
        ]
        self.vars = {}
        for i, (label, key) in enumerate(fields):
            tk.Label(self, text=label, bg="#f0f4f8", font=("Arial", 9)).grid(
                row=i, column=0, sticky="w", padx=20, pady=5)
            var = tk.StringVar(); self.vars[key] = var
            tk.Entry(self, textvariable=var, width=28, font=("Arial",10)).grid(
                row=i, column=1, padx=10, pady=5)
        self.vars["unite"].set(UNITE_DEFAULT)
        self.vars["prix"].set("0"); self.vars["stock"].set("0")
        self.vars["stock_min"].set("10")
        self.vars["palier"].set("0"); self.vars["offerts"].set("0")
        tk.Button(self, text="Enregistrer", bg="#4a90d9", fg="white",
                  font=("Arial",10,"bold"), relief="flat", padx=15, pady=6,
                  command=self._save).grid(row=len(fields), column=0, columnspan=2, pady=15)
        if pid: self._load()

    def _load(self):
        conn = get_connection()
        r = conn.execute("""SELECT nom,description,unite,prix_vente,stock_actuel,
            stock_minimum,reduction_palier,reduction_quantite FROM produits WHERE id=?""",
            (self.pid,)).fetchone()
        conn.close()
        if r:
            keys = ["nom","desc","unite","prix","stock","stock_min","palier","offerts"]
            for k, v in zip(keys, r): self.vars[k].set(str(v) if v is not None else "")

    def _save(self):
        nom = self.vars["nom"].get().strip()
        if not nom: messagebox.showerror("Erreur","Nom obligatoire.",parent=self); return
        try:
            prix=float(self.vars["prix"].get()); stock=int(self.vars["stock"].get())
            smin=int(self.vars["stock_min"].get()); pal=int(self.vars["palier"].get())
            off=int(self.vars["offerts"].get())
        except ValueError:
            messagebox.showerror("Erreur","Valeurs numeriques invalides.",parent=self); return
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
