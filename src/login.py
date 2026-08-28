# login.py — Ecran de connexion MODERNE avec CustomTkinter

import customtkinter as ctk
import hashlib, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection, init_db
from config import BOUTIQUE_NOM

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def verifier_login(username, password):
    h = hashlib.sha256(password.encode()).hexdigest()
    conn = get_connection()
    row = conn.execute(
        "SELECT id,nom,role FROM utilisateurs WHERE username=? AND password=? AND actif=1",
        (username, h)).fetchone()
    conn.close()
    return row


class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{BOUTIQUE_NOM} — Connexion")
        self.geometry("440x560")
        self.resizable(False, False)
        self.user_info = None
        self._center()
        self._build()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 440) // 2
        y = (self.winfo_screenheight() - 560) // 2
        self.geometry(f"440x560+{x}+{y}")

    def _build(self):
        # Logo + titre
        ctk.CTkLabel(self, text="🧃", font=ctk.CTkFont(size=56)).pack(pady=(40, 5))
        ctk.CTkLabel(self, text=BOUTIQUE_NOM,
                     font=ctk.CTkFont(size=26, weight="bold")).pack()
        ctk.CTkLabel(self, text="Gestion de Stock",
                     font=ctk.CTkFont(size=13),
                     text_color="gray").pack(pady=(2, 30))

        # Carte login
        frame = ctk.CTkFrame(self, corner_radius=16)
        frame.pack(fill="x", padx=40, pady=5)

        ctk.CTkLabel(frame, text="Nom d'utilisateur",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x", padx=25, pady=(20, 3))
        self.uentry = ctk.CTkEntry(frame, placeholder_text="admin",
                                    height=42, corner_radius=8,
                                    font=ctk.CTkFont(size=13))
        self.uentry.pack(fill="x", padx=25, pady=(0, 12))
        self.uentry.focus()

        ctk.CTkLabel(frame, text="Mot de passe",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").pack(fill="x", padx=25, pady=(0, 3))
        self.pentry = ctk.CTkEntry(frame, placeholder_text="••••••••",
                                    show="*", height=42, corner_radius=8,
                                    font=ctk.CTkFont(size=13))
        self.pentry.pack(fill="x", padx=25, pady=(0, 5))
        self.pentry.bind("<Return>", lambda e: self._login())

        self.err_lbl = ctk.CTkLabel(frame, text="",
                                     font=ctk.CTkFont(size=11),
                                     text_color="#ff6b6b")
        self.err_lbl.pack(pady=(0, 5))

        ctk.CTkButton(frame, text="SE CONNECTER",
                      height=44, corner_radius=10,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._login).pack(fill="x", padx=25, pady=(0, 20))

        # Comptes par défaut
        ctk.CTkLabel(self, text="admin/admin123  •  employe1/employe1",
                     font=ctk.CTkFont(size=10), text_color="gray").pack(pady=(10, 0))
        ctk.CTkLabel(self, text="employe2/employe2  •  employe3/employe3",
                     font=ctk.CTkFont(size=10), text_color="gray").pack()

    def _login(self):
        u = self.uentry.get().strip()
        p = self.pentry.get().strip()
        if not u or not p:
            self.err_lbl.configure(text="⚠ Remplissez tous les champs.")
            return
        result = verifier_login(u, p)
        if result:
            self.user_info = {"id": result[0], "nom": result[1], "role": result[2]}
            self.destroy()
        else:
            self.err_lbl.configure(text="❌ Identifiants incorrects.")
            self.pentry.delete(0, "end")
