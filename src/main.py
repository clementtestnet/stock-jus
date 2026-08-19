"""
main.py — Point d'entrée avec gestion login et roles
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db
from login import LoginWindow
from frames.dashboard import DashboardFrame
from frames.produits import ProduitsFrame
from frames.achats import AchatsFrame
from frames.fournisseurs import FournisseursFrame
from frames.historique import HistoriqueFrame
from frames.rapports import RapportsFrame
from frames.ventes import VentesFrame
from frames.impression import ImpressionFrame


class AppAdmin(tk.Tk):
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.title("🧃 Stock Jus — Administration")
        self.geometry("1100x680")
        self.minsize(900, 600)
        self.configure(bg="#f0f4f8")
        self.resizable(True, True)
        self._build_ui()
        self.show_frame("dashboard")

    def _build_ui(self):
        # ── Barre latérale ──────────────────────────────────────────
        sidebar = tk.Frame(self, bg="#1a2940", width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="🧃", font=("Arial", 32),
                 bg="#1a2940", fg="white").pack(pady=(20, 5))
        tk.Label(sidebar, text="Stock Jus", font=("Arial", 14, "bold"),
                 bg="#1a2940", fg="white").pack()
        tk.Label(sidebar, text=f"👨‍💼 {self.user_info['nom']}",
                 font=("Arial", 9), bg="#1a2940", fg="#8899aa").pack(pady=(0, 5))
        tk.Label(sidebar, text="Administrateur",
                 font=("Arial", 8), bg="#1a2940", fg="#4a90d9").pack(pady=(0, 15))

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=15, pady=5)

        nav_items = [
            ("🏠  Tableau de bord",  "dashboard"),
            ("📦  Produits & Stock", "produits"),
            ("🛒  Nouvel Achat",     "achats"),
            ("💰  Ventes",           "ventes"),
            ("🏭  Fournisseurs",     "fournisseurs"),
            ("📋  Historique",       "historique"),
            ("📊  Rapports",         "rapports"),
            ("🖨️  Imprimer PDF",    "impression"),
        ]

        self.nav_buttons = {}
        for label, key in nav_items:
            btn = tk.Button(sidebar, text=label, anchor="w", padx=15,
                            font=("Arial", 10), bg="#1a2940", fg="#ccd6e0",
                            activebackground="#2a3f5f", activeforeground="white",
                            relief="flat", cursor="hand2",
                            command=lambda k=key: self.show_frame(k))
            btn.pack(fill="x", pady=1)
            self.nav_buttons[key] = btn

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=15, pady=10, side="bottom")

        tk.Button(sidebar, text="🚪 Déconnexion", font=("Arial", 9),
                  bg="#e74c3c", fg="white", relief="flat",
                  cursor="hand2", command=self._deconnexion).pack(side="bottom", fill="x", padx=15, pady=5)

        tk.Label(sidebar, text="v2.0 — Admin", font=("Arial", 8),
                 bg="#1a2940", fg="#556677").pack(side="bottom", pady=5)

        # ── Zone principale ──────────────────────────────────────────
        self.main_area = tk.Frame(self, bg="#f0f4f8")
        self.main_area.pack(side="right", fill="both", expand=True)

        self.frames = {}
        frame_classes = {
            "dashboard":   DashboardFrame,
            "produits":    ProduitsFrame,
            "achats":      AchatsFrame,
            "ventes":      VentesFrame,
            "fournisseurs": FournisseursFrame,
            "historique":  HistoriqueFrame,
            "rapports":    RapportsFrame,
            "impression":  ImpressionFrame,
        }
        for key, cls in frame_classes.items():
            frame = cls(self.main_area, self)
            self.frames[key] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

    def show_frame(self, key):
        frame = self.frames.get(key)
        if frame:
            frame.lift()
            if hasattr(frame, "refresh"):
                frame.refresh()
        for k, btn in self.nav_buttons.items():
            btn.config(bg="#2a3f5f" if k == key else "#1a2940",
                       fg="white" if k == key else "#ccd6e0")

    def _deconnexion(self):
        self.destroy()
        lancer_app()


def lancer_app():
    """Affiche le login puis lance l'app selon le rôle."""
    init_db()
    login = LoginWindow()
    login.mainloop()

    if not login.user_info:
        return  # Fenêtre fermée sans connexion

    user = login.user_info

    if user["role"] == "admin":
        app = AppAdmin(user)
        app.mainloop()
    else:
        from app_employe import AppEmploye
        app = AppEmploye(user)
        app.mainloop()


if __name__ == "__main__":
    lancer_app()
