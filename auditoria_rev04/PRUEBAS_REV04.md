# Pruebas ejecutadas con el código rev04

Las pruebas `test_rev01.py`, `test_flecha_rev01.py` y `r08_pruebas.py` vienen de `auditoria_rev02/pruebas/` (sin cambio). Se ejecutaron contra los módulos de `codigo/fuentes_notebook/` (variable `DIBUJO`). La prueba R-08 necesita carpetas de ejemplo con la estructura de la rev02; se ejecutó sobre un árbol de trabajo que replica esa estructura. El control 0.1 de R-08 compara copias de tres módulos del ejemplo con el repositorio: se usaron las copias de la rev04.

| prueba | cómo se ejecuta | código | resultado | archivo de salida | nota |
|---|---|---|---|---|---|
| test_rev01 | `DIBUJO=<codigo/fuentes_notebook> python3 auditoria_rev02/pruebas/test_rev01.py` | 0 | 11/11 OK | `pruebas/test_rev01_salida.txt` | incluye H-01 y 6 comprobaciones de Hermite |
| test_flecha_rev01 | igual, con `test_flecha_rev01.py` | 0 | 4/4 OK | `pruebas/test_flecha_rev01_salida.txt` | H-04 |
| R-08 (50 pruebas) | `PYTHONPATH=<codigo/fuentes_notebook> CARPETA_TRABAJO=<árbol> python3 auditoria_rev02/pruebas/r08/r08_pruebas.py` | 0 | 50/50 OK | `pruebas/r08_salida.txt` | equilibrio, voladizos, rótulas, mecanismos, modelo girado, barra inclinada |
| placas base (independiente) | `DIBUJO=<codigo/fuentes_notebook> python3 placas_base/prueba_independiente.py` | 0 | 14/14 OK | `placas_base/salida.txt` | fórmulas escritas a mano; perfil sintético; no es verificación de norma (H-09) |
| aviso de perfil (LibreOffice) | `python3 verificacion_posterior/aviso_perfil/verificar_aviso_perfil.py <planilla_con_diseno.xlsx> <carpeta>` | 0 | 4/4 OK | `pruebas/aviso_perfil_salida.txt` | R-09; usa la planilla del ejemplo rev04 |
| comprobación manual | `python3 verificacion_posterior/comprobacion_manual/comprobacion_manual.py` | 0 | ejecuta, pero **calcula NTC** | `pruebas/comprobacion_manual_salida_ACTUAL.txt` | **obsoleta** (H-07) |
| test_hss | `python3 verificacion_posterior/hss/test_hss.py` | 1 | **falla**: AttributeError `_ductilidad` | `pruebas/test_hss_salida.txt` | H-08 |
| notebook completo (modo plantilla) | `python3 ejecutor/ejecutar_nb.py <carpeta>/soportes_planilla.ipynb` | 0 | 8 celdas ejecutables OK, sin ERROR | `ejemplo/ejecucion.log` | ejecuta la plantilla de ejemplo |

Las pruebas que no pasan o están obsoletas se entregan como están, para que el auditor las vea. Las correcciones irán en la rev05, con descripción del cambio.

Los hashes de cada archivo de salida están en `manifiesto_sha256.txt`.
