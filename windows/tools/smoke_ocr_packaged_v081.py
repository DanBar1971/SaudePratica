"""Test the actual packaged OCR engine, including native ONNX DLLs and models."""
import os
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[2]
EXE=ROOT/"dist"/"SaudePraticaDesktop"/"SaudePraticaDesktop.exe"

def main():
    with tempfile.TemporaryDirectory(prefix="sp-ocr-smoke-") as tmp:
        report=Path(tmp)/"ocr_ready.txt"
        env=os.environ.copy()
        env["SAUDEPRATICA_OCR_SMOKE_REPORT"]=str(report)
        proc=subprocess.run([str(EXE),"--ocr-smoke"],env=env,cwd=ROOT,
                            capture_output=True,text=True,timeout=120,check=False)
        result=report.read_text(encoding="utf-8") if report.exists() else "NO_OCR_REPORT"
        if proc.returncode or result!="OCR_READY":
            raise SystemExit(f"Packaged OCR failed ({proc.returncode}): {result}\n"
                             +proc.stderr[-3500:]+proc.stdout[-1000:])
        print("PASS: bundled offline OCR recognized synthetic image.")
if __name__=="__main__":
    main()
