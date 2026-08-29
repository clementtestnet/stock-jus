# frames/sorties.py
import customtkinter as ctk
import tkinter.ttk as ttk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from config import UNITE_DEFAULT


def _apply_tree_style():
    s = ttk.Style()
    s.configure("Dark.Treeview",
        background="#2b2b2b", foreground="white",
        fieldbackground="#2b2b2b", rowheight=28, font=("Arial",11))
    s.configure("Dark.Treeview.Heading",
        background="#1a1a2e", foreground="#7EB3FF",
        font=("Arial",11,"bold"), relief="flat")
    s.map("Dark.Treeview", background=[("selected","#1f6aa5")])


class SortiesFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.controller   = controller
        self._produit_map = {}
        _apply_tree_style()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="🟣 Sorties — Transfert Boutique",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(22,2))
        ctk.CTkLabel(self,
                     text="Produits transférés vers une autre boutique (pas vendus au client)",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(
            anchor="w", padx=30, pady=(0,14))

        card = ctk.CTkFrame(self, corner_radius=14)
        card.pack(fill="x", padx=30, pady=5)

        # Produit
        r0 = ctk.CTkFrame(card, fg_color="transparent")
        r0.pack(fill="x", padx=20, pady=(16,4))
        ctk.CTkLabel(r0, text="Produit *",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     width=220, anchor="w").pack(side="left")
        self.pvar = tk.StringVar()
        self.pcb  = ttk.Combobox(r0, textvariable=self.pvar, width=30, state="readonly")
        self.pcb.pack(side="left", padx=8)
        self.pcb.bind("<<ComboboxSelected>>", self._on_produit)
        self.lbl_stock = ctk.CTkLabel(r0, text="",
                                       font=ctk.CTkFont(size=11),
                                       text_color="gray", width=160, anchor="w")
        self.lbl_stock.pack(side="left", padx=8)

        self.vars = {"produit": self.pvar}
        for label, key in [
            (f"Quantité ({UNITE_DEFAULT}s) *",          "quantite"),
            ("Boutique destinataire *",                   "destination"),
            ("Motif (ex: approvisionnement)",             "motif"),
            ("Date",                                      "date"),
            ("Notes",                                     "notes"),
        ]:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(row, text=label,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         width=220, anchor="w").pack(side="left")
            var = tk.StringVar(); self.vars[key] = var
            ctk.CTkEntry(row, textvariable=var, width=280, height=34,
                         corner_radius=8).pack(side="left", padx=8)
            if key == "date": var.set(datetime.now().strftime("%Y-%m-%d"))

        ctk.CTkButton(card, text="🟣 Enregistrer la sortie",
                      height=44, corner_radius=10,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color="#7d3c98", hover_color="#6c3483",
                      command=self._save).pack(fill="x", padx=20, pady=(8,18))

        # Historique
        ctk.CTkLabel(self, text="Historique des sorties",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(
            anchor="w", padx=30, pady=(16,4))
        cols = ("Date","Produit","Quantité","Destination","Motif","Notes")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  height=8, style="Dark.Treeview")
        for c, w in zip(cols, [130,160,80,160,160,160]):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="x", padx=30, pady=5)

        self.status_lbl = ctk.CTkLabel(self, text="",
                                        font=ctk.CTkFont(size=11),
                                        text_color="#9b59b6")
        self.status_lbl.pack(anchor="w", padx=30, pady=4)
        self.refresh()

    def _on_produit(self, _=None):
        info = self._produit_map.get(self.pvar.get())
        if info:
            color = "#27ae60" if info["stock"] > 0 else "#e74c3c"
            self.lbl_stock.configure(
                text=f"Stock: {info['stock']} {UNITE_DEFAULT}s", text_color=color)

    def refresh(self):
        conn = get_connection()
        rows = conn.execute(
            "SELECT id,nom,stock_actuel FROM produits WHERE stock_actuel>0 ORDER BY nom"
        ).fetchall()
        conn.close()
        self._produit_map = {r[1]:{"id":r[0],"stock":r[2]} for r in rows}
        self.pcb["values"] = list(self._produit_map.keys())
        self._load_hist()

    def _load_hist(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        conn = get_connection()
        for r in conn.execute("""
            SELECT s.date_sortie,
                   COALESCE(p.nom, s.produit_nom, '[supprimé]'),
                   s.quantite, s.destination,
                   COALESCE(s.motif,'-'), COALESCE(s.notes,'-')
            FROM sorties s LEFT JOIN produits p ON s.produit_id=p.id
            ORDER BY s.date_sortie DESC LIMIT 50
        """).fetchall():
            self.tree.insert("","end",
                values=(str(r[0])[:16],r[1],r[2],r[3],r[4],r[5]))
        conn.close()

    def _save(self):
        nom  = self.pvar.get()
        dest = self.vars["destination"].get().strip()
        if not nom or nom not in self._produit_map:
            messagebox.showerror("Erreur","Sélectionnez un produit."); return
        if not dest:
            messagebox.showerror("Erreur","Indiquez la boutique destinataire."); return
        try:
            qty = int(self.vars["quantite"].get())
            if qty <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erreur","Quantité invalide."); return

        pid  = self._produit_map[nom]["id"]
        conn = get_connection()
        stock = conn.execute(
            "SELECT stock_actuel FROM produits WHERE id=?", (pid,)).fetchone()[0]
        if qty > stock:
            messagebox.showerror("Stock insuffisant",
                f"Stock: {stock}  Demandé: {qty}")
            conn.close(); return

        date  = self.vars["date"].get() or datetime.now().strftime("%Y-%m-%d")
        motif = self.vars["motif"].get() or "Transfert boutique"
        conn.execute(
            "INSERT INTO sorties "
            "(produit_id,produit_nom,quantite,destination,motif,date_sortie,notes) "
            "VALUES (?,?,?,?,?,?,?)",
            (pid,nom,qty,dest,motif,date,self.vars["notes"].get() or None))
        conn.execute(
            "UPDATE produits SET stock_actuel=MAX(0, stock_actuel-?) WHERE id=?", (qty,pid))
        conn.execute(
            "INSERT INTO mouvements (produit_id,type,quantite,motif) VALUES (?,?,?,?)",
            (pid,"sortie",qty,f"Transfert vers {dest}"))
        conn.commit(); conn.close()

        self.status_lbl.configure(
            text=f"✅ {qty} {UNITE_DEFAULT}s transférés vers {dest}")
        for k in ("quantite","destination","motif","notes"): self.vars[k].set("")
        self.lbl_stock.configure(text="", text_color="gray")
        self.refresh()
        messagebox.showinfo("Succès", f"✅ {qty} {UNITE_DEFAULT}s → {dest}")
