# Pendientes (revision 02)

Esta lista separa lo que depende del usuario o del ingeniero responsable de lo que puede avanzar el agente. Los identificadores (R-xx, H-xx) corresponden a la solicitud del auditor. La columna **estado rev02** indica el cambio respecto de `auditoria_rev01/pendientes_usuario.md`.

## A. Requieren decision o dato del usuario

| # | pendiente | ID | que se necesita | estado rev02 |
|---|---|---|---|---|
| U1 | Ubicacion, jurisdiccion y norma contractual del proyecto. Caracter industrial de los soportes. | R-04 | Confirmar el proyecto y la norma que aplica. Hoy el codigo usa NTC CDMX para acero y sismo, y AISC 360-22 ASD para resistencia, por instruccion del usuario. | Sin cambio. |
| U2 | Edicion exacta de cada norma y estado (definitivo o borrador). En particular, la norma sismica. | R-05 | Entregar el PDF o el enlace oficial de: NTC Diseno por Sismo, NTC Criterios y Acciones, NTC Acero, AISC 360-22. Confirmar la publicacion de la norma sismica en la Gaceta. | Sin cambio. |
| U3 | Ecuaciones con OCR dudoso. | R-05 | Paginas legibles o recortes con numero de ecuacion, simbolos, intervalos y notas. | Sin cambio. |
| U4 | Origen real de las cargas sismicas. El caso entregado usa cargas de prueba (+1000 kgf en los nodos 3 y 6, Sismo X). | H-03, R-06 | Calculo sismico con su memoria: peso sismico, masas tributarias, distribucion por nivel, significado de E, factores Q, Q', R, R', parametros del sitio, direcciones, signos y excentricidad. | Sin cambio. |
| U5 | Estados de carga reales del proyecto. | R-04 | Cuales aplican de: peso propio, tuberia vacia, operacion, prueba, contenido, aislacion, temperatura, friccion, guias y stops, mantenimiento. La planilla hoy tiene D, L, W y E. | Sin cambio. |
| U6 | Limite de desplazamiento compatible con piping y efectos de segundo orden. | R-04 | Valor o criterio. Hoy: flecha L/300 (Comentario L2 de AISC) y distorsion de la seccion 4.1.1 b) de NTC-CA. | Sin cambio. |
| U7 | Exclusion del viento. | R-04 | Confirmar si es limitacion provisional del software o exclusion justificada para este caso. | Sin cambio. |
| U8 | Catalogo Gerdau fuente. | R-07 | Confirmar que `perfiles_gerdau_mexico_rev04.json` es la version vigente. El archivo ya esta en `fuentes_notebook/datos/`. | **Parcial:** el archivo esta en el repositorio; falta la confirmacion de vigencia. |
| U9 | Los 30 valores completados desde el manual Gerdau. | R-07 | Confirmar la edicion del manual que se uso como fuente. Los valores estan verificados contra la imagen de las paginas 26 y 27 (PDF pagina 14). | **Parcial:** verificados; falta confirmar la edicion. |
| U10 | Designacion `IR 6 x 8.5`. | R-07 | - | **Cerrado:** la designacion esta en pulgadas y lb/ft (`ADENDA_01.md`). |
| U11 | Fu de A-572 G 60, que esta vacio en la hoja MATERIALES. | R-04 | Dato del usuario (lo actualizara en el Excel). | Sin cambio. |
| U12 | Modulo de elasticidad y coeficiente de Poisson de A-529 G 50, A-572 G 50 y A-36. | R-04, R-07 | Confirmar E = 2 038 900 kgf/cm2 y v = 0,30, o indicar otros. Confirmar el Fu de 4570 kgf/cm2 de A-529. | Sin cambio. |
| U13 | Prueba en Kaggle desde cero, con y sin Internet. | R-02 | Ejecutar `soportes_planilla.ipynb` en Kaggle y reportar, o dar acceso para que el agente lo haga. | Sin cambio. |
| U14 | Prueba en Excel de escritorio. | R-09 | Abrir `planilla_con_diseno.xlsx`, cambiar un perfil en `PERFIL_GRUPO` y reportar que se actualiza y que aviso aparece. Hoy solo se probo con LibreOffice. | Sin cambio. |
| U15 | Decisiones de diseno D1 a D20. | varios | Ver la tabla de decisiones de `AUDITORIA_SOPORTES.md` (rev00) y los comentarios `DECISION` del codigo. | Sin cambio. |

**Ya no aplica:** la decision sobre cortante AISC para perfiles macizos. Esos perfiles salen del alcance por decision del usuario (`CAMBIOS_REV02.md`).

## B. Pendientes del agente desarrollador

| # | pendiente | ID | estado rev02 |
|---|---|---|---|
| A1 | Bateria de pruebas en el orden del auditor: marco 3D completo con equilibrio de momentos; IR, CE y LI en traccion, compresion, flexion y cambios de rama; entradas faltantes o no finitas; propagacion de NO REVISADO. | R-08 | **Parcial:** 50 pruebas independientes de equilibrio, voladizos, rotulas, mecanismos, modelo girado y barra inclinada. Abiertos: movimientos combinados en 3D, IR/CE/LI en traccion, compresion, flexion y cambios de rama, entradas no finitas y propagacion de NO REVISADO. |
| A2 | Acotar el error de muestreo de `_curvatura_max`. | H-01 | **Cerrado:** forma cerrada (commit `c79e8bd`). |
| A3 | Marca de resultado desactualizado en el libro cuando cambia un perfil en `PERFIL_GRUPO`. | R-09 | **Cerrado** para LibreOffice (commit `16f7385`, prueba 4 de 4). Excel de escritorio: U14. |
| A4 | Fijar la version de openseespy en el notebook. | R-02 | **Cerrado** (3.8.0.0). |
| A5 | Comprobacion a mano del FU de la barra que gobierna, de una flecha y de una distorsion sismica. | R-03 | **Parcial:** FU de la barra 1 y flecha de la barra 15 (`pruebas/comprobacion_manual/`). Falta la distorsion sismica. |
| A6 | Documentar la correspondencia de ejes y radios de LI, CE e IR contra el catalogo. | R-07 | Pendiente. |
| A7 | Recortes de pagina de las normas, cuando el usuario entregue los PDF. | R-05 | Pendiente (depende de U2). |
| A8 | Ejemplo numerico independiente desde cargas hasta distorsion LDNE, SV y OI, con unidades y factores en cada paso. | R-06 | Pendiente (depende de U4). |
| A9 | Confirmar que la lista de perfiles y la validacion de datos rechazan entradas faltantes y no finitas. | R-08 | Pendiente. |
| A10 | Restaurar en la base las referencias de pagina y los campos pendientes del catalogo. | R-07 | **Cerrado** (commit `16f7385`): `pagina_manual`, `pagina_pdf`, `referencia_excel`, `campos_pendientes` y `fuente_completado` en la base y en la memoria. |
