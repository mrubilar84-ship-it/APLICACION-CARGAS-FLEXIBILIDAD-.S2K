# Paquete de auditoría: aplicación de diseño de soportes de acero

Versión del paquete: generada desde la rama `claude/eloquent-turing-cwpcd8` (ver `codigo/` y `plantilla/`).

Este documento es el punto de entrada para un agente o ingeniero que vaya a **auditar** la aplicación. Describe qué hace el cálculo, qué normas aplica, qué supuestos y decisiones se tomaron, qué se verificó y qué queda abierto. No sustituye la revisión del ingeniero responsable: sus comentarios son insumo para esa revisión.

---

## 0. Alcance y uso previsto

- **Qué calcula:** soportes de acero (marcos y elementos de piping y similares) a partir de una planilla Excel. Análisis lineal 3D con OpenSees (openseespy), verificación de elementos por AISC 360-22 (ASD) y verificaciones de esbeltez, ductilidad, flecha, distorsión y sismo según la NTC para México. Genera una memoria de cálculo en HTML imprimible.
- **Normas de referencia:**
  - AISC 360-22 (diseño por resistencia en ASD).
  - NTC para el Diseño y Construcción de Estructuras de Acero, CDMX 2020 (esbelteces, ductilidad, flecha).
  - NTC Criterios y Acciones (§4.1.1, desplazamientos).
  - NTC para el Diseño por Sismo 2023 (método estático, niveles de desempeño, distorsiones).
- **Restricciones de esta versión:**
  - Se usa **solo análisis estático** (no hay modal espectral en la aplicación).
  - **No se considera viento.**
  - Para el diseño **solo aplica el sismo** (con las combinaciones que defina el usuario).
- **Estado:** funcional y probada con casos de ejemplo. No está aprobada para un proyecto real. Cualquier uso productivo exige revisión profesional.

---

## 0.2 Decisiones abiertas (considerarlas en la auditoría)

Estas decisiones se tomaron para poder avanzar, pero **no están cerradas**. Cada una aparece en el código con un comentario `DECISION Dn (abierta)` en la línea donde se aplica. El auditor debe evaluarlas y decir si las acepta, las cambia o las considera incorrectas. Son independientes de los errores de programa que pueda encontrar.

| ID | Decisión actual | Alternativas | Dónde está (archivo, función o hoja) | Qué debe evaluar el auditor |
|---|---|---|---|---|
| D1 | Flecha límite **L/300**, justificada con el Comentario L2 de AISC 360-22 (pág. 16.1-543). La NTC no fija número. | L/240, L/360 (carga viva) o un límite por tipo de estructura. | NORMA `FLECHA_DIVISOR`; `flechas_vigas`; memoria 6.4. | ¿La justificación basta para un proyecto en México? ¿Qué límite exige el proyecto? |
| D2 | La flecha se evalúa con la **combinación gravitacional total** (D y L). | Solo carga viva, o total con otro límite. | `analisis_opensees.flechas_vigas` (filtro de clase gravitacional). | ¿Qué combinación corresponde a flecha según la norma y el criterio del proyecto? |
| D3 | Distorsión NTC-CA **h/250**, porque no hay elementos no estructurales frágiles unidos. Se revisa por la columna que controla y solo en combinaciones gravitacionales. | h/500 si hay frágiles unidos. | PARAMETROS `FRAGILES`; memoria 6.2. | ¿La interpretación de "frágiles unidos" es correcta? ¿La columna que controla es la forma adecuada de reportar? |
| D4 | **Kz** de pandeo torsional: lista 1.0 o 0.5 (AISC E4), elegida por el usuario. | Kz calculado según las condiciones de extremo. | PARAMETROS `KZ_TORSION`; `pn_compresion`. | ¿Qué significa cada opción? ¿Debe calcularse y no elegirse? |
| D5 | La carga sísmica de la planilla es **diseño para Seguridad de Vida**, reducido por Q′R′. Distorsión elástica = f × planilla, con f = Q′R para LDNE y OI, y f = QR para SV. | Carga sin reducir (f = 1), o reducida solo por Q. | memoria 6.3 (`_seccion_sismo`). | ¿La interpretación de §1.7 y §6.3 es correcta? Impacto en el resultado de LDNE. |
| D6 | **Q′ = Q**, es decir k = 1 del SASID. | k del SASID: Q′ = 1 + (Q − 1)/k. | `parametros.resolver`; PARAMETROS `K_SASID`. | ¿Qué k corresponde al sitio? Verificar la ecuación 3.2.1 contra el PDF. |
| D7 | **Ks = 1** (conservador) para LDNE. | Ks por zona: 1/6 (A), 1/[6 − 4(Ts − 0.5)] (B), 1/4 (C). | PARAMETROS `KS_METODO`. | ¿Es aceptable el conservadurismo? Verificar la ecuación 3.1.1. |
| D8 | **k2** = 0.5(1 − (T/Ta)²) con el **periodo menor** de los estados sísmicos, calculado con §6.4.1. | Otro método de periodo que no sea modal. | memoria 6.3; `parametros.k2_de_T`; `_periodo`. | ¿El periodo de §6.4.1 con las fuerzas de la planilla es válido? Verificar la forma de la fórmula. |
| D9 | **Segundo orden**: 0.08·V/W, con V el cortante del sismo y W la carga D sin factor más el peso propio de las barras encima. Se compara con la mayor distorsión elástica o SV del entrepiso. | Análisis P-Δ explícito. | memoria 6.3. | ¿Está bien aplicado el criterio? ¿W debe incluir sobrecarga o no? |
| D10 | `DEFORMABLES = SÍ` (LDNE 0.004), porque el proyecto no tiene elementos frágiles. | `DEFORMABLES = NO` (0.002). | PARAMETROS `DEFORMABLES`. | ¿"No hay frágiles" implica "deformables o separados" (NTC 1.7)? |
| D11 | Combinaciones de **servicio ASD**. Los factores los define el usuario en COMBINACIONES. Las combinaciones con E entran al diseño. | Combinaciones LRFD o las que indique la norma. | hoja COMBINACIONES; `diseno_asd`. | ¿Son suficientes? ¿Qué factores de sismo exige la norma para ASD? |
| D12 | **Análisis lineal de primer orden**, sin P-Δ. | Análisis de segundo orden. | `analisis_opensees`. | ¿Afecta de forma relevante con las cargas y esbelteces del proyecto? |
| D13 | **Viento fuera de esta versión**: no se resuelven estados ni combinaciones W. | Incluir viento para información. | `analisis_opensees.correr`. | ¿Es aceptable para el uso previsto? |
| D14 | Ángulos con b/t > 0.71√(E/Fy): E4 flexotorsional **no implementado**; la barra queda NO REVISADO. | Implementar E4 para ángulos. | `diseno_asd` (motivo). | ¿Cuántas barras típicas quedarían NO REVISADO? |
| D15 | Sistemas sísmicos: **solo marcos de acero** (tabla 4.3.2, 3 filas). | Contraventeos, sistemas duales y otros de la tabla. | hoja NORMA (SISTEMAS). | ¿Cuáles agregar en la primera versión? |
| D16 | Propiedades faltantes en la base Gerdau: la barra queda **NO REVISADO**, sin estimar. | Error que detiene el diseño. | `diseno_asd._props_asd`. | ¿Qué prefiere el proyecto? |
| D17 | **LX, LY, LB, KX, KY y CB obligatorios** en LONGITUDES, sin valores por defecto. | Valores por defecto con marca (longitud de la barra, K = 1). | `celda7` (`validar_datos_diseno`). | ¿Es aceptable la carga de datos? ¿K y Cb deben calcularse en otra versión? |
| D18 | **Resistencia por AISC 360-22 ASD**; NTC-Acero para esbelteces y ductilidad. | Diseño completo por NTC-Acero. | `diseno_asd`. | ¿Es correcta esta combinación de criterios normativos? |
| D19 | **DUCTILIDAD obligatoria** solo en COLUMNA y VIGA. | Obligatoria en todas las barras. | `celda7` (`validar_datos_diseno`). | ¿Es suficiente? |
| D20 | Candidatos LI sin LI CONEXION o LI LONGITUD CONEXION: quedan **NO REVISADO**. | Error. | `diseno_asd` (matriz de FU). | ¿Es aceptable para la lista de perfiles? |

