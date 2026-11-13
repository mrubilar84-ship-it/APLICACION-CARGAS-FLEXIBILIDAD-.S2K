# Pendientes

Esta lista separa lo que depende del usuario o del ingeniero responsable de lo que puede avanzar el agente desarrollador. Los identificadores (R-xx, H-xx) corresponden a la solicitud del auditor.

## A. Requieren decisión o dato del usuario

| # | pendiente | ID | qué se necesita |
|---|---|---|---|
| U1 | Ubicación, jurisdicción y norma contractual del proyecto. Carácter industrial de los soportes. | R-04 | Confirmar el proyecto y la norma que aplica. Hoy el código usa NTC CDMX para acero y sismo, y AISC 360-22 ASD para resistencia, por instrucción del usuario. |
| U2 | Edición exacta de cada norma y estado (definitivo o borrador). En particular, el archivo de sismo cuyo nombre citó el auditor. | R-05 | Entregar el PDF o el enlace oficial de: NTC Diseño por Sismo 2023, NTC Criterios y Acciones, NTC Acero, AISC 360-22. Confirmar la publicación del sismo (Gaceta u otra). |
| U3 | Ecuaciones con OCR dudoso. | R-05 | Páginas legibles o recortes con número de ecuación, símbolos, intervalos y notas. |
| U4 | Origen real de las cargas sísmicas. El caso entregado usa cargas de prueba (+1000 kgf en los nodos 3 y 6, Sismo X). | H-03, R-06 | Cálculo sísmico con su memoria: peso sísmico, masas tributarias, coordenadas, distribución por nivel, significado de E (elástica o reducida), factores Q, Q′, R, R′, parámetros del sitio y SASID si aplican, direcciones, signos y excentricidad. |
| U5 | Estados de carga reales del proyecto. | R-04 | Cuáles aplican de: peso propio, tubería vacía, operación, prueba, contenido, aislación, temperatura, fricción, guías y stops, mantenimiento. La planilla hoy tiene D, L, W y E. |
| U6 | Límite de desplazamiento compatible con piping y restricciones de segundo orden. | R-04 | Valor o criterio. Hoy: flecha L/300 (Comentario L2 de AISC) y distorsión de §4.1.1 b) de NTC-CA. |
| U7 | Exclusión del viento. | R-04 | Confirmar si es limitación provisional del software o exclusión justificada para este caso. |
| U8 | Catálogo Gerdau fuente y la revisión JSON/CSV que produjo `gerdau_datos.py`. | R-07 | Entregar el archivo fuente. No está en el repositorio ni en el paquete. |
| U9 | Los 30 valores completados desde el manual Gerdau. | R-07 | Confirmar cada valor con página y edición, o retirarlo. Hoy: NO VERIFICADO (ver `base_gerdau/`). |
| U10 | Designación `IR 6 × 8.5`. La masa de la base (12,7 kg/m) coincide con 8,5 lb/ft. | R-07 | Confirmar si la designación del catálogo está en lb/ft. |
| U11 | Fu de A-572 G 60, que está vacío en la hoja MATERIALES. | R-04 | Dato del usuario (el usuario lo actualizará en el Excel). |
| U12 | Módulo de elasticidad y coeficiente de Poisson de A-529 G 50, A-572 G 50 y A-36. La hoja MATERIALES dice "confirmar". | R-04, R-07 | Confirmar E = 2 038 900 kgf/cm² y ν = 0,30, o indicar otros. Confirmar también el Fu de 4570 kgf/cm² de A-529 (65 ksi, referencia Gerdau Corsa). |
| U13 | Prueba en Kaggle desde cero, con y sin Internet. | R-02 | Ejecutar `soportes_planilla.ipynb` en Kaggle y reportar el resultado, o dar acceso para que el agente lo haga. |
| U14 | Prueba en Excel de escritorio. | R-09 | Abrir `planilla_con_diseno.xlsx`, cambiar un perfil en `PERFIL_GRUPO` y reportar qué se actualiza. Hoy solo se probó con LibreOffice. |
| U15 | Decisiones de diseño D1–D20. | varios | Ver la tabla de decisiones de `AUDITORIA_SOPORTES.md` (rev00) y los comentarios `DECISION` del código. Siguen abiertas. |

## B. Pendientes del agente desarrollador

| # | pendiente | ID |
|---|---|---|
| A1 | Batería de pruebas en el orden del auditor: marco 3D con equilibrio de momentos, rótulas con nodos auxiliares, mecanismo, orientación girada, barra inclinada, IR/CE/LI en tracción, compresión, flexión y cambios de rama, entradas faltantes o no finitas, propagación de NO REVISADO. | R-08 |
| A2 | Acotar el error de muestreo de `_curvatura_max` (401 puntos) o usar los puntos de quiebre. | H-01 |
| A3 | Marca de resultado desactualizado en el libro cuando cambia un perfil en `PERFIL_GRUPO`. Hoy no existe aviso. | R-09 |
| A4 | Fijar la versión de openseespy en el notebook (la celda 20 instala sin versión). | R-02 |
| A5 | Comprobación a mano del FU de la barra que gobierna, de una flecha y de una distorsión sísmica, con AISC 360-22 y NTC. | R-03 |
| A6 | Documentar la correspondencia de ejes y radios de LI, CE e IR contra el catálogo. | R-07 |
| A7 | Recortes de página de las normas, cuando el usuario entregue los PDF. | R-05 |
| A8 | Ejemplo numérico independiente desde cargas hasta distorsión LDNE, SV y OI, con unidades y factores en cada paso. | R-06 |
| A9 | Confirmar que la lista de perfiles y la validación de datos rechazan entradas faltantes y no finitas (sin prueba hoy). | R-08 |
