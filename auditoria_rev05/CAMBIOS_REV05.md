# Cambios de la revisión 05 (rev04 → rev05)

**Base:** `auditoria_rev04/`, commit `f98cc13` (código y paquete de la rev04).
**Resultado del caso de ejemplo:** sin cambio (análisis, FU y estados idénticos a la rev04).

## 1. Código (`codigo/fuentes_notebook/`)

| archivo | función | cambio | observación del auditor |
|---|---|---|---|
| `diseno_asd.py` | `_elementos_E7` (I) | cuatro salientes de patín (dos por patín) | R04-12 |
| `diseno_asd.py` | `_resistencias_angulo` (LI) | umbral de E7-2: λ ≤ λr·√(Fy/Fn) (antes usaba c2) | R04-12 |
| `diseno_asd.py` | `utilizacion_asd` (envoltorio) y `_utilizacion_base` | torsión en sección abierta: chequeo de bloqueo (FU 99) | R04-02 |
| `diseno_asd.py` | `_utilizacion_base` | H1 con axial nulo (H1-1b, Pr/Pc = 0) | R04-01 |
| `diseno_asd.py` | `resistencias_asd`, `_chequear` | Fu ausente con tracción → NO REVISADO con motivo; llamadas que lo respetan | R04-08 |
| `diseno_asd.py` | `_dato`, `_demanda_fila` | demanda no finita o vacía → error; ya no se convierte en cero | R04-09 |
| `diseno_asd.py` | RESUMEN | sin «Ductilidad 12.1.2»; criterio de KL/r y de B4.1 descrito correctamente | R04-22 |
| `diseno_asd.py` | diseño por perfil (NOTAS) | alerta del catálogo visible en NOTAS | R04-11 |
| `placas_base.py` | `verificar_nodo` | validación estricta (DATO INVALIDO); estado NO REVISADO con pendientes; CUMPLE solo sin pendientes | R04-04, R04-07 |
| `placas_base.py` | `_combinacion`, `_apoyo` | pendientes: MZ, momento sin compresión, levantamiento con flexión, contacto biaxial fuera del núcleo | R04-03, R04-05 |
| `placas_base.py` | `LIMITACIONES` | anclajes, cono, soldadura y NORMA siempre listados como no verificados | R04-06, R04-23 |
| `perfiles_gerdau_nb.py` | `obtener_perfil` | devuelve `alerta_catalogo` y `campos_pendientes` | R04-11 |
| `celda6_plantilla.py` | `_hojas_diseno_vivo` | estado de grupo exige que todas las barras estén CUMPLE | R04-17 |
| `celda6_plantilla.py` | `_hoja_normas_y_parametros`, `escribir_planilla` | conserva los valores de PARAMETROS de la entrada | R04-18 |
| `celda8_dibujo.py`, `celda10_diseno.py` | llamadas a `escribir_planilla` | pasan `parametros=PAR_LEIDA` | R04-18 |
| `memoria_asd.py` | `_seccion_placas`, `_pendientes_html`, `REF` | nodos NO REVISADO con sus tablas; aviso de primer orden; L/360 como criterio adoptado | R04-04, R04-14, R04-22 |

## 2. Ejecutor (`ejecutor/ejecutar_nb.py`)

Sale con código 1 ante cualquier error o salida no nula, y declara «EJECUCION INCOMPLETA». Antes salía con 0 después de un error (R04-19).

## 3. Pruebas nuevas

`pruebas_regresion/prueba_rev05.py` (17/17), `pruebas_regresion/prueba_ejecutor.py` (3/3) y la prueba Kz de extremo a extremo (ver `PRUEBAS_REV05.md`).

## 4. Qué no cambia

- Análisis (OpenSees), plantilla, base Gerdau, hoja NORMA, factores de norma, criterio de KL/r ≤ 200, criterio de compresión por miembro y el criterio de vigas de la rev04.
- Las decisiones D2 a D8 (ver `PENDIENTES_REV05.md`) no se han cambiado.
