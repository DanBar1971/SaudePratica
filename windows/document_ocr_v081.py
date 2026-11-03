"""Local-only PDF/image preview and OCR for Windows SaúdePrática.

The original document is not sent to an online API.  Native PDF text uses
PyMuPDF; scanned PDF pages and images use bundled ONNX RapidOCR models.
All results are *untrusted suggestions* and require user approval in the UI.
"""
from __future__ import annotations

import re
from io import BytesIO
from functools import lru_cache
from pathlib import PurePath

from PIL import Image, ImageOps

MAX_BYTES=16*1024*1024
MAX_CHARS=16000
MAX_PAGES=3
MAX_PIXELS=20_000_000
ALLOWED={".pdf",".png",".jpg",".jpeg",".webp"}

class DocumentRecognitionError(ValueError):
    pass

def _valid(data,filename):
    if not isinstance(data,bytes) or not data or len(data)>MAX_BYTES:
        raise DocumentRecognitionError("Documento vazio ou superior a 16 MB.")
    ext=PurePath(filename).suffix.lower()
    if ext not in ALLOWED:
        raise DocumentRecognitionError("Escolhe um PDF, PNG, JPG ou WebP.")
    return ext

@lru_cache(maxsize=1)
def _engine():
    from rapidocr_onnxruntime import RapidOCR
    return RapidOCR()

def _image(data):
    with Image.open(BytesIO(data)) as source:
        if source.width*source.height>MAX_PIXELS:
            raise DocumentRecognitionError("Imagem demasiado grande para reconhecimento.")
        return ImageOps.exif_transpose(source).convert("RGB")

def _render_page(page):
    import pymupdf
    pix=page.get_pixmap(matrix=pymupdf.Matrix(1.35,1.35),alpha=False)
    return Image.frombytes("RGB",(pix.width,pix.height),pix.samples)

def _jpg(image,size=(700,500)):
    thumb=ImageOps.contain(image,size,method=Image.Resampling.LANCZOS)
    sink=BytesIO()
    thumb.save(sink,format="JPEG",quality=76,optimize=True)
    return sink.getvalue()

def preview_document(data,filename):
    ext=_valid(data,filename)
    try:
        if ext==".pdf":
            import pymupdf
            with pymupdf.open(stream=data,filetype="pdf") as doc:
                if len(doc)==0:raise DocumentRecognitionError("PDF sem páginas.")
                return _jpg(_render_page(doc[0]))
        return _jpg(_image(data))
    except DocumentRecognitionError:raise
    except (ValueError,OSError,RuntimeError) as exc:
        raise DocumentRecognitionError("Não foi possível pré-visualizar o ficheiro.") from exc

def _ocr_image(image):
    import numpy as np
    result,_elapsed=_engine()(np.asarray(image))
    if not result:return ""
    text=[]
    for item in result:
        if isinstance(item,(tuple,list)) and len(item)>=2 and isinstance(item[1],str):
            text.append(item[1])
    return "\n".join(text)

def recognize_document(data,filename):
    ext=_valid(data,filename)
    try:
        if ext==".pdf":
            import pymupdf
            with pymupdf.open(stream=data,filetype="pdf") as document:
                if document.is_encrypted:
                    raise DocumentRecognitionError("PDF protegido por palavra-passe.")
                if len(document)==0:raise DocumentRecognitionError("PDF sem páginas.")
                output=[]
                for page in list(document)[:MAX_PAGES]:
                    native=page.get_text("text").strip()
                    if len(native)>=35:
                        output.append(native)
                    else:
                        output.append(native+"\n"+_ocr_image(_render_page(page)))
                return "\n".join(output).strip()[:MAX_CHARS]
        return _ocr_image(_image(data)).strip()[:MAX_CHARS]
    except DocumentRecognitionError:raise
    except Exception as exc:
        raise DocumentRecognitionError("Falhou o reconhecimento local do documento: "+str(exc)[:160]) from exc

def _iso_date(value):
    from datetime import date
    v=value.strip().replace(".","/").replace("-","/")
    parts=v.split("/")
    if len(parts)!=3:return ""
    try:
        if len(parts[0])==4:
            return date(int(parts[0]),int(parts[1]),int(parts[2])).isoformat()
        return date(int(parts[2]),int(parts[1]),int(parts[0])).isoformat()
    except ValueError:
        return ""

LABELS={
    "medication":{
        "name":("medicamento","medicação","nome do medicamento","fármaco"),
        "dose":("dose","dosagem"),
        "indication":("indicação","indicações","tratamento"),
        "posology":("posologia","modo de tomar"),
        "prescriber":("médico prescritor","prescritor"),
        "prescription_date":("data da prescrição","data da receita"),
        "start_date":("início do tratamento","data de início"),
        "end_date":("fim do tratamento","data de fim"),
    },
    "appointment":{
        "title":("marcação","consulta","exame","tratamento","título"),
        "date":("data da consulta","data da marcação","data"),
        "time":("hora da consulta","hora da marcação","hora"),
        "location":("local","sala","piso"),
        "unit":("hospital","unidade de saúde"),
        "department":("serviço","departamento"),
        "doctor":("médico","profissional"),
        "specialty":("especialidade",),
        "reference":("referência","nº de referência"),
    },
}
DATE_RE=re.compile(r"\b(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[/.-]\d{1,2}[/.-]\d{4})\b")
TIME_RE=re.compile(r"\b(?:[01]?\d|2[0-3])[:hH][0-5]\d\b")

def suggest_fields(kind,text):
    """Conservative label-based extraction; never hallucinate medical details."""
    if kind not in LABELS:return {}
    if not isinstance(text,str):return {}
    result={}
    cleaned=[line.strip() for line in text.splitlines() if line.strip()]
    for line in cleaned:
        for key,aliases in LABELS[kind].items():
            if key in result:continue
            for label in sorted(aliases,key=len,reverse=True):
                match=re.match(r"^"+re.escape(label)+r"\s*[:\-]\s*(.{1,160})$",line,re.I)
                if match:
                    value=match.group(1).strip()
                    if key.endswith("date") or key=="date":
                        found=DATE_RE.search(value)
                        value=_iso_date(found.group(0)) if found else ""
                    if key=="time":
                        found=TIME_RE.search(value)
                        value=found.group(0).lower().replace("h",":") if found else ""
                        if len(value)==4:value="0"+value
                    if value:result[key]=value
                    break
    # The date/time of a standalone appointment notice is often unlabelled.
    if kind=="appointment":
        raw=" ".join(cleaned)
        if "date" not in result:
            found=DATE_RE.search(raw)
            if found:
                normalized=_iso_date(found.group(0))
                if normalized:result["date"]=normalized
        if "time" not in result:
            found=TIME_RE.search(raw)
            if found:
                clock=found.group(0).lower().replace("h",":")
                result["time"]=clock.zfill(5)
    return result
