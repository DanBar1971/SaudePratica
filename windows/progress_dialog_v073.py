"""Non-blocking, truthful phase progress for Windows backups and restores.

The percentages represent completed verified phases, not invented file bytes.
All Tk widgets are touched on the Tk thread. Worker messages use Queue.
"""
import queue
import threading
import tkinter as tk
import customtkinter as ctk

def run_progress(app, title, work, on_success, on_error):
    events=queue.Queue()
    dialog=ctk.CTkToplevel(app)
    dialog.title(title)
    dialog.geometry("490x205")
    dialog.resizable(False,False)
    dialog.transient(app)
    dialog.grab_set()
    dialog.protocol("WM_DELETE_WINDOW",lambda:None)
    frame=ctk.CTkFrame(dialog)
    frame.pack(fill="both",expand=True,padx=14,pady=14)
    ctk.CTkLabel(frame,text=title,font=ctk.CTkFont(size=18,weight="bold")).pack(
        fill="x",pady=(5,11))
    label=ctk.CTkLabel(frame,text="A preparar…",font=ctk.CTkFont(size=13))
    label.pack(fill="x",pady=(0,8))
    bar=ctk.CTkProgressBar(frame,height=17,mode="determinate")
    bar.pack(fill="x",padx=16)
    bar.set(0)
    percent=ctk.CTkLabel(frame,text="0% concluído",font=ctk.CTkFont(size=15,weight="bold"))
    percent.pack(pady=(8,0))
    dialog.update_idletasks()
    def worker():
        try:
            def report(pct,message):
                events.put(("progress",max(0,min(100,int(pct))),str(message)))
            result=work(report)
            events.put(("done",result))
        except Exception as exc:
            events.put(("error",exc))
    def drain():
        completed=False
        try:
            while True:
                msg=events.get_nowait()
                if msg[0]=="progress":
                    _,pct,caption=msg
                    bar.set(pct/100)
                    label.configure(text=caption)
                    percent.configure(text=f"{pct}% concluído")
                else:
                    completed=True
                    try:dialog.grab_release()
                    except tk.TclError:pass
                    dialog.destroy()
                    if msg[0]=="done":on_success(msg[1])
                    else:on_error(msg[1])
                    break
        except queue.Empty:
            pass
        if not completed and dialog.winfo_exists():
            dialog.after(80,drain)
    threading.Thread(target=worker,daemon=True).start()
    dialog.after(80,drain)
