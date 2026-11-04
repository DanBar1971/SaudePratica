"""Windows 0.8.9 Atividade e Saúde: clearly labelled manual records.

Health Connect is Android-only; no implied reading from a phone or wearable.
"""
from __future__ import annotations

from datetime import date,timedelta
from decimal import Decimal,InvalidOperation
import re
from tkinter import messagebox
import customtkinter as ctk

from windows.secure_store import LocalStoreError
from windows.wellness_models_v089 import ACTIVITY_LABELS, weekly_series


METRICS = (
    ("steps","👣 Passos","Ex.: 6500"),
    ("distance_km","📍 Distância (km)","Ex.: 4,5"),
    ("active_kcal","🔥 Energia ativa (kcal)","Ex.: 320"),
    ("sleep_hm","🌙 Sono (horas:minutos)","Ex.: 7:30"),
    ("heart_bpm","❤️ Ritmo cardíaco médio (bpm)","Ex.: 70"),
    ("weight_kg","⚖ Peso (kg)","Ex.: 72,4"),
    ("systolic","Tensão sistólica (mmHg)","Ex.: 120"),
    ("diastolic","Tensão diastólica (mmHg)","Ex.: 80"),
)
INTS={"steps","active_kcal","heart_bpm","systolic","diastolic"}


def _decimal_thousand(value: str) -> int:
    if not isinstance(value,str) or not re.fullmatch(r"\d+(?:[,.]\d{1,3})?",value.strip()):
        raise ValueError("Utiliza um número positivo, até três casas decimais.")
    try:
        result=Decimal(value.replace(",","."))*1000
        return int(result)
    except (InvalidOperation,OverflowError) as exc:
        raise ValueError("Número inválido.") from exc


def parse_activity_fields(widgets: dict, notes: str, day: date) -> dict:
    data={"date":day.isoformat(),"notes":notes}
    for key,_,_ in METRICS:
        raw=widgets[key].get().strip()
        if not raw:
            continue
        if key in INTS:
            data[key]=raw
        elif key=="distance_km":
            data["distance_m"]=_decimal_thousand(raw)
        elif key=="weight_kg":
            data["weight_grams"]=_decimal_thousand(raw)
        elif key=="sleep_hm":
            if not re.fullmatch(r"\d{1,2}:\d{2}",raw):
                raise ValueError("Sono: utiliza horas:minutos (por exemplo, 7:30).")
            h,m=map(int,raw.split(":"))
            if m>=60:
                raise ValueError("Os minutos de sono devem ser de 00 a 59.")
            data["sleep_minutes"]=h*60+m
    return data


def activity_display(item: dict, name: str) -> str:
    source={"distance_km":"distance_m","weight_kg":"weight_grams",
            "sleep_hm":"sleep_minutes"}.get(name,name)
    value=item.get(source)
    if value is None:
        return ""
    if name=="distance_km":
        result=Decimal(item["distance_m"])/1000
        return format(result,"f").rstrip("0").rstrip(".").replace(".",",") or "0"
    if name=="weight_kg":
        result=Decimal(item["weight_grams"])/1000
        return format(result,"f").rstrip("0").rstrip(".").replace(".",",") or "0"
    if name=="sleep_hm":
        minutes=item["sleep_minutes"]
        return f"{minutes//60}:{minutes%60:02d}"
    return str(value)


