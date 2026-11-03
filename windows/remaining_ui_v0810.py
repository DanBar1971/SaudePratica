"""Windows 0.8.10 — editable health and care fichas, always profile-bounded.

Six record sets reuse the same split layout and encrypted SecureStore. Emergency
is a separately editable profile card; no call or message is sent without action.
"""
from __future__ import annotations
from datetime import date
from tkinter import messagebox
import os
import webbrowser
import customtkinter as ctk

from windows.remaining_models_v0810 import (
    SCHEMAS, EMERGENCY_FIELDS, check_url, text_money,
)
from windows.secure_store import LocalStoreError

CARE_URLS=[
    ("ADSE Direta","https://adsedireta.adse.pt/"),
    ("Apoios sociais — gov.pt","https://www.gov.pt/guias/apoio-a-familia/apoio-social-para-idosos"),
    ("Complemento por dependência","https://www.gov.pt/servicos/obter-informacoes-sobre-o-complemento-por-dependencia"),
]
PHARMACY_URLS=[
    ("Infarmed","https://www.infarmed.pt/"),
    ("Portal SNS 24","https://www.sns24.gov.pt/pt/inicio"),
]


class RemainingUiV0810:
    def _record_page_select(self,kind,identifier):
        self._remaining_selection[kind]=identifier
        self._render()

    def _record_page_new(self,kind):
        self._remaining_selection[kind]=None
        self._render()

    def _record_page_save(self,kind):
        try:
            fields={}
            for key,(widget,typ) in self._remaining_fields.items():
                fields[key]=widget.get("1.0","end-1c") if typ=="long" else widget.get()
            if "document_sha256" in self._remaining_fields:
                fields["document_sha256"]=self._remaining_doc_options.get(
                    fields["document_sha256"],"")
            item=self.store.save_remaining_record(
                self.active_id,kind,fields,self._remaining_selection.get(kind))
            self._remaining_selection[kind]=item["id"]
            self._render()
        except (ValueError,OSError,LocalStoreError) as exc:
            messagebox.showerror("Guardar ficha",str(exc),parent=self)

    def _record_page_delete(self,kind,identifier):
        if not messagebox.askyesno(
            "Remover registo",
            "Remover este registo do perfil atual?\n"
            "Os documentos associados continuam guardados.",parent=self):
            return
        try:
            self.store.delete_remaining_record(self.active_id,kind,identifier)
            self._remaining_selection[kind]=None
            self._render()
        except (LocalStoreError,OSError) as exc:
            messagebox.showerror("Apagar",str(exc),parent=self)

    def _record_doc_open(self,digest):
        if not any(item.get("sha256")==digest for item in
                   self.store.imported_assets(self.active_id)):
            messagebox.showerror("Documentos",
                                 "O anexo não pertence a este perfil.",parent=self)
            return
        self.doc_selected_digest=digest
        self.doc_selected_profile=self.active_id
        self.doc_page_index=0
        self.navigate("documents")

    def _record_doc_selector(self,parent,profile_id,current):
        assets=self.store.imported_assets(profile_id)
        options={"Sem documento associado":""}
        for i,a in enumerate(assets,1):
            digest=a.get("sha256")
            if isinstance(digest,str) and len(digest)==64:
                label=(str(a.get("display_name") or a.get("filename") or "Documento")[:62])
                options[f"{i}. {label}"]=digest
        self._remaining_doc_options=options
        name=next((k for k,v in options.items() if v==current),
                  "Sem documento associado")
        variable=ctk.StringVar(value=name)
        self._remaining_fields["document_sha256"]=(variable,"choice")
        container=ctk.CTkFrame(parent,fg_color="transparent")
        container.pack(fill="x",padx=12,pady=(4,7))
        self._label(container,"Documento associado (deste perfil)",11,True,
                    color=self.p["muted"]).pack(anchor="w")
        ctk.CTkOptionMenu(container,values=list(options),
                          variable=variable,height=34,
                          fg_color=self.p["panel2"],
                          button_color="#116d79",
                          text_color=self.p["text"],
                          dropdown_text_color=self.p["text"],
                          dropdown_fg_color=self.p["panel"]).pack(fill="x",pady=(4,3))
        nav=ctk.CTkFrame(container,fg_color="transparent")
        nav.pack(fill="x",pady=(2,1))
        self._button(nav,"Ver Documentos",
                     lambda:self.navigate("documents"),width=140,height=29).pack(side="left")
        if current and current in options.values():
            self._button(nav,"Abrir anexo",
                         lambda v=current:self._record_doc_open(v),
                         width=126,height=29).pack(side="left",padx=5)

    def _record_input(self,parent,key,label,typ,value,limit):
        shell=ctk.CTkFrame(parent,fg_color="transparent")
        shell.pack(fill="x",padx=10,pady=(2,7))
        self._label(shell,label,11,True,
                    color=self.p["muted"]).pack(anchor="w",pady=(0,3))
        if typ=="long":
            widget=ctk.CTkTextbox(shell,height=78,
                                  fg_color=self.p["field"],
                                  text_color=self.p["text"],
                                  border_color=self.p["line"],border_width=1)
            widget.insert("1.0",str(value or ""))
            widget.pack(fill="x")
        elif typ.startswith("choice:"):
            values=typ[7:].split("|")
            chosen=str(value) if str(value) in values else values[0]
            widget=ctk.StringVar(value=chosen)
            ctk.CTkOptionMenu(shell,variable=widget,values=values,
                              height=34,fg_color=self.p["panel2"],
                              button_color="#116d79",
                              text_color=self.p["text"],
                              dropdown_fg_color=self.p["panel"],
                              dropdown_text_color=self.p["text"]).pack(fill="x")
        else:
            widget=ctk.CTkEntry(shell,height=34,
                                fg_color=self.p["field"],
                                text_color=self.p["text"],
                                border_color=self.p["line"])
            if typ=="money":
                value=text_money(value)
            widget.insert(0,str(value or ""))
            widget.pack(fill="x")
        self._remaining_fields[key]=(widget,typ)

    def _external_open(self,target):
        try:
            url=check_url(target)
            if not url or not webbrowser.open(url,new=2):
                raise ValueError("Não foi possível abrir o navegador.")
        except (OSError,ValueError) as exc:
            messagebox.showerror("Website",str(exc),parent=self)

    def _open_phone(self,number):
        import re
        clean=str(number or "").strip()
        if not re.fullmatch(r"[+\d\s()\-]{3,30}",clean):
            messagebox.showerror("Telefone","Número inválido.",parent=self)
            return
        if not messagebox.askyesno(
            "Abrir marcador telefónico",
            f"Abrir o marcador do Windows com o número {clean}?\n"
            "O Windows necessita de uma aplicação configurada para chamadas. "
            "Esta ação não envia mensagens automaticamente.",parent=self):
            return
        try:
            if os.name!="nt":
                raise OSError("Abertura de chamadas disponível apenas no Windows.")
            os.startfile("tel:"+clean.replace(" ","").replace("(","").replace(")",""))
        except (OSError,AttributeError) as exc:
            messagebox.showerror("Chamada",f"Não foi possível abrir o marcador: {exc}",
                                 parent=self)

    def _residences(self):
        if getattr(self,"_care_tab",None) not in ("residences","residence_invoices","supports"):
            self._care_tab="residences"
        self._record_page(self._care_tab)

    def _care_select_tab(self,kind):
        self._care_tab=kind
        self._render()

    def _vision(self):self._record_page("vision")
    def _symptoms(self):self._record_page("symptoms")
    def _vaccines(self):self._record_page("vaccines")
    def _pharmacy(self):self._record_page("pharmacy")

    def _record_page(self,kind):
        self.wallpaper_shell.glass_enabled=False
        profile=self.store.get_profile(self.active_id) if self.active_id else None
        schema=SCHEMAS[kind]
        title="Lares e Apoios" if kind in ("residences","residence_invoices","supports") else schema["title"]
        self._heading(title,
                      "Registos do perfil: "+str(profile.get("name",""))
                      if profile else "Seleciona um perfil.")
        if profile is None:return
        if not isinstance(getattr(self,"_remaining_selection",None),dict):
            self._remaining_selection={}
        if title=="Lares e Apoios":
            tabs=ctk.CTkFrame(self.body,fg_color="transparent")
            tabs.pack(fill="x",padx=13,pady=(0,7))
            for key,label in (
                ("residences","Instituições e Contactos"),
                ("residence_invoices","Faturas / ADSE"),
                ("supports","Apoios"),
            ):
                self._button(tabs,label,lambda p=key:self._care_select_tab(p),
                             accent=key==kind,width=185,height=34).pack(
                                 side="left",padx=(0,7))
        rows=self.store.remaining_records(profile["id"],kind)
        uid=self._remaining_selection.get(kind)
        chosen=next((item for item in rows if item.get("id")==uid),None)
        if uid and chosen is None:
            self._remaining_selection[kind]=None
        current=chosen or {}
        split=ctk.CTkFrame(self.body,fg_color="transparent")
        split.pack(fill="both",expand=True,padx=6,pady=(0,6))
        split.grid_rowconfigure(0,weight=1)
        split.grid_columnconfigure(0,weight=9,uniform="details")
        split.grid_columnconfigure(1,weight=11,uniform="details")
        left=ctk.CTkFrame(split,fg_color=self.p["panel"],
                          border_width=1,border_color=self.p["line"],
                          corner_radius=14)
        right=ctk.CTkFrame(split,fg_color=self.p["panel"],
                           border_width=1,border_color=self.p["line"],
                           corner_radius=14)
        left.grid(row=0,column=0,sticky="nsew",padx=(0,7))
        right.grid(row=0,column=1,sticky="nsew",padx=(7,0))
        self._remaining_panels=(left,right)
        head=ctk.CTkFrame(left,fg_color="transparent")
        head.pack(fill="x",padx=12,pady=(10,7))
        self._label(head,f"{len(rows)} registo(s)",16,True).pack(side="left")
        self._button(head,"+ Novo registo",lambda:self._record_page_new(kind),
                     True,width=134,height=33).pack(side="right")
        if kind=="pharmacy":
            self._label(left,"Favoritos guardados manualmente. Os horários de serviço "
                        "e disponibilidade devem ser confirmados diretamente.",
                        11,color=self.p["muted"],wrap=440).pack(anchor="w",padx=12,pady=(0,6))
        listing=ctk.CTkScrollableFrame(left,fg_color="transparent")
        listing.pack(fill="both",expand=True,padx=6,pady=(0,8))
        if not rows:
            self._label(listing,"Ainda não existem registos neste perfil.",
                        12,color=self.p["muted"]).pack(anchor="w",padx=10,pady=17)
        for row in rows:
            is_selected=bool(chosen and row.get("id")==chosen.get("id"))
            tile=ctk.CTkFrame(listing,fg_color=self.p["panel2"],
                              corner_radius=10,border_width=2 if is_selected else 1,
                              border_color="#00c9b7" if is_selected else self.p["line"])
            tile.pack(fill="x",padx=3,pady=4)
            self._label(tile,str(row.get("title") or schema["title"])[:130],
                        13,True,wrap=310).pack(anchor="w",padx=11,pady=(9,2))
            summary=(str(row.get("date") or row.get("type") or row.get("address") or "")
                     + ("  ·  "+str(row.get("status")) if row.get("status") else ""))
            if kind=="residence_invoices":
                summary+=" · "+text_money(row.get("amount_cents",0))+" €"
            self._label(tile,summary[:150],11,color=self.p["muted"],
                        wrap=370).pack(anchor="w",padx=11,pady=(0,6))
            actions=ctk.CTkFrame(tile,fg_color="transparent")
            actions.pack(fill="x",padx=10,pady=(0,9))
            self._button(actions,"Abrir / Editar",
                         lambda rid=row.get("id"):self._record_page_select(kind,rid),
                         width=121,height=29).pack(side="right")
            if kind in ("pharmacy","residences") and row.get("phone"):
                self._button(actions,"Ligar",
                             lambda number=row["phone"]:self._open_phone(number),
                             width=64,height=29).pack(side="left")
        if kind in ("pharmacy","residences","supports"):
            shortcuts=PHARMACY_URLS if kind=="pharmacy" else CARE_URLS
            bottom=ctk.CTkFrame(left,fg_color="transparent")
            bottom.pack(fill="x",padx=10,pady=(1,9))
            for label,url in shortcuts[:3]:
                self._button(bottom,label,
                             lambda u=url:self._external_open(u),
                             width=150,height=30).pack(side="left",padx=(0,5))
        top=ctk.CTkFrame(right,fg_color="transparent")
        top.pack(fill="x",padx=13,pady=(10,6))
        self._label(top,"Editar ficha" if chosen else "Nova ficha",
                    16,True).pack(side="left")
        self._button(top,"Guardar",lambda:self._record_page_save(kind),
                     True,width=100,height=33).pack(side="right")
        if chosen:
            self._button(top,"Remover",
                         lambda k=kind,rid=chosen["id"]:
                             self._record_page_delete(k,rid),
                         width=84,height=33).pack(side="right",padx=6)
        scroll=ctk.CTkScrollableFrame(right,fg_color="transparent")
        scroll.pack(fill="both",expand=True,padx=9,pady=(0,9))
        self._remaining_fields={}
        self._remaining_doc_options={}
        for key,label,typ,limit in schema["fields"]:
            if typ=="document":
                self._record_doc_selector(scroll,profile["id"],
                                          current.get(key,""))
                continue
            value=(current.get(key+"_cents",0) if typ=="money"
                   else current.get(key, ""))
            if typ=="date" and not value:
                value=date.today().strftime("%d/%m/%Y")
            self._record_input(scroll,key,label,typ,value,limit)
        if kind=="symptoms":
            warning="Este diário não avalia a gravidade dos sintomas. Sinais intensos ou preocupantes devem ser comunicados aos serviços de saúde."
        elif kind=="vaccines":
            warning="Confirma datas e próximas doses no boletim de vacinação ou com os serviços de saúde."
        elif kind=="vision":
            warning="Transcreve a graduação de uma receita confirmada. A app não calcula prescrições nem substitui exame de visão."
        elif kind=="pharmacy":
            warning="Contactos guardados por ti. Não indica farmácias de serviço em tempo real."
        else:
            warning="Dados introduzidos manualmente. Apoios e comparticipações dependem de verificação com a instituição ou entidade competente; não existe submissão automática."
        self._label(scroll,warning,11,color=self.p["muted"],
                    wrap=470).pack(anchor="w",padx=12,pady=(10,13))

    def _emergency(self):
        self.wallpaper_shell.glass_enabled=False
        profile=self.store.get_profile(self.active_id) if self.active_id else None
        self._heading("Ficha de Emergência",
                      "Informação essencial do perfil: "+str(profile.get("name",""))
                      if profile else "Seleciona um perfil.")
        if profile is None:return
        data=self.store.emergency_data(profile["id"])
        split=ctk.CTkFrame(self.body,fg_color="transparent")
        split.pack(fill="both",expand=True,padx=7,pady=(0,7))
        split.grid_columnconfigure(0,weight=10,uniform="emergency")
        split.grid_columnconfigure(1,weight=10,uniform="emergency")
        split.grid_rowconfigure(0,weight=1)
        left=ctk.CTkFrame(split,fg_color=self.p["panel"],
                          border_width=1,border_color=self.p["line"],corner_radius=14)
        right=ctk.CTkFrame(split,fg_color=self.p["panel"],
                           border_width=1,border_color=self.p["line"],corner_radius=14)
        left.grid(row=0,column=0,sticky="nsew",padx=(0,7))
        right.grid(row=0,column=1,sticky="nsew",padx=(7,0))
        self._emergency_panels=(left,right)
        self._label(left,"Informação de consulta rápida",18,True).pack(
            anchor="w",padx=15,pady=(13,8))
        notes=ctk.CTkScrollableFrame(left,fg_color="transparent")
        notes.pack(fill="both",expand=True,padx=6,pady=5)
        for key,label,limit in EMERGENCY_FIELDS:
            tile=ctk.CTkFrame(notes,fg_color=self.p["panel2"],corner_radius=9)
            tile.pack(fill="x",padx=5,pady=3)
            self._label(tile,label,11,True,color="#00c9b7").pack(
                anchor="w",padx=12,pady=(9,1))
            self._label(tile,data.get(key) or "Por preencher",
                        12,wrap=450).pack(anchor="w",padx=12,pady=(0,8))
        phone=data.get("contact_phone","")
        if phone:
            self._button(left,"Abrir marcador: "+phone,
                         lambda:self._open_phone(phone),
                         True,width=235,height=36).pack(anchor="w",padx=17,pady=7)
        self._button(left,"112 · Abrir marcador",
                     lambda:self._open_phone("112"),
                     width=210,height=37).pack(anchor="w",padx=17,pady=(0,12))
        self._label(left,
            "Em Portugal, numa emergência real liga 112 diretamente. "
            "O Windows pode não ter aplicação de chamadas. Esta ficha não "
            "substitui serviços de emergência e não é enviada automaticamente.",
            11,color=self.p["muted"],wrap=450).pack(
                anchor="w",padx=15,pady=(0,12))
        self._label(right,"Editar dados de emergência",17,True).pack(
            anchor="w",padx=14,pady=(12,5))
        editor=ctk.CTkScrollableFrame(right,fg_color="transparent")
        editor.pack(fill="both",expand=True,padx=8,pady=(0,8))
        self._remaining_fields={}
        self._emergency_entries={}
        for key,label,limit in EMERGENCY_FIELDS:
            typ="long" if limit>1000 else "text"
            self._record_input(editor,key,label,typ,data.get(key,""),limit)
            widget,t=self._remaining_fields[key]
            self._emergency_entries[key]=(widget,t)
        self._button(editor,"Guardar ficha de emergência",
                     self._emergency_save,True,width=242,height=37).pack(
                         anchor="w",padx=10,pady=13)

    def _emergency_save(self):
        try:
            fields={}
            for key,(widget,typ) in self._emergency_entries.items():
                fields[key]=(widget.get("1.0","end-1c") if typ=="long"
                             else widget.get())
            self.store.save_emergency_data(self.active_id,fields)
            self._render()
        except (ValueError,LocalStoreError,OSError) as exc:
            messagebox.showerror("Emergência",str(exc),parent=self)
