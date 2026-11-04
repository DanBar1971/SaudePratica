"""Read-only 0.8.15 SaúdePrática activity cards for backed-up Health Connect.

The PC does not connect to Android Health Connect itself: all numbers below
come exclusively from a verified, profile-scoped, imported Android snapshot.
Manual Windows records and Android manual body weights stay independent.
"""
from __future__ import annotations

from datetime import date,datetime,timedelta
import customtkinter as ctk


DASHBOARD=(
    ("steps","👣 Passos"," passos"),
    ("distance_km","📍 Distância"," km"),
    ("active_kcal","🔥 Energia ativa"," kcal"),
    ("sleep_minutes","🌙 Sono",""),
    ("heart_bpm","❤️ Ritmo cardíaco médio"," bpm"),
    ("total_kcal","⚡ Energia total"," kcal"),
)
VITALS=(
    ("oxygen_percent","🫁 SpO₂"," %"),
    ("resting_heart_bpm","❤️ Pulsação em repouso"," bpm"),
    ("systolic_mmhg","🩺 Tensão sistólica"," mmHg"),
    ("diastolic_mmhg","🩺 Tensão diastólica"," mmHg"),
    ("respiratory_per_min","🌬 Frequência respiratória","/min"),
    ("temperature_c","🌡 Temperatura"," °C"),
    ("weight_kg","⚖ Peso Health Connect"," kg"),
)
CHARTS=(
    ("Passos","steps"),("Distância","distance_km"),
    ("Energia ativa","active_kcal"),("Sono","sleep_minutes"),
    ("Pulso","heart_bpm"),("Peso","weight_kg"),
)


def snapshot_value(snapshot,day,key):
    rows=snapshot.get("days",{}) if isinstance(snapshot,dict) else {}
    x=rows.get(day,{}) if isinstance(rows,dict) else {}
    if not isinstance(x,dict):
        return None
    metric=x.get(key,{})
    return metric.get("value") if isinstance(metric,dict) else None


def weekly_health(snapshot,ending,key):
    target=date.fromisoformat(ending)
    return [(d.isoformat(),snapshot_value(snapshot,d.isoformat(),key))
            for d in (target-timedelta(days=n) for n in range(6,-1,-1))]


def format_value(key,value):
    if value is None:
        return "sem registo no backup"
    if key=="sleep_minutes":
        minutes=round(value)
        return f"{minutes//60}h {minutes%60:02d}m"
    if key in ("steps","heart_bpm","resting_heart_bpm","systolic_mmhg",
               "diastolic_mmhg","respiratory_per_min"):
        return f"{round(value):,}".replace(","," ")
    if key in ("weight_kg","oxygen_percent","temperature_c"):
        return f"{value:.1f}".replace(".",",")
    if key=="distance_km":
        return f"{value:.2f}".replace(".",",")
    return f"{value:.0f}"


def captured_at(snapshot):
    moments=[
        reading.get("captured_at_ms",0)
        for values in snapshot.get("days",{}).values() if isinstance(values,dict)
        for reading in values.values() if isinstance(reading,dict)]
    if not moments:
        return ""
    return datetime.fromtimestamp(max(moments)/1000).strftime("%d/%m/%Y %H:%M")


def recent_vitals(snapshot):
    """Latest genuinely observed value of each vital sign, by actual record time."""
    days=snapshot.get("days",{})
    if not isinstance(days,dict):
        return []
    output=[]
    for key,label,unit in VITALS:
        entries=[]
        for iso_day,values in days.items():
            row=values.get(key) if isinstance(values,dict) else None
            if isinstance(row,dict) and isinstance(row.get("value"),(float,int)):
                at=row.get("observed_at_ms") or row.get("captured_at_ms",0)
                entries.append((at,iso_day,row["value"]))
        if entries:
            _,day,value=max(entries)
            output.append((label,day,format_value(key,value)+unit))
    return output


