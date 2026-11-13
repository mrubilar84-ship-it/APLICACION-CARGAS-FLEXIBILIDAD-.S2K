# Comparacion rev00 (recibida) contra rev01 (corregida)

Mismas entradas en ambas versiones. Se comparan todas las hojas de diseno_asd.xlsx y resultados_soportes.xlsx, y todo el texto de memoria_calculo.html.

## Lineas base rev00 usadas

- **Entregada (auditoria/ejemplo):** salidas del caso gravitacional tal como se entregaron en rev00.
- **Reejecucion limpia de rev00:** soportes_planilla.ipynb de la version committed en HEAD antes de esta revision (c920894), ejecutado con el mismo ejecutor y las mismas entradas (SHA-256 9ef07e79…, gravitacional; 1e1da780…, sismo). Se usa para el caso sismo porque la carpeta prueba/sismo3 de la sesion anterior no tiene los mismos modulos (3 de 4 modulos difieren byte a byte de auditoria/codigo/modulos).

## Caso gravitacional: entregada rev00 frente a rev01

### diseno_asd.xlsx

| hoja | filas rev00 | filas rev01 | celdas comparadas | celdas distintas |
|---|---|---|---|---|
| RESUMEN | 8 | 8 | 16 | 0 |
| CAPACIDADES | 27 | 27 | 760 | 0 |
| RESULTADOS | 27 | 27 | 514 | 0 |
| DETALLE | 53 | 53 | 741 | 0 |
| LISTAS_GRUPO | 329 | 329 | 2869 | 0 |

### resultados_soportes.xlsx

| hoja | filas rev00 | filas rev01 | celdas comparadas | celdas distintas |
|---|---|---|---|---|
| RESUMEN | 15 | 15 | 30 | 0 |
| BARRAS | 105 | 105 | 1995 | 0 |
| NODOS | 73 | 73 | 657 | 0 |
| REACCIONES | 25 | 25 | 250 | 0 |
| MAXIMOS_BARRAS | 105 | 105 | 1785 | 0 |
| DEFORMADA | 73 | 73 | 1095 | 0 |

### memoria_calculo.html

- Filas de la tabla 6.4 (flechas): rev00 14, rev01 14. Filas con cambio: 2.
- Lineas de texto distintas fuera de la tabla 6.4: 0.

| barra | fila rev00 (barra, perfil, L cm, flecha mm, combinacion, x/L, limite mm, estado) | fila rev01 |
|---|---|---|
| 14 | 14 / IR 12 × 16 / 500.0 / 0.05 / ASD1 / 0.53 / 16.67 / CUMPLE | 14 / IR 12 × 16 / 500.0 / 0.05 / ASD1 / 0.52 / 16.67 / CUMPLE |
| 18 | 18 / IR 12 × 16 / 500.0 / 0.05 / ASD1 / 0.53 / 16.67 / CUMPLE | 18 / IR 12 × 16 / 500.0 / 0.05 / ASD1 / 0.52 / 16.67 / CUMPLE |

## Caso gravitacional: reejecucion limpia de rev00 frente a rev01

### diseno_asd.xlsx

| hoja | filas rev00 | filas rev01 | celdas comparadas | celdas distintas |
|---|---|---|---|---|
| RESUMEN | 8 | 8 | 16 | 0 |
| CAPACIDADES | 27 | 27 | 760 | 0 |
| RESULTADOS | 27 | 27 | 514 | 0 |
| DETALLE | 53 | 53 | 741 | 0 |
| LISTAS_GRUPO | 329 | 329 | 2869 | 0 |

### resultados_soportes.xlsx

| hoja | filas rev00 | filas rev01 | celdas comparadas | celdas distintas |
|---|---|---|---|---|
| RESUMEN | 15 | 15 | 30 | 0 |
| BARRAS | 105 | 105 | 1995 | 0 |
| NODOS | 73 | 73 | 657 | 0 |
| REACCIONES | 25 | 25 | 250 | 0 |
| MAXIMOS_BARRAS | 105 | 105 | 1785 | 0 |
| DEFORMADA | 73 | 73 | 1095 | 0 |

