# Respuesta a la auditoría de soportes: revisión 03

**Respuesta a:** `Solicitud_Antecedentes_Auditoria_Soportes_Rev00.md` (13 de noviembre de 2026) y a la revisión 02 (`auditoria_rev02/RESPUESTA_AUDITORIA_REV02.md`).
**Versión de esta respuesta:** `auditoria_rev03/`, fecha 23 de noviembre de 2026.
**Rama:** `claude/eloquent-turing-cwpcd8`. Commit de código y paquete: ver `IDENTIFICACION.txt`.
**Carpetas anteriores:** `auditoria/`, `auditoria_rev01/` y `auditoria_rev02/` no se modifican.

## 0. Respuesta corta

**¿Está correcto el diseño?** No puede afirmarse todavía. La revisión de esta entrega encontró hallazgos que cambian resultados y que requieren una decisión del ingeniero antes de usar el diseño.

Verificado con el código actual (rev03):

- Solver y análisis: `test_rev01` 11/11 OK, `test_flecha` 4/4 OK, R-08 50/50 OK. Las hojas de análisis del caso de ejemplo (REACCIONES, NODOS, BARRAS, MAXIMOS_BARRAS) son idénticas a la rev02: diferencia 0 (`comparacion/comparacion_rev02_rev03.md`).
- Placas base (bloque 10b, nuevo): 14/14 comprobaciones contra fórmulas escritas a mano (`placas_base/prueba_independiente.py`). Es verificación de implementación, no de norma (ver H-09).
- Aviso de resultado desactualizado en LibreOffice: 4/4 (`pruebas/aviso_perfil_salida.txt`).

No verificado, o con hallazgo abierto:

- **H-06 (nuevo, requiere decisión):** la esbeltez local de vigas con compresión en alguna combinación se verifica con límites de compresión axial. En el ejemplo, 7 vigas IR 12×16 pasan de FU 0.38 a 1.45 (NO CUMPLE). Causa: commit `3b335df`.
- **H-07 (nuevo):** al eliminar la ductilidad NTC cambió el FU máximo de las 26 barras del ejemplo (diferencia máxima 0.63). Los valores de la rev02 (p. ej. FU 0.97723 de la barra 1) ya no representan el código vigente, y la comprobación manual que los reproduce sigue calculando con NTC.
- **H-08 (nuevo):** `verificacion_posterior/hss/test_hss.py` falla: llama a una función que se eliminó.
- **H-09 (nuevo):** placas base. Partes de AISC Design Guide 1 y de ACI 318-02 no están verificadas en imagen. Hay una inconsistencia en la página 19 de DG1 (sección 4).
- **H-03:** las cargas sísmicas del caso de prueba son de prueba (+1000 kgf en los nodos 3 y 6), sin origen normativo.
- **Normativa:** la NTC-Acero no aplica al diseño (decisión del usuario). No está resuelto si la autoridad de Zitácuaro acepta IMCA + AISC sin NTC (U1 en `PENDIENTES_REV03.md`).
- **No probado:** Kaggle y Excel de escritorio.

**Antes de enviar este paquete:** decidir H-06. Si cambia el criterio, la rev04 lo implementará con descripción del cambio, y esta revisión queda como registro de lo que se entregó.

## 1. Contenido del paquete

| carpeta o archivo | contenido |
|---|---|
| `RESPUESTA_AUDITORIA_REV03.md` | este documento |
| `CAMBIOS_REV03.md` | commits posteriores a la rev02, efecto en resultados |
| `VALORES_ESPERADOS_REV03.md` | valores del caso de ejemplo y su comparación con la rev02 |
| `comparacion/` | comparación celda a celda de análisis y FU, rev02 contra rev03 |
| `PRUEBAS_REV03.md` y `pruebas/` | pruebas ejecutadas con el código rev03, con su salida y código de salida |
| `placas_base/` | prueba independiente de placas base (fórmulas escritas a mano) |
| `REFERENCIAS_REV03.md` | estado de cada fuente normativa, con SHA-256 de los documentos recibidos |
| `PENDIENTES_REV03.md` | decisiones y datos pendientes, con responsable |
| `ENTORNO_REV03.md` | versiones de Python, LibreOffice y paquetes |
| `ejecutor/` | `ejecutar_nb.py` y su instrucción (R-01) |
| `ejemplo/` | salidas del caso gravitacional de ejemplo con el código rev03 (Excel, memoria HTML, log) |
| `plantilla/` | `plantilla_soportes.xlsx` (misma que la raíz del repositorio) |
| `codigo/` | `fuentes_notebook/` (módulos y celdas) y `soportes_planilla.ipynb` (notebook completo) |
| `manifiesto_sha256.txt` | SHA-256 de todos los archivos del paquete (verificable con `sha256sum -c`) |
| `IDENTIFICACION.txt` | commit de código y paquete, escrito después del commit |

