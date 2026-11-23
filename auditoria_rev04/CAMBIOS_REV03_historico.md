# Cambios respecto de la revisión 02 (rev02 → rev03)

**Base:** `auditoria_rev02/`, identificada en el commit `20b1972`. Lo que sigue son los commits posteriores (de más antiguo a más reciente).
**Efecto en resultados:** ninguno en el análisis (REACCIONES, NODOS, BARRAS, MAXIMOS_BARRAS: diferencia 0 en el caso de ejemplo). Sí cambia el diseño en los puntos marcados.

| commit | cambio | efecto en el diseño |
|---|---|---|
| `72c39ed` | HSS del catálogo ATC: base (116 secciones), diseño ASD (F7, E7, G2, H1), memoria | nuevos perfiles HSS; no afecta IR, CE ni LI |
| `be3167a` | HSS: cortante con G4-1 y Cv2 (kv = 5); comprobación independiente en la prueba | HSS |
| `f61677a` | HSS: torsión (H3.1) e interacción H3-6 (H3.2). Torsión no verificada en IR, CE y LI | HSS |
| `fd0003d` | base de perfiles comprimida para cumplir el límite de 1 MB del notebook | ninguno |
| `3d21699` | tablas por grupo: FU máximo y verificación que gobierna | presentación |
| `2109e10` | FU de esfuerzos y FU de esbeltez separados en tablas y desplegable | presentación |
| `e663475` | el notebook lee la planilla subida aunque su nombre no contenga "soportes" | lectura de la entrada |
| `b767776` | celda 9b (escala de la deformada) visible para editar | presentación |
| `311400e` | deformada 3D: el cursor sobre un nodo muestra su desplazamiento | presentación |
| `7d7cac6` | memoria 6.3: tabla con el origen de la deformación (sismo, gravedad D y L) | memoria |
| `eb4cb1b` | **diseño sin NTC**: esbeltez local AISC B4.1, KL/r ≤ 200 (IMCA cap. E), sin ductilidad ni 6.3 | **cambia el FU máximo de las 26 barras del ejemplo (H-07)** |
| `fb94641` | referencia del KL/r ≤ 200: nota II-89 del IMCA, aplicada como límite del proyecto | memoria |
| `fe17a59` | memoria: la demanda de cada verificación es la de la combinación que la controla | memoria |
| `3b335df` | **compresión por miembro**: KL/r y esbeltez local en compresión para cualquier barra con compresión en alguna combinación | **cambia la esbeltez local de 7 vigas (H-06)** |
| `061b3d0` | memoria: decisión de mantener Ix = Iy del catálogo para ángulos LI en el análisis | memoria |
| `c43db53` | **placas base** (bloque 10b): hoja BASES, verificación ASD y sección 8 de la memoria | nueva verificación; no cambia columnas ni vigas |
| `7f3d4e4` | placas base: tracción en pernos con DG1 (0.7 F_u A_t); memoria ordenada paso a paso (sección 8.i.1 a 8.i.5); aplastamiento fuera del núcleo por dirección | placas base |

Este paquete (`auditoria_rev03/`) se commitea después de `7f3d4e4`. El commit exacto está en `IDENTIFICACION.txt`.

## Cambios que requieren atención del auditor

1. **Eliminación de la ductilidad NTC (`eb4cb1b`).** Los valores de la rev02 que incluyen ductilidad (p. ej. FU 0.97723 de la barra 1 en `comprobacion_manual`, y la columna "FU DUCTILIDAD" de la rev02) ya no corresponden al código vigente. Ver `comparacion/comparacion_rev02_rev03.md`.
2. **Compresión por miembro (`3b335df`).** Aplicó el límite de compresión axial a vigas con compresión secundaria. Ver H-06 en `RESPUESTA_AUDITORIA_REV03.md`, sección 3. Modifica la esbeltez local de 7 vigas del ejemplo. El commit `eb4cb1b` modifica además el FU máximo de todas las barras (H-07). H-06 requiere decisión antes de usar el diseño de vigas.
3. **Placas base (`c43db53`, `7f3d4e4`).** Es un bloque nuevo y no cambia columnas ni vigas. Sus normas tienen partes sin verificar en imagen (H-09).
4. **HSS (`72c39ed` a `f61677a`).** Son perfiles nuevos. No están incluidos en el caso de ejemplo, así que no hay resultados HSS en este paquete que comparar. Sus torsiones no están verificadas en IR, CE y LI (nota de `f61677a`).
