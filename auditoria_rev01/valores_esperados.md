# Valores esperados: caso gravitacional y caso sismo (revision 01)

Tabla pedida en R-03. Cada magnitud indica si el valor sale del propio programa (OpenSees y calculos del codigo) o si tiene una comprobacion independiente calculada desde la entrada.

## Tolerancias propuestas por el agente

No fijadas por el auditor. Son propuestas para cerrar la comparacion:

| magnitud | tolerancia propuesta |
|---|---|
| reacciones y esfuerzos (kgf, kgf·m) | 0,01 (resolucion de los Excel) |
| equilibrio global (kgf) | 0,01 |
| desplazamientos y flechas (mm) | 0,01 (resolucion de la memoria) |
| FU | 0,001 (tres decimales) |
| distorsiones | igualdad del cociente con dos cifras |

## A. Caso gravitacional (ejemplo)

Entrada: plantilla_soportes.xlsx, SHA-256 9ef07e799565b748f42f5b81ff96f6e7764104b7e1f4f8216acdd570820d26d8. Estados: Peso propio y muerta (D, con peso propio), Sobrecarga (L, sin peso propio). Combinaciones: ASD1 = 1·D; ASD2 = 1·D + 1·L. Viento excluido.

### A1. Reacciones (combinacion ASD1, kgf; FZ positiva hacia arriba)

| nodo | FX | FY | FZ | origen |
|---|---|---|---|---|
| 1 | 6.1007 | 4.2278 | 2216.9449 | programa |
| 4 | 6.1007 | -4.2278 | 2216.9449 | programa |
| 7 | -0.0000 | 4.2278 | 2361.8103 | programa |
| 10 | 0.0000 | -4.2278 | 2361.8103 | programa |
| 13 | -6.1007 | 4.2278 | 2216.9449 | programa |
| 16 | -6.1007 | -4.2278 | 2216.9449 | programa |

- Suma FZ de reacciones (programa): **13591.4000 kgf**.
- Comprobacion independiente: peso propio = Σ masa(kg/m) × longitud(m) de las 26 barras, con masa de la base Gerdau del codigo = **4591.4000 kgf**; carga nodal de D = 6 × 1500 = 9000 kgf; total esperado = **13591.4000 kgf**.
- Residuo: **1.82e-12 kgf** (dentro de la tolerancia 0,01 kgf). Suma FX = -3.14e-13 kgf; suma FY = -1.01e-12 kgf (equilibrio horizontal, programa).

### A2. Desplazamientos maximos por combinacion (memoria 6.1, mm)

Programa. Sin comprobacion independiente en esta revision.

| combinacion | UX max | UY max | UZ max | resultante max | nodo |
|---|---|---|---|---|---|
| ASD1 | 0.00 | 0.00 | 0.07 | 0.07 | 12 |
| ASD2 | 0.00 | 0.00 | 0.07 | 0.07 | 12 |

- Desplazamiento máximo: 0.07 mm en el nodo 12, combinación ASD1 (controla).

### A3. FU gobernante

- Programa (hoja RESULTADOS de diseno_asd.xlsx, columna "FU MAXIMO"): **FU = 0.9772**; barra 1 (COLUMNA, perfil IR 10 × 49, material A-572 G 50); caso que gobierna: (ductilidad).
- Consistencia: coincide con el FU 0,977 de la barra 1 en la memoria (seccion 7).
- Comprobacion independiente: no realizada. Pendiente: calcular a mano esta barra con AISC 360-22 ASD.

### A4. Distorsion horizontal de entrepiso (memoria 6.2, NTC-CA §4.1.1 b)

Programa. Comprobacion independiente: el limite h/250 con h = 350 cm da 14,00 mm, que coincide con la columna de limite.

| combinacion | casos | distorsion | nivel | h (cm) | desplazamiento (mm) | limite (mm) | estado |
|---|---|---|---|---|---|---|---|
| ASD1 | Solo D y L | 1 / 1,550,938 | 2 | 350.0 | 0.00 | 14.00 | CUMPLE |
| ASD2 | Solo D y L | 1 / 1,550,938 | 2 | 350.0 | 0.00 | 14.00 | CUMPLE |

### A5. Flechas verticales de vigas (memoria 6.4)

- Programa: flecha maxima **0.06 mm** en la barra 15 (IR 12 × 16, L = 500.0 cm), combinacion ASD1, x/L = 0.46; limite L/300 = 16.67 mm; estado CUMPLE. Las 14 vigas de la tabla cumplen.
- Comprobacion independiente: no realizada para este modelo. La formula de viga simplemente apoyada con peso propio (flecha = 5qL⁴/384EI) se comprueba en pruebas/test_flecha_rev01.py (-0,0827 cm para L = 600 cm, q = 0,2 kgf/cm).

