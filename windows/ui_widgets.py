"""Lightweight, rounded Win32/Tk buttons matching SaúdePrática colors."""
from __future__ import annotations
import tkinter as tk


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text: str, command, *, height=46,
                 fill="#13505c", fg="#f4fbfc", radius=14, font_size=11):
        self._fill=fill
        self._fg=fg
        self._hover="#177d83"
        self._command=command
        self._text=text
        self._radius=radius
        self._font=("Segoe UI",font_size,"bold")
        self._over=False
        self._active=False
        self._enabled=True
        bg=parent.cget("bg")
        super().__init__(parent, width=180, height=height, bd=0,
                         relief="flat", highlightthickness=0, background=bg,
                         takefocus=1, cursor="hand2")
        self.bind("<Configure>",lambda event:self._paint())
        self.bind("<Enter>",self._enter)
        self.bind("<Leave>",self._leave)
        self.bind("<Button-1>",self._click)
        self.bind("<Return>",self._click)
        self.bind("<space>",self._click)
        self.bind("<FocusIn>",lambda _:self._paint())
        self.bind("<FocusOut>",lambda _:self._paint())
        self._paint()

    def configure(self, cnf=None, **kw):
        if "bg" in kw:self._fill=kw.pop("bg")
        if "fg" in kw:self._fg=kw.pop("fg")
        if "text" in kw:self._text=kw.pop("text")
        result=super().configure(cnf,**kw) if kw or cnf else None
        self._paint()
        return result

    config=configure

    def _enter(self,_):
        self._over=True;self._paint()

    def _leave(self,_):
        self._over=False;self._paint()

    def _click(self,_):
        if self._enabled and callable(self._command):
            self._command()

    def _paint(self):
        try:
            w=max(self.winfo_width(),self.winfo_reqwidth(),20)
            h=max(self.winfo_height(),self.winfo_reqheight(),20)
        except tk.TclError:
            return
        r=min(self._radius,h//2,w//2)
        self.delete("all")
        bg=self._hover if self._over else self._fill
        x0,y0,x1,y1=2,2,w-2,h-2
        # Smooth rounded outline drawn from four circles and a centre strip.
        self.create_oval(x0,y0,x0+2*r,y0+2*r,fill=bg,outline="")
        self.create_oval(x1-2*r,y0,x1,y0+2*r,fill=bg,outline="")
        self.create_oval(x0,y1-2*r,x0+2*r,y1,fill=bg,outline="")
        self.create_oval(x1-2*r,y1-2*r,x1,y1,fill=bg,outline="")
        self.create_rectangle(x0+r,y0,x1-r,y1,fill=bg,outline="")
        self.create_rectangle(x0,y0+r,x1,y1-r,fill=bg,outline="")
        self.create_text(w/2,h/2,text=self._text,fill=self._fg,
                         font=self._font,width=max(w-22,10),justify="center")
        if self.focus_get() is self:
            self.create_rectangle(1,1,w-2,h-2,outline="#51e3d6",width=1)