---

## 1. Contenido del paquete

| Ruta | Qué es |
|---|---|
| `AUDITORIA_SOPORTES.md` | Este documento. |
| `codigo/modulos/*.py` | Módulos Python tal como los escribe el notebook (`%%writefile`). Son la fuente del cálculo. |
| `codigo/bloques/celda_NN.py` | Celdas de ejecución del notebook (lectura, validación, análisis, diseño, memoria). |
| `codigo/INDICE_DE_CELDAS.md` | Índice de celdas con el bloque al que pertenecen. |
| `codigo/mapa_de_codigo.md` | Funciones y clases por módulo, con línea y propósito. Generado con AST. |
| `referencias/referencias_normativas.md` | Extractos del texto de cada norma usado por el código, con archivo y líneas de origen. |
| `pruebas/test_flecha.py` | Prueba de la fórmula de flecha de vigas contra un modelo subdividido en OpenSees y contra la fórmula analítica. |
| `plantilla/plantilla_soportes.xlsx` | Plantilla Excel de entrada (hojas INSTRUCCIONES, NODOS, BARRAS, LONGITUDES, ESTADOS, MATERIALES, COMBINACIONES, CARGAS, **PARAMETROS**, **NORMA**, entre otras). |
| `ejemplo/memoria_calculo.html` | Memoria generada con la planilla de ejemplo. |
| `ejemplo/resultados_soportes.xlsx`, `ejemplo/diseno_asd.xlsx` | Resultados del análisis y del diseño de ejemplo. |
| `ejemplo/ejecucion.log` | Registro de la ejecución de ejemplo. |

**Nota sobre el origen del código:** el código de `codigo/modulos` es el que el notebook `soportes_planilla.ipynb` escribe y ejecuta. El notebook incluye además la plantilla en base64 (no se copia aquí). Los datos de perfiles (`gerdau_datos.py`) son la base Gerdau rev04 en texto.

---

## 2. Cómo verificar el paquete

1. **Prueba de flexión de vigas (independiente del notebook):**
   ```bash
   cd auditoria/pruebas && python3 test_flecha.py
   ```
   Debe terminar con `RESULTADO: OK`. Requiere `openseespy`, `numpy` y los módulos de `codigo/modulos`.
2. **Ejecución completa:** el notebook está pensado para Kaggle. Sube la planilla (partiendo de `plantilla/plantilla_soportes.xlsx`) y ejecuta los bloques 1 a 11 en orden. La celda de OpenSees se instala sola si falta.
3. **Comparación de salidas:** compare `ejemplo/memoria_calculo.html` con la memoria que produzca el notebook con la misma planilla.

---

## 3. Flujo de cálculo

| Bloque | Función | Módulos principales |
|---|---|---|
| 1 a 4 | Motor de dibujo, base Gerdau (247 perfiles), orientación de ejes | `dibujo_directo.py`, `gerdau_datos.py`, `perfiles_gerdau.py`, `orientacion_gerdau.py` |
| 6 | Crear o cargar la plantilla Excel (incluye PARAMETROS y NORMA) | celda `6`, `celda6_plantilla.py` |
| 7 | Leer y validar la planilla. Un ERROR detiene el modelo. Lee PARAMETROS y NORMA | `celda7_validar.py`, `parametros.py` |
| 8 | Dibujo de revisión y planilla regenerada | `vista3d_plotly.py` |
| 9 | Análisis lineal con OpenSees y resultados (barras, nodos, reacciones, deformada, equilibrio) | `analisis_opensees.py` |
| 10 | Diseño ASD por barra y por grupo; FU; listas desplegables de perfiles | `diseno_asd.py`, `diseno_ntc.py` |
| 11 | Memoria de cálculo HTML | `memoria_asd.py` |

**Modelo de análisis:**
- Elementos `elasticBeamColumn` 3D, con transformación lineal (`geomTransf Linear`). El eje fuerte se define con `vecxz`.
- Cargas nodales por estado de carga (ESTADOS / CARGAS).
- Peso propio como carga uniforme `beamUniform`, con la masa de la base Gerdau (kg/m).
- Combinaciones de servicio por superposición lineal (COMBINACIONES).
- Apoyos por grado de libertad. Las rótulas usan nodos auxiliares con giros libres.
- Análisis **lineal de primer orden** (sin P-Δ).
- Unidades internas: cm y kgf (y kgf·cm para momentos). La memoria reporta en mm, kgf y kgf·m según el caso.

