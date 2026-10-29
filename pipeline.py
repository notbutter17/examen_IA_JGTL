"""Ejecuta la integración, modelado, perfiles, SHAP y verificaciones."""
import subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent
for script in ['datos.py','analisis.py','complementos.py','verificar.py']:
    subprocess.run([sys.executable,str(R/'src'/script)],check=True,cwd=R)
print('Pipeline finalizado. Revisar resultados/ e informe/.')
