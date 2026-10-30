"""Window wallpaper shell for forms and options, 16:9 artwork on every page."""
import tkinter as tk
import customtkinter as ctk
from PIL import ImageTk
from windows.visual_v06 import wallpaper_image

class WallpaperShell(tk.Canvas):
    def __init__(self,parent,light=False):
        background="#edf4f7" if light else "#07151e"
        super().__init__(parent,background=background,bd=0,
                         highlightthickness=0)
        self.pack(fill="both",expand=True)
        self.light=light
        self._wallpaper_photo=None
        self._background_id=None
        self.content=ctk.CTkFrame(self,fg_color="transparent",
                                  corner_radius=0)
        self._win=self.create_window(18,12,anchor="nw",window=self.content)
        self.bind("<Configure>",self._resize,add="+")

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
