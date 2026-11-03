"""SaúdePrática Windows 0.8.6: genuine monthly calendar, not a grid of buttons.

This view reads appointment records solely from the currently active profile.
Pure colour decisions are separated from Tk widgets for regression testing.
No medical or scheduling data are changed by rendering the calendar.
"""
from __future__ import annotations

from datetime import date
import customtkinter as ctk

from windows.doses_calendar_v085 import MONTHS, WEEKDAYS, month_cells, appointments_for_day
from windows.agenda_filter_v069 import appointment_datetime, appointment_status


LONG_WEEKDAYS = (
    "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
    "sexta-feira", "sábado", "domingo",
)


def calendar_day_colors(*, has_appointments: bool, selected: bool,
                        today: bool, in_month: bool, light: bool) -> dict:
    """Return full palette for all 16 combinations, including light theme.

    Event days are distinct even when they are not selected. Today uses a
    golden outline; selection is a solid turquoise background. An event
    counter is never hidden by either emphasis.
    """
    if light:
        base = {
            "background": "#f3f8fa" if in_month else "#e5edf1",
            "border": "#d0dde5",
            "number": "#213947" if in_month else "#83959e",
            "preview": "#536b77" if in_month else "#8c9ca4",
            "badge_bg": "#cfe7e8",
            "badge_text": "#176b70",
        }
        if has_appointments:
            base.update(
                background="#c9eef0" if in_month else "#d8e9eb",
                border="#20a8ae" if in_month else "#9ebcc1",
                number="#0a4952" if in_month else "#58777e",
                preview="#186b70" if in_month else "#5d7a80",
                badge_bg="#157b86" if in_month else "#8caaae",
                badge_text="#ffffff",
            )
        if selected:
            base.update(
                background="#00b9ac", border="#087a80",
                number="#062e34", preview="#073d42",
                badge_bg="#064e58", badge_text="#f7ffff",
            )
    else:
        base = {
            "background": "#112a37" if in_month else "#0b1d27",
            "border": "#254757" if in_month else "#213641",
            "number": "#e7f4f7" if in_month else "#718c9b",
            "preview": "#a5c0c8" if in_month else "#627d88",
            "badge_bg": "#28505b",
            "badge_text": "#bde9e9",
        }
        if has_appointments:
            base.update(
                background="#145362" if in_month else "#193743",
                border="#28b9b8" if in_month else "#3f7a85",
                number="#ffffff" if in_month else "#b2d9d9",
                preview="#b7fff0" if in_month else "#8abdbb",
                badge_bg="#06b6ae" if in_month else "#286c73",
                badge_text="#05272c" if in_month else "#c5eded",
            )
        if selected:
            base.update(
                background="#00c6b5", border="#23f2df",
                number="#06343a", preview="#07464c",
                badge_bg="#075a62", badge_text="#ffffff",
            )
    if today:
        base["border"] = "#e9bc66"  # Today outline, even on the selected cell.
    return base


