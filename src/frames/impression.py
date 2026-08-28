# impression.py — MODERNE CustomTkinter
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from datetime import date
import threading, os, sys, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pdf_export import rapport_stock, rapport_achats, rapport_ventes


class ImpressionFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.controller = controller
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="🖨️ Imprimer / Exporter PDF",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=30, pady=(22,8))

        # Carte 1 — Stock
        self._carte(
            "📦 État du Stock",
            "Tableau complet : quantités, valeurs, alertes.",
            "#1f6aa5", self._stock
        )
        # Carte 2 — Achats
        c2 = self._carte("🛒 Rapport Achats",
                          "Approvisionnements sur une période donnée.",
                          "#d68910", None)
        self._periode(c2, "achats")
        # Carte 3 — Ventes
        c3 = self._carte("💰 Rapport Ventes",
                          "Ventes sur une période donnée.",
                          "#1e8449", None)
        self._periode(c3, "ventes")

        self.status = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12),
                                    text_color="#27ae60")
        self.status.pack(anchor="w", padx=30, pady=14)

    def _carte(self, title, desc, color, action):
        card = ctk.CTkFrame(self, corner_radius=14)
        card.pack(fill="x", padx=30, pady=8)
        # Barre colorée gauche
        bar = tk.Frame(card, bg=color, width=7)
        bar.pack(side="left", fill="y")
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=18, pady=14)
        ctk.CTkLabel(body, text=title,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(body, text=desc, font=ctk.CTkFont(size=11),
                     text_color="gray").pack(anchor="w", pady=(2,6))
        if action:
            ctk.CTkButton(body, text="Générer PDF", width=140, height=34,
                          corner_radius=8, fg_color=color,
                          command=action).pack(anchor="w")
        return body

    def _periode(self, parent, kind):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(anchor="w", pady=4)
        ctk.CTkLabel(row, text="Du :", font=ctk.CTkFont(size=11)).pack(side="left")
        d1 = tk.StringVar(value=f"{date.today().year}-01-01")
        ctk.CTkEntry(row, textvariable=d1, width=100, height=30).pack(side="left", padx=5)
        ctk.CTkLabel(row, text="Au :", font=ctk.CTkFont(size=11)).pack(side="left", padx=(8,0))
        d2 = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        ctk.CTkEntry(row, textvariable=d2, width=100, height=30).pack(side="left", padx=5)
        color = "#d68910" if kind == "achats" else "#1e8449"
        fn    = self._achats if kind == "achats" else self._ventes
        ctk.CTkButton(row, text="Générer PDF", width=130, height=30,
                      corner_radius=8, fg_color=color,
                      command=lambda a=d1, b=d2: fn(a.get(), b.get())).pack(side="left", padx=12)

    def _ask(self, name):
        return filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF","*.pdf")],
            initialfile=name, title="Enregistrer") or None

    def _ouvrir(self, path):
        try:
            os.startfile(path) if sys.platform == "win32" else subprocess.Popen(["xdg-open",path])
        except: pass

    def _run(self, fn, path):
        self.status.configure(text="⏳ Génération en cours...", text_color="#f39c12")
        def go():
            try:
                fn(path)
                self.after(0, lambda: self.status.configure(
                    text=f"✅ PDF créé : {os.path.basename(path)}", text_color="#27ae60"))
                self.after(0, lambda: self._ouvrir(path))
            except Exception as e:
                self.after(0, lambda: self.status.configure(
                    text=f"❌ Erreur: {e}", text_color="#e74c3c"))
        threading.Thread(target=go, daemon=True).start()

    def _stock(self):
        p = self._ask("rapport_stock.pdf")
        if p: self._run(rapport_stock, p)

    def _achats(self, d1, d2):
        p = self._ask(f"rapport_achats_{d1}_{d2}.pdf")
        if p: self._run(lambda path: rapport_achats(path, d1, d2), p)

    def _ventes(self, d1, d2):
        p = self._ask(f"rapport_ventes_{d1}_{d2}.pdf")
        if p: self._run(lambda path: rapport_ventes(path, d1, d2), p)

    def refresh(self): pass
