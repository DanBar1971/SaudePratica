"""SaúdePrática Desktop 0.4 — modern adaptive Windows client.

Phase 1: full profile editing, active profile selection, medication,
appearance/language, original brand assets and legacy DPAPI/backup compatibility.
Agenda, attachments, live Android syncing and alarms are explicitly not built.
"""
from __future__ import annotations

import base64
import json
from io import BytesIO
import threading
import queue
import time
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
from windows.backup_ui_v072 import render_backup
from windows.profile_fields_v066 import missing_profile_fields
from windows.medication_schedule_v066 import next_medication_label
from windows.medication_gallery_v068 import medication_filter_matches, medication_status
from windows.medication_editor_v080 import GROUPS, source_value, medication_document_assets, medication_document_option
from windows.document_ocr_v081 import recognize_document, preview_document, suggest_fields, DocumentRecognitionError
from windows.medication_flags_v076 import suspended as is_suspended, no_alarm as is_no_alarm, configured_reminder, active_reminder, reminder_clock
from windows.medication_time_v082 import condition_value, mismatched_legacy_clock, canonical_reminder_fields
from windows.lan_pair_v084 import PhoneDiscovery
from windows.lan_ui_v084 import LanUi
from windows.doses_calendar_ui_v085 import DosesCalendarUi
from windows.calendar_ui_v086 import CalendarVisualV086
from windows.calendar_split_v087 import CalendarSplitV087
from windows.document_split_v087 import DocumentsV087
from windows.links_options_ui_v087 import LinksOptionsV087
from windows.health_records_ui_v088 import HealthRecordsUiV088
from windows.water_ui_v089 import WaterUiV089
from windows.activity_ui_v089 import ActivityUiV089
from windows.cycle_ui_v089 import CycleUiV089
from windows.editor_controls_v083 import CONDITIONS, EXTRA_COMBO_CHOICES, shift_clock
from windows.agenda_filter_v069 import FILTERS as AGENDA_FILTERS, appointment_status, appointment_datetime, filtered_appointments
from windows.appointment_editor_v070 import MAIN_FIELDS as APPOINTMENT_FIELDS, STATUS_OPTIONS as APPOINTMENT_STATES, extra_fields as appointment_extras, parse_extra as parse_appointment_extra
from windows.appointment_reminders_v071 import CHOICES as REMINDER_CHOICES, DEFAULT as REMINDER_DEFAULT, record_offsets

ctk.set_default_color_theme("blue")
VERSION = "0.8.9"
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


