# vente_rapide.py — MODERNE CustomTkinter
import customtkinter as ctk
import tkinter.ttk as ttk
import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime
import threading, os, sys, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from facture import generer_facture
from config import MONNAIE, UNITE_DEFAULT
from reduction import calculer_reduction


def _style_tree():
    s = ttk.Style()
    s.configure("Dark.Treeview",
        background="#2b2b2b", foreground="white",
        fieldbackground="#2b2b2b", rowheight=28, font=("Arial",11))
    s.configure("Dark.Treeview.Heading",
        background="#1a1a2e", foreground="#7EB3FF",
        font=("Arial",11,"bold"), relief="flat")
    s.map("Dark.Treeview", background=[("selected","#1f6aa5")])


class VenteRapideFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.controller      = controller
        self._produit_map    = {}
        self._last_vente_id  = None
        self._red_palier     = 0
        self._red_quantite   = 0
        _style_tree()
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Enregistrer une Vente",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=30, pady=(22,2))
        ctk.CTkLabel(self, text="L'admin peut enregistrer une vente directement ici",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", padx=30, pady=(0,14))

        # Formulaire
        card = ctk.CTkFrame(self, corner_radius=14)
        card.pack(fill="x", padx=30, pady=5)

        # Produit
        row0 = ctk.CTkFrame(card, fg_color="transparent")
        row0.pack(fill="x", padx=20, pady=(16,4))
        ctk.CTkLabel(row0, text="Produit *",
                     font=ctk.CTkFont(size=12, weight="bold"), width=180, anchor="w").pack(side="left")
        self.pvar = tk.StringVar()
        self.pcb = ttk.Combobox(row0, textvariable=self.pvar, width=30, state="readonly")
        self.pcb.pack(side="left", padx=8)
        self.lbl_stock = ctk.CTkLabel(row0, text="Stock: -", font=ctk.CTkFont(size=11),
                                       text_color="gray", width=160, anchor="w")
        self.lbl_stock.pack(side="left", padx=8)
        self.pcb.bind("<<ComboboxSelected>>", self._on_produit)

        self.vars = {"produit": self.pvar}

        input_fields = [
            (f"Quantité ({UNITE_DEFAULT}s) *", "quantite"),
            (f"Prix unitaire ({MONNAIE}) *",   "prix_unit"),
            ("Client",                          "client"),
            ("Notes",                           "notes"),
            ("Date",                            "date"),
        ]
        for label, key in input_fields:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(row, text=label,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         width=180, anchor="w").pack(side="left")
            var = tk.StringVar(); self.vars[key] = var
            e = ctk.CTkEntry(row, textvariable=var, width=280, height=34, corner_radius=8)
            e.pack(side="left", padx=8)
            if key == "date":
                var.set(datetime.now().strftime("%Y-%m-%d"))
            if key in ("quantite", "prix_unit"):
                e.bind("<KeyRelease>", self._update_total)

        # Total + réduction
        tf = ctk.CTkFrame(card, corner_radius=10, fg_color=("#fff8e1","#2e2a00"))
        tf.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(tf, text="Total :", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=15, pady=10)
        self.total_lbl = ctk.CTkLabel(tf, text=f"0 {MONNAIE}",
                                       font=ctk.CTkFont(size=18, weight="bold"),
                                       text_color="#f39c12")
        self.total_lbl.pack(side="left")
        self.red_lbl = ctk.CTkLabel(tf, text="", font=ctk.CTkFont(size=11),
                                     text_color="#27ae60")
        self.red_lbl.pack(side="left", padx=20)

        # Boutons
        bf = ctk.CTkFrame(card, fg_color="transparent")
        bf.pack(pady=(8, 16))
        ctk.CTkButton(bf, text="💰 Enregistrer la vente",
                      width=200, height=40, corner_radius=10,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color="#d68910", hover_color="#b7770d",
                      command=self._save).pack(side="left", padx=8)
        self.btn_pdf = ctk.CTkButton(bf, text="🖨 Facture PDF",
                                      width=160, height=40, corner_radius=10,
                                      font=ctk.CTkFont(size=13, weight="bold"),
                                      state="disabled",
                                      command=self._generer_facture)
        self.btn_pdf.pack(side="left", padx=8)

        # Historique du jour
        ctk.CTkLabel(self, text="Ventes du jour",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(
            anchor="w", padx=30, pady=(16,4))
        cols = ("ID","Produit","Qté","Prix","Total","Offerts","Client","Heure")
        self.tree = ttk.Treeview(self, columns=cols, show="headings",
                                  height=6, style="Dark.Treeview")
        for c, w in zip(cols, [40,150,55,90,110,65,110,75]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="x", padx=30)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.status_lbl = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11),
                                        text_color="#27ae60")
        self.status_lbl.pack(anchor="w", padx=30, pady=6)
        self.refresh()

    def _on_produit(self, _=None):
        pid = self._produit_map.get(self.pvar.get())
        if not pid: return
        conn = get_connection()
        row  = conn.execute(
            "SELECT stock_actuel,prix_vente,reduction_palier,reduction_quantite FROM produits WHERE id=?",
            (pid,)).fetchone()
        conn.close()
        if row:
            self._red_palier   = row[2] or 0
            self._red_quantite = row[3] or 0
            color = "#27ae60" if row[0] > 0 else "#e74c3c"
            info  = f"Stock: {row[0]} {UNITE_DEFAULT}s"
            if self._red_palier > 0:
                info += f"  |  Offre: {self._red_palier} → +{self._red_quantite} offerts"
            self.lbl_stock.configure(text=info, text_color=color)
            if not self.vars["prix_unit"].get():
                self.vars["prix_unit"].set(str(row[1]))
            self._update_total()

    def _update_total(self, _=None):
        try:
            qty  = int(self.vars["quantite"].get())
            prix = float(self.vars["prix_unit"].get())
            red  = calculer_reduction(qty, self._red_palier, self._red_quantite, prix)
            self.total_lbl.configure(text=f"{red['prix_total']:,.0f} {MONNAIE}")
            if red["paquets_offerts"] > 0:
                self.red_lbl.configure(
                    text=f"🎁 {red['detail']}  — reçoit {qty+red['paquets_offerts']} {UNITE_DEFAULT}s !")
            else:
                self.red_lbl.configure(text=red["detail"] if self._red_palier > 0 else "")
        except (ValueError, AttributeError):
            self.total_lbl.configure(text=f"0 {MONNAIE}")
            self.red_lbl.configure(text="")

    def refresh(self):
        conn = get_connection()
        self._produit_map = {r[1]: r[0] for r in conn.execute(
            "SELECT id,nom FROM produits WHERE stock_actuel>0 ORDER BY nom").fetchall()}
        conn.close()
        self.pcb["values"] = list(self._produit_map.keys())
        today = datetime.now().strftime("%Y-%m-%d")
        for r in self.tree.get_children(): self.tree.delete(r)
        conn = get_connection()
        for r in conn.execute("""
            SELECT v.id,p.nom,v.quantite,v.prix_unitaire,v.prix_total,
                   COALESCE(v.paquets_offerts,0),COALESCE(v.client,'-'),v.date_vente
            FROM ventes v JOIN produits p ON v.produit_id=p.id
            WHERE DATE(v.date_vente)=? ORDER BY v.date_vente DESC
        """, (today,)).fetchall():
            self.tree.insert("","end", values=(
                r[0],r[1],r[2],f"{r[3]:.0f}",f"{r[4]:,.0f}",
                f"+{r[5]}" if r[5] > 0 else "-", r[6], str(r[7])[11:16]))
        conn.close()

    def _on_select(self, _=None):
        sel = self.tree.selection()
        if sel:
            self._last_vente_id = self.tree.item(sel[0])["values"][0]
            self.btn_pdf.configure(state="normal")

    def _save(self):
        nom = self.pvar.get()
        if not nom or nom not in self._produit_map:
            messagebox.showerror("Erreur","Sélectionnez un produit."); return
        try:
            qty  = int(self.vars["quantite"].get())
            prix = float(self.vars["prix_unit"].get())
            if qty <= 0 or prix < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erreur","Quantité et prix invalides."); return

        pid  = self._produit_map[nom]
        conn = get_connection()
        stock = conn.execute("SELECT stock_actuel FROM produits WHERE id=?", (pid,)).fetchone()[0]
        if qty > stock:
            messagebox.showerror("Stock insuffisant", f"Stock: {stock}  Demande: {qty}")
            conn.close(); return

        red   = calculer_reduction(qty, self._red_palier, self._red_quantite, prix)
        total = red["prix_total"]; offs = red["paquets_offerts"]
        date  = self.vars["date"].get() or datetime.now().strftime("%Y-%m-%d")

        cur = conn.execute("""
            INSERT INTO ventes (produit_id,quantite,prix_unitaire,prix_total,
                                paquets_offerts,date_vente,client,notes)
            VALUES (?,?,?,?,?,?,?,?)
        """, (pid,qty,prix,total,offs,date,
              self.vars["client"].get() or None, self.vars["notes"].get() or None))
        self._last_vente_id = cur.lastrowid
        conn.execute("UPDATE produits SET stock_actuel=stock_actuel-? WHERE id=?", (qty+offs, pid))
        conn.execute("INSERT INTO mouvements (produit_id,type,quantite,motif) VALUES (?,?,?,?)",
                     (pid,"sortie",qty+offs,"Vente admin"))
        conn.commit(); conn.close()

        self.btn_pdf.configure(state="normal")
        msg = f"✅ Vente #{self._last_vente_id} — {total:,.0f} {MONNAIE}"
        if offs > 0: msg += f"  |  +{offs} {UNITE_DEFAULT}(s) offert(s) !"
        self.status_lbl.configure(text=msg)
        for k in ("quantite","prix_unit","client","notes"): self.vars[k].set("")
        self.total_lbl.configure(text=f"0 {MONNAIE}")
        self.red_lbl.configure(text="")
        self.lbl_stock.configure(text="Stock: -", text_color="gray")
        self._red_palier = self._red_quantite = 0
        self.refresh()
        if messagebox.askyesno("Facture", "Générer la facture PDF maintenant ?"):
            self._generer_facture()

    def _generer_facture(self):
        if not self._last_vente_id:
            messagebox.showwarning("Attention","Aucune vente sélectionnée."); return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF","*.pdf")],
            initialfile=f"facture_{self._last_vente_id:04d}.pdf")
        if not path: return
        def run():
            try:
                generer_facture(self._last_vente_id, path)
                self.after(0, lambda: self.status_lbl.configure(
                    text=f"📄 Facture: {os.path.basename(path)}"))
                self.after(0, lambda: self._ouvrir(path))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erreur", str(e)))
        threading.Thread(target=run, daemon=True).start()

    def _ouvrir(self, path):
        try:
            os.startfile(path) if sys.platform=="win32" else subprocess.Popen(["xdg-open",path])
        except: pass
