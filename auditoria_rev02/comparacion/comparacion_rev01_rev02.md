# Comparacion rev01 (entregada) contra rev02 (actual)

rev01: auditoria_rev01/ (salidas de la revision 01). rev02: auditoria_rev02/ (salidas de la ejecucion del notebook actual, commit 1816de4).
Celdas: se compara cada celda con valor en ambos libros (valores numericos con tolerancia relativa 1e-9).

## Ejemplo gravitacional

| archivo | hoja | celdas comparadas | celdas distintas |
|---|---|---|---|
| diseno_asd.xlsx | RESUMEN | 16 | 1 |
| diseno_asd.xlsx | CAPACIDADES | 760 | 0 |
| diseno_asd.xlsx | RESULTADOS | 514 | 0 |
| diseno_asd.xlsx | DETALLE | 741 | 0 |
| diseno_asd.xlsx | LISTAS_GRUPO | 2869 | 0 |
| resultados_soportes.xlsx | RESUMEN | 30 | 1 |
| resultados_soportes.xlsx | BARRAS | 2205 | 0 |
| resultados_soportes.xlsx | NODOS | 657 | 0 |
| resultados_soportes.xlsx | REACCIONES | 250 | 0 |
| resultados_soportes.xlsx | MAXIMOS_BARRAS | 1785 | 0 |
| resultados_soportes.xlsx | DEFORMADA | 1095 | 0 |

Memoria: 4 lineas de texto distintas (lineas que empiezan por - son de rev01; + de rev02).

- `-Perfiles CS (barras macizas) y LM quedan fuera del diseño.`
- `+Perfiles macizos (CS, OS, SOL) eliminados de la base; LM no se incluye.`
- `+Catálogo Gerdau rev04, pág. impresa 27.`
- `+Catálogo Gerdau rev04, pág. impresa 27.`

## Caso sismo

| archivo | hoja | celdas comparadas | celdas distintas |
|---|---|---|---|
| diseno_asd.xlsx | RESUMEN | 16 | 1 |
| diseno_asd.xlsx | CAPACIDADES | 760 | 0 |
| diseno_asd.xlsx | RESULTADOS | 514 | 0 |
| diseno_asd.xlsx | DETALLE | 1103 | 0 |
| diseno_asd.xlsx | LISTAS_GRUPO | 2869 | 0 |
| resultados_soportes.xlsx | RESUMEN | 36 | 1 |
| resultados_soportes.xlsx | BARRAS | 3297 | 0 |
| resultados_soportes.xlsx | NODOS | 981 | 0 |
| resultados_soportes.xlsx | REACCIONES | 370 | 0 |
| resultados_soportes.xlsx | MAXIMOS_BARRAS | 2669 | 0 |
| resultados_soportes.xlsx | DEFORMADA | 1635 | 0 |

Memoria: 4 lineas de texto distintas (lineas que empiezan por - son de rev01; + de rev02).

- `-Perfiles CS (barras macizas) y LM quedan fuera del diseño.`
- `+Perfiles macizos (CS, OS, SOL) eliminados de la base; LM no se incluye.`
- `+Catálogo Gerdau rev04, pág. impresa 27.`
- `+Catálogo Gerdau rev04, pág. impresa 27.`

