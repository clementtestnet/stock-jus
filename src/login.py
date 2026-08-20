# login.py — Ecran de connexion

import tkinter as tk
from tkinter import messagebox
import hashlib, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection, init_db
from config import BOUTIQUE_NOM

def verifier_login(username, password):
    h = hashlib.sha256(password.encode()).hexdigest()
    conn = get_connection()
    row = conn.execute(
        "SELECT id,nom,role FROM utilisateurs WHERE username=? AND password=? AND actif=1",
        (username, h)).fetchone()
    conn.close()
    return row

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{BOUTIQUE_NOM} — Connexion")
        self.geometry("400x460")
        self.resizable(False, False)
        self.configure(bg="#1a2940")
        self.user_info = None
        self._center()
        self._build()

    def _center(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 400) // 2
        y = (self.winfo_screenheight() - 460) // 2
        self.geometry(f"400x460+{x}+{y}")

    def _build(self):
        tk.Label(self, text="🧃", font=("Arial", 48), bg="#1a2940", fg="white").pack(pady=(35,5))
        tk.Label(self, text=BOUTIQUE_NOM, font=("Arial", 20, "bold"),
                 bg="#1a2940", fg="white").pack()
        tk.Label(self, text="Gestion de Stock", font=("Arial", 9),
                 bg="#1a2940", fg="#8899aa").pack(pady=(0,25))

        card = tk.Frame(self, bg="white", padx=25, pady=20)
        card.pack(fill="x", padx=30)

        tk.Label(card, text="Nom d'utilisateur", font=("Arial", 9, "bold"),
                 bg="white", fg="#334455", anchor="w").pack(fill="x")
        self.uvar = tk.StringVar()
        ue = tk.Entry(card, textvariable=self.uvar, font=("Arial", 11),
                      relief="solid", bd=1)
        ue.pack(fill="x", pady=(3,10), ipady=6)
        ue.focus()

        tk.Label(card, text="Mot de passe", font=("Arial", 9, "bold"),
                 bg="white", fg="#334455", anchor="w").pack(fill="x")
        self.pvar = tk.StringVar()
        pe = tk.Entry(card, textvariable=self.pvar, show="*",
                      font=("Arial", 11), relief="solid", bd=1)
        pe.pack(fill="x", pady=(3,5), ipady=6)
        pe.bind("<Return>", lambda e: self._login())

        self.err = tk.Label(card, text="", font=("Arial", 9),
                             bg="white", fg="#e74c3c")
        self.err.pack(fill="x", pady=(0,5))

        tk.Button(card, text="SE CONNECTER", font=("Arial", 11, "bold"),
                  bg="#4a90d9", fg="white", relief="flat",
                  cursor="hand2", command=self._login).pack(fill="x", ipady=8)

        tk.Label(self, text="admin/admin123  |  employe1/employe1",
                 font=("Arial", 8), bg="#1a2940", fg="#445566").pack(pady=(15,0))
        tk.Label(self, text="employe2/employe2  |  employe3/employe3",
                 font=("Arial", 8), bg="#1a2940", fg="#445566").pack()

    def _login(self):
        u = self.uvar.get().strip()
        p = self.pvar.get().strip()
        if not u or not p:
            self.err.config(text="Remplissez tous les champs.")
            return
        result = verifier_login(u, p)
        if result:
            self.user_info = {"id": result[0], "nom": result[1], "role": result[2]}
            self.destroy()
        else:
            self.err.config(text="Identifiants incorrects.")
            self.pvar.set("")