---

## 4. Normas y apartados usados

Estado de la verificación:
- **Texto leído:** el apartado está en `referencias/referencias_normativas.md` con su origen.
- **Transcrito del PDF por OCR, verificar:** las fórmulas en el texto extraído pueden estar mal transcritas (símbolos).
- **Implementado y no revisado a fondo:** la implementación se hizo a partir de la norma citada; no hay extracto en el paquete.

| Norma | Apartado | Uso en el código | Estado |
|---|---|---|---|
| AISC 360-22 | D2 (tensión, Ωt = 1.67 fluencia, 2.00 fractura) | `diseno_asd.py`, tensión | Implementado. Verificar. |
| AISC 360-22 | D3 y Tabla D3.1 (factor U para ángulos) | `factor_u_angulo` | Implementado. Verificar. |
| AISC 360-22 | E1, E3 (Fe, Fn; umbral 2.25) | `pn_compresion`, `_fn_E3` | Implementado. Verificar. |
| AISC 360-22 | E4 (pandeo torsional y flexotorsional; Kz) | `pn_compresion`, `_resistencias_angulo` | Implementado para I y CE. **Ángulos: flexotorsional no implementado (ver §8).** Kz elegido en PARAMETROS. |
| AISC 360-22 | E5 (ángulos sencillos, Lc/rz, ecs. E5-1 y E5-2; límite L/ra 80) | `_resistencias_angulo` | Implementado. Verificar. |
| AISC 360-22 | E7 (elementos esbeltos, Ae, Tabla B4.1a) | `_resistencias_angulo` | Implementado. Verificar. |
| AISC 360-22 | F2, F3 (flexión I y canal; Tabla B4.1b, λp 0.38, λr 1.0) | `mn_fuerte`, `_ltb_I` | Implementado. Verificar. |
| AISC 360-22 | F6 (flexión eje menor) | `mn_debil` | Implementado. Verificar. |
| AISC 360-22 | F10 y F10.3 (ángulos: ejes principales, pandeo local de pata) | `_resistencias_angulo` | Implementado. Verificar. |
| AISC 360-22 | G2 y G3 (cortante de almas e I, ángulos; kv 5.34 y 1.2; Cv, límite 1.10 y 2.24) | `vn_fuerte`, `vn_debil` | Implementado. Verificar. |
| AISC 360-22 | H1.1 (H1-1a/b) y H2 (ángulos, H2-1) | `_inter_fila`, `_chequear` | Implementado. Verificar. |
| AISC 360-22 | L2 (flecha), Comentario L2 pág. 16.1-543 (1/300 visible) | `flechas_vigas`, NORMA `FLECHA_DIVISOR` | Usado. La NTC no fija número (ver §4.1). |
| NTC-Acero CDMX 2020 | 2.3.2 (KL/r ≤ 200 en compresión; comentario 240 y 300 en tensión) | NORMA `NTC_KLR_*` | Texto leído. |
| NTC-Acero CDMX 2020 | Tabla 3.2.1 (λr compresión: patín 0.56, alma 1.49, ala de ángulo 0.45) | NORMA `NTC_LR_*` | Texto leído (extracto). Verificar valores. |
| NTC-Acero CDMX 2020 | Tabla 3.2.2 (λpl, λp, λr flexión) | NORMA `NTC_LIM_*` | Texto leído (extracto). Verificar valores. |
| NTC-Acero CDMX 2020 | 4.4 (tensión: sin límite obligatorio; 300 como recomendación) | referencias | Texto leído. |
| NTC-Acero CDMX 2020 | 11.4 (flecha: remite a las NTC de Criterios y Acciones) | referencias | Texto leído. |
| NTC-Acero CDMX 2020 | 12.1.2 (Tabla 12.1.2, b/t para ductilidad alta 0.30 y media 0.38) | `_ductilidad`, NORMA | Verificar contra el PDF. |
| NTC-Acero CDMX 2020 | 12.1.3.1 (columnas dúctiles KL/r ≤ 60) | `NTC_KLR_DUCTIL` | Verificar contra el PDF. |
| NTC Criterios y Acciones CDMX | 4.1.1 a) (flecha vertical: remite a normas del material) y b) (h/500 con frágiles; h/250 en otros casos) | `_seccion_desplazamientos`, NORMA `NTC_CA_H_*` | Texto leído. |
| NTC Diseño por Sismo 2023 | 1.7 (LDNE: 0.002 o 0.004; SV con QR′; OI con R′ = 0.75R) | `_seccion_sismo` | Texto leído. |
| NTC Diseño por Sismo 2023 | 2.4 y ec. 2.4.1 (segundo orden si distorsión > 0.08 V/W), pág. 32 | `_seccion_sismo` | Texto leído. |
| NTC Diseño por Sismo 2023 | 3.1, tabla 3.1.1 y ec. 3.1.1 (Ks: zona A 1/6, zona C 1/4, zona B 1/[6 − 4(Ts − 0.5)]) | NORMA `KS_*`, `parametros.py` | **Transcrito por OCR. Verificar.** |
| NTC Diseño por Sismo 2023 | 3.2 y ec. 3.2.1 (Q′ = 1 + (Q − 1)/k en la rama Ta–Tb) | `parametros.py` | **Transcrito por OCR. Verificar.** |
| NTC Diseño por Sismo 2023 | 3.3.1a y 3.3.1b (R0 = 2.0 con Q ≥ 3, 1.75 con Q < 3; k1 = 1.0 o 0.8; k2 = 0.5(1 − (T/Ta)²) si T < Ta) | `parametros.py`, `_seccion_sismo` | Texto leído, con OCR en símbolos. Verificar. |
| NTC Diseño por Sismo 2023 | 3.3.2a y 3.3.2b (R′ = R para SV; R′ = 0.75R para OI) | NORMA `RP_SV`, `RP_OI` | Texto leído. |
| NTC Diseño por Sismo 2023 | Tabla 4.3.2 (marcos de acero: Q, γSV, γOI) | NORMA (hoja SISTEMAS) | Texto leído. Valores de la tabla verificados contra el texto. |
| NTC Diseño por Sismo 2023 | 6.2 (método estático: regular ≤ 30 m; irregular ≤ 20 m; no Grupo A; no fuertemente irregular) | Pendientes de la memoria | Texto leído. Solo se advierte en la memoria. |
| NTC Diseño por Sismo 2023 | 6.3 y ec. 6.3.1 (V0 = c W0 / (Q′R′)) | `_seccion_sismo` (texto de memoria) | Texto leído. |
| NTC Diseño por Sismo 2023 | 6.4.1 (periodo aproximado T = 2π √(ΣW X² / (g ΣF X))) | `_periodo` | Texto leído. Verificar la forma en el PDF. |

