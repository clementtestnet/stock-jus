# app_employe.py
import customtkinter as ctk
import tkinter.ttk as ttk
import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime
import threading, os, sys, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from database import get_connection
from facture import generer_facture
from config import MONNAIE, BOUTIQUE_NOM, UNITE_DEFAULT
from reduction import calculer_reduction

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def _apply_tree_style():
    s = ttk.Style()
    s.configure("Dark.Treeview",
        background="#2b2b2b", foreground="white",
        fieldbackground="#2b2b2b", rowheight=28, font=("Arial",11))
    s.configure("Dark.Treeview.Heading",
        background="#1a1a2e", foreground="#7EB3FF",
        font=("Arial",11,"bold"), relief="flat")
    s.map("Dark.Treeview", background=[("selected","#1f6aa5")])


class AppEmploye(ctk.CTk):
    def __init__(self, user_info):
        super().__init__()
        self.user_info       = user_info
        self._produit_map    = {}
        self._last_vente_id  = None
        self._red_palier     = 0
        self._red_quantite   = 0
        self.title(f"🧃 {BOUTIQUE_NOM} — {user_info['nom']}")
        self.geometry("960x720"); self.minsize(780,600)
        _apply_tree_style()
        self._build()

    def _build(self):
        # Barre du haut
        top = ctk.CTkFrame(self, height=52, corner_radius=0)
        top.pack(fill="x"); top.pack_propagate(False)
        ctk.CTkLabel(top, text=f"🧃 {BOUTIQUE_NOM}",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(
            side="left", padx=20)
        ctk.CTkLabel(top, text=f"👷 {self.user_info['nom']}  |  Employé",
                     font=ctk.CTkFont(size=11), text_color="#7EB3FF").pack(
            side="left", padx=10)
        ctk.CTkButton(top, text="🚪 Déconnexion",
                      width=130, height=34, corner_radius=8,
                      fg_color="#c0392b", hover_color="#96281b",
                      command=self._deconnexion).pack(side="right", padx=15, pady=8)

        # Corps scrollable
        body = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=30, pady=15)

        ctk.CTkLabel(body, text="Nouvelle Vente",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(body, text="Enregistrez la vente puis générez la facture PDF",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(
            anchor="w", pady=(0,14))

        card = ctk.CTkFrame(body, corner_radius=14)
        card.pack(fill="x")

        # Produit
        r0 = ctk.CTkFrame(card, fg_color="transparent")
        r0.pack(fill="x", padx=20, pady=(16,4))
        ctk.CTkLabel(r0, text="Produit *",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     width=180, anchor="w").pack(side="left")
        self.produit_var = tk.StringVar()
        self.produit_cb  = ttk.Combobox(r0, textvariable=self.produit_var,
                                         width=30, state="readonly")
        self.produit_cb.pack(side="left", padx=8)
        self.lbl_stock = ctk.CTkLabel(r0, text="",
                                       font=ctk.CTkFont(size=11),
                                       text_color="gray", width=180, anchor="w")
        self.lbl_stock.pack(side="left", padx=8)
        self.produit_cb.bind("<<ComboboxSelected>>", self._on_produit)

        # Champs
        self.vars = {"produit": self.produit_var}
        for label, key in [
            (f"Quantité ({UNITE_DEFAULT}s) *", "quantite"),
            (f"Prix unitaire ({MONNAIE}) *",   "prix_unit"),
            ("Client",                          "client"),
            ("Notes",                           "notes"),
            ("Date",                            "date"),
        ]:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(row, text=label,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         width=180, anchor="w").pack(side="left")
            var = tk.StringVar(); self.vars[key] = var
            e = ctk.CTkEntry(row, textvariable=var, width=280, height=34, corner_radius=8)
            e.pack(side="left", padx=8)
            if key == "date": var.set(datetime.now().strftime("%Y-%m-%d"))
            if key in ("quantite","prix_unit"):
                e.bind("<KeyRelease>", self._update_total)

        # Total
        tf = ctk.CTkFrame(card, corner_radius=10, fg_color=("#fff8e1","#2e2a00"))
        tf.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(tf, text="Total :",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(
            side="left", padx=15, pady=10)
        self.total_lbl = ctk.CTkLabel(tf, text=f"0 {MONNAIE}",
                                       font=ctk.CTkFont(size=18, weight="bold"),
                                       text_color="#f39c12")
        self.total_lbl.pack(side="left")
        self.red_lbl = ctk.CTkLabel(tf, text="",
                                     font=ctk.CTkFont(size=11),
                                     text_color="#27ae60")
        self.red_lbl.pack(side="left", padx=20)

        # Boutons
        bf = ctk.CTkFrame(card, fg_color="transparent")
        bf.pack(pady=(8,16))
        ctk.CTkButton(bf, text="💰 Enregistrer la vente",
                      width=200, height=42, corner_radius=10,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      fg_color="#d68910", hover_color="#b7770d",
                      command=self._save).pack(side="left", padx=8)
        self.btn_pdf = ctk.CTkButton(bf, text="🖨 Facture PDF",
                                      width=160, height=42, corner_radius=10,
                                      font=ctk.CTkFont(size=13, weight="bold"),
                                      state="disabled",
                                      command=self._generer_facture)
        self.btn_pdf.pack(side="left", padx=8)

        # Historique du jour
        ctk.CTkLabel(body, text="Mes ventes du jour",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(
            anchor="w", pady=(18,4))
        cols = ("ID","Produit","Qté","Prix","Total","Offerts","Client","Heure")
        self.tree = ttk.Treeview(body, columns=cols, show="headings",
                                  height=7, style="Dark.Treeview")
        for c, w in zip(cols, [40,150,55,90,110,65,110,75]):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="x")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.status_lbl = ctk.CTkLabel(body, text="",
                                        font=ctk.CTkFont(size=11),
                                        text_color="#27ae60")
        self.status_lbl.pack(anchor="w", pady=6)
        self.refresh()

    def _on_produit(self, _=None):
        nom = self.produit_var.get()
        pid = self._produit_map.get(nom, {}).get("id")
        if not pid: return
        conn = get_connection()
        row  = conn.execute(
            "SELECT stock_actuel,prix_vente,reduction_palier,reduction_quantite "
            "FROM produits WHERE id=?", (pid,)).fetchone()
        conn.close()
        if row:
            self._red_palier   = row[2] or 0
            self._red_quantite = row[3] or 0
            color = "#27ae60" if row[0] > 0 else "#e74c3c"
            info  = f"Stock: {row[0]} {UNITE_DEFAULT}s"
            if self._red_palier > 0:
                info += f"  |  Offre: {self._red_palier}→+{self._red_quantite}"
            self.lbl_stock.configure(text=info, text_color=color)
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
                self.red_lbl.configure(
                    text=red["detail"] if self._red_palier > 0 else "")
        except (ValueError, AttributeError):
            self.total_lbl.configure(text=f"0 {MONNAIE}")
            self.red_lbl.configure(text="")

    def refresh(self):
        conn = get_connection()
        rows = conn.execute(
            "SELECT id,nom FROM produits WHERE stock_actuel>0 ORDER BY nom").fetchall()
        conn.close()
        self._produit_map = {r[1]:{"id":r[0]} for r in rows}
        self.produit_cb["values"] = list(self._produit_map.keys())
        today = datetime.now().strftime("%Y-%m-%d")
        for r in self.tree.get_children(): self.tree.delete(r)
        conn = get_connection()
        for r in conn.execute("""
            SELECT v.id,
                   COALESCE(p.nom, v.produit_nom, '[supprimé]'),
                   v.quantite, v.prix_unitaire, v.prix_total,
                   COALESCE(v.paquets_offerts,0),
                   COALESCE(v.client,'-'), v.date_vente
            FROM ventes v LEFT JOIN produits p ON v.produit_id=p.id
            WHERE DATE(v.date_vente)=? ORDER BY v.date_vente DESC
        """, (today,)).fetchall():
            self.tree.insert("","end", values=(
                r[0],r[1],r[2],f"{r[3]:.0f}",f"{r[4]:,.0f}",
                f"+{r[5]}" if r[5]>0 else "—", r[6], str(r[7])[11:16]))
        conn.close()

    def _on_select(self, _=None):
        sel = self.tree.selection()
        if sel:
            self._last_vente_id = self.tree.item(sel[0])["values"][0]
            self.btn_pdf.configure(state="normal")

    def _save(self):
        nom = self.produit_var.get()
        if not nom or nom not in self._produit_map:
            messagebox.showerror("Erreur","Sélectionnez un produit."); return
        try:
            qty  = int(self.vars["quantite"].get())
            prix = float(self.vars["prix_unit"].get())
            if qty <= 0 or prix < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Erreur","Quantité et prix invalides."); return

        pid  = self._produit_map[nom]["id"]
        conn = get_connection()
        stock = conn.execute(
            "SELECT stock_actuel FROM produits WHERE id=?", (pid,)).fetchone()[0]
        if qty > stock:
            messagebox.showerror("Stock insuffisant",
                f"Stock: {stock}  Demandé: {qty}")
            conn.close(); return

        red   = calculer_reduction(qty, self._red_palier, self._red_quantite, prix)
        total = red["prix_total"]; offs = red["paquets_offerts"]
        date  = self.vars["date"].get() or datetime.now().strftime("%Y-%m-%d")

        cur = conn.execute("""
            INSERT INTO ventes
            (produit_id, produit_nom, quantite, prix_unitaire, prix_total,
             paquets_offerts, date_vente, client, notes)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (pid, nom, qty, prix, total, offs, date,
              self.vars["client"].get() or None,
              self.vars["notes"].get() or None))
        self._last_vente_id = cur.lastrowid

        # Stock jamais négatif
        conn.execute("""
            UPDATE produits SET stock_actuel=MAX(0, stock_actuel-?) WHERE id=?
        """, (qty+offs, pid))
        conn.execute(
            "INSERT INTO mouvements (produit_id,type,quantite,motif) VALUES (?,?,?,?)",
            (pid,"sortie",qty+offs,f"Vente par {self.user_info['nom']}"))
        conn.commit(); conn.close()

        self.btn_pdf.configure(state="normal")
        msg = f"✅ Vente #{self._last_vente_id} — {total:,.0f} {MONNAIE}"
        if offs > 0: msg += f"  |  +{offs} {UNITE_DEFAULT}(s) offert(s) !"
        self.status_lbl.configure(text=msg)
        for k in ("quantite","prix_unit","client","notes"): self.vars[k].set("")
        self.total_lbl.configure(text=f"0 {MONNAIE}")
        self.red_lbl.configure(text="")
        self.lbl_stock.configure(text="", text_color="gray")
        self._red_palier = self._red_quantite = 0
        self.refresh()
        if messagebox.askyesno("Facture","Générer la facture PDF maintenant ?"):
            self._generer_facture()

    def _generer_facture(self):
        if not self._last_vente_id:
            messagebox.showwarning("Attention","Aucune vente sélectionnée."); return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF","*.pdf")],
            initialfile=f"facture_{self._last_vente_id:04d}.pdf")
        if not path: return
        vid = self._last_vente_id
        def run():
            try:
                generer_facture(vid, path)
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

    def _deconnexion(self):
        self.destroy()
        subprocess.Popen([sys.executable,
                          os.path.join(os.path.dirname(__file__), "main.py")])