## 2. Respuesta a H-01 a H-09 y R-01 a R-09

| ID | Estado | Respuesta concreta | Archivo, función, celda o página | Evidencia de prueba | Pendiente y responsable |
|---|---|---|---|---|---|
| H-01 | entregado (revalidado) | Máximo de momento en el tramo en forma cerrada. El máximo de extremos y de tramo entra en `_demanda_fila`. Revalidado con el código rev03. | `codigo/fuentes_notebook/analisis_opensees.py`, `momentos_maximos_viga`; `diseno_asd.py`, `_demanda_fila` | `pruebas/test_rev01_salida.txt`: 11/11 OK, código 0 | Ninguno |
| H-02 | entregado (revalidado) | Flecha medida respecto de la cuerda, con el término de Hermite de traslación de extremos. | `analisis_opensees.py`, `_deflexion_viga` (línea 590) | `pruebas/test_flecha_rev01_salida.txt`: 4/4 OK, código 0; 6 comprobaciones de Hermite en `test_rev01` | Ninguno |
| H-03 | pendiente (datos) | El notebook no calcula sismo: las cargas E entran desde la hoja CARGAS. El caso sísmico de la rev02 sigue con cargas de prueba (+1000 kgf en los nodos 3 y 6), sin origen normativo. La plantilla de ejemplo no tiene estado E. No hay caso sísmico nuevo en esta revisión. | `codigo/fuentes_notebook/celda7_validar.py`, `validar_cargas`; `auditoria_rev02/caso_sismo/` (sin cambio) | — | Origen de las cargas y su memoria de cálculo: usuario (R-06, U4) |
| H-04 | entregado (revalidado) | Prueba de flecha con el signo tomado de la teoría, tolerancia y código de salida. | `auditoria_rev02/pruebas/test_flecha_rev01.py`, ejecutado con el código rev03 | `pruebas/test_flecha_rev01_salida.txt`: 4/4 OK | Ninguno |
| H-05 | entregado | Paquete con notebook, ejecutor, entorno, manifiesto con SHA-256 e identificación del commit. | `auditoria_rev03/` (manifiesto, `IDENTIFICACION.txt`) | `sha256sum -c` sobre el manifiesto | Ninguno |
| H-06 | **requiere decisión** (nuevo) | En una viga con compresión en alguna combinación, la esbeltez local se verifica con límites de compresión axial (Tabla B4.1a, alma λr = 1.49√(E/Fy)) en lugar de los de flexión (Tabla B4.1b, caso 15, λr = 5.70√(E/Fy)). Ver sección 3. | `diseno_asd.py`, `esbeltez_local` y `_chequear` (regla `en_compresion`); commit `3b335df` | `ejemplo/memoria_calculo.html`, barra 15; `comparacion/comparacion_rev02_rev03.md` | Decisión del usuario (sección 3) |
| H-07 | entregado (cambio documentado) y pendiente (prueba) | Se eliminó la ductilidad NTC (commit `eb4cb1b`). El FU máximo cambia en las 26 barras del ejemplo (diferencia máxima 0.63). Los valores de la rev02 quedan obsoletos. La comprobación manual de la rev02 (`comprobacion_manual.py`) sigue calculando NTC: su salida da FU ductilidad 0.97723 para la barra 1. | `comparacion/comparacion_rev02_rev03.md`; `verificacion_posterior/comprobacion_manual/comprobacion_manual.py` | `pruebas/comprobacion_manual_salida_ACTUAL.txt` (obsoleta) | Actualizar la comprobación manual al criterio AISC/IMCA: agente, rev04 |
| H-08 | pendiente | `test_hss.py` llama a `DA._ductilidad`, eliminada con el criterio NTC. Falla con AttributeError. | `verificacion_posterior/hss/test_hss.py`, línea 75 | `pruebas/test_hss_salida.txt`, código 1 | Actualizar o retirar la prueba: agente, rev04 |
| H-09 | parcial (nuevo) | Placas base (bloque 10b) implementadas. La implementación pasa 14/14 comprobaciones con fórmulas independientes. Las normas están parcialmente verificadas (sección 4). | `codigo/fuentes_notebook/placas_base.py`; `memoria_asd.py`, `_seccion_placas` | `placas_base/salida.txt`: 14/14 OK, código 0 | Verificar en imagen DG1 §3.1.2, §3.2.1 y la pág. 19 (pdf 26), y ACI 318-02 D.5.2: usuario (PDF) |
| R-01 | entregado | Notebook completo generado desde `fuentes_notebook/` por `build_soportes_planilla3.py`, con la plantilla incrustada. Módulos y notebook están en `codigo/`. Ejecutor en `ejecutor/`. | `codigo/soportes_planilla.ipynb` (32 celdas); `codigo/fuentes_notebook/` | `ejemplo/ejecucion.log`: 8 celdas ejecutables OK, sin ERROR | Kaggle (R-02, U13) |
| R-02 | parcial | Versiones en `ENTORNO_REV03.md`: Python 3.13.18, openseespy 3.8.0.0, LibreOffice 24.2.7.2, numpy 2.5.3, pandas 3.0.5, openpyxl 3.1.5, matplotlib 3.11.2, plotly 7.1.0, Pillow 12.3.0, IPython 9.18.1 (Linux x86_64). No hay `pip freeze` completo en esta revisión. | `ENTORNO_REV03.md` | Ejecución local del notebook de ejemplo | Kaggle desde cero, con y sin Internet (U13): usuario |
| R-03 | parcial | La entrada del ejemplo es `plantilla/plantilla_soportes.xlsx` (su SHA-256 está en el manifiesto). Los valores de análisis son idénticos a la rev02. Los FU de diseño cambiaron (H-06, H-07). El caso sísmico no se actualizó. | `ejemplo/`, `comparacion/` | Diferencia 0 en REACCIONES, NODOS, BARRAS, MAXIMOS_BARRAS | Caso sísmico con origen real: usuario (H-03) |
| R-04 | requiere decisión | Lista de criterios, con la fuente de cada uno (sección 5). | Sección 5 | — | Usuario: U1, U5, U6, U7, y la decisión H-06 |
| R-05 | parcial | Fuentes, páginas verificadas y SHA-256 de cada documento recibido en `REFERENCIAS_REV03.md`. AISC 360-22: páginas 16.1-19, 16.1-21 y 16.1-23 leídas del texto extraído del PDF (no en imagen). NTC: origen y edición no resueltos. | `REFERENCIAS_REV03.md` | Hashes de los 10 archivos recibidos | PDF de DG1 y de ACI 318-02; edición y origen de la NTC de sismo: usuario (U2) |
| R-06 | pendiente (datos) | Sin cambio desde la rev02: las cargas E son de prueba y el notebook no calcula sismo. | `REFERENCIAS_REV03.md`; `PENDIENTES_REV03.md` | — | Usuario (U4): peso sísmico, masas, distribución, Q y R, SASID |
| R-07 | parcial | Base Gerdau rev04 y los 30 valores completados: sin cambio (`auditoria_rev02/base_gerdau/`). Nuevo desde la rev02: 116 HSS del catálogo ATC (`datos/hss_atc_catalogo.json`, extraídos por `datos/extraer_hss_atc.py`). La verificación de esos HSS contra el PDF no se hizo en esta revisión. | `codigo/fuentes_notebook/datos/` | SHA-256 del JSON Gerdau en `REFERENCIAS_REV03.md` | Verificar los HSS contra el PDF del catálogo: agente (rev04). Edición del manual Gerdau: usuario (U9) |
| R-08 | parcial | Pruebas ejecutadas con el código rev03: `test_rev01` 11/11, `test_flecha` 4/4, R-08 50/50, placas base 14/14, aviso de perfil 4/4. Fallan `test_hss` (H-08) y la comprobación manual con NTC (H-07). Las prioridades 6 y 7 de la solicitud (entradas faltantes, propagación de NO REVISADO) no están cubiertas. | `pruebas/`, `placas_base/`, `PRUEBAS_REV03.md` | Salidas en `pruebas/` y `placas_base/` | Prioridades 6 y 7, H-07 y H-08: agente (rev04) |
| R-09 | parcial | Aviso de resultado desactualizado: 4/4 con LibreOffice. `buscar_planilla()` (en `/kaggle/input`): si hay más de una planilla válida, detiene con error y no elige una al azar; si hay .xlsx que no son planillas, detiene; si no hay ninguno, usa la plantilla de ejemplo y lo avisa. | `codigo/fuentes_notebook/celda7_validar.py`, `buscar_planilla` (líneas 25 a 47); `pruebas/aviso_perfil_salida.txt` | 4/4 OK | Excel de escritorio (U14): usuario |