### 4.1 Decisiones de interpretación normativa (ver §0.2: D1 a D10)

1. **Flecha L/300.** La NTC-Acero (§11.4) remite a las NTC de Criterios y Acciones, y la NTC-CA §4.1.1 a) remite a las normas del material. Ninguna da un número. Se usa L/300 por criterio del proyecto, con la justificación del Comentario L2 de AISC 360-22 (pág. 16.1-543). La combinación evaluada es la gravitacional total (D y L).
2. **Distorsión de entrepiso (NTC-CA 4.1.1 b).** Se usa h/250 porque el proyecto indica que no hay elementos no estructurales frágiles unidos. La distorsión se revisa por columna (la que controla) y solo en combinaciones gravitacionales. Las combinaciones con sismo se revisan en la sección 6.3 de la memoria.
3. **Distorsión por sismo (NTC Diseño por Sismo).**
   - La carga sísmica de la planilla se toma como **diseño para Seguridad de Vida**, reducida por Q·R′. La distorsión elástica (sin reducir) es entonces f = Q′·R veces la de la planilla para LDNE y OI, y f = Q·R para SV.
   - Q′ = Q supone k = 1 del SASID. Si k < 1, Q′ > Q (suelo blando, §3.2, comentario).
   - Ks = 1 (conservador) por defecto. Con la opción por zona, se usa 1/6 (A), 1/[6 − 4(Ts − 0.5)] (B) o 1/4 (C).
   - k2 se calcula con el periodo de §6.4.1 usando el menor de los periodos de los estados sísmicos (conservador).
4. **Efectos de segundo orden.** Se compara la mayor distorsión elástica o de SV por entrepiso con 0.08·V/W. V es la suma de las cargas horizontales de sismo por encima del entrepiso. W es la carga D (sin factor) por encima más el peso propio de las barras por encima.
5. **Kz (pandeo torsional de ángulos).** Lo elige el usuario entre 1.0 y 0.5 (AISC E4). El significado de cada opción debe confirmarse.

---

## 5. Parámetros de entrada y de norma

Los siguientes valores vienen de la plantilla Excel. Las **listas desplegables** y los **valores a ingresar** están en la hoja PARAMETROS. Los **valores de norma** (solo lectura) están en la hoja NORMA. El código no contiene valores de norma ni supuestos: si falta un dato, el modelo no se arma y el mensaje lo indica.

| Clave | Concepto | Valor de ejemplo (cambiar) | Unidad | Opciones | Referencia normativa |
|---|---|---|---|---|---|
| SISTEMA_SISMICO | Sistema estructural sismico | Marcos de acero de ductilidad media |  | lista (hoja NORMA, tabla 4.3.2) | NTC Diseno por Sismo 2023, tabla 4.3.2, pag. 53 |
| CRUJIAS_AMBAS | Tres o mas crujias resistentes en las dos direcciones | SÍ |  | SÍ / NO | NTC Diseno por Sismo 2023, §3.3.1, pag. 42-43 |
| ZONA_SISMICA | Zona sismica del sitio | B |  | A / B / C | NTC Diseno por Sismo 2023, §3.1 (eq. 3.1.1) |
| TS | Ts del sitio (SASID) | 0.5 | s | numero > 0 | NTC Diseno por Sismo 2023, eq. 3.1.1 y SASID |
| TA | Ta del sitio (SASID) | 0.2 | s | numero > 0 | NTC Diseno por Sismo 2023, §3.3.1b y SASID |
| TB | Tb del sitio (SASID) | 1 | s | numero > Ta | NTC Diseno por Sismo 2023, §3.2 y SASID |
| K_SASID | Factor k del SASID | 1 |  | numero > 0 | NTC Diseno por Sismo 2023, §3.2, eq. 3.2.1 |
| C_SASID | Coeficiente sismico c (SASID) | 0.25 |  | numero > 0 | NTC Diseno por Sismo 2023, §6.3, eq. 6.3.1 |
| KS_METODO | Factor Ks para la distorsion LDNE | CONSERVADOR (Ks=1) |  | CONSERVADOR (Ks=1) / SEGUN ZONA (ec. 3.1.1) | NTC Diseno por Sismo 2023, tabla 3.1.1, nota [3]; eq. 3.1.1 |
| DEFORMABLES | Elementos no estructurales capaces de deformarse o separados | SÍ |  | SÍ / NO | NTC Diseno por Sismo 2023, §1.7, pag. 26 |
| FRAGILES | Elementos no estructurales fragiles unidos | NO |  | SÍ / NO | NTC Criterios y Acciones, §4.1.1 b), pag. 8 |
| VIENTO | Viento considerado en el diseno | NO |  | NO | Criterio del proyecto (version actual) |
| KZ_TORSION | Factor Kz de pandeo torsional (extremos) | 1 |  | 1.0 / 0.5 | AISC 360-22, E4 (Kz, factor de longitud efectiva para pandeo torsional) |
| METODO | Metodo de analisis sismico | ESTÁTICO |  | ESTÁTICO | NTC Diseno por Sismo 2023, §6.1-6.2 |

### 5.1 Valores de norma (hoja NORMA)

