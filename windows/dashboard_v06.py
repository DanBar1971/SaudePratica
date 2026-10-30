"""Canvas dashboard: wallpaper is painted ON the canvas, not placed behind
an opaque CTkLabel. Prevents the 'Olá' broken rectangles from v0.5.
All tiles are actionable Tk canvas tags, not a static screenshot.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import font as tkfont
from PIL import ImageTk
from windows.ui_catalog_v05 import MODULE_CARDS, normalized
from windows.visual_v06 import wallpaper_image, icon_image

def _rounded(c, x1, y1, x2, y2, radius, **kw):
    r=min(radius,(x2-x1)/2,(y2-y1)/2)
    points=[
        x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,x2,y2-r,
        x2,y2,x2-r,y2,x1+r,y2,x1,y2,x1,y2-r,
        x1,y1+r,x1,y1
    ]
    return c.create_polygon(points,smooth=True,splinesteps=16,**kw)

class Dashboard(tk.Canvas):
    def __init__(self,parent,app,full=False):
        self.app=app
        self.full=full
        self.is_light=(app.p["bg"]=="#edf4f7")
        bg=app.p["bg"]
        super().__init__(parent,highlightthickness=0,bd=0,background=bg,
                         takefocus=1)
        self.pack(fill="both",expand=True)
        self._background_photo=None
        self._icon_cache=[]
        self._paint_pending=False
        self._scroll=None
        self._width=0
        self._height=0
        self.search_var=tk.StringVar(master=self,value=app.catalog_query)
        self.search_field=tk.Entry(self,textvariable=self.search_var,bd=1,
                        relief="flat",highlightthickness=1,
                        highlightbackground=app.p["line"],
                        highlightcolor="#00c9b7",bg=app.p["field"],
                        fg=app.p["text"],insertbackground=app.p["text"],
                        font=("Segoe UI",11))
        self.search_field.bind("<KeyRelease>",self._on_search)
        self.search_field.bind("<Escape>",lambda e:self._clear_search())
        self.bind("<Configure>",self._resize,add="+")
        self.bind("<MouseWheel>",self._wheel,add="+")
        self.bind("<Button-4>",lambda e:self.yview_scroll(-2,"units"),add="+")
        self.bind("<Button-5>",lambda e:self.yview_scroll(2,"units"),add="+")
        self.after_idle(self._paint)

    def _clear_search(self):
        self.search_var.set("")
        self._on_search()

    def _on_search(self,event=None):
        self.app.catalog_query=self.search_var.get()
        self._paint_cards()

    def _wheel(self,event):
        if self._height>self.winfo_height():
            self.yview_scroll(int(-event.delta/120)*2,"units")

    def _resize(self,event):
        if event.width!=self._width or event.height!=self._height:
            self._width=event.width
            self._height=event.height
            if not self._paint_pending:
                self._paint_pending=True
                self.after_idle(self._paint)

    def _paint(self):
        self._paint_pending=False
        w=max(self.winfo_width(),900)
        h=max(self.winfo_height(),450)
        self.delete("all")
        self._icon_cache.clear()
        self._bg_dims=(w,h)
        self._background_photo=ImageTk.PhotoImage(
             wallpaper_image(w,h,self.is_light),master=self)
        self.create_image(0,0,image=self._background_photo,anchor="nw",
                          tags="background")
        self._top=15
        dark=self.is_light
        title_color=self.app.p["text"]
        sub_color=self.app.p["muted"] if dark else "#d1e6ed"
        if not self.full:
            p=self.app.store.get_profile(self.app.active_id)
            first=p.get("name","").split()[0] if p and p.get("name") else ""
            lead="Olá, " if self.app.lang=="pt" else self.app.t("welcome")
            if first and self.app.lang=="pt":
                self.create_text(30,29,text=lead,anchor="nw",fill=title_color,
                                 font=("Segoe UI",29,"bold"))
                x=30+115
                self.create_text(x,29,text=first+"!",anchor="nw",
                    fill="#00d6c6" if not dark else "#007d75",
                    font=("Segoe UI",29,"bold"))
            else:
                self.create_text(30,29,text=self.app.t("welcome"),anchor="nw",
                    fill=title_color,font=("Segoe UI",28,"bold"))
            count=len(p.get("medications",[])) if p else 0
            sub=f"{count} medicamento(s)  •  {self.app.t('welcome_sub')}"
            self.create_text(30,85,text=sub,anchor="nw",fill=sub_color,
                             font=("Segoe UI",12))
            self._module_top=179
        else:
            self.create_text(30,31,text=self.app.t("menu_more"),
                             anchor="nw",fill=title_color,
                             font=("Segoe UI",23,"bold"))
            self._module_top=91
        self.create_text(29,self._module_top-27,
             text=self.app.t("sections") if not self.full else "Explorar módulos",
             anchor="nw",fill=title_color,font=("Segoe UI",16,"bold"))
        self.create_window(w-27,self._module_top-24,window=self.search_field,
                           anchor="ne",width=216,height=31,tags="search")
        self._paint_cards()

    def _paint_cards(self):
        self.delete("cards")
        self._icon_cache.clear()
        w=max(self.winfo_width(),900)
        cols=5 if w>=1250 else 4 if w>=1000 else 3
        margin=28
        gutter=12
        cw=(w-2*margin-(cols-1)*gutter)/cols
        ch=91
        query=normalized(self.search_var.get())
        cards=[c for c in MODULE_CARDS if query in normalized(c[2]+" "+c[3])]
        for i,(key,icon,title,description,ready) in enumerate(cards):
            row,col=divmod(i,cols)
            x=margin+col*(cw+gutter)
            y=self._module_top+row*(ch+11)
            tag=f"module_{i}"
            base="#18303d" if not self.is_light else "#f5fafc"
            edge="#276777" if not self.is_light else "#91c4cc"
            _rounded(self,x,y,x+cw,y+ch,13,fill=base,outline=edge,
                     width=1,tags=("cards",tag))
            ico=ImageTk.PhotoImage(icon_image(icon,i,46),master=self)
            self._icon_cache.append(ico)
            self.create_image(x+15,y+23,image=ico,anchor="nw",
                              tags=("cards",tag))
            name=self.app.t(key) if key in ("medication","agenda","documents",
                "water","nutrition","profiles","residences","shortcuts",
                "info","backup","sync","options") else title
            foreground=self.app.p["text"]
            muted=self.app.p["muted"]
            self.create_text(x+73,y+20,text=name,fill=foreground,
                         anchor="nw",font=("Segoe UI",12,"bold"),tags=("cards",tag))
            self.create_text(x+73,y+48,text=description,fill=muted,
                         anchor="nw",font=("Segoe UI",10),tags=("cards",tag),
                         width=max(70,cw-100))
            self.create_oval(x+cw-33,y+ch-34,x+cw-12,y+ch-13,
                             fill="#1e4b5b" if not self.is_light else "#d6e9eb",
                             outline="",tags=("cards",tag))
            self.create_text(x+cw-22.5,y+ch-24,text="›",fill="#e7ffff" if
                 not self.is_light else "#124a59",font=("Segoe UI",15,"bold"),
                 tags=("cards",tag))
            if not ready:
                # Keep honesty about feature state without overpowering the UI.
                self.create_text(x+cw-9,y+7,text="EM BREVE",anchor="ne",
                    fill="#b6cfda" if not self.is_light else "#46636e",
                    font=("Segoe UI",7),tags=("cards",tag))
            self.tag_bind(tag,"<Button-1>",lambda e,k=key:self.app.navigate(k))
            self.tag_bind(tag,"<Enter>",lambda e,t=tag:self._hover(t,True))
            self.tag_bind(tag,"<Leave>",lambda e,t=tag:self._hover(t,False))
        rows=(len(cards)+cols-1)//cols
        end=self._module_top+rows*(ch+11)+15
        self._height=end
        self.configure(scrollregion=(0,0,w,max(end,self.winfo_height())))

    def _hover(self,tag,on):
        items=self.find_withtag(tag)
        if not items:return
        try:
            self.itemconfigure(items[0],fill=(
                "#214251" if on else "#18303d") if not self.is_light else (
                "#e6f5f5" if on else "#f5fafc"))
        except tk.TclError:pass
        self.configure(cursor="hand2" if on else "")
