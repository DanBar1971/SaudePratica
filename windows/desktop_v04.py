"""SaúdePrática Desktop 0.4 — modern adaptive Windows client.

Phase 1: full profile editing, active profile selection, medication,
appearance/language, original brand assets and legacy DPAPI/backup compatibility.
Agenda, attachments, live Android syncing and alarms are explicitly not built.
"""
from __future__ import annotations

import base64
import json
from io import BytesIO
import os
from datetime import datetime
from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFilter

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT))
from windows.secure_store import SecureStore, LocalStoreError
from shared.python.saude_backup import BackupError
from windows.ui_v04_i18n import translate
from windows.ui_catalog_v05 import MODULE_CARDS, normalized, filter_cards
from windows.dashboard_v06 import Dashboard
from windows.wallpaper_shell_v06 import WallpaperShell
from windows.visual_v07 import circular_photo, wallpaper_image
from windows.android_import_v062 import plan_json, apply_plan, AndroidImportError
from windows.android_archive_v063 import archive_sources,prepare_archive,apply_archive
from windows.family_ui_v064 import family_controls, export_original_zip
from windows.profile_fields_v066 import missing_profile_fields
from windows.medication_schedule_v066 import next_medication_label
from windows.medication_gallery_v068 import medication_filter_matches, medication_status
from windows.agenda_filter_v069 import FILTERS as AGENDA_FILTERS, appointment_status, appointment_datetime, filtered_appointments
from windows.appointment_editor_v070 import MAIN_FIELDS as APPOINTMENT_FIELDS, STATUS_OPTIONS as APPOINTMENT_STATES, extra_fields as appointment_extras, parse_extra as parse_appointment_extra

