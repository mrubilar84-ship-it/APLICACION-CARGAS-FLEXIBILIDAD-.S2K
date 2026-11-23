# Respuesta a la auditoría de soportes: revisión 04

**Respuesta a:** `Solicitud_Antecedentes_Auditoria_Soportes_Rev00.md` (13 de noviembre de 2026), y a las revisiones 02 y 03.
**Versión de esta respuesta:** `auditoria_rev04/`, fecha 23 de noviembre de 2026.
**Rama:** `claude/eloquent-turing-cwpcd8`. Commit de código y paquete: ver `IDENTIFICACION.txt`.
**Carpetas anteriores:** `auditoria/`, `auditoria_rev01/`, `auditoria_rev02/` y `auditoria_rev03/` no se modifican.

## 0. Respuesta corta

**¿Está correcto el diseño?** Todavía no puede afirmarse. La revisión 04 corrige el criterio de esbeltez local de las vigas (H-06), pero quedan decisiones y verificaciones pendientes.

Qué cambió respecto de la revisión 03:

- **H-06 corregido:** cada miembro se revisa según su uso principal. Las vigas usan los límites de flexión (AISC Tabla B4.1b); los miembros comprimidos (COLUMNA, ARRIOSTRE, DIAGONAL) usan los de compresión (Tabla B4.1a). En el ejemplo, la esbeltez local de las 7 vigas IR 12×16 vuelve a 0.38.
- **Consecuencia nueva, pendiente de tu confirmación (D2):** 4 de esas vigas quedan NO CUMPLE por KL/r = 250 > 200. Es la regla de KL/r que decidiste para cualquier barra con compresión. Antes, ese resultado estaba oculto por la esbeltez local.

Verificado con el código de la revisión 04:

- Solver y análisis: `test_rev01` 11/11, `test_flecha` 4/4, R-08 50/50. El análisis del ejemplo es idéntico a la rev02 y a la rev03.
- Placas base: 14/14 comprobaciones contra fórmulas escritas a mano.
- Aviso de resultado desactualizado (LibreOffice): 4/4.

Pendiente o con hallazgo abierto: H-06 (solo la parte de KL/r en vigas), H-07 (valores de la rev02 obsoletos y comprobación manual con NTC), H-08 (`test_hss.py` falla), H-09 (placas base: normas parcialmente verificadas), H-03 (cargas sísmicas de prueba).

## 1. Contenido del paquete

| carpeta o archivo | contenido |
|---|---|
| `RESPUESTA_AUDITORIA_REV04.md` | este documento |
| `CAMBIOS_REV04.md` | cambios de la revisión 04 y su efecto |
| `VALORES_ESPERADOS_REV04.md` | valores del caso de ejemplo y su comparación |
| `comparacion/` | rev02 → rev04 y rev03 → rev04, celda por celda de análisis y FU |
| `PRUEBAS_REV04.md` y `pruebas/` | pruebas ejecutadas con el código rev04 |
| `placas_base/` | prueba independiente de placas base |
| `REFERENCIAS_REV04.md` | estado de cada fuente normativa, con SHA-256 de los documentos recibidos |
| `PENDIENTES_REV04.md` | decisiones y datos pendientes |
| `ENTORNO_REV04.md` | versiones de Python, LibreOffice y paquetes |
| `ejecutor/` | `ejecutar_nb.py` y su instrucción |
| `ejemplo/` | salidas del caso gravitacional de ejemplo con el código rev04 |
| `plantilla/` | `plantilla_soportes.xlsx` (sin cambio desde la rev03) |
| `codigo/` | `fuentes_notebook/` y `soportes_planilla.ipynb` con el código rev04 |
| `*_REV03_historico.md` | documentos de la revisión 03, sin cambio, para trazabilidad |
| `manifiesto_sha256.txt` | SHA-256 de todos los archivos del paquete |
| `IDENTIFICACION.txt` | commit de código y paquete, escrito después del commit |

## 2. Respuesta a H-01 a H-09 y R-01 a R-09

