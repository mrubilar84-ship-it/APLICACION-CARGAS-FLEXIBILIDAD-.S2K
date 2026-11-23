# Pendientes (revisión 03)

Estado al 23 de noviembre de 2026. Los identificadores U (usuario) y A (agente) siguen la rev02; se agregan H-06 a H-09.

## A. Requieren decisión o dato del usuario

| # | pendiente | ID | estado |
|---|---|---|---|
| **D1** | **Esbeltez local de vigas con compresión secundaria (H-06): elegir (a) clasificar por acción dominante, o (b) mantener el criterio actual.** Bloquea el uso del diseño de vigas del ejemplo. | H-06 | **requiere decisión** |
| U1 | Jurisdicción (Zitácuaro) y si la autoridad acepta IMCA + AISC sin NTC-Acero. | R-04 | pendiente |
| U2 | Edición y estado (definitivo o borrador) de cada norma; origen y edición del archivo "Mexico 2023-09-16 NTC-SISMO - Para Entrega". | R-05 | pendiente |
| U3 | Ecuaciones con OCR dudoso: páginas legibles o recortes con número de ecuación. | R-05 | pendiente |
| U4 | Origen de las cargas sísmicas (E): memoria, peso sísmico, masas, distribución, Q y R, SASID. | H-03, R-06 | pendiente |
| U5 | Estados de carga reales del proyecto. | R-04 | pendiente |
| U6 | Límite de desplazamiento compatible con piping y efectos de segundo orden. | R-04 | pendiente |
| U7 | Exclusión del viento: limitación provisional o exclusión justificada. | R-04 | pendiente |
| U9 | Edición del manual Gerdau de donde salen los 30 valores completados. | R-07 | pendiente |
| U11 | Fu de A-572 G 60 (vacío en la hoja MATERIALES). | R-04 | pendiente |
| U12 | E y ν de A-529 G 50, A-572 G 50 y A-36; Fu de A-529. | R-04, R-07 | pendiente |
| U13 | Prueba del notebook en Kaggle desde cero, con y sin Internet. | R-02 | pendiente |
| U14 | Prueba en Excel de escritorio (cambio de perfil en `PERFIL_GRUPO`). | R-09 | pendiente |
| U15 | Decisiones de diseño D1 a D20 (tabla de `AUDITORIA_SOPORTES.md`, rev00). | varios | pendiente |
| **P1** | Verificar en imagen DG1 §3.1.2 (espesor de placa; φ = 0.90 y Ω = 1.67) y §3.2.1 (R_n con A_t). Confirmar en el original la pág. 19 (pdf 26): 0.7 F_u o 0.75 F_u (la misma página muestra (0.75)(0.75) = 0.5625). | H-09 | pendiente (PDF) |
| **P2** | ACI 318-02, Apéndice D, §D.5.2: texto de la ecuación D-7 (k = 10 en SI). | H-09 | pendiente (PDF) |

## B. Pendientes del agente (rev04)

| # | pendiente | ID | estado |
|---|---|---|---|
| A-H06 | Implementar la decisión D1 y F4 para almas de I, si se elige (a). | H-06 | pendiente de D1 |
| A-H07 | Actualizar `comprobacion_manual.py` a AISC/IMCA: nueva comprobación independiente del FU de la barra 1 y de una viga. | H-07 | pendiente |
| A-H08 | Actualizar o retirar `verificacion_posterior/hss/test_hss.py`. | H-08 | pendiente |
| A-H09 | Verificar los 116 HSS del catálogo ATC contra el PDF (páginas 08 a 10). | R-07 | pendiente |
| A-R02 | `pip freeze` completo del entorno de ejecución. | R-02 | pendiente |
| A-R08 | Prioridades 6 y 7 de la solicitud (entradas faltantes o no finitas; propagación de NO REVISADO a resúmenes y memoria). | R-08 | pendiente |
| A-R07 | Correspondencia de ejes y radios de LI, CE e IR contra el catálogo. | R-07 | pendiente |
| A-R05 | Recortes de página de las normas cuando el usuario entregue los PDF (depende de U2). | R-05 | pendiente |
| A-R06 | Ejemplo numérico independiente desde cargas hasta distorsión (depende de U4). | R-06 | pendiente |
| A-PB | Placas base: sustituir la prueba con datos inventados por un caso real del proyecto (planilla del proyecto con la hoja BASES), y revisar la sección 8 de la memoria. | H-09 | pendiente |
| A-FX | Confirmar que la lista de perfiles y la validación rechazan entradas faltantes y no finitas. | R-08 | pendiente |

## C. Cerrados desde la rev02

Sin cambio desde la rev02, salvo lo anotado en `RESPUESTA_AUDITORIA_REV03.md`.