class Desktop(ctk.CTk, LanUi, CalendarVisualV086, DosesCalendarUi, CalendarSplitV087, DocumentsV087, LinksOptionsV087, HealthRecordsUiV088, WaterUiV089, ActivityUiV089, CycleUiV089):
    def __init__(self):
        self.store = SecureStore()
        pref = self.store.settings()
        self.lang = pref.get("language", "pt") if pref.get("language") in LANG_NAMES else "pt"
        self.theme = pref.get("theme", "system") if pref.get("theme") in THEME_KEYS else "system"
        ctk.set_appearance_mode(self.theme)
        super().__init__()
        # Prevent an unfinished application frame from appearing as a second
        # splash while the single packaged splash is still on screen.
        self.withdraw()
        self.title("SaúdePrática Desktop · " + VERSION)
        self.geometry("1370x790")
        self.minsize(1050, 650)
        self._busy_profile=None
        self.profile_loading_widget=None
        self.profile_loading_frame=None
        self.active_id = pref.get("active_profile")
        if not self.store.get_profile(self.active_id):
            self.active_id = self.store.profiles()[0]["id"] if self.store.profiles() else None
        self.editing_profile = self.active_id
        self.profile_edit_open = False
        self._profile_view_cache = {}
        self._profile_source_queue = queue.Queue()
        self.cc_photo_bytes = {}
        self.editing_med = None
        self.page = "home"
        self.profile_widgets = {}
        self.med_widgets = {}
        self.photo_draft = ""
        self.med_photo_draft = ""
        self.med_gallery_query = ""
        self.catalog_query = ""
        self.med_gallery_state = "all"
        self.calendar_selected = datetime.now().date()
        self.dose_selected = datetime.now().date()
        self.dose_filter = "all"
        self.agenda_filter = "all"
        self.doc_selected_digest = None
        self.doc_selected_profile = None
        self.doc_page_index = 0
        self._doc_viewer_window = None
        self._link_edit_id = None
        self._health_selection = {"clinical":None,"expenses":None}
        self._expense_year = datetime.now().year
        self.water_day = datetime.now().date()
        self.activity_day = datetime.now().date()
        self.cycle_day = datetime.now().date()
        self.cycle_month = datetime.now().date().replace(day=1)
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
        self._lan_events=queue.Queue()
        self._lan_manager=PhoneDiscovery(
            lambda event,item:self._lan_events.put((event,item)))
        self._lan_devices={}
        self._lan_seen=set()
        self._lan_status="À procura de telemóveis na mesma rede..."
        self._lan_requested=False
        self._lan_pair_code=""
        self.protocol("WM_DELETE_WINDOW",self._lan_close)
        self._assets()
        self._render()
        self.after(120,self._poll_profile_sources)
        if not os.environ.get("SAUDEPRATICA_SMOKE_REPORT"):
            self.after(900,self._lan_begin_discovery)
        self.after(330,self._lan_poll_ui)

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
        """Single rounded button language for navigation, modules and editors."""
        p=self.p
        return ctk.CTkButton(
            parent,text=label,command=command,width=width,height=max(height,32),
            corner_radius=14,border_width=1,
            border_color=TEAL_HOVER if accent else ("#336879" if p["bg"]!="#edf4f7" else p["line"]),
            font=ctk.CTkFont(family="Segoe UI",size=12,weight="bold"),
            fg_color=TEAL if accent else p["panel2"],
            hover_color=TEAL_HOVER if accent else p["hover"],
            text_color="#05252c" if accent else p["text"])

    def _back_button(self,parent,label,command,width=155):
        """Uniform back button at the top of every editor/module."""
        return self._button(parent,"‹  "+label,command,width=width,height=35)

    def _editor_tabs(self,parent):
        """The same prominent segmented tabs for medication and appointments."""
        p=self.p
        widget=ctk.CTkTabview(
            parent,corner_radius=13,border_width=1,border_color=p["line"],
            fg_color="transparent",text_color=p["text"],
            segmented_button_fg_color=p["panel"],
            segmented_button_selected_color="#078f93",
            segmented_button_selected_hover_color="#00a99b",
            segmented_button_unselected_color=p["panel2"],
            segmented_button_unselected_hover_color=p["hover"])
        widget.pack(fill="both",expand=True,padx=4,pady=(0,2))
        widget._segmented_button.configure(
            height=34,corner_radius=14,
            font=ctk.CTkFont(family="Segoe UI",size=12,weight="bold"))
        return widget

    def _editable_choice(self,parent,label,initial,values,row,col,span=1):
        """Android-like dropdown with free typing, so old values are not lost."""
        p=self.p
        cell=ctk.CTkFrame(parent,fg_color="transparent")
        cell.grid(row=row,column=col,columnspan=span,
                  sticky="ew",padx=4,pady=(2,6))
        self._label(cell,label,11,True,color=p["muted"]).pack(
            anchor="w",pady=(0,3))
        combo=ctk.CTkComboBox(
            cell,values=list(values),height=34,corner_radius=10,
            border_color="#167d88",border_width=1,fg_color=p["field"],
            button_color="#116c7a",button_hover_color=TEAL_HOVER,
            dropdown_fg_color=p["panel2"],
            dropdown_hover_color=p["hover"],dropdown_text_color=p["text"],
            text_color=p["text"],font=ctk.CTkFont(size=12))
        combo.pack(fill="x")
        combo.set(str(initial or ""))
        return combo

    def _time_stepper(self,parent,label,initial,row,col):
        """Editable clock with explicit up/down 5-minute controls."""
        cell=ctk.CTkFrame(parent,fg_color="transparent")
        cell.grid(row=row,column=col,sticky="ew",padx=4,pady=(2,5))
        self._label(cell,label,11,True,color=self.p["muted"]).pack(
            anchor="w",pady=(0,3))
        line=ctk.CTkFrame(cell,fg_color="transparent")
        line.pack(fill="x")
        entry=ctk.CTkEntry(
            line,height=34,corner_radius=10,border_color="#167d88",
            fg_color=self.p["field"],text_color=self.p["text"],
            font=ctk.CTkFont(family="Segoe UI",size=13,weight="bold"))
        entry.pack(side="left",fill="x",expand=True)
        entry.insert(0,str(initial or ""))
        arrows=ctk.CTkFrame(line,fg_color="transparent")
        arrows.pack(side="left",padx=(5,0))
        for symbol,step in (("▲",1),("▼",-1)):
            ctk.CTkButton(
                arrows,text=symbol,width=35,height=18,corner_radius=7,
                font=ctk.CTkFont(size=10,weight="bold"),
                fg_color="#106878",hover_color=TEAL_HOVER,
                text_color=self.p["text"],border_width=1,
                border_color=self.p["line"],
                command=lambda d=step,e=entry:self._adjust_med_time(e,d)
            ).pack(pady=(0,1))
        return entry

    def _adjust_med_time(self,entry,direction):
        try:
            updated=shift_clock(entry.get(),direction)
        except ValueError as exc:
            messagebox.showwarning("Hora de aviso",str(exc),parent=self)
            return
        entry.delete(0,"end")
        entry.insert(0,updated)
        entry.focus_set()

    def _label(self,parent,text,size=13,bold=False,color=None,anchor="w",wrap=None):
        return ctk.CTkLabel(parent,text=text,anchor=anchor,
            text_color=color or self.p["text"],
            font=ctk.CTkFont(family="Segoe UI",size=size,
                             weight="bold" if bold else "normal"),
            wraplength=wrap or 0)

    def _card(self,parent,rounding=14,**kw):
        return ctk.CTkFrame(parent,fg_color=self.p["panel"],
            corner_radius=max(rounding,15),border_width=1,
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
        """Native Windows loading pointer on every module transition."""
        self.configure(cursor="wait")
        self.update_idletasks()
        try:
            self._render_content()
            self.update_idletasks()
        finally:
            if self._busy_profile:
                self.configure(cursor="watch")
            else:
                # Tk has to process its event queue before Windows can show
                # a cursor change. Defer restoration until the frame is visible.
                self.after(150,self._finish_busy_cursor)

    def _finish_busy_cursor(self):
        if not self._busy_profile and self.winfo_exists():
            self.configure(cursor="")

    def _render_content(self):
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
            b=self._button(nav,label,lambda k=key:self.navigate(k),accent=active,width=103,height=37)
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
            right,fg_color=self.p["panel2"],corner_radius=16,
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
            self.profile_pill,text=label+"   ▼",
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
        elif self.page=="calendar": self._calendar()
        elif self.page=="doses": self._doses()
        elif self.page=="documents": self._documents()
        elif self.page=="clinical": self._clinical()
        elif self.page=="expenses": self._expenses()
        elif self.page=="water": self._water()
        elif self.page=="activity": self._activity()
        elif self.page=="cycle": self._cycle()
        elif self.page=="shortcuts": self._shortcuts()
        elif self.page=="info": self._tips()
        elif self.page=="sync": self._sync_page()
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
        if self.page not in ("home","profiles","medication","agenda","more"):
            target="options" if self.page in ("backup","sync","info") else "more"
            label="Voltar às Opções" if target=="options" else "Voltar ao menu"
            self._back_button(head,label,lambda key=target:self.navigate(key),170).pack(side="right",padx=12,pady=3)

    def navigate(self,page):
        if page!="profiles":
            self._busy_profile=None
            self.profile_loading_widget=None
            self.profile_loading_frame=None
        if page=="profiles" and self.page!="profiles":
            self.profile_edit_open=False
        self.page=page
        self._render()

    def _select_profile(self,label):
        new_id=self.profile_choices.get(label)
        if new_id == self.active_id:return
        self.active_id=new_id
        self.water_day = datetime.now().date()
        self.activity_day = datetime.now().date()
        self.cycle_day = datetime.now().date()
        self.cycle_month = datetime.now().date().replace(day=1)
        self._health_selection = {"clinical":None,"expenses":None}
        self.doc_selected_digest=None
        self.doc_selected_profile=None
        self.doc_page_index=0
        if getattr(self,"_doc_viewer_window",None) is not None:
            self._doc_close_viewer()
        self._med_image_cache={}
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
        self.water_day = datetime.now().date()
        self.activity_day = datetime.now().date()
        self.cycle_day = datetime.now().date()
        self.cycle_month = datetime.now().date().replace(day=1)
        self._health_selection = {"clinical":None,"expenses":None}
        self.doc_selected_digest=None
        self.doc_selected_profile=None
        self.doc_page_index=0
        if getattr(self,"_doc_viewer_window",None) is not None:
            self._doc_close_viewer()
        self._med_image_cache={}
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
        left,listing,right=self._two_pane(self.t("registered_profiles"),365)
        self._button(listing,"+ "+self.t("new_profile"),
                     self._new_profile,True,width=225,height=32).pack(
                         fill="x",pady=(0,8))
        for profile in self.store.profiles():
            row=ctk.CTkFrame(listing,fg_color=self.p["panel2"],corner_radius=14,
                              border_width=1,border_color=self.p["line"])
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
            self._button(row,"ABRIR  ❯",lambda pid=profile["id"]:self._edit_profile(pid),
                         width=92,height=34).pack(side="right",padx=(0,4))
        if self.profile_edit_open:
            self._profile_form(right)
        else:
            note=ctk.CTkFrame(right,fg_color="transparent")
            note.pack(fill="both",expand=True,padx=24,pady=22)
            self._label(note,"Escolhe um perfil na lista à esquerda",20,True,
                        color=TEAL).pack(anchor="w",pady=(20,12))
            self._label(note,"A ficha e as fotografias só são carregadas quando abres "
                        "o perfil. Os registos clínicos e os documentos continuam "
                        "guardados nos respetivos módulos.",13,
                        color=self.p["muted"],wrap=700).pack(anchor="w")

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
        self.profile_edit_open=True
        self._render()

    def _edit_profile(self,pid):
        self.editing_profile=pid
        self.active_id=pid
        self.profile_edit_open=True
        self.store.update_settings(active_profile=pid)
        self._busy_profile=pid if pid not in self._profile_view_cache else None
        self._render()
        if self._busy_profile==pid:
            self._load_profile_source(pid)

    def _load_profile_source(self,pid):
        """Only an explicit edit starts a ZIP scan; never block the Tk thread."""
        self._profile_view_cache[pid]=None
        def read():
            try:
                fields,photos=self.store.profile_android_images_and_fields(pid)
            except Exception:
                fields,photos={},{}
            self._profile_source_queue.put((pid,fields,photos))
        threading.Thread(target=read,daemon=True).start()

    def _poll_profile_sources(self):
        try:
            while True:
                pid,fields,photos=self._profile_source_queue.get_nowait()
                self._profile_view_cache[pid]=(fields,photos)
                if self._busy_profile==pid:
                    self._busy_profile=None
                    self.configure(cursor="")
                    bar=self.profile_loading_widget
                    frame=self.profile_loading_frame
                    if bar is not None:
                        try:
                            if bar.winfo_exists():bar.stop()
                            if frame is not None and frame.winfo_exists():frame.destroy()
                        except tk.TclError:
                            pass
                    self.profile_loading_widget=None
                    self.profile_loading_frame=None
                if not (self.page=="profiles" and self.profile_edit_open and
                        self.editing_profile==pid):
                    continue
                # Don't overwrite anything the user has already entered.
                for key,value in fields.items():
                    field=self.profile_widgets.get(key)
                    if field is not None and isinstance(value,str) and not field.get().strip():
                        field.insert(0,value)
                # The selected Android caregiver is stored in a global
                # preference, not as a text field. Apply to the switch only
                # when it has not been changed by the user while loading.
                if isinstance(fields.get("caregiver"),bool):
                    if (self.profile_caregiver.get()==self._caregiver_initial
                            and self._caregiver_source_id==pid):
                        self.profile_caregiver.set(fields["caregiver"])
                self.cc_photo_bytes=photos
                self._refresh_cc_previews()
        except queue.Empty:
            pass
        try:
            if self.winfo_exists():
                self.after(120,self._poll_profile_sources)
        except tk.TclError:
            pass

    def _show_cc_photo(self,kind):
        data=self.cc_photo_bytes.get(kind)
        if not data:return
        try:
            with Image.open(BytesIO(data)) as src:
                im=ImageOps.exif_transpose(src).convert("RGB")
                im.thumbnail((950,650),Image.Resampling.LANCZOS)
            viewer=ctk.CTkToplevel(self)
            viewer.title("Cartão de Cidadão · "+("Frente" if kind=="cc_front" else "Verso"))
            viewer.geometry(f"{max(400,im.width+42)}x{max(240,im.height+55)}")
            preview=ctk.CTkImage(im,im,size=(im.width,im.height))
            label=ctk.CTkLabel(viewer,image=preview,text="")
            label.image=preview
            label.pack(fill="both",expand=True,padx=16,pady=16)
            viewer.transient(self)
            viewer.lift()
        except (OSError,ValueError,TypeError):
            pass

    def _refresh_cc_previews(self):
        host=getattr(self,"cc_photo_host",None)
        if host is None or not host.winfo_exists():return
        for child in host.winfo_children():
            child.destroy()
        self.cc_thumbnails=[]
        for kind,title in (("cc_front","Frente do CC"),("cc_back","Verso do CC")):
            raw=self.cc_photo_bytes.get(kind)
            if not raw:continue
            try:
                with Image.open(BytesIO(raw)) as source:
                    image=ImageOps.contain(
                        ImageOps.exif_transpose(source).convert("RGB"),
                        (250,135),method=Image.Resampling.LANCZOS)
                art=ctk.CTkImage(image,image,size=(image.width,image.height))
                self.cc_thumbnails.append(art)
                ctk.CTkButton(host,text=title,image=art,compound="top",
                    fg_color=self.p["panel2"],text_color=self.p["text"],
                    hover_color=self.p["line"],width=270,height=175,
                    command=lambda k=kind:self._show_cc_photo(k)).pack(
                    side="left",padx=(0,14),pady=5)
            except (OSError,ValueError):
                continue


    def _text_field(self,parent,label,initial="",row=0,col=0,columns=2):
        box=ctk.CTkFrame(parent,fg_color="transparent")
        box.grid(row=row,column=col,columnspan=columns,sticky="ew",padx=5,pady=4)
        self._label(box,self.t(label),11,True,color=self.p["muted"]).pack(anchor="w",pady=(0,3))
        entry=ctk.CTkEntry(box,height=34,corner_radius=10,
            border_color=self.p["line"],fg_color=self.p["field"],
            text_color=self.p["text"],font=ctk.CTkFont(size=12))
        entry.insert(0,str(initial or ""))
        entry.pack(fill="x")
        return entry

    def _profile_form(self,frame):
        """A genuine Android-style patient form; never a dump of backup JSON."""
        current=self.store.get_profile(self.editing_profile) if self.editing_profile else None
        fields=dict(current or {})
        fields.update(missing_profile_fields(
            fields,fields.get("android_profile_original",{})))
        cached=self._profile_view_cache.get(current["id"]) if current else None
        if cached:
            recovered,_=cached
            fields.update({k:v for k,v in recovered.items() if not fields.get(k)})
        self.cc_photo_bytes=cached[1] if cached else {}

        if current and self._busy_profile==current["id"]:
            progress=ctk.CTkFrame(frame,fg_color=self.p["panel2"],corner_radius=10)
            progress.pack(fill="x",padx=16,pady=(6,2))
            self._label(progress,"⌛  A carregar dados e fotografias do perfil...",
                        12,True,color=TEAL).pack(anchor="w",padx=12,pady=(8,2))
            bar=ctk.CTkProgressBar(progress,mode="indeterminate",
                                  progress_color=TEAL,height=6)
            bar.pack(fill="x",padx=12,pady=(2,9))
            bar.start()
            self.profile_loading_widget=bar
            self.profile_loading_frame=progress

        head=ctk.CTkFrame(frame,fg_color="transparent")
        head.pack(fill="x",padx=16,pady=(9,4))
        self._label(head,self.t("edit_profile") if current else self.t("new_profile"),
                    17,True).pack(side="left")
        self._back_button(head,"Voltar aos perfis",
                     self._close_profile_editor,width=164).pack(side="right")
        scroll=ctk.CTkScrollableFrame(frame,fg_color="transparent")
        scroll.pack(fill="both",expand=True,padx=9,pady=(2,6))
        scroll.grid_columnconfigure(0,weight=1)
        scroll.grid_columnconfigure(1,weight=1)
        self.profile_widgets={}

        self._label(scroll,"👤 Ficha do perfil",18,True,color=TEAL).grid(
            row=0,column=0,columnspan=2,sticky="w",padx=9,pady=(7,7))
        photos=ctk.CTkFrame(scroll,fg_color="transparent")
        photos.grid(row=1,column=0,columnspan=2,sticky="ew",padx=8,pady=(0,13))
        self.photo_draft=fields.get("photo_b64","")
        portrait=ctk.CTkFrame(photos,fg_color="transparent")
        portrait.pack(side="left",padx=(0,28),anchor="n")
        self.photo_label=ctk.CTkLabel(portrait,text=self.t("photo_none"),
            text_color=self.p["muted"],height=148,width=148)
        self.photo_label.pack(anchor="center")
        self._refresh_photo()
        self._button(portrait,"Escolher fotografia",self._choose_photo,
                     width=156,height=34).pack(pady=(8,3))
        self.cc_photo_host=ctk.CTkFrame(photos,fg_color="transparent")
        self.cc_photo_host.pack(side="left",fill="x",expand=True,anchor="n")
        self._refresh_cc_previews()

        self._caregiver_initial=bool(fields.get("caregiver",False))
        self._caregiver_source_id=current["id"] if current else None
        self.profile_caregiver=ctk.BooleanVar(value=self._caregiver_initial)
        ctk.CTkSwitch(scroll,text="🙌 Este perfil é o cuidador da família",
            variable=self.profile_caregiver,progress_color=TEAL,
            button_color=TEAL,fg_color=self.p["panel2"],
            text_color=self.p["text"]).grid(
            row=2,column=0,columnspan=2,sticky="w",padx=10,pady=(6,13))
        self._label(scroll,"Dados pessoais",16,True,color=TEAL).grid(
            row=4,column=0,columnspan=2,sticky="w",padx=9,pady=(13,7))
        self._label(scroll,"Informação de saúde",16,True,color=TEAL).grid(
            row=12,column=0,columnspan=2,sticky="w",padx=9,pady=(13,7))
        self._label(scroll,"Morada e contactos",16,True,color=TEAL).grid(
            row=16,column=0,columnspan=2,sticky="w",padx=9,pady=(13,7))

        # Names/identifiers precisely correspond to editable Android fields.
        layout=[
            ("name",5,0,2,"Nome do perfil (nome curto)"),
            ("full_name",6,0,2,"Nome completo"),
            ("birth_date",7,0,1,"Data de nascimento (AAAA-MM-DD)"),
            ("gender",7,1,1,"Sexo / género"),
            ("height",8,0,1,"Altura (cm)"),
            ("nationality",8,1,1,"Nacionalidade"),
            ("cc_number",9,0,1,"N.º Cartão de Cidadão"),
            ("cc_valid_until",9,1,1,"Validade CC (DD/MM/AAAA)"),
            ("birth_place",10,0,2,"Naturalidade / Local de nascimento"),
            ("father",11,0,1,"Nome do pai"),
            ("mother",11,1,1,"Nome da mãe"),
            ("nif",13,0,1,"NIF"),
            ("sns_number",13,1,1,"N.º de utente SNS"),
            ("adse_number",14,0,1,"N.º ADSE"),
            ("niss",14,1,1,"NISS"),
            ("health_unit",15,0,2,"Unidade de saúde"),
            ("address",17,0,2,"Morada"),
            ("postal_code",18,0,1,"Código postal"),
            ("city",18,1,1,"Localidade"),
            ("phone",19,0,1,"Telemóvel / telefone pessoal"),
            ("email",19,1,1,"Email")
        ]
        for key,row,col,span,label in layout:
            self.profile_widgets[key]=self._text_field(
                scroll,label,fields.get(key,""),row,col,span)
        # Android's profile editor does not contain a generic notes field.
        # Medication notes and emergency notes belong to their own modules.

        footer=ctk.CTkFrame(frame,fg_color="transparent")
        footer.pack(fill="x",padx=16,pady=(0,9))
        self._button(footer,"✓  "+self.t("save"),self._save_profile,
                     True,width=155,height=42).pack(side="right")

    def _close_profile_editor(self):
        self.profile_edit_open=False
        self._render()

    def _refresh_photo(self):
        try:
            if self.photo_draft:
                image=Image.open(BytesIO(base64.b64decode(self.photo_draft))).convert("RGB")
                self.photo_preview=ctk.CTkImage(image,image,size=(140,140))
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
        # Preserve any old Windows-only note without copying medication notes.
        current=self.store.get_profile(self.editing_profile) if self.editing_profile else None
        fields["notes"]=current.get("notes","") if current else ""
        fields["photo_b64"]=self.photo_draft
        try:
            saved=self.store.save_profile(fields,self.editing_profile)
            self.active_id=saved["id"]
            self.editing_profile=saved["id"]
            self.store.update_settings(active_profile=self.active_id)
            self._render()
        except (LocalStoreError,ValueError) as exc:
            messagebox.showerror(self.t("profile_save_error"),str(exc),parent=self)

    def _med_photo_b64(self,med):
        """Recover this profile's Android medication photo from protected assets."""
        if med.get("photo_b64"):
            return med["photo_b64"]
        original=med.get("android_original")
        if not isinstance(original,dict) or not self.active_id:
            return ""
        refs=original.get("images")
        if not isinstance(refs,list):
            return ""
        candidates=set()
        for ref in refs:
            if isinstance(ref,str):
                name=ref.split("?")[0].replace(chr(92),"/").rsplit("/",1)[-1]
                if name and name not in (".",".."):
                    candidates.add(name)
        if not candidates:
            return ""
        cache=getattr(self,"_med_image_cache",None)
        if cache is None:
            self._med_image_cache={}
            cache=self._med_image_cache
        key=(self.active_id,med.get("id"))
        if key in cache:
            return cache[key]
        result=""
        for entry in self.store.imported_assets(self.active_id):
            if (entry.get("filename") not in candidates or
                    entry.get("category")!="fotografia de medicamento"):
                continue
            try:
                raw=self.store.read_imported_asset(entry)
                with Image.open(BytesIO(raw)) as image:
                    image=ImageOps.exif_transpose(image).convert("RGB")
                    image.thumbnail((750,750),Image.Resampling.LANCZOS)
                    out=BytesIO()
                    image.save(out,format="JPEG",quality=78,optimize=True)
                    if out.tell()<=450000:
                        result=base64.b64encode(out.getvalue()).decode("ascii")
                        break
            except (OSError,ValueError,LocalStoreError):
                continue
        cache[key]=result
        return result

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
        all_meds=self.store.get_profile(self.active_id).get("medications",[])
        total_suspended=sum(1 for m in all_meds if is_suspended(m))
        total_active_alerts=sum(1 for m in all_meds if active_reminder(m))
        total_configured=sum(1 for m in all_meds if configured_reminder(m))
        bar=ctk.CTkFrame(self.body,fg_color="transparent",height=35)
        bar.pack(fill="x",pady=(0,6))
        self._label(bar,self.t("medication_list"),15,True).pack(side="left",padx=(1,15))
        self._button(bar,"+ "+self.t("new_medication"),self._new_med,
                     True,width=160,height=32).pack(side="right",padx=(8,0))
        summary=(f"{len(all_meds)} medicamentos  ·  {total_suspended} suspensos  ·  "
                 f"{total_active_alerts} com aviso ativo  ·  {total_configured} com hora guardada")
        self._label(self.body,summary,12,color=self.p["muted"]).pack(anchor="w",pady=(0,6))
        # Keep the background inside every medicine card, not wallpaper glass.
        self.wallpaper_shell.glass_enabled=False
        query_var=ctk.StringVar(value=self.med_gallery_query)
        # No unlabelled/inert search rectangle over the wallpaper.
        search=None
        filters=ctk.CTkFrame(self.body,fg_color="transparent")
        filters.pack(fill="x",pady=(0,8))
        for key,label in (("all","Todos"),("active","Ativos"),("suspended","Suspensos"),
                          ("with_alarm","Com aviso"),("no_alarm","Sem alarme"),("undefined","Sem definição")):
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
            photo=self._med_card_photo(self._med_photo_b64(med),available,137)
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
                (med.get("dose"),reminder_clock(med) or med.get("time")) if x)
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

    def _compact_field(self,parent,label,initial,row,col,span=1):
        """Low-height clinical entry, consistent in both editor panels."""
        box=ctk.CTkFrame(parent,fg_color="transparent")
        box.grid(row=row,column=col,columnspan=span,sticky="ew",
                 padx=4,pady=(1,4))
        self._label(box,label,11,True,color=self.p["muted"]).pack(
            anchor="w",pady=(0,3))
        entry=ctk.CTkEntry(box,height=33,corner_radius=10,
            fg_color=self.p["field"],border_color="#315a66",
            border_width=1,text_color=self.p["text"],
            font=ctk.CTkFont(family="Segoe UI",size=12))
        entry.pack(fill="x")
        entry.insert(0,str(initial or ""))
        return entry

    def _editor_split(self,parent):
        """A scroll-free document panel beside a compact, tabbed editor."""
        split=ctk.CTkFrame(parent,fg_color="transparent")
        split.pack(fill="both",expand=True,padx=8,pady=(1,5))
        split.grid_rowconfigure(0,weight=1)
        split.grid_columnconfigure(0,weight=6,uniform="clinical")
        split.grid_columnconfigure(1,weight=4,uniform="clinical")
        left=ctk.CTkFrame(split,fg_color=self.p["panel"],
                          corner_radius=15,border_width=1,
                          border_color=self.p["line"])
        left.grid(row=0,column=0,sticky="nsew",padx=(0,6))
        right=ctk.CTkFrame(split,fg_color=self.p["panel"],
                           corner_radius=15,border_width=1,
                           border_color=self.p["line"])
        right.grid(row=0,column=1,sticky="nsew",padx=(6,0))
        return left,right

    def _med_form(self,frame,med):
        fields=med or {}
        self.med_photo_draft=self._med_photo_b64(fields)
        head=ctk.CTkFrame(frame,fg_color="transparent")
        head.pack(fill="x",padx=12,pady=(1,4))
        self._label(head,"Editar medicação" if med else "Nova medicação",
                    16,True).pack(side="left")
        self._back_button(head,"Voltar à medicação",self._back_to_med_gallery,
                     width=176).pack(side="right")
        left,right=self._editor_split(frame)
        tabs=self._editor_tabs(left)
        basic=tabs.add("Principal")
        for col in (0,1):basic.grid_columnconfigure(col,weight=1)
        self.med_widgets={}
        self.med_widgets["name"]=self._compact_field(
            basic,"Medicamento",fields.get("name",""),0,0,2)
        self.med_widgets["dose"]=self._compact_field(
            basic,"Dose",fields.get("dose",""),1,0)
        self.med_widgets["reminder_time"]=self._time_stepper(
            basic,"Hora de aviso (HH:MM)",reminder_clock(fields),1,1)
        # An old desktop edit can leave a second, conflicting HH:MM in time.
        # Never change the reminder automatically: the user chooses explicitly.
        old_clock=mismatched_legacy_clock(fields)
        if old_clock:
            clock_info=self.med_widgets["reminder_time"].master
            self._button(clock_info,"Usar hora anterior "+old_clock,
                lambda hhmm=old_clock:self._use_legacy_med_clock(hhmm),
                width=178,height=24).pack(anchor="e",pady=(3,0))
        self.med_widgets["indication"]=self._compact_field(
            basic,"Posologia / indicação",fields.get("indication",""),2,0,2)
        self.med_widgets["time"]=self._editable_choice(
            basic,"Condição da toma (ex.: jejum)",condition_value(fields),
            CONDITIONS,3,1)
        self.route_var=ctk.StringVar(value=next((key for key,value in ROUTES.items()
                     if value==fields.get("administration_route","")),"Não indicada"))
        self.injection_var=ctk.StringVar(value=next((key for key,value in INJECTIONS.items()
                     if value==fields.get("injection_type","")),"Não indicada"))
        self.take_var=ctk.StringVar(value=fields.get("dose_pattern",""))
        for label,variable,choices,row,col in (
            ("Tipo de toma",self.take_var,TAKES,3,0),
            ("Via de administração",self.route_var,list(ROUTES),4,0),
            ("Tipo de injeção",self.injection_var,list(INJECTIONS),4,1)):
            box=ctk.CTkFrame(basic,fg_color="transparent")
            box.grid(row=row,column=col,sticky="ew",padx=4,pady=3)
            self._label(box,label,10,True,color=self.p["muted"]).pack(
                anchor="w",pady=(0,2))
            ctk.CTkOptionMenu(box,variable=variable,values=list(choices),
                height=28,fg_color=self.p["field"],button_color=BLUE,
                dropdown_fg_color=self.p["panel2"],text_color=self.p["text"],
                dropdown_text_color=self.p["text"]).pack(fill="x")
        self.no_alarm_var=ctk.BooleanVar(value=is_no_alarm(fields))
        self.suspended_var=ctk.BooleanVar(value=is_suspended(fields))
        toggles=ctk.CTkFrame(basic,fg_color="transparent")
        toggles.grid(row=5,column=0,columnspan=2,sticky="w",pady=5)
        for key,var in (("Sem alarme",self.no_alarm_var),
                        ("Suspensa",self.suspended_var)):
            ctk.CTkSwitch(toggles,text=key,variable=var,
                progress_color=TEAL,button_color=TEAL,
                fg_color=self.p["panel2"],text_color=self.p["text"]).pack(
                    side="left",padx=(6,20))
        self._label(basic,"Notas",10,True,color=self.p["muted"]).grid(
            row=6,column=0,columnspan=2,sticky="w",padx=4)
        self.med_notes=ctk.CTkTextbox(basic,height=45,corner_radius=7,
            fg_color=self.p["field"],border_width=1,
            border_color=self.p["line"],text_color=self.p["text"])
        self.med_notes.grid(row=7,column=0,columnspan=2,sticky="ew",
                            padx=4,pady=(0,4))
        self.med_notes.insert("1.0",fields.get("notes",""))
        photo=ctk.CTkFrame(
            basic,fg_color=self.p["field"],corner_radius=12,
            border_width=1,border_color="#176d77")
        photo.grid(row=8,column=0,columnspan=2,sticky="ew",padx=4,pady=(8,4))
        self._med_preview_size=(max(280,min(535,self.winfo_width()//3)),166)
        self.med_photo_widget=ctk.CTkLabel(
            photo,text="Sem fotografia da embalagem",
            text_color=self.p["muted"],corner_radius=9,
            width=self._med_preview_size[0],height=self._med_preview_size[1])
        self.med_photo_widget.pack(side="left",padx=8,pady=7)
        controls=ctk.CTkFrame(photo,fg_color="transparent")
        controls.pack(side="left",fill="y",padx=(4,9),pady=8)
        self._button(controls,"Anexar foto\nda embalagem",
                     self._choose_med_photo,width=150,height=44).pack(
                         fill="x",pady=(8,9))
        self._button(controls,"Remover foto",self._remove_med_photo,
                     width=150,height=36).pack(fill="x",pady=(0,8))
        self._update_med_preview()

        self.med_extra_widgets={}
        self.med_doc_assets=medication_document_assets(
            self.store.imported_assets(self.active_id))
        self.med_doc_vars={}
        self.med_doc_choices={}
        self.med_doc_dropdowns={}
        for heading,entries in GROUPS:
            page=tabs.add(heading.replace(" e posologia",""))
            for col in (0,1):page.grid_columnconfigure(col,weight=1)
            for i,(key,label,_limit) in enumerate(entries):
                if key in EXTRA_COMBO_CHOICES:
                    self.med_extra_widgets[key]=self._editable_choice(
                        page,label,source_value(fields,key),
                        EXTRA_COMBO_CHOICES[key],i//2,i%2)
                else:
                    self.med_extra_widgets[key]=self._compact_field(
                        page,label,source_value(fields,key),i//2,i%2)
            if heading in ("Prescrição","Bula"):
                doc_key=("prescription_asset_sha256" if heading=="Prescrição"
                         else "leaflet_asset_sha256")
                row=1+(len(entries)+1)//2
                self._med_document_line(page,doc_key,fields.get(doc_key,""),row)
        self._build_document_panel(right,"medication",fields)
        footer=ctk.CTkFrame(frame,fg_color="transparent")
        footer.pack(fill="x",padx=13,pady=(2,6))
        self._button(footer,"✓  Guardar",self._save_med,True,
                     width=110,height=31).pack(side="right")
        self._button(footer,"×  Cancelar",self._back_to_med_gallery,
                     width=110,height=31).pack(side="right",padx=7)

    def _use_legacy_med_clock(self,hhmm):
        """Explicit choice when original and effective Windows clocks differ."""
        entry=self.med_widgets.get("reminder_time")
        if entry is None:return
        entry.delete(0,"end")
        entry.insert(0,hhmm)
        entry.focus_set()

    def _med_document_line(self,parent,key,selected,row):
        self._label(parent,"Documento da prescrição" if key.startswith("prescription")
                    else "Bula em PDF ou imagem",10,True,
                    color=self.p["muted"]).grid(row=row,column=0,
                    columnspan=2,sticky="w",padx=4,pady=(7,2))
        line=ctk.CTkFrame(parent,fg_color="transparent")
        line.grid(row=row+1,column=0,columnspan=2,sticky="ew",padx=4)
        choices={"Sem documento":""}
        for asset in self.med_doc_assets:
            name=str(asset.get("display_name") or asset.get("filename") or "Ficheiro")
            choices[f"{name[:38]} · {asset['sha256'][:8]}"]=asset["sha256"]
        self.med_doc_choices[key]=choices
        initial=next((label for label,digest in choices.items()
                      if digest and digest==selected),"Sem documento")
        variable=ctk.StringVar(value=initial)
        self.med_doc_vars[key]=variable
        dropdown=ctk.CTkOptionMenu(line,variable=variable,
            values=list(choices),height=28,fg_color=self.p["field"],
            button_color=BLUE,dropdown_fg_color=self.p["panel2"],
            text_color=self.p["text"],dropdown_text_color=self.p["text"])
        dropdown.pack(side="left",fill="x",expand=True,padx=(0,5))
        self.med_doc_dropdowns[key]=dropdown
        self._button(line,"Anexar",lambda k=key,m=dropdown:
                     self._attach_med_document(k,m),
                     width=74,height=28).pack(side="left",padx=2)
        self._button(line,"Ver",lambda k=key:self._show_attached_med_document(k),
                     width=49,height=28).pack(side="left",padx=2)

    def _build_document_panel(self,parent,kind,record):
        """Preview is fixed on the right; OCR is local and requires confirmation."""
        self._doc_context=(kind,self.active_id,
            self.editing_med if kind=="medication" else self.editing_appointment)
        self._doc_data=None
        self._doc_filename=""
        self._doc_current_entry=None
        self._doc_token=getattr(self,"_doc_token",0)+1
        self._label(parent,"DOCUMENTO E RECONHECIMENTO",14,True,
                    color=TEAL).pack(anchor="w",padx=12,pady=(10,3))
        self._label(parent,"O documento fica neste computador. "
                    "Revê sempre os valores antes de guardar.",
                    10,color=self.p["muted"],wrap=480).pack(
                        anchor="w",padx=12,pady=(0,6))
        row=ctk.CTkFrame(parent,fg_color="transparent")
        row.pack(fill="x",padx=11,pady=(0,5))
        if kind=="medication":
            self._doc_role=ctk.StringVar(value="Prescrição")
            ctk.CTkOptionMenu(row,variable=self._doc_role,
                values=["Prescrição","Bula"],
                command=lambda _v:self._show_attached_med_document(
                    "prescription_asset_sha256" if self._doc_role.get()=="Prescrição"
                    else "leaflet_asset_sha256"),
                height=28,fg_color=self.p["field"],button_color=BLUE,
                dropdown_fg_color=self.p["panel2"],text_color=self.p["text"],
                dropdown_text_color=self.p["text"]).pack(side="left",fill="x",expand=True)
        else:
            self._label(row,"Documento da marcação",11,True).pack(
                side="left",fill="x",expand=True)
        self._button(row,"Anexar",self._doc_attach,
                     width=78,height=28).pack(side="right",padx=(6,0))
        self._doc_filename_label=self._label(parent,"Sem documento associado",
                                             10,color=self.p["muted"],wrap=460)
        self._doc_filename_label.pack(anchor="w",padx=12,pady=(0,3))
        self._doc_preview_label=ctk.CTkLabel(parent,
            text="Pré-visualização do PDF ou imagem",
            fg_color=self.p["field"],corner_radius=8,
            text_color=self.p["muted"],height=205)
        self._doc_preview_label.pack(fill="x",padx=12,pady=(1,7))
        actions=ctk.CTkFrame(parent,fg_color="transparent")
        actions.pack(fill="x",padx=12,pady=(0,5))
        self._doc_recognize_btn=self._button(actions,"Reconhecer texto",
            self._doc_recognize,width=137,height=30)
        self._doc_recognize_btn.pack(side="left")
        self._button(actions,"Preencher campos",
            self._doc_apply,width=132,height=30).pack(side="left",padx=(7,0))
        self._doc_status=self._label(parent,"O OCR é local e não altera campos sem confirmação.",
                    10,color=self.p["muted"],wrap=470)
        self._doc_status.pack(anchor="w",padx=12,pady=(1,5))
        self._doc_text=ctk.CTkTextbox(parent,height=130,corner_radius=8,
            fg_color=self.p["field"],border_width=1,
            border_color=self.p["line"],text_color=self.p["text"])
        self._doc_text.pack(fill="both",expand=True,padx=12,pady=(0,11))
        if kind=="medication":
            self._show_attached_med_document("prescription_asset_sha256")
        elif record.get("document_asset_sha256"):
            match=medication_document_option(
                medication_document_assets(self.store.imported_assets(self.active_id)),
                record["document_asset_sha256"])
            if match is not None:self._doc_display(match)

    def _show_attached_med_document(self,key):
        self._doc_role.set("Prescrição" if key.startswith("prescription") else "Bula")
        mapping=self.med_doc_choices[key]
        digest=mapping.get(self.med_doc_vars[key].get(),"")
        entry=medication_document_option(self.med_doc_assets,digest) if digest else None
        self._doc_display(entry)

    def _doc_display(self,entry):
        self._doc_token+=1
        self._doc_data=None
        self._doc_current_entry=None
        self._doc_filename=""
        self._doc_text.delete("1.0","end")
        self._doc_preview_label.configure(image=None,text="Pré-visualização do documento")
        if entry is None:
            self._doc_filename_label.configure(text="Sem documento associado")
            self._doc_status.configure(text="Anexa um PDF ou uma imagem para reconhecer.")
            return
        try:
            raw=self.store.read_imported_asset(entry)
            filename=str(entry.get("filename") or "documento.pdf")
            image=Image.open(BytesIO(preview_document(raw,filename))).convert("RGB")
            image.thumbnail((440,245),Image.Resampling.LANCZOS)
            self._doc_preview_art=ctk.CTkImage(image,image,size=image.size)
            self._doc_preview_label.configure(image=self._doc_preview_art,text="")
            self._doc_data=raw
            self._doc_filename=filename
            self._doc_current_entry=entry
            self._doc_filename_label.configure(text=filename)
            self._doc_status.configure(text="Documento carregado. Clica em Reconhecer texto.")
        except (OSError,ValueError,LocalStoreError,DocumentRecognitionError) as exc:
            self._doc_filename_label.configure(text="Não foi possível abrir este documento")
            self._doc_status.configure(text=str(exc)[:150])

    def _doc_attach(self):
        if self._doc_context[0]=="medication":
            key=("prescription_asset_sha256" if self._doc_role.get()=="Prescrição"
                 else "leaflet_asset_sha256")
            self._attach_med_document(key,self.med_doc_dropdowns[key])
            return
        file=filedialog.askopenfilename(parent=self,title="Anexar PDF ou imagem do agendamento",
            filetypes=[("PDF ou imagem","*.pdf *.png *.jpg *.jpeg *.webp")])
        if not file:return
        try:
            from hashlib import sha256
            raw=Path(file).read_bytes()
            digest=sha256(raw).hexdigest()
            self.store.import_local_document(self.active_id,Path(file))
            assets=medication_document_assets(self.store.imported_assets(self.active_id))
            item=medication_document_option(assets,digest)
            if item is None:raise LocalStoreError("Documento não encontrado neste perfil.")
            self.appointment_doc_digest=digest
            self._doc_display(item)
        except (OSError,ValueError,LocalStoreError) as exc:
            messagebox.showerror("Documento do agendamento",str(exc),parent=self)

    def _doc_recognize(self):
        if self._doc_data is None:
            messagebox.showinfo("Reconhecimento","Anexa primeiro um documento.",parent=self)
            return
        raw=self._doc_data
        filename=self._doc_filename
        context=self._doc_context
        token=self._doc_token
        events=queue.Queue()
        self._doc_recognize_btn.configure(state="disabled")
        self._doc_status.configure(text="A reconhecer texto localmente...")
        def worker():
            try:
                recognized=recognize_document(raw,filename)
                events.put((token,context,recognized,None))
            except Exception as exc:
                events.put((token,context,"",str(exc)))
        threading.Thread(target=worker,daemon=True).start()
        self.after(140,lambda:self._doc_poll(events,token,context))

    def _doc_poll(self,events,token,context):
        if self._doc_token!=token or self._doc_context!=context:
            return
        expected="medication" if context[0]=="medication" else "agenda"
        if self.page!=expected or not self._doc_recognize_btn.winfo_exists():
            return
        try:
            _token,_context,text_value,error=events.get_nowait()
        except queue.Empty:
            self.after(140,lambda:self._doc_poll(events,token,context))
            return
        self._doc_recognize_btn.configure(state="normal")
        if error:
            self._doc_status.configure(text="Não foi possível reconhecer: "+error[:130])
            return
        self._doc_text.delete("1.0","end")
        self._doc_text.insert("1.0",text_value)
        self._doc_status.configure(text=("Texto encontrado. Confirma antes de preencher."
                           if text_value else "Não foi reconhecido texto. Podes inserir manualmente."))

    def _doc_apply(self):
        kind=self._doc_context[0]
        text_value=self._doc_text.get("1.0","end-1c")
        proposed=suggest_fields(kind,text_value)
        choices={}
        if kind=="medication":
            destinations={**self.med_widgets,**self.med_extra_widgets}
        else:
            destinations=self.appointment_widgets
        for key,value in proposed.items():
            field=destinations.get(key)
            if field is not None and not field.get().strip():
                choices[key]=(field,value)
        if not choices:
            messagebox.showinfo("Preencher campos",
                "Não há sugestões seguras para campos vazios. "
                "Podes copiar o texto reconhecido para os campos manualmente.",
                parent=self)
            return
        readable="\n".join(f"{key}: {value[:90]}" for key,(_,value) in choices.items())
        if not messagebox.askyesno("Confirmar sugestões OCR",
            "Os seguintes valores serão colocados APENAS em campos vazios:\n\n"
            +readable+"\n\nRevê tudo antes de guardar.",parent=self):
            return
        for field,value in choices.values():
            field.insert(0,value)
        self._doc_status.configure(text="Sugestões inseridas. Confirma todos os campos antes de guardar.")

    def _attach_med_document(self,key,dropdown):
        path=filedialog.askopenfilename(parent=self,title="Anexar documento à medicação",
            filetypes=[("PDF e imagens","*.pdf *.jpg *.jpeg *.png *.webp")])
        if not path:return
        try:
            from hashlib import sha256
            digest=sha256(Path(path).read_bytes()).hexdigest()
            self.store.import_local_document(self.active_id,Path(path))
            self.med_doc_assets=medication_document_assets(
                self.store.imported_assets(self.active_id))
            entry=medication_document_option(self.med_doc_assets,digest)
            if entry is None:
                raise LocalStoreError("Anexo não encontrado neste perfil.")
            label=f"{str(entry.get('display_name') or entry.get('filename'))[:60]} · {digest[:10]}"
            self.med_doc_choices[key][label]=digest
            dropdown.configure(values=list(self.med_doc_choices[key]))
            self.med_doc_vars[key].set(label)
            if hasattr(self,"_doc_role"):
                self._doc_display(entry)
                self._doc_role.set("Prescrição" if key.startswith("prescription") else "Bula")
        except (LocalStoreError,ValueError,OSError) as exc:
            messagebox.showerror("Medicação",str(exc),parent=self)

    def _export_med_document(self,key):
        digest=self.med_doc_choices[key].get(self.med_doc_vars[key].get(),"")
        entry=medication_document_option(self.med_doc_assets,digest) if digest else None
        if entry is None:
            messagebox.showinfo("Medicação","Seleciona primeiro um documento.",parent=self)
            return
        self._export_document(entry)

    def _update_med_preview(self):
        # The authentic stored package photo uses the space formerly empty in
        # the editor. Never use an unrelated stock/package photograph.
        width,height=getattr(self,"_med_preview_size",(330,166))
        image=self._med_card_photo(self.med_photo_draft,width,height)
        self._med_editor_image=image
        self.med_photo_widget.configure(
            image=image,text="" if image else "Sem fotografia da embalagem")

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
        try:
            fields.update(canonical_reminder_fields(
                fields.get("reminder_time",""),fields.get("time","")))
        except ValueError as exc:
            messagebox.showerror("Hora da medicação",str(exc),parent=self)
            return
        fields.update({key:entry.get() for key,entry in self.med_extra_widgets.items()})
        for key,var in self.med_doc_vars.items():
            fields[key]=self.med_doc_choices[key].get(var.get(),"")
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
        return LinksOptionsV087._settings_page(self)

    def _calendar(self):
        return CalendarSplitV087._calendar(self)

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
        """The only public Backup screen: Family / Profile .spbackup."""
        return render_backup(self)

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
            data["document_asset_sha256"]=self.appointment_doc_digest
            data["desktop_status"]=APPOINTMENT_STATES[self.appointment_status_var.get()]
            data["reminders_minutes"]=sorted(
                self.unlisted_reminder_offsets+
                [minutes for minutes,var in self.reminder_vars.items() if var.get()],
                reverse=True)
            for key,(entry,original) in self.appointment_extra_widgets.items():
                data[key]=parse_appointment_extra(key,entry.get(),original)
            self.store.save_appointment(self.active_id,data,self.editing_appointment)
            self._close_appointment()
        except (LocalStoreError,ValueError,KeyError) as exc:
            messagebox.showerror("Não foi possível guardar a marcação",str(exc),parent=self)

    def _appointment_form(self,person):
        """Readable appointments and documents; no raw Android JSON fields."""
        appointments=person.get("appointments",[])
        current=next((item for item in appointments
                      if item.get("id")==self.editing_appointment),
                     None) if self.editing_appointment else None
        if self.editing_appointment and current is None:
            self._close_appointment()
            return
        values=current or {}
        self.appointment_doc_digest=values.get("document_asset_sha256","")
        head=ctk.CTkFrame(self.body,fg_color="transparent")
        head.pack(fill="x",padx=12,pady=(1,4))
        self._label(head,"Editar marcação" if current else "Nova marcação",
                    16,True).pack(side="left")
        self._back_button(head,"Voltar à Agenda",self._close_appointment,
                     width=165).pack(side="right")
        left,right=self._editor_split(self.body)
        tabs=self._editor_tabs(left)
        primary=tabs.add("Marcação")
        contacts=tabs.add("Contactos")
        notes=tabs.add("Notas e avisos")
        for panel in (primary,contacts,notes):
            for col in (0,1):panel.grid_columnconfigure(col,weight=1)
        self.appointment_widgets={}
        self.appointment_extra_widgets={}  # Technical imported fields are never shown.
        labels=dict(APPOINTMENT_FIELDS)
        main_keys=("title","date","time","activity","type",
                   "specialty","unit","location","department","doctor","resource")
        secondary=("prescriber","reference","phone","email")
        for parent,keys in ((primary,main_keys),(contacts,secondary)):
            for index,key in enumerate(keys):
                initial=values.get(key,"")
                if key=="title" and not initial:
                    initial=values.get("activity") or values.get("name") or ""
                self.appointment_widgets[key]=self._compact_field(
                    parent,labels[key],initial,index//2,index%2)
        state=ctk.CTkFrame(primary,fg_color="transparent")
        state.grid(row=6,column=0,columnspan=2,sticky="ew",padx=4,pady=(9,2))
        self._label(state,"Estado da marcação",10,True,
                    color=self.p["muted"]).pack(side="left",padx=(0,8))
        current_state=appointment_status(values) if current else "pending"
        selected=next((label for label,status in APPOINTMENT_STATES.items()
                       if status==current_state),"Pendente")
        self.appointment_status_var=ctk.StringVar(value=selected)
        ctk.CTkOptionMenu(state,values=list(APPOINTMENT_STATES),
            variable=self.appointment_status_var,width=175,height=28,
            fg_color=self.p["panel2"],button_color=BLUE,
            dropdown_fg_color=self.p["panel2"],text_color=self.p["text"],
            dropdown_text_color=self.p["text"]).pack(side="left")
        self._label(primary,"Cancelar aqui não cancela a consulta no hospital.",
                    10,color=self.p["muted"]).grid(
                        row=7,column=0,columnspan=2,sticky="w",padx=4,pady=(2,0))
        configured=record_offsets(values) if current else list(REMINDER_DEFAULT)
        self.unlisted_reminder_offsets=[
            minute for minute in configured
            if minute not in {minute for minute,_ in REMINDER_CHOICES}]
        self.reminder_vars={}
        self._label(notes,"Avisos Windows",13,True,color=TEAL).grid(
            row=0,column=0,columnspan=2,sticky="w",pady=(4,8))
        for i,(minutes,label) in enumerate(REMINDER_CHOICES):
            var=ctk.BooleanVar(value=minutes in configured)
            self.reminder_vars[minutes]=var
            ctk.CTkCheckBox(notes,text=label,variable=var,
                checkbox_width=17,checkbox_height=17,
                fg_color=TEAL,hover_color=TEAL_HOVER,
                text_color=self.p["text"]).grid(
                    row=1+i//2,column=i%2,sticky="w",padx=7,pady=4)
        self._label(notes,"Descrição",10,True,color=self.p["muted"]).grid(
            row=4,column=0,columnspan=2,sticky="w",padx=4,pady=(10,2))
        self.appointment_description=ctk.CTkTextbox(notes,height=75,
            fg_color=self.p["field"],border_width=1,
            border_color=self.p["line"],text_color=self.p["text"])
        self.appointment_description.grid(
            row=5,column=0,columnspan=2,sticky="ew",padx=4)
        self.appointment_description.insert("1.0",str(values.get("description","") or ""))
        self._label(notes,"Notas",10,True,color=self.p["muted"]).grid(
            row=6,column=0,columnspan=2,sticky="w",padx=4,pady=(8,2))
        self.appointment_notes=ctk.CTkTextbox(notes,height=75,
            fg_color=self.p["field"],border_width=1,
            border_color=self.p["line"],text_color=self.p["text"])
        self.appointment_notes.grid(
            row=7,column=0,columnspan=2,sticky="ew",padx=4)
        self.appointment_notes.insert("1.0",str(values.get("notes","") or ""))
        self._build_document_panel(right,"appointment",values)
        footer=ctk.CTkFrame(self.body,fg_color="transparent")
        footer.pack(fill="x",padx=15,pady=(2,6))
        self._button(footer,"✓  Guardar alterações" if current else "✓  Guardar marcação",
                     self._save_appointment,True,width=170,height=31).pack(side="right")
        self._button(footer,"×  Cancelar",self._close_appointment,
                     width=105,height=31).pack(side="right",padx=7)

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
        return DocumentsV087._documents(self)

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
    """Launch the UI, the background agent, or a synthetic packaged OCR check."""
    if "--ocr-smoke" in sys.argv:
        _close_boot_splash()
        from PIL import ImageDraw, ImageFont
        test=Image.new("RGB",(1100,230),"white")
        painter=ImageDraw.Draw(test)
        try:font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",54)
        except OSError:font=ImageFont.load_default()
        painter.text((40,60),"DOSE: 25 mg",font=font,fill="black")
        stream=BytesIO()
        test.save(stream,format="PNG")
        extracted=recognize_document(stream.getvalue(),"synthetic.png")
        report=os.environ.get("SAUDEPRATICA_OCR_SMOKE_REPORT")
        if report:Path(report).write_text("OCR_READY" if extracted.strip() else "OCR_EMPTY",
                                        encoding="utf-8")
        if not extracted.strip():raise RuntimeError("Motor OCR não reconheceu texto.")
        return
    if "--reminder-agent" in sys.argv:
        _close_boot_splash()
        from windows.reminder_agent_v071 import run_reminder_agent
        run_reminder_agent()
        return
    import traceback
    app = None
    smoke_report = os.environ.get("SAUDEPRATICA_SMOKE_REPORT", "")
    try:
        app = Desktop()
        # Process and render the initial UI before marking the startup as good.
        app.update_idletasks()
        # One splash until the main window is ready, then reveal it maximized.
        _close_boot_splash()
        app.deiconify()
        try:
            app.state("zoomed")
        except tk.TclError:
            app.attributes("-zoomed",True)
        app.update()
        if smoke_report:
            # Real multi-page GUI check, not just a splash check. The runner
            # supplies an isolated LOCALAPPDATA directory and synthetic data.
            person=app.store.save_profile({"name":"Pessoa de teste",
                "caregiver":True, "health_unit":"Unidade fictícia"})
            app.active_id=person["id"]
            test_photo=Image.new("RGB",(520,230),(20,77,92))
            photo_buffer=BytesIO()
            test_photo.save(photo_buffer,format="JPEG")
            med=app.store.save_medication(person["id"],{
                "name":"Comprimido fictício","dose":"10 mg","time":"09:00",
                "reminder_time":"09:00",
                "administration_route":"oral","dose_pattern":"Jejum",
                "photo_b64":base64.b64encode(photo_buffer.getvalue()).decode("ascii")})
            for page in ("home","profiles","medication"):
                app.navigate(page)
                app.update_idletasks()
                app.update()
            app._edit_med(med["id"])
            app.update_idletasks()
            app.update()
            if app._med_editor_image is None:
                raise AssertionError("A fotografia real não apareceu ampliada.")
            if not isinstance(app.med_widgets["time"],ctk.CTkComboBox):
                raise AssertionError("Falta combobox editável de condições da toma.")
            if not all(isinstance(app.med_extra_widgets[k],ctk.CTkComboBox)
                       for k in ("frequency","repetitions","repeat_type")):
                raise AssertionError("Faltam listas editáveis nas Repetições.")
            app.med_widgets["time"].set("Jejum")
            app.med_extra_widgets["frequency"].set("1 vez ao dia")
            app.med_extra_widgets["repetitions"].set("Contínuo (sem fim)")
            app.med_extra_widgets["repeat_type"].set("Diária")
            app._adjust_med_time(app.med_widgets["reminder_time"],1)
            if app.med_widgets["reminder_time"].get()!="09:05":
                raise AssertionError("Setas do relógio não mudaram cinco minutos.")
            app._save_med()
            edited=next(x for x in app.store.get_profile(person["id"])["medications"]
                        if x["id"]==med["id"])
            if edited["reminder_time"]!="09:05" or edited["time"]!="Jejum":
                raise AssertionError("Hora e condição da toma não foram gravadas.")
            app._back_to_med_gallery()
            appointment=app.store.save_appointment(person["id"],{
                "title":"Consulta fictícia","date":"2027-02-14","time":"10:45",
                "location":"Hospital de teste","desktop_status":"pending"})
            app.navigate("agenda")
            app._open_appointment(appointment["id"])
            app.update_idletasks()
            app.update()
            app._close_appointment()
            # Windows 0.8.7: exercise the actual new Calendar and Takes UI,
            # with two separate synthetic profiles and no real patient data.
            from windows.doses_calendar_v085 import appointments_for_day, dose_entries
            app.calendar_selected=datetime(2027,2,14).date()
            app.navigate("calendar")
            app.update_idletasks()
            app.update()
            if len(appointments_for_day(app.store.get_profile(person["id"]),
                                        app.calendar_selected))!=1:
                raise AssertionError("Calendário não apresentou a marcação do perfil.")
            # The actual Tk cell for the selected day must be the turquoise,
            # appointment-coloured style and remain bound to this profile.
            from windows.calendar_ui_v086 import calendar_day_colors
            actual=app._calendar_day_cells.get(app.calendar_selected)
            expected=calendar_day_colors(
                has_appointments=True,selected=True,
                today=app.calendar_selected==datetime.now().date(),
                in_month=True,light=app.p["bg"]=="#edf4f7")
            if actual is None or actual.cget("fg_color")!=expected["background"]:
                raise AssertionError("O dia com marcação não está colorido.")
            app._calendar_choose(datetime(2027,2,13).date())
            app.update()
            if len(appointments_for_day(app.store.get_profile(person["id"]),
                                        app.calendar_selected))!=0:
                raise AssertionError("O dia vazio não foi respeitado.")
            app._calendar_choose(datetime(2027,2,14).date())
            app.update()
            confirmed=app.store.confirm_intake(person["id"],med["id"])
            app.dose_selected=datetime.now().date()
            app.navigate("doses")
            app.update_idletasks()
            app.update()
            if not any(x["status"]=="confirmed" for x in
                       dose_entries(app.store.get_profile(person["id"]),
                                    app.dose_selected)):
                raise AssertionError("Toma manual confirmada não aparece no perfil.")
            # Windows 0.8.8: exercise actual editors with synthetic values.
            app.navigate("clinical")
            app.update()
            app._health_fields["title"].insert(0,"Consulta clínica sintética")
            app._health_save("clinical")
            if len(app.store.health_records(person["id"],"clinical"))!=1:
                raise AssertionError("Situação Clínica não gravou neste perfil.")
            app.navigate("expenses")
            app.update()
            app._health_fields["merchant"].insert(0,"Prestador fictício")
            app._health_fields["amount_input"].delete(0,"end")
            app._health_fields["amount_input"].insert(0,"27,95")
            app._health_fields["refund_input"].delete(0,"end")
            app._health_fields["refund_input"].insert(0,"5,00")
            app._health_save("expenses")
            exp=app.store.health_records(person["id"],"expenses")
            if len(exp)!=1 or exp[0]["amountCents"]!=2795:
                raise AssertionError("Despesas não gravou cêntimos corretamente.")
            other=app.store.save_profile({"name":"Segundo perfil fictício"})
            app._select_profile_by_id(other["id"])
            app.navigate("calendar")
            app.update()
            app.navigate("doses")
            app.update()
            if (dose_entries(app.store.get_profile(other["id"]),app.dose_selected)
                or appointments_for_day(app.store.get_profile(other["id"]),
                                        app.calendar_selected)):
                raise AssertionError("Mistura de tomas ou agenda entre perfis.")
            app.navigate("clinical")
            app.update()
            app.navigate("expenses")
            app.update()
            if (app.store.health_records(other["id"],"clinical")
                or app.store.health_records(other["id"],"expenses")):
                raise AssertionError("Mistura de dados clínicos/despesas entre perfis.")
            app._select_profile_by_id(person["id"])
            # Windows 0.8.7: native split Documents with a real synthetic
            # JPEG and preview, then a larger internal view.
            synthetic_file=Path(os.environ["LOCALAPPDATA"])/"synthetic_preview.jpg"
            synthetic_file.write_bytes(photo_buffer.getvalue())
            app.store.import_local_document(person["id"],synthetic_file)
            synthetic_file.unlink()
            app.navigate("documents")
            app.update_idletasks()
            app.update()
            if not app._doc_entry_for_active():
                raise AssertionError("Pré-visualização de documentos sem seleção.")
            if not hasattr(app,"_doc_list_panel") or not hasattr(app,"_doc_preview_panel"):
                raise AssertionError("Documentos não têm dois painéis.")
            app._doc_open_viewer()
            app.update()
            if not app._doc_viewer_window or not app._doc_viewer_window.winfo_exists():
                raise AssertionError("Visualizador grande do documento não abriu.")
            app._doc_close_viewer()
            app.navigate("shortcuts")
            app.update()
            if len(app.store.important_links())!=2:
                raise AssertionError("Links SNS24 / IPO Lisboa ausentes.")
            app.navigate("options")
            app._link_title_var.set("Atalho sintético")
            app._link_url_var.set("https://example.org")
            app._options_link_save()
            if not any(x["title"]=="Atalho sintético" for x in app.store.important_links()):
                raise AssertionError("Gestor não gravou novo atalho.")
            app.navigate("info")
            app.update()
            app._set_med_filter("active")
            app.update()
            # Exercise the shared navigation/backup/document styles in the
            # same isolated Windows runner (no personal data or ZIPs).
            for module in ("documents","backup","more","import","sync"):
                app.navigate(module)
                app.update_idletasks()
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
        # Run the independent per-user reminder worker and configure its
        # next-login startup; the UI process may now close without stopping it.
        from windows.reminder_agent_v071 import enable_background_reminders
        try:enable_background_reminders()
        except (OSError,ImportError,PermissionError):pass
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