| ID | Estado | Respuesta concreta | Archivo, función, celda o página | Evidencia de prueba | Pendiente y responsable |
|---|---|---|---|---|---|
| H-01 | entregado (revalidado) | Máximo de momento en el tramo en forma cerrada; entra en `_demanda_fila`. | `codigo/fuentes_notebook/analisis_opensees.py`, `momentos_maximos_viga`; `diseno_asd.py`, `_demanda_fila` | `pruebas/test_rev01_salida.txt`: 11/11 OK, código 0 | Ninguno |
| H-02 | entregado (revalidado) | Flecha respecto de la cuerda, con el término de Hermite. | `analisis_opensees.py`, `_deflexion_viga` | `pruebas/test_flecha_rev01_salida.txt`: 4/4 OK; 6 comprobaciones de Hermite en `test_rev01` | Ninguno |
| H-03 | pendiente (datos) | El notebook no calcula sismo. El caso sísmico de la rev02 sigue con cargas de prueba (+1000 kgf en los nodos 3 y 6). La plantilla de ejemplo tiene solo D, L y W. | `celda7_validar.py`, `validar_cargas`; `auditoria_rev02/caso_sismo/` (sin cambio) | — | Origen de las cargas sísmicas: usuario (R-06, U4) |
| H-04 | entregado (revalidado) | Prueba de flecha con el signo de la teoría, tolerancia y código de salida. | `auditoria_rev02/pruebas/test_flecha_rev01.py`, ejecutado con el código rev04 | `pruebas/test_flecha_rev01_salida.txt`: 4/4 OK | Ninguno |
| H-05 | entregado | Paquete con notebook, ejecutor, entorno, manifiesto con SHA-256 e identificación del commit. | `auditoria_rev04/` | `sha256sum -c` sobre el manifiesto | Ninguno |
| H-06 | entregado en rev04; **D2 abierta** | Esbeltez local: vigas con límites de flexión (B4.1b); miembros comprimidos con límites de compresión (B4.1a). Queda abierto solo el efecto de KL/r en vigas con compresión (sección 3). | `diseno_asd.py`, `_chequear`: `esbeltez_local(..., compresion = compr and grupo != 'VIGA')`; `memoria_asd.py`, `_ref_local` y `_nota_normativa` | `ejemplo/`, `comparacion/comparacion_rev03_rev04.md`: solo cambian las 7 vigas | D2: usuario (sección 3) |
| H-07 | entregado (cambio documentado); prueba pendiente | Se eliminó la ductilidad NTC (`eb4cb1b`). El FU máximo cambia en las 26 barras del ejemplo (diferencia máxima 0.63). Los valores de la rev02 quedan obsoletos. | `comparacion/comparacion_rev02_rev04.md` | `pruebas/comprobacion_manual_salida_ACTUAL.txt` (obsoleta) | Actualizar la comprobación manual a AISC/IMCA: agente, rev05 |
| H-08 | pendiente | `test_hss.py` llama a `DA._ductilidad`, que ya no existe. Falla con AttributeError. | `verificacion_posterior/hss/test_hss.py`, línea 75 | `pruebas/test_hss_salida.txt`, código 1 | Actualizar o retirar la prueba: agente, rev05 |
| H-09 | parcial | Placas base implementadas y verificadas con fórmulas independientes (14/14). Las normas están parcialmente verificadas (sección 4). | `placas_base.py`; `memoria_asd.py`, `_seccion_placas` | `placas_base/salida.txt`: 14/14 OK, código 0 | Verificar en imagen DG1 §3.1.2, §3.2.1 y la pág. 19 (pdf 26), y ACI 318-02 D.5.2: usuario (PDF) |
| R-01 | entregado | Notebook completo generado desde `fuentes_notebook/` con la plantilla incrustada; módulos en `codigo/`; ejecutor en `ejecutor/`. | `codigo/soportes_planilla.ipynb` (32 celdas) | `ejemplo/ejecucion.log`: 8 celdas ejecutables OK, sin ERROR | Kaggle (R-02, U13) |
| R-02 | parcial | Versiones en `ENTORNO_REV04.md`. No hay `pip freeze` completo. | `ENTORNO_REV04.md` | Ejecución local (Linux x86_64) | Kaggle desde cero (U13): usuario; `pip freeze` completo: agente |
| R-03 | parcial | Entrada del ejemplo: `plantilla/plantilla_soportes.xlsx` (SHA-256 en el manifiesto). Análisis idéntico a rev02 y rev03. Diseño cambia solo en las 7 vigas (H-06) y en el FU máximo (H-07). El caso sísmico no se actualizó. | `ejemplo/`, `comparacion/` | Diferencia 0 en REACCIONES, NODOS, BARRAS y MAXIMOS_BARRAS | Caso sísmico con origen real: usuario (H-03) |
| R-04 | requiere decisión | Criterios con su fuente (sección 5). Se agrega la decisión de esbeltez local de vigas (confirmada) y D2. | Sección 5 | — | Usuario: D2, U1, U5, U6, U7 |
| R-05 | parcial | Fuentes, páginas verificadas y SHA-256 de cada documento recibido en `REFERENCIAS_REV04.md`. AISC 360-22: páginas 16.1-19, 16.1-21 y 16.1-23 leídas del texto del PDF (no en imagen). | `REFERENCIAS_REV04.md` | Hashes de los 10 archivos | DG1 (PDF), ACI 318-02 y edición de la NTC de sismo: usuario (U2) |
| R-06 | pendiente (datos) | Sin cambio: cargas E de prueba; el notebook no calcula sismo. | `REFERENCIAS_REV04.md`; `PENDIENTES_REV04.md` | — | Usuario (U4) |
| R-07 | parcial | Base Gerdau rev04 y los 30 valores completados: sin cambio. Desde la rev02: 116 HSS del catálogo ATC (`datos/hss_atc_catalogo.json`, extraídos por `datos/extraer_hss_atc.py`). Su verificación contra el PDF no se hizo. | `codigo/fuentes_notebook/datos/` | SHA-256 del JSON Gerdau en `REFERENCIAS_REV04.md` | Verificar los HSS contra el PDF: agente, rev05. Edición del manual: usuario (U9) |
| R-08 | parcial | Pruebas ejecutadas con el código rev04: `test_rev01` 11/11, `test_flecha` 4/4, R-08 50/50, placas base 14/14, aviso de perfil 4/4. Fallan `test_hss` (H-08) y la comprobación manual con NTC (H-07). Las prioridades 6 y 7 de la solicitud no están cubiertas. | `pruebas/`, `placas_base/`, `PRUEBAS_REV04.md` | Salidas en `pruebas/` | Prioridades 6 y 7, H-07 y H-08: agente, rev05 |
| R-09 | parcial | Aviso de resultado desactualizado: 4/4 con LibreOffice. `buscar_planilla()`: en `/kaggle/input`, si hay más de una planilla válida detiene con error (no elige al azar); si hay .xlsx que no son planillas, detiene; si no hay ninguno, usa la plantilla de ejemplo y lo avisa. | `codigo/fuentes_notebook/celda7_validar.py`, `buscar_planilla` (líneas 25 a 47); `pruebas/aviso_perfil_salida.txt` | 4/4 OK | Excel de escritorio (U14): usuario |

