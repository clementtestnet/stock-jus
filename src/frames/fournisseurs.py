# fournisseurs.py
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
        h = tk.Frame(self, bg="#f0f4f8")
        h.pack(fill="x", padx=30, pady=(20,10))
        tk.Label(h, text="Fournisseurs", font=("Arial",18,"bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(side="left")
        tk.Button(h, text="+ Nouveau", font=("Arial",10,"bold"),
                  bg="#f39c12", fg="white", relief="flat", padx=12, pady=6,
                  cursor="hand2", command=self._open_form).pack(side="right")

        cols = ("ID","Nom","Telephone","Adresse","Email","Notes")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=16)
        for c, w in zip(cols, [40,200,130,180,150,180]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=30, pady=5)
        self.tree.bind("<Double-1>", lambda e: self._edit())

        bf = tk.Frame(self, bg="#f0f4f8")
        bf.pack(fill="x", padx=30, pady=5)
        tk.Button(bf,text="Modifier",bg="#f39c12",fg="white",relief="flat",padx=10,cursor="hand2",command=self._edit).pack(side="left",padx=5)
        tk.Button(bf,text="Supprimer",bg="#e74c3c",fg="white",relief="flat",padx=10,cursor="hand2",command=self._delete).pack(side="left",padx=5)
        tk.Button(bf,text="Actualiser",bg="#27ae60",fg="white",relief="flat",padx=10,cursor="hand2",command=self.refresh).pack(side="right",padx=5)

    def refresh(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        conn = get_connection()
        for r in conn.execute("SELECT id,nom,telephone,adresse,email,notes FROM fournisseurs ORDER BY nom").fetchall():
            self.tree.insert("","end", values=(r[0],r[1],r[2] or "-",r[3] or "-",r[4] or "-",r[5] or "-"))
        conn.close()

    def _open_form(self, fid=None):
        FormFournisseur(self, fid, on_save=self.refresh)

    def _edit(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("","Selectionnez un fournisseur."); return
        self._open_form(self.tree.item(sel[0])["values"][0])

    def _delete(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("","Selectionnez un fournisseur."); return
        fid = self.tree.item(sel[0])["values"][0]
        nom = self.tree.item(sel[0])["values"][1]
        if messagebox.askyesno("Supprimer",f"Supprimer '{nom}' ?"):
            conn = get_connection()
            conn.execute("DELETE FROM fournisseurs WHERE id=?", (fid,))
            conn.commit(); conn.close(); self.refresh()


class FormFournisseur(tk.Toplevel):
    def __init__(self, parent, fid=None, on_save=None):
        super().__init__(parent)
        self.fid = fid; self.on_save = on_save
        self.title("Modifier fournisseur" if fid else "Nouveau fournisseur")
        self.geometry("400x300"); self.resizable(False,False)
        self.configure(bg="#f0f4f8"); self.grab_set()
        fields = [("Nom *","nom"),("Telephone","tel"),("Adresse","adresse"),("Email","email"),("Notes","notes")]
        self.vars = {}
        for i,(label,key) in enumerate(fields):
            tk.Label(self,text=label,bg="#f0f4f8",font=("Arial",9)).grid(row=i,column=0,sticky="w",padx=20,pady=7)
            var=tk.StringVar(); self.vars[key]=var
            tk.Entry(self,textvariable=var,width=28,font=("Arial",10)).grid(row=i,column=1,padx=10,pady=7)
        tk.Button(self,text="Enregistrer",bg="#f39c12",fg="white",font=("Arial",10,"bold"),relief="flat",padx=15,pady=6,
                  command=self._save).grid(row=len(fields),column=0,columnspan=2,pady=15)
        if fid: self._load()

    def _load(self):
        conn = get_connection()
        r = conn.execute("SELECT nom,telephone,adresse,email,notes FROM fournisseurs WHERE id=?",(self.fid,)).fetchone()
        conn.close()
        if r:
            for k,v in zip(["nom","tel","adresse","email","notes"],r): self.vars[k].set(v or "")

    def _save(self):
        nom = self.vars["nom"].get().strip()
        if not nom: messagebox.showerror("Erreur","Nom obligatoire.",parent=self); return
        conn = get_connection()
        if self.fid:
            conn.execute("UPDATE fournisseurs SET nom=?,telephone=?,adresse=?,email=?,notes=? WHERE id=?",
                         (nom,self.vars["tel"].get(),self.vars["adresse"].get(),self.vars["email"].get(),self.vars["notes"].get(),self.fid))
        else:
            conn.execute("INSERT INTO fournisseurs (nom,telephone,adresse,email,notes) VALUES (?,?,?,?,?)",
                         (nom,self.vars["tel"].get(),self.vars["adresse"].get(),self.vars["email"].get(),self.vars["notes"].get()))
        conn.commit(); conn.close()
        if self.on_save: self.on_save()
        self.destroy()
