# Cambios de la revisión 04 (rev03 → rev04)

**Base:** `auditoria_rev03/`, commit `1a14dad` (código y paquete de la rev03).

## 1. Código

| archivo | cambio |
|---|---|
| `codigo/fuentes_notebook/diseno_asd.py`, `_chequear` | la esbeltez local usa los límites de compresión solo si el miembro está comprimido y no es VIGA: `esbeltez_local(..., compresion = compr and grupo != 'VIGA')`. La KL/r sigue usando `compr` (sin cambio). |
| `codigo/fuentes_notebook/memoria_asd.py`, `_ref_local` | la referencia de esbeltez local de una VIGA es la Tabla B4.1b (flexión), no la B4.1a. |
| `codigo/fuentes_notebook/memoria_asd.py`, `_nota_normativa` | el texto "Aplica a" de las filas de compresión dice COLUMNA, ARRIOSTRE y DIAGONAL con compresión; la VIGA se revisa a flexión. |
| `codigo/soportes_planilla.ipynb` | regenerado con `build_soportes_planilla3.py` y la plantilla de la raíz. |

Sin cambios: el análisis (OpenSees), la plantilla, la base Gerdau, la norma (hoja NORMA) y las placas base.

## 2. Efecto en resultados (caso de ejemplo)

- **Análisis:** sin cambio (REACCIONES, NODOS, BARRAS y MAXIMOS_BARRAS: diferencia 0 frente a la rev03 y la rev02).
- **Esbeltez local:** cambia solo en las 7 vigas IR 12 × 16 (IDs 15, 16, 19, 20, 22, 24 y 26): de 1.451 a 0.379. Ninguna otra barra cambia.
- **FU máximo y estado:** cambian las 7 vigas. Las 4 vigas con KL/r = 250 quedan NO CUMPLE por KL/r (FU 1.250). Las 3 vigas con KL/r = 200 quedan CUMPLE (FU 1.000). Detalle en `comparacion/comparacion_rev03_rev04.md`.
- **Estados NO CUMPLE del ejemplo:** 7 en la rev03, 4 en la rev04.

## 3. Verificaciones hechas para esta revisión

- **Alma en flexión (AISC F4):** se verificó en el catálogo IR y CE que ningún alma tiene h/tw mayor que λp (máximo 59.6; λp entre 82.6 y 106.7 según el Fy). Por eso F4 no cambia ningún resultado del catálogo. No se implementó.
- **Pruebas:** ver `PRUEBAS_REV04.md`. Todas las pruebas numéricas siguen pasando con el código rev04.

## 4. Lo que la rev04 no cambia (y sigue abierto)

- **D2:** KL/r ≤ 200 en vigas con compresión (4 vigas NO CUMPLE). Requiere tu confirmación.
- **H-07:** los valores de la rev02 con ductilidad siguen obsoletos. La comprobación manual sigue con NTC.
- **H-08:** `test_hss.py` sigue fallando.
- **H-09:** las normas de placas base siguen parcialmente verificadas.

## 5. Cambios de la rev03 (ya entregados)

Ver `CAMBIOS_REV03_historico.md`.