### A6. Esfuerzos de extremo, barras 1 y 13 (hoja MAXIMOS_BARRAS de resultados_soportes.xlsx, combinaciones)

Programa. Maximo y minimo de cada esfuerzo entre los extremos I y J. Los maximos interiores por peso propio no estan en esta hoja: estan en las columnas "MZ MAX EN EL TRAMO (kgf·m)" y "MY MAX EN EL TRAMO (kgf·m)" de la hoja BARRAS (H-01).

| CASO | TIPO | BARRA | ELEMENTO | PERFIL | N MAX (kgf) | N MIN (kgf) | Vy MAX (kgf) | Vy MIN (kgf) | Vz MAX (kgf) | Vz MIN (kgf) | T MAX (kgf·m) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ASD1 | COMBINACION | 1 | COLUMNA | IR 10 × 49 | 2216.9449 | -1961.7949 | 4.2278 | -4.2278 | 6.1007 | -6.1007 | 0.0000 |
| ASD1 | COMBINACION | 13 | VIGA | IR 12 × 16 | 10.1272 | -10.1272 | 62.7236 | 56.7764 | 0.0000 | -0.0000 | 0.0000 |
| ASD2 | COMBINACION | 1 | COLUMNA | IR 10 × 49 | 2216.9449 | -1961.7949 | 4.2278 | -4.2278 | 6.1007 | -6.1007 | 0.0000 |
| ASD2 | COMBINACION | 13 | VIGA | IR 12 × 16 | 10.1272 | -10.1272 | 62.7236 | 56.7764 | 0.0000 | -0.0000 | 0.0000 |

## B. Caso sismo (cargas de prueba, no un calculo sismico)

Entrada: planilla_sismo_ENTRADA_DE_PRUEBA.xlsx, SHA-256 1e1da780bff79b144323db872d6095b5847f030da59220c89d0dbab8d8e4ce6b. Estados: Peso propio y muerta (D), Sobrecarga (L), Viento X (W, excluido), Sismo X (E, prueba). Las cargas E son arbitrarias: no provienen de un calculo sismico (R-06).

### B1. Cargas aplicadas (estado Sismo X, kgf)

| nodo | FX | FY | FZ |
|---|---|---|---|
| 3 | 1000 | 0 | 0 |
| 6 | 1000 | 0 | 0 |

### B2. Reacciones del estado Sismo X (kgf)

| nodo | FX | FY | FZ | origen |
|---|---|---|---|---|
| 1 | -297.9303 | -0.0000 | -478.4260 | programa |
| 4 | -297.9303 | -0.0000 | -478.4260 | programa |
| 7 | -400.6789 | -0.0000 | 5.3832 | programa |
| 10 | -400.6789 | -0.0000 | 5.3832 | programa |
| 13 | -301.3909 | 0.0000 | 473.0428 | programa |
| 16 | -301.3909 | 0.0000 | 473.0428 | programa |

- Comprobacion independiente de equilibrio horizontal: Σ FX cargas aplicadas = 2000.0000 kgf; Σ FX reacciones = -2000.0000 kgf; residuo = 3.07e-11 kgf (las reacciones se oponen a la carga).
- Cortante de piso: el programa reporta V = 2 000 kgf en ambos entrepisos (memoria 6.3). Es igual a la suma de cargas aplicadas por encima, porque todas estan en el nivel superior (z = 7 m). Comprobacion independiente: coincide.

### B3. Distorsion por sismo (memoria 6.3, tabla 4.3.2 con Q = 3: LDNE 0,004; OI 0,0075; SV 0,020)

Programa. Sin comprobacion independiente de Ks, δ ni T en esta revision (pendiente).

| columna | estado sismico que controla | h (cm) | δ elastica (mm) | δ/h | LDNE | ocupacion inmediata | seguridad de vida |
|---|---|---|---|---|---|---|---|
| 1 | Sismo X | 350.0 | 16.63 | 1 / 211 | NO CUMPLE (γ 0.0040)Ks·δ/h = 0.00475 | CUMPLE (γ 0.0075) | CUMPLE (γ 0.0200) |
| 2 | Sismo X | 350.0 | 22.15 | 1 / 158 | NO CUMPLE (γ 0.0040)Ks·δ/h = 0.00633 | CUMPLE (γ 0.0075) | CUMPLE (γ 0.0200) |
| 3 | Sismo X | 350.0 | 16.63 | 1 / 211 | NO CUMPLE (γ 0.0040)Ks·δ/h = 0.00475 | CUMPLE (γ 0.0075) | CUMPLE (γ 0.0200) |

- Periodo aproximado (§6.4.1, programa): **T = 0.376 s** (sin comprobacion independiente en esta revision).

Nota: el resultado NO CUMPLE en LDNE es consecuencia de las cargas de prueba; no es una conclusion de diseno.

