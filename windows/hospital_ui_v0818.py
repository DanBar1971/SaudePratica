"""Windows 0.8.18: read-only hospital team/charges/transport and image viewer.

The Windows profile must be unlocked and linked to its own verified Android
backup. No online or hospital APIs, and no cross-profile fallback.
"""
from __future__ import annotations
from io import BytesIO
import customtkinter as ctk
from PIL import Image, ImageOps
from windows.hospital_processes_v0818 import read_hospital_processes

def euros(value:int)->str:
    return f"{value//100},{value%100:02d} €"

class HospitalUiV0818:
    def _hospital_banner(self,parent,profile_id:str):
        try:
            data,images=read_hospital_processes(self.store,profile_id)
        except (OSError,ValueError,KeyError) as exc:
            self._label(parent,
                "Processos Android: não foi possível validar o backup deste perfil.",
                12,color=self.p["muted"]).pack(anchor="w",padx=12,pady=(3,8))
            return
        frame=ctk.CTkFrame(parent,fg_color=self.p["panel"],
                           corner_radius=12,border_color=self.p["line"],
                           border_width=1)
        frame.pack(fill="x",padx=7,pady=(1,10))
        title=ctk.CTkFrame(frame,fg_color="transparent")
        title.pack(fill="x",padx=12,pady=7)
        self._label(title,"🏥 Processos hospitalares do Android",15,True
            ).pack(side="left",padx=(0,15))
        if data:
            self._button(title,"Ver "+str(len(data))+" processo(s)",
                         lambda:self._hospital_view(data,images),True,
                         width=180,height=36).pack(side="right")
            self._label(frame,
                "Equipa, taxas moderadoras, identificação e transporte · leitura do backup",
                11,color=self.p["muted"]).pack(anchor="w",padx=13,pady=(0,8))
        else:
            self._label(frame,
                "Sem processos hospitalares recuperados para este perfil. "
                "Importa/restaura um backup Android criado na versão 1.9.136 ou posterior.",
                12,color=self.p["muted"],wrap=770).pack(
                    anchor="w",padx=12,pady=(0,10))

    def _hospital_view(self,processes,images):
        patient=self.store.get_profile(self.active_id) if self.active_id else None
        if not patient:return
        existing=getattr(self,"_hospital_window",None)
        if existing is not None and existing.winfo_exists():
            existing.destroy()
        window=ctk.CTkToplevel(self)
        self._hospital_window=window
        window.title("SaúdePrática · Processos hospitalares · "+
                     str(patient.get("name","")))
        window.geometry("1040x750")
        window.minsize(790,540)
        window.transient(self)
        window.grab_set()
        wrapper=ctk.CTkFrame(window,fg_color=self.p["bg"])
        wrapper.pack(fill="both",expand=True,padx=12,pady=12)
        head=ctk.CTkFrame(wrapper,fg_color="transparent")
        head.pack(fill="x",pady=(2,10))
        ctk.CTkLabel(head,text="🏥 Processos de "+str(patient.get("name","")),
                     text_color=self.p["text"],
                     font=ctk.CTkFont(size=21,weight="bold")).pack(side="left")
        ctk.CTkButton(head,text="Fechar",command=window.destroy,
                      width=90,fg_color="#0e6976").pack(side="right")
        split=ctk.CTkFrame(wrapper,fg_color="transparent")
        split.pack(fill="both",expand=True)
        left=ctk.CTkScrollableFrame(split,fg_color=self.p["panel"],
                                     width=290)
        left.pack(side="left",fill="y",padx=(0,9))
        right=ctk.CTkScrollableFrame(split,fg_color=self.p["panel"])
        right.pack(side="left",fill="both",expand=True)
        self._hospital_photo=None

        def label(parent,value,size=13,bold=False,muted=False):
            return ctk.CTkLabel(parent,text=value,anchor="w",justify="left",
                wraplength=580,text_color=self.p["muted"] if muted else self.p["text"],
                font=ctk.CTkFont(size=size,weight="bold" if bold else "normal"))

        def chosen(item):
            for child in right.winfo_children():child.destroy()
            label(right,(item["unit"] or "Unidade clínica")+" · "+
                  item["number"],20,True).pack(anchor="w",padx=15,pady=(12,10))
            label(right,"Informação registada no Android · só de consulta",
                  11,muted=True).pack(anchor="w",padx=15,pady=(0,14))
            label(right,"👩‍⚕️ A minha equipa ("+str(len(item["team"]))+")",
                  17,True).pack(anchor="w",padx=15,pady=(2,9))
            if not item["team"]:
                label(right,"Sem contactos").pack(anchor="w",padx=18,pady=4)
            for person in item["team"]:
                text=person["name"]+" · "+person["specialty"]
                if person["email"]:text+="\n✉ "+person["email"]
                if person["phone"]:text+="\n☎ "+person["phone"]
                label(right,text,12).pack(anchor="w",padx=19,pady=(1,8))
            label(right,"💶 Taxas moderadoras",17,True).pack(
                anchor="w",padx=15,pady=(16,8))
            outstanding=sum(int(c["cents"]) for c in item["charges"]
                            if c["status"]=="Por pagar")
            label(right,"Por pagar: "+euros(outstanding),14,True).pack(
                anchor="w",padx=18,pady=(1,7))
            for category in ("Consultas","Exames","Análises"):
                rows=[x for x in item["charges"] if x["category"]==category]
                owed=sum(x["cents"] for x in rows if x["status"]=="Por pagar")
                label(right,category+" · "+str(len(rows))+" registo(s) · dívida "+
                      euros(owed),13,True).pack(anchor="w",padx=18,pady=(4,5))
                for row in rows:
                    label(right,row["date"]+" · "+euros(row["cents"])+" · "+
                        row["status"]+(" · "+row["notes"] if row["notes"] else ""),
                        12).pack(anchor="w",padx=24,pady=(1,3))
            label(right,"🚕 Declarações de transporte",17,True).pack(
                anchor="w",padx=15,pady=(17,8))
            if not item["transports"]:
                label(right,"Sem pedidos de transporte").pack(
                    anchor="w",padx=18,pady=5)
            for transport in item["transports"]:
                label(right,transport["description"]+" · "+transport["status"]+
                    "\n"+transport["date"]+" · "+transport["reference"]+
                    ("\n"+transport["notes"] if transport["notes"] else ""),
                    12).pack(anchor="w",padx=18,pady=(2,8))
            label(right,"🪪 Identificação do processo",17,True).pack(
                anchor="w",padx=15,pady=(17,9))
            raw=images.get(item["image_path"])
            self._hospital_photo=None
            if raw:
                try:
                    with Image.open(BytesIO(raw)) as original:
                        original.load()
                        if original.width*original.height>25_000_000:
                            raise ValueError("Imagem demasiado grande.")
                        picture=ImageOps.contain(original.convert("RGB"),(550,360))
                    self._hospital_photo=ctk.CTkImage(light_image=picture,
                        dark_image=picture,size=picture.size)
                    ctk.CTkLabel(right,text="",image=self._hospital_photo).pack(
                        padx=12,pady=(5,20))
                except (OSError,ValueError):
                    label(right,"Imagem não disponível").pack(
                        anchor="w",padx=19,pady=6)
            else:
                label(right,"Sem imagem no backup deste perfil").pack(
                    anchor="w",padx=19,pady=6)
        for item in processes:
            caption=(item["unit"] or "Unidade")+"\nN.º "+item["number"]
            ctk.CTkButton(left,text=caption,command=lambda x=item:chosen(x),
                anchor="w",height=62,corner_radius=9,
                fg_color="#0e6976",hover_color="#07616c").pack(
                    fill="x",padx=9,pady=5)
        chosen(processes[0])
        window.focus()
