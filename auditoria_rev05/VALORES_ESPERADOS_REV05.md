# Valores esperados: caso gravitacional de ejemplo (revisión 05)

**Entrada:** `plantilla/plantilla_soportes.xlsx` (SHA-256 en `manifiesto_sha256.txt`). Estados: peso propio y muerta (D); sobrecarga (L); viento X (W, no se usa). Combinaciones ASD del ejemplo.
**Salidas:** `ejemplo/resultados_soportes.xlsx`, `ejemplo/diseno_asd.xlsx`, `ejemplo/planilla_con_diseno.xlsx`, `ejemplo/memoria_calculo.html`, `ejemplo/ejecucion.log`.

## 1. Análisis

Idéntico a la rev02 y a la rev03 (diferencia 0 en REACCIONES, NODOS, BARRAS y MAXIMOS_BARRAS). Valores de referencia en `auditoria_rev02/valores_esperados.md`.

Reacciones de ejemplo (combinación ASD1, kgf; FZ positiva hacia arriba), de la hoja REACCIONES:

| nodo | FX | FY | FZ |
|---|---|---|---|
| 1 | 6.1007 | 4.2278 | 2216.9449 |
| 4 | 6.1007 | -4.2278 | 2216.9449 |
| 7 | -0.0000 | 4.2278 | 2361.8103 |
| 10 | 0.0000 | -4.2278 | 2361.8103 |

La suma de FZ de los cuatro apoyos es 9157.5 kgf. El equilibrio global de la rev02 (sección B de `auditoria_rev02/valores_esperados.md`) no se repitió en esta revisión.

## 2. Diseño (FU por barra)

Respecto de la rev03, cambian solo las 7 vigas IR 12 × 16 (ver `comparacion/comparacion_rev03_rev04.md`):

| ID | FU esbeltez local | FU KL/r | FU máximo | estado |
|---|---|---|---|---|
| 15, 16, 19, 20 | 0.379 | 1.250 | 1.250 | NO CUMPLE |
| 22, 24, 26 | 0.379 | 1.000 | 1.000 | CUMPLE |

Las demás barras no cambian respecto de la rev03. Respecto de la rev02, el FU máximo cambia en todas las barras por la eliminación de la ductilidad NTC (`comparacion/comparacion_rev02_rev04.md`).

## 3. Lo que no está en este paquete

- **Caso sísmico:** no hay caso sísmico nuevo (H-03).
- **Comprobación manual de FU con criterio AISC/IMCA:** pendiente (H-07).

## 4. Revisión 05

Los valores son los mismos que en la rev04 (`comparacion/comparacion_rev04_rev05.md`: diferencia 0 en análisis y en FU). Los casos corregidos en la rev05 no aparecen en este ejemplo; su verificación está en `PRUEBAS_REV05.md`.
