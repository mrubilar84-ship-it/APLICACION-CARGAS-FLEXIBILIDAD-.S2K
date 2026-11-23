# Pendientes (revisión 05)

Estado al 23 de noviembre de 2026. Decisiones y datos que dependen del usuario, y trabajo del agente para la rev06.

## A. Decisiones del usuario

| # | decisión | ID del auditor | opciones |
|---|---|---|---|
| D2 | KL/r ≤ 200 en vigas con compresión (cuatro vigas IR 12 × 16 del ejemplo, KL/r = 250, NO CUMPLE) | R04-13 | (a) mantener la regla para toda barra con compresión (recomendado: es su instrucción anterior); (b) no aplicar KL/r a vigas |
| D3 | LI con Ix = Iy del catálogo en el análisis | R04-15 | (a) aceptar el alcance actual con esa suposición validada por el usuario; (b) restringir LI a un alcance validado |
| D4 | espesor de diseño de HSS (AISC §B4.2: 0.93·t nominal para norma distinta de ASTM A1065/A1085) | R04-10 | confirmar la norma del producto (A500 u otra) y si las propiedades del catálogo ATC ya usan el espesor de diseño. Si corresponde, las propiedades se recalculan, no se escalan |
| D5 | caso real del proyecto: geometría, apoyos, perfiles, cargas gravitacionales y de tuberías, reacciones, origen de las cargas sísmicas | R04-21 | entregar entrada, salida, memoria y log del caso real |
| D6 | método de segundo orden y su aplicabilidad (P-Δ, P-δ, imperfecciones) | R04-14 | implementar un método o limitar el alcance a marcos sin efectos significativos |
| D7 | flujo de selección de perfil | R04-16 | (a) los candidatos son predimensionamiento con demandas congeladas (rotulado); (b) cada cambio de perfil exige un nuevo análisis |
| D8 | alcance de placas base hasta cerrar anclajes, soldadura y momentos | R04-03, R04-05, R04-06, R04-23 | (a) uso solo como predimensionamiento; (b) completar el modelo (grupo de soldadura, MZ, contacto biaxial, mecanismos de anclaje) |

## B. Datos y verificaciones del usuario

| pendiente | ID |
|---|---|
| DG1 original (pág. 19, pdf 26) y §3.1.2: confirmar 0.7 F_u frente a 0.75; espesor de placa | R04-06 |
| ACI 318-02 Apéndice D (D.5.2, ec. D-7) | R04-06 |
| Norma del producto de los HSS y base del catálogo ATC (D4) | R04-10 |
| Resolver las siete alertas de catálogo contra la fuente | R04-11 |
| Fu de A-572 G60 (vacío en la plantilla) | R04-08 |
| Jurisdicción (Zitácuaro) y aceptación de IMCA + AISC sin NTC-Acero | — |
| Estados de carga reales, límite de desplazamiento y viento | — |
| Factores sísmicos Q, R y SASID | R04-21 |
| Prueba en Kaggle y en Excel de escritorio | R-02, R-09 |

## C. Trabajo del agente (rev06)

| tarea | ID |
|---|---|
| Actualizar o retirar `test_hss.py` y la comprobación manual con NTC | H-07, H-08 |
| Prueba automatizada de E7 para LI (umbral E7-2) | R04-12 |
| Prueba del caso mixto de grupo (barra sin coincidencia en la matriz) | R04-17 |
| Separar en la memoria clasificación, resistencia y límite contractual | R04-13 |
| Rotular RESULTADOS y memoria de los candidatos de predimensionamiento | R04-16 |
| Verificar los HSS del catálogo ATC contra el PDF (páginas 08 a 10) | R-07 |
| `pip freeze` completo del entorno | R-02 |
| Reproducir el script del auditor (T01–T23) si se autoriza su ejecución | R04-20 |
| Revisar la numeración de F7 y la excepción de LTB en HSS cuadrados (no confirmadas en el texto extraído de AISC) | R04-22 |