### memoria_calculo.html

- Filas de la tabla 6.4 (flechas): rev00 14, rev01 14. Filas con cambio: 2.
- Lineas de texto distintas fuera de la tabla 6.4: 0.

| barra | fila rev00 (barra, perfil, L cm, flecha mm, combinacion, x/L, limite mm, estado) | fila rev01 |
|---|---|---|
| 14 | 14 / IR 12 × 16 / 500.0 / 0.05 / ASD1 / 0.53 / 16.67 / CUMPLE | 14 / IR 12 × 16 / 500.0 / 0.05 / ASD1 / 0.52 / 16.67 / CUMPLE |
| 18 | 18 / IR 12 × 16 / 500.0 / 0.05 / ASD1 / 0.53 / 16.67 / CUMPLE | 18 / IR 12 × 16 / 500.0 / 0.05 / ASD1 / 0.52 / 16.67 / CUMPLE |

## Caso sismo: reejecucion limpia de rev00 frente a rev01

### diseno_asd.xlsx

| hoja | filas rev00 | filas rev01 | celdas comparadas | celdas distintas |
|---|---|---|---|---|
| RESUMEN | 8 | 8 | 16 | 0 |
| CAPACIDADES | 27 | 27 | 760 | 0 |
| RESULTADOS | 27 | 27 | 514 | 0 |
| DETALLE | 79 | 79 | 1103 | 0 |
| LISTAS_GRUPO | 329 | 329 | 2869 | 0 |

### resultados_soportes.xlsx

| hoja | filas rev00 | filas rev01 | celdas comparadas | celdas distintas |
|---|---|---|---|---|
| RESUMEN | 18 | 18 | 36 | 0 |
| BARRAS | 157 | 157 | 2983 | 0 |
| NODOS | 109 | 109 | 981 | 0 |
| REACCIONES | 37 | 37 | 370 | 0 |
| MAXIMOS_BARRAS | 157 | 157 | 2669 | 0 |
| DEFORMADA | 109 | 109 | 1635 | 0 |

### memoria_calculo.html

- Filas de la tabla 6.4 (flechas): rev00 14, rev01 14. Filas con cambio: 2.
- Lineas de texto distintas fuera de la tabla 6.4: 0.

| barra | fila rev00 (barra, perfil, L cm, flecha mm, combinacion, x/L, limite mm, estado) | fila rev01 |
|---|---|---|
| 14 | 14 / IR 12 × 16 / 500.0 / 0.05 / ASD1 / 0.53 / 16.67 / CUMPLE | 14 / IR 12 × 16 / 500.0 / 0.05 / ASD1 / 0.52 / 16.67 / CUMPLE |
| 18 | 18 / IR 12 × 16 / 500.0 / 0.05 / ASD1 / 0.53 / 16.67 / CUMPLE | 18 / IR 12 × 16 / 500.0 / 0.05 / ASD1 / 0.52 / 16.67 / CUMPLE |

## Lectura

- En ninguna hoja de los dos Excel de resultados hay celdas distintas, en ninguno de los casos ni en las dos lineas base.
- La unica diferencia de la memoria es la posicion x/L del maximo de flecha en las filas que se listan arriba. El valor en mm se muestra con dos decimales y no cambia en esa resolucion, por lo que la diferencia es menor que 0,01 mm.
- Esa diferencia viene de H-02: solo cambia cuando los extremos de la barra tienen desplazamiento vertical distinto (por deformacion del marco).
- H-01 no cambia ningun resultado de estos dos casos: en ambos, los momentos de extremo son mayores que el maximo interior. El efecto de H-01 se muestra en las pruebas aisladas (pruebas/test_rev01.py y pruebas/prueba_inicial_salida.txt).

