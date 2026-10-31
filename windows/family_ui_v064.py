"""Full-family Android backup UI for Windows desktop v0.6.4.

All sensitive bytes remain in memory until the user confirms import; source
archives are saved by SecureStore under Windows DPAPI, not in public files.
"""
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
import customtkinter as ctk

from windows.android_import_v062 import AndroidImportError
from windows.family_portability_v064 import plan_family_archive, plan_summary
from windows.secure_store import LocalStoreError

def choose_family_zip(app):
    filename=filedialog.askopenfilename(parent=app,
        title="Abrir backup da família SaúdePrática Android",
        filetypes=[("Backup Android","*.zip"),("Todos os ficheiros","*.*")])
    if not filename:return
    try:
        path=Path(filename)
        if path.stat().st_size>220*1024*1024:
            raise AndroidImportError("O ZIP excede 220 MB.")
        app.family_import_plan=plan_family_archive(path.read_bytes(),app.store.profiles())
        app.family_import_result=""
        app.android_import_error=""
    except (AndroidImportError,OSError,ValueError) as exc:
        app.family_import_plan=None
        app.android_import_error=str(exc)
    app._render()

def confirm_family_zip(app):
    plan=getattr(app,"family_import_plan",None)
    if plan is None:return
    summary=plan_summary(plan)
    names=", ".join(m.source.name for m in plan.members[:15])
    if not messagebox.askyesno("Importar família inteira",
        f"Importar {summary['profiles']} perfis ({summary['new_profiles']} novos), "
        f"{summary['medications']} medicamentos, {summary['appointments']} marcações "
        f"e {summary['attachments']} anexos?\n\n"
        f"Perfis: {names}\n\n"
        "O Windows guardará também uma cópia CIFRADA do ZIP Android original, "
        "incluindo os dados de módulos ainda não disponíveis. "
        "Os dados existentes não serão substituídos. Continuar?",parent=app):
        return
    try:
        stats=app.store.import_android_family(plan)
        app.family_import_plan=None
        app.family_import_result=(
            f"Importação concluída: {stats['profiles']} perfis, "
            f"{stats['new_profiles']} criados, "
            f"{stats['medications']} medicações e {stats['appointments']} marcações. "
            "Cópia integral do ZIP Android protegida no Windows.")
        app.android_import_error=""
        app._render()
    except (AndroidImportError,LocalStoreError,OSError,ValueError) as exc:
        app.android_import_error=str(exc)
        app._render()

def export_original_zip(app):
    """Explicitly export plaintext original ZIP only after privacy confirmation."""
    archives=app.store.android_archives()
    if not archives:
        messagebox.showinfo("Backup Android",
            "Ainda não existe um backup familiar Android importado.",parent=app)
        return
    if len(archives)>1:
        labels="\n".join(f"{i+1}. {item['sha256'][:12]} "
            f"({item['bytes']/1048576:.1f} MB)"
            for i,item in enumerate(archives[:30]))
        idx=simpledialog.askinteger("Escolher ZIP Android",
            "Escolhe o número do arquivo:\n"+labels,parent=app,
            minvalue=1,maxvalue=min(30,len(archives)))
        if idx is None:return
        item=archives[idx-1]
    else:item=archives[0]
    if not messagebox.askyesno("Exportar dados sem encriptação",
        "O ZIP original contém dados pessoais e clínicos de vários perfis. "
        "O ficheiro exportado NÃO está encriptado pela SaúdePrática. "
        "Guarda-o apenas num local seguro. Continuar?",parent=app):
        return
    filename="SaudePratica-backup-original-"+item["sha256"][:12]+".zip"
    destination=filedialog.asksaveasfilename(parent=app,title="Exportar ZIP original",
        initialfile=filename,defaultextension=".zip",
        filetypes=[("Backup ZIP Android","*.zip")])
    if not destination:return
    try:
        data=app.store.export_original_android_zip(item["sha256"])
        path=Path(destination)
        if path.exists() and not messagebox.askyesno(
            "Confirmar substituição","Substituir o ficheiro existente?",parent=app):
            return
        path.write_bytes(data)
        messagebox.showinfo("ZIP original",
            "ZIP Android original exportado. Não o partilhes publicamente.",parent=app)
    except (AndroidImportError,LocalStoreError,OSError,ValueError) as exc:
        messagebox.showerror("ZIP original",str(exc),parent=app)

def family_controls(app):
    """A single preview/confirm workflow independent of the active Windows profile."""
    app._label(app.body,"Importação e exportação da família inteira",19,True).pack(
        anchor="w",pady=(5,7))
    app._label(app.body,
        "Importar todos os perfis do backup Android numa operação, incluindo "
        "Medicação, Agenda, fotos e documentos reconhecidos. O ZIP original "
        "fica protegido integralmente e pode ser reexportado sem alterações. "
        "Outros módulos ainda não ficam editáveis no Windows.",
        12,color=app.p["muted"],wrap=1000).pack(anchor="w",pady=(0,12))
    bar=ctk.CTkFrame(app.body,fg_color="transparent")
    bar.pack(fill="x",pady=(0,12))
    app._button(bar,"Importar ZIP familiar completo",
        lambda:choose_family_zip(app),True,width=264,height=39).pack(
            side="left",padx=(0,9))
    app._button(bar,"Exportar ZIP Android original",
        lambda:export_original_zip(app),width=252,height=39).pack(
            side="left",padx=(0,9))
    app._button(bar,"Backup completo encriptado",
        lambda:app.navigate("backup"),width=249,height=39).pack(side="left")
    if getattr(app,"family_import_result",""):
        app._label(app.body,app.family_import_result,14,True,
            color="#17b8a9",wrap=1000).pack(anchor="w",pady=(6,12))
    plan=getattr(app,"family_import_plan",None)
    if plan:
        stats=plan_summary(plan)
        app._label(app.body,
            f"Pré-visualização: {stats['profiles']} perfis / "
            f"{stats['new_profiles']} novos / {stats['original_files']} ficheiros originais",
            17,True,color="#17b8a9").pack(anchor="w",pady=(6,7))
        for m in plan.members:
            action="Criar" if m.create else "Atualizar sem substituir"
            app._label(app.body,
                f"{action}: {m.source.name} · "
                f"{len(m.imported.medications.new)} medicações, "
                f"{len(m.imported.appointments.new)} marcações, "
                f"{len(m.imported.attachments)} anexos",
                12,color=app.p["text"],wrap=1000).pack(anchor="w",pady=3)
        app._button(app.body,"Confirmar importação familiar",
            lambda:confirm_family_zip(app),True,width=300,height=41).pack(
                anchor="w",pady=(11,18))
