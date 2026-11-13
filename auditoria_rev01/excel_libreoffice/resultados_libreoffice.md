# Verificacion en LibreOffice de planilla_con_diseno.xlsx

- Herramienta: LibreOffice 24.2.7.2 420(Build:2)
- Entrada: planilla_con_diseno.xlsx (SHA-256 63b4f81d956913705e0f55b8f21a61fe4b4683a767d37aaef1f8f27ad2e48a79)
- Recalculo forzado al abrir (OOXMLRecalcMode = 0).

## 1. Recalculo contra valores guardados

| hoja | celdas comparadas | distintas | ejemplo |
|---|---|---|---|
| INSTRUCCIONES | 27 | 0 | - |
| NODOS | 138 | 0 | - |
| BARRAS | 274 | 0 | - |
| LONGITUDES | 196 | 0 | - |
| CONEXIONES | 16 | 0 | - |
| LISTAS | 1211 | 0 | - |
| PERFIL_GRUPO | 34 | 0 | - |
| FU_BARRAS | 271 | 0 | - |
| FU_MATRIZ | 46915 | 0 | - |
| CALCULO | 3657 | 0 | - |
| CALCULO_3D | 4415 | 0 | - |
| ESTADOS | 16 | 0 | - |
| MATERIALES | 34 | 0 | - |
| COMBINACIONES | 20 | 0 | - |
| NORMA | 260 | 0 | - |
| PARAMETROS | 96 | 0 | - |
| CALCULO_CARGAS | 1521 | 0 | - |
| CARGAS | 80 | 0 | - |
| VISTA_VIVA | 14 | 0 | - |

Celdas con valor de error despues de recalcular (por hoja):

- CALCULO: 1948
- CALCULO_3D: 1441
- CALCULO_CARGAS: 185

## 2. Cambio de perfil en la lista (sin volver a ejecutar OpenSees)

PERFIL_GRUPO!B2 cambia de "IR 10 × 49" a "IR 12 × 16". Celdas que cambian despues de recalcular:

| hoja | celdas distintas | ejemplos (celda, antes, despues) |
|---|---|---|
| BARRAS | 12 | ('E2', 'IR 10 × 49', 'IR 12 × 16'); ('E3', 'IR 10 × 49', 'IR 12 × 16'); ('E4', 'IR 10 × 49', 'IR 12 × 16') |
| PERFIL_GRUPO | 5 | ('B2', 'IR 10 × 49', 'IR 12 × 16'); ('C2', '0.9772', '2.9167'); ('D2', '0.7278', '1.451') |
| FU_BARRAS | 84 | ('C2', 'IR 10 × 49', 'IR 12 × 16'); ('D2', '32', '41'); ('E2', '0.9772', '2.9167') |

Lectura: la lista y las formulas de FU recalculan; rigidez, peso y esfuerzos no cambian porque OpenSees no se vuelve a ejecutar.

## 3. Nota sobre los valores #N/A

Los #N/A de las hojas CALCULO, CALCULO_3D y CALCULO_CARGAS son intencionales. Las fórmulas usan NA() para que los gráficos de planta no dibujen puntos fuera de la vista seleccionada (por ejemplo, `=IF(AND(ISNUMBER(B2),H2=VISTA_VIVA!$C$3,...),F2,NA())`). No son errores de cálculo. Ninguna celda de PERFIL_GRUPO, FU_BARRAS, BARRAS ni de las hojas de resultados tiene #N/A.

## 4. Alcance

Probado con LibreOffice 24.2.7.2 en Linux, en modo headless. No se probó con Excel de escritorio. La comprobación de la protección de la hoja NORMA, de las validaciones de datos y del comportamiento al añadir filas queda pendiente.
