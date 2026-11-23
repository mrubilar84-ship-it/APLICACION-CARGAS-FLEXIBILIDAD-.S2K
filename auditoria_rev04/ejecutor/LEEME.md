# Ejecutor del notebook (R-01)

`ejecutar_nb.py` ejecuta, celda por celda y en orden, el notebook `soportes_planilla.ipynb`. Escribe los módulos de las celdas `%%writefile` en la carpeta del notebook.

**Uso:**

1. Copiar el notebook a una carpeta vacía (los módulos y las salidas se escriben ahí):
   `mkdir ~/prueba_soportes && cp codigo/soportes_planilla.ipynb ~/prueba_soportes/`
2. Ejecutar: `python3 ejecutor/ejecutar_nb.py ~/prueba_soportes/soportes_planilla.ipynb`
3. El log muestra una línea por celda: `[celda N] OK` o `[celda N] ERROR`. Sale con código 0 si ninguna celda falló.

**Notas:**

- Fuera de Kaggle, la celda 7 usa la plantilla de ejemplo (busca planillas en `/kaggle/input`). En la prueba de placas base se fijó la ruta de la planilla dentro del notebook; ver `pruebas/`.
- Requiere las versiones de `ENTORNO_REV03.md`.
- Este ejecutor es la copia usada para `ejemplo/ejecucion.log`.
