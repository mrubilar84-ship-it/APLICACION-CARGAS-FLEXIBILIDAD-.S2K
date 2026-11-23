# Respuesta a la auditoría de soportes: revisión 05

**Respuesta a:** `Auditoria_Soportes_Rev04_Para_Agente.md` (23 de noviembre de 2026), sobre el paquete `auditoria_soportes_rev04.zip` (SHA-256 `55fa9919…421d67`).
**Versión de esta respuesta:** `auditoria_rev05/`, fecha 23 de noviembre de 2026.
**Rama:** `claude/eloquent-turing-cwpcd8`. Commit de código y paquete: ver `IDENTIFICACION.txt`.
**Carpetas anteriores:** `auditoria/`, `auditoria_rev01/` a `auditoria_rev04/` no se modifican.

## 0. Resumen

- **Reproducción de los contraejemplos del auditor: no realizada.** Intenté ejecutar el script `pruebas_auditor.py` del informe y el permiso de ejecución fue denegado por el sistema. No lo sorteé. Por eso **no reproduje los valores T01 a T23**. Verifiqué cada observación leyendo el código de la rev04, y con pruebas propias (`pruebas_regresion/prueba_rev05.py`, 17/17). Si quiere la reproducción del auditor, hay que autorizar la ejecución o ejecutar el script y enviar su salida.
- **Corregido con prueba propia:** R04-01, R04-04, R04-07, R04-08, R04-09, R04-12 (IR), R04-18, R04-19, R04-17 (fórmula), R04-22 (RESUMEN).
- **Corregido como bloqueo** (la barra o el nodo no pueden aprobarse, sin supuesto): R04-02, R04-03, R04-05, R04-06, R04-23.
- **Pendiente de decisión o dato del usuario:** R04-10 (espesor de diseño HSS), R04-14 (segundo orden), R04-15 (LI, Ix = Iy), R04-16 (flujo de selección de perfil, parcial), R04-21 (caso real).
- **Resultados del caso de ejemplo:** idénticos a la rev04 (análisis, FU, estados). Ninguno de los casos corregidos aparece en ese ejemplo. Las correcciones se verifican con pruebas dirigidas, no con el ejemplo.

## 1. Respuesta por observación

Estados: **corregido** (con prueba propia), **bloqueo** (fuera de alcance con bloqueo de aprobación), **parcial**, **pendiente** (decisión o dato).
Líneas: `diseno_asd.py` y `placas_base.py` según `fuentes_notebook/` en el commit de la rev05.

