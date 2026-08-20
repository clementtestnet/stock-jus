# impression.py
import tkinter as tk
from tkinter import filedialog
from datetime import date
import threading, os, sys, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pdf_export import rapport_stock, rapport_achats, rapport_ventes

class ImpressionFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f4f8")
        self.controller = controller
        self._build()

    def _build(self):
        tk.Label(self,text="Imprimer / Exporter PDF",font=("Arial",18,"bold"),
                 bg="#f0f4f8",fg="#1a2940").pack(anchor="w",padx=30,pady=(20,5))

        self._carte("Etat du Stock","Tableau complet: quantites, valeurs, alertes.","#4a90d9",self._stock)
        b2=self._carte("Rapport Achats","Approvisionnements sur une periode donnee.","#f39c12",None)
        self._periode(b2,"achats")
        b3=self._carte("Rapport Ventes","Ventes sur une periode donnee.","#27ae60",None)
        self._periode(b3,"ventes")

        self.status=tk.Label(self,text="",font=("Arial",10,"italic"),bg="#f0f4f8",fg="#27ae60")
        self.status.pack(anchor="w",padx=30,pady=10)

    def _carte(self,title,desc,color,action):
        c=tk.Frame(self,bg="white",highlightbackground="#dde3ed",highlightthickness=1)
        c.pack(fill="x",padx=30,pady=8)
        tk.Frame(c,bg=color,width=8).pack(side="left",fill="y")
        b=tk.Frame(c,bg="white"); b.pack(side="left",fill="both",expand=True,padx=15,pady=12)
        tk.Label(b,text=title,font=("Arial",12,"bold"),bg="white",fg="#1a2940").pack(anchor="w")
        tk.Label(b,text=desc,font=("Arial",9),bg="white",fg="#667788").pack(anchor="w",pady=2)
        if action:
            tk.Button(b,text="Generer PDF",font=("Arial",9,"bold"),bg=color,fg="white",
                      relief="flat",padx=12,pady=5,cursor="hand2",command=action).pack(anchor="w",pady=(8,0))
        return b

    def _periode(self,parent,kind):
        row=tk.Frame(parent,bg="white"); row.pack(anchor="w",pady=(8,0))
        tk.Label(row,text="Du:",bg="white",font=("Arial",9)).pack(side="left")
        d1=tk.StringVar(value=f"{date.today().year}-01-01")
        tk.Entry(row,textvariable=d1,width=12).pack(side="left",padx=4)
        tk.Label(row,text="Au:",bg="white",font=("Arial",9)).pack(side="left",padx=(8,0))
        d2=tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        tk.Entry(row,textvariable=d2,width=12).pack(side="left",padx=4)
        color="#f39c12" if kind=="achats" else "#27ae60"
        fn=self._achats if kind=="achats" else self._ventes
        tk.Button(row,text="Generer PDF",font=("Arial",9,"bold"),bg=color,fg="white",
                  relief="flat",padx=12,pady=4,cursor="hand2",
                  command=lambda a=d1,b=d2: fn(a.get(),b.get())).pack(side="left",padx=12)

    def _ask(self,name):
        return filedialog.asksaveasfilename(defaultextension=".pdf",
               filetypes=[("PDF","*.pdf")],initialfile=name,title="Enregistrer") or None

    def _ouvrir(self,path):
        try:
            os.startfile(path) if sys.platform=="win32" else subprocess.Popen(["xdg-open",path])
        except: pass

    def _run(self,fn,path):
        def go():
            try:
                fn(path)
                self.after(0,lambda:self.status.config(text=f"PDF cree: {os.path.basename(path)}",fg="#27ae60"))
                self.after(0,lambda:self._ouvrir(path))
            except Exception as e:
                self.after(0,lambda:self.status.config(text=f"Erreur: {e}",fg="#e74c3c"))
        threading.Thread(target=go,daemon=True).start()
        self.status.config(text="Generation en cours...",fg="#f39c12")

    def _stock(self):
        p=self._ask("rapport_stock.pdf")
        if p: self._run(rapport_stock,p)

    def _achats(self,d1,d2):
        p=self._ask(f"rapport_achats_{d1}_{d2}.pdf")
        if p: self._run(lambda path: rapport_achats(path,d1,d2), p)

    def _ventes(self,d1,d2):
        p=self._ask(f"rapport_ventes_{d1}_{d2}.pdf")
        if p: self._run(lambda path: rapport_ventes(path,d1,d2), p)

    def refresh(self): pass
