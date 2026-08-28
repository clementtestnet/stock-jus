# main.py — AppAdmin MODERNE avec CustomTkinter
import customtkinter as ctk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import init_db
from login import LoginWindow
from config import BOUTIQUE_NOM
from frames.dashboard    import DashboardFrame
from frames.produits     import ProduitsFrame
from frames.achats       import AchatsFrame
from frames.fournisseurs import FournisseursFrame
from frames.historique   import HistoriqueFrame
from frames.rapports     import RapportsFrame
from frames.ventes       import VentesFrame
from frames.impression   import ImpressionFrame
from frames.vente_rapide import VenteRapideFrame
from frames.sorties      import SortiesFrame

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

NAV_ITEMS = [
    ("🏠  Tableau de bord",  "dashboard"),
    ("📦  Produits & Stock", "produits"),
    ("💰  Vente rapide",     "vente_rapide"),
    ("🛒  Nouvel Achat",     "achats"),
    ("🟣  Sorties",          "sorties"),
    ("📋  Ventes",           "ventes"),
    ("📋  Historique",       "historique"),
    ("📊  Rapports",         "rapports"),
    ("🖨️  Imprimer PDF",     "impression"),
]

FRAME_MAP = [
    ("dashboard",   DashboardFrame),
    ("produits",    ProduitsFrame),
    ("vente_rapide",VenteRapideFrame),
    ("achats",      AchatsFrame),
    ("sorties",     SortiesFrame),
    ("ventes",      VentesFrame),
    ("historique",  HistoriqueFrame),
    ("rapports",    RapportsFrame),
    ("impression",  ImpressionFrame),
]


class AppAdmin(ctk.CTk):
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.title(f"🧃 {BOUTIQUE_NOM} — Administration")
        self.geometry("1200x720")
        self.minsize(960, 620)
        self._build()
        self.show_frame("dashboard")

    def _build(self):
        # ─── Sidebar ───────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        ctk.CTkLabel(self.sidebar, text="🧃",
                     font=ctk.CTkFont(size=42)).pack(pady=(24, 4))
        ctk.CTkLabel(self.sidebar, text=BOUTIQUE_NOM,
                     font=ctk.CTkFont(size=16, weight="bold")).pack()
        ctk.CTkLabel(self.sidebar,
                     text=f"Admin: {self.user_info['nom']}",
                     font=ctk.CTkFont(size=11),
                     text_color="#7EB3FF").pack(pady=(2, 14))

        ctk.CTkFrame(self.sidebar, height=1, fg_color="#3a3f4b").pack(fill="x", padx=18, pady=4)

        # Boutons nav
        self.nav_btns = {}
        for label, key in NAV_ITEMS:
            btn = ctk.CTkButton(
                self.sidebar, text=label, anchor="w",
                height=38, corner_radius=8,
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                hover_color="#2a3a5a",
                command=lambda k=key: self.show_frame(k)
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_btns[key] = btn

        ctk.CTkFrame(self.sidebar, height=1, fg_color="#3a3f4b").pack(
            fill="x", padx=18, pady=8, side="bottom")
        ctk.CTkButton(
            self.sidebar, text="🚪  Déconnexion",
            height=36, corner_radius=8,
            font=ctk.CTkFont(size=12),
            fg_color="#c0392b", hover_color="#96281b",
            command=self._deconnexion
        ).pack(side="bottom", fill="x", padx=12, pady=(0, 14))
        ctk.CTkLabel(self.sidebar, text="v4.0 — Modern",
                     font=ctk.CTkFont(size=10),
                     text_color="gray").pack(side="bottom", pady=4)

        # ─── Zone principale ───────────────────────────────────
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray92", "gray14"))
        self.main_area.pack(side="right", fill="both", expand=True)

        self.frames = {}
        for key, cls in FRAME_MAP:
            f = cls(self.main_area, self)
            self.frames[key] = f
            f.place(relx=0, rely=0, relwidth=1, relheight=1)

    def show_frame(self, key):
        f = self.frames.get(key)
        if f:
            f.lift()
            if hasattr(f, "refresh"):
                f.refresh()
        for k, btn in self.nav_btns.items():
            if k == key:
                btn.configure(fg_color="#1f6aa5", text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=("gray10", "gray90"))

    def _deconnexion(self):
        self.destroy()
        lancer_app()


def lancer_app():
    init_db()
    login = LoginWindow()
    login.mainloop()
    if not login.user_info:
        return
    user = login.user_info
    if user["role"] == "admin":
        AppAdmin(user).mainloop()
    else:
        from app_employe import AppEmploye
        AppEmploye(user).mainloop()


if __name__ == "__main__":
    lancer_app()
