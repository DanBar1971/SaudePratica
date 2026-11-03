"""Experimental Android detection UI. No data sync and no patient data transfer."""
from __future__ import annotations
import os
import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from windows.lan_pair_v084 import Phone, LinkError, lan_ip, ask_to_pair, get_pair_result

class LanUi:
    def _lan_begin_discovery(self):
        # A genuine rescan, even if the mDNS watcher already exists.
        if getattr(self,"_lan_scanning",False):
            return
        self._lan_scanning=True
        self._lan_events.put(("status",
            "A pesquisar Android por mDNS e broadcast Wi-Fi..."))
        def run():
            try:
                self._lan_manager.start()
                self._lan_manager.refresh()
                devices=self._lan_manager.snapshot()
                if devices:
                    info=(f"{len(devices)} dispositivo(s) encontrado(s) "
                          "automaticamente. Escolhe Pedir ligação.")
                else:
                    info=("Ainda não encontrei o Android automaticamente "
                          "(mDNS/UDP). Confirma que está visível, na mesma "
                          "rede local e sem rede convidado/isolamento. "
                          "A ligação por IP continua disponível.")
                self._lan_events.put(("status",info))
            except Exception as exc:
                self._lan_events.put(("status",
                    "Pesquisa indisponível: "+str(exc)[:140]))
            finally:
                self._lan_scanning=False
        threading.Thread(target=run,daemon=True).start()

    def _lan_close(self):
        try:self._lan_manager.close()
        except Exception:pass
        self.destroy()

    def _lan_poll_ui(self):
        try:
            if not self.winfo_exists():return
        except tk.TclError:
            return
        changed=False
        discovered=[]
        for _ in range(30):
            try:event,value=self._lan_events.get_nowait()
            except queue.Empty:break
            if event=="found":
                duplicate=next((p for p in self._lan_devices.values()
                                if p.host==value.host and p.port==value.port),None)
                if duplicate is None:
                    if value.service not in self._lan_devices:
                        discovered.append(value)
                    self._lan_devices[value.service]=value
                    changed=True
            elif event=="removed":
                self._lan_devices.pop(value,None)
                changed=True
            elif event=="status":
                self._lan_status=value
                changed=True
            elif event=="pair_requested":
                phone,code=value
                self._lan_pair_code=code
                self._lan_status="Pedido enviado a "+phone.name+" · código "+code
                changed=True
            elif event=="pair_result":
                self._lan_requested=False
                self._lan_status=value
                changed=True
        if changed and self.page=="sync":self._render()
        for phone in discovered:
            if phone.service in self._lan_seen:continue
            self._lan_seen.add(phone.service)
            if self.page=="sync" or os.environ.get("SAUDEPRATICA_SMOKE_REPORT"):
                continue
            def offer(item=phone):
                if not self.winfo_exists():return
                if messagebox.askyesno(
                    "SaúdePrática · Telemóvel encontrado",
                    "Foi encontrado «"+item.name+"» na mesma rede.\n\n"
                    "Queres abrir a página de ligação para pedir autorização?\n\n"
                    "Este primeiro teste NÃO transfere dados clínicos.",
                    parent=self):
                    self.navigate("sync")
            self.after(10,offer)
        self.after(330,self._lan_poll_ui)

    def _sync_page(self):
        self._heading("Sincronização Wi-Fi · ligação experimental",
                      "Windows reconhece o Android e pede autorização")
        warning=self._card(self.body)
        warning.pack(fill="x",padx=6,pady=(0,12))
        self._label(warning,"TESTE DE LIGAÇÃO · nenhum dado clínico é transferido",
                    14,True,color="#00c9b7").pack(anchor="w",padx=15,pady=(10,3))
        self._label(warning,
            "O objetivo é verificar a descoberta mDNS + UDP/broadcast e a autorização. "
            "Não sincroniza medicação, perfis, agenda, documentos ou fotografias.",
            12,color=self.p["muted"],wrap=980).pack(anchor="w",padx=15,pady=(0,12))
        self._label(self.body,"Telemóveis SaúdePrática encontrados",18,True).pack(
            anchor="w",padx=12,pady=(5,6))
        devices=self._card(self.body)
        devices.pack(fill="x",padx=7,pady=(0,13))
        if not self._lan_devices:
            self._label(devices,
                "Ainda não apareceu nenhum Android. Abre a aplicação de teste "
                "«SaúdePrática Ligação» no telemóvel e toca em «Tornar visível». "
                "Ambos devem estar na mesma rede local, sem isolamento de clientes.",
                12,color=self.p["muted"],wrap=950).pack(
                    anchor="w",padx=18,pady=16)
        for phone in list(self._lan_devices.values())[:12]:
            line=ctk.CTkFrame(devices,fg_color=self.p["panel2"],corner_radius=12)
            line.pack(fill="x",padx=10,pady=5)
            self._label(line,"📱  "+phone.name,14,True).pack(
                side="left",padx=(13,17),pady=12)
            self._label(line,phone.target,11,color=self.p["muted"]).pack(
                side="left",pady=12)
            self._button(line,"Pedir ligação",lambda item=phone:
                         self._lan_request(item),True,width=160,height=34).pack(
                             side="right",padx=10,pady=6)
        row=ctk.CTkFrame(self.body,fg_color="transparent")
        row.pack(fill="x",padx=12,pady=(3,7))
        self._button(row,"Procurar novamente",
                     self._lan_refresh,width=173,height=34).pack(side="left")
        self._label(self.body,
            "Descoberta automática usa mDNS e broadcast UDP na rede local. "
            "Se a rede bloquear ambos os protocolos, utiliza Ligar por IP "
            "como alternativa. Não é necessário configurar portas no router.",
            11,color=self.p["muted"],wrap=1050).pack(
                anchor="w",padx=16,pady=(5,0))
        self._label(row,"Ligar por IP (alternativa)",
                    12,True,color=self.p["muted"]).pack(side="left",padx=(22,8))
        self.lan_manual_ip=ctk.CTkEntry(row,width=145,height=33,
                 placeholder_text="192.168.1.40",fg_color=self.p["field"],
                 border_color=self.p["line"],text_color=self.p["text"])
        self.lan_manual_ip.pack(side="left")
        self.lan_manual_port=ctk.CTkEntry(row,width=82,height=33,
                 placeholder_text="Porta",fg_color=self.p["field"],
                 border_color=self.p["line"],text_color=self.p["text"])
        self.lan_manual_port.pack(side="left",padx=7)
        self._button(row,"Pedir por IP",self._lan_manual_request,
                     width=126,height=34).pack(side="left")
        status=self._card(self.body)
        status.pack(fill="x",padx=7,pady=(12,6))
        self._label(status,self._lan_status,14,True,color="#00c9b7",
                    wrap=990).pack(anchor="w",padx=15,pady=12)
        if self._lan_requested and self._lan_pair_code:
            self._label(status,"Confirma no Android que o código é "+
                        self._lan_pair_code+". A autorização é obrigatória.",
                        12,color=self.p["text"]).pack(anchor="w",padx=15,pady=(0,12))
        self._label(self.body,
            "Esta prova de ligação não usa cifragem e NÃO transporta "
            "informação médica. A futura sincronização exigirá um protocolo "
            "autenticado e cifrado, resolução de conflitos e confirmação antes de gravar.",
            11,color=self.p["muted"],wrap=990).pack(
                anchor="w",padx=15,pady=12)

    def _lan_refresh(self):
        self._lan_status="A pesquisar novamente por mDNS e UDP..."
        self._lan_begin_discovery()
        self._render()

    def _lan_manual_request(self):
        try:
            host=lan_ip(self.lan_manual_ip.get())
            port=int(self.lan_manual_port.get().strip())
            if not 1<=port<=65535:raise ValueError("Porta inválida.")
            phone=Phone(service="manual-"+host,name="Android por IP",
                        host=host,port=port)
        except (LinkError,ValueError) as exc:
            messagebox.showwarning("Ligação manual",
                "Introduz o IPv4 local e a porta indicada no Android.\n"+str(exc),
                parent=self)
            return
        self._lan_request(phone)

    def _lan_request(self,phone):
        if self._lan_requested:
            messagebox.showinfo("SaúdePrática",
                "Já existe um pedido de ligação em curso.",parent=self)
            return
        if not messagebox.askyesno("Confirmar pedido de ligação",
            "Pedir autorização ao telemóvel «"+phone.name+"»?\n\n"
            "Não serão enviados dados clínicos.\n"
            "O Android terá de aceitar o código.",parent=self):
            return
        self._lan_requested=True
        self._lan_pair_code=""
        self._lan_status="A contactar "+phone.name+"..."
        self._render()
        def task():
            try:
                code,request_id=ask_to_pair(phone)
                self._lan_events.put(("pair_requested",(phone,code)))
                for _ in range(25):
                    time.sleep(2)
                    state=get_pair_result(phone,request_id)
                    if state=="pending":continue
                    result={
                        "accepted":"Ligação aprovada em "+phone.name+
                                   ". Teste concluído, sem transferir dados.",
                        "rejected":"O pedido foi recusado pelo Android.",
                        "expired":"O pedido expirou; tenta novamente.",
                    }[state]
                    self._lan_events.put(("pair_result",result))
                    return
                self._lan_events.put(("pair_result","Tempo de autorização esgotado."))
            except (LinkError,ValueError,OSError) as exc:
                self._lan_events.put(("pair_result","Ligação falhou: "+str(exc)))
        threading.Thread(target=task,daemon=True).start()