| Clave | Valor | Unidad | Referencia | Explicación |
|---|---|---|---|---|
| LDNE_DEFORMABLES | 0.004 |  | NTC Diseno por Sismo 2023, §1.7, pag. 26 | Limite de distorsion LDNE si los elementos no estructurales son deformables o estan separados. |
| LDNE_NO | 0.002 |  | NTC Diseno por Sismo 2023, §1.7, pag. 26 | Limite LDNE en los demas casos. |
| NTC_CA_H_FRAGILES | 500 |  | NTC Criterios y Acciones, §4.1.1 b), pag. 8 | Distorsion horizontal h/500 con elementos no estructurales fragiles unidos. |
| NTC_CA_H_OTROS | 250 |  | NTC Criterios y Acciones, §4.1.1 b), pag. 8 | Distorsion h/250 en otros casos. |
| SEG2_FACTOR | 0.08 |  | NTC Diseno por Sismo 2023, §2.4, eq. 2.4.1, pag. 32 | Efectos de segundo orden despreciables si la distorsion no excede 0.08 V/W. |
| FLECHA_DIVISOR | 300 |  | AISC 360-22, Comentario L2, pag. 16.1-543 | Flecha vertical maxima L/300 en vigas. El comentario indica que 1/300 del claro es visible y puede causar dano arquitectonico. La NTC-Acero no fija un numero (§11.4 remite a la NTC-CA). |
| K1_SI | 1 |  | NTC Diseno por Sismo 2023, §3.3.1a, pag. 42-43 | k1 con tres o mas crujias en ambas direcciones. |
| K1_NO | 0.8 |  | NTC Diseno por Sismo 2023, §3.3.1a, pag. 42-43 | k1 con menos de tres crujias en alguna direccion. |
| K2_COEF | 0.5 |  | NTC Diseno por Sismo 2023, §3.3.1b, pag. 43 | k2 = 0.5 (1 - (T/Ta)^2) si T < Ta. |
| K2_EXP | 2 |  | NTC Diseno por Sismo 2023, §3.3.1b, pag. 43 | Exponente de T/Ta en k2. |
| RP_SV | 1 |  | NTC Diseno por Sismo 2023, §3.3.2a | R-prima para Seguridad de Vida = R. |
| RP_OI | 0.75 |  | NTC Diseno por Sismo 2023, §3.3.2b | R-prima para Ocupacion Inmediata = 0.75 R. |
| KS_A_DEN | 6 |  | NTC Diseno por Sismo 2023, eq. 3.1.1 (zona A) | Ks = 1/6 en zona A. |
| KS_C_DEN | 4 |  | NTC Diseno por Sismo 2023, eq. 3.1.1 (zona C) | Ks = 1/4 en zona C. |
| KS_B_A | 6 |  | NTC Diseno por Sismo 2023, eq. 3.1.1 (zona B) | Zona B: Ks = 1/[6 - 4(Ts - 0.5)]. |
| KS_B_B | 4 |  | NTC Diseno por Sismo 2023, eq. 3.1.1 (zona B) | Coeficiente de Ts en la zona B. |
| KS_B_C | 0.5 | s | NTC Diseno por Sismo 2023, eq. 3.1.1 (zona B) | Valor de Ts en la zona B. |
| G | 9.81 | m/s2 | NTC Diseno por Sismo 2023, §6.4.1 | Aceleracion de la gravedad para el periodo T. |
| NTC_LR_PATIN | 0.56 | sqrt(E/Fy) | NTC-Acero 2020, tabla 3.2.1, pag. 57 | lambda_r de patin (I y canal) en compresion. |
| NTC_LR_ALMA | 1.49 | sqrt(E/Fy) | NTC-Acero 2020, tabla 3.2.1, pag. 57 | lambda_r de alma en compresion. |
| NTC_LR_PATA | 0.45 | sqrt(E/Fy) | NTC-Acero 2020, tabla 3.2.1, pag. 57 | lambda_r de ala de angulo en compresion. |
| NTC_LIM_PATIN_PL | 0.3 | sqrt(E/Fy) | NTC-Acero 2020, tabla 3.2.2, pag. 58 | Patin tipo 1 (flexion). |
| NTC_LIM_PATIN_P | 0.38 | sqrt(E/Fy) | NTC-Acero 2020, tabla 3.2.2, pag. 58 | Patin tipo 2 (flexion) y limite media de Tabla 12.1.2. |
| NTC_LIM_PATIN_R | 1 | sqrt(E/Fy) | NTC-Acero 2020, tabla 3.2.2, pag. 58 | Patin tipo 3 (flexion). |
| NTC_LIM_ALMA_PL | 2.45 | sqrt(E/Fy) | NTC-Acero 2020, tabla 3.2.2, pag. 58 | Alma tipo 1 (flexion). |
| NTC_LIM_ALMA_P | 3.76 | sqrt(E/Fy) | NTC-Acero 2020, tabla 3.2.2, pag. 58 | Alma tipo 2 (flexion). |
| NTC_LIM_ALMA_R | 5.7 | sqrt(E/Fy) | NTC-Acero 2020, tabla 3.2.2, pag. 58 | Alma tipo 3 (flexion). |
| NTC_LIM_PATA_P | 0.54 | sqrt(E/Fy) | NTC-Acero 2020, tabla 3.2.2, pag. 58 | Ala de angulo tipo 2 (flexion). |
| NTC_LIM_PATA_R | 0.91 | sqrt(E/Fy) | NTC-Acero 2020, tabla 3.2.2, pag. 58 | Ala de angulo tipo 3 (flexion). |
| NTC_KLR_COMP | 200 |  | NTC-Acero 2020, §2.3.2, pag. 41 | KL/r maximo en compresion (obligatorio). |
| NTC_KLR_REF_PRINC | 240 |  | NTC-Acero 2020, §2.3.2 (comentario) | L/r de referencia en tension, miembros principales. |
| NTC_KLR_REF_CONTR | 300 |  | NTC-Acero 2020, §2.3.2 (comentario) | L/r de referencia en tension, contraventeos. |
| NTC_KLR_DUCTIL | 60 |  | NTC-Acero 2020, §12.1.3.1, pag. 207 | KL/r maximo en columnas ductiles. |
| AISC_OMEGA_TFLU | 1.67 |  | AISC 360-22, D2 (fluencia en traccion) | Factor de seguridad ASD, traccion por fluencia. |
| AISC_OMEGA_TFRA | 2 |  | AISC 360-22, D2 (fractura en traccion) | Factor de seguridad ASD, traccion por fractura. |
| AISC_OMEGA_C | 1.67 |  | AISC 360-22, E1 (compresion) | Factor de seguridad ASD en compresion. |
| AISC_OMEGA_B | 1.67 |  | AISC 360-22, F1 (flexion) | Factor de seguridad ASD en flexion. |
| AISC_OMEGA_V | 1.67 |  | AISC 360-22, G1 (cortante) | Factor de seguridad ASD en cortante. |
| AISC_OMEGA_V_LAM | 1.5 |  | AISC 360-22, G2.1(a) | Cortante en alma de I laminada con h/tw <= 2.24 sqrt(E/Fy). |
| AISC_KV_I | 5.34 |  | AISC 360-22, G2.2 | kv de alma sin atiesadores. |
| AISC_KV_ANG | 1.2 |  | AISC 360-22, G3 | kv de la pata de angulo. |
| AISC_CB_MAX_ANG | 1.5 |  | AISC 360-22, F10-4 | Cb maximo para angulos. |
| AISC_LP_PATIN | 0.38 | sqrt(E/Fy) | AISC 360-22, Tabla B4.1b | lambda_p de ala (flexion, I y canal). |
| AISC_LR_PATIN | 1 | sqrt(E/Fy) | AISC 360-22, Tabla B4.1b | lambda_r de ala (flexion, I y canal). |
| AISC_CV_LIM | 1.1 |  | AISC 360-22, G2.2 | Limite de h/tw para Cv = 1 (factor 1.10 sqrt(kv E/Fy)). |
| AISC_HTW_LAM | 2.24 |  | AISC 360-22, G2.1(a) | Limite h/tw de I laminada con Ωv = 1.50. |
| AISC_LIM_ANG_E4 | 0.71 |  | AISC 360-22, E4 y F10.3 (angulos) | b/t de angulo sin pandeo flexotorsional. |
| AISC_E5_RAT_LIM | 80 |  | AISC 360-22, E5 | L/ra de corte entre E5-1 y E5-2. |
| AISC_B41A_C1_ALMA | 0.18 |  | AISC 360-22, Tabla B4.1a | Coeficiente c1 de alma (E7). |
| AISC_B41A_C2_ALMA | 1.31 |  | AISC 360-22, Tabla B4.1a | Coeficiente c2 de alma (E7). |
| AISC_B41A_C1_PATA | 0.22 |  | AISC 360-22, Tabla B4.1a | Coeficiente c1 de pata (E7). |
| AISC_B41A_C2_PATA | 1.49 |  | AISC 360-22, Tabla B4.1a | Coeficiente c2 de pata (E7). |
| AISC_LR_PATA_B41A | 0.45 | sqrt(E/Fy) | AISC 360-22, Tabla B4.1a | lambda_r de pata de angulo (E7). |

