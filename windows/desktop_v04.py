"""SaúdePrática Desktop 0.4 — modern adaptive Windows client.

Phase 1: full profile editing, active profile selection, medication,
appearance/language, original brand assets and legacy DPAPI/backup compatibility.
Agenda, attachments, live Android syncing and alarms are explicitly not built.
"""
from __future__ import annotations

import base64
from io import BytesIO
import os
from datetime import datetime
from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageOps, ImageEnhance, ImageDraw

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT))
from windows.secure_store import SecureStore, LocalStoreError
from shared.python.saude_backup import BackupError
from windows.ui_v04_i18n import translate

ctk.set_default_color_theme("blue")
VERSION = "0.4.0"
TEAL = "#00c9b7"
TEAL_HOVER = "#00a99b"
BLUE = "#0e6976"
WHITE = "#edfaff"
ROUTES = {
    "Não indicada": "", "Via oral": "oral", "Via sublingual": "sublingual",
    "Injeção / parentérica": "parenteral", "Tópica / cutânea": "topical",
    "Inalatória": "inhaled", "Retal": "rectal", "Vaginal": "vaginal",
    "Ocular": "ocular", "Otológica": "otic", "Nasal": "nasal", "Outra": "other"
}
INJECTIONS = {"Não indicada": "", "Subcutânea": "sc",
              "Intramuscular": "im", "Intravenosa": "iv",
              "Intradérmica": "id", "Outra": "other"}
TAKES = ["", "Jejum", "Pequeno-almoço", "Almoço", "Jantar",
         "Às refeições", "Ao deitar", "SOS", "Horário livre",
         "De 4 em 4 horas", "De 6 em 6 horas", "De 12 em 12 horas"]
TABS = [("home","⌂","home"), ("profiles","◉","profiles"),
        ("medication","✚","medication"), ("agenda","▦","agenda"),
        ("more","⋯","menu_more")]
MODULES = [
    ("profiles","👥","profiles"), ("medication","💊","medication"),
    ("agenda","📅","agenda"), ("documents","📄","documents"),
    ("water","💧","water"), ("nutrition","🥗","nutrition"),
    ("care","🤝","care"), ("residences","🏠","residences"),
    ("shortcuts","🔗","shortcuts"), ("info","💡","info"),
    ("backup","🔐","backup"), ("sync","🔄","sync"),
    ("options","⚙️","options"),
]
LANG_NAMES = {"pt":"Português","en":"English","fr":"Français",
              "de":"Deutsch","es":"Español"}
THEME_KEYS = {"system":"theme_system","dark":"theme_dark","light":"theme_light"}


