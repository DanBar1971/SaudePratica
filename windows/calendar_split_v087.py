"""Windows 0.8.7 compact split calendar. No database mutations or global patient queries."""
from __future__ import annotations

from datetime import date
import customtkinter as ctk

from windows.calendar_ui_v086 import (
    calendar_day_colors, calendar_event_title, calendar_status_badge,
    LONG_WEEKDAYS,
)
from windows.doses_calendar_v085 import WEEKDAYS, MONTHS, month_cells, appointments_for_day
from windows.agenda_filter_v069 import appointment_datetime


class CalendarSplitV087:
    def _calendar(self):
        self.wallpaper_shell.glass_enabled = False
        profile = self.store.get_profile(self.active_id) if self.active_id else None
        self._heading("Calendário", "Marcações do perfil: " + str(profile.get("name", ""))
                      if profile else "Seleciona um perfil.")
        if profile is None:
            return
        today = date.today()
        selected = getattr(self, "calendar_selected", today)
        if not isinstance(selected, date):
            selected = today
            self.calendar_selected = selected
        light = self.p["bg"] == "#edf4f7"
        weeks = month_cells(profile, selected.year, selected.month)
        count = sum(qty for week in weeks for day, own, qty in week if own)

        split = ctk.CTkFrame(self.body, fg_color="transparent")
        split.pack(fill="both", expand=True, padx=(5, 6), pady=(0, 5))
        split.grid_columnconfigure(0, weight=11, uniform="saude_split")
        split.grid_columnconfigure(1, weight=9, uniform="saude_split")
        split.grid_rowconfigure(0, weight=1)
        self._calendar_split = split
        left = ctk.CTkFrame(split, fg_color=self.p["panel"], corner_radius=15,
                            border_width=1, border_color=self.p["line"])
        left.grid(row=0, column=0, sticky="nsew", padx=(3, 7))
        right = ctk.CTkFrame(split, fg_color=self.p["panel"], corner_radius=15,
                             border_width=1, border_color=self.p["line"])
        right.grid(row=0, column=1, sticky="nsew", padx=(7, 3))
        self._calendar_left = left
        self._calendar_right = right

        top = ctk.CTkFrame(left, fg_color="transparent")
        top.pack(fill="x", padx=13, pady=(13, 7))
        heading = ctk.CTkFrame(top, fg_color="transparent")
        heading.pack(side="left", fill="x", expand=True)
        self._label(heading, f"{MONTHS[selected.month-1]} {selected.year}",
                    21, True).pack(anchor="w")
        self._label(heading, f"{count} marcações neste mês", 11,
                    color=self.p["muted"]).pack(anchor="w")
        nav = ctk.CTkFrame(top, fg_color="transparent")
        nav.pack(side="right")
        self._button(nav, "‹", lambda: self._calendar_move(-1),
                     width=40, height=33).pack(side="left", padx=(0, 3))
        self._button(nav, "Hoje", lambda: self._calendar_choose(today),
                     width=64, height=33).pack(side="left", padx=3)
        self._button(nav, "›", lambda: self._calendar_move(1),
                     width=40, height=33).pack(side="left", padx=(3, 0))

        grid = ctk.CTkFrame(left, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=10, pady=(1, 11))
        for col in range(7):
            grid.grid_columnconfigure(col, weight=1, uniform="day")
            self._label(grid, WEEKDAYS[col].upper(), 11, True,
                        color=self.p["muted"], anchor="center").grid(
                            row=0, column=col, sticky="ew", padx=2, pady=(0, 5))
        self._calendar_day_cells = {}
        for row_n, week in enumerate(weeks, start=1):
            grid.grid_rowconfigure(row_n, weight=1, uniform="calendar_week")
            for col, (day, in_month, day_count) in enumerate(week):
                paint = calendar_day_colors(
                    has_appointments=day_count > 0,
                    selected=day == selected, today=day == today,
                    in_month=in_month, light=light)
                tile = ctk.CTkFrame(
                    grid, fg_color=paint["background"], corner_radius=9,
                    border_color=paint["border"],
                    border_width=2 if day == today or day == selected else 1,
                    height=57)
                tile.grid(row=row_n, column=col, sticky="nsew", padx=2, pady=2)
                tile.grid_propagate(False)
                self._calendar_day_cells[day] = tile
                day_num = self._label(
                    tile, str(day.day), 16, in_month or day == selected,
                    color=paint["number"])
                day_num.pack(anchor="nw", padx=7, pady=(5, 0))
                clickable = [tile, day_num]
                if day_count:
                    badge = ctk.CTkLabel(
                        tile, text=f"● {day_count}", height=18, corner_radius=8,
                        fg_color=paint["badge_bg"], text_color=paint["badge_text"],
                        font=ctk.CTkFont(size=10, weight="bold"))
                    badge.pack(anchor="sw", padx=6, pady=(0, 4))
                    clickable.append(badge)
                elif day == today:
                    mark = self._label(tile, "HOJE", 8, True, color=paint["preview"])
                    mark.pack(anchor="sw", padx=7, pady=(0, 3))
                    clickable.append(mark)
                for widget in clickable:
                    widget.bind("<Button-1>",
                                lambda _event, chosen=day:self._calendar_choose(chosen),
                                add="+")

        # Right panel is independently scrollable; left month never moves.
        header = ctk.CTkFrame(right, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(12, 8))
        day_title = (f"{selected.day} de {MONTHS[selected.month-1].lower()} "
                     f"de {selected.year}")
        self._label(header, day_title, 18, True).pack(anchor="w")
        self._label(header, LONG_WEEKDAYS[selected.weekday()].capitalize(), 11,
                    color=self.p["muted"]).pack(anchor="w", pady=(1, 0))
        events = appointments_for_day(profile, selected)
        self._label(header,
                    f"{len(events)} marcação" if len(events) == 1
                    else f"{len(events)} marcações",
                    12, True, color="#00a79f" if light else "#70eee0").pack(
                        anchor="w", pady=(5, 0))
        buttons = ctk.CTkFrame(right, fg_color="transparent")
        buttons.pack(fill="x", padx=14, pady=(0, 7))
        self._button(buttons, "+ Nova marcação", self._calendar_new_appointment,
                     True, width=151, height=34).pack(side="left")
        self._button(buttons, "Ver Agenda", lambda:self.navigate("agenda"),
                     width=110, height=34).pack(side="left", padx=7)
        listing = ctk.CTkScrollableFrame(
            right, fg_color="transparent", corner_radius=0)
        listing.pack(fill="both", expand=True, padx=(6, 7), pady=(0, 9))
        self._calendar_day_list = listing
        if not events:
            self._label(listing, "Sem marcações neste dia.", 13,
                        color=self.p["muted"]).pack(anchor="w", padx=12, pady=20)
            return
        for event in events:
            when = appointment_datetime(event)
            hour = when.strftime("%H:%M") if when else "--:--"
            status_text, bg, fg = calendar_status_badge(event, light=light)
            row = ctk.CTkFrame(
                listing, fg_color=self.p["panel2"], corner_radius=10,
                border_width=1, border_color=self.p["line"])
            row.pack(fill="x", padx=3, pady=3)
            self._label(row, hour, 14, True, color="#007e79" if light
                        else "#50e4d7").pack(side="left", padx=(9, 10), pady=11)
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, pady=8)
            self._label(info, calendar_event_title(event)[:90], 12,
                        True, wrap=230).pack(anchor="w")
            place = str(event.get("location") or event.get("unit")
                        or event.get("place") or "").strip()
            if place:
                self._label(info, place[:95], 10, color=self.p["muted"],
                            wrap=230).pack(anchor="w", pady=(1, 0))
            status = ctk.CTkLabel(
                row, text=status_text, fg_color=bg, text_color=fg,
                corner_radius=8, height=23, font=ctk.CTkFont(size=10))
            status.pack(side="left", padx=(4, 5))
            uid = event.get("id")
            if uid:
                self._button(row, "Abrir",
                             lambda eid=uid:self._open_calendar_appointment(eid),
                             width=58, height=30).pack(side="right", padx=(0, 7))
