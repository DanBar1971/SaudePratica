"""SaúdePrática Windows 0.8.10 — schema of seven remaining modules.

No diagnosis, vaccine recommendation, eligibility decision, pharmacy opening
hours, or automatic emergency call is inferred from locally entered records.
"""
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import re
from urllib.parse import urlsplit

# key, label, field type, limit; "choice:a|b" is explicit user status.
SCHEMAS = {
    "vision": {
        "title":"Saúde Visual","storage":"vision_records",
        "fields":[
            ("date","Data do exame (DD/MM/AAAA)","date",16),
            ("title","Tipo de exame ou receita","text",150),
            ("professional","Oftalmologista / optometrista","text",160),
            ("right_sphere","Direito: Esfera (SPH)","decimal",15),
            ("right_cyl","Direito: Cilindro (CYL)","decimal",15),
            ("right_axis","Direito: Eixo (0–180)","axis",4),
            ("right_add","Direito: Adição (ADD)","decimal",15),
            ("left_sphere","Esquerdo: Esfera (SPH)","decimal",15),
            ("left_cyl","Esquerdo: Cilindro (CYL)","decimal",15),
            ("left_axis","Esquerdo: Eixo (0–180)","axis",4),
            ("left_add","Esquerdo: Adição (ADD)","decimal",15),
            ("pd","Distância pupilar (mm)","decimal",15),
            ("notes","Notas / observações","long",2000),
            ("document_sha256","Receita ou relatório do perfil","document",64),
        ]},
    "symptoms": {
        "title":"Sintomas","storage":"symptom_records",
        "fields":[
            ("date","Data (DD/MM/AAAA)","date",16),
            ("title","Descrição do sintoma","text",160),
            ("type","Tipo de registo","choice:Sintoma|Possível efeito secundário",60),
            ("severity","Intensidade (0 a 10)","severity",2),
            ("details","Notas / evolução","long",3000),
            ("document_sha256","Documento associado","document",64),
        ]},
    "vaccines": {
        "title":"Vacinas","storage":"vaccine_records",
        "fields":[
            ("title","Nome da vacina","text",160),
            ("date","Data de administração","date",16),
            ("next","Próxima dose (opcional)","optional_date",16),
            ("dose","Dose / número","text",80),
            ("lot","Lote","text",120),
            ("unit","Local / unidade de saúde","text",160),
            ("notes","Observações","long",1200),
            ("document_sha256","Boletim / comprovativo","document",64),
        ]},
    "pharmacy": {
        "title":"Farmácias","storage":"pharmacy_records",
        "fields":[
            ("title","Nome da farmácia","text",160),
            ("address","Morada","text",250),
            ("city","Localidade","text",100),
            ("phone","Telefone","phone",30),
            ("website","Website (opcional)","url",1000),
            ("notes","Notas pessoais","long",1200),
        ]},
    "residences": {
        "title":"Lares e Apoios","storage":"residence_records",
        "fields":[
            ("title","Instituição","text",160),
            ("type","Valência","choice:ERPI|Serviço de Apoio Domiciliário|Centro de Dia|Outra",70),
            ("address","Morada","text",240),
            ("phone","Telefone","phone",30),
            ("email","Email","text",160),
            ("website","Website","url",1000),
            ("admission","Data de admissão (opcional)","optional_date",16),
            ("contact","Contacto responsável","text",140),
            ("notes","Contrato / cuidados / observações","long",3000),
            ("document_sha256","Contrato / documento","document",64),
        ]},
    "residence_invoices": {
        "title":"Faturas e ADSE","storage":"residence_invoices",
        "fields":[
            ("date","Mês da fatura (DD/MM/AAAA, usar dia 1)","date",16),
            ("title","Instituição / referência","text",160),
            ("status","Estado do pedido","choice:Por pedir|Pedida|Recebida|Submetida|Em análise|Pendente de correção|Reembolsada|Não elegível / Não submetida",80),
            ("amount","Valor faturado (€)","money",30),
            ("paid","Valor pago (€)","money",30),
            ("reimbursed","Valor reembolsado (€)","money",30),
            ("reference","Referência de processo / fatura","text",160),
            ("notes","Notas e datas de submissão","long",2500),
            ("document_sha256","Fatura / comprovativo","document",64),
        ]},
    "supports": {
        "title":"Apoios","storage":"support_records",
        "fields":[
            ("title","Nome do apoio","text",160),
            ("type","Tipo de apoio","choice:ADSE|Segurança Social|Complemento por dependência|Complemento Solidário para Idosos|Outro",90),
            ("status","Estado manual","choice:Por avaliar|Em preparação|Pedido apresentado|A aguardar resposta|Aprovado|Indeferido|Terminado",80),
            ("date","Data do registo","date",16),
            ("reference","Referência (opcional)","text",160),
            ("notes","Observações","long",2500),
            ("document_sha256","Documento / comprovativo","document",64),
        ]},
}

EMERGENCY_FIELDS = [
    ("contact_name","Contacto de emergência",160),
    ("contact_phone","Telefone",30),
    ("second_contact","Segundo contacto",240),
    ("allergies","Alergias conhecidas",2000),
    ("chronic_conditions","Doenças crónicas",2000),
    ("conditions","Informações médicas relevantes",2000),
    ("blood_group","Grupo sanguíneo (se confirmado)",30),
    ("notes","Outras informações",2000),
]
MEAL_FIELDS = [
    ("meal","Tipo de refeição",80),
    ("foods","Alimentos e porções",1200),
    ("kcal","Energia estimada ou registada (kcal)",20),
    ("protein_g","Proteínas (g)",20),
    ("carbs_g","Hidratos (g)",20),
    ("fat_g","Gorduras (g)",20),
    ("note","Observações",500),
]
MEAL_MAX=5000

