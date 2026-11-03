"""Private profile-specific document preview and memory-only printing.

Decrypted clinical PDFs/images are never written to a temporary plaintext file.
An in-process reader uses PyMuPDF/Pillow and the Windows printer GDI.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageOps

from windows.secure_store import LocalStoreError

MAX_PREVIEW_BYTES = 28 * 1024 * 1024
MAX_IMAGE_PIXELS = 32_000_000


def document_kind(raw: bytes, filename: str = "") -> str:
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_PREVIEW_BYTES:
        raise ValueError("Documento vazio ou demasiado grande para pré-visualizar.")
    if raw[:5] == b"%PDF-":
        return "pdf"
    if raw[:3] == b"\xff\xd8\xff":
        return "image"
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return "image"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image"
    raise ValueError("Pré-visualização disponível apenas para PDF, JPG, PNG e WebP.")


def render_document(raw: bytes, filename: str, index: int = 0,
                    max_width: int = 640, max_height: int = 600):
    """Return (RGB PIL preview, page count) from verified bytes, in memory."""
    kind = document_kind(raw, filename)
    if index < 0 or max_width < 100 or max_height < 100:
        raise ValueError("Página ou tamanho inválido.")
    if kind == "pdf":
        import fitz
        with fitz.open(stream=raw, filetype="pdf") as pdf:
            if pdf.needs_pass:
                raise ValueError("PDF protegido com palavra-passe.")
            total = len(pdf)
            if not total:
                raise ValueError("PDF sem páginas.")
            if index >= total:
                raise ValueError("Página não existe.")
            page = pdf[index]
            bounds = page.rect
            if bounds.width <= 0 or bounds.height <= 0:
                raise ValueError("Página PDF com tamanho inválido.")
            scale = min(2.0, max_width / bounds.width,
                        max_height / bounds.height)
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale),
                                  alpha=False, colorspace=fitz.csRGB)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            return image, total
    if index:
        raise ValueError("Esta imagem tem apenas uma página.")
    with Image.open(BytesIO(raw)) as file:
        if file.width * file.height > MAX_IMAGE_PIXELS:
            raise ValueError("Imagem demasiado grande para pré-visualização.")
        if file.format not in {"PNG", "JPEG", "WEBP"}:
            raise ValueError("Formato de imagem não permitido.")
        image = ImageOps.exif_transpose(file).convert("RGB")
    image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    return image, 1


def printer_preview(raw: bytes, filename: str):
    """Send all pages to the default Windows printer; no plaintext disk file.

    Caller must first obtain affirmative consent, describing the target
    default printer. The OS print queue may retain its normal spool data.
    """
    import win32print
    import win32ui
    import win32con
    from PIL import ImageWin

    target = win32print.GetDefaultPrinter()
    kind = document_kind(raw, filename)
    total = 1
    if kind == "pdf":
        import fitz
        with fitz.open(stream=raw, filetype="pdf") as doc:
            if doc.needs_pass:
                raise ValueError("PDF protegido com palavra-passe.")
            total = len(doc)
    if total < 1 or total > 100:
        raise ValueError("Só são permitidos documentos de 1 a 100 páginas.")
    dc = win32ui.CreateDC()
    dc.CreatePrinterDC(target)
    started = False
    try:
        width = dc.GetDeviceCaps(win32con.HORZRES)
        height = dc.GetDeviceCaps(win32con.VERTRES)
        if width <= 0 or height <= 0:
            raise RuntimeError("Área de impressão inválida.")
        dc.StartDoc("SaúdePrática — documento")
        started = True
        for page in range(total):
            # Bound each GDI bitmap to the printer's printable pixels.
            image, _ = render_document(
                raw, filename, page,
                min(width, 2400), min(height, 3200))
            x = max(0, (width - image.width) // 2)
            y = max(0, (height - image.height) // 2)
            dc.StartPage()
            ImageWin.Dib(image).draw(
                dc.GetHandleOutput(), (x, y, x + image.width, y + image.height))
            dc.EndPage()
        dc.EndDoc()
    except Exception:
        if started:
            try: dc.AbortDoc()
            except Exception: pass
        raise
    finally:
        dc.DeleteDC()
    return target, total


class DocumentsV087:
    def _doc_entry_for_active(self):
        person = self.store.get_profile(self.active_id) if self.active_id else None
        if not person:
            return None
        digest = getattr(self, "doc_selected_digest", None)
        return next((item for item in self.store.imported_assets(person["id"])
                     if item.get("sha256") == digest and
                     item.get("profile_id") == person["id"]), None)

    def _doc_select(self, digest):
        self.doc_selected_digest = digest
        self.doc_selected_profile = self.active_id
        self.doc_page_index = 0
        self._render()

    def _doc_step(self, direction):
        entry = self._doc_entry_for_active()
        if not entry:
            return
        index = getattr(self, "doc_page_index", 0) + direction
        if 0 <= index < getattr(self, "_doc_total_pages", 1):
            self.doc_page_index = index
            self._render()

    def _doc_preview(self, parent, entry):
        if not entry:
            self._label(parent, "Seleciona um documento na lista à esquerda.",
                        13, color=self.p["muted"]).pack(padx=12, pady=22)
            return
        try:
            data = self.store.read_imported_asset(entry)
            filename = str(entry.get("filename") or "documento")
            image, total = render_document(
                data, filename, getattr(self, "doc_page_index", 0), 550, 470)
            self._doc_total_pages = total
            self._doc_preview_art = ctk.CTkImage(
                image, image, size=image.size)
        except (OSError, ValueError, LocalStoreError, RuntimeError) as exc:
            self._doc_total_pages = 0
            self._label(parent, "Não foi possível mostrar este documento.", 13,
                        True).pack(anchor="w", padx=15, pady=(12, 4))
            self._label(parent, str(exc)[:200], 11,
                        color=self.p["muted"], wrap=450).pack(anchor="w", padx=15)
            return

        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(1, 6))
        self._label(top, f"Página {getattr(self, 'doc_page_index', 0)+1} de {total}",
                    12, color=self.p["muted"]).pack(side="left")
        if total > 1:
            self._button(top, "›", lambda:self._doc_step(+1),
                         width=38).pack(side="right", padx=(4, 0))
            self._button(top, "‹", lambda:self._doc_step(-1),
                         width=38).pack(side="right")
        # In a scrollable area, PDF and image previews retain aspect ratio.
        photo = ctk.CTkLabel(parent, image=self._doc_preview_art, text="")
        photo.pack(anchor="center", padx=8, pady=(0, 5))
        photo.bind("<Double-Button-1>",
                   lambda _event:self._doc_open_viewer())

    def _doc_open_viewer(self):
        entry = self._doc_entry_for_active()
        if entry is None:
            return
        old = getattr(self, "_doc_viewer_window", None)
        if old is not None and old.winfo_exists():
            old.lift()
            return
        window = ctk.CTkToplevel(self)
        window.title("SaúdePrática · Visualização de documento")
        window.geometry("1120x780")
        window.minsize(680, 480)
        window.transient(self)
        self._doc_viewer_window = window
        self._doc_viewer_profile = self.active_id
        self._doc_viewer_digest = entry["sha256"]
        self._doc_viewer_index = 0
        self._doc_viewer_picture = None
        self._doc_viewer_controls = ctk.CTkFrame(
            window, fg_color="transparent")
        self._doc_viewer_controls.pack(fill="x", padx=14, pady=12)
        self._doc_viewer_counter = ctk.CTkLabel(
            self._doc_viewer_controls, text="")
        self._doc_viewer_counter.pack(side="left", padx=8)
        self._doc_viewer_label = ctk.CTkLabel(window, text="")
        self._doc_viewer_label.pack(fill="both", expand=True, padx=12, pady=7)
        self._button(self._doc_viewer_controls, "Fechar",
                     self._doc_close_viewer,width=80).pack(side="right",padx=7)
        self._button(self._doc_viewer_controls, "Seguinte ›",
                     lambda:self._doc_viewer_step(+1),width=95).pack(side="right",padx=4)
        self._button(self._doc_viewer_controls, "‹ Anterior",
                     lambda:self._doc_viewer_step(-1),width=95).pack(side="right",padx=4)
        window.protocol("WM_DELETE_WINDOW",self._doc_close_viewer)
        self._doc_viewer_show()

    def _doc_viewer_show(self):
        entry = self._doc_entry_for_active()
        if (entry is None or self.active_id != getattr(self, "_doc_viewer_profile", None)
                or entry["sha256"] != getattr(self, "_doc_viewer_digest", None)):
            self._doc_close_viewer()
            return
        try:
            raw = self.store.read_imported_asset(entry)
            picture, total = render_document(
                raw, entry.get("filename", ""),
                self._doc_viewer_index, 1000, 680)
            self._doc_viewer_total = total
            self._doc_viewer_picture = ctk.CTkImage(
                picture, picture, size=picture.size)
            self._doc_viewer_label.configure(image=self._doc_viewer_picture, text="")
            self._doc_viewer_counter.configure(
                text=f"{entry.get('display_name') or entry.get('filename')} · "
                     f"Página {self._doc_viewer_index+1}/{total}")
        except (OSError, LocalStoreError, ValueError, RuntimeError) as exc:
            messagebox.showerror("Documentos", str(exc), parent=self)
            self._doc_close_viewer()

    def _doc_viewer_step(self, direction):
        index = self._doc_viewer_index + direction
        if 0 <= index < getattr(self, "_doc_viewer_total", 1):
            self._doc_viewer_index = index
            self._doc_viewer_show()

    def _doc_close_viewer(self):
        window = getattr(self, "_doc_viewer_window", None)
        self._doc_viewer_window = None
        self._doc_viewer_picture = None
        if window is not None and window.winfo_exists():
            window.destroy()

    def _doc_print(self):
        entry = self._doc_entry_for_active()
        if entry is None:
            return
        try:
            import win32print
            printer = win32print.GetDefaultPrinter()
        except Exception:
            messagebox.showerror("Impressão",
                "Não existe uma impressora predefinida disponível neste Windows.",
                parent=self)
            return
        if not messagebox.askyesno(
            "Imprimir documento",
            f"Imprimir {entry.get('display_name') or entry.get('filename')} "
            f"na impressora predefinida:\n{printer}\n\n"
            "O Windows poderá manter dados na fila de impressão. Continuar?",
            parent=self):
            return
        try:
            raw = self.store.read_imported_asset(entry)
            _, pages = printer_preview(raw, entry.get("filename", ""))
            messagebox.showinfo("Impressão",
                f"{pages} página(s) enviadas para a impressora.", parent=self)
        except (OSError, ValueError, LocalStoreError, RuntimeError, Exception) as exc:
            messagebox.showerror("Impressão", str(exc)[:350], parent=self)

    def _documents(self):
        self.wallpaper_shell.glass_enabled = False
        profile = self.store.get_profile(self.active_id) if self.active_id else None
        self._heading("Documentos", "Ficheiros protegidos do perfil: " +
                      str(profile.get("name", "")) if profile else "Seleciona um perfil.")
        if profile is None:
            return
        if getattr(self, "doc_selected_profile", None) != self.active_id:
            self.doc_selected_digest = None
            self.doc_page_index = 0
            self.doc_selected_profile = self.active_id
        items = self.store.imported_assets(profile["id"])
        known = {row.get("sha256") for row in items}
        if getattr(self, "doc_selected_digest", None) not in known:
            self.doc_selected_digest = items[0].get("sha256") if items else None
            self.doc_page_index = 0

        split = ctk.CTkFrame(self.body, fg_color="transparent")
        split.pack(fill="both", expand=True, padx=(6, 7), pady=(0, 5))
        split.grid_columnconfigure(0, weight=8, uniform="docs")
        split.grid_columnconfigure(1, weight=12, uniform="docs")
        split.grid_rowconfigure(0, weight=1)
        self._doc_split = split
        left = ctk.CTkFrame(split, fg_color=self.p["panel"], corner_radius=13,
                            border_width=1, border_color=self.p["line"])
        left.grid(row=0,column=0,sticky="nsew",padx=(0,7))
        right = ctk.CTkFrame(split, fg_color=self.p["panel"], corner_radius=13,
                             border_width=1, border_color=self.p["line"])
        right.grid(row=0,column=1,sticky="nsew",padx=(7,0))
        self._doc_list_panel = left
        self._doc_preview_panel = right

        heading = ctk.CTkFrame(left, fg_color="transparent")
        heading.pack(fill="x", padx=13, pady=(10, 4))
        self._label(heading, f"Documentos ({len(items)})", 17, True).pack(side="left")
        actions = ctk.CTkFrame(left, fg_color="transparent")
        actions.pack(fill="x", padx=12, pady=(0, 7))
        self._button(actions, "+ Importar", self._add_manual_document,
                     True, width=122).pack(side="left", padx=(0, 6))
        self._button(actions, "Importar ZIP", lambda:self.navigate("import"),
                     width=111).pack(side="left")
        scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=(0, 7))
        if not items:
            self._label(scroll, "Sem documentos neste perfil.", 12,
                        color=self.p["muted"]).pack(anchor="w", padx=8, pady=14)
        for item in items:
            digest=item.get("sha256")
            current=digest == self.doc_selected_digest
            row = ctk.CTkFrame(
                scroll, fg_color=self.p["chip"] if current else self.p["panel2"],
                corner_radius=10, border_width=1,
                border_color="#00c9b7" if current else self.p["line"])
            row.pack(fill="x", padx=4, pady=3)
            desc = str(item.get("display_name") or item.get("filename") or "Documento")
            subtitle = str(item.get("category") or "Ficheiro") + " · " + (
                f"{item.get('bytes',0)/1024:.0f} KB" if isinstance(
                    item.get("bytes"),(int,float)) else "tamanho desconhecido")
            title = self._label(row, desc[:90], 12, True, wrap=290)
            title.pack(anchor="w", padx=11, pady=(7, 1))
            sub = self._label(row, subtitle[:110], 10, color=self.p["muted"])
            sub.pack(anchor="w", padx=11, pady=(0, 7))
            for widget in (row,title,sub):
                widget.bind("<Button-1>",
                            lambda _event, h=digest:self._doc_select(h),add="+")

        preview_header = ctk.CTkFrame(right, fg_color="transparent")
        preview_header.pack(fill="x", padx=13, pady=(10, 4))
        self._label(preview_header, "Pré-visualização", 17, True).pack(side="left")
        entry = self._doc_entry_for_active()
        if entry:
            controls = ctk.CTkFrame(right, fg_color="transparent")
            controls.pack(fill="x", padx=12, pady=(0, 4))
            self._button(controls, "Abrir", self._doc_open_viewer,
                         True, width=83).pack(side="left", padx=(0, 5))
            self._button(controls, "Imprimir", self._doc_print,
                         width=93).pack(side="left", padx=(0, 5))
            self._button(controls, "Guardar como",
                         lambda e=entry:self._export_document(e),
                         width=118).pack(side="left")
        preview = ctk.CTkScrollableFrame(
            right, fg_color="transparent", corner_radius=0)
        preview.pack(fill="both", expand=True, padx=7, pady=(3, 8))
        self._doc_preview(preview, entry)
