"""Resident SaúdePrática reminders. Built with NO boot splash.

Independent PyInstaller EXE so launching a background notifier never displays
the main application startup artwork or any foreground Tk window.
"""
from windows.reminder_agent_v071 import run_reminder_agent

if __name__=="__main__":
    run_reminder_agent()
