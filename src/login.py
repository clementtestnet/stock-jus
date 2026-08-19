"""
login.py — Ecran de connexion
"""

import tkinter as tk
from tkinter import messagebox
import hashlib
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from database import get_connection, init_db


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verifier_login(username, password):
    """Retourne (id, nom, role) ou None si echec."""
    conn = get_connection()
    row = conn.execute("""
        SELECT id, nom, role FROM utilisateurs
        WHERE username=? AND password=? AND actif=1
    """, (username, hash_password(password))).fetchone()
    conn.close()
    return row


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stock Jus — Connexion")
        self.geometry("400x480")
        self.resizable(False, False)
        self.configure(bg="#1a2940")
        self.user_info = None
        self._center()
        self._build()

    def _center(self):
        self.update_idletasks()
        w, h = 400, 480
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        # Logo
        tk.Label(self, text="🧃", font=("Arial", 48),
                 bg="#1a2940", fg="white").pack(pady=(40, 5))
        tk.Label(self, text="Stock Jus", font=("Arial", 22, "bold"),
                 bg="#1a2940", fg="white").pack()
        tk.Label(self, text="Gestion de Stock — Jus en Bouteille",
                 font=("Arial", 9), bg="#1a2940", fg="#8899aa").pack(pady=(0, 30))

        # Carte login
        card = tk.Frame(self, bg="white", padx=30, pady=25)
        card.pack(fill="x", padx=30)

        tk.Label(card, text="Nom d'utilisateur", font=("Arial", 9, "bold"),
                 bg="white", fg="#334455", anchor="w").pack(fill="x")
        self.username_var = tk.StringVar()
        username_entry = tk.Entry(card, textvariable=self.username_var,
                                   font=("Arial", 11), relief="solid", bd=1)
        username_entry.pack(fill="x", pady=(3, 12), ipady=6)
        username_entry.focus()

        tk.Label(card, text="Mot de passe", font=("Arial", 9, "bold"),
                 bg="white", fg="#334455", anchor="w").pack(fill="x")
        self.password_var = tk.StringVar()
        password_entry = tk.Entry(card, textvariable=self.password_var,
                                   show="*", font=("Arial", 11), relief="solid", bd=1)
        password_entry.pack(fill="x", pady=(3, 5), ipady=6)
        password_entry.bind("<Return>", lambda e: self._login())

        self.error_lbl = tk.Label(card, text="", font=("Arial", 9),
                                   bg="white", fg="#e74c3c")
        self.error_lbl.pack(fill="x", pady=(0, 5))

        tk.Button(card, text="SE CONNECTER", font=("Arial", 11, "bold"),
                  bg="#4a90d9", fg="white", relief="flat",
                  activebackground="#357abd", cursor="hand2",
                  command=self._login).pack(fill="x", ipady=8)

        # Comptes par défaut
        tk.Label(self, text="Comptes par défaut :", font=("Arial", 8),
                 bg="#1a2940", fg="#556677").pack(pady=(15, 2))
        tk.Label(self, text="admin / admin123   |   employe1 / employe1",
                 font=("Arial", 8), bg="#1a2940", fg="#445566").pack()
        tk.Label(self, text="employe2 / employe2   |   employe3 / employe3",
                 font=("Arial", 8), bg="#1a2940", fg="#445566").pack()

    def _login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            self.error_lbl.config(text="⚠ Remplissez tous les champs.")
            return

        result = verifier_login(username, password)
        if result:
            self.user_info = {"id": result[0], "nom": result[1], "role": result[2]}
            self.destroy()
        else:
            self.error_lbl.config(text="❌ Nom d'utilisateur ou mot de passe incorrect.")
            self.password_var.set("")
