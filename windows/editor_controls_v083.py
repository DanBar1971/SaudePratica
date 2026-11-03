"""Shared Windows v0.8.3 clinical editor choices and clock controls.

UI dropdowns are editable, preserving arbitrary original Android data.
These display suggestions are not treatments or automatic prescriptions.
"""
from __future__ import annotations
from datetime import datetime,timedelta
from windows.medication_flags_v076 import CLOCK

CONDITIONS=(
    "", "Jejum", "Antes das refeições", "Ao pequeno-almoço",
    "Ao almoço", "Ao jantar", "Às refeições", "Após as refeições",
    "Ao deitar", "Com alimentos", "Sem alimentos", "SOS"
)
FREQUENCIES=(
    "", "1 vez ao dia", "2 vezes ao dia", "3 vezes ao dia",
    "4 vezes ao dia", "De 4 em 4 horas", "De 6 em 6 horas",
    "De 8 em 8 horas", "De 12 em 12 horas", "Diária", "Semanal",
    "Mensal", "Quando necessário", "Personalizada"
)
REPETITIONS=(
    "", "Contínuo (sem fim)", "1", "2", "3", "4", "5",
    "7", "10", "14", "28", "30", "Personalizado"
)
REPEAT_TYPES=(
    "", "Diária", "Semanal", "Mensal", "Anual",
    "Dias úteis", "Dias alternados", "Personalizada"
)
EXTRA_COMBO_CHOICES={
    "frequency":FREQUENCIES,
    "repetitions":REPETITIONS,
    "repeat_type":REPEAT_TYPES,
}

def shift_clock(value:str,direction:int,minutes:int=5)->str:
    """Round-trip a valid HH:MM, wrapping at midnight; blank starts at 08:00.

    No medication record or Android alarm is changed until explicit Save.
    """
    value=value.strip() if isinstance(value,str) else ""
    if not CLOCK.fullmatch(value):
        if value:
            raise ValueError("Introduz primeiro uma hora válida no formato HH:MM.")
        value="08:00"
    if direction not in (-1,1):
        raise ValueError("Direção da seta inválida.")
    if minutes not in (1,5,10,15):
        raise ValueError("Incremento de minutos inválido.")
    hours,mins=map(int,value.split(":"))
    total=(hours*60+mins+direction*minutes)%(24*60)
    return f"{total//60:02d}:{total%60:02d}"
