"""Single SaúdePrática backup screen with FAMILY or PROFILE .spbackup only.

UI never treats the source archive as a cloud sync. Restore is previewed,
explicit, non-duplicating, and creates an encrypted safety copy first.
"""
from pathlib import Path
from tkinter import filedialog,messagebox
import customtkinter as ctk
from windows.progress_dialog_v073 import run_progress

def render_backup(app):
    app._heading("Backup e Restauro",
        "Um formato encriptado .spbackup · Família inteira ou um perfil")
    wrapper=app._card(app.body)
    wrapper.pack(fill="x",pady=8)
    inner=ctk.CTkFrame(wrapper,fg_color="transparent")
    inner.pack(fill="x",padx=25,pady=20)
    app._label(inner,"Palavra-passe de proteção e restauro",15,True).pack(anchor="w")
    password=ctk.CTkEntry(inner,show="●",height=43,width=365,
        fg_color=app.p["field"],border_color=app.p["line"])
    password.pack(anchor="w",pady=(5,10))
    app._label(inner,"Confirmar palavra-passe (na exportação)",13,True).pack(anchor="w")
    repeat=ctk.CTkEntry(inner,show="●",height=43,width=365,
        fg_color=app.p["field"],border_color=app.p["line"])
    repeat.pack(anchor="w",pady=(5,16))
    app._label(inner,
        "Um único formato para Android, Windows e futuro macOS. "
        "Restaurar um perfil que já existe SUBSTITUI os seus dados apenas "
        "depois de mostrar a comparação e obter confirmação. "
        "Cria sempre um backup de segurança antes de substituir.",
        13,color=app.p["muted"],wrap=930).pack(anchor="w",pady=(0,16))
    def export(selected=None):
        pwd=password.get()
        if len(pwd)<10 or pwd!=repeat.get():
            messagebox.showerror("Backup",
                "Palavra-passe com pelo menos 10 caracteres e confirmação igual.",
                parent=app);return
        profiles=app.store.profiles()
        if selected is not None and not app.store.get_profile(selected):
            messagebox.showerror("Backup","Seleciona um perfil existente.",parent=app);return
        people=profiles if selected is None else [app.store.get_profile(selected)]
        category="Família" if selected is None else "Perfil"
        meds=sum(len(p.get("medications",[])) for p in people)
        agendas=sum(len(p.get("appointments",[])) for p in people)
        docs=sum(len(app.store.imported_assets(p["id"])) for p in people)
        if not messagebox.askyesno("Validar backup",
            f"{category}: {len(people)} perfis; {meds} medicamentos; "
            f"{agendas} agendamentos; {docs} anexos conhecidos.\n\n"
            "Confirma que estes números correspondem ao esperado.",
            parent=app):return
        name=("familia" if selected is None else
              "perfil-"+people[0]["name"].strip().replace(" ","_")[:30])
        dest=filedialog.asksaveasfilename(parent=app,
            defaultextension=".spbackup",initialfile=f"SaudePratica-{name}.spbackup",
            filetypes=[("Backup SaúdePrática encriptado","*.spbackup")])
        if not dest:return
        target=Path(dest)
        if target.exists() and not messagebox.askyesno("Substituir",
            "Já existe um ficheiro com este nome. Substituir?",parent=app):return

        def work(progress):
            progress(5,"Etapa 1/4 · Recolher e cifrar dados...")
            payload=app.store.export_backup(pwd,selected)
            progress(55,"Etapa 2/4 · Verificar ficheiro encriptado e perfis...")
            verified=app.store.inspect_portable_backup(payload,pwd)
            if len(verified.people)!=len(people):
                raise ValueError("O backup produzido perdeu perfis.")
            progress(75,"Etapa 3/4 · Guardar ficheiro em segurança...")
            import os,tempfile
            fd,tmp=tempfile.mkstemp(prefix=".spbackup_",dir=target.parent)
            try:
                with os.fdopen(fd,"wb") as out:
                    out.write(payload)
                    out.flush()
                    os.fsync(out.fileno())
                os.replace(tmp,target)
            finally:
                if os.path.exists(tmp):os.unlink(tmp)
            progress(100,"Etapa 4/4 · Backup concluído e verificado")
            return len(verified.people),target
        def success(result):
            count,location=result
            messagebox.showinfo("Backup verificado",
                f"Backup encriptado e verificado: {count} perfis.\n{location}",
                parent=app)
        def failure(exc):
            messagebox.showerror("Falha no backup",
                str(exc)+"\nO ficheiro não foi anunciado como concluído.",
                parent=app)
        run_progress(app,"A criar backup encriptado",work,success,failure)

    def restore():
        pwd=password.get()
        if not pwd:
            messagebox.showerror("Restauro",
                "Indica a palavra-passe do ficheiro .spbackup.",parent=app);return
        src=filedialog.askopenfilename(parent=app,
            filetypes=[("Backup SaúdePrática encriptado","*.spbackup")])
        if not src:return

        def inspect_work(progress):
            progress(5,"Etapa 1/3 · Ler backup cifrado...")
            file=Path(src)
            if file.stat().st_size>520*1024*1024:
                raise ValueError("O backup ultrapassa o limite de segurança.")
            blob=file.read_bytes()
            progress(35,"Etapa 2/3 · Autenticar e verificar integridade...")
            plan=app.store.inspect_portable_backup(blob,pwd)
            progress(100,"Etapa 3/3 · Verificação concluída")
            return plan

        def inspected(plan):
            lines=[
                f"{p.name}: {p.operation.upper()} → {p.target_id[:8]} "
                f"({p.medications} medicamentos, {p.appointments} agenda, "
                f"{p.attachments} anexos)"
                for p in plan.people
            ]
            replaced=sum(p.operation=="replace" for p in plan.people)
            created=sum(p.operation=="create" for p in plan.people)
            if not messagebox.askyesno("Confirmar restauro sem duplicar",
                f"Tipo: {plan.scope}; {created} perfis novos; "
                f"{replaced} perfis EXISTENTES A SUBSTITUIR.\n\n"+
                "\n".join(lines)+
                "\n\nIsto substitui os dados dos perfis correspondentes "
                "e mantém os restantes. Será criada primeiro uma cópia "
                "de segurança encriptada. Continuar?",
                parent=app):return

            def apply_work(progress):
                progress(5,"Etapa 1/3 · Validar destino e perfis...")
                progress(20,"Etapa 2/3 · Guardar cópia de segurança e restaurar...")
                result=app.store.restore_portable_backup(plan,pwd)
                progress(100,"Etapa 3/3 · Registos gravados e verificados")
                return result
            def finished(result):
                messagebox.showinfo("Restauro concluído",
                    f"Restaurados {result['profiles']} perfis; "
                    f"{result['replaced']} substituídos; "
                    f"{result['created']} criados.\n"+
                    (f"Cópia anterior: {result['recovery']}"
                     if result["recovery"] else ""),parent=app)
                app._render()
            run_progress(app,"A restaurar perfis e registos",apply_work,finished,
                lambda exc:messagebox.showerror("Restauro interrompido",
                    str(exc)+"\nOs dados atuais devem permanecer intactos.",
                    parent=app))
        run_progress(app,"A verificar ficheiro .spbackup",inspect_work,inspected,
            lambda exc:messagebox.showerror("Backup inválido",
                str(exc)+"\nNenhum dado foi alterado.",parent=app))
    app._button(inner,"Backup .spbackup · Família",
        lambda:export(),True,width=360,height=44).pack(anchor="w",pady=5)
    selected=app.active_id if app.active_id and app.store.get_profile(app.active_id) else None
    profile_button=app._button(inner,"Backup .spbackup · Perfil selecionado",
        lambda:export(selected),width=360,height=44)
    profile_button.pack(anchor="w",pady=5)
    if selected is None: profile_button.configure(state="disabled")
    app._button(inner,"Restaurar .spbackup · Família ou Perfil",
        restore,width=360,height=44).pack(anchor="w",pady=(15,5))
    app._label(inner,
        "Para backup de perfil escolhe primeiro o perfil no topo. "
        "A aplicação não mistura automaticamente perfis com nomes repetidos. "
        "Um perfil vazio pode produzir ficheiro pequeno; confirma sempre "
        "as contagens apresentadas antes de exportar.",
        12,color=app.p["muted"],wrap=900).pack(anchor="w",pady=(13,0))
