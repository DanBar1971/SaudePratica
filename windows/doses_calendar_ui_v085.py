"""Native, profile-scoped Takes and Calendar pages for Windows 0.8.5.

Every read resolves the currently selected profile; no global family-wide
clinical query and no implicit medication confirmation or background alarm.
"""
from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from tkinter import messagebox
import customtkinter as ctk

from windows.doses_calendar_v085 import (
    MONTHS, WEEKDAYS, month_cells, appointments_for_day, month_shift,
    dose_entries, dose_counts,
)
from windows.agenda_filter_v069 import appointment_datetime, appointment_status
from windows.secure_store import LocalStoreError

TEAL = "#00c9b7"


class DosesCalendarUi:
    def _calendar_move(self, delta):
        day = self.calendar_selected
        year, month = month_shift(day.year, day.month, delta)
        new_day = min(day.day, calendar.monthrange(year, month)[1])
        self.calendar_selected = date(year, month, new_day)
        self._render()

    def _calendar_choose(self, day):
        self.calendar_selected = day
        self._render()

    def _open_calendar_appointment(self, identifier):
        # Agenda editor already owns persistence and all Android metadata.
        self.page = "agenda"
        self.agenda_mode = "editor"
        self.editing_appointment = identifier
        self._render()

    def _calendar(self):
        self.wallpaper_shell.glass_enabled = False
        profile = self.store.get_profile(self.active_id) if self.active_id else None
        name = profile.get("name", "") if profile else ""
        self._heading("Calendário", "Marcações do perfil: " + name if name else
                      "Seleciona um perfil para consultar o calendário")
        if not profile:
            return
        today = date.today()
        if not isinstance(getattr(self, "calendar_selected", None), date):
            self.calendar_selected = today
        selected = self.calendar_selected

        toolbar = ctk.CTkFrame(self.body, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 6))
        self._button(toolbar, "‹  Mês anterior",
                     lambda: self._calendar_move(-1), width=155).pack(side="left")
        self._button(toolbar, "Mês seguinte  ›",
                     lambda: self._calendar_move(1), width=155).pack(side="right")
        self._button(toolbar, "Hoje",
                     lambda: self._calendar_choose(today), width=88).pack(side="right", padx=9)
        self._label(toolbar, f"{MONTHS[selected.month-1]} {selected.year}",
                    19, True, anchor="center").pack(side="left", expand=True, padx=12)

        grid = ctk.CTkFrame(self.body, fg_color="transparent")
        grid.pack(fill="x", pady=(1, 7))
        for column in range(7):
            grid.grid_columnconfigure(column, weight=1, uniform="days")
            self._label(grid, WEEKDAYS[column], 12, True,
                        anchor="center").grid(row=0, column=column, sticky="ew", pady=(0, 3))
        for row_num, week in enumerate(month_cells(profile, selected.year, selected.month), 1):
            for column, (day, in_month, count) in enumerate(week):
                active = day == selected
                bg = TEAL if active else (self.p["panel2"] if in_month else self.p["bg"])
                fg = "#042b31" if active else (
                    self.p["text"] if in_month else self.p["muted"])
                mark = f"  • {count} marcaç." if count else ""
                cell = ctk.CTkButton(
                    grid, text=f"{day.day:02d}{mark}", height=43,
                    corner_radius=10, border_width=1,
                    border_color=TEAL if active else self.p["line"],
                    fg_color=bg, hover_color=self.p["hover"],
                    text_color=fg, font=ctk.CTkFont(size=12, weight="bold" if count or active else "normal"),
                    command=lambda d=day: self._calendar_choose(d))
                cell.grid(row=row_num, column=column, sticky="nsew", padx=3, pady=2)

        controls = ctk.CTkFrame(self.body, fg_color="transparent")
        controls.pack(fill="x", pady=(5, 7))
        items = appointments_for_day(profile, selected)
        self._label(controls, f"{selected:%d/%m/%Y}  ·  {len(items)} marcação(ões)",
                    16, True).pack(side="left", padx=(2, 8))
        self._button(controls, "+ Adicionar", self._calendar_new_appointment,
                     accent=True, width=134).pack(side="right")
        self._button(controls, "Ver Agenda", lambda: self.navigate("agenda"),
                     width=124).pack(side="right", padx=6)

        history = ctk.CTkScrollableFrame(self.body, fg_color="transparent")
        history.pack(fill="both", expand=True)
        if not items:
            self._label(history, "Não existem marcações neste dia.", 13,
                        color=self.p["muted"]).pack(anchor="w", pady=(9, 0))
        for event in items:
            dt = appointment_datetime(event)
            status = appointment_status(event)
            name = str(event.get("title") or event.get("activity") or
                       event.get("department") or event.get("name") or "Marcação")
            place = str(event.get("location") or event.get("unit") or
                        event.get("place") or "")
            tag = {"pending": "Pendente", "done": "Realizada",
                   "cancelled": "Cancelada"}.get(status, "Pendente")
            row = self._card(history)
            row.pack(fill="x", pady=4, padx=(0, 4))
            clock = dt.strftime("%H:%M") if dt else "--:--"
            self._label(row, clock, 16, True, color=TEAL).pack(side="left", padx=13, pady=12)
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, padx=8, pady=6)
            self._label(info, name[:180], 13, True).pack(anchor="w")
            self._label(info, (place[:160] + "  •  " if place else "") + tag,
                        11, color=self.p["muted"]).pack(anchor="w", pady=(2, 0))
            identifier = event.get("id")
            if identifier:
                self._button(row, "Abrir ficha",
                             lambda eid=identifier: self._open_calendar_appointment(eid),
                             width=112).pack(side="right", padx=12)

    def _calendar_new_appointment(self):
        self.page = "agenda"
        self.agenda_mode = "editor"
        self.editing_appointment = None
        self._render()

    def _dose_choose_day(self, delta):
        self.dose_selected = self.dose_selected + timedelta(days=delta)
        self._render()

    def _dose_choose_filter(self, category):
        self.dose_filter = category
        self._render()

    def _confirm_planned(self, medication_id, planned_at):
        profile = self.store.get_profile(self.active_id)
        if not profile:
            return
        medicine = next((m for m in profile.get("medications", [])
                         if m.get("id") == medication_id), None)
        if not medicine:
            messagebox.showerror("Tomas", "Medicamento não encontrado neste perfil.", parent=self)
            return
        if not messagebox.askyesno(
            "Confirmar toma",
            f"Confirmas que tomaste {medicine.get('name', 'Medicação')}?\n"
            "Esta ação grava um registo de toma real no perfil selecionado.",
            parent=self):
            return
        try:
            self.store.confirm_intake(self.active_id, medication_id,
                                      scheduled_at=planned_at)
            self._render()
        except (LocalStoreError, OSError) as exc:
            messagebox.showerror("Tomas", str(exc), parent=self)

    def _confirm_manual(self):
        profile = self.store.get_profile(self.active_id)
        if not profile:
            return
        label = self.dose_med_var.get()
        med_id = self._dose_med_choices.get(label)
        if not med_id:
            messagebox.showwarning("Tomas", "Escolhe um medicamento deste perfil.", parent=self)
            return
        typed = self.dose_at.get().strip()
        try:
            when = datetime.strptime(typed, "%d/%m/%Y %H:%M")
        except ValueError:
            messagebox.showwarning("Tomas",
                "Indica a data e hora no formato DD/MM/AAAA HH:MM.", parent=self)
            return
        if not messagebox.askyesno(
            "Registar toma manual",
            f"Confirma que a medicação foi efetivamente tomada a {typed}?\n"
            "Um registo manual não altera os alarmes programados.",
            parent=self):
            return
        try:
            self.store.confirm_intake(self.active_id, med_id,
                                      confirmed_at=when.isoformat(timespec="minutes"))
            self.dose_selected = when.date()
            self._render()
        except (LocalStoreError, OSError) as exc:
            messagebox.showerror("Tomas", str(exc), parent=self)

    def _delete_confirmed(self, identifier):
        if not messagebox.askyesno(
            "Apagar toma", "Queres apagar este registo confirmado?\n"
            "A medicação e os respetivos horários não serão alterados.", parent=self):
            return
        try:
            self.store.delete_intake(self.active_id, identifier)
            self._render()
        except (LocalStoreError, OSError) as exc:
            messagebox.showerror("Tomas", str(exc), parent=self)

    def _doses(self):
        self.wallpaper_shell.glass_enabled = False
        profile = self.store.get_profile(self.active_id) if self.active_id else None
        self._heading("Tomas",
                      "Histórico e confirmações do perfil: " + profile.get("name", "")
                      if profile else "Seleciona um perfil primeiro")
        if not profile:
            return
        if not isinstance(getattr(self, "dose_selected", None), date):
            self.dose_selected = date.today()
        if getattr(self, "dose_filter", None) not in ("all", "pending", "confirmed"):
            self.dose_filter = "all"
        day = self.dose_selected
        controls = ctk.CTkFrame(self.body, fg_color="transparent")
        controls.pack(fill="x", pady=(0, 10))
        self._button(controls, "‹  Dia anterior",
                     lambda: self._dose_choose_day(-1), width=144).pack(side="left")
        self._label(controls, day.strftime("%d/%m/%Y"), 17, True,
                    anchor="center").pack(side="left", expand=True, padx=6)
        self._button(controls, "Hoje",
                     lambda: self._dose_today(), width=74).pack(side="right", padx=(7, 0))
        self._button(controls, "Dia seguinte  ›",
                     lambda: self._dose_choose_day(1), width=144).pack(side="right")

        counts = dose_counts(profile, day)
        totals = ctk.CTkFrame(self.body, fg_color="transparent")
        totals.pack(fill="x", pady=(0, 9))
        self._label(totals,
            f"✓ Confirmadas: {counts['confirmed']}    "
            f"◷ Por confirmar: {counts['pending']}    "
            f"⚠ Atrasadas por confirmar: {counts['late']}",
            12, True).pack(side="left")
        tabs = ctk.CTkFrame(self.body, fg_color="transparent")
        tabs.pack(fill="x", pady=(0, 10))
        for key, title in (("all", "Todas"), ("pending", "Por confirmar"),
                           ("confirmed", "Confirmadas")):
            self._button(tabs, title, lambda k=key: self._dose_choose_filter(k),
                         accent=self.dose_filter == key,
                         width=142).pack(side="left", padx=(0, 6))

        if self.dose_filter in ("all", "confirmed"):
            medications = [m for m in profile.get("medications", [])
                           if isinstance(m, dict) and m.get("id")]
            if medications:
                form = ctk.CTkFrame(self.body, fg_color=self.p["panel"],
                                    corner_radius=12, border_color=self.p["line"],
                                    border_width=1)
                form.pack(fill="x", pady=(0, 9))
                self._label(form, "Registar toma manual", 13, True).pack(
                    side="left", padx=(11, 9), pady=11)
                choices = {}
                for i, med in enumerate(medications, 1):
                    key = f"{med.get('name') or 'Medicação'} · {med.get('dose') or ''} [{i}]"
                    choices[key] = med["id"]
                self._dose_med_choices = choices
                self.dose_med_var = ctk.StringVar(value=next(iter(choices)))
                ctk.CTkOptionMenu(form, variable=self.dose_med_var,
                                  values=list(choices), width=260,
                                  fg_color=self.p["panel2"],
                                  button_color="#116c7a",
                                  button_hover_color="#00a99b",
                                  text_color=self.p["text"]).pack(
                                      side="left", padx=6, pady=8)
                self.dose_at = ctk.CTkEntry(form, width=170)
                self.dose_at.insert(0, datetime.now().strftime("%d/%m/%Y %H:%M"))
                self.dose_at.pack(side="left", padx=7)
                self._button(form, "✓ Tomei",
                             self._confirm_manual, accent=True,
                             width=105).pack(side="left", padx=8)
        info = self._label(self.body,
            "Tomas previstas apenas quando há uma regra real de repetição. "
            "Atrasada não significa omitida. A aplicação Windows não dispara alarmes de medicação.",
            11, color=self.p["muted"], wrap=980)
        info.pack(anchor="w", pady=(0, 7))

        records = dose_entries(profile, day)
        if self.dose_filter == "confirmed":
            records = [r for r in records if r["status"] == "confirmed"]
        elif self.dose_filter == "pending":
            records = [r for r in records if r["status"] != "confirmed"]
        scroll = ctk.CTkScrollableFrame(self.body, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        if not records:
            self._label(scroll, "Não existem tomas nesta vista para este dia.",
                        13, color=self.p["muted"]).pack(anchor="w", pady=12)
        for record in records:
            state = record["status"]
            status_label = {
                "confirmed": "✓ Confirmada",
                "pending": "◷ Por confirmar",
                "late": "⚠ Atrasada por confirmar",
            }[state]
            colour = {"confirmed": "#55caa1", "pending": TEAL,
                      "late": "#e6ad60"}[state]
            row = self._card(scroll)
            row.pack(fill="x", padx=(0, 4), pady=4)
            self._label(row, record["time"], 15, True,
                        color=colour).pack(side="left", padx=(13, 17), pady=13)
            details = ctk.CTkFrame(row, fg_color="transparent")
            details.pack(side="left", fill="both", expand=True, pady=7)
            title = record["medication"] + (f" · {record['dose']}" if record["dose"] else "")
            self._label(details, title[:210], 14, True).pack(anchor="w")
            self._label(details, status_label, 11, color=colour).pack(anchor="w")
            if state == "confirmed" and record.get("id"):
                self._button(row, "Apagar registo",
                    lambda uid=record["id"]: self._delete_confirmed(uid),
                    width=124).pack(side="right", padx=12)
            elif record.get("scheduled_at"):
                self._button(row, "✓ Tomei",
                    lambda med=record["medication_id"], at=record["scheduled_at"]:
                        self._confirm_planned(med, at),
                    accent=True, width=100).pack(side="right", padx=12)

    def _dose_today(self):
        self.dose_selected = date.today()
        self._render()
