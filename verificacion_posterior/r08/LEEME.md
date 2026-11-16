# Pruebas R-08 (verificación independiente del solver)

`r08_pruebas.py` ejecuta 50 comprobaciones contra el código del repositorio: equilibrio de fuerzas y momentos, voladizo 3D en ambos ejes, rótulas, mecanismos, modelo girado y barra inclinada. Las pruebas que usan `REIMPLEMENTACION` prueban fórmulas con openseespy directo, no el programa.

## Cómo ejecutarlo

1. Ejecute el notebook con el ejecutor (`ejecutor/LEEME.md`) en dos carpetas: `trabajo/ejemplo` (planilla del caso gravitacional) y `trabajo/sismo` (planilla del caso sísmico de prueba, `casos_rev02/caso_sismo/planilla_sismo_ENTRADA.xlsx`).
2. Desde esta carpeta:

```bash
CARPETA_TRABAJO=/ruta/a/trabajo python3 r08_pruebas.py
```

Sale con código 0 solo si las 50 pruebas están OK.

## Resultado (`salida_r08.txt`)

50 pruebas: **50 OK, 0 FALLA**.

| prueba | resultado | qué comprueba |
|---|---|---|
| 1.x equilibrio de fuerzas y momentos (ejemplo y sismo, todos los estados) | OK | residuos de 10⁻¹⁰ o menos |
| 2.x voladizo 3D, eje fuerte y débil, axial | OK | coincide con PL³/3EI y PL/EA |
| 3.1 biapoyada con rótulas en ambos extremos | OK | el programa avisa **MODELO INESTABLE**: la torsión alrededor de la barra queda libre en ambos extremos |
| 3.3 empotrada-rotulada | OK | M = qL²/8 en el empotramiento, 0 en la rótula |
| 3.4 voladizo con rótula en la punta | OK | M = 0 en la punta, resuelto por el programa |
| 4.1 y 4.2 mecanismo con giro libre en la base | OK | el programa falla con error (antes entregaba desplazamientos de 10¹⁷ cm sin aviso) |
| 4.3 mecanismo con giro libre en la base y solo peso propio | OK | la comprobación de estabilidad lo marca inestable |
| 4.4 control estable | OK | coincide con la fórmula |
| 5.1 a 5.4 modelo girado 30° con ejes fuertes girados | OK | reacciones, esfuerzos y desplazamientos se transforman correctamente |
| 5.2 modelo girado con el eje fuerte de las columnas **sin girar** | OK (control) | los esfuerzos cambian: el resultado depende del eje dado en la planilla |
| 6.x barra inclinada, dos orientaciones | OK | flecha analítica y ejes locales |

## Cambios del solver en esta revisión

- **Eje fuerte obligatorio.** Cada barra debe tener EJE_FUERTE_X/Y/Z en la hoja BARRAS. Sin valor, la validación de la planilla muestra un error por barra y el modelo no se arma. Se eliminó la regla por defecto: el ejemplo tiene ahora el eje explícito de cada barra, con el mismo modelo que antes (0 celdas distintas).
- **Rótulas en el plano.** En un extremo rotulado el giro alrededor de la barra se transmite del nudo (igualdad exacta para barras alineadas con los ejes globales). Los giros en el plano quedan libres. Un nudo con una sola barra rotulada y sin otra conexión no tiene giro en el plano que definir, y se fija.
- **Barras rotuladas oblicuas.** Su restricción de giro es lineal y se impone por penalización (α = 10¹²): error relativo de ~10⁻⁷. Sin rótulas oblicuas el modelo usa la transformación exacta.
- **Aviso de inestabilidad.** Antes de resolver cualquier estado, el programa aplica una carga de prueba fija en cada nudo. Si los desplazamientos superan 10⁴ (cm o rad), el modelo se declara inestable e indica el nudo y el grado de libertad. Además, la captura del aviso del solver detecta matrices singulares: OpenSees devuelve código 0 en ese caso, por eso no basta con el código de retorno.

## Limitaciones conocidas

- Con barras rotuladas oblicuas, la restricción de penalización es una relación lineal entre giros que OpenSees no libera al cambiar de modelo en la misma sesión. Si una sesión mezcla un modelo con rótula oblicua y otro modelo distinto, reinicie el núcleo entre ambos. Esto no ocurre con rótulas alineadas.
- La prueba de estabilidad es una comprobación por carga de prueba: un mecanismo con rigidez residual pequeña pero no nula podría no superar el límite. La comprobación de rango de la matriz queda pendiente.
- No hay pruebas de marco 3D completo con rótulas en nodos compartidos, ni de viento (excluido en esta versión), ni de entradas faltantes o no finitas.