## 3. H-06: criterio aplicado y pendiente de D2

**Criterio aplicado (opción A, aprobada por el usuario).** Cada miembro se revisa según su uso principal:

- **VIGA:** esbeltez local con los límites de flexión (AISC 360-22, Tabla B4.1b: patín λr = 1.00√(E/Fy); alma λr = 5.70√(E/Fy)). Aunque tenga compresión en alguna combinación.
- **COLUMNA, ARRIOSTRE y DIAGONAL con compresión:** esbeltez local con los límites de compresión (Tabla B4.1a).

**Resultado en el ejemplo (barras de las vigas IR 12 × 16):**

| ID | FU esbeltez local rev03 | FU esbeltez local rev04 | FU KL/r rev04 | estado rev04 |
|---|---|---|---|---|
| 15, 16, 19, 20 | 1.451 | 0.379 | 1.250 (KL/r = 250) | NO CUMPLE |
| 22, 24, 26 | 1.451 | 0.379 | 1.000 (KL/r = 200) | CUMPLE |

**D2 (decisión pendiente).** La regla de KL/r ≤ 200 se aplica a cualquier barra con compresión en alguna combinación, como lo decidiste antes. Por eso las 4 vigas con KL/r = 250 siguen NO CUMPLE. Dos opciones:

- (a) Mantener la regla (el resultado actual). Coincide con tu instrucción anterior.
- (b) No aplicar KL/r a vigas, y revisar KL/r solo a columnas, arriostres y diagonales.

**Alma en flexión (AISC F4):** el código no reduce la resistencia de un alma de I que no sea compacta. Se verificó en el catálogo: ningún perfil IR o CE tiene h/tw mayor que λp (máximo h/tw = 59.6; λp entre 82.6 y 106.7 según el Fy). Por eso F4 no altera ningún resultado del catálogo actual. No se implementó; queda documentado para el caso de secciones futuras con almas esbeltas.

## 4. H-09: estado de las normas de placas base

