# Respuesta a la auditoria de soportes: revision 02

**Respuesta a:** `Solicitud_Antecedentes_Auditoria_Soportes_Rev00.md` (13 de noviembre de 2026), y a la revision 01 (`auditoria_rev01/RESPUESTA_AUDITORIA.md` y su `ADENDA_01.md`, que no se modifican).
**Version de esta respuesta:** `auditoria_rev02/`, fecha 16 de noviembre de 2026.
**Rama:** `claude/eloquent-turing-cwpcd8`. El commit de esta revision esta en `IDENTIFICACION.txt`.

## 0. Resumen

- **Hallazgos H-01 a H-04: sin cambio de estado.** Siguen corregidos con las mismas pruebas (ver tabla). Las pruebas de rev01 se actualizaron en un dato de entrada (eje fuerte), no en sus comprobaciones.
- **Se cerraron cinco pendientes de la revision 01:** A2 (maximo en el tramo en forma cerrada), A3 y R-09 (aviso de resultado desactualizado, verificado en LibreOffice), A4 (openseespy fijado), A10 (paginas del catalogo en la base) y U10 (designacion `IR 6 x 8.5`).
- **Se agrego R-08 nuevo:** 50 comprobaciones independientes del solver (`pruebas/r08/`), 50 OK y 0 FALLA. Cubren equilibrio, voladizos, rotulas, mecanismos, modelo girado y barra inclinada. **No cubren** lo que sigue en la tabla.
- **Cambio de alcance:** los perfiles macizos (CS, OS y SOL) salen de la base, del diseno y de la plantilla, por decision del usuario. El catalogo fuente se conserva completo.
- **Los resultados entregados no cambian** en ningun valor numerico, en los dos casos (`comparacion/comparacion_rev01_rev02.md`). Cambian dos textos de RESUMEN y cuatro lineas de memoria.
- **Lo que sigue abierto:** R-04, R-05, R-06 y parte de R-02, R-03, R-07 y R-08 dependen de datos o decisiones del ingeniero (`pendientes_usuario.md`). Kaggle y Excel de escritorio no se probaron.

## 1. Contenido del paquete

| carpeta o archivo | contenido |
|---|---|
| `RESPUESTA_AUDITORIA_REV02.md` | este documento |
| `CAMBIOS_REV02.md` | cambios respecto de rev01: commits, archivos, efecto en resultados, pruebas modificadas |
| `pendientes_usuario.md` | decisiones y datos pendientes, con el estado de cada uno |
| `valores_esperados.md` | valores de reacciones, desplazamientos, esfuerzos, FU, flechas y distorsiones (R-03) |
| `codigo/` | modulos y celdas extraidos del notebook, mapa de codigo, indice de celdas y generador (`codigo/generador/`) |
| `pruebas/` | pruebas de rev01 (con el eje fuerte explicito), control contra rev00, R-08 (50 pruebas), aviso de PERFIL_GRUPO, comprobacion manual |
| `ejemplo/`, `caso_sismo/` | entrada, salidas, memoria y log de cada caso (ejecucion de rev02) |
| `plantilla/` | `plantilla_soportes.xlsx` (mismo archivo que la raiz del repositorio) |
| `excel_libreoffice/` | recalculo en LibreOffice, reporte y cambio de perfil |
| `comparacion/` | comparacion celda a celda y de memoria rev01 -> rev02; diff de codigo |
| `ejecutor/` | `ejecutar_nb.py` y su instruccion (sin cambios desde rev01) |
| `entorno/` | versiones de Python, sistema y paquetes; `requirements.txt`; `pip freeze` completo |
| `base_gerdau/` | los 30 valores completados desde el manual, con pagina y estado |
| `referencias/` | extractos de texto de las normas (sin cambios desde rev00) |
| `manifiesto_sha256.txt` | SHA-256 de los archivos de este paquete, del notebook y de la plantilla |

## 2. Respuesta por ID

Estados: **entregado**, **parcial**, **pendiente**, **requiere decision**. Las rutas son relativas a `auditoria_rev02/`. El cambio respecto de rev01 esta en la ultima columna.

