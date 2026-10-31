"""Safe editable appointment fields for SaúdePrática Windows 0.7.0.

Only the Windows copy changes. Immutable Android import identifiers and the
original imported payload are retained for audit/backup compatibility.
"""
from __future__ import annotations
import json
from datetime import date
from .agenda_filter_v069 import appointment_datetime

MAIN_FIELDS=(
 ("title","Título"),("date","Data (AAAA-MM-DD)"),("time","Hora (HH:MM)"),
 ("activity","Atividade"),("type","Tipo de marcação"),
 ("specialty","Especialidade"),("unit","Unidade de Saúde"),
 ("location","Local / sala"),("department","Serviço / departamento"),
 ("doctor","Médico / profissional"),("prescriber","Médico prescritor"),
 ("resource","Recurso"),("reference","Referência"),("phone","Telefone"),
 ("email","Email"),("description","Descrição"),("notes","Notas")
)
TEXT_FIELDS={key for key,_ in MAIN_FIELDS}
STATUS_VALUES=("pending","done","cancelled")
STATUS_OPTIONS={"Pendente":"pending","Realizada":"done","Cancelada":"cancelled"}
PROTECTED={
 "id","android_original","android_source_id","android_source_key",
 "android_source_hash","android_origin","desktop_status","status",
 "state","appointment_status","appointmentStatus","statusAgendamento",
 "status_agendamento","situacao","situação","estado","isDone","completed",
 "isCompleted","done","realizada","realizado","cancelled","canceled",
 "isCancelled","isCanceled","cancelada","cancelado",
}
MAX_FIELDS=150

def _editable(value):
    return value is None or isinstance(value,(str,int,float,bool,dict,list))

def extra_fields(record):
    """Extra Android/Windows values exposed without touching provenance."""
    result=[]
    for key,value in record.items():
        if (key not in TEXT_FIELDS and key not in PROTECTED and
                not key.startswith("android_") and
                not key.startswith("desktop_") and
                isinstance(key,str) and len(key)<=100 and _editable(value)):
            rendered=json.dumps(value,ensure_ascii=False)
            if len(rendered)<=16000:result.append((key,value))
        if len(result)>=MAX_FIELDS:break
    return result

def parse_extra(key,text,original):
    """Keep the old value type so numeric/boolean fields stay roundtrippable."""
    if not isinstance(key,str) or len(key)>100 or key in TEXT_FIELDS or key in PROTECTED or key.startswith(("android_","desktop_")):
        raise ValueError("Campo adicional protegido.")
    if len(text)>16000:raise ValueError("Campo adicional demasiado comprido.")
    if original is None or isinstance(original,str):
        return text
    try:value=json.loads(text)
    except ValueError as exc:raise ValueError("O campo "+key+" exige JSON válido.") from exc
    if isinstance(original,bool):
        if type(value) is not bool:raise ValueError("O campo "+key+" deve ser verdadeiro/falso.")
    elif isinstance(original,int):
        if type(value) is not int:raise ValueError("O campo "+key+" deve ser um número inteiro.")
    elif isinstance(original,float):
        if type(value) not in (float,int):raise ValueError("O campo "+key+" deve ser um número.")
    elif type(value) is not type(original):
        raise ValueError("O campo "+key+" deve manter o tipo original.")
    return value

def clean_appointment_fields(changes,old=None):
    """Validate form values, not a mandatory set of clinical details."""
    if not isinstance(changes,dict):raise ValueError("Ficha de agendamento inválida.")
    old=old or {}
    result={}
    for key,value in changes.items():
        if key=="desktop_status":
            if value not in STATUS_VALUES:raise ValueError("Estado da marcação inválido.")
            result[key]=value
            continue
        if key in PROTECTED or key.startswith(("android_","desktop_")) or not isinstance(key,str):
            raise ValueError("Não é permitido alterar identificadores nem dados originais.")
        if key in TEXT_FIELDS:
            if not isinstance(value,str) or len(value)>4000:
                raise ValueError("Campo inválido: "+str(key))
            if key not in ("description","notes") and len(value)>350:
                raise ValueError("Campo demasiado comprido: "+key)
            result[key]=value.strip()
        else:
            if key not in old or key not in dict(extra_fields(old)):
                raise ValueError("Campo adicional não reconhecido: "+key)
            encoded=json.dumps(value,ensure_ascii=False)
            prior=old[key]
            if ((prior is not None and type(value) is not type(prior)) or
                    len(encoded)>16000 or not _editable(value)):
                raise ValueError("Campo adicional inválido: "+key)
            result[key]=value
    if not (result.get("title") or old.get("title") or old.get("name") or old.get("activity")):
        raise ValueError("Indica um título para o agendamento.")
    for key in ("date","time"):
        if key not in result or result[key]==old.get(key):continue
        value=result[key]
        if not value:continue
        if key=="date":
            try:
                if len(value)!=10:raise ValueError()
                date.fromisoformat(value)
            except ValueError as exc:raise ValueError("Data inválida. Utiliza AAAA-MM-DD.") from exc
        else:
            import re
            if not re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]",value):
                raise ValueError("Hora inválida. Utiliza HH:MM.")
    return result
