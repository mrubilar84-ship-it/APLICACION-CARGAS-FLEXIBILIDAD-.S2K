# Adenda 01 a la respuesta de la revisión 01

**Fecha:** 16 de noviembre de 2026
**Respuesta que se complementa:** `RESPUESTA_AUDITORIA.md` y el ZIP `auditoria_soportes_rev01.zip` (SHA-256 `4d0575e1cbb6911866891af78a943847992b3933d6db5ef0d530c01104ab1a75`), commit de código `f486b836b2bbd0da01742544846cd4f37a1c782f`.

La revisión 01 entregada no se modifica y su manifiesto no cambia. Esta adenda corrige dos respuestas que dimos mal, registra los cambios posteriores a la revisión 01 y actualiza el estado de los pendientes.

## 1. Correcciones a la respuesta entregada

### R-05 (corregido): la norma sísmica sí está disponible

Lo escrito en la respuesta decía que el archivo no podía identificarse. Eso era incorrecto:

- Está en las cargas del usuario: `Mexico_2023-09-16_NTC-SISMO_-_Para_Entrega.zip`, que contiene `Mexico 2023-09-16 NTC-SISMO - Para Entrega.pdf`. El nombre coincide con el que citó el auditor.
- El PDF tiene 232 páginas, título vacío, fecha de creación 19-sep-2023 y fecha de modificación 19-sep-2023 (UTC). No se reproduce el dato personal de sus metadatos.
- La portada y el índice no declaran fecha de publicación en Gaceta ni si el documento es definitivo o borrador.
- Búsqueda pública (16-nov-2026): no confirma la fecha de publicación de esta norma. Existe una copia de 2020 de la misma NTC con encabezado de Gaceta del 9 de junio de 2020, por lo que el texto de 2023 es otra edición. Hay un aviso de Gaceta del 6 de noviembre de 2023 que corresponde a otras NTC del reglamento, no a esta. Fuentes: [copia PAOT de la NTC-Sismo con comentarios](https://paot.mx/centro/normas_a/2022/2%20NORMAS%20TECNICAS%20COMPLEMENTARIAS%20PARA%20DISENO%20POR%20SISMO%20CON%20COMENTARIOS.pdf); [registro de regulaciones CDMX, NTC de criterios y acciones](https://regulaciones.cdmx.gob.mx/mejora/public/regulacionPdf/605); [Gaceta Oficial CDMX](https://data.consejeria.cdmx.gob.mx/).
- Pendiente (U2 en `pendientes_usuario.md`): confirmar en la Gaceta Oficial la fecha y el estatus de la edición, y si una revisión posterior (2024-2029) la reemplaza.

### R-07 (corregido): los 30 valores sí están en el manual

Lo escrito en la respuesta decía que ninguno de los 30 valores aparecía en el manual y que las páginas 26 y 27 no existían. Ambas cosas eran incorrectas:

- Las páginas 26 y 27 son **números impresos** del manual. El PDF tiene 23 páginas, y las tablas CE (impresa 26) e IR (impresa 27) están en la misma imagen, en la página PDF 14. Las tablas son imágenes, por eso la búsqueda por texto no las encontró.
- Comparación visual de los 30 valores de `CORRECCIONES_MANUAL` contra esa imagen. Coinciden todos:
  - IR 10 × 12: J = 2,5. IR 10 × 15: Ix = 2686, Sx = 226, rx = 10 (verificado a 300 dpi).
  - CE 3 × 3.5: J = 0,72, Cw = 384,61, ro = 4,00. CE 3 × 4.1: J = 0,98, Cw = 478,86, ro = 3,90.
  - CE 4 × 4.5: A = 8,90, Iy = 12,00, Sy = 4,00, ry = 1,20, J = 1,30, Cw = 1167,10, Zy = 9,00, ro = 5,10.
  - CE 4 × 5.40: J = 1,44, Cw = 1520,51, ro = 4,80. CE 6 × 8.20: J = 2,77, Cw = 8414,88, ro = 6,70.
  - CE 6 × 10.50: J = 4,69, Cw = 12672,17, ro = 6,30. CE 6 × 13.00: J = 8,92, Cw = 17790,92, ro = 6,00.
  - Las tablas CE se revisaron a 110 dpi, legibles. Para una verificación más fina conviene una imagen a 300 dpi.
- El catálogo rev04 marca esos campos como pendientes (`campos_pendientes`: J y Cw en los CE). Los valores del manual son la fuente de completado.
- **Trazabilidad pendiente (A10):** la base del notebook no conserva `pagina_manual`, `pagina_pdf`, `referencia_excel` ni `campos_pendientes`. Están en el JSON del repositorio y debe restaurarse su paso a la base.

### R-07 (catálogo fuente): ahora disponible en el repositorio

- `fuentes_notebook/datos/perfiles_gerdau_mexico_rev04.json`, SHA-256 `c5fdf1b1b09a9a7e98bfcdc92504a2b258bfc54d9571d1548eda3595ac0b3754`. Es la fuente de la base del notebook: los mismos 247 perfiles con los mismos nombres.
- El CSV rev04 (`588d0d32…`, SHA-256 `252da1a9c975a697b593ef6a489e3fa11cd9f285229d3b9c8130f3b3c1c4578d`) no se copió porque el generador no lo lee. Queda en las cargas del usuario.
- La base no es idéntica campo a campo al JSON: el generador conserva un subconjunto de los campos y completa los 30 valores. La equivalencia se verificó en los campos que usa el notebook, no en todos.

### U10 (resuelto): designación `IR 6 × 8.5`

El JSON da la designación en pulgadas y su equivalente métrico: `IR 6 × 8.5` corresponde a `152 × 12.7`, con masa 12,7 kg/m. Es decir, la designación está en pulgadas × lb/ft (8,5 lb/ft = 12,65 kg/m).

## 2. Cambios posteriores a la revisión 01

Estos cambios no están en el manifiesto de la revisión 01. Se identifican por el commit que contiene esta adenda.

| cambio | archivo | motivo |
|---|---|---|
| El máximo de momento en el tramo se calcula en forma cerrada. Ya no se muestrean 401 puntos. | `soportes_planilla.ipynb`, celda 19 (`_curvatura_max`); fuente en `fuentes_notebook/analisis_opensees.py` | A2 cerrado. Con carga uniforme, EI·v'' es un polinomio de grado 2; el máximo de |M| está en un extremo o en el vértice. |
| `openseespy` se instala fijado en `3.8.0.0`. | celda 20; fuente `fuentes_notebook/celda9_analisis.py` | A4 cerrado. Coincide con `entorno/requirements.txt`. |
| Las fuentes del generador se versionan en el repositorio. La ruta del catálogo pasa a ser relativa a la carpeta. | `fuentes_notebook/` | Las fuentes estaban solo en la carpeta de trabajo de la sesión, que puede limpiarse. |
| Se excluye `perfiles_gerdau.py` de las fuentes. Es una copia de desarrollo con una ruta de carga; el notebook escribe `perfiles_gerdau.py` desde `perfiles_gerdau_nb.py`, que lee la base embebida. | `fuentes_notebook/` (no se copió) | Evita una versión que no entra en el notebook y tiene una ruta local. |

**Verificación de reconstrucción:** `fuentes_notebook/build_soportes_planilla3.py` reconstruye `soportes_planilla.ipynb` byte a byte desde el propio repositorio. Uso en `fuentes_notebook/LEEME.md`.

## 3. Verificación de los cambios

**Forma cerrada frente a muestreo** (`adenda_verificacion/curv_exacta_prueba.py`, salida en `curv_exacta_salida.txt`):

- 3000 vigas aleatorias: en ningún caso la forma cerrada da menos que el muestreo.
- Error máximo del muestreo de 401 puntos: 8,1·10⁻⁶ relativo. La forma cerrada lo elimina.
- Viga simple con carga uniforme: 9000 kgf·cm = qL²/8, en ambos métodos.

**Ejemplo gravitacional** (ejecución limpia del notebook actualizado, código 0):

- Hojas de diseño y resultados: 9 celdas en RESULTADOS, 18 en DETALLE y 87 en BARRAS cambian. El error relativo máximo es 5,4·10⁻¹⁰, es decir, ruido de punto flotante.
- Ningún FU cambia al redondearlo a tres decimales. Ningún texto de cumplimiento cambia.
- Memoria: idéntica (cero líneas distintas).

**Caso sísmico** (ejecución limpia, código 0):

- Diseño: 60 celdas distintas, error absoluto máximo 1,1·10⁻¹⁶. Resultados: 143 celdas distintas, error absoluto máximo 5,7·10⁻¹³.
- Error relativo máximo en valores con |valor| > 10⁻³: 1,0·10⁻¹⁵.
- Ningún FU cambia al redondearlo. Memoria idéntica.
- Nota: un primer cálculo dio 1,5 % porque dividía entre valores casi nulos. Se corrigió midiendo el error relativo solo para |valor| > 10⁻³.

**Pruebas de la revisión 01 con los módulos nuevos:**

- `test_rev01.py`: 11 comprobaciones OK, código 0 (`adenda_verificacion/test_rev01_salida.txt`).
- `test_flecha_rev01.py`: OK, código 0 (`adenda_verificacion/test_flecha_salida.txt`).

## 4. Estado de los pendientes

| # | estado tras esta adenda |
|---|---|
| U2 | Abierto. Fecha y estatus de la edición de la norma sísmica no confirmados. El usuario debe confirmar en la Gaceta. |
| U8 | Catálogo disponible en el repositorio. Falta que el usuario confirme que el rev04 es la versión vigente. |
| U9 | Los 30 valores están verificados contra el manual (imagen). Falta que el usuario confirme la fuente de completado. |
| U10 | Resuelto (ver sección 1). |
| A2, A4 | Cerrados (sección 2). |
| A10 (nuevo) | Restaurar en la base las referencias de página y los campos pendientes del JSON. Responsable: agente. |
| U1, U3 a U7, U11 a U15 | Sin cambios. |
| A1, A3, A5 a A9 | Sin cambios. |