ctk.set_default_color_theme("blue")
VERSION = "0.7.0"
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
        self.geometry("1370x790")
        self.minsize(1050, 650)
        self.active_id = pref.get("active_profile")
        if not self.store.get_profile(self.active_id):
            self.active_id = self.store.profiles()[0]["id"] if self.store.profiles() else None
        self.editing_profile = self.active_id
        self.editing_med = None
        self.page = "home"
        self.profile_widgets = {}
        self.med_widgets = {}
        self.photo_draft = ""
        self.med_photo_draft = ""
        self.med_gallery_query = ""
        self.catalog_query = ""
        self.med_gallery_state = "all"
        self.agenda_filter = "all"
        self.agenda_mode = "catalog"
        self.editing_appointment = None
        self.appointment_widgets = {}
        self.appointment_extra_widgets = {}
        self.gallery_mode = "catalog"
        self.profile_menu = None
        self.profile_avatar = None
        self.android_import_plan = None
        self.android_zip_inspection = None
        self.android_zip_sources = ()
        self.android_zip_blob = None
        self.android_zip_plan = None
        self.android_zip_selected = ""
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
        self.logo = ctk.CTkImage(self._original_icon, self._original_icon, size=(40,40))
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
        # Every widget consumes explicit theme colours. No white default
        # foregrounds are allowed in the light appearance mode.
        if ctk.get_appearance_mode().lower()=="light":
            return dict(bg="#edf4f7",panel="#ffffff",panel2="#e2edf1",
                        text="#172b36",muted="#52616e",line="#c4d7df",
                        field="#f8fbfd",banner="#062630",
                        hover="#c5e3e6",thumb="#d9e8ed",
                        chip="#d3eee9",chip_text="#124a49")
        return dict(bg="#07151e",panel="#16232e",panel2="#203240",
                    text="#f1f7fa",muted="#b6c4cd",line="#334554",
                    field="#101d27",banner="#062630",
                    hover="#285163",thumb="#263c4a",
                    chip="#1c5659",chip_text="#a8fff0")

    def _button(self,parent,label,command,accent=False,width=124,height=32):
        p=self.p
        return ctk.CTkButton(parent,text=label,command=command,width=width,height=height,
            corner_radius=10,font=ctk.CTkFont(family="Segoe UI",size=12,weight="bold"),
            fg_color=TEAL if accent else p["panel2"],
            hover_color=TEAL_HOVER if accent else p["hover"],
            text_color="#05252c" if accent else p["text"])

    def _label(self,parent,text,size=13,bold=False,color=None,anchor="w",wrap=None):
        return ctk.CTkLabel(parent,text=text,anchor=anchor,
            text_color=color or self.p["text"],
            font=ctk.CTkFont(family="Segoe UI",size=size,
                             weight="bold" if bold else "normal"),
            wraplength=wrap or 0)

    def _card(self,parent,rounding=14,**kw):
        return ctk.CTkFrame(parent,fg_color=self.p["panel"],
            corner_radius=rounding,border_width=1,
            border_color=self.p["line"],**kw)

    def _chip(self,parent,text,color=None):
        return ctk.CTkLabel(parent,text="  "+text+"  ",
            font=ctk.CTkFont(size=10,weight="bold"),
            text_color=color or self.p["chip_text"],
            fg_color=self.p["chip"],corner_radius=8,height=23)

    def _clear(self):
        for child in self.winfo_children():
            child.destroy()

    def _render(self):
        self.p=self._palette()
        self.configure(fg_color=self.p["bg"])
        self._clear()
        header=ctk.CTkFrame(self,height=65,
                            fg_color="#0b2330" if self.p["bg"]!="#edf4f7" else "#ffffff",
                            corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        brand=ctk.CTkFrame(header,fg_color="transparent")
        brand.pack(side="left",padx=(24,16),fill="y")
        ctk.CTkLabel(brand,image=self.logo,text="").pack(side="left",padx=(0,8),pady=5)
        self._label(brand,"SaúdePrática",17,True,color=TEAL).pack(side="left",pady=13)
        nav=ctk.CTkFrame(header,fg_color="transparent")
        nav.pack(side="left",padx=(8,8),fill="y")
        for key,glyph,title in TABS:
            target=key
            active=self.page==target or (target=="more" and self.page not in ("home","profiles","medication","agenda"))
            label=glyph+"  "+self.t(title)
            b=self._button(nav,label,lambda k=key:self.navigate(k),accent=active,width=96,height=34)
            b.pack(side="left",padx=3,pady=15)

        right=ctk.CTkFrame(header,fg_color="transparent")
        right.pack(side="right",padx=(5,18),pady=11)
        entries=self.store.profiles()
        current=self.store.get_profile(self.active_id)
        label=current.get("name","") if current else self.t("active_none")
        photo=circular_photo(current.get("photo_b64",""),36) if current else None
        self.profile_avatar=ctk.CTkImage(photo,photo,size=(36,36)) if photo else None
        # Separate avatar and label; centring both inside a wide CTkButton
        # previously left an unsightly gap before the photograph.
        self.profile_pill=ctk.CTkFrame(
            right,fg_color=self.p["panel2"],corner_radius=13,
            border_color="#177b87",border_width=1,height=41,
            width=max(165,min(300,len(label)*9+110)))
        self.profile_pill.pack(side="right")
        self.profile_pill.pack_propagate(False)
        avatar_label=ctk.CTkLabel(
            self.profile_pill,image=self.profile_avatar,
            text="" if self.profile_avatar else "👤",width=36,height=36)
        avatar_label.pack(side="left",padx=(5,4),pady=2)
        avatar_label.bind("<Button-1>",lambda _event:self._toggle_profile_menu())
        self.profile_select=ctk.CTkButton(
            self.profile_pill,text=label+"  ⌄",
            command=self._toggle_profile_menu,
            anchor="w",width=max(105,min(225,len(label)*9+35)),
            height=36,corner_radius=9,
            fg_color="transparent",hover_color=self.p["hover"],
            font=ctk.CTkFont(size=12,weight="bold"),text_color=self.p["text"])
        self.profile_select.pack(side="left",padx=(0,5),pady=2)

        catalog=self.page in ("home","more")
        if catalog:
            body=ctk.CTkFrame(self,fg_color="transparent")
            body.pack(fill="both",expand=True)
            self.body=body
        else:
            shell=WallpaperShell(self,light=self.p["bg"]=="#edf4f7")
            self.body=shell.content
            self.wallpaper_shell=shell
        if self.page=="home": self._home()
        elif self.page=="profiles": self._profiles()
        elif self.page=="medication": self._medication()
        elif self.page=="backup": self._backup()
        elif self.page=="import": self._android_import_page()
        elif self.page=="agenda": self._agenda()
        elif self.page=="documents": self._documents()
        elif self.page=="options": self._settings_page()
        elif self.page=="more": self._modules(full=True)
        else: self._pending(self.page)

        footer=ctk.CTkFrame(self,height=28,fg_color=self.p["panel"],corner_radius=0)
        footer.pack(fill="x",side="bottom")
        self._label(footer,f"Windows {VERSION} · experimental",10,color=self.p["muted"]).pack(side="left",padx=18,pady=5)
        self._label(footer,self.t("not_alarm"),10,color=self.p["muted"]).pack(side="right",padx=18,pady=5)
        self.profile_menu=None

    def _heading(self,title,subtitle=None):
        # One clean typography-only header, never another opaque box.
        head=ctk.CTkFrame(self.body,fg_color="transparent",corner_radius=0)
        head.pack(fill="x",pady=(7,13))
        rule=ctk.CTkFrame(head,fg_color=TEAL,width=3,height=42,corner_radius=2)
        rule.pack(side="left",fill="y",padx=(4,15),pady=1)
        texts=ctk.CTkFrame(head,fg_color="transparent")
        texts.pack(side="left",fill="x",expand=True)
        self._label(texts,title,26,True).pack(anchor="w")
        if subtitle:
            self._label(texts,subtitle,11,color=self.p["muted"]).pack(anchor="w",pady=(1,0))

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
        self.dashboard=Dashboard(self.body,self,full=False)

    def _modules(self,compact=False,full=False):
        self.dashboard=Dashboard(self.body,self,full=True)

    def _toggle_profile_menu(self):
        if self.profile_menu is not None:
            self.profile_menu.destroy()
            self.profile_menu=None
            return
        menu=ctk.CTkFrame(self,fg_color=self.p["panel"],
                          corner_radius=14,border_color="#267684",
                          border_width=1,width=280)
        menu.place(relx=1,x=-17,y=67,anchor="ne")
        self.profile_menu=menu
        for person in self.store.profiles():
            row=ctk.CTkFrame(menu,fg_color="transparent")
            row.pack(fill="x",padx=6,pady=3)
            avatar=circular_photo(person.get("photo_b64",""),42)
            photo=ctk.CTkImage(avatar,avatar,size=(42,42)) if avatar else None
            active=person["id"]==self.active_id
            mark="  ✓" if active else ""
            name=person["name"]+mark
            if person.get("caregiver"):
                name+="  🙌"
            button=ctk.CTkButton(
                row,text=name,image=photo,compound="left",
                fg_color=self.p["panel2"] if active else "transparent",
                hover_color=self.p["hover"],text_color=self.p["text"],
                anchor="w",height=56,corner_radius=10,
                font=ctk.CTkFont(size=13,weight="bold"),
                command=lambda pid=person["id"]:self._select_profile_by_id(pid))
            button.pack(fill="x")
        self._button(menu,"⚙  "+self.t("profiles"),
                    lambda:self._profile_menu_to_profiles(),
                    width=255,height=34).pack(fill="x",padx=8,pady=(5,9))
        menu.lift()

    def _select_profile_by_id(self,pid):
        if self.profile_menu is not None:
            self.profile_menu.destroy()
            self.profile_menu=None
        if pid==self.active_id:return
        self.active_id=pid
        self.editing_profile=pid
        self.editing_med=None
        try:self.store.update_settings(active_profile=pid)
        except LocalStoreError as exc:
            messagebox.showerror("SaúdePrática",str(exc),parent=self)
        self._render()

    def _profile_menu_to_profiles(self):
        if self.profile_menu is not None:
            self.profile_menu.destroy()
            self.profile_menu=None
        self.navigate("profiles")

    def _pending(self,key):
        self._heading(self.t(key),self.t("module_pending"))
        self._label(self.body,self.t("coming"),20,True,color=TEAL).pack(anchor="w",pady=(15,4))
        self._label(self.body,self.t("soon_detail"),13,color=self.p["muted"]).pack(anchor="w")

    def _two_pane(self,left_title,left_width=330):
        container=ctk.CTkFrame(self.body,fg_color="transparent")
        container.pack(fill="both",expand=True)
        left=ctk.CTkFrame(container,width=left_width,fg_color="transparent",
                          corner_radius=0)
        left.pack(side="left",fill="y",padx=(0,10))
        left.pack_propagate(False)
        self._label(left,left_title,16,True).pack(anchor="w",padx=13,pady=(11,6))
        left_scroll=ctk.CTkScrollableFrame(left,fg_color="transparent")
        left_scroll.pack(fill="both",expand=True,padx=8,pady=(2,8))
        right=ctk.CTkFrame(container,fg_color="transparent",
                           corner_radius=0)
        right.pack(side="left",fill="both",expand=True)
        return left,left_scroll,right

    def _authentic_thumb(self,b64,width=92,height=92):
        """Use only the actual photo saved with the record; never fake packaging."""
        if not b64:return None
        try:
            raw=base64.b64decode(b64,validate=True)
            if len(raw)>450000:return None
            with Image.open(BytesIO(raw)) as original:
                if original.width*original.height>20_000_000:return None
                image=ImageOps.contain(original.convert("RGB"),(width,height),
                                       method=Image.Resampling.LANCZOS)
            return ctk.CTkImage(image,image,size=(image.width,image.height))
        except Exception:
            return None

    def _med_card_photo(self,b64,width,height):
        """Fill the photo frame using ONLY the stored authentic photograph.

        A blurred crop fills the full frame; the uncropped medicine photo is
        centred over it so names/dosages are not lost on portrait images.
        """
        if not b64:return None
        try:
            raw=base64.b64decode(b64,validate=True)
            if len(raw)>600000:return None
            with Image.open(BytesIO(raw)) as original:
                if original.width*original.height>20_000_000:return None
                clean=ImageOps.exif_transpose(original).convert("RGB")
                back=ImageOps.fit(clean,(width,height),
                    method=Image.Resampling.LANCZOS)
                back=back.filter(ImageFilter.GaussianBlur(radius=13))
                front=ImageOps.contain(clean,(width,height),
                    method=Image.Resampling.LANCZOS)
                back.paste(front,((width-front.width)//2,(height-front.height)//2))
            return ctk.CTkImage(back,back,size=(width,height))
        except (ValueError,OSError,TypeError):
            return None

    def _profiles(self):
        self._heading(self.t("profiles"),self.t("profile_hint"))
        left,listing,right=self._two_pane(self.t("registered_profiles"),290)
        self._button(listing,"+ "+self.t("new_profile"),
                     self._new_profile,True,width=225,height=32).pack(
                         fill="x",pady=(0,8))
        for profile in self.store.profiles():
            row=ctk.CTkFrame(listing,fg_color=self.p["panel2"],corner_radius=11)
            row.pack(fill="x",pady=4)
            raw_avatar=circular_photo(profile.get("photo_b64",""),49)
            pic=ctk.CTkImage(raw_avatar,raw_avatar,size=(49,49)) if raw_avatar else None
            if pic:
                photo=ctk.CTkLabel(row,image=pic,text="",width=50,height=53)
            else:
                photo=ctk.CTkLabel(row,text="👤",width=50,height=53,
                    font=ctk.CTkFont(family="Segoe UI Emoji",size=25))
            photo.pack(side="left",padx=(8,4),pady=6)
            content=ctk.CTkFrame(row,fg_color="transparent")
            content.pack(side="left",fill="both",expand=True,padx=3)
            self._label(content,profile.get("name",""),13,True).pack(anchor="w",pady=(6,0))
            status=("🙌  "+self.t("caregiver_field") if profile.get("caregiver") else
                    ("● "+self.t("active_profile") if profile["id"]==self.active_id else ""))
            if status:self._label(content,status,10,color=self.p["muted"]).pack(anchor="w")
            self._button(row,"🗑",lambda pid=profile["id"]:self._delete_profile(pid),
                         width=34,height=30).pack(side="right",padx=(0,6))
            self._button(row,"›",lambda pid=profile["id"]:self._edit_profile(pid),
                         width=29,height=30).pack(side="right",padx=(0,3))
        self._profile_form(right)

    def _delete_profile(self,pid):
        person=self.store.get_profile(pid)
        if person is None:return
        meds=len(person.get("medications",[]))
        agenda=len(person.get("appointments",[]))
        docs=len(self.store.imported_assets(pid))
        if not messagebox.askyesno("Eliminar perfil",
            f"Eliminar DEFINITIVAMENTE o perfil {person.get('name','')}?\\n\\n"
            f"Serão retirados {meds} medicamentos, {agenda} marcações e "
            f"{docs} anexos associados a este perfil Windows.\\n\\n"
            "Os backups exportados e o ZIP familiar Android original "
            "permanecem guardados. Recomenda-se criar um backup "
            "encriptado antes de eliminar.\\n\\nContinuar?",
            parent=self):
            return
        try:
            result=self.store.delete_profile(pid)
            self.active_id=result["next_active"] or (
                self.store.profiles()[0]["id"] if self.store.profiles() else None)
            if self.editing_profile==pid:self.editing_profile=self.active_id
            self.gallery_mode="catalog"
            self.editing_med=None
            self._render()
        except (LocalStoreError,OSError,ValueError) as exc:
            messagebox.showerror("Eliminar perfil",str(exc),parent=self)

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
        box.grid(row=row,column=col,columnspan=columns,sticky="ew",padx=5,pady=4)
        self._label(box,self.t(label),11,True,color=self.p["muted"]).pack(anchor="w",pady=(0,3))
        entry=ctk.CTkEntry(box,height=33,corner_radius=8,
            border_color=self.p["line"],fg_color=self.p["field"],
            text_color=self.p["text"],font=ctk.CTkFont(size=12))
        entry.insert(0,str(initial or ""))
        entry.pack(fill="x")
        return entry

    def _profile_form(self,frame):
        current=self.store.get_profile(self.editing_profile) if self.editing_profile else None
        fields=dict(current or {})
        self.profile_extra_rows=()
        if current:
            # Old imports may have retained fields only in the original Android
            # ZIP. Retrieve them privately via DPAPI, never display mock data.
            fields.update(missing_profile_fields(
                fields,fields.get("android_profile_original",{})))
            try:
                recovered,extra=self.store.profile_android_extras(current["id"])
                fields.update({k:v for k,v in recovered.items() if not fields.get(k)})
                self.profile_extra_rows=extra
            except (LocalStoreError,OSError,ValueError):
                pass
        head=ctk.CTkFrame(frame,fg_color="transparent")
        head.pack(fill="x",padx=16,pady=(9,4))
        self._label(head,self.t("edit_profile") if current else self.t("new_profile"),
                    17,True).pack(side="left")
        self._button(head,self.t("cancel"),
                     lambda:self._edit_profile(self.active_id) if self.active_id
                     else self._new_profile(),width=100,height=34).pack(side="right")
        scroll=ctk.CTkScrollableFrame(frame,fg_color="transparent")
        scroll.pack(fill="both",expand=True,padx=9,pady=(2,6))
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
            button_color=TEAL,fg_color=self.p["panel2"],text_color=self.p["text"]).grid(
                row=11,column=0,columnspan=2,sticky="w",padx=10,pady=12)
        self._label(scroll,self.t("notes"),12,True,color=self.p["muted"]).grid(
            row=12,column=0,columnspan=2,sticky="w",padx=9)
        self.profile_notes=ctk.CTkTextbox(scroll,height=82,corner_radius=12,
               fg_color=self.p["field"],border_width=1,
               border_color=self.p["line"],text_color=self.p["text"])
        self.profile_notes.grid(row=13,column=0,columnspan=2,sticky="ew",padx=8,pady=(4,14))
        self.profile_notes.insert("1.0",fields.get("notes",""))
        next_row=14
        if current:
            # Identification documents are individually protected under DPAPI.
            # Render authentic images only, never a generic/fabricated CC.
            ids=[entry for entry in self.store.imported_assets(current["id"])
                 if entry.get("category")=="identificação"]
            if ids:
                self._label(scroll,"Documentos de identificação do Android",15,
                    True,color=TEAL).grid(row=next_row,column=0,columnspan=2,
                                          sticky="w",padx=9,pady=(15,7))
                next_row+=1
                id_panel=ctk.CTkFrame(scroll,fg_color="transparent")
                id_panel.grid(row=next_row,column=0,columnspan=2,
                              sticky="ew",padx=8,pady=5)
                next_row+=1
                for entry in ids[:30]:
                    line=ctk.CTkFrame(id_panel,fg_color=self.p["panel2"],
                                      corner_radius=8)
                    line.pack(fill="x",pady=3)
                    filename=str(entry.get("filename",""))
                    if Path(filename).suffix.lower() in (".jpg",".jpeg",".png",".webp"):
                        try:
                            raw=self.store.read_imported_asset(entry)
                            if len(raw)<16_000_000:
                                with Image.open(BytesIO(raw)) as original:
                                    if original.width*original.height<=20_000_000:
                                        image=ImageOps.contain(original.convert("RGB"),
                                            (155,100),method=Image.Resampling.LANCZOS)
                                        photo=ctk.CTkImage(image,image,
                                            size=(image.width,image.height))
                                        ctk.CTkLabel(line,image=photo,text="",
                                            width=160).pack(side="left",padx=6,pady=5)
                        except (OSError,ValueError,LocalStoreError):
                            pass
                    self._label(line,str(entry.get("display_name") or filename),
                                12,True).pack(side="left",padx=8)
                    self._button(line,"Exportar",lambda item=entry:self._export_document(item),
                                 width=110).pack(side="right",padx=9,pady=6)
            if self.profile_extra_rows:
                self._label(scroll,"Informação adicional recuperada do Android",
                    15,True,color=TEAL).grid(row=next_row,column=0,columnspan=2,
                                              sticky="w",padx=9,pady=(17,7))
                next_row+=1
                helptext=("Dados de leitura recuperados do backup Android. "
                    "Podem incluir campos que ainda não têm editor Windows. "
                    "Estes valores não são alterados ao guardar a ficha.")
                self._label(scroll,helptext,11,color=self.p["muted"],
                    wrap=900).grid(row=next_row,column=0,columnspan=2,
                                   sticky="w",padx=9,pady=(0,8))
                next_row+=1
                for name,value in self.profile_extra_rows[:250]:
                    line=ctk.CTkFrame(scroll,fg_color=self.p["field"],
                                     corner_radius=5)
                    line.grid(row=next_row,column=0,columnspan=2,
                              sticky="ew",padx=8,pady=2)
                    self._label(line,str(name),11,True,
                                color=self.p["muted"],wrap=400).pack(
                                    side="left",padx=9,pady=4)
                    self._label(line,str(value),11,wrap=600).pack(
                        side="right",padx=9,pady=4)
                    next_row+=1
        footer=ctk.CTkFrame(frame,fg_color="transparent")
        footer.pack(fill="x",padx=16,pady=(0,9))
        self._button(footer,self.t("save"),self._save_profile,True,width=137,height=33).pack(side="right")

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
        self._heading(self.t("medication"),
                      "Catálogo de medicação · " + self.t("not_alarm"))
        if not self.active_id or not self.store.get_profile(self.active_id):
            self._label(self.body,self.t("invalid_profile"),15).pack(anchor="w")
            self._button(self.body,self.t("profiles"),
                         lambda:self.navigate("profiles"),True).pack(anchor="w",pady=10)
            return
        if self.gallery_mode == "editor":
            frame=ctk.CTkFrame(self.body,fg_color="transparent",
                               corner_radius=0)
            frame.pack(fill="both",expand=True)
            meds=self.store.get_profile(self.active_id).get("medications",[])
            med=next((m for m in meds if m.get("id")==self.editing_med),None)
            self._med_form(frame,med)
            return
        bar=ctk.CTkFrame(self.body,fg_color="transparent",height=35)
        bar.pack(fill="x",pady=(0,6))
        self._label(bar,self.t("medication_list"),15,True).pack(side="left",padx=(1,15))
        self._button(bar,"+ "+self.t("new_medication"),self._new_med,
                     True,width=160,height=32).pack(side="right",padx=(8,0))
        # Keep the background inside every medicine card, not wallpaper glass.
        self.wallpaper_shell.glass_enabled=False
        query_var=ctk.StringVar(value=self.med_gallery_query)
        # No unlabelled/inert search rectangle over the wallpaper.
        search=None
        filters=ctk.CTkFrame(self.body,fg_color="transparent")
        filters.pack(fill="x",pady=(0,8))
        for key,label in (("all","Todos"),("active","Ativos"),("suspended","Suspensos"),
                          ("no_alarm","Sem alarme"),("undefined","Sem definição")):
            self._button(filters,label,lambda k=key:self._set_med_filter(k),
                accent=(self.med_gallery_state==key),width=116 if key=="undefined" else 100,height=29).pack(
                    side="left",padx=(0,5))
        listing=ctk.CTkScrollableFrame(self.body,fg_color="transparent",
            scrollbar_button_color=self.p["panel2"],corner_radius=0)
        listing.pack(fill="both",expand=True)
        self._med_gallery_grid=ctk.CTkFrame(listing,fg_color="transparent")
        self._med_gallery_grid.pack(fill="both",expand=True)
        def filter_query(*_):
            self.med_gallery_query=query_var.get()
            self._populate_med_gallery()
        query_var.trace_add("write",filter_query)
        self._populate_med_gallery()

    def _set_med_filter(self,key):
        self.med_gallery_state=key
        self._render()

    def _populate_med_gallery(self):
        grid=self._med_gallery_grid
        for child in grid.winfo_children():child.destroy()
        profile=self.store.get_profile(self.active_id)
        if not profile:return
        meds=profile.get("medications",[])
        search=normalized(self.med_gallery_query)
        meds=[m for m in meds if search in normalized(m.get("name","")+" "+
              m.get("dose","")+" "+m.get("dose_pattern",""))]
        meds=[m for m in meds if medication_filter_matches(m,self.med_gallery_state)]
        columns=5 if self.winfo_width()>=1400 else 4 if self.winfo_width()>=1100 else 3
        for col in range(columns):grid.grid_columnconfigure(col,weight=1,uniform="meds")
        if not meds:
            empty=self._card(grid)
            empty.grid(row=0,column=0,columnspan=columns,sticky="ew",pady=5)
            self._label(empty,"Sem medicamentos para estes filtros.",13,
                        color=self.p["muted"]).pack(pady=30)
        for i,med in enumerate(meds):
            r,c=divmod(i,columns)
            tile=self._card(grid,rounding=13)
            tile.grid(row=r,column=c,sticky="nsew",padx=5,pady=5)
            # Auto-size content. Grid aligns cards in the same row.
            available=max(170,int((self.winfo_width()-110)/columns)-37)
            photo=self._med_card_photo(med.get("photo_b64",""),available,137)
            poster=ctk.CTkFrame(tile,fg_color=self.p["thumb"],height=137,
                                 corner_radius=10)
            poster.pack(fill="x",padx=8,pady=(8,7))
            poster.pack_propagate(False)
            if photo:
                picture=ctk.CTkLabel(poster,image=photo,text="")
            else:
                picture=ctk.CTkLabel(poster,text="💊",height=115,
                    font=ctk.CTkFont(family="Segoe UI Emoji",size=46),
                    text_color=self.p["text"])
                self._label(poster,"Sem fotografia",9,
                            color=self.p["muted"]).place(relx=.5,rely=.9,anchor="center")
            picture.pack(fill="both",expand=True)
            title=self._label(tile,med.get("name",""),14,True,wrap=available)
            title.pack(anchor="w",fill="x",padx=12)
            meta="  ·  ".join(str(x) for x in
                (med.get("dose"),med.get("time")) if x)
            subtitle=self._label(tile,meta,11,color=self.p["muted"],wrap=available)
            subtitle.pack(anchor="w",fill="x",padx=12,pady=(2,1))
            dose_info=next_medication_label(med)
            predicted=self._label(tile,dose_info,10,color=self.p["muted"],wrap=available)
            predicted.pack(anchor="w",fill="x",padx=12,pady=(3,1))
            status,status_bg,status_fg=medication_status(med)
            line=ctk.CTkFrame(tile,fg_color="transparent")
            line.pack(side="bottom",fill="x",padx=10,pady=(8,10))
            ctk.CTkLabel(line,text="  "+status+"  ",
                font=ctk.CTkFont(size=10,weight="bold"),
                text_color=status_fg,fg_color=status_bg,
                corner_radius=8,height=24).pack(side="left")
            self._button(line,self.t("edit_medication"),
                         lambda mid=med["id"]:self._edit_med(mid),
                         width=110,height=27).pack(side="right")
            # Clicking the poster or title opens the editor, just like a
            # movie card; no extra floating form windows.
            for widget in (poster,picture,title,subtitle,predicted):
                widget.bind("<Button-1>",lambda event,mid=med["id"]:self._edit_med(mid),add="+")
            tile.configure(cursor="hand2")

    def _new_med(self):
        self.editing_med=None
        self.gallery_mode="editor"
        self._render()

    def _edit_med(self,mid):
        self.editing_med=mid
        self.gallery_mode="editor"
        self._render()

    def _back_to_med_gallery(self):
        self.gallery_mode="catalog"
        self.editing_med=None
        self._render()

    def _med_form(self,frame,med):
        fields=med or {}
        self.med_photo_draft=fields.get("photo_b64","")
        head=ctk.CTkFrame(frame,fg_color="transparent")
        head.pack(fill="x",padx=15,pady=(8,4))
        self._label(head,self.t("edit_medication") if med else self.t("new_medication"),
                    18,True).pack(side="left")
        self._button(head,"‹  "+self.t("cancel"),self._back_to_med_gallery,
                     width=105,height=30).pack(side="right")
        body=ctk.CTkScrollableFrame(frame,fg_color="transparent")
        body.pack(fill="both",expand=True,padx=10,pady=4)
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
            box.grid(row=row,column=col,sticky="ew",padx=5,pady=4)
            self._label(box,self.t(title),12,True,color=self.p["muted"]).pack(anchor="w",pady=(0,6))
            ctk.CTkOptionMenu(box,values=list(choices),variable=var,width=180,
                height=33,fg_color=self.p["field"],button_color=BLUE,
                dropdown_fg_color=self.p["panel2"],text_color=self.p["text"],
                dropdown_text_color=self.p["text"]).pack(fill="x")
        self.no_alarm_var=ctk.BooleanVar(value=fields.get("no_alarm",False))
        self.suspended_var=ctk.BooleanVar(value=fields.get("suspended",False))
        toggles=ctk.CTkFrame(body,fg_color="transparent")
        toggles.grid(row=5,column=0,columnspan=2,sticky="w",padx=7,pady=(8,5))
        for k,var in [("no_alarm",self.no_alarm_var),("suspended",self.suspended_var)]:
            ctk.CTkSwitch(toggles,text=self.t(k),variable=var,
                progress_color=TEAL,button_color=TEAL,
                fg_color=self.p["panel2"],text_color=self.p["text"]).pack(side="left",padx=(0,20))
        self._label(body,self.t("notes"),12,True,color=self.p["muted"]).grid(
            row=6,column=0,columnspan=2,sticky="w",padx=8)
        self.med_notes=ctk.CTkTextbox(body,height=58,corner_radius=9,
            fg_color=self.p["field"],border_width=1,border_color=self.p["line"],
            text_color=self.p["text"])
        self.med_notes.grid(row=7,column=0,columnspan=2,sticky="ew",padx=8,pady=(5,16))
        self.med_notes.insert("1.0",fields.get("notes",""))
        photo_row=ctk.CTkFrame(body,fg_color="transparent",corner_radius=0)
        photo_row.grid(row=8,column=0,columnspan=2,sticky="ew",padx=6,pady=5)
        self.med_photo_widget=ctk.CTkLabel(photo_row,text="Sem fotografia",
            text_color=self.p["muted"],width=80,height=62)
        self.med_photo_widget.pack(side="left",padx=9,pady=6)
        self._update_med_preview()
        self._button(photo_row,"📷  Anexar foto da embalagem",
            self._choose_med_photo,width=207,height=31).pack(side="left",padx=8)
        self._button(photo_row,"Remover foto",self._remove_med_photo,
            width=100,height=31).pack(side="left",padx=4)
        # Future fields are labelled, not falsely presented as implemented.
        for i,key in enumerate(("prescription","repetitions","leaflet","more_info")):
            p=ctk.CTkFrame(body,fg_color="transparent",corner_radius=0)
            p.grid(row=9+i,column=0,columnspan=2,sticky="ew",padx=6,pady=3)
            self._label(p,self.t(key)+"  ·  "+self.t("coming"),11,
                        color=self.p["muted"]).pack(anchor="w",padx=11,pady=7)
        footer=ctk.CTkFrame(frame,fg_color="transparent")
        footer.pack(fill="x",padx=16,pady=7)
        self._button(footer,self.t("save"),self._save_med,True,width=135,height=33).pack(side="right")
        self._button(footer,self.t("cancel"),self._back_to_med_gallery,
                     width=120,height=33).pack(side="right",padx=7)

    def _update_med_preview(self):
        image=self._authentic_thumb(self.med_photo_draft,85,62)
        self.med_photo_widget.configure(image=image,text="" if image else "Sem fotografia")

    def _remove_med_photo(self):
        self.med_photo_draft=""
        self._update_med_preview()

    def _choose_med_photo(self):
        path=filedialog.askopenfilename(parent=self,filetypes=[
            ("Imagens","*.jpg *.jpeg *.png *.webp"),("Todos os ficheiros","*.*")])
        if not path:return
        try:
            with Image.open(path) as image:
                image=ImageOps.exif_transpose(image).convert("RGB")
                image.thumbnail((750,750),Image.Resampling.LANCZOS)
                data=BytesIO()
                image.save(data,format="JPEG",quality=81,optimize=True)
                if data.tell()>450000:
                    raise ValueError("A fotografia é demasiado grande.")
                self.med_photo_draft=base64.b64encode(data.getvalue()).decode("ascii")
            self._update_med_preview()
        except Exception as exc:
            messagebox.showerror("SaúdePrática",str(exc),parent=self)

    def _save_med(self):
        fields={key:entry.get() for key,entry in self.med_widgets.items()}
        fields.update({
            "administration_route":ROUTES[self.route_var.get()],
            "injection_type":INJECTIONS[self.injection_var.get()],
            "dose_pattern":self.take_var.get(),
            "no_alarm":self.no_alarm_var.get() or self.take_var.get()=="SOS",
            "suspended":self.suspended_var.get(),
            "notes":self.med_notes.get("1.0","end-1c"),
            "photo_b64":self.med_photo_draft,
        })
        try:
            self.store.save_medication(self.active_id,fields,self.editing_med)
            self._back_to_med_gallery()
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
             text_color=self.p["text"],dropdown_text_color=self.p["text"],
             dropdown_fg_color=self.p["panel"],command=self._change_theme)
        menu.set(next((title for title,v in values.items() if v==self.theme),next(iter(values))))
        menu.grid(row=0,column=1,padx=30,pady=10)
        lang_menu=ctk.CTkOptionMenu(inner,values=list(LANG_NAMES.values()),
            width=230,fg_color=self.p["panel2"],button_color=BLUE,
            text_color=self.p["text"],dropdown_text_color=self.p["text"],
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
        self._button(wrapper,"Importar toda a família Android",
                     lambda:self.navigate("import"),width=302,height=38).pack(anchor="w",pady=(18,0))
        self._button(wrapper,"Reexportar ZIP Android original",
                     lambda:export_original_zip(self),width=300,height=34).pack(anchor="w",pady=(8,0))
        self._label(wrapper,
            "O backup .spbackup encriptado inclui todos os perfis, fotos, documentos, "
            "medicação, agenda e os ZIPs Android originais anteriormente importados.",
            12,color=self.p["muted"],wrap=920).pack(anchor="w",pady=(12,0))

    def _open_appointment(self,appointment_id):
        self.editing_appointment=appointment_id
        self.agenda_mode="editor"
        self._render()

    def _new_appointment(self):
        self.editing_appointment=None
        self.agenda_mode="editor"
        self._render()

    def _close_appointment(self):
        self.editing_appointment=None
        self.agenda_mode="catalog"
        self._render()

    def _save_appointment(self):
        try:
            data={key:entry.get() for key,entry in self.appointment_widgets.items()}
            data["notes"]=self.appointment_notes.get("1.0","end-1c")
            data["description"]=self.appointment_description.get("1.0","end-1c")
            data["desktop_status"]=APPOINTMENT_STATES[self.appointment_status_var.get()]
            for key,(entry,original) in self.appointment_extra_widgets.items():
                data[key]=parse_appointment_extra(key,entry.get(),original)
            self.store.save_appointment(self.active_id,data,self.editing_appointment)
            self._close_appointment()
        except (LocalStoreError,ValueError,KeyError) as exc:
            messagebox.showerror("Não foi possível guardar a marcação",str(exc),parent=self)

    def _appointment_form(self,person):
        appointments=person.get("appointments",[])
        current=next((x for x in appointments if x.get("id")==self.editing_appointment),
                     None) if self.editing_appointment else None
        if self.editing_appointment and current is None:
            self._close_appointment()
            return
        values=current or {}
        heading=ctk.CTkFrame(self.body,fg_color="transparent")
        heading.pack(fill="x",padx=12,pady=(7,8))
        self._label(heading,"Editar marcação" if current else "Nova marcação",20,True).pack(side="left")
        self._button(heading,"Voltar à Agenda",self._close_appointment,
                     width=156,height=32).pack(side="right")
        content=ctk.CTkScrollableFrame(self.body,fg_color="transparent",corner_radius=0)
        content.pack(fill="both",expand=True,padx=9,pady=5)
        content.grid_columnconfigure(0,weight=1)
        content.grid_columnconfigure(1,weight=1)
        self.appointment_widgets={}
        self.appointment_extra_widgets={}
        labels=dict(APPOINTMENT_FIELDS)
        self._label(content,"Dados do agendamento",15,True,color=TEAL).grid(
            row=0,column=0,columnspan=2,sticky="w",padx=8,pady=(4,11))
        primary=[key for key,_ in APPOINTMENT_FIELDS if key not in ("notes","description")]
        for i,key in enumerate(primary):
            initial=values.get(key,"")
            if key=="title" and not initial:
                initial=values.get("activity") or values.get("name") or ""
            row,col=1+i//2,i%2
            box=ctk.CTkFrame(content,fg_color="transparent")
            box.grid(row=row,column=col,sticky="ew",padx=7,pady=5)
            self._label(box,labels[key],11,True,color=self.p["muted"]).pack(anchor="w",pady=(0,3))
            entry=ctk.CTkEntry(box,height=35,corner_radius=8,
                 border_color=self.p["line"],fg_color=self.p["field"],
                 text_color=self.p["text"])
            entry.pack(fill="x")
            entry.insert(0,str(initial) if initial is not None else "")
            self.appointment_widgets[key]=entry
        base_row=1+(len(primary)+1)//2
        state_box=ctk.CTkFrame(content,fg_color="transparent")
        state_box.grid(row=base_row,column=0,columnspan=2,sticky="ew",padx=7,pady=(12,9))
        self._label(state_box,"Estado da marcação",12,True,color=TEAL).pack(anchor="w",pady=(0,5))
        current_state=appointment_status(values) if current else "pending"
        selected=next((label for label,key in APPOINTMENT_STATES.items()
                       if key==current_state),"Pendente")
        self.appointment_status_var=ctk.StringVar(value=selected)
        ctk.CTkOptionMenu(state_box,values=list(APPOINTMENT_STATES),
            variable=self.appointment_status_var,height=36,width=250,
            fg_color=self.p["panel2"],button_color=BLUE,
            dropdown_fg_color=self.p["panel2"],text_color=self.p["text"],
            dropdown_text_color=self.p["text"]).pack(anchor="w")
        self._label(state_box,
            "Cancelar aqui altera apenas a ficha local. Não cancela a consulta no hospital.",
            11,color=self.p["muted"],wrap=880).pack(anchor="w",pady=(6,0))
        for delta,(key,label) in enumerate((("description","Descrição"),("notes","Notas"))):
            row=base_row+1+delta*2
            self._label(content,label,11,True,color=self.p["muted"]).grid(
                row=row,column=0,columnspan=2,sticky="w",padx=9,pady=(11,3))
            field=ctk.CTkTextbox(content,height=85,fg_color=self.p["field"],
                 border_width=1,border_color=self.p["line"],text_color=self.p["text"])
            field.grid(row=row+1,column=0,columnspan=2,sticky="ew",padx=7,pady=(0,6))
            field.insert("1.0",str(values.get(key,"") or ""))
            if key=="notes":self.appointment_notes=field
            else:self.appointment_description=field
        start_extra=base_row+5
        extras=appointment_extras(values)
        if extras:
            self._label(content,"Outros campos importados ou personalizados",15,
                True,color=TEAL).grid(row=start_extra,column=0,columnspan=2,
                                     sticky="w",padx=8,pady=(19,8))
            for index,(key,value) in enumerate(extras):
                box=ctk.CTkFrame(content,fg_color="transparent")
                box.grid(row=start_extra+1+index//2,column=index%2,
                         sticky="ew",padx=7,pady=4)
                self._label(box,key,11,True,color=self.p["muted"]).pack(anchor="w",pady=(0,3))
                entry=ctk.CTkEntry(box,height=35,fg_color=self.p["field"],
                     border_color=self.p["line"],text_color=self.p["text"])
                entry.pack(fill="x")
                entry.insert(0,json.dumps(value,ensure_ascii=False)
                             if not isinstance(value,str) else value)
                self.appointment_extra_widgets[key]=(entry,value)
        if current and current.get("android_original") is not None:
            hint_row=start_extra+2+(len(extras)+1)//2
            self._label(content,
                "Os campos originais de importação Android e os identificadores ficam "
                "protegidos. Todos os restantes campos visíveis são editáveis.",
                11,color=self.p["muted"],wrap=900).grid(
                    row=hint_row,column=0,columnspan=2,sticky="w",padx=8,pady=11)
        actions=ctk.CTkFrame(self.body,fg_color="transparent")
        actions.pack(fill="x",padx=20,pady=(5,11))
        self._button(actions,"Guardar alterações" if current else "Guardar marcação",
                     self._save_appointment,True,width=179,height=36).pack(side="right")
        self._button(actions,"Cancelar",self._close_appointment,
                     width=112,height=36).pack(side="right",padx=8)

    def _set_agenda_filter(self,key):
        """Re-render the Agenda with one of the four Android-style views."""
        if key not in dict(AGENDA_FILTERS):return
        self.agenda_filter=key
        self._render()

    def _agenda(self):
        """Filter appointments without changing the imported Android records."""
        self.wallpaper_shell.glass_enabled=False
        self._heading("Agenda", "Consultas, exames e tratamentos num só lugar")
        profile=self.store.get_profile(self.active_id) if self.active_id else None
        if not profile:
            self._label(self.body,"Seleciona primeiro um perfil.",14).pack(anchor="w")
            return
        if self.agenda_mode=="editor":
            self._appointment_form(profile)
            return

        controls=ctk.CTkFrame(self.body,fg_color="transparent")
        controls.pack(fill="x",pady=(0,11))
        for key,label in AGENDA_FILTERS:
            self._button(
                controls,label,lambda k=key:self._set_agenda_filter(k),
                accent=(self.agenda_filter==key),
                width=124 if key!="all" else 113,height=32
            ).pack(side="left",padx=(0,6))

        all_items=[x for x in profile.get("appointments",[]) if isinstance(x,dict)]
        now=datetime.now()
        items=filtered_appointments(all_items,self.agenda_filter,now)
        summary=ctk.CTkFrame(self.body,fg_color="transparent")
        summary.pack(fill="x",pady=(2,11))
        self._label(summary,"Marcações",18,True).pack(side="left",padx=(0,12))
        self._label(summary,f"{len(items)} de {len(all_items)}",12,
                    color=self.p["muted"]).pack(side="left",pady=(3,0))
        self._button(summary,"+ Adicionar",self._new_appointment,
                     True,width=145,height=32).pack(side="right",padx=8)

        if not items:
            self._label(self.body,"Não existem marcações para este filtro.",14,
                        color=self.p["muted"]).pack(anchor="w",pady=22)
            return

        upcoming,past=[],[]
        for item in items:
            when=appointment_datetime(item)
            is_future=when is not None and when>=now
            (upcoming if is_future else past).append((when or datetime.min,item))
        upcoming.sort(key=lambda pair:pair[0])
        past.sort(key=lambda pair:pair[0],reverse=True)

        scroll=ctk.CTkScrollableFrame(self.body,fg_color="transparent",
                                     corner_radius=0)
        scroll.pack(fill="both",expand=True)

        def section(heading,entries,is_future):
            if not entries:return
            label=ctk.CTkFrame(scroll,fg_color="transparent")
            label.pack(fill="x",pady=(5,7))
            ctk.CTkFrame(label,fg_color=TEAL,width=3,height=23).pack(
                side="left",padx=(1,12))
            self._label(label,heading,15,True).pack(side="left")
            for _,item in entries:
                name=str(item.get("title") or item.get("activity") or
                         item.get("department") or item.get("name") or
                         "Marcação")[:180]
                date=str(item.get("date") or "")[:40]
                hour=str(item.get("time") or "")[:40]
                location=str(item.get("location") or item.get("place") or
                             item.get("unit") or "")[:220]
                status=appointment_status(item,now)
                status_name={"pending":"● PENDENTE","done":"✓ REALIZADA",
                             "cancelled":"✕ CANCELADA"}[status]
                bright="#eaf5fa" if self.p["bg"]!="#edf4f7" else "#ffffff"
                dark="#0d1f2a" if self.p["bg"]!="#edf4f7" else "#e4eef2"
                bg=bright if is_future else dark
                fg="#173140" if is_future else self.p["muted"]
                secondary="#496170" if is_future else "#8098a6"
                status_color=("#9e353b" if is_future else "#f09a9a") if status=="cancelled" else (
                    ("#0c6762" if is_future else "#67c9b5") if status=="done"
                    else ("#0c716a" if is_future else "#70d4cc"))
                row=ctk.CTkFrame(scroll,fg_color=bg,corner_radius=11,
                    border_width=1,border_color="#c5e6ef" if is_future else self.p["line"])
                row.pack(fill="x",pady=5,padx=(0,8))
                when=appointment_datetime(item)
                tile=ctk.CTkFrame(row,fg_color="#c5ecec" if is_future else "#193b48",
                                  corner_radius=9,width=105)
                tile.pack(side="left",padx=(11,14),pady=10)
                if when:
                    month_names=("JAN","FEV","MAR","ABR","MAI","JUN",
                                 "JUL","AGO","SET","OUT","NOV","DEZ")
                    date_badge=f"{when.day:02d} {month_names[when.month-1]}"
                    self._label(tile,date_badge,13,True,
                        color="#14585e" if is_future else "#a3d4d5",
                        anchor="center").pack(fill="x",padx=7,pady=(9,2))
                    self._label(tile,when.strftime("%H:%M"),12,True,
                        color="#14585e" if is_future else "#a3d4d5",
                        anchor="center").pack(fill="x",padx=7,pady=(0,8))
                else:
                    self._label(tile,date or "Sem data",11,True,
                        color="#14585e" if is_future else "#a3d4d5",
                        anchor="center").pack(fill="x",padx=7,pady=14)
                info=ctk.CTkFrame(row,fg_color="transparent")
                info.pack(side="left",fill="both",expand=True,pady=(8,9),padx=(0,9))
                appointment_title=self._label(info,name,14,True,color=fg,wrap=880)
                appointment_title.pack(anchor="w",fill="x")
                if location:
                    self._label(info,location,11,color=secondary,wrap=880).pack(
                        anchor="w",fill="x",pady=(2,0))
                status_widget=self._label(info,status_name,11,True,color=status_color)
                status_widget.pack(anchor="w",pady=(3,0))
                # Editing is explicit; clicking the title or date also opens
                # the full-screen form, never a floating dialog.
                self._button(row,"Abrir ficha",
                    lambda uid=item["id"]:self._open_appointment(uid),
                    width=110,height=32).pack(side="right",padx=(5,12),pady=13)
                for widget in (row,tile,info,appointment_title,status_widget):
                    widget.bind("<Button-1>",
                        lambda _event,uid=item["id"]:self._open_appointment(uid),add="+")

        section("Próximos compromissos",upcoming,True)
        section("Compromissos anteriores",past,False)

    def _documents(self):
        self._heading("Documentos","Fotografias, PDFs e anexos importados do Android")
        profile=self.store.get_profile(self.active_id) if self.active_id else None
        if not profile:
            self._label(self.body,"Seleciona um perfil.",14).pack(anchor="w")
            return
        actions=ctk.CTkFrame(self.body,fg_color="transparent")
        actions.pack(fill="x",pady=(0,9))
        self._button(actions,"+ Importar documento / fotografia",
                     self._add_manual_document,True,width=265,height=34).pack(side="left")
        self._button(actions,"Importar ZIP Android",lambda:self.navigate("import"),
                     width=170,height=34).pack(side="left",padx=10)
        items=self.store.imported_assets(profile["id"])
        self._label(self.body,f"{len(items)} documentos e fotografias guardados com proteção Windows",
                    12,color=self.p["muted"]).pack(anchor="w",pady=(0,12))
        if not items:
            self._label(self.body,"Importa o ZIP Android para trazer as fotografias e documentos.",
                        13).pack(anchor="w")
            self._button(self.body,"Importar ZIP Android",lambda:self.navigate("import"),
                         True,width=185).pack(anchor="w",pady=12)
            return
        listbox=ctk.CTkScrollableFrame(self.body,fg_color="transparent",corner_radius=0)
        listbox.pack(fill="both",expand=True)
        for item in items:
            row=ctk.CTkFrame(listbox,fg_color=self.p["panel"],corner_radius=9)
            row.pack(fill="x",padx=4,pady=3)
            info=ctk.CTkFrame(row,fg_color="transparent")
            info.pack(side="left",fill="x",expand=True,padx=14,pady=8)
            self._label(info,item.get("display_name") or item["filename"],13,True).pack(anchor="w")
            self._label(info,f"{item['category']} · {round(item['bytes']/1024)} KB",
                        11,color=self.p["muted"]).pack(anchor="w")
            self._button(row,"Exportar ficheiro",lambda x=item:self._export_document(x),
                         width=150,height=32).pack(side="right",padx=10)

    def _add_manual_document(self):
        if not self.active_id:return
        file=filedialog.askopenfilename(parent=self,title="Importar documento ou fotografia",
             filetypes=[("PDF e fotografias","*.pdf *.jpg *.jpeg *.png *.webp")])
        if not file:return
        try:
            created=self.store.import_local_document(self.active_id,Path(file))
            messagebox.showinfo("Documentos",
                "Documento protegido e associado ao perfil." if created else
                "Documento já existente neste perfil.",parent=self)
            self._render()
        except (LocalStoreError,OSError,ValueError) as exc:
            messagebox.showerror("Documentos",str(exc),parent=self)

    def _export_profile_json(self,kind):
        profile=self.store.get_profile(self.active_id) if self.active_id else None
        if not profile:return
        if not messagebox.askyesno("Exportar JSON",
            "O JSON exportado não será encriptado. Guarda-o numa pasta segura. Continuar?",
            parent=self):
            return
        filename="medicacao.json" if kind=="medications" else "agenda.json"
        dest=filedialog.asksaveasfilename(parent=self,title="Exportar JSON do perfil",
              defaultextension=".json",initialfile=filename,
              filetypes=[("JSON","*.json")])
        if not dest:return
        try:
            records=[]
            for item in profile.get(kind,[]):
                raw=item.get("android_original")
                if isinstance(raw,dict):
                    records.append(raw)
                else:
                    obj=dict(item)
                    if kind=="medications":
                        obj["medication"]=obj.pop("name","")
                    else:
                        obj["activity"]=obj.pop("title","")
                    records.append(obj)
            Path(dest).write_text(json.dumps({kind:records},ensure_ascii=False,
                               indent=2),encoding="utf-8")
            messagebox.showinfo("Exportar JSON",
                "JSON exportado. A importação deste ficheiro no Android ainda precisa de testes.",
                parent=self)
        except (OSError,ValueError) as exc:
            messagebox.showerror("Exportar JSON",str(exc),parent=self)

    def _export_document(self,item):
        ext=Path(item["filename"]).suffix.lower()
        path=filedialog.asksaveasfilename(parent=self,
             title="Guardar cópia desencriptada deste documento",
             initialfile=item["filename"],
             defaultextension=ext)
        if not path:return
        try:
            dest=Path(path)
            if dest.exists() and not messagebox.askyesno("Confirmar",
                "Substituir o documento existente?",parent=self):return
            raw=self.store.read_imported_asset(item)
            dest.write_bytes(raw)
            messagebox.showinfo("Documento","Ficheiro guardado no local escolhido.",parent=self)
        except (OSError,LocalStoreError,ValueError) as exc:
            messagebox.showerror("Documento","Não foi possível exportar: "+str(exc),parent=self)

    def _pick_android_json(self,kind):
        # File picker is the OS-native dialog; the preview and confirmation
        # live in the full-size SaúdePrática screen, never in a popup form.
        title="Medicação Android" if kind=="medications" else "Agenda Android"
        file=filedialog.askopenfilename(parent=self,title="Importar JSON: "+title,
             filetypes=[("Ficheiros JSON","*.json"),("Todos os ficheiros","*.*")])
        if not file:return
        try:
            source=Path(file)
            if source.stat().st_size>8*1024*1024:
                raise AndroidImportError("O JSON excede 8 MB.")
            profile=self.store.get_profile(self.active_id)
            self.android_import_plan=plan_json(source.read_bytes(),kind,profile)
            self.android_zip_inspection=None
            self.android_import_error=""
            self.android_import_feedback=""
        except (AndroidImportError,OSError,ValueError) as exc:
            self.android_import_error=str(exc)
            self.android_import_plan=None
        self._render()

    def _inspect_android_zip(self):
        file=filedialog.askopenfilename(parent=self,
             title="Escolher backup completo SaúdePrática Android",
             filetypes=[("Backup ZIP Android","*.zip"),("Todos os ficheiros","*.*")])
        if not file:return
        try:
            source=Path(file)
            if source.stat().st_size>220*1024*1024:
                raise AndroidImportError("O ZIP excede 220 MB.")
            blob=source.read_bytes()
            choices=archive_sources(blob)  # checks all SHA-256 hashes before preview
            self.android_zip_blob=blob
            self.android_zip_sources=choices
            self.android_zip_selected=""
            self.android_zip_plan=None
            self.android_import_plan=None
            self.android_import_error=""
            self.android_import_feedback=""
        except (AndroidImportError,OSError,ValueError) as exc:
            self.android_import_error=str(exc)
            self.android_zip_blob=None
            self.android_zip_sources=()
            self.android_zip_plan=None
        self._render()

    def _choose_zip_source(self,value):
        selected=next((p for p in self.android_zip_sources if value.startswith(
            p.name+" · ")),None)
        self.android_zip_selected=selected.identifier if selected else ""
        self.android_zip_plan=None
        self._render()

    def _preview_zip_import(self):
        try:
            if not self.android_zip_blob or not self.android_zip_selected:
                raise AndroidImportError("Escolhe o perfil Android de origem.")
            profile=self.store.get_profile(self.active_id)
            self.android_zip_plan=prepare_archive(
                self.android_zip_blob,self.android_zip_selected,profile)
            self.android_import_error=""
            self.android_import_feedback=""
        except (AndroidImportError,ValueError,OSError) as exc:
            self.android_import_error=str(exc)
            self.android_zip_plan=None
        self._render()

    def _confirm_zip_import(self):
        plan=self.android_zip_plan
        if plan is None:return
        if plan.profile_id!=self.active_id:
            self.android_import_error="O perfil Windows mudou. Prepara a importação novamente."
            self.android_zip_plan=None
        else:
            try:
                added=apply_archive(self.store,plan)
                self.android_import_feedback=(
                    f"ZIP importado no perfil {plan.source.name}: "
                    f"{added['medications']} medicamentos, "
                    f"{added['appointments']} marcações e "
                    f"{added['attachments']} fotografias/documentos protegidos.")
                self.android_import_error=""
                self.android_zip_plan=None
                self.android_zip_blob=None
                self.android_zip_sources=()
            except (AndroidImportError,OSError,ValueError) as exc:
                self.android_import_error=str(exc)
        self._render()

    def _confirm_android_import(self):
        plan=self.android_import_plan
        if plan is None:return
        if plan.profile_id!=self.active_id:
            self.android_import_error="O perfil ativo mudou. Escolhe o ficheiro novamente."
            self.android_import_plan=None
            self._render()
            return
        try:
            count=apply_plan(self.store,plan)
            kind="medicamentos" if plan.kind=="medications" else "marcações"
            self.android_import_feedback=f"Importação concluída: {count} {kind} adicionados."
            self.android_import_error=""
            self.android_import_plan=None
        except Exception as exc:
            self.android_import_error=str(exc)
        self._render()

    def _android_import_page(self):
        self._heading("Importar / Exportar dados",
                      "Família completa Android ou importação individual por perfil")
        family_controls(self)
        profile=self.store.get_profile(self.active_id) if self.active_id else None
        if not profile:
            self._label(self.body,"Para importações JSON isoladas, seleciona um perfil de destino. "
                        "A importação da família inteira funciona mesmo sem perfil selecionado.",
                        13,color=self.p["muted"],wrap=960).pack(anchor="w",pady=12)
            if getattr(self,"android_import_error",""):
                self._label(self.body,self.android_import_error,13,color="#e59b9b").pack(anchor="w")
            return
        self._label(self.body,"Importação individual · Destino: "+str(profile.get("name","")),
                    17,True,color=TEAL).pack(anchor="w",pady=(4,13))
        bar=ctk.CTkFrame(self.body,fg_color="transparent")
        bar.pack(fill="x",pady=(0,14))
        self._button(bar,"Importar Medicação JSON",lambda:self._pick_android_json("medications"),
                     True,width=232,height=38).pack(side="left",padx=(0,10))
        self._button(bar,"Importar Agenda JSON",lambda:self._pick_android_json("appointments"),
                     True,width=216,height=38).pack(side="left",padx=(0,10))
        self._button(bar,"Importar ZIP Android",self._inspect_android_zip,
                     width=218,height=38).pack(side="left")
        exports=ctk.CTkFrame(self.body,fg_color="transparent")
        exports.pack(fill="x",pady=(0,9))
        self._button(exports,"Exportar Medicação JSON",lambda:self._export_profile_json("medications"),
                     width=220,height=34).pack(side="left",padx=(0,9))
        self._button(exports,"Exportar Agenda JSON",lambda:self._export_profile_json("appointments"),
                     width=215,height=34).pack(side="left")
        self._label(self.body,"Ficheiros aceites: medicacao.json, agenda.json ou ZIP completo Android. "
                    "Os dados novos serão acrescentados apenas ao perfil escolhido.",
                    12,color=self.p["muted"],wrap=1000).pack(anchor="w",pady=(0,12))
        if getattr(self,"android_import_error",""):
            self._label(self.body,"Não foi possível preparar a importação: "+
                   self.android_import_error,13,color="#f5a0a0",wrap=1000).pack(
                   anchor="w",pady=(8,12))
        if getattr(self,"android_import_feedback",""):
            self._label(self.body,self.android_import_feedback,16,True,
                   color=TEAL).pack(anchor="w",pady=(8,12))
        plan=self.android_import_plan
        if plan is not None:
            label="Medicação" if plan.kind=="medications" else "Agenda"
            self._label(self.body,"Pré-visualização · "+label,19,True).pack(
                anchor="w",pady=(12,7))
            self._label(self.body,f"Registos no ficheiro: {len(plan.entries)}  ·  "
                f"Novos: {len(plan.new)}  ·  Já importados: {plan.repeated}",
                15).pack(anchor="w",pady=(0,9))
            self._label(self.body,"Exemplos: "+", ".join(plan.names[:8])+
                    ("…" if len(plan.names)>8 else ""),12,
                    color=self.p["muted"],wrap=1000).pack(anchor="w",pady=(0,15))
            controls=ctk.CTkFrame(self.body,fg_color="transparent")
            controls.pack(fill="x",pady=(5,11))
            self._button(controls,"Confirmar importação",self._confirm_android_import,
                  True,width=210,height=39).pack(side="left",padx=(0,9))
            self._button(controls,"Cancelar",self._cancel_android_import,
                  width=130,height=39).pack(side="left")
        if self.android_zip_sources:
            self._label(self.body,"ZIP Android validado · escolher perfil de origem",17,True).pack(
                    anchor="w",pady=(12,7))
            choices=[f"{p.name} · {p.medications} medicamentos · {p.appointments} marcações · {p.attachments} anexos"
                     for p in self.android_zip_sources]
            menu=ctk.CTkOptionMenu(self.body,values=choices,width=630,height=38,
                    fg_color=self.p["panel2"],text_color=self.p["text"],
                    button_color="#137b89",command=self._choose_zip_source)
            target=next((i for i,p in enumerate(self.android_zip_sources)
                         if p.identifier==self.android_zip_selected),None)
            if target is None:
                menu.set("Escolher perfil Android (origem)")
            else:menu.set(choices[target])
            menu.pack(anchor="w",pady=(0,12))
            self._button(self.body,"Preparar importação deste perfil",
                        self._preview_zip_import,width=285,height=38).pack(anchor="w")
        if self.android_zip_plan is not None:
            p=self.android_zip_plan
            self._label(self.body,"Pré-visualização ZIP (antes de gravar)",18,True,
                        color=TEAL).pack(anchor="w",pady=(13,7))
            self._label(self.body,
                f"Origem Android: {p.source.name} → Windows: {profile.get('name','')}",
                13).pack(anchor="w",pady=(0,5))
            self._label(self.body,
                f"Medicação: {len(p.medications.new)} novas / {p.medications.repeated} repetidas; "
                f"Agenda: {len(p.appointments.new)} novas / {p.appointments.repeated} repetidas; "
                f"Anexos: {len(p.attachments)}",
                13).pack(anchor="w",pady=(0,12))
            self._button(self.body,"Confirmar importação ZIP",self._confirm_zip_import,
                         True,width=255,height=40).pack(anchor="w")
        spacer=ctk.CTkFrame(self.body,fg_color="transparent")
        spacer.pack(fill="both",expand=True)
        actions=ctk.CTkFrame(self.body,fg_color="transparent")
        actions.pack(fill="x",pady=(8,11))
        self._button(actions,"Ver Medicação",lambda:self.navigate("medication"),
            width=160,height=34).pack(side="left",padx=(0,8))
        self._button(actions,"Ver Agenda",lambda:self.navigate("agenda"),
            width=160,height=34).pack(side="left")
        self._label(self.body,"Importação ZIP por perfil, com anexos protegidos por DPAPI. "
            "Não substitui os alarmes Android. Exportação Windows: backup encriptado .spbackup.",
            11,color=self.p["muted"],wrap=1000).pack(anchor="w",pady=(8,4))

    def _cancel_android_import(self):
        self.android_import_plan=None
        self.android_import_error=""
        self.android_import_feedback=""
        self.android_zip_inspection=None
        self.android_zip_sources=()
        self.android_zip_blob=None
        self.android_zip_plan=None
        self._render()

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
            # Real multi-page GUI check, not just a splash check. The runner
            # supplies an isolated LOCALAPPDATA directory and synthetic data.
            person=app.store.save_profile({"name":"Pessoa de teste",
                "caregiver":True, "health_unit":"Unidade fictícia"})
            app.active_id=person["id"]
            med=app.store.save_medication(person["id"],{
                "name":"Comprimido fictício","dose":"10 mg","time":"09:00",
                "administration_route":"oral","dose_pattern":"Jejum"})
            for page in ("home","profiles","medication"):
                app.navigate(page)
                app.update_idletasks()
                app.update()
            app._edit_med(med["id"])
            app.update_idletasks()
            app.update()
            app._back_to_med_gallery()
            app._set_med_filter("active")
            app.update()
            for theme in ("light","dark","system"):
                ctk.set_appearance_mode(theme)
                app.navigate("home")
                app.update_idletasks()
                app.update()
                app.navigate("medication")
                app.update()
                app.navigate("profiles")
                app.update()
                app.navigate("options")
                app.update()
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
