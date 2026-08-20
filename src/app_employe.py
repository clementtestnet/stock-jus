"""
app_employe.py — Interface pour les employes (Ventes + Facture PDF uniquement)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import threading, os, sys, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from database import get_connection
from facture import generer_facture
from config import MONNAIE, BOUTIQUE_NOM, UNITE_DEFAULT
from reduction import calculer_reduction


class AppEmploye(tk.Tk):
    def __init__(self, user_info):
        super().__init__()
        self.user_info       = user_info
        self._produit_map    = {}
        self._last_vente_id  = None
        self._red_palier     = 0
        self._red_quantite   = 0
        self._last_reduction = None
        self.title(f"🧃 {BOUTIQUE_NOM} — {user_info['nom']}")
        self.geometry("900x700")
        self.minsize(700, 550)
        self.configure(bg="#f0f4f8")
        self._build()

    def _build(self):
        # ── Barre du haut ────────────────────────────────────────
        top = tk.Frame(self, bg="#1a2940", height=50)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text=f"🧃 {BOUTIQUE_NOM}", font=("Arial", 13, "bold"),
                 bg="#1a2940", fg="white").pack(side="left", padx=20)
        tk.Label(top, text=f"👷 {self.user_info['nom']}  |  Employé",
                 font=("Arial", 9), bg="#1a2940", fg="#8899aa").pack(side="left", padx=10)
        tk.Button(top, text="🚪 Déconnexion", font=("Arial", 9),
                  bg="#e74c3c", fg="white", relief="flat", padx=10,
                  cursor="hand2", command=self._deconnexion).pack(side="right", padx=15, pady=8)

        # ── Corps ────────────────────────────────────────────────
        body = tk.Frame(self, bg="#f0f4f8")
        body.pack(fill="both", expand=True, padx=30, pady=20)

        tk.Label(body, text="Nouvelle Vente", font=("Arial", 16, "bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(anchor="w")
        tk.Label(body, text="Remplissez le formulaire puis générez la facture PDF",
                 font=("Arial", 9), bg="#f0f4f8", fg="#667788").pack(anchor="w", pady=(0, 15))

        # Formulaire
        card = tk.Frame(body, bg="white", highlightbackground="#dde3ed", highlightthickness=1)
        card.pack(fill="x", pady=5)

        fields = [
            ("Produit *",                        "produit"),
            (f"Quantité ({UNITE_DEFAULT}s) *",   "quantite"),
            (f"Prix unitaire ({MONNAIE}) *",     "prix_unit"),
            ("Client",                           "client"),
            ("Notes",                            "notes"),
            ("Date",                             "date"),
        ]
        self.vars = {}

        for i, (label, key) in enumerate(fields):
            tk.Label(card, text=label, font=("Arial", 9, "bold"),
                     bg="white", fg="#334455").grid(row=i, column=0, sticky="w", padx=20, pady=7)
            if key == "produit":
                self.produit_var = tk.StringVar()
                self.produit_cb  = ttk.Combobox(card, textvariable=self.produit_var,
                                                 width=32, state="readonly")
                self.produit_cb.grid(row=i, column=1, padx=10, pady=7, sticky="w")
                self.produit_cb.bind("<<ComboboxSelected>>", self._on_produit_change)
                self.vars[key] = self.produit_var
            else:
                var = tk.StringVar()
                self.vars[key] = var
                e = tk.Entry(card, textvariable=var, width=34, font=("Arial", 10))
                e.grid(row=i, column=1, padx=10, pady=7, sticky="w")
                if key == "date":
                    var.set(datetime.now().strftime("%Y-%m-%d"))
                if key in ("quantite", "prix_unit"):
                    e.bind("<KeyRelease>", self._update_total)

        # Stock dispo
        self.lbl_stock = tk.Label(card, text="Stock : —", font=("Arial", 9, "italic"),
                                   bg="white", fg="#667788")
        self.lbl_stock.grid(row=0, column=2, padx=10, sticky="w")

        # Total
        total_f = tk.Frame(card, bg="#fef9e7")
        total_f.grid(row=len(fields), column=0, columnspan=3, sticky="ew", padx=20, pady=5)
        tk.Label(total_f, text="Total :", font=("Arial", 11, "bold"),
                 bg="#fef9e7", fg="#1a2940").pack(side="left", padx=15, pady=8)
        self.total_lbl = tk.Label(total_f, text=f"0 {MONNAIE}",
                                   font=("Arial", 14, "bold"), bg="#fef9e7", fg="#f39c12")
        self.total_lbl.pack(side="left")

        # Bloc réduction
        self.red_frame = tk.Frame(card, bg="#eafaf1")
        self.red_frame.grid(row=len(fields)+1, column=0, columnspan=3,
                             sticky="ew", padx=20, pady=3)
        self.red_lbl = tk.Label(self.red_frame, text="", font=("Arial", 9, "italic"),
                                 bg="#eafaf1", fg="#27ae60")
        self.red_lbl.pack(anchor="w", padx=10, pady=5)

        # Boutons
        btn_f = tk.Frame(card, bg="white")
        btn_f.grid(row=len(fields)+2, column=0, columnspan=3, pady=12)

        tk.Button(btn_f, text="💰 Enregistrer la vente", font=("Arial", 10, "bold"),
                  bg="#f39c12", fg="white", relief="flat", padx=18, pady=7,
                  cursor="hand2", command=self._save_vente).pack(side="left", padx=8)

        self.btn_facture = tk.Button(btn_f, text="🖨️ Générer Facture PDF",
                                      font=("Arial", 10, "bold"),
                                      bg="#4a90d9", fg="white", relief="flat",
                                      padx=18, pady=7, cursor="hand2",
                                      state="disabled", command=self._generer_facture)
        self.btn_facture.pack(side="left", padx=8)

        # ── Historique ventes du jour ─────────────────────────────
        tk.Label(body, text="Mes ventes du jour", font=("Arial", 12, "bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(anchor="w", pady=(18, 5))

        cols = ("ID", "Produit", "Qté", f"Prix ({MONNAIE})", "Total", "Offerts", "Client", "Heure")
        self.tree = ttk.Treeview(body, columns=cols, show="headings", height=6)
        widths     = [40, 150, 60, 90, 100, 70, 110, 80]
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="x")
        self.tree.bind("<<TreeviewSelect>>", self._on_select_vente)

        # Status
        self.status_lbl = tk.Label(body, text="", font=("Arial", 9, "italic"),
                                    bg="#f0f4f8", fg="#27ae60")
        self.status_lbl.pack(anchor="w", pady=5)

        self.refresh()

    # ── Logique produit & réduction ───────────────────────────────
    def _on_produit_change(self, event=None):
        nom = self.produit_var.get()
        pid = self._produit_map.get(nom)
        if pid:
            conn = get_connection()
            row = conn.execute(
                "SELECT stock_actuel, prix_vente, reduction_palier, reduction_quantite FROM produits WHERE id=?",
                (pid,)).fetchone()
            conn.close()
            if row:
                color = "#27ae60" if row[0] > 0 else "#e74c3c"
                self.lbl_stock.config(text=f"Stock : {row[0]} {UNITE_DEFAULT}s", fg=color)
                if not self.vars["prix_unit"].get():
                    self.vars["prix_unit"].set(str(row[1]))
                self._red_palier   = row[2] or 0
                self._red_quantite = row[3] or 0
                # Afficher la règle de réduction
                if self._red_palier > 0:
                    self.lbl_stock.config(
                        text=f"Stock : {row[0]} {UNITE_DEFAULT}s  |  "
                             f"🎁 Offre : {self._red_palier} achetés = +{self._red_quantite} offerts"
                    )
                self._update_total()

    def _update_total(self, event=None):
        try:
            qty  = int(self.vars["quantite"].get())
            prix = float(self.vars["prix_unit"].get())
            red  = calculer_reduction(qty, self._red_palier, self._red_quantite, prix)
            self.total_lbl.config(text=f"{red['prix_total']:,.0f} {MONNAIE}")
            if red["paquets_offerts"] > 0:
                self.red_lbl.config(
                    text=f"🎁 {red['detail']}  →  "
                         f"Vous recevez {qty + red['paquets_offerts']} {UNITE_DEFAULT}s au total !"
                )
                self.red_frame.config(bg="#eafaf1")
                self.red_lbl.config(bg="#eafaf1")
            else:
                self.red_lbl.config(
                    text=red["detail"] if self._red_palier > 0 else ""
                )
            self._last_reduction = red
        except (ValueError, AttributeError):
            self.total_lbl.config(text=f"0 {MONNAIE}")
            self.red_lbl.config(text="")
            self._last_reduction = None

    # ── Refresh & historique ──────────────────────────────────────
    def refresh(self):
        conn = get_connection()
        produits = conn.execute(
            "SELECT id, nom FROM produits WHERE stock_actuel > 0 ORDER BY nom"
        ).fetchall()
        conn.close()
        self._produit_map = {p[1]: p[0] for p in produits}
        self.produit_cb["values"] = list(self._produit_map.keys())
        self._load_today()

    def _load_today(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        today = datetime.now().strftime("%Y-%m-%d")
        conn  = get_connection()
        rows  = conn.execute("""
            SELECT v.id, p.nom, v.quantite, v.prix_unitaire, v.prix_total,
                   COALESCE(v.paquets_offerts, 0), COALESCE(v.client,'—'), v.date_vente
            FROM ventes v JOIN produits p ON v.produit_id = p.id
            WHERE DATE(v.date_vente) = ?
            ORDER BY v.date_vente DESC
        """, (today,)).fetchall()
        conn.close()
        for r in rows:
            self.tree.insert("", "end", values=(
                r[0], r[1], r[2], f"{r[3]:.0f}",
                f"{r[4]:,.0f}", f"+{r[5]}" if r[5] > 0 else "—",
                r[6], str(r[7])[11:16]
            ))

    def _on_select_vente(self, event=None):
        sel = self.tree.selection()
        if sel:
            self._last_vente_id = self.tree.item(sel[0])["values"][0]
            self.btn_facture.config(state="normal")

    # ── Enregistrer vente ─────────────────────────────────────────
    def _save_vente(self):
        produit_nom = self.vars["produit"].get()
        if not produit_nom or produit_nom not in self._produit_map:
            messagebox.showerror("Erreur", "Sélectionnez un produit valide.")
            return
        try:
            qty       = int(self.vars["quantite"].get())
            prix_unit = float(self.vars["prix_unit"].get())
            if qty <= 0 or prix_unit < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Quantité et prix doivent être des nombres positifs.")
            return

        produit_id = self._produit_map[produit_nom]
        conn       = get_connection()
        stock      = conn.execute("SELECT stock_actuel FROM produits WHERE id=?",
                                   (produit_id,)).fetchone()[0]
        if qty > stock:
            messagebox.showerror("Stock insuffisant",
                                  f"Stock dispo : {stock} {UNITE_DEFAULT}s\nDemande : {qty}")
            conn.close()
            return

        # Calcul réduction
        red           = calculer_reduction(qty, self._red_palier, self._red_quantite, prix_unit)
        prix_total    = red["prix_total"]
        paquets_offerts = red["paquets_offerts"]
        date_vente    = self.vars["date"].get() or datetime.now().strftime("%Y-%m-%d")

        cur = conn.execute("""
            INSERT INTO ventes (produit_id, quantite, prix_unitaire, prix_total,
                                paquets_offerts, date_vente, client, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (produit_id, qty, prix_unit, prix_total, paquets_offerts, date_vente,
              self.vars["client"].get() or None, self.vars["notes"].get() or None))
        self._last_vente_id = cur.lastrowid

        # Déduire du stock (quantite commandée + paquets offerts)
        total_sortie = qty + paquets_offerts
        conn.execute("UPDATE produits SET stock_actuel = stock_actuel - ? WHERE id=?",
                     (total_sortie, produit_id))
        conn.execute("""
            INSERT INTO mouvements (produit_id, type, quantite, motif)
            VALUES (?, 'sortie', ?, ?)
        """, (produit_id, total_sortie,
              f"Vente par {self.user_info['nom']} — {paquets_offerts} offerts"))
        conn.commit()
        conn.close()

        self.btn_facture.config(state="normal")
        msg = f"✅ Vente #{self._last_vente_id} enregistrée — {prix_total:,.0f} {MONNAIE}"
        if paquets_offerts > 0:
            msg += f"  |  🎁 {paquets_offerts} {UNITE_DEFAULT}(s) offert(s) !"
        self.status_lbl.config(text=msg)

        # Reset
        for k in ("quantite", "prix_unit", "client", "notes"):
            self.vars[k].set("")
        self.total_lbl.config(text=f"0 {MONNAIE}")
        self.red_lbl.config(text="")
        self.lbl_stock.config(text="Stock : —")
        self._last_reduction = None
        self.refresh()

        if messagebox.askyesno("Facture", "Vente enregistrée !\nGénérer la facture PDF maintenant ?"):
            self._generer_facture()

    # ── Facture PDF ───────────────────────────────────────────────
    def _generer_facture(self):
        if not self._last_vente_id:
            messagebox.showwarning("Attention", "Aucune vente sélectionnée.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"facture_{self._last_vente_id:04d}.pdf",
            title="Enregistrer la facture"
        )
        if not path:
            return

        def run():
            try:
                generer_facture(self._last_vente_id, path)
                self.after(0, lambda: self.status_lbl.config(
                    text=f"✅ Facture générée : {os.path.basename(path)}"))
                self.after(0, lambda: self._open_pdf(path))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erreur", str(e)))

        threading.Thread(target=run, daemon=True).start()
        self.status_lbl.config(text="⏳ Génération de la facture...", fg="#f39c12")

    def _open_pdf(self, path):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

    def _deconnexion(self):
        self.destroy()
        import subprocess as sp
        sp.Popen([sys.executable, os.path.join(os.path.dirname(__file__), "main.py")])
