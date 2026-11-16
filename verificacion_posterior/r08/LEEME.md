# Pruebas R-08 (verificación independiente del solver)

`r08_pruebas.py` ejecuta 50 comprobaciones contra el código del repositorio: equilibrio de fuerzas y momentos, voladizo 3D en ambos ejes, rótulas, mecanismos, modelo girado y barra inclinada. Las comprobaciones de rótulas que usan `REIMPLEMENTACION` prueban fórmulas con openseespy directo, no el programa.

## Cómo ejecutarlo

1. Ejecute el notebook con el ejecutor (`ejecutor/LEEME.md`) en dos carpetas: `trabajo/ejemplo` (planilla del caso gravitacional) y `trabajo/sismo` (planilla del caso sísmico de prueba).
2. Desde esta carpeta:

```bash
CARPETA_TRABAJO=/ruta/a/trabajo python3 r08_pruebas.py
```

Sale con código 0 solo si las 50 pruebas están OK.

## Resultado (corrida del 16-nov-2026, `salida_r08.txt`)

50 pruebas: **46 OK, 4 FALLA**.

| prueba | resultado | clasificación |
|---|---|---|
| 1.x equilibrio de fuerzas y momentos (ejemplo y sismo, todos los estados) | OK | residuos de 10⁻¹⁰ o menos |
| 2.x voladizo 3D, eje fuerte y débil, axial | OK | coincide con PL³/3EI y PL/EA |
| 3.1 viga biapoyada con rótulas en ambos extremos | FALLA | el programa no resuelve: la torsión alrededor de la barra queda libre en ambos extremos, es un mecanismo. El error es correcto, pero el mensaje debería decirlo. |
| 3.3 empotrada-rotulada | OK | M = qL²/8 en el empotramiento, 0 en la rótula |
| 3.4 voladizo con rótula en la punta | FALLA | el programa no resuelve. Causa probable (no comprobada en detalle): el nodo original del extremo rotulado queda con giros sin ningún elemento que los sujete. Propuesta: fijar esos giros cuando el nodo no tiene otra barra. |
| 4.1 y 4.2 mecanismo con giro libre en la base | **corregido** | antes el programa entregaba desplazamientos de 10¹⁷ cm sin aviso. Ahora falla por la guarda de equilibrio (residuo mayor que 10⁻⁶ de la carga). |
| 4.3 mecanismo por giro libre en la base con solo peso propio | FALLA (pendiente) | la guarda no lo detecta porque el equilibrio sí se cumple. Hace falta detectar modos de cuerpo rígido (rango de la matriz). |
| 5.1 a 5.4 modelo girado 30° | OK, salvo 5.2 | |
| 5.2 modelo girado con el eje fuerte de columnas por defecto | FALLA | no es un error numérico: el eje fuerte por defecto de las columnas queda fijo en Y global, así que al girar el modelo cambian los esfuerzos (≈39 %). Propuesta: exigir la marca EJE_FUERTE en columnas o advertirlo. |
| 6.x barra inclinada, dos orientaciones | OK | |

## Cambio en el código en esta revisión

- `analisis_opensees.py`, `_resolver`: después de resolver, las reacciones deben equilibrar las cargas aplicadas y el peso propio con tolerancia 10⁻⁶ relativa. Si no, falla con `ErrorAnalisis`. Verificado: los casos gravitacional y sísmico no cambian (0 celdas distintas) y los casos de mecanismo 4.1 y 4.2 ahora fallan.
- En la corrida anterior, la prueba 5.4b daba un error relativo de 1,1·10⁻⁸ en el caso sísmico girado; ahora da 1,6·10⁻¹³. Hipótesis: el máximo interior muestreado con 401 puntos, reemplazado por la forma cerrada. No comprobado directamente.

## Lo que estas pruebas no cubren

- Marco 3D completo con rótulas en nodos compartidos.
- Pandeo, tracción, flexión y cambios de rama de las ecuaciones de diseño (esto corresponde a otras pruebas de R-08).
- Entradas faltantes o no finitas (validación de datos).
