# Verificacion en LibreOffice de planilla_con_diseno.xlsx

- Herramienta: LibreOffice 24.2.7.2 420(Build:2)
- Entrada: planilla_con_diseno.xlsx (SHA-256 ce32d705ca728d359f1a4d0f3c8246bc771dea6531a78c7dba8b966959b38594)
- Recalculo forzado al abrir (OOXMLRecalcMode = 0).

## 1. Recalculo contra valores guardados

| hoja | celdas comparadas | distintas | ejemplo |
|---|---|---|---|
| INSTRUCCIONES | 27 | 0 | - |
| NODOS | 138 | 0 | - |
| BARRAS | 352 | 0 | - |
| LONGITUDES | 196 | 0 | - |
| CONEXIONES | 16 | 0 | - |
| LISTAS | 962 | 0 | - |
| PERFIL_GRUPO | 44 | 0 | - |
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
| PERFIL_GRUPO | 6 | ('B2', 'IR 10 × 49', 'IR 12 × 16'); ('C2', '0.9772', '2.9167'); ('D2', '0.7278', '1.451') |
| FU_BARRAS | 84 | ('C2', 'IR 10 × 49', 'IR 12 × 16'); ('D2', '32', '41'); ('E2', '0.9772', '2.9167') |

Lectura: la lista y las formulas de FU recalculan; rigidez, peso y esfuerzos no cambian porque OpenSees no se vuelve a ejecutar.