class Desktop(ctk.CTk):
    def __init__(self):
        self.store = SecureStore()
        pref = self.store.settings()
        self.lang = pref.get("language", "pt") if pref.get("language") in LANG_NAMES else "pt"
        self.theme = pref.get("theme", "system") if pref.get("theme") in THEME_KEYS else "system"
        ctk.set_appearance_mode(self.theme)
        super().__init__()
        self.title("SaúdePrática Desktop · " + VERSION)
        self.geometry("1350x810")
        self.minsize(1060, 690)
        self.active_id = pref.get("active_profile")
        if not self.store.get_profile(self.active_id):
            self.active_id = self.store.profiles()[0]["id"] if self.store.profiles() else None
        self.editing_profile = self.active_id
        self.editing_med = None
        self.page = "home"
        self.profile_widgets = {}
        self.med_widgets = {}
        self.photo_draft = ""
        self._assets()
        self._render()

    def t(self, key):
        return translate(self.lang, key)

    def _assets(self):
        self._original_icon = Image.open(ROOT/"assets"/"saude_icon.png").convert("RGBA")
        self._original_bg = Image.open(ROOT/"assets"/"saude_background.png").convert("RGB")
        icon_file = ROOT/"assets"/"saude_icon.ico"
        if icon_file.is_file():
            try: self.iconbitmap(str(icon_file))
            except tk.TclError: pass
        self.logo = ctk.CTkImage(self._original_icon, self._original_icon, size=(48,48))
        self.hero_logo = ctk.CTkImage(self._original_icon,self._original_icon,size=(116,116))
        self._hero_image = None
        self._set_hero_art()

    def _set_hero_art(self):
        image = ImageOps.fit(self._original_bg, (1200,265),
                             method=Image.Resampling.LANCZOS, centering=(0.51,0.51)).convert("RGBA")
        veil = Image.new("RGBA",image.size,(2,19,28,150))
        image=Image.alpha_composite(image,veil).convert("RGB")
        self._hero_image = ctk.CTkImage(image,image,size=(1200,265))

    def _palette(self):
        if ctk.get_appearance_mode().lower()=="light":
            return dict(bg="#eff6f8",panel="#ffffff",panel2="#e6f1f4",
                        text="#132d35",muted="#46626b",line="#c7e0e3",
                        field="#f7fbfc",banner="#062630")
        return dict(bg="#051a23",panel="#102e39",panel2="#153c47",
                    text="#f0fafa",muted="#acc9d0",line="#27555e",
                    field="#0b2630",banner="#062630")

    def _button(self,parent,label,command,accent=False,width=150,height=40):
        p=self.p
        return ctk.CTkButton(parent,text=label,command=command,width=width,height=height,
            corner_radius=13,font=ctk.CTkFont(family="Segoe UI",size=13,weight="bold"),
            fg_color=TEAL if accent else p["panel2"],
            hover_color=TEAL_HOVER if accent else BLUE,
            text_color="#05252c" if accent else p["text"])

    def _label(self,parent,text,size=13,bold=False,color=None,anchor="w",wrap=None):
        return ctk.CTkLabel(parent,text=text,anchor=anchor,
            text_color=color or self.p["text"],
            font=ctk.CTkFont(family="Segoe UI",size=size,
                             weight="bold" if bold else "normal"),
            wraplength=wrap or 0)

    def _card(self,parent,rounding=19,**kw):
        return ctk.CTkFrame(parent,fg_color=self.p["panel"],
            corner_radius=rounding,border_width=1,
            border_color=self.p["line"],**kw)

    def _clear(self):
        for child in self.winfo_children():
            child.destroy()

    def _render(self):
        self.p=self._palette()
        self.configure(fg_color=self.p["bg"])
        self._clear()
        header=ctk.CTkFrame(self,height=88,fg_color=self.p["panel"],
                            corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        brand=ctk.CTkFrame(header,fg_color="transparent")
        brand.pack(side="left",padx=(24,16),fill="y")
        ctk.CTkLabel(brand,image=self.logo,text="").pack(side="left",padx=(0,9),pady=16)
        self._label(brand,"SaúdePrática",20,True,color=TEAL).pack(side="left",pady=22)
        nav=ctk.CTkFrame(header,fg_color="transparent")
        nav.pack(side="left",padx=(8,8),fill="y")
        for key,glyph,title in TABS:
            target=key
            active=self.page==target or (target=="more" and self.page not in ("home","profiles","medication","agenda"))
            label=glyph+"  "+self.t(title)
            b=self._button(nav,label,lambda k=key:self.navigate(k),accent=active,width=110,height=42)
            b.pack(side="left",padx=3,pady=23)

        right=ctk.CTkFrame(header,fg_color="transparent")
        right.pack(side="right",padx=(4,23),pady=20)
        self._label(right,self.t("active_profile"),11,color=self.p["muted"]).pack(side="left",padx=(0,9))
        entries=self.store.profiles()
        self.profile_choices={}
        for p in entries:
            title=p["name"]
            if title in self.profile_choices:
                title += " · "+p["id"][:6]
            self.profile_choices[title]=p["id"]
        if not self.profile_choices:
            self.profile_choices[self.t("active_none")]=None
        selected=next((label for label,pid in self.profile_choices.items()
                       if pid==self.active_id),next(iter(self.profile_choices)))
        self.profile_select=ctk.CTkOptionMenu(right,values=list(self.profile_choices),
            command=self._select_profile,width=165,height=39,corner_radius=12,
            fg_color=self.p["panel2"],button_color=BLUE,button_hover_color=TEAL_HOVER,
            text_color=self.p["text"],dropdown_fg_color=self.p["panel"],
            dropdown_text_color=self.p["text"])
        self.profile_select.set(selected)
        self.profile_select.pack(side="left")

        body=ctk.CTkFrame(self,fg_color="transparent")
        body.pack(fill="both",expand=True,padx=26,pady=(20,6))
        self.body=body
        if self.page=="home": self._home()
        elif self.page=="profiles": self._profiles()
        elif self.page=="medication": self._medication()
        elif self.page=="backup": self._backup()
        elif self.page=="options": self._settings_page()
        elif self.page=="more": self._modules(full=True)
        else: self._pending(self.page)

        footer=ctk.CTkFrame(self,height=38,fg_color=self.p["panel"],corner_radius=0)
        footer.pack(fill="x",side="bottom")
        self._label(footer,self.t("status_experimental"),11,color=self.p["muted"]).pack(side="left",padx=26,pady=8)
        self._label(footer,self.t("not_alarm"),11,color=self.p["muted"]).pack(side="right",padx=26,pady=8)

    def _heading(self,title,subtitle=None):
        self._label(self.body,title,28,True).pack(anchor="w",pady=(0,4))
        if subtitle:
            self._label(self.body,subtitle,13,color=self.p["muted"]).pack(anchor="w",pady=(0,15))

    def navigate(self,page):
        self.page=page
        self._render()

    def _select_profile(self,label):
        new_id=self.profile_choices.get(label)
        if new_id == self.active_id:return
        self.active_id=new_id
        self.editing_profile=new_id
        self.editing_med=None
        try:self.store.update_settings(active_profile=new_id)
        except LocalStoreError as exc:
            messagebox.showerror("SaúdePrática",str(exc),parent=self)
        self._render()

    def _home(self):
        banner=ctk.CTkFrame(self.body,height=234,fg_color=self.p["banner"],
                            corner_radius=23)
        banner.pack(fill="x",pady=(2,15))
        banner.pack_propagate(False)
        wallpaper=ctk.CTkLabel(banner,image=self._hero_image,text="")
        wallpaper.place(x=0,y=0,relwidth=1,relheight=1)
        content=ctk.CTkFrame(banner,fg_color="transparent")
        content.place(x=30,y=24)
        self._label(content,"SAÚDEPRÁTICA DESKTOP",12,True,color="#67eee2").pack(anchor="w")
        self._label(content,self.t("welcome"),31,True,color=WHITE).pack(anchor="w",pady=(10,3))
        self._label(content,self.t("welcome_sub"),14,color="#d5ebed").pack(anchor="w")
        self._button(content,self.t("welcome_action"),
                     lambda:self.navigate("profiles"),True,180,40).pack(anchor="w",pady=(20,0))
        ctk.CTkLabel(banner,image=self.hero_logo,text="").place(relx=.89,rely=.45,anchor="center")

        stats=ctk.CTkFrame(self.body,fg_color="transparent")
        stats.pack(fill="x",pady=(0,16))
        profiles=self.store.profiles()
        med_count=sum(len(p.get("medications",[])) for p in profiles)
        for i,(val,label) in enumerate(((str(len(profiles)),self.t("registered_profiles")),
                                        (str(med_count),self.t("registered_meds")),
                                        ("0",self.t("agenda")))):
            stats.grid_columnconfigure(i,weight=1)
            card=self._card(stats)
            card.grid(row=0,column=i,sticky="ew",padx=5,ipady=12)
            self._label(card,val,27,True,color=TEAL).pack(anchor="w",padx=22,pady=(5,0))
            self._label(card,label,12,color=self.p["muted"]).pack(anchor="w",padx=22)
        self._modules(compact=True)

    def _modules(self,compact=False,full=False):
        if full:
            self._heading(self.t("menu_more"),self.t("notice"))
        else:
            self._label(self.body,self.t("sections"),19,True).pack(anchor="w",pady=(0,10))
        outer=ctk.CTkScrollableFrame(self.body,fg_color="transparent",
                                     scrollbar_button_color=self.p["panel2"])
        outer.pack(fill="both",expand=True)
        items=MODULES if full else MODULES[:10]
        cols=4 if full else 5
        for col in range(cols):outer.grid_columnconfigure(col,weight=1)
        for i,(key,glyph,label) in enumerate(items):
            r,c=divmod(i,cols)
            card=self._card(outer)
            card.grid(row=r,column=c,sticky="nsew",padx=6,pady=7)
            self._label(card,glyph,31).pack(anchor="w",padx=17,pady=(9,2))
            self._label(card,self.t(label),14,True).pack(anchor="w",padx=17,pady=(0,9))
            self._button(card,self.t("open"),lambda k=key:self.navigate(k),
                         width=110,height=33).pack(anchor="w",padx=16,pady=(0,14))

    def _pending(self,key):
        self._heading(self.t(key),self.t("module_pending"))
        card=self._card(self.body)
        card.pack(fill="x",pady=14)
        self._label(card,self.t("coming"),22,True,color=TEAL).pack(anchor="w",padx=24,pady=(24,10))
        self._label(card,self.t("soon_detail"),15,color=self.p["muted"]).pack(anchor="w",padx=24,pady=(0,26))

    def _two_pane(self,left_title,left_width=330):
        container=ctk.CTkFrame(self.body,fg_color="transparent")
        container.pack(fill="both",expand=True)
        left=self._card(container,width=left_width)
        left.pack(side="left",fill="y",padx=(0,16))
        left.pack_propagate(False)
        self._label(left,left_title,19,True).pack(anchor="w",padx=17,pady=(20,8))
        left_scroll=ctk.CTkScrollableFrame(left,fg_color="transparent")
        left_scroll.pack(fill="both",expand=True,padx=10,pady=(2,12))
        right=self._card(container)
        right.pack(side="left",fill="both",expand=True)
        return left,left_scroll,right

    def _profiles(self):
        self._heading(self.t("profiles"),self.t("profile_hint"))
        left,listing,right=self._two_pane(self.t("registered_profiles"),315)
        self._button(listing,"+ "+self.t("new_profile"),
                     self._new_profile,True,width=260,height=43).pack(fill="x",pady=(3,12))
        for profile in self.store.profiles():
            active=profile["id"]==self.active_id
            row=ctk.CTkFrame(listing,fg_color=self.p["panel2"],corner_radius=14)
            row.pack(fill="x",pady=5)
            icon="◉" if active else "○"
            text=icon+"  "+profile["name"]
            ctk.CTkButton(row,text=text,anchor="w",fg_color="transparent",
                hover_color=BLUE,text_color=self.p["text"],height=50,
                command=lambda pid=profile["id"]:self._edit_profile(pid)).pack(fill="x",padx=8,pady=6)
        self._profile_form(right)

    def _new_profile(self):
        self.editing_profile=None
        self._render()

    def _edit_profile(self,pid):
        self.editing_profile=pid
        self.active_id=pid
        self.store.update_settings(active_profile=pid)
        self._render()

    def _text_field(self,parent,label,initial="",row=0,col=0,columns=2):
        box=ctk.CTkFrame(parent,fg_color="transparent")
        box.grid(row=row,column=col,columnspan=columns,sticky="ew",padx=7,pady=7)
        self._label(box,self.t(label),12,True,color=self.p["muted"]).pack(anchor="w",pady=(0,6))
        entry=ctk.CTkEntry(box,height=40,corner_radius=11,
            border_color=self.p["line"],fg_color=self.p["field"],
            text_color=self.p["text"],font=ctk.CTkFont(size=13))
        entry.insert(0,str(initial or ""))
        entry.pack(fill="x")
        return entry

    def _profile_form(self,frame):
        current=self.store.get_profile(self.editing_profile) if self.editing_profile else None
        fields=current or {}
        head=ctk.CTkFrame(frame,fg_color="transparent")
        head.pack(fill="x",padx=25,pady=(19,6))
        self._label(head,self.t("edit_profile") if current else self.t("new_profile"),
                    20,True).pack(side="left")
        self._button(head,self.t("cancel"),
                     lambda:self._edit_profile(self.active_id) if self.active_id
                     else self._new_profile(),width=100,height=34).pack(side="right")
        scroll=ctk.CTkScrollableFrame(frame,fg_color="transparent")
        scroll.pack(fill="both",expand=True,padx=14,pady=(4,10))
        scroll.grid_columnconfigure(0,weight=1)
        scroll.grid_columnconfigure(1,weight=1)
        self.profile_widgets={}
        self._label(scroll,self.t("profile_details"),15,True,color=TEAL).grid(
            row=0,column=0,columnspan=2,sticky="w",padx=9,pady=(4,9))
        layout=[("name",1,0,2,"first_name"),("birth_date",2,0,1,"birth_date"),
                ("phone",2,1,1,"phone"),("email",3,0,2,"email"),
                ("niss",5,0,1,"niss"),("health_unit",5,1,1,"health_unit"),
                ("address",6,0,2,"address"),("city",7,0,1,"city"),
                ("postal_code",7,1,1,"postal_code"),
                ("emergency_name",9,0,1,"emergency_name"),
                ("emergency_phone",9,1,1,"emergency_phone")]
        self._label(scroll,self.t("health"),15,True,color=TEAL).grid(
            row=4,column=0,columnspan=2,sticky="w",padx=9,pady=(15,7))
        self._label(scroll,self.t("contacts"),15,True,color=TEAL).grid(
            row=8,column=0,columnspan=2,sticky="w",padx=9,pady=(15,7))
        for key,r,col,span,text in layout:
            self.profile_widgets[key]=self._text_field(scroll,text,fields.get(key,""),
                                                         r,col,span)
        self.photo_draft=fields.get("photo_b64","")
        photo_box=ctk.CTkFrame(scroll,fg_color="transparent")
        photo_box.grid(row=10,column=0,columnspan=2,sticky="ew",padx=8,pady=12)
        self._label(photo_box,self.t("photo"),12,True).pack(anchor="w")
        self.photo_label=ctk.CTkLabel(photo_box,text=self.t("photo_none"),
                                     text_color=self.p["muted"])
        self.photo_label.pack(side="left",padx=(0,18))
        self._refresh_photo()
        self._button(photo_box,self.t("photo_select"),self._choose_photo,
                     width=175,height=34).pack(side="left")
        self.profile_caregiver=ctk.BooleanVar(value=bool(fields.get("caregiver",False)))
        ctk.CTkSwitch(scroll,text=self.t("caregiver_field"),
            variable=self.profile_caregiver,progress_color=TEAL,
            button_color=TEAL,fg_color=self.p["panel2"]).grid(
                row=11,column=0,columnspan=2,sticky="w",padx=10,pady=12)
        self._label(scroll,self.t("notes"),12,True,color=self.p["muted"]).grid(
            row=12,column=0,columnspan=2,sticky="w",padx=9)
        self.profile_notes=ctk.CTkTextbox(scroll,height=82,corner_radius=12,
               fg_color=self.p["field"],border_width=1,
               border_color=self.p["line"],text_color=self.p["text"])
        self.profile_notes.grid(row=13,column=0,columnspan=2,sticky="ew",padx=8,pady=(4,14))
        self.profile_notes.insert("1.0",fields.get("notes",""))
        footer=ctk.CTkFrame(frame,fg_color="transparent")
        footer.pack(fill="x",padx=22,pady=(0,18))
        self._button(footer,self.t("save"),self._save_profile,True,width=185,height=45).pack(side="right")

    def _refresh_photo(self):
        try:
            if self.photo_draft:
                image=Image.open(BytesIO(base64.b64decode(self.photo_draft))).convert("RGB")
                self.photo_preview=ctk.CTkImage(image,image,size=(64,64))
                self.photo_label.configure(image=self.photo_preview,text="")
            else:
                self.photo_label.configure(image=None,text=self.t("photo_none"))
        except Exception:
            self.photo_label.configure(image=None,text=self.t("photo_none"))

    def _choose_photo(self):
        path=filedialog.askopenfilename(parent=self,filetypes=[
            ("Imagens","*.jpg *.jpeg *.png *.webp"),("Todos os ficheiros","*.*")])
        if not path:return
        try:
            with Image.open(path) as image:
                image=ImageOps.exif_transpose(image).convert("RGB")
                image.thumbnail((500,500),Image.Resampling.LANCZOS)
                out=BytesIO()
                image.save(out,format="JPEG",quality=80,optimize=True)
                if out.tell()>450000:raise ValueError("Fotografia demasiado grande.")
                self.photo_draft=base64.b64encode(out.getvalue()).decode("ascii")
                self._refresh_photo()
        except Exception as exc:messagebox.showerror("SaúdePrática",
                self.t("image_error")+"\n"+str(exc),parent=self)

    def _save_profile(self):
        fields={key:entry.get() for key,entry in self.profile_widgets.items()}
        fields["caregiver"]=self.profile_caregiver.get()
        fields["notes"]=self.profile_notes.get("1.0","end-1c")
        fields["photo_b64"]=self.photo_draft
        try:
            saved=self.store.save_profile(fields,self.editing_profile)
            self.active_id=saved["id"]
            self.editing_profile=saved["id"]
            self.store.update_settings(active_profile=self.active_id)
            self._render()
        except (LocalStoreError,ValueError) as exc:
            messagebox.showerror(self.t("profile_save_error"),str(exc),parent=self)

    def _medication(self):
        self._heading(self.t("medication"),self.t("not_alarm"))
        if not self.active_id:
            self._pending("medication")
            return
        current=self.store.get_profile(self.active_id)
        if not current:
            self._pending("medication")
            return
        left,listing,right=self._two_pane(self.t("medication_list"),315)
        self._button(listing,"+ "+self.t("new_medication"),self._new_med,
                     True,width=255).pack(fill="x",pady=(0,11))
        for m in current.get("medications",[]):
            row=ctk.CTkFrame(listing,fg_color=self.p["panel2"],corner_radius=15)
            row.pack(fill="x",pady=5)
            self._label(row,m.get("name",""),14,True).pack(anchor="w",padx=13,pady=(9,2))
            self._label(row,(m.get("dose","")+" · "+m.get("time","")).strip(),
                        11,color=self.p["muted"]).pack(anchor="w",padx=13)
            self._button(row,self.t("open"),lambda mid=m["id"]:self._edit_med(mid),
                         width=105,height=31).pack(anchor="e",padx=9,pady=(5,10))
        med=next((m for m in current.get("medications",[])
                  if m.get("id")==self.editing_med),None)
        self._med_form(right,med)

    def _new_med(self):
        self.editing_med=None
        self._render()

    def _edit_med(self,mid):
        self.editing_med=mid
        self._render()

    def _med_form(self,frame,med):
        fields=med or {}
        head=ctk.CTkFrame(frame,fg_color="transparent")
        head.pack(fill="x",padx=22,pady=(18,7))
        self._label(head,self.t("edit_medication") if med else self.t("new_medication"),
                    21,True).pack(side="left")
        body=ctk.CTkScrollableFrame(frame,fg_color="transparent")
        body.pack(fill="both",expand=True,padx=15,pady=5)
        body.grid_columnconfigure(0,weight=1)
        body.grid_columnconfigure(1,weight=1)
        self.med_widgets={}
        for k,label,row,col,span in [
            ("name","med_name",0,0,2),("dose","dose",1,0,1),
            ("time","time",1,1,1),("indication","indication",4,0,2)
        ]:
            self.med_widgets[k]=self._text_field(body,label,fields.get(k,""),row,col,span)
        route_name=next((key for key,val in ROUTES.items()
                         if val==fields.get("administration_route","")),"Não indicada")
        injection_name=next((key for key,val in INJECTIONS.items()
                             if val==fields.get("injection_type","")),"Não indicada")
        self.route_var=ctk.StringVar(value=route_name)
        self.injection_var=ctk.StringVar(value=injection_name)
        self.take_var=ctk.StringVar(value=fields.get("dose_pattern",""))
        for title,var,choices,row,col in [
            ("route",self.route_var,ROUTES,2,0),
            ("injection",self.injection_var,INJECTIONS,2,1),
            ("dose_pattern",self.take_var,TAKES,3,0)
        ]:
            box=ctk.CTkFrame(body,fg_color="transparent")
            box.grid(row=row,column=col,sticky="ew",padx=7,pady=7)
            self._label(box,self.t(title),12,True,color=self.p["muted"]).pack(anchor="w",pady=(0,6))
            ctk.CTkOptionMenu(box,values=list(choices),variable=var,width=180,
                height=40,fg_color=self.p["field"],button_color=BLUE,
                dropdown_fg_color=self.p["panel2"],text_color=self.p["text"]).pack(fill="x")
        self.no_alarm_var=ctk.BooleanVar(value=fields.get("no_alarm",False))
        self.suspended_var=ctk.BooleanVar(value=fields.get("suspended",False))
        toggles=ctk.CTkFrame(body,fg_color="transparent")
        toggles.grid(row=5,column=0,columnspan=2,sticky="w",padx=8,pady=(16,10))
        for k,var in [("no_alarm",self.no_alarm_var),("suspended",self.suspended_var)]:
            ctk.CTkSwitch(toggles,text=self.t(k),variable=var,
                progress_color=TEAL,button_color=TEAL,
                fg_color=self.p["panel2"]).pack(side="left",padx=(0,25))
        self._label(body,self.t("notes"),12,True,color=self.p["muted"]).grid(
            row=6,column=0,columnspan=2,sticky="w",padx=8)
        self.med_notes=ctk.CTkTextbox(body,height=83,corner_radius=12,
            fg_color=self.p["field"],border_width=1,border_color=self.p["line"])
        self.med_notes.grid(row=7,column=0,columnspan=2,sticky="ew",padx=8,pady=(5,16))
        self.med_notes.insert("1.0",fields.get("notes",""))
        # Groups visible but explicitly marked as not implemented. Never fake persistence.
        for i,key in enumerate(("prescription","repetitions","leaflet","photos","more_info")):
            p=ctk.CTkFrame(body,fg_color=self.p["panel2"],corner_radius=12)
            p.grid(row=8+i,column=0,columnspan=2,sticky="ew",padx=8,pady=4)
            self._label(p,self.t(key)+"  ·  "+self.t("coming"),12,
                        color=self.p["muted"]).pack(anchor="w",padx=15,pady=12)
        footer=ctk.CTkFrame(frame,fg_color="transparent")
        footer.pack(fill="x",padx=22,pady=15)
        self._button(footer,self.t("save"),self._save_med,True,width=165).pack(side="right")

    def _save_med(self):
        fields={key:entry.get() for key,entry in self.med_widgets.items()}
        fields.update({
            "administration_route":ROUTES[self.route_var.get()],
            "injection_type":INJECTIONS[self.injection_var.get()],
            "dose_pattern":self.take_var.get(),
            "no_alarm":self.no_alarm_var.get() or self.take_var.get()=="SOS",
            "suspended":self.suspended_var.get(),
            "notes":self.med_notes.get("1.0","end-1c"),
        })
        try:
            m=self.store.save_medication(self.active_id,fields,self.editing_med)
            self.editing_med=m["id"]
            self._render()
        except (LocalStoreError,ValueError,KeyError) as exc:
            messagebox.showerror(self.t("med_save_error"),str(exc),parent=self)

    def _settings_page(self):
        self._heading(self.t("preferences"),self.t("preferences_desc"))
        card=self._card(self.body)
        card.pack(fill="x",pady=8)
        inner=ctk.CTkFrame(card,fg_color="transparent")
        inner.pack(anchor="w",fill="x",padx=27,pady=24)
        self._label(inner,self.t("theme"),16,True).grid(row=0,column=0,sticky="w",pady=11)
        self._label(inner,self.t("language"),16,True).grid(row=1,column=0,sticky="w",pady=11)
        values={self.t(k):v for v,k in THEME_KEYS.items()}
        self.theme_values=values
        menu=ctk.CTkOptionMenu(inner,values=list(values),width=230,
             fg_color=self.p["panel2"],button_color=BLUE,
             dropdown_fg_color=self.p["panel"],command=self._change_theme)
        menu.set(next((title for title,v in values.items() if v==self.theme),next(iter(values))))
        menu.grid(row=0,column=1,padx=30,pady=10)
        lang_menu=ctk.CTkOptionMenu(inner,values=list(LANG_NAMES.values()),
            width=230,fg_color=self.p["panel2"],button_color=BLUE,
            dropdown_fg_color=self.p["panel"],command=self._change_language)
        lang_menu.set(LANG_NAMES[self.lang])
        lang_menu.grid(row=1,column=1,padx=30,pady=10)
        self._label(card,self.t("notice"),12,color=self.p["muted"],wrap=820).pack(
            anchor="w",padx=28,pady=(0,22))

    def _change_theme(self,title):
        theme=self.theme_values[title]
        try:self.store.update_settings(theme=theme)
        except LocalStoreError as exc:
            messagebox.showerror("SaúdePrática",str(exc),parent=self);return
        self.theme=theme
        ctk.set_appearance_mode(theme)
        self._render()

    def _change_language(self,title):
        locale=next((code for code,name in LANG_NAMES.items() if name==title),"pt")
        try:self.store.update_settings(language=locale)
        except LocalStoreError as exc:
            messagebox.showerror("SaúdePrática",str(exc),parent=self);return
        self.lang=locale
        self._render()

    def _backup(self):
        self._heading(self.t("backup_title"),self.t("backup_desc"))
        card=self._card(self.body)
        card.pack(fill="x",pady=10)
        wrapper=ctk.CTkFrame(card,fg_color="transparent")
        wrapper.pack(fill="x",padx=30,pady=25)
        self._label(wrapper,self.t("password"),13,True).pack(anchor="w")
        self.backup_pass=ctk.CTkEntry(wrapper,show="●",height=43,width=320,
            fg_color=self.p["field"],border_color=self.p["line"])
        self.backup_pass.pack(anchor="w",pady=(6,15))
        self._label(wrapper,self.t("confirm_password"),13,True).pack(anchor="w")
        self.backup_confirm=ctk.CTkEntry(wrapper,show="●",height=43,width=320,
            fg_color=self.p["field"],border_color=self.p["line"])
        self.backup_confirm.pack(anchor="w",pady=(6,20))
        actions=ctk.CTkFrame(wrapper,fg_color="transparent")
        actions.pack(anchor="w")
        self._button(actions,self.t("export"),self._export_backup,True,200).pack(side="left",padx=(0,10))
        self._button(actions,self.t("restore"),self._restore_backup,width=200).pack(side="left")

    def _export_backup(self):
        password=self.backup_pass.get()
        if password!=self.backup_confirm.get():
            messagebox.showerror("Backup","A confirmação da palavra-passe não coincide.",parent=self);return
        path=filedialog.asksaveasfilename(parent=self,defaultextension=".spbackup",
              initialfile="SaudePratica_"+datetime.now().strftime("%Y%m%d")+".spbackup",
              filetypes=[("SaúdePrática Backup","*.spbackup")])
        if not path:return
        try:
            content=self.store.export_backup(password)
            Path(path).write_bytes(content)
            messagebox.showinfo("Backup",self.t("backup_success"),parent=self)
        except Exception as exc:messagebox.showerror("Backup",str(exc),parent=self)

    def _restore_backup(self):
        path=filedialog.askopenfilename(parent=self,filetypes=[("SaúdePrática Backup","*.spbackup")])
        if not path:return
        try:
            people,files=self.store.inspect_backup(Path(path).read_bytes(),self.backup_pass.get())
            names=", ".join(p["name"] for p in people)
            if not messagebox.askyesno(self.t("restore"),self.t("confirm_restore")+"\n"+names,parent=self):
                return
            count=self.store.restore_backup(files)
            messagebox.showinfo(self.t("restore"),self.t("restore_success")+f" ({count})",parent=self)
            self._render()
        except Exception as exc:
            messagebox.showerror(self.t("restore"),str(exc),parent=self)


def _close_boot_splash():
    try:
        import pyi_splash
        pyi_splash.close()
    except Exception:
        pass


def main():
    """Never hide startup failures behind the persistent splash.

    CI tests both unbundled source and the actual packaged EXE through a
    synthetic, short-lived GUI launch; health details are never uploaded.
    """
    import traceback
    app = None
    smoke_report = os.environ.get("SAUDEPRATICA_SMOKE_REPORT", "")
    try:
        app = Desktop()
        # Process and render the initial UI before marking the startup as good.
        app.update_idletasks()
        app.update()
        _close_boot_splash()
        if smoke_report:
            Path(smoke_report).write_text("GUI_READY\n", encoding="utf-8")
            app.destroy()
            return
        app.mainloop()
    except Exception:
        failure = traceback.format_exc()
        _close_boot_splash()
        if smoke_report:
            Path(smoke_report).write_text("GUI_ERROR\n" + failure, encoding="utf-8")
            if app:
                try: app.destroy()
                except Exception: pass
            raise
        # Keep diagnostics private on this Windows account; no personal or
        # clinical data are included in the exception report.
        try:
            root = Path(os.getenv("LOCALAPPDATA", str(Path.home())))
            log = root / "SaudePraticaDesktop" / "startup_error.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(failure, encoding="utf-8")
            message = ("A SaúdePrática não conseguiu iniciar.\n"
                       "A janela de abertura foi fechada.\n"
                       "Podes enviar apenas o ficheiro de diagnóstico:\n\n"
                       + str(log))
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message,
                "SaúdePrática — erro de arranque", 0x10)
        except Exception:
            pass
        if app:
            try: app.destroy()
            except Exception: pass
        raise


if __name__=="__main__":
    main()