| ID | estado rev02 | respuesta | evidencia | pendiente y responsable | cambio respecto de rev01 |
|---|---|---|---|---|---|
| H-01 | entregado | Maximo de momento en el tramo en `momentos_maximos_viga` (forma cerrada, `codigo/modulos/analisis_opensees.py`). `_demanda_fila` toma el maximo de extremos y de tramo. | `pruebas/test_rev01_salida.txt`: 11 OK, codigo 0. Prueba inicial del auditor: `pruebas/prueba_inicial_salida.txt`, 9000 kgf·cm (antes 0). | Prueba de marco 3D completo (R-08). | Sin cambio de estado. El muestreo de 401 puntos se reemplazo por la forma cerrada (A2 cerrado). |
| H-02 | entregado | Flecha medida respecto de la cuerda, con el termino de Hermite de traslacion de extremos. | `pruebas/test_rev01_salida.txt`: 6 comprobaciones de Hermite OK. Control contra rev00: `pruebas/control_rev00_test_rev01_salida.txt`, 4 FALLA. | Movimientos combinados de extremos en 3D (R-08). | Sin cambio de estado. |
| H-03 | parcial | Caso sismo con su entrada, log, memoria, Excel y valores esperados. **Las cargas E son de prueba** (+1000 kgf en los nodos 3 y 6, sin origen normativo). | `caso_sismo/`; equilibrio horizontal independiente en `valores_esperados.md`, B. | Cargas sismicas reales y su origen (U4). | Sin cambio de estado. Los resultados no cambian. |
| H-04 | entregado | Prueba de flecha con signo tomado de la teoria, tolerancia y codigo de salida. | `pruebas/test_flecha_rev01_salida.txt`: 4 OK, codigo 0. | Ninguno. | Sin cambio. |
| H-05 | entregado | Paquete completo: notebook, ejecutor, dependencias, manifiesto con SHA-256 e identificacion del commit. | `manifiesto_sha256.txt`; `IDENTIFICACION.txt`. | Ninguno. | Nuevo paquete rev02. |
| R-01 | entregado | Notebook regenerado desde `fuentes_notebook/`. Modulos extraidos de las celdas `%%writefile`, sin diferencias. Indice de celdas y mapa de codigo. | `codigo/INDICE_DE_CELDAS.md`, `codigo/mapa_de_codigo.md`. | Ninguno. | Actualizado. |
| R-02 | parcial | `openseespy` fijado en 3.8.0.0 (A4 cerrado). Versiones de Python, sistema, LibreOffice y paquetes en `entorno/`. | `entorno/entorno.md`, `entorno/requirements.txt`, `entorno/pip_freeze_completo.txt`. | Kaggle no se probo: desde cero, con y sin Internet (U13). | Actualizado. |
| R-03 | parcial | Valores esperados actualizados. Comprobacion manual independiente: FU de la barra 1 (0,97723, por ductilidad b/t, reproducido con AISC 360-22 y NTC) y flecha de la barra 15 (0,0625 mm frente a 0,06 mm de la memoria). | `valores_esperados.md`; `pruebas/comprobacion_manual/salida.txt`. | Comprobacion a mano de la distorsion sismica (A5 parcial). Tolerancias: validacion del usuario. | Parcial en rev01; ahora con comprobacion manual de FU y flecha. |
| R-04 | requiere decision | Requisitos fijados por el usuario: analisis estatico, AISC 360-22 ASD con criterios NTC, demandas y normas solo desde la planilla, viento excluido. Los perfiles macizos (CS, OS, SOL) quedan fuera del alcance. | `pendientes_usuario.md`. | Ubicacion y norma contractual, estados de carga, limite de desplazamiento, decisiones D1 a D20 (U1, U5 a U7, U15). Responsable: usuario. | Cambio de alcance: macizos fuera. |
| R-05 | parcial | Extractos de texto de las normas (`referencias/`), sin cambio. La revision 01 corrigio la afirmacion sobre la norma sismica (ver `ADENDA_01.md`). | `referencias/referencias_normativas.md`. | Edicion y estatus de cada norma (U2); PDF o enlace oficial; recortes de pagina para ecuaciones dudosas (A7). Responsable: usuario y agente. | Sin cambio en `referencias/`. |
| R-06 | pendiente (datos) | Origen de E sin cambio: carga de prueba. | `caso_sismo/`; `valores_esperados.md`, B. | Origen real de las fuerzas y datos del sitio (U4). Ejemplo numerico independiente desde cargas hasta distorsion (A8). Responsable: usuario y agente. | Sin cambio. |
| R-07 | parcial | Catalogo fuente en el repositorio (`fuentes_notebook/datos/perfiles_gerdau_mexico_rev04.json`, SHA-256 `c5fdf1b1…`). Los 30 valores completados se verificaron contra la imagen de las paginas impresas 26 (CE) y 27 (IR), PDF pagina 14. La base registra pagina y fuente de cada valor (A10 cerrado). Designacion `IR 6 x 8.5` en pulgadas y lb/ft (U10 cerrado). | `base_gerdau/valores_completados_desde_manual.md`; `ADENDA_01.md`, seccion 1. | Confirmar que rev04 es la version vigente (U8) y la edicion del manual (U9). Documentar ejes y radios de LI, CE e IR contra el catalogo (A6). Responsable: usuario y agente. | Avanzado. |
| R-08 | parcial | **Pruebas nuevas:** 50 comprobaciones independientes (`pruebas/r08/`): equilibrio de fuerzas y momentos en los dos casos, voladizo 3D en ambos ejes, rotulas, mecanismos, modelo girado 30 grados y barra inclinada. Resultado: 50 OK, 0 FALLA. Ademas: pruebas de rev01 (11 y 4 OK), prueba inicial del auditor. | `pruebas/r08/salida_r08.txt`; `pruebas/*_salida.txt`. | Pendiente: puntos 1, 5, 6 y 7 del orden del auditor (ver nota abajo); rotulas en nodos compartidos de un marco 3D; entradas faltantes o no finitas (A9). Responsable: agente. | Nuevo: R-08 con 50 pruebas. |
| R-09 | parcial | **Aviso de resultado desactualizado** implementado: las columnas PERFIL ANALIZADO y EJECUCION de `PERFIL_GRUPO` marcan "vigente" o "DESACTUALIZADO" (A3 cerrado para LibreOffice). Cambio de perfil de COLUMNA: 12 celdas de BARRAS, 6 de PERFIL_GRUPO y 84 de FU_BARRAS cambian; ningun valor de OpenSees cambia. Entradas sin perfil: "SIN PERFIL". Seleccion de archivo: error si hay mas de un `.xlsx` con "soportes". | `pruebas/aviso_perfil/salida_verificacion.txt` (4 de 4 OK); `excel_libreoffice/resultados_libreoffice.md`. | Excel de escritorio no se probo (U14). Proteccion de NORMA, validaciones y añadir filas: no probados. Responsable: usuario (Excel) y agente. | Avanzado. |

**Nota sobre R-08 y la lista del auditor** (orden del punto A1 de rev01): cubiertos el punto 2 (equilibrio de fuerzas y de momentos en los dos marcos, en todos los estados), el punto 3 (rotulas, mecanismos, modelo girado y barra inclinada) y el punto 4 (parcial: peso propio en un estado). Abiertos: el punto 1 (movimientos combinados de extremos en 3D), el punto 5 (IR, CE y LI en traccion, compresion, flexion y cambios de rama), el punto 6 (entradas faltantes o no finitas) y el punto 7 (propagacion de NO REVISADO).

## 3. Lo que no se afirma

- No se afirma que el programa sea correcto en general: las pruebas cubren los casos listados.
- No se afirma compatibilidad con Kaggle ni con Excel de escritorio.
- No se afirma cumplimiento normativo: los criterios de diseno siguen abiertos (D1 a D20 y R-04).
- El caso sismo no es una verificacion sismica de la estructura: sus cargas son de prueba.
- Las comprobaciones manuales de FU y flecha leen como entrada las demandas y los desplazamientos de los libros. Verifican capacidades, formulas y postproceso, no el ensamblado del modelo.
