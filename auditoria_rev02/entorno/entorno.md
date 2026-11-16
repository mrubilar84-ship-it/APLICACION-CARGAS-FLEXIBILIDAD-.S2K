# Entorno de ejecucion (revision 02)

Ejecuciones de esta revision (`ejemplo/`, `caso_sismo/`, `pruebas/`, `excel_libreoffice/`): Linux 6.18.44-fc-v470; Python 3.13.18; LibreOffice 24.2.7.2 420(Build:2).
- Ejecutor: `ejecutor/ejecutar_nb.py` (ejecuta las celdas de codigo en orden; NO es Kaggle).
- Kaggle: NO probado en esta revision. No se afirma compatibilidad.
- Excel de escritorio: NO probado. Las comprobaciones de Excel se hicieron con LibreOffice 24.2.7.2.

## Paquetes (pip freeze, filtrado)

```text
ipython==9.18.1
matplotlib==3.11.2
numpy==2.5.3
openpyxl==3.1.5
openseespy==3.8.0.0
pandas==3.0.5
pillow==12.3.0
plotly==7.1.0
xlsxwriter==3.2.9
```

`requirements.txt` fija las versiones usadas (openseespy 3.8.0.0 como en el notebook). `pip_freeze_completo.txt` lista todo el entorno.

## Instalacion

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r entorno/requirements.txt
```
