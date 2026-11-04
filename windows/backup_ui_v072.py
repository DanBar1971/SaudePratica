"""Single SaúdePrática backup screen with FAMILY or PROFILE .spbackup only.

UI never treats the source archive as a cloud sync. Restore is previewed,
explicit, non-duplicating, and creates an encrypted safety copy first.
"""
from pathlib import Path
from tkinter import filedialog,messagebox,simpledialog
from shared.python.saude_backup import backup_access_kind
import customtkinter as ctk
from windows.progress_dialog_v073 import run_progress

def render_backup(app):
    app._heading("Backup e Restauro",
        "PIN numérico de 4 dígitos · .spbackup para toda a família ou um perfil")
    wrapper=app._card(app.body)
    wrapper.pack(fill="x",pady=8)
    inner=ctk.CTkFrame(wrapper,fg_color="transparent")
    inner.pack(fill="x",padx=25,pady=20)
    app._label(inner,"PIN para criar ou restaurar backup (4 números)",15,True).pack(anchor="w")
    password=ctk.CTkEntry(inner,show="●",height=35,corner_radius=10,width=190,
        fg_color=app.p["field"],border_color=app.p["line"],
        text_color=app.p["text"])
    password.pack(anchor="w",pady=(5,10))
    app._label(inner,"Confirmar PIN (na exportação)",13,True).pack(anchor="w")
    repeat=ctk.CTkEntry(inner,show="●",height=35,corner_radius=10,width=190,
        fg_color=app.p["field"],border_color=app.p["line"],
        text_color=app.p["text"])
    repeat.pack(anchor="w",pady=(5,16))
    app._label(inner,
        "Um único formato para Android, Windows e futuro macOS. "
        "Restaurar um perfil que já existe SUBSTITUI os seus dados apenas "
        "depois de mostrar a comparação e obter confirmação. "
        "Cria sempre um backup de segurança antes de substituir. "
        "Um PIN curto é mais cómodo, mas protege menos contra ataques "
        "fora da aplicação: guarda os ficheiros em local seguro.",
        13,color=app.p["muted"],wrap=930).pack(anchor="w",pady=(0,16))
    def export(selected=None):
        pwd=password.get()
        if len(pwd)!=4 or not pwd.isascii() or not pwd.isdigit() or pwd!=repeat.get():
            messagebox.showerror("Backup",
                "Indica o mesmo PIN de 4 números nos dois campos.",
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
        src=filedialog.askopenfilename(parent=app,
            filetypes=[("Backup SaúdePrática encriptado","*.spbackup")])
        if not src:return
        try:
            with Path(src).open("rb") as source:
                header=source.read(8192)
            kind=backup_access_kind(header)
        except (OSError,ValueError) as exc:
            messagebox.showerror("Restauro",str(exc),parent=app)
            return
        if kind=="password":
            pwd=simpledialog.askstring(
                "Backup antigo","Este é um backup antigo. Introduz a "
                "palavra-passe original para o restaurar.",
                parent=app,show="●")
            if pwd is None:return
        else:
            pwd=password.get()
            if len(pwd)!=4 or not pwd.isascii() or not pwd.isdigit():
                messagebox.showerror(
                    "Restauro","Introduz o PIN de 4 números deste backup.",
                    parent=app)
                return

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
                modules=result.get("android_modules",{})
                totals=(
                    f"\nMódulos Android recuperados:\n"
                    f"Refeições: {modules.get('meals',0)} · "
                    f"Fotografias: {modules.get('meal_photos',0)}\n"
                    f"Água: {modules.get('water',0)} · "
                    f"Sintomas: {modules.get('symptoms',0)} · "
                    f"Tomas confirmadas: {modules.get('intakes',0)}\n"
                    f"Fichas SOS: {modules.get('sos',0)} campos · "
                    f"Lares: {modules.get('residences',0)} · "
                    f"Mensalidades: {modules.get('invoices',0)}\n"
                    f"Outras medições: {modules.get('measurements',0)}\n")
                messagebox.showinfo("Restauro concluído",
                    f"Restaurados {result['profiles']} perfis; "
                    f"{result['replaced']} substituídos; "
                    f"{result['created']} criados.\n"+
                    totals+
                    (f"\nCópia anterior: {result['recovery']}"
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

    def recover_from_stored_android():
        pwd=password.get()
        if len(pwd)!=4 or not pwd.isascii() or not pwd.isdigit():
            messagebox.showerror("Recuperar dados Android",
                "Introduz um PIN de 4 números para proteger a cópia de segurança.",
                parent=app)
            return
        if not messagebox.askyesno("Recuperar os módulos Android",
            "Ler os backups Android originais já guardados neste computador "
            "e preencher automaticamente as fichas dos perfis correspondentes?\n\n"
            "Recupera Nutrição e fotografias, Hidratação, Sintomas, Tomas "
            "confirmadas, SOS, Lares e medições antigas.\n\n"
            "Não substitui registos Windows nem mistura dados de perfis. "
            "Será criada primeiro uma cópia de segurança encriptada.",
            parent=app):
            return
        def work(progress):
            import datetime
            progress(5,"Criar uma cópia de segurança antes da importação...")
            blob=app.store.export_backup(pwd)
            recovery=app.store.path.parent/"restores"
            recovery.mkdir(mode=0o700,parents=True,exist_ok=True)
            stamp=datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            target=recovery/("pre-android-recovery-"+stamp+".spbackup")
            import os,tempfile
            fd,tmp=tempfile.mkstemp(prefix=".spbackup_",dir=recovery)
            try:
                with os.fdopen(fd,"wb") as out:
                    out.write(blob)
                    out.flush()
                    os.fsync(out.fileno())
                os.replace(tmp,target)
            finally:
                if os.path.exists(tmp):os.unlink(tmp)
            progress(45,"Importar apenas os módulos Android em falta...")
            result=app.store.recover_android_modules()
            progress(100,"Recuperação protegida concluída")
            return result,target
        def done(out):
            result,target=out
            mods=result["android_modules"]
            app._render()
            messagebox.showinfo(
                "Módulos Android recuperados",
                f"Perfis com backup Android: {result['profiles']}\n"
                f"Refeições: {mods['meals']} · Fotografias: {mods['meal_photos']}\n"
                f"Água: {mods['water']} · Sintomas: {mods['symptoms']}\n"
                f"Tomas confirmadas: {mods['intakes']}\n"
                f"Emergência: {mods['sos']} campos · Lares: {mods['residences']}\n"
                f"Mensalidades: {mods['invoices']} · "
                f"Medições: {mods['measurements']}\n\n"
                f"Cópia de segurança anterior: {target}",
                parent=app)
        run_progress(app,"A recuperar módulos Android",work,done,
            lambda exc:messagebox.showerror(
                "Recuperação interrompida",
                str(exc)+"\nA cópia original foi preservada.",parent=app))

    app._button(inner,"Recuperar dados Android dos backups já guardados",
        recover_from_stored_android,width=360,height=44).pack(
            anchor="w",pady=(10,5))
    app._label(inner,
        "Para backup de perfil escolhe primeiro o perfil no topo. "
        "A aplicação não mistura automaticamente perfis com nomes repetidos. "
        "Um perfil vazio pode produzir ficheiro pequeno; confirma sempre "
        "as contagens apresentadas antes de exportar.",
        12,color=app.p["muted"],wrap=900).pack(anchor="w",pady=(13,0))
