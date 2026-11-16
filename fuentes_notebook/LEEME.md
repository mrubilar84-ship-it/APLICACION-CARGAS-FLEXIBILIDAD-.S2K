# Fuentes del notebook `soportes_planilla.ipynb`

Esta carpeta contiene el generador que escribe el notebook del repositorio. El notebook es el artefacto que se ejecuta; estas fuentes permiten reconstruirlo y modificarlo con trazabilidad.

## Contenido

| archivo | función |
|---|---|
| `build_soportes_planilla3.py` | Escribe el notebook. Lee las fuentes de esta carpeta y el catálogo de `datos/`. |
| `celda6_plantilla.py` … `celda11_memoria.py`, `celda9b_deformada.py` | Celdas de código del notebook (plantilla, validación, dibujo, análisis, diseño, memoria). |
| `analisis_opensees.py`, `diseno_asd.py`, `diseno_ntc.py`, `memoria_asd.py`, `parametros.py`, `orientacion_gerdau.py`, `perfiles_gerdau_nb.py` (el notebook lo escribe como `perfiles_gerdau.py`), `dibujo_directo.py`, `vista3d_plotly.py` | Módulos que el notebook escribe con `%%writefile`. |
| `datos/hss_atc_catalogo.json` | HSS del catálogo ATC (116 secciones), generado por `datos/extraer_hss_atc.py` a partir del PDF. Ver `CAMBIOS_HSS.md`. |
| `datos/extraer_hss_atc.py` | Extrae las HSS del PDF del catálogo ATC (páginas 08 a 10) y verifica su SHA-256. |
| `generar_plantilla.py` | Regenera `plantilla_soportes.xlsx` desde las fuentes de esta carpeta (base, LISTAS, NORMA). |
| `datos/perfiles_gerdau_mexico_rev04.json` | Catálogo Gerdau rev04 (247 perfiles), SHA-256 `c5fdf1b1b09a9a7e98bfcdc92504a2b258bfc54d9571d1548eda3595ac0b3754`. Fuente de la base de perfiles del notebook. |

## Reconstruir el notebook

Desde esta carpeta, con Python 3:

```bash
python3 build_soportes_planilla3.py ../soportes_planilla.ipynb ../plantilla_soportes.xlsx
```

El segundo argumento es la plantilla que el notebook incrusta. Para regenerar la plantilla desde las fuentes: `python3 generar_plantilla.py ../plantilla_soportes.xlsx` (requiere LibreOffice). Con la plantilla de la raíz del repositorio el resultado es el notebook versionado.

## Diseño de HSS

Las HSS del catálogo ATC se diseñan con AISC 360-22 (E3/E7, F7, G2, H1) y la NTC (esbeltez local, Tabla 12.1.2).
Los detalles, la corrección de E7-2 y las limitaciones (torsión sin verificar, nota [c], A500 por confirmar) están en `CAMBIOS_HSS.md`.

## Advertencias

- Las rutas de trabajo de la sesión original ya no se usan: el catálogo se lee de `datos/`.
- Los 30 valores completados desde el manual están en `CORRECCIONES_MANUAL` de `build_soportes_planilla3.py`. Se verificaron contra la imagen de las páginas impresas 26 y 27 del manual (ver `auditoria_rev01/ADENDA_01.md`).
- Si cambia una celda o un módulo, vuelva a reconstruir el notebook y revise el diff con `git diff`.

## Perfiles macizos eliminados

Los perfiles CS (cuadrado solido), OS (redondo solido) y SOL (solera) se eliminan de la base del notebook al construirla (`FAMILIAS_ELIMINADAS` en `build_soportes_planilla3.py`) y no se diseñan. El catalogo `datos/perfiles_gerdau_mexico_rev04.json` se conserva completo, sin modificar, para trazabilidad. La base del notebook queda con 164 perfiles (IR 110, CE 7, LI 47). La hoja LISTAS de la plantilla sale de esa base, por lo que tampoco contiene perfiles macizos.