class ActivityHealthConnectUiV0815:
    def _draw_health_connect(self,left,snapshot,day):
        self._label(left,"Health Connect · dados do backup Android",15,True).pack(
            anchor="w",padx=14,pady=(8,3))
        last=captured_at(snapshot)
        self._label(left,
            "Cópia local, sem ligação em tempo real ao relógio. "
            +("Última captura: "+last if last else "Sem data de captura."),
            11,color=self.p["muted"],wrap=470).pack(
                anchor="w",padx=14,pady=(0,8))
        box=ctk.CTkFrame(left,fg_color=self.p["panel2"],corner_radius=11)
        box.pack(fill="x",padx=11,pady=(0,8))
        self._label(box,day.strftime("%d/%m/%Y"),14,True,
                    color="#00c9b7").pack(anchor="w",padx=12,pady=(9,4))
        for key,title,unit in DASHBOARD:
            value=snapshot_value(snapshot,day.isoformat(),key)
            self._label(box,title+": "+format_value(key,value)+(
                unit if value is not None and key!="sleep_minutes" else ""),
                12).pack(anchor="w",padx=14,pady=(0,4))
        self._label(box,"",5).pack()

        hdr=ctk.CTkFrame(left,fg_color="transparent")
        hdr.pack(fill="x",padx=12,pady=(4,6))
        self._label(hdr,"Evolução · últimos 7 dias",13,True).pack(side="left")
        names=[name for name,_ in CHARTS]
        select=ctk.CTkOptionMenu(
            hdr,values=names,width=130,height=29,
            fg_color=self.p["field"],button_color="#007e80",
            button_hover_color="#00a7a5",text_color=self.p["text"])
        select.pack(side="right",padx=(5,0))
        graph=ctk.CTkFrame(left,fg_color="transparent")
        graph.pack(fill="x",padx=13,pady=(0,9))

        def render_chart(choice):
            for child in graph.winfo_children():
                child.destroy()
            key=dict(CHARTS)[choice]
            weekly=weekly_health(snapshot,day.isoformat(),key)
            maximum=max([float(v) for _,v in weekly if v is not None]+[1.0])
            valid=[float(v) for _,v in weekly if v is not None]
            if valid:
                self._label(graph,
                    choice+" · média "+format_value(key,sum(valid)/len(valid)),
                    11,color="#00c9b7").pack(anchor="w",pady=(0,4))
            else:
                self._label(graph,"Sem medições no backup para estes dias.",
                            11,color=self.p["muted"]).pack(anchor="w",pady=(0,4))
            bars=ctk.CTkFrame(graph,fg_color="transparent")
            bars.pack(fill="x")
            for i,(stamp,value) in enumerate(weekly):
                bars.grid_columnconfigure(i,weight=1,uniform="hcweek")
                column=ctk.CTkFrame(bars,fg_color="transparent")
                column.grid(row=0,column=i,sticky="nsew",padx=2)
                self._label(column,stamp[8:10],10,anchor="center",
                            color=self.p["muted"]).pack()
                bar=ctk.CTkProgressBar(
                    column,orientation="vertical",height=54,width=12,
                    fg_color=self.p["panel2"],progress_color="#00c9b7")
                bar.pack(pady=(4,3))
                bar.set(float(value)/maximum if value is not None else 0.0)
                self._label(column,format_value(key,value) if value is not None else "—",
                            10,anchor="center").pack()
        select.configure(command=render_chart)
        select.set("Passos")
        render_chart("Passos")

        readings=recent_vitals(snapshot)
        if readings:
            self._label(left,"Sinais vitais · Health Connect",13,True).pack(
                anchor="w",padx=14,pady=(4,6))
            vital_box=ctk.CTkFrame(left,fg_color=self.p["panel2"],corner_radius=10)
            vital_box.pack(fill="x",padx=11,pady=(0,9))
            for title,stamp,value in readings:
                self._label(vital_box,title+": "+value+"  ·  "+stamp,
                            11).pack(anchor="w",padx=12,pady=(6,2))
            self._label(vital_box,"",5).pack()

    def _draw_android_body(self,left,body):
        if not isinstance(body,dict):
            return
        weights=body.get("weights",[])
        if not isinstance(weights,list):
            weights=[]
        height=body.get("height_cm")
        if not weights and not height:
            return
        self._label(left,"Peso manual guardado no Android",13,True).pack(
            anchor="w",padx=14,pady=(6,5))
        card=ctk.CTkFrame(left,fg_color=self.p["panel2"],corner_radius=10)
        card.pack(fill="x",padx=11,pady=(0,10))
        if height:
            self._label(card,"Altura: "+format_value("weight_kg",height)+" cm",
                        11).pack(anchor="w",padx=12,pady=(7,2))
        for row in sorted(
            [x for x in weights if isinstance(x,dict)],key=lambda x:x.get("at",0),
            reverse=True)[:8]:
            self._label(card,row.get("date","")+" · "+
                        format_value("weight_kg",row.get("kg"))+" kg",
                        11).pack(anchor="w",padx=12,pady=(5,2))
        self._label(card,"",5).pack()
