"""Smoke-test actual Windows desktop startup, including PyInstaller splash.

Use only an isolated, synthetic temporary profile store. CI requires the GUI
to finish the first render and close within 75s; an EXE that merely compiles
but hangs on the splash is a FAILED build.
"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]

def main():
    if sys.platform!="win32":
        raise SystemExit("Windows required for a GUI smoke test")
    packaged="--exe" in sys.argv
    if packaged:
        target=ROOT/"dist"/"SaudePraticaDesktop"/"SaudePraticaDesktop.exe"
        command=[str(target)]
    else:
        command=[sys.executable,str(ROOT/"windows"/"desktop_v04.py")]

    with tempfile.TemporaryDirectory(prefix="saudepratica-ci-gui-") as tmp:
        marker=Path(tmp)/"gui_ready.txt"
        local=Path(tmp)/"LocalAppData"
        local.mkdir()
        env=os.environ.copy()
        env["LOCALAPPDATA"]=str(local)
        env["SAUDEPRATICA_SMOKE_REPORT"]=str(marker)
        env["PYTHONUNBUFFERED"]="1"
        print("Testing", "packaged EXE" if packaged else "Python source", flush=True)
        try:
            run=subprocess.run(command,env=env,cwd=ROOT,capture_output=True,
                               text=True,timeout=75,check=False)
        except subprocess.TimeoutExpired as exc:
            raise SystemExit("FAIL: GUI hung (splash never closed): "+str(exc))
        if marker.exists():
            status=marker.read_text(encoding="utf-8")
        else:
            status="NO_GUI_READY_MARKER"
        if run.returncode or not status.startswith("GUI_READY"):
            print("Exit code:",run.returncode)
            print("GUI diagnostic:",status[:9000])
            print("Standard error:",run.stderr[-9000:])
            print("Standard output:",run.stdout[-4000:])
            raise SystemExit(1)
        print("PASS: first GUI frame rendered, splash dismissed and app exited.")

if __name__=="__main__":
    main()
