"""
impression.py — Interface pour générer et ouvrir des rapports PDF
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
import os, sys, subprocess, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pdf_export import rapport_stock, rapport_achats, rapport_ventes


class ImpressionFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.controller = controller
        self._build()

    def _build(self):
        tk.Label(self, text="Imprimer / Exporter PDF", font=("Arial", 18, "bold"),
                 bg="#f0f4f8", fg="#1a2940").pack(anchor="w", padx=30, pady=(25, 5))
        tk.Label(self, text="Générez un rapport PDF et ouvrez-le directement",
                 font=("Arial", 10), bg="#f0f4f8", fg="#667788").pack(anchor="w", padx=30, pady=(0, 20))

        # ── Carte 1 : État du stock ───────────────────────────────────
        self._make_card(
            title="📦 État du Stock",
            desc="Tableau complet de tous les produits avec quantités, valeur et alertes.",
            color="#4a90d9",
            action=self._export_stock,
        )

        # ── Carte 2 : Rapport achats ──────────────────────────────────
        frame_achats = self._make_card(
            title="🛒 Rapport Achats",
            desc="Liste des approvisionnements sur une période donnée.",
            color="#f39c12",
            action=None,
        )
        self._add_period_controls(frame_achats, "achats")

        # ── Carte 3 : Rapport ventes ──────────────────────────────────
        frame_ventes = self._make_card(
            title="💰 Rapport Ventes",
            desc="Liste des ventes sur une période donnée.",
            color="#27ae60",
            action=None,
        )
        self._add_period_controls(frame_ventes, "ventes")

        # Barre de statut
        self.status_lbl = tk.Label(self, text="", font=("Arial", 10, "italic"),
                                    bg="#f0f4f8", fg="#27ae60")
        self.status_lbl.pack(anchor="w", padx=30, pady=10)

    def _make_card(self, title, desc, color, action):
        card = tk.Frame(self, bg="white", highlightbackground="#dde3ed",
                         highlightthickness=1)
        card.pack(fill="x", padx=30, pady=8)

        left = tk.Frame(card, bg=color, width=8)
        left.pack(side="left", fill="y")

        body = tk.Frame(card, bg="white")
        body.pack(side="left", fill="both", expand=True, padx=15, pady=12)

        tk.Label(body, text=title, font=("Arial", 12, "bold"),
                 bg="white", fg="#1a2940").pack(anchor="w")
        tk.Label(body, text=desc, font=("Arial", 9),
                 bg="white", fg="#667788").pack(anchor="w", pady=2)

        if action:
            tk.Button(body, text="⬇️ Générer PDF", font=("Arial", 9, "bold"),
                      bg=color, fg="white", relief="flat", padx=12, pady=5,
                      cursor="hand2", command=action).pack(anchor="w", pady=(8, 0))
        return body

    def _add_period_controls(self, parent, kind):
        row = tk.Frame(parent, bg="white")
        row.pack(anchor="w", pady=(8, 0))
        tk.Label(row, text="Du :", bg="white", font=("Arial", 9)).pack(side="left")
        debut = tk.StringVar(value=f"{date.today().year}-01-01")
        tk.Entry(row, textvariable=debut, width=12).pack(side="left", padx=4)
        tk.Label(row, text="Au :", bg="white", font=("Arial", 9)).pack(side="left", padx=(8, 0))
        fin = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        tk.Entry(row, textvariable=fin, width=12).pack(side="left", padx=4)

        color = "#f39c12" if kind == "achats" else "#27ae60"
        fn = self._export_achats if kind == "achats" else self._export_ventes
        tk.Button(row, text="⬇️ Générer PDF", font=("Arial", 9, "bold"),
                  bg=color, fg="white", relief="flat", padx=12, pady=4,
                  cursor="hand2",
                  command=lambda d=debut, f=fin: fn(d.get(), f.get())).pack(side="left", padx=12)

    def _ask_save_path(self, default_name: str) -> str | None:
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Fichier PDF", "*.pdf")],
            initialfile=default_name,
            title="Enregistrer le rapport PDF"
        )
        return path or None

    def _open_pdf(self, path: str):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

    def _set_status(self, msg, color="#27ae60"):
        self.status_lbl.config(text=msg, fg=color)

    # ── Actions ───────────────────────────────────────────────────
    def _export_stock(self):
        path = self._ask_save_path("rapport_stock.pdf")
        if not path:
            return
        def run():
            try:
                rapport_stock(path)
                self.after(0, lambda: self._set_status(f"✅ PDF créé : {os.path.basename(path)}"))
                self.after(0, lambda: self._open_pdf(path))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"❌ Erreur : {e}", "#e74c3c"))
        threading.Thread(target=run, daemon=True).start()
        self._set_status("⏳ Génération en cours…", "#f39c12")

    def _export_achats(self, debut, fin):
        path = self._ask_save_path(f"rapport_achats_{debut}_{fin}.pdf")
        if not path:
            return
        def run():
            try:
                rapport_achats(path, debut, fin)
                self.after(0, lambda: self._set_status(f"✅ PDF créé : {os.path.basename(path)}"))
                self.after(0, lambda: self._open_pdf(path))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"❌ Erreur : {e}", "#e74c3c"))
        threading.Thread(target=run, daemon=True).start()
        self._set_status("⏳ Génération en cours…", "#f39c12")

    def _export_ventes(self, debut, fin):
        path = self._ask_save_path(f"rapport_ventes_{debut}_{fin}.pdf")
        if not path:
            return
        def run():
            try:
                rapport_ventes(path, debut, fin)
                self.after(0, lambda: self._set_status(f"✅ PDF créé : {os.path.basename(path)}"))
                self.after(0, lambda: self._open_pdf(path))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"❌ Erreur : {e}", "#e74c3c"))
        threading.Thread(target=run, daemon=True).start()
        self._set_status("⏳ Génération en cours…", "#f39c12")

    def refresh(self):
        pass
