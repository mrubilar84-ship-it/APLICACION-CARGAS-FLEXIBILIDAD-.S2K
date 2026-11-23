# Comparacion rev02 -> rev03 del caso gravitacional (ejemplo)

Mismo archivo de entrada de ejemplo en ambas revisiones (plantilla_soportes.xlsx de la raiz en la rev03); la rev03 usa la plantilla de la raiz del repositorio.

## Analisis (OpenSees)

| hoja | forma | diferencias numericas | diferencias de texto |
|---|---|---|---|
| REACCIONES | 24 x 10 | 0.000e+00 | 0 |
| NODOS | 72 x 9 | 0.000e+00 | 0 |
| BARRAS | 104 x 21 | 0.000e+00 | 0 |
| MAXIMOS_BARRAS | 104 x 17 | 0.000e+00 | 0 |

Conclusion: el analisis es identico entre rev02 y rev03 en las hojas comparadas. Los cambios estan en el diseno.

## Diseno: FU por barra (hoja RESULTADOS)

| ID | perfil | grupo | FU max rev02 | FU max rev03 | FU esbeltez local rev02 | FU esbeltez local rev03 | estado rev02 | estado rev03 |
|---|---|---|---|---|---|---|---|---|
| 1 | IR 10 × 49 | COLUMNA | 0.9772 | 0.7278 | 0.7278 | 0.7278 | CUMPLE | CUMPLE |
| 2 | IR 10 × 49 | COLUMNA | 0.9772 | 0.7278 | 0.7278 | 0.7278 | CUMPLE | CUMPLE |
| 3 | IR 10 × 49 | COLUMNA | 0.9772 | 0.7278 | 0.7278 | 0.7278 | CUMPLE | CUMPLE |
| 4 | IR 10 × 49 | COLUMNA | 0.9772 | 0.7278 | 0.7278 | 0.7278 | CUMPLE | CUMPLE |
| 5 | IR 10 × 49 | COLUMNA | 0.9772 | 0.7278 | 0.7278 | 0.7278 | CUMPLE | CUMPLE |
| 6 | IR 10 × 49 | COLUMNA | 0.9772 | 0.7278 | 0.7278 | 0.7278 | CUMPLE | CUMPLE |
| 7 | IR 10 × 49 | COLUMNA | 0.9772 | 0.7278 | 0.7278 | 0.7278 | CUMPLE | CUMPLE |
| 8 | IR 10 × 49 | COLUMNA | 0.9772 | 0.7278 | 0.7278 | 0.7278 | CUMPLE | CUMPLE |
| 9 | IR 10 × 49 | COLUMNA | 0.9772 | 0.7278 | 0.7278 | 0.7278 | CUMPLE | CUMPLE |
| 10 | IR 10 × 49 | COLUMNA | 0.9772 | 0.7278 | 0.7278 | 0.7278 | CUMPLE | CUMPLE |
| 11 | IR 10 × 49 | COLUMNA | 0.9772 | 0.7278 | 0.7278 | 0.7278 | CUMPLE | CUMPLE |
| 12 | IR 10 × 49 | COLUMNA | 0.9772 | 0.7278 | 0.7278 | 0.7278 | CUMPLE | CUMPLE |
| 13 | IR 12 × 16 | VIGA | 0.8236 | 0.3793 | 0.3793 | 0.3793 | CUMPLE | CUMPLE |
| 14 | IR 12 × 16 | VIGA | 0.8236 | 0.3793 | 0.3793 | 0.3793 | CUMPLE | CUMPLE |
| 15 | IR 12 × 16 | VIGA | 0.8236 | 1.4510 | 0.3793 | 1.4510 | CUMPLE | NO CUMPLE |
| 16 | IR 12 × 16 | VIGA | 0.8236 | 1.4510 | 0.3793 | 1.4510 | CUMPLE | NO CUMPLE |
| 17 | IR 12 × 16 | VIGA | 0.8236 | 0.3793 | 0.3793 | 0.3793 | CUMPLE | CUMPLE |
| 18 | IR 12 × 16 | VIGA | 0.8236 | 0.3793 | 0.3793 | 0.3793 | CUMPLE | CUMPLE |
| 19 | IR 12 × 16 | VIGA | 0.8236 | 1.4510 | 0.3793 | 1.4510 | CUMPLE | NO CUMPLE |
| 20 | IR 12 × 16 | VIGA | 0.8236 | 1.4510 | 0.3793 | 1.4510 | CUMPLE | NO CUMPLE |
| 21 | IR 12 × 16 | VIGA | 0.8236 | 0.3793 | 0.3793 | 0.3793 | CUMPLE | CUMPLE |
| 22 | IR 12 × 16 | VIGA | 0.8236 | 1.4510 | 0.3793 | 1.4510 | CUMPLE | NO CUMPLE |
| 23 | IR 12 × 16 | VIGA | 0.8236 | 0.3793 | 0.3793 | 0.3793 | CUMPLE | CUMPLE |
| 24 | IR 12 × 16 | VIGA | 0.8236 | 1.4510 | 0.3793 | 1.4510 | CUMPLE | NO CUMPLE |
| 25 | IR 12 × 16 | VIGA | 0.8236 | 0.3793 | 0.3793 | 0.3793 | CUMPLE | CUMPLE |
| 26 | IR 12 × 16 | VIGA | 0.8236 | 1.4510 | 0.3793 | 1.4510 | CUMPLE | NO CUMPLE |

Nota: rev02 calculaba el FU de ductilidad (NTC) y lo sumaba al FU maximo; rev03 no lo calcula (decision del usuario, sin NTC). La columna de esbeltez local de las vigas cambia porque rev03 aplica el limite de compresion a cualquier miembro con compresion en alguna combinacion (ver H-06 en RESPUESTA_AUDITORIA_REV03.md).
