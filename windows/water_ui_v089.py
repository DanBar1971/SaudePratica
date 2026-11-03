"""Windows 0.8.9 Hidratação: compact private diary with user-set goal.

No inferred water consumption, automatic notifications, or clinical target.
Unlike the early Android one-day counter, Windows retains dated entries.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from tkinter import messagebox
import customtkinter as ctk

from windows.secure_store import LocalStoreError
from windows.wellness_models_v089 import water_total,progress_pct


class WaterUiV089:
    def _water_day_move(self, offset):
        if not isinstance(getattr(self,"water_day",None),date):
            self.water_day=date.today()
        new=self.water_day+timedelta(days=offset)
        if new<=date.today():
            self.water_day=new
            self._render()

    def _water_today(self):
        self.water_day=date.today()
        self._render()

    def _water_add(self, selected_ml=None):
        if not self.active_id:
            return
        try:
            amount=(selected_ml if selected_ml is not None
                    else self._water_amount.get().strip())
            chosen=getattr(self,"water_day",date.today())
            clock=self._water_clock.get().strip()
            self.store.add_water(self.active_id, chosen.isoformat(),clock,amount)
            self._render()
        except (LocalStoreError,ValueError,OSError) as exc:
            messagebox.showerror("Hidratação",str(exc),parent=self)

    def _water_save_settings(self):
        if not self.active_id:
            return
        try:
            inputs={key:widget.get().strip()
                    for key,widget in self._water_settings_fields.items()}
            self.store.set_water_settings(self.active_id,inputs)
            self._render()
        except (LocalStoreError,ValueError,OSError) as exc:
            messagebox.showerror("Objetivo de hidratação",str(exc),parent=self)

    def _water_remove(self,identifier):
        if not messagebox.askyesno("Remover registo de água",
                "Remover este consumo registado? Os restantes não serão alterados.",
                parent=self):
            return
        try:
            self.store.remove_water(self.active_id,identifier)
            self._render()
        except (LocalStoreError,ValueError,OSError) as exc:
            messagebox.showerror("Hidratação",str(exc),parent=self)

    def _water_input(self,parent,label,key,initial):
        box=ctk.CTkFrame(parent,fg_color="transparent")
        box.pack(fill="x",padx=9,pady=(3,4))
        self._label(box,label,11,True,color=self.p["muted"]).pack(
            anchor="w",pady=(0,3))
        entry=ctk.CTkEntry(
            box,height=33,fg_color=self.p["field"],
            border_color=self.p["line"],text_color=self.p["text"])
        entry.insert(0,str(initial))
        entry.pack(fill="x")
        self._water_settings_fields[key]=entry

    def _water(self):
        self.wallpaper_shell.glass_enabled=False
        person=self.store.get_profile(self.active_id) if self.active_id else None
        self._heading("Hidratação",
                      "Registo de água do perfil: " + str(person.get("name",""))
                      if person else "Seleciona primeiro um perfil.")
        if not person:
            return
        if not isinstance(getattr(self,"water_day",None),date):
            self.water_day=date.today()
        day=self.water_day
        state=self.store.wellness_data(person["id"],"water")
        goal=state["settings"]["target_ml"]
        total=water_total(state["entries"],day.isoformat())
        percentage=progress_pct(total,goal)
        day_entries=sorted(
            [x for x in state["entries"] if isinstance(x,dict) and
             x.get("date")==day.isoformat()],
            key=lambda x:(x.get("time",""),x.get("id","")),reverse=True)

        layout=ctk.CTkFrame(self.body,fg_color="transparent")
        layout.pack(fill="both",expand=True,padx=(5,7),pady=(0,6))
        layout.grid_rowconfigure(0,weight=1)
        layout.grid_columnconfigure(0,weight=11,uniform="water")
        layout.grid_columnconfigure(1,weight=9,uniform="water")
        left=ctk.CTkFrame(layout,fg_color=self.p["panel"],
                          border_width=1,border_color=self.p["line"],
                          corner_radius=14)
        right=ctk.CTkFrame(layout,fg_color=self.p["panel"],
                           border_width=1,border_color=self.p["line"],
                           corner_radius=14)
        left.grid(row=0,column=0,sticky="nsew",padx=(0,7))
        right.grid(row=0,column=1,sticky="nsew",padx=(7,0))

        nav=ctk.CTkFrame(left,fg_color="transparent")
        nav.pack(fill="x",padx=13,pady=(10,5))
        self._button(nav,"‹",lambda:self._water_day_move(-1),
                     width=38,height=32).pack(side="left")
        self._label(nav,day.strftime("%d/%m/%Y"),17,True).pack(
            side="left",padx=13)
        self._button(nav,"›",lambda:self._water_day_move(+1),
                     width=38,height=32).pack(side="left")
        self._button(nav,"Hoje",self._water_today,width=71,height=32).pack(
            side="right")
        top=ctk.CTkFrame(left,fg_color="transparent")
        top.pack(fill="x",padx=17,pady=(8,8))
        self._label(top,f"{total:,}".replace(","," ")+" ml",31,True,
                    color="#00c9b7").pack(anchor="w")
        goal_label=(f"Objetivo escolhido: {goal} ml · {percentage}% registado"
                    if goal else "Sem objetivo diário definido")
        self._label(top,goal_label,12,color=self.p["muted"]).pack(anchor="w")
        if goal:
            progress=ctk.CTkProgressBar(
                left,height=13,fg_color=self.p["panel2"],
                progress_color="#00c9b7",corner_radius=8)
            progress.pack(fill="x",padx=17,pady=(2,10))
            progress.set(min(1,total/goal))
        self._label(left,"Últimos 7 dias (registos manuais)",
                    14,True).pack(anchor="w",padx=16,pady=(6,4))
        week=ctk.CTkFrame(left,fg_color="transparent")
        week.pack(fill="x",padx=16,pady=(0,10))
        weekly=[(day-timedelta(days=i),water_total(
            state["entries"],(day-timedelta(days=i)).isoformat()))
            for i in range(6,-1,-1)]
        max_ml=max([amount for _,amount in weekly]+[goal,1])
        for i,(when,amount) in enumerate(weekly):
            week.grid_columnconfigure(i,weight=1,uniform="week")
            col=ctk.CTkFrame(week,fg_color="transparent")
            col.grid(row=0,column=i,sticky="nsew",padx=3)
            self._label(col,when.strftime("%d/%m"),10,
                        color=self.p["muted"],anchor="center").pack()
            bar=ctk.CTkProgressBar(
                col,orientation="vertical",height=52,width=13,
                fg_color=self.p["panel2"],progress_color="#00bfb4")
            bar.pack(pady=(5,4))
            bar.set(min(1,amount/max_ml))
            self._label(col,str(amount),10,anchor="center").pack()

        self._label(left,f"Histórico de {day:%d/%m/%Y}",
                    14,True).pack(anchor="w",padx=16,pady=(4,6))
        history=ctk.CTkScrollableFrame(left,fg_color="transparent")
        history.pack(fill="both",expand=True,padx=6,pady=(0,8))
        if not day_entries:
            self._label(history,"Sem consumo registado neste dia.",
                        12,color=self.p["muted"]).pack(
                            anchor="w",padx=9,pady=13)
        for row in day_entries:
            cell=ctk.CTkFrame(history,fg_color=self.p["panel2"],
                              corner_radius=9)
            cell.pack(fill="x",padx=5,pady=3)
            self._label(cell,f"{row.get('time','--:--')}  ·  "
                        f"{row.get('ml',0)} ml",13,True).pack(
                            side="left",padx=11,pady=9)
            if row.get("id"):
                self._button(cell,"Remover",
                             lambda rid=row["id"]:self._water_remove(rid),
                             width=84,height=28).pack(side="right",padx=7)

        scroll=ctk.CTkScrollableFrame(right,fg_color="transparent",
                                     corner_radius=0)
        scroll.pack(fill="both",expand=True,padx=9,pady=(10,9))
        self._label(scroll,"Registar água",17,True).pack(
            anchor="w",padx=8,pady=(0,6))
        add=ctk.CTkFrame(scroll,fg_color=self.p["panel2"],corner_radius=11)
        add.pack(fill="x",padx=5,pady=(0,11))
        self._label(add,"Volume por registo (ml)",11,True).pack(
            anchor="w",padx=11,pady=(10,2))
        self._water_amount=ctk.CTkEntry(
            add,fg_color=self.p["field"],text_color=self.p["text"],height=35)
        self._water_amount.insert(0,str(state["settings"]["glass_ml"]))
        self._water_amount.pack(fill="x",padx=11)
        self._label(add,"Hora do consumo (HH:MM)",11,
                    color=self.p["muted"]).pack(
                        anchor="w",padx=11,pady=(7,3))
        self._water_clock=ctk.CTkEntry(
            add,fg_color=self.p["field"],text_color=self.p["text"],height=34)
        self._water_clock.insert(0,datetime.now().strftime("%H:%M"))
        self._water_clock.pack(fill="x",padx=11)
        actions=ctk.CTkFrame(add,fg_color="transparent")
        actions.pack(fill="x",padx=10,pady=10)
        self._button(actions,"+ Um copo",
                     lambda:self._water_add(state["settings"]["glass_ml"]),
                     True,width=130,height=35).pack(side="left",padx=(0,5))
        self._button(actions,"+ Registar volume",
                     lambda:self._water_add(),width=169,height=35).pack(
                         side="left")
        self._label(scroll,"Configuração pessoal",16,True).pack(
            anchor="w",padx=9,pady=(2,6))
        self._water_settings_fields={}
        for label,key in (
            ("Volume predefinido do copo (30–1000 ml)","glass_ml"),
            ("Objetivo diário opcional (0 = sem objetivo)","target_ml"),
            ("Hora de início para futuros avisos","water_start"),
            ("Hora de fim para futuros avisos","water_end"),
            ("Intervalo de avisos (minutos, 30–360)","water_interval"),
        ):
            self._water_input(scroll,label,key,state["settings"][key])
        self._button(scroll,"Guardar configuração",
                     self._water_save_settings,True,width=201,height=36).pack(
                         anchor="w",padx=9,pady=(9,10))
        self._label(scroll,
            "Objetivo escolhido pelo utilizador, não é uma recomendação "
            "médica. Os horários ficam guardados para futura compatibilidade "
            "com Android; esta versão Windows não envia alarmes de água.",
            11,color=self.p["muted"],wrap=440).pack(
                anchor="w",padx=10,pady=(0,10))