### 5.2 Sistemas sísmicos (hoja NORMA, tabla 4.3.2)

| Sistema | Q | γSV | γOI | R0 | Referencia |
|---|---|---|---|---|---|
| Marcos de acero de ductilidad alta | 4 | 0.03 | 0.0075 | 2 | NTC Diseno por Sismo 2023, tabla 4.3.2, i) Marcos, pag. 53; R0 de §3.3.1a |
| Marcos de acero de ductilidad media | 3 | 0.02 | 0.0075 | 2 | NTC Diseno por Sismo 2023, tabla 4.3.2, i) Marcos, pag. 53; R0 de §3.3.1a |
| Marcos de acero de ductilidad baja | 2 | 0.015 | 0.0075 | 1.75 | NTC Diseno por Sismo 2023, tabla 4.3.2, i) Marcos, pag. 53; R0 de §3.3.1a (Q < 3) |

---

## 6. Reglas de cálculo por módulo (resumen)

Índice completo de funciones: `codigo/mapa_de_codigo.md`.

**Análisis (`analisis_opensees.py`)**
- `propiedades_barras`: sección de la base Gerdau (A, Ix, Iy, J, masa). Si falta un dato, se lista y se detiene.
- `_modelo` y `_resolver`: modelo OpenSees por estado. Devuelve desplazamientos, fuerzas en extremos, reacciones y extremos de cada elemento.
- `correr`: resuelve estados y combinaciones; omite estados y combinaciones con viento; calcula desplazamientos, equilibrio residual y clases de combinación (`clase_combinacion`).
- `flechas_vigas` y `_deflexion_viga`: flecha de vigas horizontales. Solución exacta de Euler-Bernoulli entre extremos, con los giros del modelo y la carga propia uniforme, respecto a la cuerda. Validada en `pruebas/test_flecha.py`.

**Diseño (`diseno_asd.py`)**
- `cargar_norma`: carga los valores de la hoja NORMA. Si falta uno, se detiene. No hay valores por defecto.
- `_entrada_barra`: LX, LY, LB, KX, KY y CB son obligatorios. LI requiere LI CONEXION y LI LONGITUD CONEXION. No se suponen valores.
- `_props_asd`: propiedades de la base. Sin estimaciones: si la base no trae Zx, Zy o Cw, la barra queda NO REVISADO.
- Capacidades: tensión (D2, D3), compresión (E3, E4, E5, E7), flexión (F2, F3, F6, F10), cortante (G2, G3), interacción (H1, H2). Factores ASD de NORMA.
- Esbeltez: local por NTC 3.2 (λr de NORMA), global KL/r ≤ 200 (NTC 2.3.2), referencia 240 y 300, columnas dúctiles KL/r ≤ 60 (12.1.3.1), ductilidad (12.1.2).
- `matriz_fu_por_perfil`: FU de cada perfil del catálogo para cada barra. Un candidato LI sin datos de conexión queda NO REVISADO.

**Sismo y memoria (`parametros.py`, `memoria_asd.py`)**
- `resolver`: valida cada elección de PARAMETROS y calcula Q′, Ks, γLDNE, límite NTC-CA, R (sin k2), etc.
- `_seccion_sismo`: R = k1·R0 + k2 con k2 desde T (§6.4.1); f para LDNE y OI (Q′R); f para SV (QR); tabla por columna; periodo; segundo orden.
- `_seccion_desplazamientos`: secciones 6.1 (desplazamientos y deformada), 6.2 (distorsión NTC-CA), 6.3 (sismo), 6.4 (flecha).
- `_parametros_html`: sección 3.1 de la memoria (todos los parámetros con su referencia).

