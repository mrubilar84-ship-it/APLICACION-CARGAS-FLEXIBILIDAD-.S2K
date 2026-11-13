# Cambios respecto de la versión recibida (rev00 → rev01)

**Base:** `auditoria/` (versión recibida, sin cambios).
**Código de referencia de rev00:** los 10 módulos de `auditoria/codigo/modulos/` son idénticos a los extraídos de las celdas `%%writefile` del notebook del commit `c9208948f93f7a3cddc691550aa967c1e0eca363`.
**Diferencias de código:** `comparacion/cambios_rev00_rev01.diff` (diff unificado, `rev00/` contra `rev01/`).

## 1. Cambios de código

Solo cambian tres módulos y un bloque de celda. El resto del código es idéntico al de rev00.

| archivo | función | cambio | hallazgo | líneas de diff (+/−) |
|---|---|---|---|---|
| `codigo/modulos/analisis_opensees.py` | `_tablas` (l. 236) | Recibe `props` y `fpp`. Agrega las columnas `MZ MAX EN EL TRAMO (kgf·m)` y `MY MAX EN EL TRAMO (kgf·m)` a las tablas de barras (REPORTAR y DISENO_BARRAS). | H-01 | 233–251 |
| `codigo/modulos/analisis_opensees.py` | `_curvatura_max` (l. 478) — **nueva** | Máximo de \|EI·v''\| a lo largo de la viga, con la solución exacta de Euler-Bernoulli entre extremos, con carga uniforme. Muestreo de 401 puntos. | H-01 | 460–494 |
| `codigo/modulos/analisis_opensees.py` | `momentos_maximos_viga` (l. 490) — **nueva** | Calcula Mz y My máximos en el tramo para cada combinación (plano x–y con E·Iz; plano x–z con E·Iy), con el peso propio de la combinación. | H-01 | 460–494 |
| `codigo/modulos/analisis_opensees.py` | `_deflexion_viga` (l. 452) | Agrega el término de Hermite de traslación de extremos, g(ξ)·(v_i − v_j) con g = ξ − 3ξ² + 2ξ³, en los dos planos. Antes solo usaba los giros. | H-02 | 460–494 |
| `codigo/modulos/analisis_opensees.py` | `correr` (l. 534) | Calcula `pp_map` y `fpp_caso` (factor del peso propio por estado y por combinación) y los pasa a `_tablas`. Ahora `DISENO_BARRAS` también recibe `props` y `fpp_caso`. | H-01 | 523–547 |
| `codigo/modulos/diseno_asd.py` | `_demanda_fila` (l. 527) | Mr_x y Mr_y toman el máximo entre los extremos I y J y el máximo en el tramo (columnas nuevas). Acceso estricto a las claves: si falta una columna, el cálculo se detiene. | H-01 | 528–538 |
| `codigo/modulos/diseno_asd.py` | `listas_por_grupo_asd` (l. 969) | Guarda `NotImplementedError`. Código sin uso que lee solo los momentos de extremo. Se conserva para trazabilidad. | H-01 (código muerto) | 964–970 |
| `codigo/modulos/diseno_ntc.py` | `diseno_desde_planilla` (l. 462) | Guarda `NotImplementedError` (mismo motivo). | H-01 (código muerto) | 460–466 |
| `codigo/modulos/diseno_ntc.py` | `listas_por_grupo` (l. 644) | Guarda `NotImplementedError` (mismo motivo). | H-01 (código muerto) | 641–647 |
| `codigo/bloques/celda_15.py` | `buscar_planilla` (l. 26) | Ordena la lista de archivos y lanza `RuntimeError` si hay más de un `.xlsx` con "soportes" en `/kaggle/input`. Antes elegía el primero. | R-09 | (bloque, no está en el diff de módulos) |

El notebook `soportes_planilla.ipynb` (raíz del repositorio) se regeneró a partir de estas fuentes. Sus celdas de código coinciden con `codigo/modulos/` y `codigo/bloques/`.

## 2. Qué no cambió

- `plantilla_soportes.xlsx` (raíz del repositorio): mismo SHA-256 que antes (`9ef07e79…`).
- Hojas de entrada y de norma de la plantilla. No se modificó ningún dato de diseño ni de norma.
- Decisiones D1–D20: siguen abiertas. Los comentarios `DECISION` del código (18 apariciones) no se cambiaron.
- `referencias/`, `auditoria/` y su ZIP.
- El resto de los módulos (`gerdau_datos.py`, `orientacion_gerdau.py`, `parametros.py`, `memoria_asd.py`, `dibujo_directo.py`, `vista3d_plotly.py`, `perfiles_gerdau.py`, `diseno_ntc.py` salvo las guardas).

## 3. Efecto sobre los resultados entregados

- **Hojas de los Excel:** ninguna celda cambia, en los dos casos (`comparacion/comparacion_rev00_rev01.md`).
- **Memoria:** en la tabla 6.4 cambia la posición x/L del máximo de flecha en dos barras (0,53 → 0,52), por H-02. El valor en mm no cambia con dos decimales.
- **H-01 en estos casos:** no cambia ningún resultado, porque el momento de extremo supera al interior. El efecto de H-01 se demuestra en las pruebas aisladas.

## 4. Limitaciones conocidas de esta revisión

- `_curvatura_max` muestrea 401 puntos. El error de muestreo no está acotado formalmente. Para cargas puntuales o momentos de extremo con quiebres en la curva, el máximo podría quedar entre dos puntos. Pendiente: acotar el error o usar los puntos de quiebre (agente, siguiente ronda).
- Las guardas de código muerto no eliminan el código. Si se reutiliza, debe cambiarse para leer las columnas del tramo.
- No se corrigió nada en la base Gerdau ni en las 30 propiedades completadas; su estado sigue siendo NO VERIFICADO (ver `base_gerdau/`).
