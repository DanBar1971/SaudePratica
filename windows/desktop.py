"""SaúdePrática Desktop — primeira versão experimental para Windows.

Janela inicial 16:9 e redimensionável. Usa imagens ORIGINAIS do projeto.
Perfis e medicamentos locais ficam protegidos por DPAPI.
AVISO: a versão inicial NÃO fornece alarmes nem sincronização com Android.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

from PIL import Image, ImageOps, ImageTk

# Local source execution and PyInstaller bundle resolve these assets identically.
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT))
from windows.secure_store import SecureStore, LocalStoreError
from shared.python.saude_backup import BackupError

DARK = "#071b23"
DARKER = "#04151d"
CARD = "#143441"
TEAL = "#24d5c5"
WHITE = "#f4fbfc"
MUTED = "#a6c1c8"
BUTTON = "#164c57"


class Desktop(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SaúdePrática Desktop · Experimental")
        self.geometry("1280x720")
        self.minsize(940, 620)
        self.configure(bg=DARK)
        self.store = None
        self.selected_profile = None
        self.page = "Início"
        self._background = Image.open(ROOT / "assets" / "saude_background.png").convert("RGB")
        self._icon = Image.open(ROOT / "assets" / "saude_icon.png").convert("RGBA")
        self._splash = Image.open(ROOT / "assets" / "saude_splash.png").convert("RGBA")
        self.iconphoto(True, ImageTk.PhotoImage(self._icon.resize((48, 48))))
        self._last_size = None
        self._backref = None

        self.canvas = tk.Canvas(self, bg=DARK, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        self.sidebar = tk.Frame(self.canvas, bg=DARKER)
        self.main = tk.Frame(self.canvas, bg=DARK)
        self.sidebar_id = self.canvas.create_window(0, 0, anchor="nw", window=self.sidebar)
        self.main_id = self.canvas.create_window(245, 0, anchor="nw", window=self.main)
        self.canvas.tag_lower("background")
        self._make_sidebar()
        try:
            self.store = SecureStore()
        except Exception as exc:
            messagebox.showerror("Armazenamento protegido",
                "Não foi possível abrir o armazenamento seguro desta conta Windows.\n"
                "Nenhum dado foi criado ou substituído.\n\n" + str(exc))
        self.show("Início")

    def _on_resize(self, event):
        w, h = max(event.width,1), max(event.height,1)
        if self._last_size == (w,h):
            return
        self._last_size = w,h
        # Centre crop portrait artwork to preserve proportions in a 16:9 window.
        image = ImageOps.fit(self._background, (w,h), method=Image.Resampling.LANCZOS,
                             centering=(0.5,0.5))
        self._backref = ImageTk.PhotoImage(image)
        if getattr(self,"background_id",None) is None:
            self.background_id = self.canvas.create_image(0,0,anchor="nw",image=self._backref,tags="background")
        else:
            self.canvas.itemconfigure(self.background_id, image=self._backref)
        self.canvas.tag_lower(self.background_id)
        sidebar_width = 235 if w>=1080 else 190
        self.canvas.coords(self.sidebar_id,0,0)
        self.canvas.itemconfigure(self.sidebar_id,width=sidebar_width,height=h)
        self.canvas.coords(self.main_id,sidebar_width,0)
        self.canvas.itemconfigure(self.main_id,width=w-sidebar_width,height=h)

    def _button(self, parent, title, action, wide=False):
        b = tk.Button(parent, text=title, command=action,
                      bg=BUTTON, fg=WHITE, activebackground="#127e80",
                      activeforeground=WHITE, font=("Segoe UI", 12),
                      relief="flat", bd=0, padx=18, pady=12, cursor="hand2",
                      wraplength=210)
        if wide: b.pack(fill="x", padx=12, pady=6)
        return b

    def _label(self, parent, text, size=14, color=WHITE, bold=False):
        return tk.Label(parent,text=text,fg=color,bg=parent.cget("bg"),
                        font=("Segoe UI",size,"bold" if bold else "normal"),
                        anchor="w",justify="left",wraplength=740)

    def _make_sidebar(self):
        mark=ImageTk.PhotoImage(self._icon.resize((80,80)))
        label=tk.Label(self.sidebar,image=mark,bg=DARKER)
        label.image=mark
        label.pack(pady=(20,2))
        tk.Label(self.sidebar,text="SaúdePrática",bg=DARKER,fg=TEAL,
                 font=("Segoe UI",18,"bold")).pack(pady=(0,18))
        for title in ("Início","Perfis","Medicação","Agenda","Documentos","Backup","Sincronização"):
            self._button(self.sidebar,title,lambda name=title:self.show(name),wide=True)
        tk.Label(self.sidebar,text="DESKTOP · EXPERIMENTAL",bg=DARKER,fg=MUTED,
                 font=("Segoe UI",9)).pack(side="bottom",pady=24)

    def _card(self, parent):
        return tk.Frame(parent,bg=CARD,highlightthickness=1,
                        highlightbackground="#215360",padx=20,pady=18)

    def _reset(self):
        for child in self.main.winfo_children():
            child.destroy()
        top=tk.Frame(self.main,bg=DARK)
        top.pack(fill="x",padx=26,pady=(25,10))
        self._label(top,self.page,26,bold=True).pack(side="left")
        profiles = self.store.profiles() if self.store else []
        current = next((p["name"] for p in profiles if p["id"]==self.selected_profile),"Sem perfil")
        tk.Label(top,text=current,bg=BUTTON,fg=TEAL,font=("Segoe UI",11),
                 padx=15,pady=9).pack(side="right")
        body=tk.Frame(self.main,bg=DARK)
        body.pack(fill="both",expand=True,padx=26,pady=(0,25))
        return body

    def show(self, page):
        self.page=page
        body=self._reset()
        if page=="Início": self._home(body)
        elif page=="Perfis": self._profiles(body)
        elif page=="Medicação": self._medication(body)
        elif page=="Backup": self._backup(body)
        elif page=="Sincronização": self._planned(body, "Sincronização bidirecional Windows ↔ Android", 
               "Emparelhamento seguro, seleção de perfis, comparação das alterações e resolução de conflitos. Ainda não disponível nesta versão experimental.")
        elif page=="Agenda": self._planned(body, "Agenda médica",
               "O modelo de agenda está previsto para a próxima etapa. Ainda não envia avisos.")
        elif page=="Documentos": self._planned(body, "Documentos digitais",
               "PDF, fotografias e outros anexos serão integrados com o backup universal. Ainda não estão disponíveis.")

    def _planned(self, body, title, text):
        card=self._card(body);card.pack(fill="x",pady=20)
        self._label(card,title,20,TEAL,True).pack(fill="x")
        self._label(card,text,13,MUTED).pack(fill="x",pady=(12,6))

    def _home(self, body):
        card=self._card(body);card.pack(fill="x",pady=(15,12))
        self._label(card,"SaúdePrática · Tudo num só lugar",22,TEAL,True).pack(fill="x")
        self._label(card,"A mesma identidade da aplicação Android, adaptada a uma janela Windows redimensionável.",
                    13,WHITE).pack(fill="x",pady=(12,10))
        profiles=self.store.profiles() if self.store else []
        n=sum(len(p.get("medications",[])) for p in profiles)
        self._label(card,f"Perfis: {len(profiles)}    ·    Medicamentos registados: {n}",15,WHITE,True).pack(fill="x",pady=6)
        self._button(card,"Gerir perfis",lambda:self.show("Perfis")).pack(anchor="w",pady=10)
        warning=self._card(body);warning.pack(fill="x",pady=12)
        self._label(warning,"Versão experimental · não substituir alarmes Android",14,TEAL,True).pack(fill="x")
        self._label(warning,"O Windows ainda não sincroniza com o telemóvel e não emite os alarmes de medicação. Os dados locais ficam protegidos na conta Windows.",12,MUTED).pack(fill="x",pady=8)

    def _profiles(self, body):
        actions=tk.Frame(body,bg=DARK);actions.pack(fill="x")
        self._button(actions,"+ Criar perfil",self.create_profile).pack(side="left",pady=10)
        if not self.store: self._planned(body,"Armazenamento indisponível","Não é seguro editar dados.");return
        for p in self.store.profiles():
            card=self._card(body);card.pack(fill="x",pady=5)
            self._label(card,p["name"],17,bold=True).pack(side="left")
            self._button(card,"Selecionar",lambda pid=p["id"]:self.choose_profile(pid)).pack(side="right")

    def create_profile(self):
        if not self.store: return
        name=simpledialog.askstring("Novo perfil","Nome do perfil:",parent=self)
        if name is None:return
        try:
            p=self.store.create_profile(name)
            self.selected_profile=p["id"]
            self.show("Perfis")
        except Exception as exc:messagebox.showerror("Perfil",str(exc),parent=self)

    def choose_profile(self, profile_id):
        self.selected_profile=profile_id
        self.show("Medicação")

    def _medication(self, body):
        if not self.store: self._planned(body,"Indisponível","Armazenamento protegido não foi aberto.");return
        if not self.selected_profile and self.store.profiles():
            self.selected_profile=self.store.profiles()[0]["id"]
        profile=self.store.get_profile(self.selected_profile) if self.selected_profile else None
        if not profile:
            self._planned(body,"Sem perfil selecionado","Cria ou seleciona um perfil para registar medicação.")
            self._button(body,"Criar perfil",self.create_profile).pack(anchor="w",pady=10);return
        actions=tk.Frame(body,bg=DARK);actions.pack(fill="x")
        self._button(actions,"+ Adicionar medicamento",self.add_medication).pack(side="left",pady=8)
        if not profile["medications"]:
            self._planned(body,"Sem medicação registada","Os registos desta versão ficam apenas no armazenamento local protegido.")
        for m in profile["medications"]:
            c=self._card(body);c.pack(fill="x",pady=5)
            self._label(c,m.get("name",""),16,WHITE,True).pack(fill="x")
            self._label(c,m.get("dose","")+"   ·   "+(m.get("time") or "Sem hora"),12,MUTED).pack(fill="x",pady=7)

    def add_medication(self):
        if not self.store or not self.selected_profile:return
        name=simpledialog.askstring("Medicação","Nome do medicamento:",parent=self)
        if name is None:return
        dose=simpledialog.askstring("Medicação","Dose (por exemplo 20 mg):",parent=self)
        if dose is None:return
        time=simpledialog.askstring("Medicação","Hora de aviso (HH:mm) ou vazio:",parent=self)
        if time is None:return
        route=simpledialog.askstring("Medicação","Via (oral, sublingual, parenteral, inhaled...):",parent=self)
        if route is None:return
        try:
            self.store.add_medication(self.selected_profile,name,dose,time,route.lower().strip())
            self.show("Medicação")
        except Exception as exc:messagebox.showerror("Medicação",str(exc),parent=self)

    def _backup(self, body):
        self._planned(body,"Backup seguro · formato .spbackup",
          "Ficheiro encriptado com palavra-passe e validado por SHA-256. Este formato está implementado aqui no Windows; a importação/exportação Android ainda não foi integrada. Não partilhes a palavra-passe pelo GitHub.")
        bar=tk.Frame(body,bg=DARK);bar.pack(fill="x",pady=10)
        self._button(bar,"Exportar backup",self.export_backup).pack(side="left",padx=(0,10))
        self._button(bar,"Restaurar backup",self.restore_backup).pack(side="left")

    def export_backup(self):
        if not self.store:return
        one=simpledialog.askstring("Encriptação","Cria uma palavra-passe (mínimo 10 caracteres):",show="*",parent=self)
        if one is None:return
        two=simpledialog.askstring("Confirmar palavra-passe","Repete a palavra-passe:",show="*",parent=self)
        if two is None:return
        if one!=two:messagebox.showerror("Backup","As palavras-passe não coincidem.",parent=self);return
        where=filedialog.asksaveasfilename(parent=self,title="Guardar backup encriptado",
            defaultextension=".spbackup",filetypes=[("SaúdePrática Backup","*.spbackup")],
            initialfile="SaudePratica_"+datetime.now().strftime("%Y%m%d")+".spbackup")
        if not where:return
        try:
            data=self.store.export_backup(one)
            Path(where).write_bytes(data)
            messagebox.showinfo("Backup","Backup encriptado guardado com sucesso.",parent=self)
        except Exception as exc:messagebox.showerror("Backup",str(exc),parent=self)

    def restore_backup(self):
        if not self.store:return
        where=filedialog.askopenfilename(parent=self,title="Abrir backup encriptado",
                                           filetypes=[("SaúdePrática Backup","*.spbackup")])
        if not where:return
        password=simpledialog.askstring("Restauro","Palavra-passe do backup:",show="*",parent=self)
        if password is None:return
        try:
            blob=Path(where).read_bytes()
            people,verified=self.store.inspect_backup(blob,password)
            summary=", ".join(p["name"] for p in people)
            if not messagebox.askyesno("Confirmar restauro",
                f"Adicionar {len(people)} perfil(is): {summary}\n"
                "Não serão substituídos perfis existentes.\nContinuar?",parent=self):
                return
            count=self.store.restore_backup(verified)
            messagebox.showinfo("Restauro",f"{count} perfil(is) importado(s).",parent=self)
            self.show("Perfis")
        except Exception as exc:
            messagebox.showerror("Restauro",str(exc),parent=self)


if __name__=="__main__":
    Desktop().mainloop()