| ID | Estado | Cambio y justificación | Archivo, función y línea | Prueba y valor esperado | Evidencia / pendiente |
|---|---|---|---|---|---|
| R04-01 | corregido | H1 también con axial nulo: H1-1b con Pr/Pc = 0 → Mrx/Mcx + Mry/Mcy ≤ 1. Antes no se calculaba la interacción. | `diseno_asd.py`, `_utilizacion_base`, línea 628 | Prueba: Mrx = Mry = 600, Mcx = Mcy = 1000 → H1 = 1.20 (esperado 1.20). Uniaxial → 0.60. | `pruebas_regresion/salida.txt`. Angulos LI siguen con H2 (sin cambio). |
| R04-02 | bloqueo | Torsión en sección abierta (IR, CE, LI) con |Tr| > 1e-3 kgf·cm: chequeo de bloqueo con FU 99 (no se supone resistencia). La torsión de sección abierta no se modela. | `diseno_asd.py`, `utilizacion_asd` línea 584; `CHEQUEO_TORSION_ABIERTA` línea 580 | Prueba: Tr = 1e6 → bloqueo; Tr = 1e-6 → sin bloqueo. | El ruido numérico queda por debajo de 1e-3 kgf·cm; las demandas del ejemplo son ≤ 1e-6. |
| R04-03 | bloqueo | MZ en la base y momentos sin compresión (transferencia al dado y anclajes) → pendiente explícito. La base no puede quedar CUMPLE con ellos. No se modelan. | `placas_base.py`, `_combinacion`, línea 147 | Prueba: reacción de torsión pura → NO REVISADO (no CUMPLE, no FU cero). | Modelar MZ y el momento sin axial: pendiente de alcance (D8). |
| R04-04 | corregido | El estado global ya no lee CUMPLE solo porque FU ≤ 1: sin pendientes → CUMPLE; con pendientes → NO REVISADO; FU > 1 → NO CUMPLE. Las limitaciones de anclajes, cono y soldadura siempre están listadas. | `placas_base.py`, `verificar_nodo`, líneas 299–306; `LIMITACIONES` línea 44 | Prueba: levantamiento con flexión de placa → NO REVISADO; anclajes siempre listados. | La memoria muestra estos nodos con sus tablas (clase `norev`). |
| R04-05 | bloqueo | Contacto biaxial fuera del núcleo: pendiente explícito («sin solución de contacto»). La presión aproximada no se usa para aprobar. | `placas_base.py`, `_apoyo` línea 106; `_combinacion` línea ~152 | Prueba: ex = ey = 3 cm → pendiente y estado distinto de CUMPLE. | Solución de contacto biaxial sin tracciones: pendiente. La discontinuidad en la frontera biaxial queda documentada y no se usa. |
| R04-06 | bloqueo | El módulo de anclajes se declara predimensionamiento. Se listan como no verificados: arrancamiento lateral, rotura lateral, pryout, espesor, efecto de grupo, y el supuesto A_Nc = A_Nco. No se cambió ningún factor. | `placas_base.py`, `LIMITACIONES`, línea 44 | Prueba: las limitaciones aparecen en todo nodo. | Caso real con plano de pernos y bordes (D5). 0.7 F_u A_t: pendiente de confirmar en el original de DG1 (pág. 19, pdf 26). |
| R04-07 | corregido | Validación antes de calcular: valores finitos, positivos, n entero par ≥ 2, c anclas < N/2, dado ≥ placa, placa ≥ envolvente de la sección (antes solo aviso). Resultado: DATO INVALIDO sin FU. | `placas_base.py`, `verificar_nodo`, líneas 228–255 | Prueba: espesor −2 → DATO INVALIDO; n = 4.5 → DATO INVALIDO; placa 10×30 bajo 15×6 → DATO INVALIDO; valor infinito → DATO INVALIDO. | La validación de Excel no se considera suficiente; la del motor sí. |
| R04-08 | corregido | Fu ausente con tracción: no se supone fractura. Se bloquea la barra con motivo «NO REVISADO: falta Fu». | `diseno_asd.py`, `resistencias_asd` línea 548; `_chequear` línea 851; llamadas 1023, 1099, 1317 | Prueba: IR con Fu vacío y tracción → NO REVISADO con motivo. | Fu de A-572 G60 sigue vacío en la plantilla (U11). |
| R04-09 | corregido | Demanda vacía, texto, NaN o infinito → error del diseño («no se supone cero»). Antes se convertía en 0. | `diseno_asd.py`, `_dato` línea 746; `_demanda_fila` línea 758 | Prueba: Vy = NaN → error con el mensaje; fila de ceros → correcta. | El ejemplo tiene todas las demandas finitas (sin cambio de resultados). |
| R04-10 | pendiente (D4) | AISC 360-22 §B4.2 (texto extraído, no verificado en imagen): para HSS de normas distintas de ASTM A1065/A1085 (A500 incluido), el espesor de diseño es 0.93 veces el nominal. El catálogo ATC no indica si sus propiedades usan el nominal o el de diseño, ni la norma del producto. No se cambia el cálculo sin esa información. | `ATC` (`datos/hss_atc_catalogo.json`); `_hss_planos`, `mn_hss` | — | Decisión D4: norma del producto y base de las propiedades del catálogo. Si es A500, las propiedades deben recalcularse, no solo escalarse. |
| R04-11 | parcial | La alerta del catálogo llega a `obtener_perfil` y a la columna NOTAS del resultado. Pendiente: memoria, selector de perfiles y resolver las siete inconsistencias. | `perfiles_gerdau_nb.py` línea 26; `diseno_asd.py` líneas 1106–1107 | Prueba: 7 perfiles con alerta; la alerta aparece en obtener_perfil. | Resolver contra la fuente (dato del usuario). |
| R04-12 | corregido (IR); LI corregido por lectura | IR: cuatro salientes de patín (AISC E7, dos por patín). LI: umbral de E7-2 = λr·√(Fy/Fn), igual que IR/CE/HSS (antes se usaba c2 y no era E7-2). | IR: `diseno_asd.py` línea 119; LI: `_resistencias_angulo`, línea ~470 | IR: prueba con expectativa independiente (47.783093 cm²). LI: no automatizada; verificada leyendo AISC E7-2 (texto extraído, pág. 16.1-48). | Prueba automatizada de LI pendiente (rev06). |
| R04-13 | parcial | La clasificación local de la VIGA (B4.1b) y la compresión (B4.1a) se muestran por separado; la compresión sigue entrando a E7 y KL/r. Sin cambio de cálculo. | `diseno_asd.py`, `_chequear` línea ~842 | — | Separar clasificación, resistencia y límite contractual en la memoria: pendiente (rev06). |
| R04-14 | bloqueo | Análisis elástico de primer orden. La memoria lo declara y lo deja NO REVISADO como estabilidad (P-Δ, P-δ, imperfecciones). No se implementa segundo orden. | `memoria_asd.py`, `_pendientes_html` (primer ítem) | — | Método de segundo orden y su aplicabilidad: decisión D6. |
| R04-15 | pendiente (D3) | Se mantiene la decisión del usuario (Ix = Iy del catálogo para LI en el análisis). No se restringe ni se corrige la distribución de rigideces. | `analisis_opensees.py`, `propiedades_barras`; memoria de ángulos LI | — | Aceptar el alcance LI con Ix = Iy, o restringir LI a un alcance validado: decisión D3. |
| R04-16 | parcial | Ya existe la alerta «DESACTUALIZADO» en PERFIL_GRUPO. Pendiente: que RESULTADOS y la memoria rotulen los candidatos como predimensionamiento con demandas congeladas. | `celda10_diseno.py`, `_aplicar`; `celda6_plantilla.py` líneas 1296–1313 | — | Flujo de emisión: decisión D7 (predimensionamiento o análisis nuevo por cada cambio). |
| R04-17 | corregido (fórmula) | El estado de grupo es CUMPLE solo si todas las barras del grupo están CUMPLE. Si hay una NO REVISADO → «NO REVISADO: barras sin verificacion completa». | `celda6_plantilla.py`, `_hojas_diseno_vivo`, línea 1311 | Recalculado con LibreOffice en el ejemplo: VIGA NO CUMPLE, COLUMNA CUMPLE (correcto). | Prueba del caso mixto con barra sin coincidencia: pendiente (rev06). |
| R04-18 | corregido | Al regenerar el libro se conservan los valores de PARAMETROS de la entrada (antes se restauraban los del catálogo). | `celda6_plantilla.py` línea 1024; `celda8_dibujo.py` y `celda10_diseno.py` (`parametros=PAR_LEIDA`) | **Extremo a extremo:** Kz = 0.5 en la entrada → libro regenerado con Kz = 0.5 (ejecución completa, código 0). | Procedimiento en `PRUEBAS_REV05.md`, sección «Kz»; su log no está en el paquete. |
| R04-19 | corregido | El ejecutor sale con código 1 ante cualquier error o SystemExit no nulo, y declara «EJECUCION INCOMPLETA». | `auditoria_rev05/ejecutor/ejecutar_nb.py` | Prueba: error al inicio → 1; error al final → 1; completo → 0. | Sin cambio en el notebook. |
| R04-20 | parcial | Se incluyen fuentes de las pruebas, salidas y la prueba de regresión propia (17/17), la prueba de placas (14/14) y R-08 (50/50). La prueba de HSS sigue fallando (H-08). No se reproduce el script del auditor. | `pruebas/`, `placas_base/`, `pruebas_regresion/`, `PRUEBAS_REV05.md` | Ver `PRUEBAS_REV05.md`. | Actualizar o retirar la prueba HSS (A-H08). Comparación con OpenSees/Kaggle: pendiente. |
| R04-21 | pendiente (dato) | El paquete no contiene un caso real del proyecto. No hay cargas sísmicas de origen normativo. | — | — | Caso real con entrada, salida, memoria y log (U4, D5). |
| R04-22 | parcial | RESUMEN corregida: sin «Ductilidad 12.1.2» y con el criterio de KL/r para miembros comprimidos. L/360 documentado como criterio adoptado para este proyecto. **No confirmado:** la numeración F7 (el texto extraído de AISC 360-22 usa F7-8 a F7-11 para LTB, igual que el código) y la excepción de LTB para HSS cuadrados (no aparece en el texto de F7, pág. 16.1-63). | `diseno_asd.py` líneas 1148–1160; `memoria_asd.py` línea 547 | Texto de F7 en `REFERENCIAS_REV05.md`. | Si el auditor tiene la edición con esa excepción o la numeración distinta, debe indicar página. |
| R04-23 | bloqueo | El modelo de soldadura es simplificado (cortante + tensión). No es un modelo de grupo. Se declara NO REVISADO y no puede aprobar. | `placas_base.py`, `LIMITACIONES`; `_combinacion` | — | Modelo de grupo de soldadura y transferencia columna–placa: pendiente (D8). |