def calendar_event_title(item: dict) -> str:
    """An authentic title with a safe fallback, never invented care data."""
    for key in ("title", "activity", "department", "name"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "Marcação"


def calendar_status_badge(item: dict, *, light: bool) -> tuple[str, str, str]:
    state = appointment_status(item)
    if state == "cancelled":
        return ("Cancelada", "#712e38" if not light else "#f9e1e4",
                "#ffe1e5" if not light else "#963e49")
    if state == "done":
        return ("Realizada", "#194f4a" if not light else "#d6f1e7",
                "#b3f6dc" if not light else "#136a58")
    return ("Pendente", "#264e66" if not light else "#dcebf8",
            "#d1edff" if not light else "#1c5c81")


class CalendarVisualV086:
    """Visual override; all existing Takes/Agenda/Backup handlers stay intact."""

    def _calendar(self):
        self.wallpaper_shell.glass_enabled = False
        person = self.store.get_profile(self.active_id) if self.active_id else None
        profile_name = str(person.get("name", "")) if person else ""
        self._heading("Calendário",
                      "Consultas e marcações do perfil: " + profile_name
                      if person else "Seleciona primeiro um perfil.")
        if person is None:
            return

        today = date.today()
        selected = getattr(self, "calendar_selected", today)
        if not isinstance(selected, date):
            selected = today
            self.calendar_selected = selected
        year, month = selected.year, selected.month
        light = self.p["bg"] == "#edf4f7"
        weeks = month_cells(person, year, month)
        current_days = [(day, count) for week in weeks
                        for day, current, count in week if current]
        active_days = sum(count > 0 for _, count in current_days)
        total_events = sum(count for _, count in current_days)

        # One scrolling surface includes both the calendar and the actual
        # appointments. This avoids hiding cards on shorter/larger-font screens.
        surface = ctk.CTkScrollableFrame(
            self.body, fg_color="transparent", corner_radius=0)
        surface.pack(fill="both", expand=True, padx=(4, 4), pady=(0, 4))
        self._calendar_surface = surface

        top = ctk.CTkFrame(surface, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(2, 6))
        heading = ctk.CTkFrame(top, fg_color="transparent")
        heading.pack(side="left", fill="x", expand=True)
        self._label(heading, f"{MONTHS[month-1]} {year}", 25, True).pack(anchor="w")
        detail = (f"{active_days} dia(s) com marcações  •  "
                  f"{total_events} marcação(ões) neste mês")
        self._label(heading, detail, 12, color=self.p["muted"]).pack(
            anchor="w", pady=(0, 2))
        buttons = ctk.CTkFrame(top, fg_color="transparent")
        buttons.pack(side="right", pady=7)
        self._button(buttons, "‹", lambda: self._calendar_move(-1),
                     width=48, height=38).pack(side="left", padx=4)
        self._button(buttons, "Hoje", lambda: self._calendar_choose(today),
                     width=86, height=38).pack(side="left", padx=4)
        self._button(buttons, "›", lambda: self._calendar_move(1),
                     width=48, height=38).pack(side="left", padx=4)

        legend = ctk.CTkFrame(surface, fg_color="transparent")
        legend.pack(fill="x", padx=18, pady=(0, 9))
        for glyph, caption, colour in (
            ("●", "Dia com marcação", "#00bfb4" if not light else "#087d83"),
            ("▢", "Hoje", "#e9bc66" if not light else "#ad7615"),
            ("■", "Selecionado", "#62f0dd" if not light else "#008c84"),
        ):
            chip = ctk.CTkFrame(legend, fg_color="transparent")
            chip.pack(side="left", padx=(0, 23))
            self._label(chip, glyph, 14, True, color=colour).pack(side="left")
            self._label(chip, caption, 11, color=self.p["muted"]).pack(
                side="left", padx=(5, 0))

        # A calendar board with large vertical day cells and information
        # inside each cell, rather than 42 identical one-line buttons.
        board = ctk.CTkFrame(
            surface,
            fg_color="#0b1d28" if not light else "#e9f2f5",
            border_width=1, border_color=self.p["line"], corner_radius=16)
        board.pack(fill="x", padx=10, pady=(0, 12))
        grid = ctk.CTkFrame(board, fg_color="transparent")
        grid.pack(fill="x", padx=10, pady=(11, 11))
        self._calendar_day_cells = {}
        for col in range(7):
            grid.grid_columnconfigure(col, weight=1, uniform="calendar_days")
            self._label(grid, WEEKDAYS[col].upper(), 11, True,
                        anchor="center", color=self.p["muted"]).grid(
                            row=0, column=col, sticky="ew",
                            padx=4, pady=(0, 6))

        # The month grid is generated from the selected profile only.
        for row_i, week in enumerate(weeks, start=1):
            for col, (day, in_month, count) in enumerate(week):
                event_items = appointments_for_day(person, day) if count else []
                palette = calendar_day_colors(
                    has_appointments=bool(event_items),
                    selected=day == selected,
                    today=day == today,
                    in_month=in_month,
                    light=light)
                card = ctk.CTkFrame(
                    grid, height=89, corner_radius=11,
                    fg_color=palette["background"], border_width=2
                    if day == selected or day == today else 1,
                    border_color=palette["border"])
                card.grid(row=row_i, column=col, sticky="nsew",
                          padx=3, pady=3)
                card.grid_propagate(False)
                self._calendar_day_cells[day] = card

                line = ctk.CTkFrame(card, fg_color="transparent")
                line.pack(fill="x", padx=10, pady=(7, 2))
                number = self._label(line, f"{day.day:02d}", 20,
                                     in_month or day == selected,
                                     color=palette["number"])
                number.pack(side="left")
                interactive = [card, line, number]
                if event_items:
                    badge_text = str(count) + (" marcação" if count == 1 else " marcações")
                    badge = ctk.CTkLabel(
                        line, text=badge_text, height=22, corner_radius=9,
                        fg_color=palette["badge_bg"],
                        text_color=palette["badge_text"],
                        font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"))
                    badge.pack(side="right", padx=(2, 0))
                    interactive.append(badge)

                    # Show a genuine upcoming item from this day; ellipses
                    # indicate more entries rather than hiding their count.
                    first = calendar_event_title(event_items[0])
                    preview = self._label(
                        card, "●  " + (first[:24] + "…" if len(first) > 24 else first),
                        10, color=palette["preview"])
                    preview.pack(anchor="w", padx=11, pady=(0, 0))
                    interactive.append(preview)
                    if count > 1:
                        more = self._label(
                            card, f"+ {count - 1} outra(s)", 10,
                            color=palette["preview"])
                        more.pack(anchor="w", padx=11, pady=(0, 2))
                        interactive.append(more)
                elif day == today:
                    today_hint = self._label(card, "HOJE", 10, True,
                                             color=palette["preview"])
                    today_hint.pack(anchor="w", padx=11)
                    interactive.append(today_hint)
                # Make the entire date tile clickable, including its labels.
                for widget in interactive:
                    widget.bind(
                        "<Button-1>",
                        lambda _event, target=day: self._calendar_choose(target),
                        add="+")

        day_events = appointments_for_day(person, selected)
        head = ctk.CTkFrame(surface, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(1, 9))
        titles = ctk.CTkFrame(head, fg_color="transparent")
        titles.pack(side="left", fill="x", expand=True)
        pretty_date = (
            f"{LONG_WEEKDAYS[selected.weekday()].capitalize()}, "
            f"{selected.day} de {MONTHS[selected.month-1].lower()} de {selected.year}")
        self._label(titles, pretty_date, 17, True).pack(anchor="w")
        sub = (f"{len(day_events)} marcação" if len(day_events) == 1
               else f"{len(day_events)} marcações")
        self._label(titles, sub + " neste dia", 11,
                    color=self.p["muted"]).pack(anchor="w", pady=(2, 0))
        actions = ctk.CTkFrame(head, fg_color="transparent")
        actions.pack(side="right", pady=4)
        self._button(actions, "Ver Agenda", lambda: self.navigate("agenda"),
                     width=119, height=37).pack(side="left", padx=(0, 8))
        self._button(actions, "+ Nova marcação",
                     self._calendar_new_appointment, accent=True,
                     width=158, height=37).pack(side="left")

        if not day_events:
            empty = ctk.CTkFrame(
                surface, fg_color=self.p["panel"], corner_radius=14,
                border_width=1, border_color=self.p["line"])
            empty.pack(fill="x", padx=12, pady=(0, 9))
            self._label(empty, "Sem marcações neste dia", 14,
                        True).pack(anchor="w", padx=19, pady=(15, 1))
            self._label(
                empty,
                "Seleciona um dia colorido para consultar as marcações "
                "ou cria uma nova marcação na Agenda.",
                12, color=self.p["muted"]).pack(
                    anchor="w", padx=19, pady=(0, 15))
        else:
            for item in day_events:
                date_time = appointment_datetime(item)
                hour = date_time.strftime("%H:%M") if date_time else "--:--"
                place = str(item.get("location") or item.get("unit") or
                            item.get("place") or "").strip()
                status_text, status_bg, status_fg = calendar_status_badge(
                    item, light=light)
                row = ctk.CTkFrame(
                    surface, fg_color=self.p["panel"], corner_radius=12,
                    border_width=1, border_color=self.p["line"])
                row.pack(fill="x", padx=12, pady=4)
                accent = ctk.CTkFrame(
                    row, fg_color="#00b6ac", width=4,
                    corner_radius=3)
                accent.pack(side="left", fill="y", padx=(0, 11), pady=10)
                self._label(row, hour, 16, True, color="#00c9b7"
                            if not light else "#087d83").pack(
                                side="left", padx=(3, 14), pady=14)
                info = ctk.CTkFrame(row, fg_color="transparent")
                info.pack(side="left", fill="x", expand=True, pady=10)
                self._label(info, calendar_event_title(item)[:180],
                            14, True).pack(anchor="w")
                self._label(info, place[:180] if place else "Local não indicado",
                            11, color=self.p["muted"]).pack(
                                anchor="w", pady=(3, 0))
                status = ctk.CTkLabel(
                    row, text=status_text,
                    fg_color=status_bg, text_color=status_fg,
                    corner_radius=10, height=25,
                    font=ctk.CTkFont(size=11, weight="bold"))
                status.pack(side="left", padx=(6, 10))
                identifier = item.get("id")
                if identifier:
                    self._button(
                        row, "Abrir ficha",
                        lambda uid=identifier: self._open_calendar_appointment(uid),
                        width=111, height=34).pack(
                            side="right", padx=(2, 13), pady=10)