---

## 7. Decisiones y correcciones tomadas durante el desarrollo

Esta sección deja trazabilidad de lo que cambió a lo largo del trabajo. Varias son correcciones de errores anteriores.

1. **Q′ no es siempre ≤ Q.** Se afirmó erróneamente que Q′ ≤ Q. El comentario de §3.2 indica que Q′ puede ser mayor que Q cuando k < 1. La memoria ya no presenta Q′ = Q como conservador.
2. **Periodo (§6.4.1).** La primera versión omitía los niveles sin fuerza horizontal en la suma. Corregido: se suman todos los niveles.
3. **Valores por defecto eliminados.** LX, LY y LB tomaban la longitud de la barra; KX y KY valían 1.0; CB valía 1.0. Ahora son datos obligatorios de LONGITUDES.
4. **Estimaciones de propiedades eliminadas.** Zx, Zy y Cw de IR se estimaban cuando la base no los traía. Ahora la barra queda NO REVISADO.
5. **Conexión LI.** Antes se suponía "UNA PATA" y la longitud de la barra. Ahora falta el dato y el candidato queda NO REVISADO.
6. **Kz de pandeo torsional.** Antes valía 1.0 sin elección. Ahora es una lista (1.0 o 0.5) en PARAMETROS.
7. **Viento.** Esta versión no lo considera. Se omiten estados y combinaciones con W en el análisis, el diseño y la memoria.
8. **Factor elástico de la planilla.** Antes se usaba solo Q. Se corrigió a Q′·R (LDNE y OI) y Q·R (SV), siguiendo §1.7 y §6.3.
9. **Escenario "reducido solo por Q".** Se quitó de la memoria: la reducción del sismo es la del método estático (Q′R′).
10. **Flecha L/300.** Se justifica con el Comentario L2 de AISC y no con la NTC (que no da número). Antes se decía "criterio del proyecto" sin referencia.
11. **Combinación sísmica.** Las combinaciones con E entran al diseño. Los factores (por ejemplo 0.7) los define el usuario en COMBINACIONES.
12. **Hojas de la plantilla.** PARAMETROS y NORMA se generan con el mismo código que la plantilla. Se corrigió un error en que la cabecera de la hoja pisaba el título, y un desfase de columna en LONGITUDES de ejemplo.

---

## 8. Limitaciones conocidas (reportadas por el desarrollador)

1. **Ángulos: pandeo flexotorsional (E4) no implementado.** Si b/t > 0.71·√(E/Fy), la barra queda NO REVISADO.
2. **Análisis lineal de primer orden.** No hay P-Δ. El efecto se revisa solo como criterio (2.4.1).
3. **Conexiones no verificadas.** No hay placas, soldaduras, pernos ni elementos de apoyo.
4. **Sismo.** El programa **no calcula** las fuerzas sísmicas. Las recibe como estado de carga (V0 = c·W0/(Q′R′)) con c y los parámetros del SASID que da el usuario. No hay torsión accidental, ni sismo en dos direcciones simultáneas, ni irregularidades del capítulo 5, ni penalizaciones de la norma.
5. **Cargas en vigas.** Solo se admiten cargas nodales y peso propio. La fórmula de flecha depende de que no haya cargas intermedias.
6. **K, Cb y longitudes.** Son datos del usuario en LONGITUDES. El programa no los calcula a partir del marco.
7. **Sistemas sísmicos.** Solo están los marcos de acero de la tabla 4.3.2. Para otros sistemas hay que agregarlos en NORMA.
8. **Base Gerdau.** Hay 30 valores completados desde el manual Gerdau (verificar una muestra).
9. **Excel.** Las fórmulas de FU y MAXIFS se verificaron en LibreOffice en una versión anterior de la plantilla. Las hojas PARAMETROS y NORMA **no se han probado en Excel de escritorio**.
10. **Transcripción de la NTC Diseño por Sismo.** Algunas fórmulas (3.1.1, 3.2.1 y 6.4.1) llegaron por OCR. Se deben verificar contra el PDF.
11. **Material sin Fu.** En la planilla de ejemplo, A-572 G 60 no tiene Fu y debe cargarse.
12. **Ejecución.** Las pruebas se hicieron con un ejecutor local del notebook, no en Kaggle. Sin resultados de otra versión de openseespy.

---

## 9. Pruebas y evidencias

| Prueba | Qué comprueba | Resultado |
|---|---|---|
| `pruebas/test_flecha.py` | Flecha de vigas: fórmula contra un modelo de 4 elementos en OpenSees (carga propia, momento en extremo, combinados) y contra la fórmula analítica 5qL⁴/(384EI). | Diferencia máxima 1.8·10⁻¹⁵ cm frente al modelo subdividido. Coincide con la analítica en magnitud y sentido. `RESULTADO: OK`. |
| Ejecución de ejemplo (`ejemplo/`) | Notebook completo: lectura de planilla, análisis, diseño, memoria. | Sin errores. Memoria sin `None` ni `nan`. |
| Ejemplo con sismo (prueba interna) | Estado sísmico E, combinación con 0.7·E y revisión 6.3. | Sin errores. Sección 6.3 generada desde la configuración. |
| Planilla con TS vacío (prueba interna) | Un dato obligatorio faltante detiene el modelo. | Mensaje `PARAMETROS TS: falta el dato`. Modelo no armado. |
| Planilla de ejemplo, validación | Sin ERROR en la validación. | Correcto. |
| Equilibrio residual (análisis) | Suma de reacciones, cargas y peso propio. | Reportado en la cabecera de resultados (residuo en kgf). Debe ser ~0. |
| Excel (sesión anterior) | Recalculo FU de la hoja con LibreOffice frente al cálculo Python. | Diferencia ≤ 5·10⁻⁵ (reportado en la sesión anterior). |

---

## 10. Preguntas abiertas para el auditor

Cada pregunta se relaciona con las decisiones de la sección 0.2 (D1 a D20). Si una respuesta cambia una decisión, indique el identificador.

Responda a cada número. Si una respuesta depende de un texto de norma, cite el apartado y el extracto de `referencias/referencias_normativas.md`. Si necesita otro texto, indíquelo.

