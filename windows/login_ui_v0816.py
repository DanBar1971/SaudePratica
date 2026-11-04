"""Windows entry PIN and once-only default profile selection.

No clinical content is constructed or drawn before the PIN is verified.
The default profile is independent of the profile temporarily selected later.
"""
from __future__ import annotations

import os

import customtkinter as ctk
from tkinter import messagebox

from windows import login_pin_v0816 as pin_access


class LoginUiV0816:
    def _pin_entry(self,parent,label):
        self._label(parent,label,12,True).pack(anchor="w",pady=(7,4))
        field=ctk.CTkEntry(
            parent,width=230,height=44,show="●",placeholder_text="4 números",
            fg_color=self.p["field"],text_color=self.p["text"],
            border_color=self.p["line"],
            font=ctk.CTkFont(size=19,weight="bold"))
        field.pack(anchor="w",pady=(0,4))
        return field

    def _profile_options(self,people):
        labels={}
        for p in people:
            key=(str(p.get("name","Perfil"))[:60]+" · "+p["id"][:8])
            labels[key]=p["id"]
        return labels

    def _display_login(self):
        self.p=self._palette()
        self.configure(fg_color=self.p["bg"])
        self._clear()
        page=ctk.CTkFrame(self,fg_color=self.p["bg"])
        page.pack(fill="both",expand=True)
        outer=ctk.CTkFrame(
            page,fg_color=self.p["panel"],border_width=1,
            border_color=self.p["line"],corner_radius=22,width=520)
        outer.pack(expand=True,padx=25,pady=30)
        content=ctk.CTkFrame(outer,fg_color="transparent",width=420)
        content.pack(padx=45,pady=30)
        self._label(content,"🔐  SaúdePrática",28,True,
                    color="#00c9b7").pack(anchor="w",pady=(0,10))
        existing=pin_access.configured(self.store)
        if existing:
            self._label(content,"Introduz o teu PIN para entrar",17,True).pack(
                anchor="w",pady=(0,4))
            self._label(content,
                "O PIN é exclusivo desta instalação Windows.",
                12,color=self.p["muted"],wrap=390).pack(anchor="w",pady=(0,12))
            field=self._pin_entry(content,"PIN de entrada")
            field.bind("<Return>",lambda _evt:self._check_login_pin(field))
            self._login_message=self._label(
                content,"",11,color="#f7aeae",wrap=400)
            self._login_message.pack(anchor="w",pady=(6,10))
            self._button(content,"Entrar",
                         lambda:self._check_login_pin(field),
                         True,width=230,height=44).pack(anchor="w",pady=(8,4))
            field.focus_set()
            return
        self._label(content,"Primeira utilização no Windows",17,True).pack(
            anchor="w",pady=(0,7))
        self._label(content,
            "Escolhe o perfil que abre sempre após introduzires o PIN. "
            "Poderás mudar para os restantes perfis normalmente.",
            12,color=self.p["muted"],wrap=390).pack(anchor="w",pady=(0,12))
        self._login_profile_map=self._profile_options(self.store.profiles())
        self._label(content,"Perfil predefinido",12,True).pack(anchor="w")
        choices=list(self._login_profile_map) or ["Ainda não há perfis"]
        self._login_profile_choice=ctk.CTkOptionMenu(
            content,values=choices,width=330,height=38,
            fg_color=self.p["field"],button_color="#087b8c",
            dropdown_fg_color=self.p["panel"],
            text_color=self.p["text"])
        self._login_profile_choice.pack(anchor="w",pady=(5,12))
        self._login_first_pin=self._pin_entry(content,"Criar PIN (4 números)")
        self._login_confirm_pin=self._pin_entry(content,"Confirmar PIN")
        self._login_message=self._label(
            content,"",11,color="#f7aeae",wrap=400)
        self._login_message.pack(anchor="w",pady=(5,8))
        self._button(content,"Guardar PIN e entrar",
            self._configure_login_pin,True,width=230,height=44).pack(
                anchor="w",pady=(8,4))
        self._login_first_pin.focus_set()

    def _configure_login_pin(self):
        first=self._login_first_pin.get()
        if first!=self._login_confirm_pin.get():
            self._login_message.configure(text="Os dois PINs são diferentes.")
            return
        selected=self._login_profile_map.get(
            self._login_profile_choice.get())
        try:
            pin_access.setup(self.store,first,selected)
        except (ValueError,OSError) as exc:
            self._login_message.configure(text=str(exc))
            return
        self._on_login_unlocked()

    def _check_login_pin(self,field):
        candidate=field.get()
        field.delete(0,"end")
        try:
            success,blocked=pin_access.verify(self.store,candidate)
        except (ValueError,OSError) as exc:
            self._login_message.configure(text=str(exc))
            return
        if success:
            self._on_login_unlocked()
        else:
            self._login_message.configure(text=(
                f"PIN incorreto ou entrada bloqueada. Aguarda {blocked} s."
                if blocked else "PIN incorreto. Tenta novamente."))
            field.focus_set()

    def _on_login_unlocked(self):
        if self.store.profiles() and not pin_access.default_profile(self.store):
            self._display_choose_default_after_unlock()
            return
        self._finish_login()

    def _display_choose_default_after_unlock(self):
        self.p=self._palette()
        self._clear()
        page=ctk.CTkFrame(self,fg_color=self.p["bg"])
        page.pack(fill="both",expand=True)
        card=ctk.CTkFrame(
            page,fg_color=self.p["panel"],border_width=1,
            border_color=self.p["line"],corner_radius=20)
        card.pack(expand=True,padx=32,pady=28)
        self._label(card,"Escolher perfil predefinido",21,True).pack(
            anchor="w",padx=28,pady=(25,7))
        self._label(card,
            "Este perfil abrirá após o PIN. Continuarás a poder trocar de perfil.",
            12,color=self.p["muted"]).pack(anchor="w",padx=28)
        choices=self._profile_options(self.store.profiles())
        selection=ctk.CTkOptionMenu(
            card,values=list(choices),width=310,height=40,
            fg_color=self.p["field"],button_color="#087b8c",
            text_color=self.p["text"],dropdown_fg_color=self.p["panel"])
        selection.pack(padx=28,pady=20)
        def apply():
            try:
                pin_access.set_default(self.store,choices[selection.get()])
                self._finish_login()
            except (OSError,ValueError) as exc:
                messagebox.showerror("Perfil predefinido",str(exc),parent=self)
        self._button(card,"Guardar e entrar",apply,True,
                     width=195,height=39).pack(
                         anchor="w",padx=28,pady=(0,24))

    def _finish_login(self):
        self._login_unlocked=True
        default=pin_access.default_profile(self.store)
        if default:
            self.active_id=default
        elif self.store.profiles() and not self.store.get_profile(self.active_id):
            self.active_id=self.store.profiles()[0]["id"]
        self.editing_profile=self.active_id
        self._render()
        if not os.environ.get("SAUDEPRATICA_SMOKE_REPORT"):
            self.after(900,self._lan_begin_discovery)

    def _pin_options(self):
        surface=self._options_surface
        frame=ctk.CTkFrame(
            surface,fg_color=self.p["panel"],border_width=1,
            border_color=self.p["line"],corner_radius=13)
        frame.pack(fill="x",padx=5,pady=(0,8))
        self._label(frame,"Proteção de entrada · PIN Windows",17,True).pack(
            anchor="w",padx=16,pady=(11,3))
        self._label(frame,
            "O PIN de entrada é diferente do PIN dos backups. "
            "Será solicitado quando voltares a abrir a SaúdePrática.",
            11,color=self.p["muted"],wrap=880).pack(
                anchor="w",padx=16,pady=(0,7))
        people=self.store.profiles()
        options=self._profile_options(people)
        if options:
            line=ctk.CTkFrame(frame,fg_color="transparent")
            line.pack(fill="x",padx=14,pady=(4,11))
            self._label(line,"Perfil predefinido:",12,True).pack(
                side="left",padx=(0,10))
            selection=ctk.CTkOptionMenu(
                line,values=list(options),width=230,
                fg_color=self.p["field"],button_color="#087b8c",
                text_color=self.p["text"],
                dropdown_fg_color=self.p["panel"])
            selection.pack(side="left",padx=(0,9))
            default=pin_access.default_profile(self.store)
            selection.set(next((key for key,pid in options.items()
                                if pid==default),next(iter(options))))
            def save_profile():
                try:
                    pin_access.set_default(self.store,options[selection.get()])
                    messagebox.showinfo(
                        "Perfil predefinido",
                        "Na próxima abertura, a app entrará neste perfil.",
                        parent=self)
                except (ValueError,OSError) as exc:
                    messagebox.showerror("Perfil predefinido",str(exc),parent=self)
            self._button(line,"Guardar perfil predefinido",save_profile,
                         width=194,height=35).pack(side="left")

        group=ctk.CTkFrame(frame,fg_color="transparent")
        group.pack(fill="x",padx=14,pady=(0,14))
        current=self._pin_entry(group,"PIN atual")
        new=self._pin_entry(group,"Novo PIN (4 números)")
        confirm=self._pin_entry(group,"Repetir novo PIN")
        def save_pin():
            if new.get()!=confirm.get():
                messagebox.showerror("Alterar PIN","Os dois PINs novos diferem.",
                                     parent=self)
                return
            try:
                pin_access.change_pin(self.store,current.get(),new.get())
                for entry in (current,new,confirm):
                    entry.delete(0,"end")
                messagebox.showinfo("Alterar PIN","PIN de entrada alterado.",
                                    parent=self)
            except (ValueError,OSError) as exc:
                messagebox.showerror("Alterar PIN",str(exc),parent=self)
        self._button(group,"Alterar PIN de entrada",save_pin,
                     width=194,height=36).pack(anchor="w",pady=(9,0))