class ActivityUiV089:
    def _activity_select(self,day: date):
        if day<=date.today():
            self.activity_day=day
            self._render()

    def _activity_move(self,offset: int):
        current=getattr(self,"activity_day",date.today())
        self._activity_select(current+timedelta(days=offset))

    def _activity_save(self):
        profile=self.store.get_profile(self.active_id) if self.active_id else None
        if not profile:
            return
        try:
            record=parse_activity_fields(self._activity_fields,
                                         self._activity_notes.get("1.0","end-1c"),
                                         self.activity_day)
            self.store.save_activity_day(profile["id"],record)
            self._render()
        except (ValueError,LocalStoreError,OSError) as exc:
            messagebox.showerror("Atividade e Saúde",str(exc),parent=self)

    def _activity_delete(self):
        if not messagebox.askyesno(
            "Apagar medições",
            "Queres remover os valores registados neste dia?\n"
            "Os registos dos restantes dias ficam guardados.",
            parent=self):
            return
        try:
            self.store.delete_activity_day(self.active_id,
                                           self.activity_day.isoformat())
            self._render()
        except (LocalStoreError,OSError) as exc:
            messagebox.showerror("Atividade e Saúde",str(exc),parent=self)

    def _activity(self):
        self.wallpaper_shell.glass_enabled=False
        person=self.store.get_profile(self.active_id) if self.active_id else None
        self._heading("Atividade e Saúde",
                      "Medições manuais do perfil: "+str(person.get("name",""))
                      if person else "Seleciona um perfil.")
        if not person:
            return
        if not isinstance(getattr(self,"activity_day",None),date):
            self.activity_day=date.today()
        day=self.activity_day
        entries=self.store.wellness_data(person["id"],"activity")["entries"]
        selected=next((x for x in entries if x.get("date")==day.isoformat()),{})
        recent=sorted(entries,key=lambda r:r.get("date",""),reverse=True)
        main=ctk.CTkFrame(self.body,fg_color="transparent")
        main.pack(fill="both",expand=True,padx=(5,7),pady=(0,6))
        main.grid_rowconfigure(0,weight=1)
        main.grid_columnconfigure(0,weight=9,uniform="activity")
        main.grid_columnconfigure(1,weight=11,uniform="activity")
        left=ctk.CTkFrame(main,fg_color=self.p["panel"],
                          border_color=self.p["line"],border_width=1,
                          corner_radius=14)
        right=ctk.CTkFrame(main,fg_color=self.p["panel"],
                           border_color=self.p["line"],border_width=1,
                           corner_radius=14)
        left.grid(row=0,column=0,sticky="nsew",padx=(0,7))
        right.grid(row=0,column=1,sticky="nsew",padx=(7,0))
        self._activity_left=left
        self._activity_right=right
        self._label(left,"Resumo de atividade",17,True).pack(
            anchor="w",padx=14,pady=(12,4))
        self._label(left,
            "Os dados são introduzidos manualmente. Ainda não existe "
            "ligação do Windows ao Health Connect do Android.",
            11,color=self.p["muted"],wrap=465).pack(
                anchor="w",padx=14,pady=(0,13))
        summary=ctk.CTkFrame(left,fg_color=self.p["panel2"],corner_radius=11)
        summary.pack(fill="x",padx=11,pady=(0,10))
        self._label(summary,f"{day:%d/%m/%Y}",16,True,
                    color="#00c9b7").pack(anchor="w",padx=12,pady=(11,4))
        labels=(
            ("steps","👣 Passos",""),
            ("distance_m","📍 Distância"," m"),
            ("sleep_minutes","🌙 Sono"," min"),
            ("heart_bpm","❤️ Ritmo cardíaco médio"," bpm"),
            ("active_kcal","🔥 Energia ativa"," kcal"),
        )
        for key,desc,unit in labels:
            value=selected.get(key)
            self._label(summary,
                desc+": "+(f"{value}{unit}" if value is not None else "sem registo"),
                12,color=self.p["text"]).pack(anchor="w",padx=14,pady=2)
        self._label(summary,"",8).pack(pady=2)

        self._label(left,"Passos · últimos 7 dias",14,True).pack(
            anchor="w",padx=15,pady=(3,7))
        series=weekly_series(entries,"steps",day.isoformat())
        max_steps=max([v for _,v in series if v is not None]+[1])
        bars=ctk.CTkFrame(left,fg_color="transparent")
        bars.pack(fill="x",padx=15,pady=(0,10))
        for i,(day_text,value) in enumerate(series):
            bars.grid_columnconfigure(i,weight=1,uniform="actweek")
            part=ctk.CTkFrame(bars,fg_color="transparent")
            part.grid(row=0,column=i,sticky="nsew",padx=2)
            self._label(part,day_text[8:10],10,anchor="center",
                        color=self.p["muted"]).pack()
            bar=ctk.CTkProgressBar(
                part,orientation="vertical",height=57,width=14,
                fg_color=self.p["panel2"],progress_color="#00c9b7")
            bar.pack(pady=(5,3))
            bar.set((value or 0)/max_steps)
            self._label(part,str(value) if value is not None else "—",
                        10,anchor="center").pack()

        original_measurements=person.get("android_health_measurements",[])
        if isinstance(original_measurements,list) and original_measurements:
            self._label(left,"Medições originais do Android",14,True).pack(
                anchor="w",padx=15,pady=(0,5))
            original_box=ctk.CTkFrame(left,fg_color=self.p["panel2"],
                                      corner_radius=10)
            original_box.pack(fill="x",padx=12,pady=(0,10))
            for event in sorted(
                [x for x in original_measurements if isinstance(x,dict)],
                key=lambda x:x.get("date",""),reverse=True)[:5]:
                self._label(original_box,
                    str(event.get("date",""))+" · "+
                    str(event.get("title","Medição"))[:60]+" · "+
                    str(event.get("value",""))[:30]+" "+
                    str(event.get("unit",""))[:25],
                    11,True,wrap=440).pack(anchor="w",padx=10,pady=(6,2))
            self._label(original_box,
                "Registos manuais de saúde importados, separados das "
                "medições automáticas Health Connect.",
                10,color=self.p["muted"],wrap=440).pack(
                    anchor="w",padx=10,pady=(5,9))
        self._label(left,"Histórico registado",14,True).pack(
            anchor="w",padx=15,pady=(0,5))
        listbox=ctk.CTkScrollableFrame(left,fg_color="transparent")
        listbox.pack(fill="both",expand=True,padx=6,pady=(0,9))
        if not recent:
            self._label(listbox,"Ainda não existem medições manuais.",
                        12,color=self.p["muted"]).pack(
                            anchor="w",padx=9,pady=13)
        for item in recent:
            cell=ctk.CTkFrame(listbox,fg_color=self.p["panel2"],
                              corner_radius=9)
            cell.pack(fill="x",padx=4,pady=3)
            d=date.fromisoformat(item["date"])
            count=sum(item.get(k) is not None for k in
                      ("steps","distance_m","sleep_minutes","active_kcal",
                       "heart_bpm","weight_grams","systolic","diastolic"))
            self._label(cell,f"{d:%d/%m/%Y}  ·  {count} medições",
                        12,True).pack(side="left",padx=11,pady=9)
            self._button(cell,"Ver / Editar",
                         lambda chosen=d:self._activity_select(chosen),
                         width=106,height=29).pack(side="right",padx=8)

        scroller=ctk.CTkScrollableFrame(right,fg_color="transparent")
        scroller.pack(fill="both",expand=True,padx=9,pady=(10,8))
        top=ctk.CTkFrame(scroller,fg_color="transparent")
        top.pack(fill="x",padx=7,pady=(0,9))
        self._label(top,"Registo do dia",17,True).pack(side="left")
        ctrl=ctk.CTkFrame(top,fg_color="transparent")
        ctrl.pack(side="right")
        self._button(ctrl,"‹",lambda:self._activity_move(-1),
                     width=37,height=30).pack(side="left")
        self._label(ctrl,f"{day:%d/%m/%Y}",12,True).pack(
            side="left",padx=8)
        self._button(ctrl,"›",lambda:self._activity_move(+1),
                     width=37,height=30).pack(side="left")
        self._button(ctrl,"Hoje",lambda:self._activity_select(date.today()),
                     width=62,height=30).pack(side="left",padx=(5,0))
        self._activity_fields={}
        for label_keys in (METRICS[:4],METRICS[4:]):
            grid=ctk.CTkFrame(scroller,fg_color="transparent")
            grid.pack(fill="x",padx=8,pady=(0,1))
            grid.grid_columnconfigure(0,weight=1,uniform="activityfields")
            grid.grid_columnconfigure(1,weight=1,uniform="activityfields")
            for i,(key,label,hint) in enumerate(label_keys):
                container=ctk.CTkFrame(grid,fg_color="transparent")
                container.grid(row=i//2,column=i%2,sticky="ew",padx=5,pady=5)
                self._label(container,label,11,True,
                            color=self.p["muted"]).pack(anchor="w",pady=(0,3))
                field=ctk.CTkEntry(
                    container,height=34,fg_color=self.p["field"],
                    text_color=self.p["text"],placeholder_text=hint,
                    border_color=self.p["line"])
                field.insert(0,activity_display(selected,key))
                field.pack(fill="x")
                self._activity_fields[key]=field
        self._label(scroller,"Observações opcionais",11,
                    True,color=self.p["muted"]).pack(
                        anchor="w",padx=15,pady=(7,3))
        self._activity_notes=ctk.CTkTextbox(
            scroller,height=90,fg_color=self.p["field"],
            text_color=self.p["text"],border_color=self.p["line"],
            border_width=1,wrap="word")
        self._activity_notes.pack(fill="x",padx=13)
        self._activity_notes.insert("1.0",selected.get("notes",""))
        bottom=ctk.CTkFrame(scroller,fg_color="transparent")
        bottom.pack(fill="x",padx=13,pady=(11,12))
        self._button(bottom,"Guardar medições",
                     self._activity_save,True,width=168,height=36).pack(
                         side="left",padx=(0,7))
        if selected.get("id"):
            self._button(bottom,"Apagar dia",self._activity_delete,
                         width=120,height=36).pack(side="left")
        self._label(scroller,
            "Valores manuais, sem acesso automático a passos, sono ou "
            "sensores. Esta app não interpreta medições nem substitui "
            "acompanhamento médico.",
            11,color=self.p["muted"],wrap=490).pack(
                anchor="w",padx=14,pady=(0,13))
