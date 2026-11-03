"""Windows 0.8.7: Android-style Options hierarchy and editable Web shortcuts."""
from __future__ import annotations

import webbrowser
from tkinter import messagebox
import customtkinter as ctk

from windows.important_links_v087 import (
    upsert_link, delete_link, move_link, validate_link,
)
from windows.secure_store import LocalStoreError

THEME_KEYS = {"system":"theme_system","dark":"theme_dark","light":"theme_light"}
LANG_NAMES = {"pt":"Português","en":"English","fr":"Français",
              "de":"Deutsch","es":"Español"}


class LinksOptionsV087:
    def _open_important_link(self, identifier):
        link = next((x for x in self.store.important_links()
                     if x["id"]==identifier), None)
        if link is None:
            messagebox.showerror("Atalhos","Atalho já não existe.",parent=self)
            return
        try:
            target = validate_link(link)["url"]
            if not webbrowser.open(target, new=2):
                raise RuntimeError("O Windows não conseguiu abrir o navegador.")
        except (ValueError,RuntimeError,OSError) as exc:
            messagebox.showerror("Atalhos",str(exc),parent=self)

    def _shortcuts(self):
        self._heading("Atalhos Importantes",
                      "Ligações Web úteis · não alteram dados clínicos.")
        try:links=self.store.important_links()
        except LocalStoreError as exc:
            messagebox.showerror("Atalhos",str(exc),parent=self)
            return
        actions=ctk.CTkFrame(self.body,fg_color="transparent")
        actions.pack(fill="x",padx=6,pady=(2,12))
        self._button(actions,"Gerir atalhos nas Opções",
                     lambda:self.navigate("options"),
                     True,width=228,height=36).pack(side="right")
        listing=ctk.CTkScrollableFrame(self.body,fg_color="transparent")
        listing.pack(fill="both",expand=True,padx=5)
        if not links:
            self._label(listing,"Ainda não existem atalhos. Adiciona-os em Opções.",
                        13,color=self.p["muted"]).pack(anchor="w",padx=12,pady=18)
        for i,item in enumerate(links):
            row=ctk.CTkFrame(listing,fg_color=self.p["panel"],
                             border_width=1,border_color=self.p["line"],
                             corner_radius=12)
            row.pack(fill="x",padx=7,pady=5)
            self._label(row,"🔗",22,True).pack(side="left",padx=(14,13),pady=12)
            details=ctk.CTkFrame(row,fg_color="transparent")
            details.pack(side="left",fill="x",expand=True,pady=11)
            self._label(details,item["title"],14,True).pack(anchor="w")
            self._label(details,item["url"],11,color=self.p["muted"],
                        wrap=760).pack(anchor="w")
            self._button(row,"Abrir website",
                         lambda key=item["id"]:self._open_important_link(key),
                         True,width=135,height=34).pack(side="right",padx=13)

    def _options_link_edit(self, identifier):
        item=next((x for x in self.store.important_links()
                   if x["id"]==identifier),None)
        if item is None:return
        self._link_edit_id=identifier
        self._render()

    def _options_link_new(self):
        self._link_edit_id=None
        self._render()

    def _options_link_save(self):
        title=self._link_title_var.get()
        url=self._link_url_var.get()
        try:
            links=upsert_link(self.store.important_links(),title,url,
                              getattr(self,"_link_edit_id",None))
            self.store.save_important_links(links)
        except (LocalStoreError,ValueError,OSError) as exc:
            messagebox.showerror("Gerir atalhos",str(exc),parent=self)
            return
        self._link_edit_id=None
        self._render()

    def _options_link_delete(self, identifier):
        item=next((x for x in self.store.important_links()
                   if x["id"]==identifier),None)
        if not item:return
        if not messagebox.askyesno("Remover atalho",
            "Remover o atalho «"+item["title"]+"»?\n"
            "A remoção não altera o website externo.",parent=self):
            return
        try:
            self.store.save_important_links(
                delete_link(self.store.important_links(),identifier))
        except (LocalStoreError,ValueError,OSError) as exc:
            messagebox.showerror("Gerir atalhos",str(exc),parent=self)
            return
        if getattr(self,"_link_edit_id",None)==identifier:
            self._link_edit_id=None
        self._render()

    def _options_link_move(self, identifier, direction):
        try:
            self.store.save_important_links(
                move_link(self.store.important_links(),identifier,direction))
        except (LocalStoreError,ValueError,OSError) as exc:
            messagebox.showerror("Gerir atalhos",str(exc),parent=self)
            return
        self._render()

    def _settings_page(self):
        self._heading("Opções", "Preferências, ferramentas e atalhos Web")
        main=ctk.CTkScrollableFrame(self.body,fg_color="transparent")
        main.pack(fill="both",expand=True,padx=7,pady=(0,5))
        self._options_surface=main

        pref=ctk.CTkFrame(main,fg_color=self.p["panel"],
                          border_width=1,border_color=self.p["line"],
                          corner_radius=13)
        pref.pack(fill="x",padx=5,pady=(0,8))
        self._label(pref,"Aspeto e Idiomas",17,True).pack(
            anchor="w",padx=16,pady=(12,2))
        inner=ctk.CTkFrame(pref,fg_color="transparent")
        inner.pack(fill="x",padx=18,pady=(3,9))
        self._label(inner,self.t("theme"),12,True).pack(side="left",padx=(0,9))
        values={self.t(k):v for v,k in THEME_KEYS.items()}
        self.theme_values=values
        theme=ctk.CTkOptionMenu(
            inner,values=list(values),width=160,
            fg_color=self.p["panel2"],button_color="#087b8c",
            text_color=self.p["text"],
            dropdown_text_color=self.p["text"],
            dropdown_fg_color=self.p["panel"],
            command=self._change_theme)
        theme.set(next((key for key,value in values.items()
                        if value==self.theme),next(iter(values))))
        theme.pack(side="left",padx=(0,23))
        self._label(inner,self.t("language"),12,True).pack(side="left",padx=(0,9))
        locale=ctk.CTkOptionMenu(
            inner,values=list(LANG_NAMES.values()),width=170,
            fg_color=self.p["panel2"],button_color="#087b8c",
            text_color=self.p["text"],
            dropdown_text_color=self.p["text"],
            dropdown_fg_color=self.p["panel"],
            command=self._change_language)
        locale.set(LANG_NAMES[self.lang])
        locale.pack(side="left")
        self._label(pref,self.t("notice"),11,color=self.p["muted"],
                    wrap=970).pack(anchor="w",padx=18,pady=(0,11))

        tools=ctk.CTkFrame(main,fg_color=self.p["panel"],
                           border_width=1,border_color=self.p["line"],
                           corner_radius=13)
        tools.pack(fill="x",padx=5,pady=(0,8))
        self._label(tools,"Ferramentas",17,True).pack(anchor="w",padx=16,pady=(12,7))
        actions=ctk.CTkFrame(tools,fg_color="transparent")
        actions.pack(fill="x",padx=15,pady=(0,13))
        self._button(actions,"💡 Dicas e Informações",
                     lambda:self.navigate("info"),width=190,height=38).pack(
                         side="left",padx=(0,8))
        self._button(actions,"🔐 Backup e Restauro",
                     lambda:self.navigate("backup"),width=184,height=38).pack(
                         side="left",padx=(0,8))
        self._button(actions,"🔄 Sincronização",
                     lambda:self.navigate("sync"),width=165,height=38).pack(
                         side="left",padx=(0,8))
        self._button(actions,"🔗 Ver Atalhos",
                     lambda:self.navigate("shortcuts"),width=155,height=38).pack(
                         side="left")

        links_card=ctk.CTkFrame(main,fg_color=self.p["panel"],
                                border_width=1,border_color=self.p["line"],
                                corner_radius=13)
        links_card.pack(fill="x",padx=5,pady=(0,10))
        self._label(links_card,"Gestor de Atalhos Web",17,True).pack(
            anchor="w",padx=16,pady=(13,2))
        self._label(links_card,
            "Criar, editar, remover ou mudar a ordem. Os atalhos são comuns "
            "à instalação Windows e ficam protegidos no backup.",
            11,color=self.p["muted"]).pack(anchor="w",padx=16,pady=(0,9))
        try:
            links=self.store.important_links()
        except LocalStoreError as exc:
            self._label(links_card,str(exc),12,color="#e88585").pack(anchor="w")
            return
        for index,item in enumerate(links):
            line=ctk.CTkFrame(links_card,fg_color=self.p["panel2"],
                              corner_radius=9)
            line.pack(fill="x",padx=14,pady=2)
            ident=item["id"]
            self._label(line,f"{index+1}. {item['title']}",12,True,
                        wrap=280).pack(side="left",padx=11,pady=8)
            self._label(line,item["url"],10,color=self.p["muted"],
                        wrap=340).pack(side="left",padx=9)
            self._button(line,"Remover",
                         lambda key=ident:self._options_link_delete(key),
                         width=76,height=30).pack(side="right",padx=(0,7))
            self._button(line,"Editar",
                         lambda key=ident:self._options_link_edit(key),
                         width=62,height=30).pack(side="right",padx=(0,5))
            self._button(line,"↓",
                         lambda key=ident:self._options_link_move(key,1),
                         width=37,height=30).pack(side="right",padx=(0,5))
            self._button(line,"↑",
                         lambda key=ident:self._options_link_move(key,-1),
                         width=37,height=30).pack(side="right",padx=(0,5))

        existing=next((x for x in links if x["id"]==
                        getattr(self,"_link_edit_id",None)),None)
        form=ctk.CTkFrame(links_card,fg_color="transparent")
        form.pack(fill="x",padx=15,pady=(10,14))
        self._label(form,"Editar atalho" if existing else "Adicionar atalho",13,
                    True).pack(anchor="w",pady=(0,6))
        fields=ctk.CTkFrame(form,fg_color="transparent")
        fields.pack(fill="x")
        self._link_title_var=ctk.StringVar(
            value=existing["title"] if existing else "")
        self._link_url_var=ctk.StringVar(
            value=existing["url"] if existing else "")
        ctk.CTkEntry(fields,textvariable=self._link_title_var,width=235,
                     placeholder_text="Nome do atalho",height=35,
                     fg_color=self.p["field"],
                     text_color=self.p["text"]).pack(side="left",padx=(0,7))
        ctk.CTkEntry(fields,textvariable=self._link_url_var,width=470,
                     placeholder_text="https://...",height=35,
                     fg_color=self.p["field"],
                     text_color=self.p["text"]).pack(side="left",padx=(0,8))
        self._button(fields,"Guardar",
                     self._options_link_save,True,width=94,height=35).pack(
                         side="left",padx=(0,7))
        self._button(fields,"Novo / Limpar",
                     self._options_link_new,width=116,height=35).pack(
                         side="left")

    def _tips(self):
        self._heading("Dicas e Informações",
                      "Orientações de utilização da SaúdePrática")
        self._button(self.body,"‹ Voltar às Opções",
                     lambda:self.navigate("options"),width=177).pack(
                         anchor="w",padx=9,pady=(0,10))
        tips=(
            ("Escolhe o perfil certo",
             "Confirma sempre o perfil selecionado no canto superior direito "
             "antes de consultar ou modificar dados."),
            ("Faz cópias de segurança",
             "Nas Opções, abre Backup e Restauro. Guarda uma cópia protegida "
             "por palavra-passe antes de instalar novas versões."),
            ("Confirma as tomas reais",
             "Uma toma prevista ou atrasada não equivale a uma toma realizada. "
             "Regista Tomei apenas depois de tomar a medicação."),
            ("Documentos privados",
             "Os originais ficam protegidos na conta Windows. Guardar como "
             "ou imprimir pode criar cópias externas não encriptadas."),
            ("Sincronização",
             "A ligação ao telemóvel por Wi-Fi ainda não equivale à "
             "sincronização automática de medicação, consultas ou tomas."),
        )
        scroll=ctk.CTkScrollableFrame(self.body,fg_color="transparent")
        scroll.pack(fill="both",expand=True)
        for title,description in tips:
            row=self._card(scroll)
            row.pack(fill="x",padx=6,pady=5)
            self._label(row,title,14,True).pack(anchor="w",padx=14,pady=(12,3))
            self._label(row,description,12,color=self.p["muted"],
                        wrap=990).pack(anchor="w",padx=14,pady=(0,14))
