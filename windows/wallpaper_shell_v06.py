"""Wallpaper shell: composite real wallpaper underneath CTk form panels.

CustomTkinter's fg_color='transparent' is NOT native alpha transparency:
its internal Canvas normally draws an opaque rectangle using its parent's
flat colour. Glass here is a clipped, image-composited 16:9 wallpaper + veil
painted onto the frame's *own* canvas, while interactive controls remain live.
"""
import tkinter as tk
import customtkinter as ctk
from PIL import Image,ImageTk
from windows.visual_v07 import wallpaper_image

class WallpaperShell(tk.Canvas):
    def __init__(self,parent,light=False):
        bg="#edf4f7" if light else "#07151e"
        super().__init__(parent,background=bg,bd=0,highlightthickness=0)
        self.pack(fill="both",expand=True)
        self.light=light
        self._wallpaper_photo=None
        self._background_id=None
        self._glass_photos={}
        self._glass_pending=None
        self.content=ctk.CTkFrame(self,fg_color="transparent",corner_radius=0)
        self._win=self.create_window(18,12,anchor="nw",window=self.content)
        self.bind("<Configure>",self._resize,add="+")
        self.content.bind("<Configure>",self._schedule_glass,add="+")

    def _resize(self,event):
        w=max(1,event.width)
        h=max(1,event.height)
        self._wallpaper_photo=ImageTk.PhotoImage(
            wallpaper_image(w,h,self.light),master=self)
        if self._background_id is None:
            self._background_id=self.create_image(
                0,0,anchor="nw",image=self._wallpaper_photo)
        else:
            self.itemconfigure(self._background_id,image=self._wallpaper_photo)
        self.tag_lower(self._background_id)
        self.itemconfigure(self._win,width=max(1,w-36),height=max(1,h-24))
        self._schedule_glass()

    def _schedule_glass(self,event=None):
        if self._glass_pending is not None:
            try:self.after_cancel(self._glass_pending)
            except (tk.TclError,ValueError):pass
        self._glass_pending=self.after(110,self._paint_glass)

    def _descend(self,root):
        yield root
        for child in root.winfo_children():
            yield from self._descend(child)

    def _paint_glass(self):
        self._glass_pending=None
        if not self.winfo_exists():return
        w,h=self.winfo_width(),self.winfo_height()
        if w<160 or h<160:return
        source=wallpaper_image(w,h,self.light)
        # Panels maintain a 15-22% veil to retain legibility while showing
        # the underlying wallpaper. Do not use OS-level window transparency.
        tint="#e9f2f5" if self.light else "#061622"
        alpha=.19 if self.light else .22
        x0,y0=self.winfo_rootx(),self.winfo_rooty()
        active=set()
        for frame in self._descend(self.content):
            if not isinstance(frame,ctk.CTkFrame):continue
            fw,fh=frame.winfo_width(),frame.winfo_height()
            if fw<235 or fh<92:continue
            canvas=getattr(frame,"_canvas",None)
            if canvas is None:continue
            fx=frame.winfo_rootx()-x0
            fy=frame.winfo_rooty()-y0
            if fx>=w or fy>=h or fx+fw<=0 or fy+fh<=0:continue
            # Crop exact corresponding background, even under resizable panes.
            crop=Image.new("RGB",(fw,fh),tint)
            a,b=max(0,fx),max(0,fy)
            right,bottom=min(w,fx+fw),min(h,fy+fh)
            if right>a and bottom>b:
                part=source.crop((a,b,right,bottom))
                crop.paste(part,(a-fx,b-fy))
            glaze=Image.new("RGB",(fw,fh),tint)
            crop=Image.blend(crop,glaze,alpha)
            photo=ImageTk.PhotoImage(crop,master=canvas)
            active.add(frame)
            self._glass_photos[frame]=photo
            try:
                old=canvas.find_withtag("saudepratica_glass")
                if old:canvas.itemconfigure(old[0],image=photo)
                else:canvas.create_image(0,0,image=photo,anchor="nw",
                                         tags=("saudepratica_glass",))
                canvas.tag_raise("saudepratica_glass")
            except tk.TclError:pass
        for frame in list(self._glass_photos):
            if frame not in active:self._glass_photos.pop(frame,None)
