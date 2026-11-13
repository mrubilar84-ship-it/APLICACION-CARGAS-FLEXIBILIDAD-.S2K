# Ejecutor local del notebook

`ejecutar_nb.py` ejecuta, en orden, las celdas de código de un notebook y escribe los módulos de las celdas `%%writefile`. Registra `[celda N] OK` o el error de cada celda. **No es Kaggle**: no instala dependencias ni cambia rutas de Kaggle. Se usó para generar `ejemplo/ejecucion.log` y `caso_sismo/ejecucion.log`.

## Uso

1. Cree una carpeta vacía y copie ahí:
   - `soportes_planilla.ipynb` (raíz del repositorio), y
   - la planilla que va a calcular, con el nombre `plantilla_soportes.xlsx`. El caso gravitacional usa `plantilla/plantilla_soportes.xlsx`; el caso sísmico usa `caso_sismo/planilla_sismo_ENTRADA_DE_PRUEBA.xlsx` renombrado a `plantilla_soportes.xlsx`.
2. Desde cualquier carpeta, ejecute:

```bash
python3 /ruta/a/ejecutor/ejecutar_nb.py /ruta/a/soportes_planilla.ipynb > ejecucion.log 2>&1
```

El ejecutor cambia a la carpeta del notebook. Por eso la planilla y las salidas quedan junto al notebook.

3. Revise `ejecucion.log`. La última celda de código debe aparecer como `[celda 29] OK`, y el log no debe contener `ERROR` ni `SystemExit`.

## Salidas

En la carpeta del notebook: `memoria_calculo.html`, `resultados_soportes.xlsx`, `diseno_asd.xlsx`, `planilla_con_diseno.xlsx`, `planilla_con_vista.xlsx`, y los módulos `.py` escritos por las celdas `%%writefile`.

## Requisitos

- Probado con Python 3.13.18 en Linux x86_64.
- Paquetes: `entorno/requirements.txt` (`pip install -r entorno/requirements.txt`). openseespy 3.8.0.0.
- LibreOffice es opcional. Si está instalado, la celda 12 recalcula el libro. Se probó con LibreOffice 24.2.7.2.
- La celda 20 instala `openseespy` con pip si no puede importarlo. Con la versión fijada en `requirements.txt` no hace falta.