## 3. H-06: esbeltez local de vigas con compresión secundaria

**Qué hace el código.** La función `esbeltez_local` compara λ con λr de la Tabla B4.1a (compresión axial) cuando el miembro tiene compresión en alguna combinación (`en_compresion`, regla que se aplica desde el commit `3b335df`). En una viga, eso significa que el alma y el ala se comparan con 1.49√(E/Fy) y 0.56√(E/Fy).

**Qué dice AISC 360-22.** La sección B4.1 (pág. 16.1-19) separa los casos: los miembros sometidos a **compresión axial** usan la Tabla B4.1a, y los sometidos a **flexión** usan la Tabla B4.1b. La Tabla B4.1a (pág. 16.1-21, caso 5) da λr = 1.49√(E/Fy) para el alma de I. La Tabla B4.1b (pág. 16.1-23, caso 15) da λp = 3.76√(E/Fy) y λr = 5.70√(E/Fy) para el alma de I en flexión. Estas páginas se leyeron del texto extraído del PDF (`pdftotext`), no de imagen.

**Efecto medido en el ejemplo.** Barra 15, IR 12 × 16, VIGA, A-572 G 50 (Fy = 3 515 kgf/cm²):

| magnitud | valor |
|---|---|
| alma, λ = (H − 2t)/e | 52.07 |
| λr con límite de compresión (B4.1a) | 35.89 → NO CUMPLE |
| λp con límite de flexión (B4.1b) | 90.56 |
| λr con límite de flexión (B4.1b) | 137.28 → FU = 0.38 |