**Resistencia AISC (ASD)**
1. ¿Las ecuaciones E3, E4, E5, E7, F2, F3, F6, F10, G2, G3, H1 y H2 coinciden con AISC 360-22? Revise especialmente E7 (patas esbeltas), F10.3 (pata) y G3 (kv = 1.2).
2. ¿Es correcto usar Ωt = 1.67 para fluencia y 2.00 para fractura, con U según D3 para ángulos?
3. ¿La interacción de servicio (H1 y H2) suma las fracciones de flexión sin axial? ¿Debe usarse la suma completa de H1-1a/b?
4. ¿Los límites de Tablas B4.1a y B4.1b (0.18, 1.31, 0.22, 1.49, 0.45, 0.38, 1.0) están bien aplicados a I, canal y ángulo?
5. ¿El uso de 0.71 (E4) como umbral de flexotorsional para ángulos es correcto? ¿Qué debe hacerse cuando se supera?

**Esbeltez y ductilidad (NTC-Acero CDMX 2020)**
6. ¿KL/r ≤ 200 (2.3.2) aplica a todas las barras comprimidas? ¿Los valores de referencia 240 y 300 en tensión se reportan bien?
7. ¿Tabla 3.2.1 y Tabla 3.2.2 están bien transcritas y aplicadas por tipo de elemento?
8. ¿Tabla 12.1.2 (0.30 alta, 0.38 media) y 12.1.3.1 (KL/r ≤ 60) se aplican bien a COLUMNA y VIGA?

**Flecha y desplazamientos**
9. ¿L/300 con la justificación de AISC (Comentario L2) es suficiente para un proyecto en México? ¿Prefiere L/240, L/300 o L/360, o solo carga viva?
10. ¿La flecha por Euler-Bernoulli con los giros del modelo y la carga propia está bien planteada? ¿Hay casos en que la hipótesis de vigas sin cargas intermedias falle?
11. ¿h/250 con elementos no frágiles (NTC-CA 4.1.1 b) es la interpretación correcta? ¿La columna que controla es la forma correcta de reportar?

**Sismo (NTC Diseño por Sismo 2023, método estático)**
12. ¿La interpretación de que la carga de la planilla es diseño para Seguridad de Vida (reducida por Q·R′) es correcta? ¿Afecta el resultado de LDNE?
13. ¿La distorsión elástica es f·δ_planilla, con f = Q′·R para LDNE y OI, y f = Q·R para SV?
14. ¿La ecuación 3.2.1 (Q′ = 1 + (Q − 1)/k en la rama Ta–Tb) está bien transcrita? Verifique contra el PDF.
15. ¿Ks = 1/6 (zona A), 1/4 (zona C) y 1/[6 − 4(Ts − 0.5)] (zona B) están bien transcritos (ec. 3.1.1)?
16. ¿R0 = 2.0 (Q ≥ 3) y 1.75 (Q < 3), y k1 = 1.0 con tres o más crujías en ambas direcciones, son correctos (§3.3.1a)?
17. ¿k2 = 0.5(1 − (T/Ta)²) con el menor periodo de los estados sísmicos (§3.3.1b y §6.4.1) es el uso correcto?
18. ¿El periodo de §6.4.1 con las fuerzas y desplazamientos del estado sísmico está bien planteado? Verifique la forma de la fórmula.
19. ¿El criterio de segundo orden (2.4.1) está bien aplicado: V como cortante de sismo, W como carga D sin factor y peso propio de barras encima?
20. ¿Las filas de Tabla 4.3.2 (marcos de acero) están bien transcritas (Q, γSV, γOI)?

**Diseño y combinaciones**
21. ¿El diseño ASD con combinaciones de servicio es adecuado para esta aplicación? ¿Falta algún criterio de combinación?
22. ¿La exclusión del viento (solo sismo para el diseño) cumple con lo que la norma exige en su caso?
23. ¿Kz = 1.0 o 0.5 (AISC E4): qué criterio debe usar el usuario según sus conexiones?

**Código, Excel y trazabilidad**
24. Busque en `codigo/modulos` valores fijos de norma, supuestos o defaults que no vengan de PARAMETROS o NORMA (por ejemplo `or 1.0`, `default`, `supuesto`).
25. ¿El análisis (nodos auxiliares, reacciones, signos, unidades y equilibrio) está bien implementado?
26. ¿La hoja PARAMETROS (listas, validaciones) y la hoja NORMA (protección) funcionan en Excel de escritorio?
27. ¿La memoria (sección 3.1) reporta todos los parámetros que usa el cálculo? ¿Hay algún valor usado que no esté en ella?
28. ¿La base Gerdau tiene valores completados sin marcar (30 en total)? Proponga una muestra para verificar.

---

## 11. Formato de los comentarios del auditor

Entregue sus comentarios en una tabla con este formato. Un comentario por fila.

| ID | Severidad | Área | Archivo y función | Referencia normativa (apartado y extracto) | Decisión relacionada (Dn) | Hallazgo | Evidencia (línea, valor o cálculo) | Recomendación | Confirmado o hipótesis |
|---|---|---|---|---|---|---|---|---|---|

- **Severidad:** crítico (resultado incorrecto o inseguro), alto (criterio normativo mal aplicado), medio (dato o supuesto no trazable), bajo (presentación, texto, redacción) o nota.
- **Confirmado:** lo comprobó con el texto de la norma o con una prueba reproducible. **Hipótesis:** lo sospecha y debe confirmarse.
- No cite normas ni apartados que no estén en el paquete sin indicar que son de memoria.
- Separe errores de programa, criterios de ingeniería y textos de la memoria.

---

## 12. Prompt sugerido para el agente auditor

> Eres un auditor técnico de software de cálculo estructural en acero. Vas a revisar el paquete `auditoria/` de la aplicación de diseño de soportes. Empieza por `AUDITORIA_SOPORTES.md`. Revisa `codigo/` contra `referencias/referencias_normativas.md`. Ejecuta `pruebas/test_flecha.py`. Responde las preguntas de la sección 10 con el formato de la sección 11. No inventes valores de norma: si un apartado no está en las referencias, dilo. No firmes ni apruebes el cálculo. Tu salida es una tabla de comentarios y un resumen de los hallazgos críticos y altos.
