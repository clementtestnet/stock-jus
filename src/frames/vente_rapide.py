# frames/vente_rapide.py — Multi-produits, recherche live, prix fixe, stock sécurisé
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


def _apply_tree_style():
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
        self._all_produits   = {}   # nom -> {id, prix, stock, palier, qte_offerte}
        self._panier         = []   # lignes du panier
        self._last_vente_ids = []
        self._selecting      = False  # verrou suggestions
        _apply_tree_style()
        self._build()

    # ─── UI ─────────────────────────────────────────────────────────────────

    def _build(self):
        ctk.CTkLabel(self, text="Enregistrer une Vente",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(22,2))
        ctk.CTkLabel(self,
                     text="Recherche rapide → Prix fixe → Ajouter au panier → Enregistrer",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(
            anchor="w", padx=30, pady=(0,12))

        # ── Carte ajout produit ──────────────────────────────────────────
        add = ctk.CTkFrame(self, corner_radius=14)
        add.pack(fill="x", padx=30, pady=4)

        # Ligne recherche
        r0 = ctk.CTkFrame(add, fg_color="transparent")
        r0.pack(fill="x", padx=20, pady=(16,4))
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

        self.lbl_stock = ctk.CTkLabel(r0, text="",
                                       font=ctk.CTkFont(size=11),
                                       text_color="#27ae60", width=200, anchor="w")
        self.lbl_stock.pack(side="left", padx=8)

        # Listbox suggestions flottante
        self._sug_frame = tk.Frame(self, bg="#1e2533", relief="flat", bd=1)
        self._sug_lb = tk.Listbox(self._sug_frame,
                                   bg="#1e2533", fg="white",
                                   selectbackground="#1f6aa5",
                                   font=("Arial",12), relief="flat", bd=0,
                                   activestyle="none", height=5, width=32)
        self._sug_lb.pack(fill="both", expand=True)
        self._sug_lb.bind("<ButtonRelease-1>", self._on_sug_select)
        self._sug_lb.bind("<Return>",           self._on_sug_select)

        # Ligne prix + quantité
        r1 = ctk.CTkFrame(add, fg_color="transparent")
        r1.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(r1, text=f"Prix ({MONNAIE})",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     width=150, anchor="w").pack(side="left")
        self.prix_var = tk.StringVar(value="—")
        ctk.CTkLabel(r1, textvariable=self.prix_var,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#f39c12", width=130, anchor="w").pack(side="left", padx=8)
        ctk.CTkLabel(r1, text="Quantité *",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     width=90, anchor="w").pack(side="left", padx=(20,0))
        self.qty_var = tk.StringVar(value="1")
        self.qty_entry = ctk.CTkEntry(r1, textvariable=self.qty_var,
                                       placeholder_text="ex: 1 ou 0.5",
                                       width=100, height=34, corner_radius=8)
        self.qty_entry.pack(side="left", padx=8)
        # accepter la virgule comme séparateur décimal
        self.qty_entry.bind("<KeyRelease>", self._normaliser_virgule)
        self.qty_var.trace_add("write", self._update_preview)
        self.preview_lbl = ctk.CTkLabel(r1, text="",
                                         font=ctk.CTkFont(size=12),
                                         text_color="#27ae60")
        self.preview_lbl.pack(side="left", padx=12)

        # Bouton ajouter
        r2 = ctk.CTkFrame(add, fg_color="transparent")
        r2.pack(fill="x", padx=20, pady=(6,14))
        ctk.CTkButton(r2, text="➕ Ajouter au panier",
                      width=180, height=38, corner_radius=10,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color="#1f6aa5", hover_color="#164e8a",
                      command=self._ajouter).pack(side="left")
        self.add_msg = ctk.CTkLabel(r2, text="",
                                     font=ctk.CTkFont(size=11),
                                     text_color="#27ae60")
        self.add_msg.pack(side="left", padx=12)

        # ── Panier ────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="🛒 Panier",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(
            anchor="w", padx=30, pady=(14,4))
        pan = ctk.CTkFrame(self, corner_radius=14)
        pan.pack(fill="x", padx=30, pady=2)

        cols = ("Produit", f"Qté", "Prix unit.", "Offerts", "Total")
        self.pan_tree = ttk.Treeview(pan, columns=cols, show="headings",
                                      height=5, style="Dark.Treeview")
        for c, w in zip(cols, [200,70,110,80,140]):
            self.pan_tree.heading(c, text=c)
            self.pan_tree.column(c, width=w, anchor="center")
        self.pan_tree.pack(fill="x", padx=12, pady=(10,6))

        pb = ctk.CTkFrame(pan, fg_color="transparent")
        pb.pack(fill="x", padx=12, pady=(0,10))
        ctk.CTkButton(pb, text="🗑 Retirer ligne",
                      width=140, height=32, corner_radius=8,
                      fg_color="#c0392b", hover_color="#96281b",
                      command=self._retirer_ligne).pack(side="left", padx=4)
        ctk.CTkButton(pb, text="🧹 Vider",
                      width=100, height=32, corner_radius=8,
                      fg_color="gray40", hover_color="gray30",
                      command=self._vider).pack(side="left", padx=4)
        self.total_lbl = ctk.CTkLabel(pb,
                                       text=f"Total : 0 {MONNAIE}",
                                       font=ctk.CTkFont(size=14, weight="bold"),
                                       text_color="#f39c12")
        self.total_lbl.pack(side="right", padx=12)

        # ── Infos vente ───────────────────────────────────────────────────
        info = ctk.CTkFrame(self, corner_radius=14)
        info.pack(fill="x", padx=30, pady=6)
        ri = ctk.CTkFrame(info, fg_color="transparent")
        ri.pack(fill="x", padx=20, pady=(12,8))
        for lbl, attr, w in [("Client","client_var",180),
                               ("Notes","notes_var",200),
                               ("Date","date_var",110)]:
            ctk.CTkLabel(ri, text=lbl,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         width=60, anchor="w").pack(side="left", padx=(8,0))
            var = tk.StringVar(); setattr(self, attr, var)
            ctk.CTkEntry(ri, textvariable=var, width=w, height=32,
                         corner_radius=8).pack(side="left", padx=6)
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))

        bf = ctk.CTkFrame(info, fg_color="transparent")
        bf.pack(pady=(4,14))
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

        # ── Historique du jour ────────────────────────────────────────────
        ctk.CTkLabel(self, text="Ventes du jour",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=30, pady=(14,4))
        hcols = ("ID","Produit","Qté","Prix","Total","Offerts","Client","Heure")
        self.hist_tree = ttk.Treeview(self, columns=hcols, show="headings",
                                       height=5, style="Dark.Treeview")
        for c, w in zip(hcols, [40,160,55,90,110,65,110,75]):
            self.hist_tree.heading(c, text=c)
            self.hist_tree.column(c, width=w, anchor="center")
        self.hist_tree.pack(fill="x", padx=30)
        self.hist_tree.bind("<<TreeviewSelect>>", self._on_hist_select)

        self.status_lbl = ctk.CTkLabel(self, text="",
                                        font=ctk.CTkFont(size=11),
                                        text_color="#27ae60")
        self.status_lbl.pack(anchor="w", padx=30, pady=6)

        self._selected = None
        self.refresh()

    def _normaliser_virgule(self, _=None):
        """Remplace la virgule par un point dans le champ quantité."""
        val = self.qty_var.get()
        if ',' in val:
            pos = self.qty_entry.index('insert')
            self.qty_var.set(val.replace(',', '.'))
            try: self.qty_entry.icursor(pos)
            except: pass

    def _parse_qty(self):
        """Retourne la quantité en float, ou None si invalide."""
        try:
            q = float(self.qty_var.get().replace(',', '.'))
            if q <= 0: return None
            # arrondi à 1 décimale pour éviter les flottants bizarres (0.10000001)
            return round(q, 1)
        except (ValueError, TypeError):
            return None

    # ─── Recherche live ──────────────────────────────────────────────────────

    def _on_search(self, *_):
        if self._selecting: return
        self._selected = None
        self.prix_var.set("—")
        self.lbl_stock.configure(text="", text_color="gray")
        self.preview_lbl.configure(text="")
        q = self.search_var.get().strip().lower()
        if not q: self._hide_sug(); return
        matches = [n for n in self._all_produits if q in n.lower()][:8]
        if not matches: self._hide_sug(); return
        self._sug_lb.delete(0,"end")
        for m in matches:
            p = self._all_produits[m]
            self._sug_lb.insert("end",
                f"{m}  ({p['stock']} {UNITE_DEFAULT}s — {p['prix']:.0f} {MONNAIE})")
        self._sug_lb.config(height=min(len(matches),6))
        self._show_sug()

    def _show_sug(self):
        x = self.search_entry.winfo_rootx() - self.winfo_rootx()
        y = self.search_entry.winfo_rooty() - self.winfo_rooty() + \
            self.search_entry.winfo_height()
        self._sug_frame.place(x=x+48, y=y, width=380)
        self._sug_frame.lift()

    def _hide_sug(self):
        self._sug_frame.place_forget()

    def _on_sug_select(self, _=None):
        idx = self._sug_lb.curselection()
        if not idx: return
        nom = self._sug_lb.get(idx[0]).split("  (")[0]
        self._selecting = True
        self._select(nom)
        self._selecting = False

    def _select(self, nom):
        p = self._all_produits.get(nom)
        if not p: return
        self._selected = {"nom": nom, **p}
        self.search_var.set(nom)
        self.prix_var.set(f"{p['prix']:.0f} {MONNAIE}")
        color = "#27ae60" if p["stock"] > 0 else "#e74c3c"
        info  = f"Stock: {p['stock']} {UNITE_DEFAULT}s"
        if p["palier"] > 0:
            info += f"  |  Offre: {p['palier']} → +{p['qte_offerte']} offerts"
        self.lbl_stock.configure(text=info, text_color=color)
        self._hide_sug()
        self.qty_entry.focus()
        self._update_preview()

    def _update_preview(self, *_):
        p = self._selected
        if not p: self.preview_lbl.configure(text=""); return
        qty = self._parse_qty()
        if qty is None: self.preview_lbl.configure(text=""); return
        try:
            red = calculer_reduction(qty, p["palier"], p["qte_offerte"], p["prix"])
            # affichage de la quantité : 1.0 -> "1", 0.5 -> "0.5"
            def fq(q): return str(int(q)) if float(q)==int(float(q)) else str(q)
            txt = f"= {red['prix_total']:,.0f} {MONNAIE}"
            if qty != int(qty):
                txt += f"  ({fq(qty)} paquet)"
            if red["paquets_offerts"] > 0:
                txt += f"  🎁 +{fq(red['paquets_offerts'])} offerts"
            self.preview_lbl.configure(text=txt, text_color="#27ae60")
        except (ValueError, TypeError):
            self.preview_lbl.configure(text="")

    # ─── Panier ──────────────────────────────────────────────────────────────

    def _ajouter(self):
        p = self._selected
        if not p:
            self.add_msg.configure(text="⚠ Sélectionnez un produit.", text_color="#e74c3c")
            return
        qty = self._parse_qty()
        if qty is None:
            self.add_msg.configure(text="⚠ Quantité invalide (ex: 1 ou 0.5).", text_color="#e74c3c")
            return
        # Stock disponible = stock réel - déjà réservé dans le panier
        reserve = sum(l["qty"]+l["offerts"] for l in self._panier if l["pid"]==p["id"])
        dispo   = p["stock"] - reserve
        if qty > dispo:
            self.add_msg.configure(
                text=f"⚠ Stock insuffisant (dispo: {dispo})", text_color="#e74c3c")
            return
        red = calculer_reduction(qty, p["palier"], p["qte_offerte"], p["prix"])
        self._panier.append({"nom":p["nom"],"pid":p["id"],"qty":qty,
                              "prix":p["prix"],"offerts":red["paquets_offerts"],
                              "total":red["prix_total"],
                              "palier":p["palier"],"qte_offerte":p["qte_offerte"]})
        self._refresh_pan()
        self.search_var.set(""); self.qty_var.set("1")
        self.prix_var.set("—"); self.lbl_stock.configure(text="")
        self.preview_lbl.configure(text="")
        self._selected = None
        self.add_msg.configure(text=f"✅ {p['nom']} ajouté", text_color="#27ae60")
        self.search_entry.focus()

    def _refresh_pan(self):
        def fq(q): return str(int(q)) if float(q)==int(float(q)) else str(q)
        for r in self.pan_tree.get_children(): self.pan_tree.delete(r)
        tot = 0
        for l in self._panier:
            self.pan_tree.insert("","end", values=(
                l["nom"], fq(l["qty"]), f"{l['prix']:.0f} {MONNAIE}",
                f"+{fq(l['offerts'])}" if l["offerts"]>0 else "—",
                f"{l['total']:,.0f} {MONNAIE}"))
            tot += l["total"]
        self.total_lbl.configure(text=f"Total : {tot:,.0f} {MONNAIE}")

    def _retirer_ligne(self):
        sel = self.pan_tree.selection()
        if not sel: return
        idx = self.pan_tree.index(sel[0])
        if 0 <= idx < len(self._panier): self._panier.pop(idx)
        self._refresh_pan()

    def _vider(self):
        self._panier.clear(); self._refresh_pan()

    # ─── Enregistrement ──────────────────────────────────────────────────────

    def _save(self):
        if not self._panier:
            messagebox.showerror("Erreur","Le panier est vide."); return
        date_v = self.date_var.get() or datetime.now().strftime("%Y-%m-%d")
        client = self.client_var.get() or None
        notes  = self.notes_var.get() or None
        conn   = get_connection()

        # Vérification finale des stocks en base
        for i, l in enumerate(self._panier):
            row = conn.execute(
                "SELECT stock_actuel FROM produits WHERE id=?", (l["pid"],)).fetchone()
            if row is None:
                conn.close()
                messagebox.showerror("Erreur", f"Produit '{l['nom']}' introuvable."); return
            stock_reel = float(row[0])
            # déduire ce que les lignes précédentes du même produit vont prendre
            deja = sum(float(x["qty"])+float(x["offerts"]) for x in self._panier[:i]
                       if x["pid"]==l["pid"])
            if (float(l["qty"])+float(l["offerts"])) > (stock_reel - deja):
                conn.close()
                messagebox.showerror("Stock insuffisant",
                    f"{l['nom']}: dispo={stock_reel-deja}, "
                    f"demandé={float(l['qty'])+float(l['offerts'])}"); return

        self._last_vente_ids = []
        for l in self._panier:
            cur = conn.execute("""
                INSERT INTO ventes
                (produit_id,produit_nom,quantite,prix_unitaire,prix_total,
                 paquets_offerts,date_vente,client,notes)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (l["pid"],l["nom"],l["qty"],l["prix"],l["total"],
                  l["offerts"],date_v,client,notes))
            self._last_vente_ids.append(cur.lastrowid)
            conn.execute("""
                UPDATE produits
                SET stock_actuel = MAX(0, stock_actuel - ?)
                WHERE id = ?
            """, (l["qty"]+l["offerts"], l["pid"]))
            conn.execute(
                "INSERT INTO mouvements (produit_id,type,quantite,motif) VALUES (?,?,?,?)",
                (l["pid"],"sortie",l["qty"]+l["offerts"],"Vente admin"))
        conn.commit(); conn.close()

        tot = sum(l["total"] for l in self._panier)
        self.status_lbl.configure(
            text=f"✅ {len(self._panier)} produit(s) — Total: {tot:,.0f} {MONNAIE}")
        self.btn_pdf.configure(state="normal")
        self._panier.clear(); self._refresh_pan()
        self.client_var.set(""); self.notes_var.set("")
        self.add_msg.configure(text="")
        self.refresh()
        if messagebox.askyesno("Facture","Générer la facture PDF maintenant ?"):
            self._generer_facture()

    # ─── Historique & PDF ────────────────────────────────────────────────────

    def refresh(self):
        conn = get_connection()
        rows = conn.execute(
            "SELECT id,nom,prix_vente,stock_actuel,reduction_palier,reduction_quantite "
            "FROM produits WHERE stock_actuel>0 ORDER BY nom").fetchall()
        conn.close()
        self._all_produits = {
            r[1]: {"id":r[0],"prix":r[2],"stock":r[3],
                   "palier":r[4] or 0,"qte_offerte":r[5] or 0}
            for r in rows}
        today = datetime.now().strftime("%Y-%m-%d")
        for r in self.hist_tree.get_children(): self.hist_tree.delete(r)
        conn = get_connection()
        for r in conn.execute("""
            SELECT v.id,
                   COALESCE(p.nom,v.produit_nom,'[supprimé]'),
                   v.quantite,v.prix_unitaire,v.prix_total,
                   COALESCE(v.paquets_offerts,0),
                   COALESCE(v.client,'-'),v.date_vente
            FROM ventes v LEFT JOIN produits p ON v.produit_id=p.id
            WHERE DATE(v.date_vente)=? ORDER BY v.date_vente DESC
        """, (today,)).fetchall():
            qte = float(r[2])
            qte_str = str(int(qte)) if qte == int(qte) else str(qte)
            self.hist_tree.insert("","end", values=(
                r[0],r[1],qte_str,f"{r[3]:.0f}",f"{r[4]:,.0f}",
                f"+{r[5]}" if float(r[5])>0 else "—", r[6], str(r[7])[11:16]))
        conn.close()

    def _on_hist_select(self, _=None):
        sel = self.hist_tree.selection()
        if sel:
            self._last_vente_ids = [self.hist_tree.item(sel[0])["values"][0]]
            self.btn_pdf.configure(state="normal")

    def _generer_facture(self):
        if not self._last_vente_ids:
            messagebox.showwarning("Attention","Aucune vente."); return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF","*.pdf")],
            initialfile=f"facture_{self._last_vente_ids[0]:04d}.pdf")
        if not path: return
        ids = list(self._last_vente_ids)
        def run():
            try:
                generer_facture(ids, path)
                self.after(0, lambda: self.status_lbl.configure(
                    text=f"📄 {os.path.basename(path)}"))
                self.after(0, lambda: self._ouvrir(path))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Erreur", str(e)))
        threading.Thread(target=run, daemon=True).start()

    def _ouvrir(self, path):
        try:
            os.startfile(path) if sys.platform=="win32" \
                else subprocess.Popen(["xdg-open",path])
        except: pass
