# Entorno de ejecucion usado para generar las salidas

- Python: 3.13.18
- Sistema: Linux 6.18.44-fc-v445 x86_64
- Ejecutor: ejecutor/ejecutar_nb.py (ejecuta las celdas de codigo en orden; NO es Kaggle)
- Kaggle: NO probado en esta revision. Sin afirmar compatibilidad verificada.

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

## Instalación

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r entorno/requirements.txt
```

`requirements.txt` fija las versiones usadas. `pip_freeze_completo.txt` lista todos los paquetes del entorno de prueba.

## Kaggle

No probado en esta revisión. No se afirma compatibilidad con Kaggle ni el resultado de reiniciar y ejecutar desde cero allí.
