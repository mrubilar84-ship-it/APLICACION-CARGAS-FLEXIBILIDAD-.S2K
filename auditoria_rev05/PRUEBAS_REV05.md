# Pruebas de la revisión 05

Todas se ejecutaron con el código de `codigo/fuentes_notebook/` (variable `DIBUJO` o `PYTHONPATH`). Las pruebas `test_rev01`, `test_flecha_rev01` y `r08` vienen de `auditoria_rev02/pruebas/` sin cambio. Las pruebas `prueba_rev05`, `prueba_ejecutor` y `prueba_independiente` son propias de esta revisión.

| prueba | cómo se ejecuta | código | resultado | archivo |
|---|---|---|---|---|
| test_rev01 | `DIBUJO=<modulos> python3 auditoria_rev02/pruebas/test_rev01.py` | 0 | 11/11 OK | `pruebas/test_rev01_salida.txt` |
| test_flecha_rev01 | igual, con `test_flecha_rev01.py` | 0 | 4/4 OK | `pruebas/test_flecha_rev01_salida.txt` |
| R-08 (50 pruebas) | `PYTHONPATH=<modulos> CARPETA_TRABAJO=<árbol de la rev02> python3 auditoria_rev02/pruebas/r08/r08_pruebas.py` | 0 | 50/50 OK | `pruebas/r08_salida.txt` |
| placas base independiente | `DIBUJO=<modulos> python3 placas_base/prueba_independiente.py` | 0 | 14/14 OK | `placas_base/salida.txt` |
| regresión rev05 | `DIBUJO=<modulos> PLANTILLA=plantilla/plantilla_soportes.xlsx python3 pruebas_regresion/prueba_rev05.py` | 0 | 17/17 OK | `pruebas_regresion/salida.txt` |
| ejecutor | `python3 pruebas_regresion/prueba_ejecutor.py` | 0 | 3/3 OK | `pruebas_regresion/salida_ejecutor.txt` |
| aviso de perfil (LibreOffice) | `python3 verificacion_posterior/aviso_perfil/verificar_aviso_perfil.py <planilla_con_diseno.xlsx> <carpeta>` | 0 | 4/4 OK | `pruebas/aviso_perfil_salida.txt` |
| Kz de extremo a extremo (R04-18) | ver abajo | 0 | Kz = 0.5 conservado | (no incluido en el paquete) |
| test_hss | `PYTHONPATH=<modulos> python3 verificacion_posterior/hss/test_hss.py` | 1 | **falla**: AttributeError `_ductilidad` | `pruebas/test_hss_salida.txt` |
| comprobación manual | `python3 verificacion_posterior/comprobacion_manual/comprobacion_manual.py` | 0 | ejecuta; calcula **NTC** (obsoleta) | `pruebas/comprobacion_manual_salida_ACTUAL.txt` |
| notebook completo (plantilla) | `python3 ejecutor/ejecutar_nb.py <carpeta>/soportes_planilla.ipynb` | 0 | EJECUCION COMPLETA | `ejemplo/ejecucion.log` |

## Prueba Kz (R04-18)

1. Copiar `plantilla/plantilla_soportes.xlsx` y poner `KZ_TORSION = 0.5` en la hoja PARAMETROS (columna C).
2. Construir el notebook con `build_soportes_planilla3.py` y cambiar en la celda 7 `RUTA_PLANILLA_LEIDA = buscar_planilla()` por la ruta de la copia.
3. Ejecutar con `ejecutor/ejecutar_nb.py` en una carpeta vacía.
4. Leer la hoja PARAMETROS de `planilla_con_diseno.xlsx`: el valor de KZ_TORSION debe ser 0.5. Resultado: **0.5**.

## Nota sobre la reproducción del auditor

El script del informe del auditor (`pruebas_auditor.py`) no se ejecutó en esta revisión porque el permiso de ejecución fue denegado. Sus valores T01–T23 no están reproducidos.
