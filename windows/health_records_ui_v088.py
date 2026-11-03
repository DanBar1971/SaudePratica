"""SaúdePrática Windows 0.8.8: clinical status and health expenses editors.

Both modules intentionally use a selected profile, not family-wide records.
Data typed here remain local until explicit backup; they are not synchronized
with Android's encrypted clinical/expenses indexes.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from windows.clinical_expenses_v088 import (
    CLINICAL_TYPES, CLINICAL_STATES, EXPENSE_TYPES, TAX_STATES,
    annual_summary, cents_from_pt, date_iso, euro_text,
)
from windows.secure_store import LocalStoreError


class HealthRecordsUiV088:
    def _clinical(self):
        self._health_module("clinical")

    def _expenses(self):
        self._health_module("expenses")

    def _health_select(self, kind, record_id):
        self._health_selection[kind] = record_id
        self._render()

    def _health_new(self, kind):
        self._health_selection[kind] = None
        self._render()

    def _health_change_year(self, direction):
        self._expense_year = max(1900, min(9999, self._expense_year + direction))
        self._health_selection["expenses"] = None
        self._render()

    def _health_field(self, parent, label, key, value, *, width=300):
        line=ctk.CTkFrame(parent, fg_color="transparent")
        line.pack(fill="x", padx=8, pady=(3, 5))
        self._label(line, label, 11, True, color=self.p["muted"]).pack(
            anchor="w", pady=(0, 3))
        entry=ctk.CTkEntry(
            line, height=35, fg_color=self.p["field"],
            text_color=self.p["text"], border_color=self.p["line"],
            corner_radius=9)
        entry.insert(0, str(value or ""))
        entry.pack(fill="x", expand=True)
        self._health_fields[key]=entry
        return entry

    def _health_choice(self, parent, label, key, values, value):
        line=ctk.CTkFrame(parent, fg_color="transparent")
        line.pack(fill="x", padx=8, pady=(4, 5))
        self._label(line, label, 11, True, color=self.p["muted"]).pack(
            anchor="w", pady=(0, 3))
        variable=ctk.StringVar(value=value if value in values else values[0])
        ctk.CTkOptionMenu(
            line, variable=variable, values=list(values), height=34,
            fg_color=self.p["panel2"], button_color="#0e6976",
            text_color=self.p["text"], dropdown_fg_color=self.p["panel"],
            dropdown_text_color=self.p["text"]).pack(fill="x")
        self._health_fields[key]=variable

    def _health_notes(self, parent, label, key, value):
        box=ctk.CTkFrame(parent, fg_color="transparent")
        box.pack(fill="x", padx=8, pady=(4, 7))
        self._label(box, label, 11, True, color=self.p["muted"]).pack(
            anchor="w", pady=(0, 3))
        text=ctk.CTkTextbox(
            box, height=88, fg_color=self.p["field"],
            text_color=self.p["text"], border_color=self.p["line"],
            border_width=1, corner_radius=10, wrap="word")
        text.insert("1.0", str(value or ""))
        text.pack(fill="x")
        self._health_fields[key]=text
        self._health_multiline.add(key)

    def _health_documents_choice(self, parent, data, profile_id):
        entries=self.store.imported_assets(profile_id)
        options={"Sem documento associado": ""}
        for i, item in enumerate(entries, 1):
            digest=item.get("sha256")
            if not isinstance(digest, str):
                continue
            label=f"{i:02d} · {str(item.get('display_name') or item.get('filename') or 'Documento')[:75]}"
            options[label]=digest
        self._health_documents=options
        chosen=data.get("document_sha256", "")
        current=next((name for name,digest in options.items()
                      if digest==chosen), "Sem documento associado")
        self._health_doc_var=ctk.StringVar(value=current)
        wrapper=ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.pack(fill="x",padx=8,pady=(4, 8))
        self._label(wrapper, "Documento associado (deste perfil)", 11,
                    True,color=self.p["muted"]).pack(anchor="w",pady=(0,3))
        ctk.CTkOptionMenu(
            wrapper,variable=self._health_doc_var,values=list(options),
            fg_color=self.p["panel2"],button_color="#0e6976",
            text_color=self.p["text"],dropdown_fg_color=self.p["panel"],
            dropdown_text_color=self.p["text"],height=34).pack(fill="x")
        controls=ctk.CTkFrame(wrapper,fg_color="transparent")
        controls.pack(fill="x",pady=(4,0))
        self._button(controls,"Ver documentos do perfil",
                     lambda:self.navigate("documents"),
                     width=204,height=30).pack(side="left")
        if chosen and chosen in options.values():
            self._button(controls,"Abrir documento",
                         lambda digest=chosen:self._health_open_document(digest),
                         width=144,height=30).pack(side="left",padx=7)

    def _health_open_document(self, digest):
        profile=self.store.get_profile(self.active_id) if self.active_id else None
        if not profile or not any(
            x.get("sha256")==digest and x.get("profile_id")==profile["id"]
            for x in self.store.imported_assets(profile["id"])):
            messagebox.showerror("Documento",
                "Documento indisponível neste perfil.",parent=self)
            return
        self.doc_selected_digest=digest
        self.doc_selected_profile=profile["id"]
        self.doc_page_index=0
        self.navigate("documents")

    def _health_form_data(self, kind):
        out={}
        for key,widget in self._health_fields.items():
            if key in self._health_multiline:
                out[key]=widget.get("1.0","end-1c")
            else:
                out[key]=widget.get()
        out["document_sha256"]=self._health_documents.get(
            self._health_doc_var.get(),"")
        if kind=="expenses":
            out["amountCents"]=cents_from_pt(out.pop("amount_input"))
            out["reimbursedCents"]=cents_from_pt(out.pop("refund_input"))
        return out

    def _health_save(self, kind):
        if not self.active_id:
            return
        try:
            fields=self._health_form_data(kind)
            item=self.store.save_health_record(
                self.active_id, kind, fields,self._health_selection.get(kind))
            self._health_selection[kind]=item["id"]
            if kind=="expenses":
                self._expense_year=int(item["date"][:4])
            self._render()
        except (ValueError,LocalStoreError,OSError) as exc:
            messagebox.showerror("Guardar registo",str(exc),parent=self)

    def _health_delete(self,kind,record_id):
        if not self.active_id or not record_id:
            return
        if not messagebox.askyesno("Apagar registo",
            "Queres remover este registo do perfil selecionado?\n"
            "O documento associado não será apagado.",
            parent=self):
            return
        try:
            self.store.delete_health_record(self.active_id,kind,record_id)
            self._health_selection[kind]=None
            self._render()
        except (ValueError,LocalStoreError,OSError) as exc:
            messagebox.showerror("Apagar registo",str(exc),parent=self)

    def _health_export_expenses(self):
        profile=self.store.get_profile(self.active_id) if self.active_id else None
        if not profile:
            return
        year=self._expense_year
        entries=[x for x in self.store.health_records(profile["id"],"expenses")
                 if str(x.get("date","")).startswith(str(year)+"-")]
        if not entries:
            messagebox.showinfo("Exportar despesas","Não existem despesas neste ano.",
                                parent=self)
            return
        if not messagebox.askyesno(
            "Exportação sem encriptação",
            "O CSV contém informação pessoal e financeira. Será guardado "
            "sem encriptação fora da SaúdePrática. Continuar?",parent=self):
            return
        path=filedialog.asksaveasfilename(
            parent=self,title="Exportar despesas de saúde para CSV",
            defaultextension=".csv",
            initialfile=f"SaudePratica-despesas-{year}.csv",
            filetypes=[("CSV (Excel)","*.csv")])
        if not path:
            return
        def safe(value):
            text=str(value or "")
            return "'"+text if text.startswith(("=","+","-","@","\t","\r")) else text
        try:
            dest=Path(path)
            with dest.open("w",encoding="utf-8-sig",newline="") as stream:
                writer=csv.writer(stream,delimiter=";")
                writer.writerow(("Data","Categoria","Entidade",
                    "Descrição","Número da fatura","NIF",
                    "Valor (€)","Reembolsado (€)","Estado e-Fatura","Notas"))
                for x in entries:
                    writer.writerow((
                        safe(x.get("date")),safe(x.get("category")),
                        safe(x.get("merchant")),safe(x.get("description")),
                        safe(x.get("receiptNumber")),safe(x.get("supplierNif")),
                        euro_text(x.get("amountCents",0)),
                        euro_text(x.get("reimbursedCents",0)),
                        safe(x.get("taxStatus")),safe(x.get("notes"))))
            messagebox.showinfo("Despesas", "CSV exportado. Guarda-o em segurança.",
                                parent=self)
        except (OSError,ValueError) as exc:
            messagebox.showerror("Exportar despesas",str(exc),parent=self)

    def _health_module(self, kind):
        clinical=(kind=="clinical")
        name="Situação Clínica" if clinical else "Despesas de Saúde"
        person=self.store.get_profile(self.active_id) if self.active_id else None
        self.wallpaper_shell.glass_enabled=False
        self._heading(name, "Registos do perfil: " + str(person.get("name",""))
                      if person else "Seleciona um perfil primeiro.")
        if not person:
            return
        if not isinstance(getattr(self,"_health_selection",None),dict):
            self._health_selection={"clinical":None,"expenses":None}
        if not isinstance(getattr(self,"_expense_year",None),int):
            self._expense_year=date.today().year
        rows=self.store.health_records(person["id"],kind)
        if not clinical:
            rows=[r for r in rows if str(r.get("date","")).startswith(
                str(self._expense_year)+"-")]
        chosen=self._health_selection.get(kind)
        active=next((r for r in rows if r.get("id")==chosen),None)
        if active is None:
            self._health_selection[kind]=None
        data=active or {}
        split=ctk.CTkFrame(self.body,fg_color="transparent")
        split.pack(fill="both",expand=True,padx=(5,7),pady=(0,7))
        split.grid_rowconfigure(0,weight=1)
        split.grid_columnconfigure(0,weight=9,uniform="health")
        split.grid_columnconfigure(1,weight=11,uniform="health")
        left=ctk.CTkFrame(split,fg_color=self.p["panel"],corner_radius=14,
                          border_color=self.p["line"],border_width=1)
        right=ctk.CTkFrame(split,fg_color=self.p["panel"],corner_radius=14,
                           border_color=self.p["line"],border_width=1)
        left.grid(row=0,column=0,sticky="nsew",padx=(1,7))
        right.grid(row=0,column=1,sticky="nsew",padx=(7,1))
        heading=ctk.CTkFrame(left,fg_color="transparent")
        heading.pack(fill="x",padx=13,pady=(12,5))
        self._label(heading,
                    "Histórico clínico" if clinical else
                    f"Despesas de {self._expense_year}",
                    17,True).pack(side="left")
        self._button(heading,"+ Novo registo",
                     lambda:self._health_new(kind),True,
                     width=130).pack(side="right")
        if clinical:
            self._label(left,f"{len(rows)} registo(s) deste perfil",11,
                        color=self.p["muted"]).pack(
                            anchor="w",padx=15,pady=(0,7))
        else:
            tools=ctk.CTkFrame(left,fg_color="transparent")
            tools.pack(fill="x",padx=12,pady=(0,7))
            self._button(tools,"‹",lambda:self._health_change_year(-1),
                         width=38).pack(side="left")
            self._label(tools,str(self._expense_year),15,True).pack(
                side="left",padx=11)
            self._button(tools,"›",lambda:self._health_change_year(1),
                         width=38).pack(side="left")
            self._button(tools,"Exportar CSV",self._health_export_expenses,
                         width=125).pack(side="right")
            summary=annual_summary(rows,self._expense_year)
            # Always recompute from ALL entries for this selected profile.
            summary=annual_summary(self.store.health_records(person["id"],kind),
                                   self._expense_year)
            self._label(left,
                f"Total: {euro_text(summary['amountCents'])}   ·   "
                f"Reembolsado: {euro_text(summary['reimbursedCents'])}\n"
                f"Por suportar: {euro_text(summary['remainingCents'])}",
                13,True,wrap=480).pack(anchor="w",padx=14,pady=(1,10))
        listing=ctk.CTkScrollableFrame(left,fg_color="transparent")
        listing.pack(fill="both",expand=True,padx=6,pady=(0,7))
        if not rows:
            self._label(listing,"Ainda não há registos neste período.",
                        13,color=self.p["muted"]).pack(
                            anchor="w",padx=12,pady=18)
        for record in rows:
            is_active=active is not None and record["id"]==active["id"]
            tile=ctk.CTkFrame(
                listing,fg_color=self.p["panel2"],corner_radius=10,
                border_width=2 if is_active else 1,
                border_color="#00c9b7" if is_active else self.p["line"])
            tile.pack(fill="x",padx=3,pady=4)
            header=ctk.CTkFrame(tile,fg_color="transparent")
            header.pack(fill="x",padx=11,pady=(8,2))
            title=(record.get("title","") if clinical else
                   (record.get("merchant") or record.get("description") or
                    record.get("category","Despesa")))
            self._label(header,str(title)[:120],13,True,
                        wrap=300).pack(side="left",fill="x",expand=True)
            if not clinical:
                self._label(header,euro_text(record.get("amountCents",0)),
                            13,True,color="#00b4a6").pack(side="right")
            caption=(str(record.get("date",""))+"  ·  "+
                     str(record.get("category","")))
            self._label(tile,caption,11,color=self.p["muted"]).pack(
                anchor="w",padx=11,pady=(2,2))
            self._button(tile,"Abrir / Editar",
                         lambda rid=record["id"]:self._health_select(kind,rid),
                         width=123,height=29).pack(anchor="e",padx=11,pady=(0,8))

        line=ctk.CTkFrame(right,fg_color="transparent")
        line.pack(fill="x",padx=13,pady=(11,4))
        self._label(line,"Editar registo" if active else "Novo registo",
                    17,True).pack(side="left")
        if active:
            self._button(line,"Apagar",lambda uid=active["id"]:
                         self._health_delete(kind,uid),
                         width=75,height=31).pack(side="right",padx=(7,0))
        self._button(line,"Guardar",lambda:self._health_save(kind),
                     True,width=107,height=33).pack(side="right")
        form=ctk.CTkScrollableFrame(right,fg_color="transparent",corner_radius=0)
        form.pack(fill="both",expand=True,padx=8,pady=(0,10))
        self._health_fields={}
        self._health_multiline=set()
        if clinical:
            self._health_field(form,"Título / situação *","title",
                               data.get("title",""))
            self._health_field(form,"Data (DD/MM/AAAA) *","date",
                               data.get("date",date.today().strftime("%d/%m/%Y")))
            self._health_choice(form,"Tipo","category",
                                CLINICAL_TYPES,data.get("category","Consulta"))
            self._health_choice(form,"Estado registado","status",
                                CLINICAL_STATES,data.get("status","Por avaliar"))
            self._health_field(form,"Unidade de saúde / serviço","unit",
                               data.get("unit",""))
            self._health_field(form,"Profissional / médico","professional",
                               data.get("professional",""))
            self._health_field(form,"Próxima avaliação (opcional)","next_date",
                               data.get("next_date",""))
            self._health_notes(form,"Descrição / observações","description",
                               data.get("description",""))
        else:
            self._health_field(form,"Data da fatura (DD/MM/AAAA) *","date",
                               data.get("date",date.today().strftime("%d/%m/%Y")))
            self._health_choice(form,"Categoria","category",
                                EXPENSE_TYPES,data.get("category","Farmácia"))
            self._health_field(form,"Entidade / prestador","merchant",
                               data.get("merchant",""))
            self._health_field(form,"Descrição","description",
                               data.get("description",""))
            self._health_field(form,"Número da fatura","receiptNumber",
                               data.get("receiptNumber",""))
            self._health_field(form,"NIF do emitente","supplierNif",
                               data.get("supplierNif",""))
            self._health_field(form,"Total (€)","amount_input",
                               (euro_text(data["amountCents"]).removesuffix(" €")
                                if "amountCents" in data else "0,00"))
            self._health_field(form,"Reembolso (€)","refund_input",
                               (euro_text(data["reimbursedCents"]).removesuffix(" €")
                                if "reimbursedCents" in data else "0,00"))
            self._health_choice(form,"Estado no e-Fatura (manual)","taxStatus",
                                TAX_STATES,data.get("taxStatus","Por verificar"))
            self._health_notes(form,"Notas","notes",data.get("notes",""))
        self._health_documents_choice(form,data,person["id"])
        self._label(form,
            "Registo local do Windows. Não substitui informação médica "
            "nem valida automaticamente o IRS/e-Fatura. A sincronização "
            "com os módulos Android ainda não está ativa.",
            11,color=self.p["muted"],wrap=490).pack(
                anchor="w",padx=9,pady=(6,9))
