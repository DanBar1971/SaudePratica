"""Safe per-installation web-link manager, shared by Options and Important Shortcuts.

Links are public shortcuts, not profile health records. Never open untrusted
schemes (file:, javascript:, data:) or credentials embedded in a URL.
"""
from __future__ import annotations

from urllib.parse import urlsplit
from uuid import uuid4

DEFAULT_LINKS = [
    {"id":"sns24","title":"SNS 24",
     "url":"https://www.sns24.gov.pt/pt/inicio"},
    {"id":"ipo-lisboa","title":"IPO Lisboa",
     "url":"https://www.ipolisboa.min-saude.pt"},
]
MAX_LINKS = 50


def validate_link(entry):
    if not isinstance(entry, dict):
        raise ValueError("Atalho inválido.")
    identifier = entry.get("id")
    title = entry.get("title")
    url = entry.get("url")
    if not isinstance(identifier, str) or not identifier or len(identifier)>100 or any(
            not (c.isascii() and (c.isalnum() or c in "-_")) for c in identifier):
        raise ValueError("Identificador inválido.")
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 90:
        raise ValueError("Indica um nome de 1 a 90 caracteres.")
    if not isinstance(url, str):
        raise ValueError("Endereço Web inválido.")
    url = url.strip()
    if not 10 <= len(url) <= 2048 or any(c.isspace() or ord(c)<32 for c in url):
        raise ValueError("O endereço não pode conter espaços nem caracteres de controlo.")
    try:
        parts = urlsplit(url)
        if (parts.scheme not in ("http", "https") or not parts.hostname
                or parts.username is not None or parts.password is not None):
            raise ValueError("Utiliza um endereço http:// ou https:// válido.")
        _=parts.port
    except (TypeError, ValueError) as exc:
        raise ValueError("Endereço Web inválido. Utiliza http:// ou https://.") from exc
    return {"id":identifier, "title":title.strip(), "url":url}


def validated_links(rows):
    if not isinstance(rows,list) or len(rows)>MAX_LINKS:
        raise ValueError("Lista de atalhos demasiado grande.")
    result=[validate_link(row) for row in rows]
    if len({r["id"] for r in result}) != len(result):
        raise ValueError("Existem atalhos com identificador duplicado.")
    return result


def upsert_link(rows, title, url, identifier=None):
    original = validated_links(rows)
    key = identifier or uuid4().hex
    item = validate_link({"id":key, "title":title, "url":url})
    index = next((i for i,x in enumerate(original) if x["id"]==key),None)
    if identifier is not None and index is None:
        raise ValueError("O atalho a editar não existe.")
    if index is None:
        original.append(item)
    else:
        original[index] = item
    return validated_links(original)


def delete_link(rows, identifier):
    original=validated_links(rows)
    if not any(x["id"]==identifier for x in original):
        raise ValueError("Atalho inexistente.")
    return [x for x in original if x["id"]!=identifier]


def move_link(rows, identifier, direction):
    original=validated_links(rows)
    if direction not in (-1,1):
        raise ValueError("Direção inválida.")
    index=next((i for i,x in enumerate(original) if x["id"]==identifier),None)
    if index is None:
        raise ValueError("Atalho inexistente.")
    other=index+direction
    if 0<=other<len(original):
        original[index],original[other]=original[other],original[index]
    return original