| tema | fuente | estado |
|---|---|---|
| aplastamiento: P_p = mín[0.85 f′c A1 √(A2/A1); 1.7 f′c A1], Ω_c = 2.31 | IMCA cap. J, J8-1 y J8-2, pág. II-218 (pdf 312) | verificada en imagen |
| tracción en pernos: R_n = 0.7 F_u A_t, Ω = 2.00 | DG1 pág. 19 (pdf 26): 0.7 F_u verificada en imagen; A_t según §3.2.1 (texto del resumen) | **parcial**: en la misma página aparece "(0.75)(0.75) F_u A_b = 0.5625 F_u A_b". Se sigue el texto (0.7) por instrucción del usuario. Confirmar en el original. |
| cortante en pernos con roscas: R_n = 0.4 F_u A_b, φ = 0.75 | DG1 pág. 42 (pdf 49) | verificada en imagen |
| soldadura E70: 0.6 F_EXX, φ = 0.75 | DG1 pág. 42 (pdf 49) | verificada en imagen |
| espesor de placa (voladizo m, n, λn′), φ = 0.90, Ω = 1.67 | DG1 §3.1.2 | texto del resumen, **no verificado en imagen** |
| cono de concreto: N_b = k λ √f′c h_ef^1.5, k = 10 (SI), φ = 0.70 | ACI 318-02 Ap. D, §D.5.2, ec. D-7 | **no verificado**; φ = 0.70 aparece en DG1 págs. 19 y 42 |
| conversión a ASD: Ω = 1.5/φ | reproduce Ω_c = 2.31 (IMCA, φ = 0.65) y los Ω de DG1 | derivada |

**Limitaciones que la memoria marca como NO REVISADO:** excentricidad fuera del núcleo (se evalúa cada dirección por separado, no es biaxial exacta); pernos solo en la dirección N; cono con A_Nc = A_Nco; levantamiento sin verificar la flexión de la placa; soldadura sin transferencia de compresión por contacto.

**Datos de prueba.** La prueba de placas base usa datos inventados (placa 30 × 30 cm, dado 60 × 60 cm, 4 pernos Ø 3/4", perfil sintético H = 15 cm, B = 6 cm). No hay un caso real del proyecto validado.

## 5. R-04: base de diseño y criterios

| criterio | estado | fuente |
|---|---|---|
| resistencia con AISC 360-22 ASD | confirmado | instrucción del usuario |
| NTC-Acero y NTC de sismo no aplican al diseño | confirmado | instrucción del usuario |
| KL/r ≤ 200 como límite del proyecto (IMCA cap. E, nota II-89, "preferiblemente") | confirmado; referencia verificada en imagen | instrucción del usuario |
| KL/r y esbeltez local en compresión para cualquier barra con compresión en alguna combinación | confirmado (KL/r y compresión); aplicación a vigas: **D2** | instrucción del usuario |
| esbeltez local de vigas con límites de flexión | confirmado (opción A) | decisión del usuario |
| sismo entra como carga de la planilla; el notebook no lo calcula | confirmado | instrucción del usuario |
| viento excluido | pendiente de confirmar: limitación provisional o exclusión justificada (U7) | — |
| flecha L/360 (AISC 360-22, Comentario L2) | confirmado | instrucción del usuario |
| ángulos LI: análisis con Ix = Iy del catálogo; diseño con Iu e Iv | confirmado | instrucción del usuario |
| placas base: IMCA cap. J + DG1 + ACI 318-02, todos los datos de entrada | enfoque confirmado; valores pendientes (sección 4) | instrucción del usuario |
| jurisdicción (Zitácuaro) y si la autoridad acepta IMCA sin NTC | pendiente (U1) | — |
| estados de carga reales, límite de desplazamiento y viento | pendiente (U5, U6, U7) | — |
| factores sísmicos Q, R, SASID | pendiente (U4) | — |

## 6. Cómo reproducir

1. Verificar el paquete desde la raíz del repositorio, en el commit de `IDENTIFICACION.txt`: `grep -E '^[0-9a-f]{64}  ' auditoria_rev04/manifiesto_sha256.txt | sha256sum -c`.
2. Ejecutar el notebook en una carpeta vacía: `python3 ejecutor/ejecutar_nb.py <carpeta>/soportes_planilla.ipynb` (ver `ejecutor/LEEME.md`).
3. Pruebas: ver `PRUEBAS_REV04.md`.
