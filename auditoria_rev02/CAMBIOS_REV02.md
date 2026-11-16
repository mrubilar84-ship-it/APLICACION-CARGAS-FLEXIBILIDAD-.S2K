# Cambios respecto de la revision 01 (rev01 -> rev02)

**Fecha:** 16 de noviembre de 2026.
**Base:** `auditoria_rev01/` (codigo de la revision 01: commit `f486b836b2bbd0da01742544846cd4f37a1c782f`, segun `ADENDA_01.md`). `auditoria_rev01/` no se modifica.
**Esta revision:** `auditoria_rev02/`. Su commit se registra en `IDENTIFICACION.txt`.
**Rama:** `claude/eloquent-turing-cwpcd8`.

## 1. Cambios de codigo (commits posteriores a la revision 01)

| commit | cambio | efecto en los resultados |
|---|---|---|
| `c79e8bd` | El maximo de momento en el tramo se calcula en forma cerrada (con carga uniforme, EI·v'' es un polinomio de grado 2). Sustituye el muestreo de 401 puntos. Cierra A2. | Diferencias solo de punto flotante (menores que 1e-9 relativo). Ver `ADENDA_01.md`, seccion 3. |
| `c79e8bd` | `openseespy` se instala fijado en 3.8.0.0 (cierra A4). Las fuentes del generador se versionan en `fuentes_notebook/`. | Ninguno. |
| `16f7385` | Aviso de resultado desactualizado en `PERFIL_GRUPO`: columnas PERFIL ANALIZADO y EJECUCION. Referencias de pagina del catalogo y campos pendientes en la base (cierra A10). | Agrega dos columnas en la hoja de diseno. Ningun valor numerico cambia. |
| `cf35170` | Prueba del aviso EJECUCION con LibreOffice (4 casos). | Ninguno (prueba). |
| `cf079c6` | Comprobacion manual independiente de FU (barra 1) y de flecha (barra 15). | Ninguno (prueba). |
| `d474205` | Solver: un modelo singular se detecta aunque OpenSees devuelva codigo 0 (captura del aviso en la salida de error); guarda de residuo de equilibrio. Pruebas R-08 reproducibles. | Ninguno en los casos entregados. Un modelo singular ahora detiene el analisis con error. |
| `6e9b55e` | Texto de RESUMEN de reacciones: las reacciones son las fuerzas que el apoyo ejerce sobre la estructura. Antes el texto invertia el signo. | Cambia `RESUMEN!B5` de `resultados_soportes.xlsx` en los dos casos. Ningun numero cambia. |
| `89b8467` | Eje fuerte obligatorio (EJE_FUERTE_X/Y/Z en BARRAS, sin valor por defecto). Rotulas en el plano: el giro alrededor de la barra se transmite del nudo; en rotulas oblicuas se usa penalizacion. Aviso de modelo inestable antes de resolver. | Ninguno en los casos entregados: la planilla de ejemplo ahora trae el eje explicito de cada barra, el mismo que daba la regla anterior. |
| `8822ad1` | Se eliminan CS y OS de la base, del diseno y de los textos (decision del usuario: son macizos). | Cambia el alcance de la memoria y de `RESUMEN!B7`. Ningun numero cambia. |
| `1816de4` | Se elimina SOL (solera, macizo). La plantilla y la hoja LISTAS no contienen perfiles macizos. | Igual que el anterior. La base queda con 164 perfiles (IR 110, CE 7, LI 47). El catalogo JSON se conserva completo. |

## 2. Archivos de codigo que cambiaron

Diferencias contra `auditoria_rev01/codigo/` (diff unificado en `comparacion/cambios_codigo_rev01_rev02.diff`):

| archivo | lineas agregadas | lineas quitadas |
|---|---|---|
| codigo/modulos/analisis_opensees.py | 168 | 26 |
| codigo/modulos/diseno_asd.py | 3 | 3 |
| codigo/modulos/diseno_ntc.py | 1 | 1 |
| codigo/modulos/gerdau_datos.py | 1 | 1 |
| codigo/modulos/memoria_asd.py | 6 | 2 |
| codigo/modulos/orientacion_gerdau.py | 8 | 6 |
| codigo/modulos/perfiles_gerdau.py | 3 | 2 |
| codigo/bloques/celda_12.py | 26 | 7 |
| codigo/bloques/celda_15.py | 3 | 0 |
| codigo/bloques/celda_20.py | 1 | 1 |
| codigo/bloques/celda_27.py | 16 | 1 |

