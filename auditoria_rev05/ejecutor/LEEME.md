# Ejecutor del notebook (R04-19)

`ejecutar_nb.py` ejecuta, celda por celda y en orden, el notebook `soportes_planilla.ipynb`. Escribe los módulos de las celdas `%%writefile` en la carpeta del notebook.

**Uso:**

1. Copiar el notebook a una carpeta vacía: `mkdir ~/prueba_soportes && cp codigo/soportes_planilla.ipynb ~/prueba_soportes/`
2. Ejecutar: `python3 ejecutor/ejecutar_nb.py ~/prueba_soportes/soportes_planilla.ipynb`
3. El log muestra una línea por celda (`[celda N] OK`, `[celda N] ERROR`). El último renglón dice `EJECUCION COMPLETA` (código 0) o `EJECUCION INCOMPLETA en la celda N` (código 1).

**Notas:**

- Si el código sale con 1, no use las salidas de esa carpeta.
- Fuera de Kaggle, la celda 7 usa la plantilla de ejemplo (busca planillas en `/kaggle/input`).
- Requiere las versiones de `ENTORNO_REV05.md`.
