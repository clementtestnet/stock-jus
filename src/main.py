# main.py — Point d'entree
import tkinter as tk
from tkinter import ttk
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


class AppAdmin(tk.Tk):
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.title(f"🧃 {BOUTIQUE_NOM} — Administration")
        self.geometry("1100x680"); self.minsize(900,600)
        self.configure(bg="#f0f4f8"); self.resizable(True,True)
        self._build()
        self.show_frame("dashboard")

    def _build(self):
        # Sidebar
        sb = tk.Frame(self, bg="#1a2940", width=200)
        sb.pack(side="left", fill="y"); sb.pack_propagate(False)
        tk.Label(sb,text="🧃",font=("Arial",30),bg="#1a2940",fg="white").pack(pady=(18,3))
        tk.Label(sb,text=BOUTIQUE_NOM,font=("Arial",13,"bold"),bg="#1a2940",fg="white").pack()
        tk.Label(sb,text=f"Admin: {self.user_info['nom']}",font=("Arial",8),bg="#1a2940",fg="#4a90d9").pack(pady=(0,15))
        ttk.Separator(sb,orient="horizontal").pack(fill="x",padx=15,pady=5)

        nav=[("Tableau de bord","dashboard"),("Produits & Stock","produits"),
             ("Nouvel Achat","achats"),("Ventes","ventes"),
             ("Fournisseurs","fournisseurs"),("Historique","historique"),
             ("Rapports","rapports"),("Imprimer PDF","impression")]
        self.btns={}
        for label,key in nav:
            b=tk.Button(sb,text=label,anchor="w",padx=15,font=("Arial",10),
                        bg="#1a2940",fg="#ccd6e0",activebackground="#2a3f5f",
                        activeforeground="white",relief="flat",cursor="hand2",
                        command=lambda k=key: self.show_frame(k))
            b.pack(fill="x",pady=1); self.btns[key]=b

        ttk.Separator(sb,orient="horizontal").pack(fill="x",padx=15,pady=10,side="bottom")
        tk.Button(sb,text="Deconnexion",font=("Arial",9),bg="#e74c3c",fg="white",
                  relief="flat",cursor="hand2",command=self._deconnexion).pack(side="bottom",fill="x",padx=15,pady=5)
        tk.Label(sb,text="v3.0 — Admin",font=("Arial",8),bg="#1a2940",fg="#556677").pack(side="bottom",pady=5)

        # Zone principale
        self.main=tk.Frame(self,bg="#f0f4f8")
        self.main.pack(side="right",fill="both",expand=True)
        self.frames={}
        for key,cls in [("dashboard",DashboardFrame),("produits",ProduitsFrame),
                         ("achats",AchatsFrame),("ventes",VentesFrame),
                         ("fournisseurs",FournisseursFrame),("historique",HistoriqueFrame),
                         ("rapports",RapportsFrame),("impression",ImpressionFrame)]:
            f=cls(self.main,self); self.frames[key]=f
            f.place(relx=0,rely=0,relwidth=1,relheight=1)

    def show_frame(self,key):
        f=self.frames.get(key)
        if f:
            f.lift()
            if hasattr(f,"refresh"): f.refresh()
        for k,b in self.btns.items():
            b.config(bg="#2a3f5f" if k==key else "#1a2940",
                     fg="white" if k==key else "#ccd6e0")

    def _deconnexion(self):
        self.destroy(); lancer_app()


def lancer_app():
    init_db()
    login=LoginWindow(); login.mainloop()
    if not login.user_info: return
    user=login.user_info
    if user["role"]=="admin":
        AppAdmin(user).mainloop()
    else:
        from app_employe import AppEmploye
        AppEmploye(user).mainloop()


if __name__=="__main__":
    lancer_app()