Las siete vigas IR 12 × 16 del ejemplo (IDs 15, 16, 19, 20, 22, 24 y 26) pasan de FU esbeltez local 0.379 a 1.451, y su FU máximo de 0.824 a 1.451.

**Observación adicional (verificada en el código).** `mn_fuerte` reduce la resistencia por pandeo local del **ala** (F3) pero no la del **alma** de I en flexión (F4). Para el IR 12 × 16 no hace diferencia, porque h/tw = 52 < λp = 90.6. Sí puede afectar a secciones con λ entre 90.6 y 137.3. No se verificó cuántos perfiles del catálogo caen en ese rango.

**Opciones para decidir (el agente no las aplica sin tu decisión):**

- (a) Clasificar cada miembro por su acción dominante: si es flexión, usar la Tabla B4.1b; si domina la compresión, usar la Tabla B4.1a. Implementar F4 para almas de I. Es el criterio que sigue el texto de B4.1.
- (b) Mantener la regla actual (cualquier compresión, límite de compresión axial). Es más conservadora y es el resultado que entregamos hoy: 7 vigas NO CUMPLE en el ejemplo.

El agente recomienda (a). La regla de compresión por miembro fue tu decisión para la compresión (KL/r y resistencia); no se decidió su aplicación a la esbeltez local del alma de vigas.

## 4. H-09: estado de las normas de placas base

| tema | fuente | estado |
|---|---|---|
| aplastamiento: P_p = mín[0.85 f′c A1 √(A2/A1); 1.7 f′c A1], Ω_c = 2.31 | IMCA cap. J, J8-1 y J8-2, pág. II-218 (pdf 312) | verificada en imagen |
| tracción en pernos: R_n = 0.7 F_u A_t, Ω = 2.00 | DG1 pág. 19 (pdf 26): verificada en imagen (0.7 F_u). Área A_t según §3.2.1 (texto del resumen) | **parcial**: la misma página tiene "(0.75)(0.75) F_u A_b = 0.5625 F_u A_b" en la línea siguiente. Se sigue el texto de DG1 (0.7), por instrucción del usuario. Confirmar en el original. |
| cortante en pernos con roscas: R_n = 0.4 F_u A_b, φ = 0.75 | DG1 pág. 42 (pdf 49) | verificada en imagen |
| soldadura E70: 0.6 F_EXX, φ = 0.75 | DG1 pág. 42 (pdf 49) | verificada en imagen |
| espesor de placa (voladizo m, n, λn′), φ = 0.90, Ω = 1.67 | DG1 §3.1.2 | texto del resumen, **no verificado en imagen** |
| cono de concreto: N_b = k λ √f′c h_ef^1.5, k = 10 (SI), φ = 0.70 | ACI 318-02 Ap. D, §D.5.2, ec. D-7 | **no verificado**; φ = 0.70 sí aparece en DG1 págs. 19 y 42 |
| conversión a ASD: Ω = 1.5/φ | reproduce Ω_c = 2.31 (IMCA, φ = 0.65) y los Ω de DG1 | derivada; consistente con las dos fuentes |