Los modulos nuevos o eliminados: ninguno. El notebook `soportes_planilla.ipynb` (raiz del repositorio) se regenero desde `fuentes_notebook/`.

## 3. Pruebas de la revision 01: cambio en los modelos de prueba

Desde `89b8467` el eje fuerte es obligatorio. Las pruebas de rev01 usaban `'eje_fuerte': None` en sus modelos de prueba y **dejaban de correr** (`ValueError: barra sin eje fuerte`). Esto no es un error del calculo: era una entrada incompleta del modelo de prueba.

En `pruebas/` se dio a cada modelo el eje fuerte explicito `(0, 0, 1)` (peralte vertical). Con la formula actual da `vecxz = (0, -1, 0)`, la misma orientacion que la regla de rev01 para vigas a lo largo de X (`vector_vecxz`, verificado numericamente). **Las comprobaciones y sus valores esperados no cambiaron.** Cada archivo lleva una linea de cabecera que lo indica.

Se probo antes `(0, 1, 0)`: daba `vecxz = (0, 0, 1)`, es decir, flexion sobre el otro eje. La prueba de flecha dio 10 veces el valor analitico. Se descarto ese valor.

Los archivos originales de rev01 no cambiaron. El control contra el codigo recibido (rev00) se ejecuto con las mismas pruebas.

## 4. Efecto sobre los resultados entregados

Comparacion celda a celda (`comparacion/comparacion_rev01_rev02.md`, tolerancia relativa 1e-9):

- **Ejemplo gravitacional:** ninguna celda numerica distinta en `diseno_asd.xlsx` (CAPACIDADES 760, RESULTADOS 514, DETALLE 741, LISTAS_GRUPO 2869 celdas comparadas) ni en `resultados_soportes.xlsx` (BARRAS 2205, NODOS 657, REACCIONES 250, MAXIMOS_BARRAS 1785, DEFORMADA 1095).
- **Caso sismo:** ninguna celda numerica distinta en las mismas hojas (DETALLE 1103, BARRAS 3297, NODOS 981, REACCIONES 370, MAXIMOS_BARRAS 2669, DEFORMADA 1635).
- **Textos cambiados** (dos celdas por libro, en los dos casos):
  - `diseno_asd.xlsx`, `RESUMEN!B7`: alcance. Dice que se eliminaron los perfiles macizos (CS, OS, SOL) de la base.
  - `resultados_soportes.xlsx`, `RESUMEN!B5`: signo de las reacciones (commit `6e9b55e`).
- **Memoria:** cuatro lineas de texto distintas por caso. Dos cambian el alcance (CS y LM), y dos agregan la pagina del catalogo (`Catalogo Gerdau rev04, pag. impresa 27`) a las tablas de perfiles.
- **Caso sismo, entrada:** el archivo de entrada cambio (eje fuerte explicito y LISTAS sin SOL). Su nombre es `planilla_sismo_ENTRADA.xlsx`, con SHA-256 en `valores_esperados.md`.

Las salidas de la revision 02 vienen de una ejecucion del notebook actual (hash del notebook verificado antes de ejecutar: `f923b93a…`), con codigo de salida 0 (`ejemplo/ejecucion.log` y `caso_sismo/ejecucion.log`).

## 5. Limitaciones que siguen vigentes

- Los perfiles macizos CS, OS y SOL ya no estan en la base. Una planilla vieja que los use recibe un ERROR en la validacion (`PERFIL ... no existe en la base Gerdau`). Esa ruta esta en el codigo de la celda 7, pero **no se probo con una planilla que use esos perfiles**.
- Kaggle y Excel de escritorio no se probaron. LibreOffice 24.2.7.2 si.
- Las cargas sismicas del caso son de prueba (H-03, R-06).
- Las comprobaciones manuales (FU, flecha) leen como entrada las demandas (BARRAS) y los desplazamientos (DEFORMADA) de los libros. Verifican capacidades, formulas y postproceso; no el ensamblado del modelo.
