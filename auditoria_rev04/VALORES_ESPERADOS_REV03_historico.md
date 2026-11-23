# Valores esperados: caso gravitacional de ejemplo (revisión 03)

**Entrada:** `plantilla/plantilla_soportes.xlsx` (SHA-256 en `manifiesto_sha256.txt`). Estados: peso propio y muerta; sobrecarga. Combinaciones ASD del ejemplo. Sin viento.
**Salidas:** `ejemplo/resultados_soportes.xlsx`, `ejemplo/diseno_asd.xlsx`, `ejemplo/planilla_con_diseno.xlsx`, `ejemplo/memoria_calculo.html`, `ejemplo/ejecucion.log`.

## 1. Análisis

Los valores de análisis son los mismos que en la rev02 (`auditoria_rev02/valores_esperados.md`). Diferencia numérica 0 y cero diferencias de texto en REACCIONES, NODOS, BARRAS y MAXIMOS_BARRAS (`comparacion/comparacion_rev02_rev03.md`).

Ejemplo de reacciones (combinación ASD1, kgf; FZ positiva hacia arriba), tomadas de la hoja REACCIONES:

| nodo | FX | FY | FZ |
|---|---|---|---|
| 1 | 6.1007 | 4.2278 | 2216.9449 |
| 4 | 6.1007 | -4.2278 | 2216.9449 |
| 7 | -0.0000 | 4.2278 | 2361.8103 |
| 10 | 0.0000 | -4.2278 | 2361.8103 |

La suma de FZ de los cuatro apoyos es 9157.5 kgf. El equilibrio global de la rev02 (sección B de `auditoria_rev02/valores_esperados.md`) no se repitió en la rev03.

## 2. Diseño (FU máximo por barra, rev03)

Los FU de diseño cambian respecto de la rev02 (ver `comparacion/comparacion_rev02_rev03.md`, tabla completa por barra):

- FU máximo: cambia en las 26 barras (H-07). La diferencia máxima es 0.63.
- Esbeltez local: cambia en 7 vigas IR 12 × 16 (IDs 15, 16, 19, 20, 22, 24 y 26), de 0.379 a 1.451 (H-06). Estas vigas quedan NO CUMPLE en la rev03.

## 3. Lo que no está en este paquete

- **Caso sísmico:** no hay caso sísmico nuevo. El de la rev02 (`auditoria_rev02/caso_sismo/`) usa cargas de prueba (H-03).
- **Valores de comprobación independiente de FU:** la comprobación manual de la rev02 calcula con NTC y queda obsoleta (H-07).
