# vente_rapide.py — L'admin peut aussi enregistrer des ventes

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import threading, os, sys, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database import get_connection
from facture import generer_facture
from config import MONNAIE, UNITE_DEFAULT
from reduction import calculer_reduction


class VenteRapideFrame(tk.Frame):
    """Interface de vente rapide pour l'Admin — identique a celle de l'employe."""

    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.controller      = controller
        self._produit_map    = {}
        self._last_vente_id  = None
        self._red_palier     = 0
        self._red_quantite   = 0
        self._build()

    def _build(self):
        tk.Label(self, text="Enregistrer une Vente",
                 font=("Arial", 18, "bold"), bg="#f0f4f8", fg="#1a2940").pack(anchor="w", padx=30, pady=(20, 3))
        tk.Label(self, text="L'admin peut enregistrer une vente directement ici",
                 font=("Arial", 9), bg="#f0f4f8", fg="#667788").pack(anchor="w", padx=30, pady=(0, 12))

        card = tk.Frame(self, bg="white", highlightbackground="#dde3ed", highlightthickness=1)
        card.pack(fill="x", padx=30, pady=5)

        fields = [
            ("Produit *",                       "produit"),
            (f"Quantite ({UNITE_DEFAULT}s) *",  "quantite"),
            (f"Prix unitaire ({MONNAIE}) *",    "prix_unit"),
            ("Client",                          "client"),
            ("Notes",                           "notes"),
            ("Date",                            "date"),
        ]
        self.vars = {}

        for i, (label, key) in enumerate(fields):
            tk.Label(card, text=label, font=("Arial", 9, "bold"),
                     bg="white", fg="#334455").grid(row=i, column=0, sticky="w", padx=20, pady=7)
            if key == "produit":
                self.pvar = tk.StringVar()
                self.pcb  = ttk.Combobox(card, textvariable=self.pvar, width=32, state="readonly")
                self.pcb.grid(row=i, column=1, padx=10, pady=7, sticky="w")
                self.pcb.bind("<<ComboboxSelected>>", self._on_produit)
                self.vars[key] = self.pvar
            else:
                var = tk.StringVar(); self.vars[key] = var
                e = tk.Entry(card, textvariable=var, width=34, font=("Arial", 10))
                e.grid(row=i, column=1, padx=10, pady=7, sticky="w")
                if key == "date":
                    var.set(datetime.now().strftime("%Y-%m-%d"))
                if key in ("quantite", "prix_unit"):
                    e.bind("<KeyRelease>", self._update_total)

        # Stock + offre
        self.lbl_stock = tk.Label(card, text="Stock: -", font=("Arial", 9, "italic"),
                                   bg="white", fg="#667788")
        self.lbl_stock.grid(row=0, column=2, padx=10, sticky="w")

        # Total
        tf = tk.Frame(card, bg="#fef9e7")
        tf.grid(row=len(fields), column=0, columnspan=3, sticky="ew", padx=20, pady=5)
        tk.Label(tf, text="Total:", font=("Arial", 11, "bold"),
                 bg="#fef9e7", fg="#1a2940").pack(side="left", padx=15, pady=8)
        self.total_lbl = tk.Label(tf, text=f"0 {MONNAIE}",
                                   font=("Arial", 14, "bold"), bg="#fef9e7", fg="#f39c12")
        self.total_lbl.pack(side="left")

        # Bloc réduction
        self.red_frame = tk.Frame(card, bg="#eafaf1")
        self.red_frame.grid(row=len(fields)+1, column=0, columnspan=3, sticky="ew", padx=20, pady=3)
        self.red_lbl = tk.Label(self.red_frame, text="", font=("Arial", 9, "italic"),
                                 bg="#eafaf1", fg="#27ae60")
        self.red_lbl.pack(anchor="w", padx=10, pady=4)

        # Boutons
        bf = tk.Frame(card, bg="white")
        bf.grid(row=len(fields)+2, column=0, columnspan=3, pady=12)
        tk.Button(bf, text="Enregistrer la vente", font=("Arial", 10, "bold"),
                  bg="#f39c12", fg="white", relief="flat", padx=18, pady=7,
                  cursor="hand2", command=self._save).pack(side="left", padx=8)
        self.btn_pdf = tk.Button(bf, text="Generer Facture PDF",
                                  font=("Arial", 10, "bold"), bg="#4a90d9", fg="white",
                                  relief="flat", padx=18, pady=7, cursor="hand2",
                                  state="disabled", command=self._generer_facture)
        self.btn_pdf.pack(side="left", padx=8)

        # Historique du jour
        tk.Label(self, text="Ventes du jour", font=("Arial", 12, "bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(anchor="w", padx=30, pady=(15, 5))
        cols = ("ID", "Produit", "Qte", "Prix", "Total", "Offerts", "Client", "Heure")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=6)
        for c, w in zip(cols, [40, 150, 55, 90, 110, 65, 110, 75]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="x", padx=30)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.status_lbl = tk.Label(self, text="", font=("Arial", 9, "italic"),
                                    bg="#f0f4f8", fg="#27ae60")
        self.status_lbl.pack(anchor="w", padx=30, pady=5)
        self.refresh()

    def _on_produit(self, event=None):
        pid = self._produit_map.get(self.pvar.get())
        if not pid: return
        conn = get_connection()
        row  = conn.execute(
            "SELECT stock_actuel, prix_vente, reduction_palier, reduction_quantite FROM produits WHERE id=?",
            (pid,)).fetchone()
        conn.close()
        if row:
            self._red_palier   = row[2] or 0
            self._red_quantite = row[3] or 0
            fg   = "#27ae60" if row[0] > 0 else "#e74c3c"
            info = f"Stock: {row[0]} {UNITE_DEFAULT}s"
            if self._red_palier > 0:
                info += f"  |  Offre: {self._red_palier} achetes = +{self._red_quantite} offerts"
            self.lbl_stock.config(text=info, fg=fg)
            if not self.vars["prix_unit"].get():
                self.vars["prix_unit"].set(str(row[1]))
            self._update_total()

    def _update_total(self, event=None):
        try:
            qty  = int(self.vars["quantite"].get())
            prix = float(self.vars["prix_unit"].get())
            red  = calculer_reduction(qty, self._red_palier, self._red_quantite, prix)
            self.total_lbl.config(text=f"{red['prix_total']:,.0f} {MONNAIE}")
            if red["paquets_offerts"] > 0:
                self.red_lbl.config(
                    text=f"Cadeau: {red['detail']}  ->  "
                         f"Vous recevez {qty + red['paquets_offerts']} {UNITE_DEFAULT}s au total !")
            else:
                self.red_lbl.config(text=red["detail"] if self._red_palier > 0 else "")
        except (ValueError, AttributeError):
            self.total_lbl.config(text=f"0 {MONNAIE}")
            self.red_lbl.config(text="")

    def refresh(self):
        conn = get_connection()
        self._produit_map = {r[1]: r[0] for r in conn.execute(
            "SELECT id, nom FROM produits WHERE stock_actuel > 0 ORDER BY nom").fetchall()}
        conn.close()
        self.pcb["values"] = list(self._produit_map.keys())
        today = datetime.now().strftime("%Y-%m-%d")
        for r in self.tree.get_children(): self.tree.delete(r)
        conn = get_connection()
        rows = conn.execute("""
            SELECT v.id, p.nom, v.quantite, v.prix_unitaire, v.prix_total,
                   COALESCE(v.paquets_offerts, 0), COALESCE(v.client, '-'), v.date_vente
            FROM ventes v JOIN produits p ON v.produit_id = p.id
            WHERE DATE(v.date_vente) = ? ORDER BY v.date_vente DESC
        """, (today,)).fetchall()
        conn.close()
        for r in rows:
            self.tree.insert("", "end", values=(
                r[0], r[1], r[2], f"{r[3]:.0f}", f"{r[4]:,.0f}",
                f"+{r[5]}" if r[5] > 0 else "-", r[6], str(r[7])[11:16]))

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if sel:
            self._last_vente_id = self.tree.item(sel[0])["values"][0]
            self.btn_pdf.config(state="normal")

    def _save(self):
        nom = self.pvar.get()
        if not nom or nom not in self._produit_map:
            messagebox.showerror("Erreur", "Selectionnez un produit."); return
        try:
            qty  = int(self.vars["quantite"].get())
            prix = float(self.vars["prix_unit"].get())
            if qty <= 0 or prix < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Quantite et prix invalides."); return

        pid   = self._produit_map[nom]
        conn  = get_connection()
        stock = conn.execute("SELECT stock_actuel FROM produits WHERE id=?", (pid,)).fetchone()[0]
        if qty > stock:
            messagebox.showerror("Stock insuffisant", f"Stock: {stock}  Demande: {qty}")
            conn.close(); return

        red   = calculer_reduction(qty, self._red_palier, self._red_quantite, prix)
        total = red["prix_total"]
        offs  = red["paquets_offerts"]
        date  = self.vars["date"].get() or datetime.now().strftime("%Y-%m-%d")

        cur = conn.execute("""
            INSERT INTO ventes (produit_id, quantite, prix_unitaire, prix_total,
                                paquets_offerts, date_vente, client, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (pid, qty, prix, total, offs, date,
              self.vars["client"].get() or None, self.vars["notes"].get() or None))
        self._last_vente_id = cur.lastrowid

        conn.execute("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE id=?", (qty + offs, pid))
        conn.execute("INSERT INTO mouvements (produit_id, type, quantite, motif) VALUES (?,?,?,?)",
                     (pid, "sortie", qty + offs, "Vente admin"))
        conn.commit(); conn.close()

        self.btn_pdf.config(state="normal")
        msg = f"Vente #{self._last_vente_id} — {total:,.0f} {MONNAIE}"
        if offs > 0: msg += f"  |  +{offs} {UNITE_DEFAULT}(s) offert(s) !"
        self.status_lbl.config(text=msg, fg="#27ae60")

        for k in ("quantite", "prix_unit", "client", "notes"): self.vars[k].set("")
        self.total_lbl.config(text=f"0 {MONNAIE}")
        self.red_lbl.config(text="")
        self.lbl_stock.config(text="Stock: -")
        self._red_palier = self._red_quantite = 0
        self.refresh()

        if messagebox.askyesno("Facture", "Generer la facture PDF maintenant ?"):
            self._generer_facture()

    def _generer_facture(self):
        if not self._last_vente_id:
            messagebox.showwarning("Attention", "Aucune vente selectionnee."); return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
            initialfile=f"facture_{self._last_vente_id:04d}.pdf",
            title="Enregistrer la facture")
        if not path: return

        def run():
            try:
                generer_facture(self._last_vente_id, path)
                self.after(0, lambda: self.status_lbl.config(
                    text=f"Facture: {os.path.basename(path)}", fg="#27ae60"))
                self.after(0, lambda: self._ouvrir(path))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erreur", str(e)))
        threading.Thread(target=run, daemon=True).start()

    def _ouvrir(self, path):
        try:
            os.startfile(path) if sys.platform == "win32" else subprocess.Popen(["xdg-open", path])
        except: pass
