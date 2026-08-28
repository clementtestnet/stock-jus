# vente_rapide.py — MODERNE : recherche live, prix fixe, multi-produits
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
        fieldbackground="#2b2b2b", rowheight=28, font=("Arial", 11))
    s.configure("Dark.Treeview.Heading",
        background="#1a1a2e", foreground="#7EB3FF",
        font=("Arial", 11, "bold"), relief="flat")
    s.map("Dark.Treeview", background=[("selected", "#1f6aa5")])


class VenteRapideFrame(ctk.CTkFrame):
    """
    Vente rapide multi-produits pour l'Admin.
    - Recherche live (tape une lettre → suggestions)
    - Prix unitaire prédéfini, non modifiable
    - Panier : plusieurs produits dans une seule vente
    - Enregistrement + Facture PDF
    """

    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.controller      = controller
        self._all_produits   = {}   # nom -> {id, prix, stock, palier, qte_offerte}
        self._panier         = []   # liste de dicts ligne
        self._last_vente_ids = []
        self._selecting      = False  # verrou : empeche trace de reset pendant selection
        _style_tree()
        self._build()

    # ─── Construction UI ────────────────────────────────────────────────────

    def _build(self):
        ctk.CTkLabel(self, text="Enregistrer une Vente",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(22, 2))
        ctk.CTkLabel(self,
                     text="Recherche rapide → Prix fixe → Ajouter au panier → Enregistrer",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(
            anchor="w", padx=30, pady=(0, 12))

        # ── Zone d'ajout d'un produit ──────────────────────────────────────
        add_card = ctk.CTkFrame(self, corner_radius=14)
        add_card.pack(fill="x", padx=30, pady=4)

        # Ligne 1 : Recherche produit
        r0 = ctk.CTkFrame(add_card, fg_color="transparent")
        r0.pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkLabel(r0, text="Produit *",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     width=150, anchor="w").pack(side="left")

        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            r0, textvariable=self.search_var,
            placeholder_text="Tapez le nom du produit...",
            width=260, height=36, corner_radius=8)
        self.search_entry.pack(side="left", padx=8)
        self.search_var.trace_add("write", self._on_search)

        # Listbox suggestions (cachée par défaut)
        self._suggest_frame = tk.Frame(self, bg="#1e2533", relief="flat", bd=1)
        self._suggest_lb = tk.Listbox(
            self._suggest_frame, bg="#1e2533", fg="white",
            selectbackground="#1f6aa5", font=("Arial", 12),
            relief="flat", bd=0, activestyle="none",
            height=5, width=32)
        self._suggest_lb.pack(fill="both", expand=True)
        self._suggest_lb.bind("<ButtonRelease-1>", self._on_suggest_select)
        self._suggest_lb.bind("<Return>",           self._on_suggest_select)

        self.lbl_stock = ctk.CTkLabel(r0, text="", font=ctk.CTkFont(size=11),
                                       text_color="#27ae60", width=200, anchor="w")
        self.lbl_stock.pack(side="left", padx=8)

        # Ligne 2 : Prix (lecture seule) + Quantité
        r1 = ctk.CTkFrame(add_card, fg_color="transparent")
        r1.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(r1, text=f"Prix ({MONNAIE})",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     width=150, anchor="w").pack(side="left")
        self.prix_var = tk.StringVar(value="—")
        self.prix_lbl = ctk.CTkLabel(r1, textvariable=self.prix_var,
                                      font=ctk.CTkFont(size=14, weight="bold"),
                                      text_color="#f39c12", width=120, anchor="w")
        self.prix_lbl.pack(side="left", padx=8)

        ctk.CTkLabel(r1, text=f"Quantité *",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     width=90, anchor="w").pack(side="left", padx=(20, 0))
        self.qty_var = tk.StringVar(value="1")
        self.qty_entry = ctk.CTkEntry(r1, textvariable=self.qty_var,
                                       width=80, height=34, corner_radius=8)
        self.qty_entry.pack(side="left", padx=8)
        self.qty_var.trace_add("write", self._update_preview)

        self.preview_lbl = ctk.CTkLabel(r1, text="",
                                         font=ctk.CTkFont(size=12),
                                         text_color="#27ae60")
        self.preview_lbl.pack(side="left", padx=12)

        # Ligne 3 : Bouton Ajouter
        r2 = ctk.CTkFrame(add_card, fg_color="transparent")
        r2.pack(fill="x", padx=20, pady=(6, 14))
        ctk.CTkButton(r2, text="➕ Ajouter au panier",
                      width=180, height=38, corner_radius=10,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color="#1f6aa5", hover_color="#164e8a",
                      command=self._ajouter_au_panier).pack(side="left")
        self.add_msg = ctk.CTkLabel(r2, text="", font=ctk.CTkFont(size=11),
                                     text_color="#27ae60")
        self.add_msg.pack(side="left", padx=12)

        # ── Panier ────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="🛒 Panier",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(
            anchor="w", padx=30, pady=(14, 4))

        pan_card = ctk.CTkFrame(self, corner_radius=14)
        pan_card.pack(fill="x", padx=30, pady=2)

        cols_pan = ("Produit", f"Qté ({UNITE_DEFAULT})", "Prix unit.", "Offerts", "Total")
        self.pan_tree = ttk.Treeview(pan_card, columns=cols_pan,
                                      show="headings", height=5,
                                      style="Dark.Treeview")
        for c, w in zip(cols_pan, [200, 90, 110, 80, 130]):
            self.pan_tree.heading(c, text=c)
            self.pan_tree.column(c, width=w, anchor="center")
        self.pan_tree.pack(fill="x", padx=12, pady=(10, 6))

        pan_btns = ctk.CTkFrame(pan_card, fg_color="transparent")
        pan_btns.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkButton(pan_btns, text="🗑 Supprimer ligne",
                      width=160, height=32, corner_radius=8,
                      fg_color="#c0392b", hover_color="#96281b",
                      command=self._supprimer_ligne).pack(side="left", padx=4)
        ctk.CTkButton(pan_btns, text="🧹 Vider panier",
                      width=140, height=32, corner_radius=8,
                      fg_color="gray40", hover_color="gray30",
                      command=self._vider_panier).pack(side="left", padx=4)
        self.total_panier_lbl = ctk.CTkLabel(
            pan_btns, text="Total : 0 FC",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#f39c12")
        self.total_panier_lbl.pack(side="right", padx=12)

        # ── Infos vente ────────────────────────────────────────────────────
        info_card = ctk.CTkFrame(self, corner_radius=14)
        info_card.pack(fill="x", padx=30, pady=6)

        ri = ctk.CTkFrame(info_card, fg_color="transparent")
        ri.pack(fill="x", padx=20, pady=(12, 8))

        ctk.CTkLabel(ri, text="Client", font=ctk.CTkFont(size=12, weight="bold"),
                     width=80, anchor="w").pack(side="left")
        self.client_var = tk.StringVar()
        ctk.CTkEntry(ri, textvariable=self.client_var, width=180, height=32,
                     corner_radius=8).pack(side="left", padx=8)

        ctk.CTkLabel(ri, text="Notes", font=ctk.CTkFont(size=12, weight="bold"),
                     width=60, anchor="w").pack(side="left", padx=(16, 0))
        self.notes_var = tk.StringVar()
        ctk.CTkEntry(ri, textvariable=self.notes_var, width=200, height=32,
                     corner_radius=8).pack(side="left", padx=8)

        ctk.CTkLabel(ri, text="Date", font=ctk.CTkFont(size=12, weight="bold"),
                     width=50, anchor="w").pack(side="left", padx=(16, 0))
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ctk.CTkEntry(ri, textvariable=self.date_var, width=110, height=32,
                     corner_radius=8).pack(side="left", padx=8)

        # Boutons finaux
        bf = ctk.CTkFrame(info_card, fg_color="transparent")
        bf.pack(pady=(4, 14))
        ctk.CTkButton(bf, text="💾 Enregistrer la vente",
                      width=210, height=42, corner_radius=10,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color="#d68910", hover_color="#b7770d",
                      command=self._save).pack(side="left", padx=8)
        self.btn_pdf = ctk.CTkButton(bf, text="🖨 Facture PDF",
                                      width=160, height=42, corner_radius=10,
                                      font=ctk.CTkFont(size=13, weight="bold"),
                                      state="disabled",
                                      command=self._generer_facture)
        self.btn_pdf.pack(side="left", padx=8)

        # ── Historique du jour ─────────────────────────────────────────────
        ctk.CTkLabel(self, text="Ventes du jour",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=30, pady=(14, 4))
        cols_h = ("ID", "Produit", "Qté", "Prix", "Total", "Offerts", "Client", "Heure")
        self.hist_tree = ttk.Treeview(self, columns=cols_h, show="headings",
                                       height=5, style="Dark.Treeview")
        for c, w in zip(cols_h, [40, 150, 55, 90, 110, 65, 110, 75]):
            self.hist_tree.heading(c, text=c)
            self.hist_tree.column(c, width=w, anchor="center")
        self.hist_tree.pack(fill="x", padx=30)
        self.hist_tree.bind("<<TreeviewSelect>>", self._on_hist_select)

        self.status_lbl = ctk.CTkLabel(self, text="",
                                        font=ctk.CTkFont(size=11),
                                        text_color="#27ae60")
        self.status_lbl.pack(anchor="w", padx=30, pady=6)

        # Produit courant sélectionné
        self._selected_produit = None   # dict ou None
        self.refresh()

    # ─── Recherche live ─────────────────────────────────────────────────────

    def _on_search(self, *_):
        # Si on est en train de sélectionner depuis la liste, ne pas réinitialiser
        if self._selecting:
            return
        q = self.search_var.get().strip().lower()
        self._selected_produit = None
        self.prix_var.set("—")
        self.lbl_stock.configure(text="", text_color="gray")
        self.preview_lbl.configure(text="")

        if not q:
            self._hide_suggest()
            return

        matches = [n for n in self._all_produits if q in n.lower()][:8]
        if not matches:
            self._hide_suggest()
            return

        self._suggest_lb.delete(0, "end")
        for m in matches:
            p = self._all_produits[m]
            self._suggest_lb.insert("end", f"{m}  ({p['stock']} {UNITE_DEFAULT}s — {p['prix']:.0f} {MONNAIE})")
        self._suggest_lb.config(height=min(len(matches), 6))
        self._show_suggest()

    def _show_suggest(self):
        x = self.search_entry.winfo_rootx() - self.winfo_rootx()
        y = self.search_entry.winfo_rooty() - self.winfo_rooty() + self.search_entry.winfo_height()
        self._suggest_frame.place(x=x + 48, y=y, width=380)
        self._suggest_frame.lift()

    def _hide_suggest(self):
        self._suggest_frame.place_forget()

    def _on_suggest_select(self, _=None):
        idx = self._suggest_lb.curselection()
        if not idx:
            return
        line = self._suggest_lb.get(idx[0])
        nom  = line.split("  (")[0]
        self._selecting = True      # verrou ON
        self._select_produit(nom)
        self._selecting = False     # verrou OFF

    def _select_produit(self, nom):
        p = self._all_produits.get(nom)
        if not p:
            return
        self._selected_produit = {"nom": nom, **p}
        self.search_var.set(nom)
        self.prix_var.set(f"{p['prix']:.0f} {MONNAIE}")
        color = "#27ae60" if p["stock"] > 0 else "#e74c3c"
        info  = f"Stock: {p['stock']} {UNITE_DEFAULT}s"
        if p["palier"] > 0:
            info += f"  |  Offre: {p['palier']} → +{p['qte_offerte']} offerts"
        self.lbl_stock.configure(text=info, text_color=color)
        self._hide_suggest()
        self.qty_entry.focus()
        self._update_preview()

    def _update_preview(self, *_):
        p = self._selected_produit
        if not p:
            self.preview_lbl.configure(text="")
            return
        try:
            qty = int(self.qty_var.get())
            if qty <= 0: raise ValueError
            red = calculer_reduction(qty, p["palier"], p["qte_offerte"], p["prix"])
            txt = f"= {red['prix_total']:,.0f} {MONNAIE}"
            if red["paquets_offerts"] > 0:
                txt += f"  🎁 +{red['paquets_offerts']} offerts"
            self.preview_lbl.configure(text=txt, text_color="#27ae60")
        except (ValueError, TypeError):
            self.preview_lbl.configure(text="")

    # ─── Panier ─────────────────────────────────────────────────────────────

    def _ajouter_au_panier(self):
        p = self._selected_produit
        if not p:
            self.add_msg.configure(text="⚠ Sélectionnez un produit.", text_color="#e74c3c")
            return
        try:
            qty = int(self.qty_var.get())
            if qty <= 0: raise ValueError
        except ValueError:
            self.add_msg.configure(text="⚠ Quantité invalide.", text_color="#e74c3c")
            return
        if qty > p["stock"]:
            self.add_msg.configure(
                text=f"⚠ Stock insuffisant ({p['stock']})", text_color="#e74c3c")
            return

        red = calculer_reduction(qty, p["palier"], p["qte_offerte"], p["prix"])
        ligne = {
            "nom":     p["nom"],
            "pid":     p["id"],
            "qty":     qty,
            "prix":    p["prix"],
            "offerts": red["paquets_offerts"],
            "total":   red["prix_total"],
            "palier":  p["palier"],
            "qte_offerte": p["qte_offerte"],
        }
        self._panier.append(ligne)
        self._refresh_panier()

        # Reset zone saisie
        self.search_var.set("")
        self.qty_var.set("1")
        self.prix_var.set("—")
        self.lbl_stock.configure(text="")
        self.preview_lbl.configure(text="")
        self._selected_produit = None
        self.add_msg.configure(
            text=f"✅ {p['nom']} ajouté au panier", text_color="#27ae60")
        self.search_entry.focus()

    def _refresh_panier(self):
        for r in self.pan_tree.get_children(): self.pan_tree.delete(r)
        total = 0
        for l in self._panier:
            self.pan_tree.insert("", "end", values=(
                l["nom"], l["qty"],
                f"{l['prix']:.0f} {MONNAIE}",
                f"+{l['offerts']}" if l["offerts"] > 0 else "-",
                f"{l['total']:,.0f} {MONNAIE}"))
            total += l["total"]
        self.total_panier_lbl.configure(text=f"Total : {total:,.0f} {MONNAIE}")

    def _supprimer_ligne(self):
        sel = self.pan_tree.selection()
        if not sel:
            return
        idx = self.pan_tree.index(sel[0])
        if 0 <= idx < len(self._panier):
            self._panier.pop(idx)
        self._refresh_panier()

    def _vider_panier(self):
        self._panier.clear()
        self._refresh_panier()

    # ─── Enregistrement ─────────────────────────────────────────────────────

    def _save(self):
        if not self._panier:
            messagebox.showerror("Erreur", "Le panier est vide."); return
        date_v = self.date_var.get() or datetime.now().strftime("%Y-%m-%d")
        client = self.client_var.get() or None
        notes  = self.notes_var.get() or None
        conn   = get_connection()
        # Vérif stocks
        for l in self._panier:
            stock = conn.execute(
                "SELECT stock_actuel FROM produits WHERE id=?", (l["pid"],)).fetchone()[0]
            if l["qty"] > stock:
                conn.close()
                messagebox.showerror(
                    "Stock insuffisant",
                    f"{l['nom']}: stock={stock}, demandé={l['qty']}")
                return

        self._last_vente_ids = []
        for l in self._panier:
            cur = conn.execute("""
                INSERT INTO ventes (produit_id,quantite,prix_unitaire,prix_total,
                                    paquets_offerts,date_vente,client,notes)
                VALUES (?,?,?,?,?,?,?,?)
            """, (l["pid"], l["qty"], l["prix"], l["total"],
                  l["offerts"], date_v, client, notes))
            self._last_vente_ids.append(cur.lastrowid)
            conn.execute(
                "UPDATE produits SET stock_actuel=stock_actuel-? WHERE id=?",
                (l["qty"] + l["offerts"], l["pid"]))
            conn.execute(
                "INSERT INTO mouvements (produit_id,type,quantite,motif) VALUES (?,?,?,?)",
                (l["pid"], "sortie", l["qty"]+l["offerts"], "Vente admin"))
        conn.commit(); conn.close()

        total_global = sum(l["total"] for l in self._panier)
        self.status_lbl.configure(
            text=f"✅ {len(self._panier)} produit(s) enregistrés — Total: {total_global:,.0f} {MONNAIE}")
        self.btn_pdf.configure(state="normal")
        self._panier.clear()
        self._refresh_panier()
        self.client_var.set(""); self.notes_var.set("")
        self.add_msg.configure(text="")
        self.refresh()
        if messagebox.askyesno("Facture", "Générer la facture PDF maintenant ?"):
            self._generer_facture()

    # ─── Historique & PDF ────────────────────────────────────────────────────

    def refresh(self):
        conn = get_connection()
        rows = conn.execute(
            "SELECT id,nom,prix_vente,stock_actuel,reduction_palier,reduction_quantite "
            "FROM produits WHERE stock_actuel>0 ORDER BY nom").fetchall()
        conn.close()
        self._all_produits = {
            r[1]: {"id": r[0], "prix": r[2], "stock": r[3],
                   "palier": r[4] or 0, "qte_offerte": r[5] or 0}
            for r in rows}

        today = datetime.now().strftime("%Y-%m-%d")
        for r in self.hist_tree.get_children(): self.hist_tree.delete(r)
        conn = get_connection()
        for r in conn.execute("""
            SELECT v.id,p.nom,v.quantite,v.prix_unitaire,v.prix_total,
                   COALESCE(v.paquets_offerts,0),COALESCE(v.client,'-'),v.date_vente
            FROM ventes v JOIN produits p ON v.produit_id=p.id
            WHERE DATE(v.date_vente)=? ORDER BY v.date_vente DESC
        """, (today,)).fetchall():
            self.hist_tree.insert("", "end", values=(
                r[0], r[1], r[2], f"{r[3]:.0f}", f"{r[4]:,.0f}",
                f"+{r[5]}" if r[5] > 0 else "-", r[6], str(r[7])[11:16]))
        conn.close()

    def _on_hist_select(self, _=None):
        sel = self.hist_tree.selection()
        if sel:
            self._last_vente_ids = [self.hist_tree.item(sel[0])["values"][0]]
            self.btn_pdf.configure(state="normal")

    def _generer_facture(self):
        if not self._last_vente_ids:
            messagebox.showwarning("Attention", "Aucune vente sélectionnée."); return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
            initialfile=f"facture_{self._last_vente_ids[0]:04d}.pdf")
        if not path: return
        vid = self._last_vente_ids[0]
        def run():
            try:
                generer_facture(vid, path)
                self.after(0, lambda: self.status_lbl.configure(
                    text=f"📄 Facture: {os.path.basename(path)}"))
                self.after(0, lambda: self._ouvrir(path))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erreur", str(e)))
        threading.Thread(target=run, daemon=True).start()

    def _ouvrir(self, path):
        try:
            os.startfile(path) if sys.platform == "win32" \
                else subprocess.Popen(["xdg-open", path])
        except: pass