## 2. Qué no se hizo y por qué

- **Script de reproducción del auditor (T01–T23):** no ejecutado (permiso denegado). Por eso los valores que cita (por ejemplo 0.60, 1.20, 0.04435, 0.97723) no están reproducidos aquí.
- **Ejecución en OpenSees, Kaggle y Excel de escritorio:** no realizada en esta revisión.
- **Comparación con SAP2000:** no aplica (decisión del usuario: no se incluye el modelo).

## 3. Decisiones pendientes del usuario

Ver `PENDIENTES_REV05.md`. Resumen:
- **D2:** KL/r ≤ 200 en vigas con compresión (cuatro vigas NO CUMPLE en el ejemplo).
- **D3:** LI con Ix = Iy (R04-15).
- **D4:** espesor de diseño de HSS (R04-10): norma del producto y base del catálogo.
- **D5:** caso real del proyecto (R04-21).
- **D6:** método de segundo orden (R04-14).
- **D7:** flujo de selección de perfil (R04-16).
- **D8:** alcance de placas base hasta cerrar anclajes, soldadura y momentos (R04-03, R04-05, R04-06, R04-23).

## 4. Cómo reproducir

1. Verificar el paquete desde la raíz del repositorio en el commit de `IDENTIFICACION.txt`: `grep -E '^[0-9a-f]{64}  ' auditoria_rev05/manifiesto_sha256.txt | sha256sum -c`.
2. Ejecutar el notebook en una carpeta vacía: `python3 ejecutor/ejecutar_nb.py <carpeta>/soportes_planilla.ipynb`.
3. Pruebas: `PRUEBAS_REV05.md`.
