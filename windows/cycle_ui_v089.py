"""SaúdePrática Windows 0.8.9 menstrual calendar + explicit pill acknowledgements.

Cycle projection is only approximate. It is not an ovulation, fertility,
contraception, pregnancy or medication scheduling recommendation.
"""
from __future__ import annotations

import calendar
from datetime import date,timedelta
from tkinter import messagebox
import customtkinter as ctk

from windows.secure_store import LocalStoreError
from windows.wellness_models_v089 import (
    PILL_PATTERNS, estimated_next_period, pill_scheduled,
)


MONTHS=("Janeiro","Fevereiro","Março","Abril","Maio","Junho",
        "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro")
WEEKDAYS=("Seg","Ter","Qua","Qui","Sex","Sáb","Dom")


class CycleUiV089:
    def _cycle_pick(self,chosen: date):
        self.cycle_day=chosen
        self.cycle_month=chosen.replace(day=1)
        self._render()

    def _cycle_move(self,offset):
        first=getattr(self,"cycle_month",date.today().replace(day=1))
        index=first.year*12+first.month-1+offset
        year,month=divmod(index,12)
        if not 1900<=year<=9999:
            return
        self.cycle_month=date(year,month+1,1)
        self.cycle_day=self.cycle_month
        self._render()

    def _cycle_save_settings(self):
        if not self.active_id:
            return
        try:
            label=self._cycle_pattern.get()
            selected=PILL_PATTERNS[label]
            value={
                "cycle_days":self._cycle_days.get().strip(),
                "pill_pattern":selected,
                "pill_start":self._cycle_pill_start.get().strip(),
                "pill_time":self._cycle_pill_time.get().strip(),
            }
            self.store.set_cycle_settings(self.active_id,value)
            self._render()
        except (KeyError,ValueError,LocalStoreError,OSError) as exc:
            messagebox.showerror("Configurar ciclo",str(exc),parent=self)

    def _cycle_add_period(self):
        if not self.active_id:
            return
        try:
            self.store.add_cycle_period(
                self.active_id,
                self._cycle_start.get().strip(),
                self._cycle_end.get().strip(),
                self._cycle_note.get("1.0","end-1c"))
            self._render()
        except (ValueError,LocalStoreError,OSError) as exc:
            messagebox.showerror("Registar período",str(exc),parent=self)

    def _cycle_delete(self,identifier):
        if not messagebox.askyesno(
            "Remover período",
            "Remover este período registado? Outros registos não serão alterados.",
            parent=self):
            return
        try:
            self.store.delete_cycle_period(self.active_id,identifier)
            self._render()
        except (LocalStoreError,OSError) as exc:
            messagebox.showerror("Ciclo Menstrual",str(exc),parent=self)

    def _cycle_mark_pill(self,day: date,taken: bool):
        if day>date.today():
            return
        if taken and not messagebox.askyesno(
            "Confirmar toma de pílula",
            f"Confirma que a pílula foi realmente tomada em "
            f"{day:%d/%m/%Y}?\nEsta ação grava uma confirmação manual.",
            parent=self):
            return
        if not taken and not messagebox.askyesno(
            "Anular confirmação",
            "Retirar o registo de pílula tomada neste dia?",parent=self):
            return
        try:
            self.store.set_pill_taken(self.active_id,day.isoformat(),taken)
            self._render()
        except (ValueError,LocalStoreError,OSError) as exc:
            messagebox.showerror("Ciclo Menstrual",str(exc),parent=self)

    def _cycle_field(self,parent,label,value):
        row=ctk.CTkFrame(parent,fg_color="transparent")
        row.pack(fill="x",padx=8,pady=(3,6))
        self._label(row,label,11,True,color=self.p["muted"]).pack(
            anchor="w",pady=(0,3))
        field=ctk.CTkEntry(
            row,height=33,fg_color=self.p["field"],
            border_color=self.p["line"],text_color=self.p["text"])
        field.insert(0,str(value or ""))
        field.pack(fill="x")
        return field

    def _cycle(self):
        self.wallpaper_shell.glass_enabled=False
        person=self.store.get_profile(self.active_id) if self.active_id else None
        self._heading("Ciclo Menstrual",
                      "Registo pessoal do perfil: " + str(person.get("name",""))
                      if person else "Seleciona primeiro um perfil.")
        if not person:
            return
        if not isinstance(getattr(self,"cycle_month",None),date):
            self.cycle_month=date.today().replace(day=1)
        if not isinstance(getattr(self,"cycle_day",None),date):
            self.cycle_day=date.today()
        state=self.store.wellness_data(person["id"],"cycle")
        periods=sorted(state["periods"],key=lambda r:r.get("start",""),
                       reverse=True)
        settings=state["settings"]
        taken=set(state["pill_taken"])
        next_date=estimated_next_period(periods,settings["cycle_days"])
        selected=self.cycle_day
        month=self.cycle_month
        layout=ctk.CTkFrame(self.body,fg_color="transparent")
        layout.pack(fill="both",expand=True,padx=(5,7),pady=(0,6))
        layout.grid_rowconfigure(0,weight=1)
        layout.grid_columnconfigure(0,weight=10,uniform="cycle")
        layout.grid_columnconfigure(1,weight=10,uniform="cycle")
        left=ctk.CTkFrame(layout,fg_color=self.p["panel"],
                          border_color=self.p["line"],border_width=1,
                          corner_radius=14)
        right=ctk.CTkFrame(layout,fg_color=self.p["panel"],
                           border_color=self.p["line"],border_width=1,
                           corner_radius=14)
        left.grid(row=0,column=0,sticky="nsew",padx=(0,7))
        right.grid(row=0,column=1,sticky="nsew",padx=(7,0))
        self._cycle_left=left
        self._cycle_right=right
        top=ctk.CTkFrame(left,fg_color="transparent")
        top.pack(fill="x",padx=13,pady=(11,7))
        self._label(top,f"{MONTHS[month.month-1]} {month.year}",
                    19,True).pack(side="left")
        nav=ctk.CTkFrame(top,fg_color="transparent")
        nav.pack(side="right")
        self._button(nav,"‹",lambda:self._cycle_move(-1),
                     width=38,height=32).pack(side="left",padx=(0,3))
        self._button(nav,"Hoje",lambda:self._cycle_pick(date.today()),
                     width=69,height=32).pack(side="left",padx=3)
        self._button(nav,"›",lambda:self._cycle_move(1),
                     width=38,height=32).pack(side="left",padx=(3,0))
        legends=ctk.CTkFrame(left,fg_color="transparent")
        legends.pack(fill="x",padx=15,pady=(0,5))
        for marker,caption,fg in (
            ("●","Período registado","#ed7fae"),
            ("◌","Estimativa","#c5abef"),
            ("✓","Pílula confirmada","#00c9b7"),
        ):
            col=ctk.CTkFrame(legends,fg_color="transparent")
            col.pack(side="left",padx=(0,12))
            self._label(col,marker,12,True,color=fg).pack(side="left")
            self._label(col,caption,10,color=self.p["muted"]).pack(
                side="left",padx=(3,0))
        calendar_grid=ctk.CTkFrame(left,fg_color="transparent")
        calendar_grid.pack(fill="x",padx=10,pady=(2,8))
        for col,name in enumerate(WEEKDAYS):
            calendar_grid.grid_columnconfigure(col,weight=1,uniform="cycle_days")
            self._label(calendar_grid,name.upper(),10,True,
                        anchor="center",color=self.p["muted"]).grid(
                            row=0,column=col,sticky="ew",padx=2,pady=(0,5))
        self._cycle_day_tiles={}
        for row,week in enumerate(
            calendar.Calendar(firstweekday=0).monthdatescalendar(
                month.year,month.month),1):
            for col,day in enumerate(week):
                inside=day.month==month.month
                iso=day.isoformat()
                actual=any(p.get("start","")<=iso<=p.get("end","")
                           for p in periods)
                predicted=iso==next_date
                acknowledged=iso in taken
                is_selected=day==selected
                is_today=day==date.today()
                if is_selected:
                    background="#00b9ac"
                    ink="#052f35"
                elif actual:
                    background="#79405c" if self.p["bg"]!="#edf4f7" else "#ffe0ec"
                    ink="#ffffff" if self.p["bg"]!="#edf4f7" else "#7d2352"
                elif predicted:
                    background="#3b4165" if self.p["bg"]!="#edf4f7" else "#f0e8ff"
                    ink="#e9ddff" if self.p["bg"]!="#edf4f7" else "#6844a3"
                else:
                    background=self.p["panel2"] if inside else self.p["bg"]
                    ink=self.p["text"] if inside else self.p["muted"]
                tile=ctk.CTkFrame(
                    calendar_grid,fg_color=background,corner_radius=9,
                    height=58,border_width=2 if is_today or is_selected else 1,
                    border_color="#e9bc66" if is_today else (
                        "#00c9b7" if is_selected else self.p["line"]))
                tile.grid(row=row,column=col,sticky="nsew",padx=2,pady=2)
                tile.grid_propagate(False)
                self._cycle_day_tiles[day]=tile
                num=self._label(tile,str(day.day),15,inside or is_selected,
                                color=ink)
                num.pack(anchor="nw",padx=8,pady=(4,1))
                marker_text=("✓" if acknowledged else
                             "●" if actual else "◌" if predicted else
                             "p" if pill_scheduled(iso,settings) else "")
                widgets=[tile,num]
                if marker_text:
                    small=self._label(
                        tile,marker_text,12,True,color=ink)
                    small.pack(anchor="sw",padx=9,pady=(0,1))
                    widgets.append(small)
                for widget in widgets:
                    widget.bind("<Button-1>",lambda _event,d=day:
                                self._cycle_pick(d),add="+")
        summary=ctk.CTkFrame(left,fg_color=self.p["panel2"],
                             corner_radius=10)
        summary.pack(fill="x",padx=12,pady=(3,10))
        self._label(summary,
            "Próximo início estimado: "+
            (date.fromisoformat(next_date).strftime("%d/%m/%Y")
             if next_date else "sem dados suficientes"),
            13,True,color="#00c9b7").pack(
                anchor="w",padx=11,pady=(10,2))
        self._label(summary,
            f"Ciclo configurado: {settings['cycle_days']} dias. "
            "Estimativa aproximada baseada no último período.",
            11,color=self.p["muted"],wrap=510).pack(
                anchor="w",padx=11,pady=(0,10))
        self._label(left,
            "As estimativas não preveem fertilidade nem substituem "
            "contraceção ou aconselhamento médico.",
            11,color=self.p["muted"],wrap=500).pack(
                anchor="w",padx=14,pady=(0,8))

        scroll=ctk.CTkScrollableFrame(right,fg_color="transparent")
        scroll.pack(fill="both",expand=True,padx=8,pady=(9,8))
        self._label(scroll,f"Dia selecionado · {selected:%d/%m/%Y}",
                    17,True).pack(anchor="w",padx=8,pady=(0,4))
        s=selected.isoformat()
        actual=next((p for p in periods if p["start"]<=s<=p["end"]),None)
        status=(
            "Período registado" if actual else
            "Dia estimado para próximo período" if s==next_date
            else "Sem período registado neste dia")
        self._label(scroll,status,12,color="#00c9b7").pack(
            anchor="w",padx=8,pady=(0,9))

        pill=ctk.CTkFrame(scroll,fg_color=self.p["panel2"],
                          corner_radius=10)
        pill.pack(fill="x",padx=4,pady=(0,11))
        self._label(pill,"💊 Registo de pílula",14,True).pack(
            anchor="w",padx=11,pady=(9,4))
        due=pill_scheduled(s,settings)
        confirmed=s in taken
        pill_label=(
            "Confirmada manualmente" if confirmed
            else "Toma prevista pelo esquema escolhido" if due
            else "Sem toma prevista neste dia")
        self._label(pill,pill_label,11,color=self.p["muted"]).pack(
            anchor="w",padx=11,pady=(0,6))
        if confirmed:
            self._button(pill,"Anular confirmação",
                         lambda:self._cycle_mark_pill(selected,False),
                         width=170,height=32).pack(anchor="w",padx=11,pady=(0,10))
        elif due and selected<=date.today():
            self._button(pill,"✓ Tomei (confirmar)",
                         lambda:self._cycle_mark_pill(selected,True),
                         True,width=190,height=32).pack(
                             anchor="w",padx=11,pady=(0,10))
        else:
            self._label(pill,"",5).pack(pady=1)

        self._label(scroll,"Registar período",15,True).pack(
            anchor="w",padx=9,pady=(2,3))
        period_form=ctk.CTkFrame(scroll,fg_color=self.p["panel2"],
                                 corner_radius=10)
        period_form.pack(fill="x",padx=4,pady=(0,10))
        self._cycle_start=self._cycle_field(
            period_form,"Início (DD/MM/AAAA)",
            selected.strftime("%d/%m/%Y"))
        self._cycle_end=self._cycle_field(
            period_form,"Fim (DD/MM/AAAA)",
            selected.strftime("%d/%m/%Y"))
        self._label(period_form,"Nota opcional",11,
                    color=self.p["muted"]).pack(anchor="w",padx=9)
        self._cycle_note=ctk.CTkTextbox(
            period_form,height=49,fg_color=self.p["field"],
            text_color=self.p["text"],border_width=1,
            border_color=self.p["line"])
        self._cycle_note.pack(fill="x",padx=9,pady=(4,6))
        self._button(period_form,"+ Guardar período",
                     self._cycle_add_period,True,width=179,height=33).pack(
                         anchor="w",padx=9,pady=(1,11))

        self._label(scroll,"Histórico de períodos",15,True).pack(
            anchor="w",padx=9,pady=(2,5))
        if not periods:
            self._label(scroll,"Sem períodos registados.",
                        12,color=self.p["muted"]).pack(
                            anchor="w",padx=10,pady=(0,8))
        for period in periods:
            row=ctk.CTkFrame(scroll,fg_color=self.p["panel2"],
                             corner_radius=9)
            row.pack(fill="x",padx=4,pady=3)
            first=date.fromisoformat(period["start"]).strftime("%d/%m/%Y")
            last=date.fromisoformat(period["end"]).strftime("%d/%m/%Y")
            self._label(row,f"{first}  —  {last}",12,True).pack(
                side="left",padx=9,pady=10)
            self._button(row,"Remover",
                         lambda rid=period["id"]:self._cycle_delete(rid),
                         width=75,height=28).pack(side="right",padx=7)

        self._label(scroll,"Configuração do ciclo e pílula",15,True).pack(
            anchor="w",padx=9,pady=(10,5))
        self._cycle_days=self._cycle_field(
            scroll,"Duração estimada do ciclo (21–45 dias)",
            settings["cycle_days"])
        self._label(scroll,"Esquema de pílula",11,True,
                    color=self.p["muted"]).pack(
                        anchor="w",padx=9,pady=(4,3))
        active_label=next((label for label,key in PILL_PATTERNS.items()
                           if key==settings["pill_pattern"]),next(iter(PILL_PATTERNS)))
        self._cycle_pattern=ctk.StringVar(value=active_label)
        ctk.CTkOptionMenu(
            scroll,values=list(PILL_PATTERNS),variable=self._cycle_pattern,
            height=34,fg_color=self.p["panel2"],
            button_color="#0e6976",text_color=self.p["text"],
            dropdown_fg_color=self.p["panel"],
            dropdown_text_color=self.p["text"]).pack(fill="x",padx=9)
        self._cycle_pill_start=self._cycle_field(
            scroll,"Início do esquema (DD/MM/AAAA)",
            settings["pill_start"])
        self._cycle_pill_time=self._cycle_field(
            scroll,"Hora prevista (HH:MM)",settings["pill_time"])
        self._button(scroll,"Guardar configuração",
                     self._cycle_save_settings,True,width=197,height=35).pack(
                         anchor="w",padx=9,pady=(9,8))
        self._label(scroll,
            "A pílula só fica confirmada depois de clicares em Tomei. "
            "A versão Windows ainda não envia alarmes de pílula e "
            "não sincroniza este histórico com o Android.",
            11,color=self.p["muted"],wrap=470).pack(
                anchor="w",padx=9,pady=(0,12))