**Limitaciones que la memoria marca como NO REVISADO:**
- Excentricidad fuera del núcleo (e > N/6 en una dirección): se evalúa cada dirección por separado (lineal si está dentro de su tercio medio, triangular si queda fuera). No es la solución biaxial exacta.
- Pernos solo en la dirección N (dos filas de n/2 pernos). No se modelan pernos en Y.
- Cono de concreto con A_Nc = A_Nco: no se verifican separación ni distancia al borde ≥ 1.5 h_ef.
- Levantamiento: la flexión de la placa por los pernos no se verifica.
- Soldadura: no se verifica la transferencia de compresión por contacto.

**Datos de prueba.** La prueba de placas base usa datos inventados (placa 30 × 30 cm, dado 60 × 60 cm, 4 pernos Ø 3/4", y un perfil sintético H = 15 cm, B = 6 cm). No hay un caso real del proyecto validado. Los resultados de la planilla del proyecto con sus placas no se incluyen en el paquete, porque contienen datos del proyecto.

## 5. R-04: base de diseño y criterios

| criterio | estado | fuente |
|---|---|---|
| resistencia con AISC 360-22 ASD | confirmado | instrucción del usuario |
| NTC-Acero y NTC de sismo no aplican al diseño | confirmado | instrucción del usuario ("no aplica la NTC") |
| KL/r ≤ 200 como límite del proyecto, referencia IMCA cap. E, nota II-89 ("preferiblemente") | confirmado; la referencia está verificada en imagen | instrucción del usuario |
| verificación de compresión (KL/r y esbeltez local en compresión) en cualquier miembro con compresión en alguna combinación | confirmado | instrucción del usuario |
| esbeltez local en flexión de vigas | **pendiente** (H-06) | — |
| sismo entra como carga de la planilla; el notebook no lo calcula | confirmado | instrucción del usuario |
| viento excluido | pendiente de confirmar: ¿limitación provisional o exclusión justificada? (U7) | — |
| flecha: L/360 (AISC 360-22, Comentario L2) | confirmado | instrucción del usuario |
| ángulos LI: análisis con Ix = Iy del catálogo; diseño con Iu e Iv | confirmado ("se mantiene") | instrucción del usuario |
| placas base: IMCA cap. J + DG1 + ACI 318-02, todos los datos de entrada | enfoque confirmado; valores pendientes de verificación (sección 4) | instrucción del usuario |
| base de perfiles: Gerdau rev04 y HSS del catálogo ATC | confirmado el uso; verificación de HSS pendiente | — |
| jurisdicción (Zitácuaro) y si la autoridad acepta IMCA sin NTC | **pendiente** (U1) | — |
| estados de carga reales, límite de desplazamiento por piping y segundo orden | **pendiente** (U5, U6) | — |
| factores sísmicos Q, R, SASID | **pendiente** (U4) | — |

## 6. Cambios desde la rev02

Ver `CAMBIOS_REV03.md`. Resumen: se eliminó el criterio NTC (ductilidad, ahora sin 6.3), se agregó la verificación KL/r ≤ 200, se aplicó la compresión por miembro, se agregaron HSS del catálogo ATC (diseño, cortante y torsión), y se agregó el bloque de placas base. El análisis no cambió.

## 7. Cómo reproducir

1. Verificar el paquete: desde la raíz del repositorio en el commit de `IDENTIFICACION.txt`, `grep -E '^[0-9a-f]{64}  ' auditoria_rev03/manifiesto_sha256.txt | sha256sum -c`.
2. Ejecutar el notebook en una carpeta vacía: `python3 ejecutor/ejecutar_nb.py <carpeta>/soportes_planilla.ipynb` (ver `ejecutor/LEEME.md`).
3. Pruebas: ver `PRUEBAS_REV03.md`.
