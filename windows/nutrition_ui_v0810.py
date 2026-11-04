"""SaúdePrática Windows 0.8.10 nutrition diary with original Android food photos.

Manual meal entries are editable. A separate explicit operation reads the
already-protected complete Android backup for ONLY the active profile, and
imports its real meals and JPEGs without duplication. No invented nutrition
analysis or automatic photo recognition.
"""
from __future__ import annotations
from datetime import datetime,date
from io import BytesIO
from pathlib import Path
from tkinter import filedialog,messagebox
import customtkinter as ctk
from PIL import Image,ImageOps

from windows.secure_store import LocalStoreError
from windows.remaining_models_v0810 import MEAL_FIELDS


class NutritionUiV0810:
    def _nutrition_select(self,record_id):
        self._nutrition_selected=record_id
        self._nutrition_photo_draft=None
        self._render()

    def _nutrition_new(self):
        self._nutrition_selected=None
        self._nutrition_photo_draft=None
        self._render()

    def _nutrition_import_android(self):
        if not self.active_id:return
        if not messagebox.askyesno(
            "Importar refeições Android",
            "Importar apenas o diário e as fotografias originais do perfil "
            "Android associado ao perfil selecionado?\n\n"
            "A importação preserva registos já existentes e não envia "
            "fotografias nem dados pessoais para a Internet.",
            parent=self):
            return
        try:
            result=self.store.import_meal_diary_android(self.active_id)
            self._nutrition_selected=None
            self._nutrition_photo_draft=None
            self._render()
            messagebox.showinfo(
                "Nutrição",
                f"Refeições encontradas no backup: {result['available']}\n"
                f"Novas refeições: {result['added']}\n"
                f"Fotografias originais importadas: {result['photos']}\n\n"
                "Se o backup for antigo, poderá não conter as refeições "
                "adicionadas posteriormente no Android.",
                parent=self)
        except (OSError,ValueError,LocalStoreError) as exc:
            messagebox.showerror("Importação Android",str(exc),parent=self)

    def _nutrition_pick_photo(self):
        filename=filedialog.askopenfilename(
            parent=self,title="Fotografia da refeição",
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.webp")])
        if not filename:return
        try:
            path=Path(filename)
            if not path.is_file() or path.stat().st_size>8*1024*1024:
                raise ValueError("Fotografia inválida ou superior a 8 MB.")
            data=path.read_bytes()
            with Image.open(BytesIO(data)) as src:
                if src.width*src.height>25_000_000 or src.format not in (
                    "JPEG","PNG","WEBP"):
                    raise ValueError("Formato ou tamanho de fotografia inválido.")
                src.verify()
            self._nutrition_photo_draft=data
            self._nutrition_show_picture(data)
        except (OSError,ValueError) as exc:
            messagebox.showerror("Fotografia",str(exc),parent=self)

    def _nutrition_show_picture(self,raw):
        if not hasattr(self,"_nutrition_photo_label"):return
        try:
            with Image.open(BytesIO(raw)) as base:
                image=ImageOps.exif_transpose(base).convert("RGB")
                image.thumbnail((305,180),Image.Resampling.LANCZOS)
            picture=ctk.CTkImage(image,image,size=image.size)
            self._nutrition_image_ref=picture
            self._nutrition_photo_label.configure(image=picture,text="")
        except (OSError,ValueError):
            self._nutrition_photo_label.configure(image=None,text="Fotografia indisponível")

    def _nutrition_save(self):
        if not self.active_id:return
        try:
            values={}
            for key,(widget,typ) in self._nutrition_fields.items():
                values[key]=(widget.get("1.0","end-1c") if typ=="long"
                             else widget.get().strip())
            for number in ("kcal","protein_g","carbs_g","fat_g"):
                if not values.get(number):
                    values[number]="0"
            item=self.store.save_meal(
                self.active_id,values,
                getattr(self,"_nutrition_selected",None),
                getattr(self,"_nutrition_photo_draft",None))
            self._nutrition_selected=item["id"]
            self._nutrition_photo_draft=None
            self._render()
        except (LocalStoreError,ValueError,OSError) as exc:
            messagebox.showerror("Guardar refeição",str(exc),parent=self)

    def _nutrition_remove(self,record_id):
        if not messagebox.askyesno(
            "Apagar refeição",
            "Remover esta refeição do diário deste perfil?\n"
            "A fotografia protegida não é enviada nem partilhada.",
            parent=self):
            return
        try:
            self.store.delete_meal(self.active_id,record_id)
            self._nutrition_selected=None
            self._nutrition_photo_draft=None
            self._render()
        except (LocalStoreError,OSError) as exc:
            messagebox.showerror("Nutrição",str(exc),parent=self)

    def _nutrition_field(self,parent,key,label,value,*,large=False):
        container=ctk.CTkFrame(parent,fg_color="transparent")
        container.pack(fill="x",padx=10,pady=(2,5))
        self._label(container,label,11,True,color=self.p["muted"]).pack(
            anchor="w",pady=(0,3))
        if large:
            widget=ctk.CTkTextbox(
                container,height=70,fg_color=self.p["field"],
                text_color=self.p["text"],border_width=1,
                border_color=self.p["line"])
            widget.insert("1.0",str(value or ""))
            widget.pack(fill="x")
            typ="long"
        else:
            widget=ctk.CTkEntry(container,height=33,
                                fg_color=self.p["field"],
                                text_color=self.p["text"],
                                border_color=self.p["line"])
            widget.insert(0,str(value or ""))
            widget.pack(fill="x")
            typ="text"
        self._nutrition_fields[key]=(widget,typ)

    def _nutrition(self):
        self.wallpaper_shell.glass_enabled=False
        person=self.store.get_profile(self.active_id) if self.active_id else None
        self._heading("Nutrição",
            "Diário de refeições e fotografias do perfil: "+str(person.get("name",""))
            if person else "Seleciona um perfil.")
        if person is None:return
        records=self.store.meal_records(person["id"])
        current=next((r for r in records if r.get("id")==
                      getattr(self,"_nutrition_selected",None)),None)
        if getattr(self,"_nutrition_selected",None) and current is None:
            self._nutrition_selected=None
        data=current or {}
        split=ctk.CTkFrame(self.body,fg_color="transparent")
        split.pack(fill="both",expand=True,padx=(6,7),pady=(0,6))
        split.grid_rowconfigure(0,weight=1)
        split.grid_columnconfigure(0,weight=9,uniform="nutrition")
        split.grid_columnconfigure(1,weight=11,uniform="nutrition")
        left=ctk.CTkFrame(split,fg_color=self.p["panel"],
                          corner_radius=14,border_width=1,
                          border_color=self.p["line"])
        right=ctk.CTkFrame(split,fg_color=self.p["panel"],
                           corner_radius=14,border_width=1,
                           border_color=self.p["line"])
        left.grid(row=0,column=0,sticky="nsew",padx=(0,7))
        right.grid(row=0,column=1,sticky="nsew",padx=(7,0))
        self._nutrition_panels=(left,right)
        top=ctk.CTkFrame(left,fg_color="transparent")
        top.pack(fill="x",padx=12,pady=(11,7))
        self._label(top,f"Diário · {len(records)} refeições",16,True).pack(side="left")
        self._button(top,"+ Nova",self._nutrition_new,
                     True,width=91,height=33).pack(side="right")
        self._label(left,
            "As refeições e fotografias do backup Android são restauradas "
            "automaticamente e mantidas no perfil correto.",
            11,color=self.p["muted"],wrap=450).pack(
                anchor="w",padx=13,pady=(0,10))
        scroll=ctk.CTkScrollableFrame(left,fg_color="transparent")
        scroll.pack(fill="both",expand=True,padx=6,pady=(0,9))
        if not records:
            self._label(scroll,
                        "Ainda não há refeições importadas ou registadas neste perfil.",
                        13,color=self.p["muted"],wrap=430).pack(
                            anchor="w",padx=11,pady=13)
        for row in records:
            selected=current is not None and row.get("id")==current.get("id")
            tile=ctk.CTkFrame(
                scroll,fg_color=self.p["panel2"],corner_radius=10,
                border_width=2 if selected else 1,
                border_color="#00c9b7" if selected else self.p["line"])
            tile.pack(fill="x",padx=3,pady=4)
            item=ctk.CTkFrame(tile,fg_color="transparent")
            item.pack(fill="x",padx=9,pady=8)
            # Miniatura verdadeira à esquerda, sempre do perfil em consulta.
            if row.get("photo_sha256"):
                try:
                    raw=self.store.meal_photo(person["id"],row["id"])
                    if raw:
                        with Image.open(BytesIO(raw)) as source:
                            source.thumbnail((320,320))
                            thumb=ImageOps.fit(
                                source.convert("RGB"),(76,76),
                                method=Image.Resampling.LANCZOS)
                        preview_image=ctk.CTkImage(
                            light_image=thumb,dark_image=thumb,size=(76,76))
                        preview=ctk.CTkLabel(
                            item,text="",image=preview_image,width=80,height=80)
                        preview.image=preview_image
                        preview.pack(side="left",padx=(0,10))
                except (OSError,ValueError,LocalStoreError):
                    pass
            details=ctk.CTkFrame(item,fg_color="transparent")
            details.pack(side="left",fill="both",expand=True)
            stamp=str(row.get("date",""))+" · "+str(row.get("clock",""))
            self._label(details,
                f"{stamp}  ·  {row.get('meal') or 'Refeição'}",
                12,True).pack(anchor="w",pady=(0,3))
            foods=str(row.get("foods",""))
            if foods:
                self._label(details,foods[:150],11,color=self.p["muted"],
                            wrap=320).pack(anchor="w",pady=(0,5))
            foot=ctk.CTkFrame(details,fg_color="transparent")
            foot.pack(fill="x")
            energy=row.get("kcal",0)
            hint=(f"{energy:g} kcal" if isinstance(energy,(int,float)) and energy>0
                  else "Energia não informada")
            if row.get("photo_sha256"):hint+=" · Foto"
            if row.get("source")=="android":hint+=" · Android"
            self._label(foot,hint,10,color=self.p["muted"]).pack(side="left")
            self._button(foot,"Abrir",
                         lambda uid=row.get("id"):self._nutrition_select(uid),
                         width=63,height=28).pack(side="right")
        header=ctk.CTkFrame(right,fg_color="transparent")
        header.pack(fill="x",padx=13,pady=(11,7))
        self._label(header,"Editar refeição" if current else "Nova refeição",
                    16,True).pack(side="left")
        self._button(header,"Guardar",self._nutrition_save,
                     True,width=102,height=33).pack(side="right")
        if current:
            self._button(header,"Remover",
                         lambda uid=current["id"]:self._nutrition_remove(uid),
                         width=83,height=33).pack(side="right",padx=6)
        form=ctk.CTkScrollableFrame(right,fg_color="transparent")
        form.pack(fill="both",expand=True,padx=8,pady=(0,10))
        image_box=ctk.CTkFrame(form,fg_color=self.p["panel2"],
                               corner_radius=11)
        image_box.pack(fill="x",padx=10,pady=(1,8))
        self._label(image_box,"Fotografia da refeição",12,True).pack(
            anchor="w",padx=12,pady=(9,5))
        self._nutrition_photo_label=ctk.CTkLabel(
            image_box,text="Sem fotografia",height=100)
        self._nutrition_photo_label.pack(padx=10,pady=(0,8))
        photo=getattr(self,"_nutrition_photo_draft",None)
        if photo is None and current and current.get("photo_sha256"):
            try:photo=self.store.meal_photo(person["id"],current["id"])
            except (OSError,ValueError,LocalStoreError):photo=None
        if photo:self._nutrition_show_picture(photo)
        self._button(image_box,"Escolher fotografia",
                     self._nutrition_pick_photo,width=186,height=31).pack(
                         anchor="w",padx=11,pady=(0,11))
        self._nutrition_fields={}
        self._nutrition_field(form,"date","Data (DD/MM/AAAA)",
                              data.get("date",date.today().strftime("%d/%m/%Y")))
        self._nutrition_field(form,"clock","Hora (HH:MM)",
                              data.get("clock",datetime.now().strftime("%H:%M")))
        for key,label,limit in MEAL_FIELDS:
            value=data.get(key,"")
            self._nutrition_field(form,key,label,value,
                                  large=key in ("foods","note"))
        if data.get("source")=="android":
            self._label(form,
                "Registo originalmente guardado no Android. A foto e os "
                "valores não foram recalculados no Windows.",
                11,color=self.p["muted"],wrap=450).pack(
                    anchor="w",padx=12,pady=(5,7))
        self._label(form,
            "As calorias e macronutrientes são valores introduzidos ou "
            "estimados pelo utilizador/Android; não são análises clínicas. "
            "O Windows não faz reconhecimento nutricional automático.",
            11,color=self.p["muted"],wrap=470).pack(
                anchor="w",padx=12,pady=(6,12))
