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
from tkinter import filedialog, messagebox, simpledialog, ttk

from PIL import Image, ImageOps, ImageTk

# Local source execution and PyInstaller bundle resolve these assets identically.
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT))
from windows.secure_store import SecureStore, LocalStoreError
from shared.python.saude_backup import BackupError
from windows.ui_widgets import RoundedButton

DARK = "#071d25"
DARKER = "#041720"
CARD = "#143742"
TEAL = "#24d5c5"
WHITE = "#f4fbfc"
MUTED = "#a6c1c8"
BUTTON = "#13505c"


class Desktop(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SaúdePrática Desktop · 0.3.0 experimental")
        self.geometry("1280x720")
        self.minsize(1040, 640)
        self.configure(bg=DARK)
        self.store = None
        self.selected_profile = None
        self.page = "Início"
        self.selected_medication = None
        self._editor_open = False
        self._background = Image.open(ROOT / "assets" / "saude_background.png").convert("RGB")
        self._icon = Image.open(ROOT / "assets" / "saude_icon.png").convert("RGBA")
        # Use the real Windows icon and keep a PhotoImage for the title bar.
        icon_file = ROOT / "assets" / "saude_icon.ico"
        if icon_file.is_file():
            try:
                self.iconbitmap(str(icon_file))
            except tk.TclError:
                pass
        self._title_icon = ImageTk.PhotoImage(
            self._icon.resize((48, 48), Image.Resampling.LANCZOS))
        self.iconphoto(True, self._title_icon)
        self._init_theme()
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

    def _init_theme(self):
        """Keep drop-downs dark and legible; no white Windows comboboxes."""
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Saude.TCombobox", padding=(12, 8),
                        fieldbackground="#0b2a34", background="#164854",
                        foreground="#f4fbfc", arrowcolor="#55e8db",
                        bordercolor="#2a6672", lightcolor="#2a6672",
                        darkcolor="#2a6672", relief="flat")
        style.map("Saude.TCombobox",
                  fieldbackground=[("readonly", "#0b2a34")],
                  foreground=[("readonly", "#f4fbfc")],
                  selectbackground=[("readonly", "#0b2a34")],
                  selectforeground=[("readonly", "#f4fbfc")])
        style.configure("Saude.Vertical.TScrollbar", background="#125260",
                        troughcolor="#0a252e", arrowcolor="#5ce6d6",
                        bordercolor="#0a252e")
        self.option_add("*TCombobox*Listbox.background", "#0b2a34")
        self.option_add("*TCombobox*Listbox.foreground", "#f4fbfc")
        self.option_add("*TCombobox*Listbox.selectBackground", "#176c75")
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

    def _button(self, parent, title, action, wide=False):
        b = RoundedButton(parent, title, action, height=48,
                          fill=BUTTON, fg=WHITE, radius=13)
        if wide:
            b.pack(fill="x", padx=12, pady=6)
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
        self.nav_buttons = {}
        for title in ("Início","Perfis","Medicação","Agenda","Documentos","Backup","Sincronização"):
            button = self._button(self.sidebar, title, lambda name=title:self.show(name), wide=True)
            self.nav_buttons[title] = button
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
        if self._editor_open and self.page == "Medicação" and page != "Medicação":
            if not messagebox.askyesno("Sair da ficha",
                    "Tens uma ficha de medicação aberta. Sair sem guardar alterações?",
                    parent=self):
                return
        self._editor_open = False
        self.page=page
        for label, button in getattr(self, "nav_buttons", {}).items():
            active = label == page
            button.configure(bg="#177b7f" if active else BUTTON,
                             fg="#ffffff" if active else WHITE)
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
        """Dashboard legível num PC, com iconografia oficial."""
        hero=tk.Frame(body,bg=CARD,highlightthickness=1,
                      highlightbackground="#27626a",padx=26,pady=24)
        hero.pack(fill="x",pady=(12,16))
        text=tk.Frame(hero,bg=CARD)
        text.pack(side="left",fill="both",expand=True)
        self._label(text,"SAÚDEPRÁTICA DESKTOP",12,TEAL,True).pack(anchor="w")
        self._label(text,"Tudo num só lugar.",26,WHITE,True).pack(
            anchor="w",pady=(13,8))
        self._label(text,"Os teus perfis, medicação e documentos, organizados "
                         "num ambiente pensado para Windows.",
                    13,MUTED).pack(anchor="w",pady=(0,18))
        self._button(text,"Gerir medicação",
                     lambda:self.show("Medicação")).pack(anchor="w")
        logo=ImageTk.PhotoImage(self._icon.resize((170,170),
                                                    Image.Resampling.LANCZOS))
        logo_widget=tk.Label(hero,image=logo,bg=CARD,bd=0)
        logo_widget.image=logo
        logo_widget.pack(side="right",padx=(15,0))

        profiles=self.store.profiles() if self.store else []
        n=sum(len(p.get("medications",[])) for p in profiles)
        counts=tk.Frame(body,bg=DARK)
        counts.pack(fill="x",pady=(0,15))
        for label,value in (("Perfis registados",len(profiles)),
                            ("Medicamentos",n),
                            ("Cópias de segurança"," .spbackup")):
            card=tk.Frame(counts,bg="#103540",highlightthickness=1,
                          highlightbackground="#27626a",padx=20,pady=16)
            card.pack(side="left",fill="both",expand=True,padx=(0,12))
            self._label(card,str(value),21,TEAL,True).pack(anchor="w")
            self._label(card,label,11,MUTED).pack(anchor="w",pady=(6,0))

        warning=self._card(body)
        warning.pack(fill="x")
        self._label(warning,"Versão experimental · os alarmes continuam no Android",
                    13,TEAL,True).pack(anchor="w")
        self._label(warning,
            "Os dados desta versão ficam protegidos nesta conta Windows. "
            "A sincronização Android ↔ Windows está em desenvolvimento; "
            "não uses esta versão como única fonte de dados clínicos.",
            12,MUTED).pack(anchor="w",pady=(8,0))

    def _profiles(self, body):
        if not self.store:
            self._planned(body, "Armazenamento indisponível",
                          "Não é seguro editar dados sem a proteção Windows.")
            return
        self._label(body, "Os perfis são guardados nesta conta Windows.", 12, MUTED).pack(
            anchor="w", pady=(0, 8))
        create = self._card(body)
        create.pack(fill="x", pady=(8, 16))
        self._label(create, "Novo perfil", 16, TEAL, True).pack(anchor="w")
        row = tk.Frame(create, bg=CARD)
        row.pack(fill="x", pady=(12, 0))
        name = tk.StringVar()
        entry = self._entry(row, name)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 12))
        entry.insert(0, "")
        def save_profile():
            try:
                p = self.store.create_profile(name.get())
                self.selected_profile = p["id"]
                self.show("Perfis")
            except Exception as exc:
                messagebox.showerror("Perfil", str(exc), parent=self)
        self._button(row, "Criar perfil", save_profile).pack(side="right")
        entry.bind("<Return>", lambda event: save_profile())

        for p in self.store.profiles():
            card = self._card(body)
            card.pack(fill="x", pady=5)
            self._label(card, p["name"], 17, bold=True).pack(side="left")
            self._button(card, "Abrir medicação",
                         lambda pid=p["id"]: self.choose_profile(pid)).pack(side="right")

    def _entry(self, parent, var):
        return tk.Entry(parent, textvariable=var, relief="flat", bd=0,
                        highlightthickness=1, highlightbackground="#35606b",
                        highlightcolor=TEAL, bg="#09242c", fg=WHITE,
                        insertbackground=WHITE, font=("Segoe UI", 12))

    def create_profile(self):
        self.show("Perfis")

    def choose_profile(self, profile_id):
        self.selected_profile=profile_id
        self.selected_medication=None
        self.show("Medicação")

    def _form_field(self, parent, caption, variable, row, column=0, width=1):
        box=tk.Frame(parent,bg=CARD)
        box.grid(row=row,column=column,columnspan=width,sticky="ew",padx=6,pady=8)
        self._label(box,caption,11,MUTED,True).pack(anchor="w",pady=(0,7))
        entry=self._entry(box,variable)
        entry.pack(fill="x",ipady=10)
        return entry

    def _form_combo(self, parent, caption, variable, choices, row, column=0):
        box=tk.Frame(parent,bg=CARD)
        box.grid(row=row,column=column,sticky="ew",padx=6,pady=8)
        self._label(box,caption,11,MUTED,True).pack(anchor="w",pady=(0,7))
        combo=ttk.Combobox(box,textvariable=variable,values=choices,state="readonly",
                           font=("Segoe UI",12),style="Saude.TCombobox")
        combo.pack(fill="x",ipady=8)
        return box,combo

    def _medication(self, body):
        if not self.store:
            self._planned(body,"Armazenamento protegido indisponível",
                          "Não é possível guardar medicação com segurança.")
            return
        profiles=self.store.profiles()
        if not self.selected_profile and profiles:
            self.selected_profile=profiles[0]["id"]
        profile=self.store.get_profile(self.selected_profile) if self.selected_profile else None
        if not profile:
            self._planned(body,"Sem perfil selecionado",
                          "Cria ou seleciona um perfil para registar medicação.")
            self._button(body,"Criar perfil",lambda:self.show("Perfis")).pack(anchor="w",pady=10)
            return

        header=tk.Frame(body,bg=DARK)
        header.pack(fill="x",pady=(0,14))
        self._label(header,f"Perfil: {profile['name']}",13,MUTED).pack(side="left")
        self._button(header,"+ Nova medicação",
                     lambda:self._show_medication_editor(editor,profile,None)).pack(side="right")

        workspace=tk.Frame(body,bg=DARK)
        workspace.pack(fill="both",expand=True)
        list_side=tk.Frame(workspace,bg=CARD,padx=12,pady=16,
                           highlightthickness=1,highlightbackground="#275662")
        list_side.pack(side="left",fill="y",padx=(0,14))
        list_side.configure(width=270)
        list_side.pack_propagate(False)
        self._label(list_side,"Medicamentos",16,WHITE,True).pack(anchor="w",padx=5)
        self._label(list_side,f"{len(profile['medications'])} registados",
                    11,MUTED).pack(anchor="w",padx=5,pady=(3,15))

        editor=tk.Frame(workspace,bg=CARD,highlightthickness=1,
                        highlightbackground="#275662")
        editor.pack(side="left",fill="both",expand=True)

        if not profile["medications"]:
            self._label(list_side,"Nenhum medicamento.\nSeleciona + Nova medicação.",
                        12,MUTED).pack(fill="x",pady=12)

        for medication in profile["medications"]:
            card=tk.Frame(list_side,bg="#0c323d",padx=12,pady=12,
                          highlightthickness=1,highlightbackground="#21535e")
            card.pack(fill="x",pady=5)
            name=medication.get("name","Sem nome")
            self._label(card,name[:38],12,WHITE,True).pack(anchor="w")
            time=medication.get("time") or "Sem horário"
            tag=(" · Sem alarme" if medication.get("no_alarm") else
                 (" · Suspensa" if medication.get("suspended") else ""))
            self._label(card,medication.get("dose","")+" · "+time+tag,
                        10,MUTED).pack(anchor="w",pady=(6,0))
            self._button(card,"Editar",lambda m=medication:
                         self._show_medication_editor(editor,profile,m)).pack(
                             anchor="e",pady=(8,0))

        initial=next((m for m in profile["medications"] if m.get("id")==self.selected_medication),None)
        if initial is not None:
            self._show_medication_editor(editor,profile,initial)
        else:
            self._medication_empty(editor)

    def _medication_empty(self, parent):
        for child in parent.winfo_children():child.destroy()
        self._editor_open=False
        title=tk.Frame(parent,bg=CARD,padx=34,pady=35)
        title.pack(fill="both",expand=True)
        icon=ImageTk.PhotoImage(self._icon.resize((118,118),Image.Resampling.LANCZOS))
        mark=tk.Label(title,image=icon,bg=CARD,bd=0)
        mark.image=icon
        mark.pack(anchor="w",pady=(2,24))
        self._label(title,"Uma ficha, todos os campos.",23,TEAL,True).pack(anchor="w")
        self._label(title,
            "Seleciona Editar num medicamento ou cria um novo.\n"
            "Os dados aparecem num único formulário, sem caixas sucessivas.",
            13,MUTED).pack(anchor="w",pady=15)

    def _show_medication_editor(self,parent,profile,medication):
        for child in parent.winfo_children():child.destroy()
        self._editor_open=True
        self.selected_medication=medication.get("id") if medication else None
        vals=medication or {}
        heading=tk.Frame(parent,bg=CARD,padx=24,pady=14)
        heading.pack(fill="x")
        self._label(heading,"Editar medicação" if medication else "Nova medicação",
                    20,WHITE,True).pack(anchor="w")
        self._label(heading,"Informação principal · todas as alterações num único ecrã",
                    11,MUTED).pack(anchor="w",pady=(4,0))

        section=tk.Frame(parent,bg=CARD)
        section.pack(fill="both",expand=True,padx=(15,5))
        cv=tk.Canvas(section,bg=CARD,highlightthickness=0)
        sb=ttk.Scrollbar(section,orient="vertical",command=cv.yview,style="Saude.Vertical.TScrollbar")
        cv.configure(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y")
        cv.pack(side="left",fill="both",expand=True)
        form=tk.Frame(cv,bg=CARD,padx=8,pady=8)
        window=cv.create_window((0,0),window=form,anchor="nw")
        form.bind("<Configure>",lambda _:cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>",lambda e:cv.itemconfigure(window,width=e.width))
        def wheel(event):
            if event.delta:cv.yview_scroll(int(-1*(event.delta/120)),"units")
        cv.bind("<Enter>",lambda _:cv.bind_all("<MouseWheel>",wheel))
        cv.bind("<Leave>",lambda _:cv.unbind_all("<MouseWheel>"))

        form.grid_columnconfigure(0,weight=1,uniform="details")
        form.grid_columnconfigure(1,weight=1,uniform="details")
        name=tk.StringVar(value=vals.get("name",""))
        dose=tk.StringVar(value=vals.get("dose",""))
        time=tk.StringVar(value=vals.get("time","07:00"))
        indication=tk.StringVar(value=vals.get("indication",""))
        routes={
            "Por indicar": "", "Via oral": "oral","Via sublingual": "sublingual",
            "Injeção / parentérica": "parenteral","Via tópica / cutânea": "topical",
            "Via inalatória": "inhaled","Via retal": "rectal",
            "Via vaginal": "vaginal","Via ocular": "ocular",
            "Via otológica": "otic","Via nasal": "nasal","Outra": "other",
        }
        injections={
            "Por especificar":"","Subcutânea":"sc","Intramuscular":"im",
            "Intravenosa":"iv","Intradérmica":"id","Outra injeção":"other"
        }
        route_start=next((label for label,key in routes.items()
                          if key==vals.get("administration_route","")),"Por indicar")
        injection_start=next((label for label,key in injections.items()
                              if key==vals.get("injection_type","")),"Por especificar")
        route=tk.StringVar(value=route_start)
        injection=tk.StringVar(value=injection_start)
        takes=("", "Jejum", "Pequeno-almoço", "Almoço", "Jantar",
               "Às refeições", "Ao deitar", "SOS", "Horário livre",
               "De 4 em 4 horas", "De 6 em 6 horas", "De 12 em 12 horas")
        take=tk.StringVar(value=vals.get("dose_pattern",""))
        no_alarm=tk.BooleanVar(value=bool(vals.get("no_alarm",False)))
        suspended=tk.BooleanVar(value=bool(vals.get("suspended",False)))

        self._label(form,"IDENTIFICAÇÃO",11,TEAL,True).grid(
            row=0,column=0,columnspan=2,sticky="w",pady=(4,9),padx=6)
        focus=self._form_field(form,"Nome do medicamento",name,1)
        self._form_field(form,"Dose / apresentação",dose,1,1)
        route_box,_=self._form_combo(form,"Via de administração",route,list(routes),2)
        inject_box,_=self._form_combo(form,"Tipo de injeção",injection,list(injections),2,1)
        take_box,take_combo=self._form_combo(form,"Tipo de toma",take,list(takes),3,0)
        self._form_field(form,"Hora de aviso (HH:mm)",time,3,1)
        self._form_field(form,"Posologia / indicação",indication,4,width=2)

        def update_route(*_):
            if routes.get(route.get())=="parenteral":
                inject_box.grid()
            else:
                inject_box.grid_remove()
        route.trace_add("write",update_route)
        update_route()
        def update_sos(*_):
            if take.get()=="SOS":no_alarm.set(True)
        take.trace_add("write",update_sos)

        toggles=tk.Frame(form,bg=CARD)
        toggles.grid(row=5,column=0,columnspan=2,sticky="ew",padx=6,pady=(12,12))
        for label,var in (("Sem alarme (registo apenas)",no_alarm),
                          ("Terapêutica suspensa",suspended)):
            tk.Checkbutton(toggles,text=label,variable=var,bg=CARD,fg=WHITE,
                           selectcolor="#164c57",activebackground=CARD,
                           activeforeground=TEAL,font=("Segoe UI",11),
                           padx=5,pady=8).pack(side="left",padx=(0,12))
        self._label(form,"NOTAS",11,TEAL,True).grid(
            row=6,column=0,columnspan=2,sticky="w",pady=(0,6),padx=6)
        notes=tk.Text(form,height=4,wrap="word",relief="flat",bd=0,
                      highlightthickness=1,highlightbackground="#35606b",
                      highlightcolor=TEAL,bg="#09242c",fg=WHITE,
                      insertbackground=WHITE,font=("Segoe UI",11),padx=12,pady=10)
        notes.grid(row=7,column=0,columnspan=2,sticky="ew",padx=6,pady=(0,14))
        notes.insert("1.0",vals.get("notes",""))

        footer=tk.Frame(parent,bg="#102b34",padx=20,pady=14)
        footer.pack(side="bottom",fill="x")
        self._label(footer,"Sem alterações aos alarmes Android",10,MUTED).pack(side="left")

        def cancel():
            self.selected_medication=None
            self._editor_open=False
            self.show("Medicação")

        def save():
            try:
                self.store.save_medication(profile["id"],{
                    "name":name.get(),"dose":dose.get(),"time":time.get(),
                    "administration_route":routes[route.get()],
                    "injection_type":injections[injection.get()],
                    "dose_pattern":take.get(),"indication":indication.get(),
                    "notes":notes.get("1.0","end-1c"),
                    "no_alarm":no_alarm.get(),"suspended":suspended.get(),
                }, medication_id=medication.get("id") if medication else None)
                self.selected_medication=None
                self._editor_open=False
                self.show("Medicação")
            except (LocalStoreError, ValueError, KeyError) as exc:
                messagebox.showerror("Verificar medicação",str(exc),parent=self)
        self._button(footer,"✓ Guardar",save).pack(side="right",padx=(10,0))
        self._button(footer,"Cancelar",cancel).pack(side="right")
        focus.focus_set()

    def _backup(self, body):
        self._planned(body,"Backup encriptado da SaúdePrática · .spbackup",
          "Guarda os perfis e medicação deste Windows num ficheiro privado, protegido por palavra-passe. Não é um ZIP comum. Conserva a palavra-passe em local seguro; sem ela não será possível restaurar. A importação no Android ainda não está disponível.")
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
    app = Desktop()
    # The bootloader splash stays visible until the first real window is ready.
    try:
        import pyi_splash
        pyi_splash.close()
    except ImportError:
        pass
    app.mainloop()