def normalize_date(value: str, optional: bool=False)->str:
    s=str(value or "").strip()
    if not s and optional:return ""
    for fmt in ("%Y-%m-%d","%d/%m/%Y"):
        try:return datetime.strptime(s,fmt).date().isoformat()
        except ValueError:pass
    raise ValueError("Data inválida. Usa DD/MM/AAAA.")

def safe_money(value)->int:
    if isinstance(value,int) and not isinstance(value,bool):
        if 0<=value<=10000000000:return value
        raise ValueError("Valor em cêntimos fora do intervalo.")
    s=str(value or "0").replace("€","").replace(" ","").strip()
    if "," in s:s=s.replace(".","").replace(",",".")
    try:x=Decimal(s)
    except (InvalidOperation,ValueError) as e:raise ValueError("Valor monetário inválido.") from e
    if not x.is_finite() or x<0 or x>100000000:
        raise ValueError("Valor monetário fora do intervalo.")
    if x.as_tuple().exponent<-2:
        raise ValueError("Máximo duas casas decimais.")
    return int(x*100)

def text_money(cents):
    if not isinstance(cents,int):return "0,00"
    return f"{cents//100},{cents%100:02d}"

def check_url(value):
    if not value:return ""
    if not isinstance(value,str) or len(value)>1000 or any(c.isspace() or ord(c)<32 for c in value):
        raise ValueError("Website inválido.")
    try:
        v=urlsplit(value)
        if v.scheme not in ("https","http") or not v.hostname or v.username or v.password:
            raise ValueError("Website inválido; usa https://.")
        _=v.port
    except ValueError as exc:raise ValueError("Website inválido; usa https://.") from exc
    return value

def validate_record(kind,raw):
    if kind not in SCHEMAS or not isinstance(raw,dict):
        raise ValueError("Tipo de ficha inválido.")
    result={}
    for key,label,typ,limit in SCHEMAS[kind]["fields"]:
        value=raw.get(key,"")
        if typ=="money":
            result[key+"_cents"]=safe_money(value)
            continue
        if not isinstance(value,str) or len(value)>limit:
            raise ValueError(f"{label}: texto inválido ou demasiado longo.")
        value=value.strip()
        if typ=="date":
            value=normalize_date(value)
        elif typ=="optional_date":
            value=normalize_date(value,True)
        elif typ=="choice":
            choices=typ[7:].split("|")
            if value not in choices:raise ValueError(f"{label}: valor inválido.")
        elif typ=="axis" and value:
            if not value.isdigit() or not 0<=int(value)<=180:raise ValueError(f"{label}: usa 0–180.")
        elif typ=="severity":
            if not value.isdigit() or not 0<=int(value)<=10:
                raise ValueError("A intensidade deve estar entre 0 e 10.")
        elif typ=="decimal" and value:
            try: n=Decimal(value.replace(",","."))
            except InvalidOperation as exc:raise ValueError(f"{label}: valor inválido.") from exc
            if not n.is_finite() or abs(n)>1000:raise ValueError(f"{label}: valor fora do intervalo.")
        elif typ=="document" and value:
            if not re.fullmatch("[0-9a-f]{64}",value):raise ValueError("Documento inválido.")
        elif typ=="phone" and value:
            if not re.fullmatch(r"[+\d\s()\-]{3,30}",value):
                raise ValueError("Telefone inválido.")
        elif typ=="url":
            value=check_url(value)
        result[key]=value
    if not result.get("title"):
        raise ValueError("Indica o nome ou descrição.")
    return result

def validate_emergency(raw):
    if not isinstance(raw,dict):raise ValueError("Ficha de emergência inválida.")
    result={}
    for key,label,limit in EMERGENCY_FIELDS:
        value=raw.get(key,"")
        if not isinstance(value,str) or len(value)>limit:
            raise ValueError(label+": campo inválido.")
        result[key]=value.strip()
    for key in ("contact_phone",):
        if result[key] and not re.fullmatch(r"[+\d\s()\-]{3,30}",result[key]):
            raise ValueError("Telefone inválido.")
    return result

def validate_meal(row):
    if not isinstance(row,dict):raise ValueError("Refeição inválida.")
    result={}
    for k,label,limit in MEAL_FIELDS:
        value=row.get(k,0 if k in ("kcal","protein_g","carbs_g","fat_g") else "")
        if k in ("kcal","protein_g","carbs_g","fat_g"):
            try:x=Decimal(str(value).replace(",","."))
            except InvalidOperation as exc:raise ValueError(label+": valor inválido.") from exc
            if not x.is_finite() or x<0 or x>MEAL_MAX:
                raise ValueError(label+": valor fora do intervalo.")
            result[k]=float(x)
        else:
            if not isinstance(value,str) or len(value)>limit:
                raise ValueError(label+": campo inválido.")
            result[k]=value.strip()
    if not result["foods"]:raise ValueError("Indica os alimentos ou porções.")
    return result
