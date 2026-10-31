"""Visual catalog metadata for SaúdePrática Windows 0.5.

Android is the source of truth for modules. A card being visible does not
imply that its feature is implemented on Windows.
"""
from __future__ import annotations
import unicodedata

# key, icon, title PT-PT, subtitle PT-PT, implemented in Windows 0.5
MODULE_CARDS = [
    ("medication", "💊", "Medicação", "Terapêutica e avisos", True),
    ("doses", "✅", "Tomas", "Pendentes e confirmadas", False),
    ("agenda", "📆", "Agenda", "Consultas e exames", True),
    ("calendar", "🗓️", "Calendário", "Vista mensal e marcações", False),
    ("documents", "📁", "Documentos", "PDF e fotografias", True),
    ("clinical", "🏥", "Situação Clínica", "Medicina do trabalho", False),
    ("expenses", "🧾", "Despesas de Saúde", "Faturas e IRS", False),
    ("water", "💧", "Beber Água", "Hidratação", False),
    ("activity", "❤️", "Atividade e Saúde", "Passos, sono e medições", False),
    ("cycle", "🌸", "Ciclo Menstrual", "Período e pílula", False),
    ("nutrition", "🥗", "Nutrição", "Diário de refeições", False),
    ("vision", "👓", "Saúde Visual", "Graduação e receita", False),
    ("symptoms", "🩺", "Sintomas", "Diário e efeitos", False),
    ("vaccines", "💉", "Vacinas", "Histórico de vacinação", False),
    ("emergency", "🆘", "Emergência", "Contactos de emergência", False),
    ("pharmacy", "✚", "Farmácias", "Serviços próximos", False),
    ("sns24", "🏥", "SNS 24", "Serviço oficial", False),
    ("ipo", "🏨", "IPO Lisboa", "Serviço externo", False),
    ("profiles", "👥", "Perfis", "Família e cuidador", True),
    ("residences", "🏠", "Lares e Apoios", "Gestão familiar", False),
    ("shortcuts", "🔗", "Atalhos Importantes", "Links úteis", False),
    ("info", "💡", "Dicas e Informações", "Conteúdos guardados", False),
    ("backup", "🔐", "Backup", "Cópias encriptadas", True),
    ("sync", "🔄", "Sincronização", "Entre dispositivos", False),
    ("options", "⚙️", "Opções", "Aspeto e idiomas", True),
]

def normalized(text: str) -> str:
    base = unicodedata.normalize("NFKD", str(text))
    return "".join(c for c in base if not unicodedata.combining(c)).casefold().strip()

def filter_cards(query: str):
    q = normalized(query)
    return [card for card in MODULE_CARDS
            if q in normalized(card[2] + " " + card[3])]

def accessible_contrast(hex_a: str, hex_b: str) -> float:
    """WCAG contrast ratio; use for automated light/dark theme assertions."""
    def luminance(h):
        vals = [int(h[i:i+2],16)/255 for i in (1,3,5)]
        vals = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in vals]
        return .2126*vals[0]+.7152*vals[1]+.0722*vals[2]
    a,b=sorted([luminance(hex_a),luminance(hex_b)])
    return (b+.05)/(a+.05)
