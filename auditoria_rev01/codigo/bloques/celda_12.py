# celda 12 del notebook; bloque anterior: ## Bloque 6. Cargar plantilla Excel
# Plantilla Excel: escribe el libro completo (NODOS, BARRAS, CARGAS, ESTADOS, CONEXIONES, LISTAS, VISTA_VIVA).
# La misma funcion regenera el Excel con sus datos en el bloque 8, asi nada se pierde al guardar.
import os
import base64
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
COLS_MATRIZ_XL = ['CLAVE', 'ID', 'PERFIL', 'ELEMENTO DISENO', 'FU MAXIMO', 'FU DEMANDA',
                  'FU ESBELTEZ LOCAL (B4.1)', 'FU ESBELTEZ GLOBAL (KL/r<=200)',
                  'FU DUCTILIDAD (12.1.2, 12.1.3.1)', 'CASO QUE GOBIERNA', 'ESTADO']
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.drawing.image import Image as XLImage
from openpyxl.workbook.properties import CalcProperties
from dibujo_directo import DibujoModelo, ELEMENTOS, TIPOS_APOYO, TIPOS_CONEXION
import perfiles_gerdau as G
import pandas as pd

NODOS_COLS = ['ID', 'X (m)', 'Y (m)', 'Z (m)', 'UX', 'UY', 'UZ', 'RX', 'RY', 'RZ', 'NOTA', 'REPORTAR']
GRADOS_COLS = ['UX', 'UY', 'UZ', 'RX', 'RY', 'RZ']       # columnas E..J de NODOS: SI = grado restringido
BARRAS_COLS = ['ID', 'NODO_I', 'NODO_J', 'ELEMENTO', 'PERFIL', 'EJE_FUERTE_X', 'EJE_FUERTE_Y', 'EJE_FUERTE_Z',
               'CONEXION_I', 'CONEXION_J', 'MATERIAL', 'NOTA', 'REPORTAR', 'DUCTILIDAD']
MAT_MAX = 10
MAT_FIN = MAT_MAX + 1
# Valores de partida de la plantilla. Son datos de ENTRADA en la hoja MATERIALES: el notebook los lee de ahi
# (no los fija). E = 200 000 MPa = 2 038 900 kgf/cm2 y NU = 0.3, igual que A-36 en el modelo SAP CMZ-5746.
E_ACERO_PARTIDA = 2038900
NU_ACERO_PARTIDA = 0.3
MATERIALES_DEFAULT = [
    ['A-36', 'Acero', 2530, 4078, E_ACERO_PARTIDA, NU_ACERO_PARTIDA,
     'Manual Gerdau, pie de pagina 22 (fy). Fu y E: modelo SAP CMZ-5746 (A36).'],
    ['A-529 G 50', 'Acero', 3515, 4570, E_ACERO_PARTIDA, NU_ACERO_PARTIDA,
     'Manual Gerdau, pie de pagina 22 (fy). Fu 65 ksi: referencia Gerdau Corsa (confirmar). E y NU: confirmar.'],
    ['A-572 G 50', 'Acero', 3515, 4570, E_ACERO_PARTIDA, NU_ACERO_PARTIDA,
     'Manual Gerdau, pie de pagina 22. Perfiles IR (pag. 6): A992 / A572 G50. Fu 4570 kgf/cm2: dato del usuario (confirmar). E y NU: confirmar.'],
    ['A-572 G 60', 'Acero', 4200, None, E_ACERO_PARTIDA, NU_ACERO_PARTIDA,
     'Manual Gerdau, pie de pagina 22. Fu pendiente. E y NU: confirmar.'],
]
NODOS_MAX = 98          # filas 2..99 de NODOS
BARRAS_MAX = 106        # filas 2..107 de BARRAS
FIN_N = NODOS_MAX + 1
FIN_B = BARRAS_MAX + 1
NIV = 'VISTA_VIVA!$C$3'     # nivel Z para planta (celda editable)
COTA = 'VISTA_VIVA!$C$4'    # cota Y para alzado (celda editable)
PERFILES_ORDEN = G.lista_perfiles_ordenada()
ENCABEZADO = PatternFill('solid', fgColor='DDEBF7')
CABECERA_CALC = PatternFill('solid', fgColor='EDEDED')
ENTRADA = PatternFill('solid', fgColor='FFF2CC')
NEGRITA = Font(bold=True)


def _encabezado(ws, columnas, anchos, relleno=ENCABEZADO):
    for c, nombre in enumerate(columnas, start=1):
        celda = ws.cell(row=1, column=c, value=nombre)
        celda.font = NEGRITA; celda.fill = relleno
        celda.alignment = Alignment(horizontal='center', wrap_text=True)
        ws.column_dimensions[celda.column_letter].width = anchos[c - 1]
    ws.freeze_panes = 'A2'


def _filas(df, columnas):
    """Filas (listas) de un DataFrame leido de la planilla, en el orden de columnas; NaN -> None."""
    salida = []
    for _, r in df.iterrows():
        fila = []
        for c in columnas:
            v = r[c] if c in r.index else None
            if v is None or (isinstance(v, float) and pd.isna(v)):
                v = None
            fila.append(v)
        salida.append(fila)
    return salida


def ejemplo_filas():
    """Marco de ejemplo: 18 nodos, 26 barras, 6 apoyos empotrados."""
    ejemplo = DibujoModelo(ruta='ejemplo')
    ejemplo.marco_grilla([0, 5, 10], [0, 4], [0, 3.5, 7], 'IR 10 × 49', 'IR 12 × 16', 'IR 12 × 16')
    for i, q in enumerate(ejemplo.nodos):
        if abs(q[2]) < 1e-9:
            ejemplo.apoyo(i, 'empotrado')
    nodos = []
    for i, (x, y, z) in enumerate(ejemplo.nodos):
        restr = ejemplo.apoyos.get(i, (False,) * 6)
        nodos.append([i + 1, x, y, z, *['SI' if v else None for v in restr], None, 'SI'])
    barras = [[k + 1, b['n1'] + 1, b['n2'] + 1, b['elemento'], b['perfil'], None, None, None,
               b['conexion_i'], b['conexion_j'], (b.get('material') or 'A-572 G 50'), None, 'SI',
               ('MEDIA' if b['elemento'] in ('COLUMNA', 'VIGA') else None)]
              for k, b in enumerate(ejemplo.barras)]
    return nodos, barras


def _hoja_calculo(wb):
    """Columnas que alimentan los graficos. Regla: la coordenada X de cada serie es siempre numerica (asi el
    grafico no usa numeros de fila); solo la coordenada que se oculta (la de la vista que no corresponde) es #N/A."""
    ws = wb.create_sheet('CALCULO')
    _encabezado(ws, ['', 'nodo I (fila)', 'nodo J (fila)', 'X1', 'X2', 'Y1', 'Y2', 'Z1', 'Z2',
                     'planta X1', 'planta X2', 'planta Y1', 'planta Y2',
                     'alzado X1', 'alzado X2', 'alzado Z1', 'alzado Z2', '',
                     'nodo X (planta)', 'nodo Y (planta)', 'nodo X (alzado)', 'nodo Z (alzado)',
                     'apoyo X (planta)', 'apoyo Y (planta)', 'apoyo X (alzado)', 'apoyo Z (alzado)'],
                [4] + [11] * 16 + [3] + [11] * 8, relleno=CABECERA_CALC)
    for r in range(2, FIN_B + 1):
        ws[f'B{r}'] = f'=IFERROR(MATCH(BARRAS!B{r},NODOS!$A$2:$A${FIN_N},0),NA())'
        ws[f'C{r}'] = f'=IFERROR(MATCH(BARRAS!C{r},NODOS!$A$2:$A${FIN_N},0),NA())'
        for col, ref, idx in [('D', 'B', 'B'), ('E', 'B', 'C'), ('F', 'C', 'B'), ('G', 'C', 'C'),
                              ('H', 'D', 'B'), ('I', 'D', 'C')]:
            ws[f'{col}{r}'] = f'=IFERROR(INDEX(NODOS!${ref}$2:${ref}${FIN_N},{idx}{r}),0)'
        vis_p = f'AND(ISNUMBER(B{r}),H{r}={NIV},I{r}={NIV})'
        vis_a = f'AND(ISNUMBER(B{r}),F{r}={COTA},G{r}={COTA})'
        ws[f'J{r}'] = f'=D{r}'
        ws[f'K{r}'] = f'=E{r}'
        ws[f'L{r}'] = f'=IF({vis_p},F{r},NA())'
        ws[f'M{r}'] = f'=IF({vis_p},G{r},NA())'
        ws[f'N{r}'] = f'=D{r}'
        ws[f'O{r}'] = f'=E{r}'
        ws[f'P{r}'] = f'=IF({vis_a},H{r},NA())'
        ws[f'Q{r}'] = f'=IF({vis_a},I{r},NA())'
    CX = 'VISTA_VIVA!$C$8'          # cota X de la vista lateral Y-Z
    for col_, titulo in [(32, 'lat Z1 (barra)'), (33, 'lat Z2 (barra)'), (34, 'lat Y nodo'), (35, 'lat Z nodo'),
                         (36, 'lat Z apoyo'), (37, 'lat rotula I (Z)'), (38, 'lat rotula J (Z)')]:
        ws.cell(row=1, column=col_, value=titulo).font = NEGRITA
        ws.column_dimensions[_L(col_)].width = 14
    for r in range(2, FIN_B + 1):
        ws[f'AF{r}'] = f'=IF(AND(ISNUMBER(B{r}),D{r}={CX},E{r}={CX}),H{r},NA())'
        ws[f'AG{r}'] = f'=IF(AND(ISNUMBER(B{r}),D{r}={CX},E{r}={CX}),I{r},NA())'
        ws[f'AK{r}'] = f'=IF(AND(LOWER(TRIM(BARRAS!I{r}))="rotulado",ISNUMBER(B{r}),D{r}={CX}),H{r},NA())'
        ws[f'AL{r}'] = f'=IF(AND(LOWER(TRIM(BARRAS!J{r}))="rotulado",ISNUMBER(C{r}),E{r}={CX}),I{r},NA())'
    for r in range(2, FIN_N + 1):
        ws[f'AH{r}'] = f'=NODOS!$C{r}'
        ws[f'AI{r}'] = f'=IF(AND(NODOS!$A{r}<>"",NODOS!$B{r}={CX}),NODOS!$D{r},NA())'
        ws[f'AJ{r}'] = f'=IF(AND(COUNTIF(NODOS!$E{r}:$J{r},"SI")>0,NODOS!$B{r}={CX}),NODOS!$D{r},NA())'
    for col_, titulo in [(28, 'rotula I planta (Y)'), (29, 'rotula J planta (Y)'),
                         (30, 'rotula I alzado (Z)'), (31, 'rotula J alzado (Z)')]:
        ws.cell(row=1, column=col_, value=titulo).font = NEGRITA
        ws.column_dimensions[_L(col_)].width = 14
    for r in range(2, FIN_B + 1):
        rot_i = f'LOWER(TRIM(BARRAS!I{r}))="rotulado"'
        rot_j = f'LOWER(TRIM(BARRAS!J{r}))="rotulado"'
        ws[f'AB{r}'] = f'=IF(AND({rot_i},ISNUMBER(B{r}),H{r}={NIV}),F{r},NA())'
        ws[f'AC{r}'] = f'=IF(AND({rot_j},ISNUMBER(C{r}),I{r}={NIV}),G{r},NA())'
        ws[f'AD{r}'] = f'=IF(AND({rot_i},ISNUMBER(B{r}),F{r}={COTA}),H{r},NA())'
        ws[f'AE{r}'] = f'=IF(AND({rot_j},ISNUMBER(C{r}),G{r}={COTA}),I{r},NA())'
    for r in range(2, FIN_N + 1):
        ok = f'NODOS!$A{r}<>""'
        ws[f'S{r}'] = f'=NODOS!$B{r}'
        ws[f'T{r}'] = f'=IF(AND({ok},NODOS!$D{r}={NIV}),NODOS!$C{r},NA())'
        ws[f'U{r}'] = f'=NODOS!$B{r}'
        ws[f'V{r}'] = f'=IF(AND({ok},NODOS!$C{r}={COTA}),NODOS!$D{r},NA())'
        ws[f'W{r}'] = f'=NODOS!$B{r}'
        ws[f'X{r}'] = f'=IF(AND(COUNTIF(NODOS!$E{r}:$J{r},"SI")>0,NODOS!$D{r}={NIV}),NODOS!$C{r},NA())'
        ws[f'Y{r}'] = f'=NODOS!$B{r}'
        ws[f'Z{r}'] = f'=IF(AND(COUNTIF(NODOS!$E{r}:$J{r},"SI")>0,NODOS!$C{r}={COTA}),NODOS!$D{r},NA())'
    return ws


from openpyxl.utils import get_column_letter as _L, column_index_from_string as _CI

CALC3D_BARRAS = ['bx1', 'bxm', 'bx2', 'bxm2', 'bxt',
                 'by1', 'bym', 'by2', 'bym2', 'byt',
                 'L', 'xu', 'yu', 'zu', 'nb', 'nc', 'hasU', 'dot',
                 'ux', 'uy', 'uz', 'un', 'ex', 'ey', 'ez', 'mx', 'my', 'mz', 'rotI', 'rotJ', 'lblB',
                 'rot', 'nA', 'nM', 'nB', 'rA', 'rM', 'rB']
CALC3D_NODOS = ['nsx', 'nsy', 'apE', 'apR', 'lblN']


def _hoja_3d(wb):
    """Vista 3D esquematica en vivo (proyeccion ortogonal). Azimut (C5), elevacion (C6) y largo de la flecha (C7)
    de VISTA_VIVA. Cada barra es una serie de 5 puntos: inicio, medio, fin, medio, punta de la flecha del eje
    fuerte (vector del usuario o por defecto del motor, igual que ejes_locales())."""
    ws = wb.create_sheet('CALCULO_3D')
    col = {}
    for k, nombre in enumerate(CALC3D_BARRAS, start=2):
        col[nombre] = _L(k)
    ini_n = len(CALC3D_BARRAS) + 4
    for k, nombre in enumerate(CALC3D_NODOS, start=ini_n):
        col[nombre] = _L(k)
    KC = _L(ini_n + len(CALC3D_NODOS) + 2)
    VC = _L(ini_n + len(CALC3D_NODOS) + 3)
    col['_VC'] = VC
    _encabezado(ws, [''] + CALC3D_BARRAS + [''] * 2 + CALC3D_NODOS,
                [4] + [9] * len(CALC3D_BARRAS) + [3, 3] + [9] * len(CALC3D_NODOS), relleno=CABECERA_CALC)
    cA, sA, cE, sE, largo = f'${VC}$2', f'${VC}$3', f'${VC}$4', f'${VC}$5', f'${VC}$6'
    ws[f'{KC}2'] = 'cos(azimut)'; ws[f'{VC}2'] = f'=COS(RADIANS(VISTA_VIVA!$C$5))'
    ws[f'{KC}3'] = 'sen(azimut)'; ws[f'{VC}3'] = f'=SIN(RADIANS(VISTA_VIVA!$C$5))'
    ws[f'{KC}4'] = 'cos(elevacion)'; ws[f'{VC}4'] = f'=COS(RADIANS(VISTA_VIVA!$C$6))'
    ws[f'{KC}5'] = 'sen(elevacion)'; ws[f'{VC}5'] = f'=SIN(RADIANS(VISTA_VIVA!$C$6))'
    ws[f'{KC}6'] = 'largo flecha (m)'; ws[f'{VC}6'] = '=VISTA_VIVA!$C$7'
    ws[f'{KC}7'] = 'x de leyenda (no se dibuja)'; ws[f'{VC}7'] = 0
    ws[f'{KC}8'] = 'y de leyenda (no se dibuja)'; ws[f'{VC}8'] = '=NA()'
    for r in range(2, FIN_B + 1):
        c = lambda n: f'{col[n]}{r}'
        vis = f'ISNUMBER(CALCULO!B{r})'
        mx, my, mz = c('mx'), c('my'), c('mz')
        f = {
            'bx1': f'=CALCULO!D{r}*{cA}-CALCULO!F{r}*{sA}',
            'bx2': f'=CALCULO!E{r}*{cA}-CALCULO!G{r}*{sA}',
            'bxm': f'={mx}*{cA}-{my}*{sA}',
            'bxm2': f'={c("bxm")}',
            'bxt': f'=({mx}+{largo}*{c("ex")})*{cA}-({my}+{largo}*{c("ey")})*{sA}',
            'by1': f'=IF({vis},CALCULO!H{r}*{cE}+(CALCULO!D{r}*{sA}+CALCULO!F{r}*{cA})*{sE},NA())',
            'by2': f'=IF(ISNUMBER(CALCULO!C{r}),CALCULO!I{r}*{cE}+(CALCULO!E{r}*{sA}+CALCULO!G{r}*{cA})*{sE},NA())',
            'bym': f'=IF({vis},{mz}*{cE}+({mx}*{sA}+{my}*{cA})*{sE},NA())',
            'bym2': f'={c("bym")}',
            'byt': f'=IF({vis},({mz}+{largo}*{c("ez")})*{cE}+(({mx}+{largo}*{c("ex")})*{sA}+({my}+{largo}*{c("ey")})*{cA})*{sE},NA())',
            'L': f'=IF({vis},SQRT((CALCULO!E{r}-CALCULO!D{r})^2+(CALCULO!G{r}-CALCULO!F{r})^2+(CALCULO!I{r}-CALCULO!H{r})^2),1)',
            'xu': f'=(CALCULO!E{r}-CALCULO!D{r})/{c("L")}',
            'yu': f'=(CALCULO!G{r}-CALCULO!F{r})/{c("L")}',
            'zu': f'=(CALCULO!I{r}-CALCULO!H{r})/{c("L")}',
            'nb': f'=MAX(SQRT({c("xu")}^2+{c("yu")}^2),0.000000001)',
            'nc': f'=MAX(SQRT({c("zu")}^2+{c("yu")}^2),0.000000001)',
            'hasU': f'=COUNT(BARRAS!F{r}:H{r})>0',
            'dot': f'=N(BARRAS!F{r})*{c("xu")}+N(BARRAS!G{r})*{c("yu")}+N(BARRAS!H{r})*{c("zu")}',
            'ux': f'=N(BARRAS!F{r})-{c("dot")}*{c("xu")}',
            'uy': f'=N(BARRAS!G{r})-{c("dot")}*{c("yu")}',
            'uz': f'=N(BARRAS!H{r})-{c("dot")}*{c("zu")}',
            'un': f'=MAX(SQRT({c("ux")}^2+{c("uy")}^2+{c("uz")}^2),0.000000001)',
            'ex': f'=IFERROR(IF({c("hasU")},{c("ux")}/{c("un")},IF(ABS({c("zu")})>0.9,0,-{c("xu")}*{c("zu")}/{c("nb")})),0)',
            'ey': f'=IFERROR(IF({c("hasU")},{c("uy")}/{c("un")},IF(ABS({c("zu")})>0.9,-{c("zu")}/{c("nc")},-{c("yu")}*{c("zu")}/{c("nb")})),0)',
            'ez': f'=IFERROR(IF({c("hasU")},{c("uz")}/{c("un")},IF(ABS({c("zu")})>0.9,{c("yu")}/{c("nc")},({c("xu")}^2+{c("yu")}^2)/{c("nb")})),0)',
            'mx': f'=(CALCULO!D{r}+CALCULO!E{r})/2',
            'my': f'=(CALCULO!F{r}+CALCULO!G{r})/2',
            'mz': f'=(CALCULO!H{r}+CALCULO!I{r})/2',
            'rotI': f'=IF(AND({vis},LOWER(TRIM(BARRAS!I{r}))="rotulado"),{c("by1")},NA())',
            'rotJ': f'=IF(AND(ISNUMBER(CALCULO!C{r}),LOWER(TRIM(BARRAS!J{r}))="rotulado"),{c("by2")},NA())',
            'lblB': f'=IF(BARRAS!A{r}="","","B"&BARRAS!A{r})',
            'rot': f'=IF(OR(LOWER(TRIM(BARRAS!I{r}))="rotulado",LOWER(TRIM(BARRAS!J{r}))="rotulado"),1,0)',
            'nA': f'=IF(AND({vis},{c("rot")}=0),{c("by1")},NA())',
            'nM': f'=IF(AND({vis},{c("rot")}=0),{c("bym")},NA())',
            'nB': f'=IF(AND(ISNUMBER(CALCULO!C{r}),{c("rot")}=0),{c("by2")},NA())',
            'rA': f'=IF(AND({vis},{c("rot")}=1),{c("by1")},NA())',
            'rM': f'=IF(AND({vis},{c("rot")}=1),{c("bym")},NA())',
            'rB': f'=IF(AND(ISNUMBER(CALCULO!C{r}),{c("rot")}=1),{c("by2")},NA())',
        }
        for nombre, formula in f.items():
            ws[c(nombre)] = formula
    for r in range(2, FIN_N + 1):
        ws[f"{col['nsx']}{r}"] = f'=NODOS!B{r}*{cA}-NODOS!C{r}*{sA}'
        ws[f"{col['nsy']}{r}"] = f'=IF(NODOS!A{r}<>"",NODOS!D{r}*{cE}+(NODOS!B{r}*{sA}+NODOS!C{r}*{cA})*{sE},NA())'
        cuenta = f'COUNTIF(NODOS!$E{r}:$J{r},"SI")'          # grados restringidos del nodo (0 a 6)
        condiciones = {'apE': f'{cuenta}=6', 'apR': f'AND({cuenta}>0,{cuenta}<6)'}   # empotrado; parcial o rotulado
        for nombre, cond in condiciones.items():
            ws[f"{col[nombre]}{r}"] = (f'=IF(AND(NODOS!A{r}<>"",{cond}),'
                                       f'NODOS!D{r}*{cE}+(NODOS!B{r}*{sA}+NODOS!C{r}*{cA})*{sE},NA())')
        ws[f"{col['lblN']}{r}"] = f'=IF(NODOS!A{r}="","","N"&NODOS!A{r})'
    return ws, col


def _grafico_3d(ws_v, ws3, col):
    """Vista 3D esquematica en vivo. Cada barra y cada nodo es una serie cuyo nombre sale de una celda
    (B14, N3): asi las etiquetas funcionan en todas las versiones de Excel. Barra gris; flecha negra (ultimo
    tramo de la serie); extremo rotulado = circulo blanco; apoyo empotrado = cuadrado; rotulado = rombo.
    Limite de Excel: 255 series por grafico; aqui hay 214."""
    from openpyxl.chart.legend import Legend, LegendEntry
    from openpyxl.chart.series import SeriesLabel
    from openpyxl.chart.data_source import StrRef
    from openpyxl.chart.label import DataLabel, DataLabelList
    from openpyxl.chart.marker import DataPoint
    from openpyxl.chart.shapes import GraphicalProperties
    from openpyxl.drawing.line import LineProperties

    ch = ScatterChart()
    ch.title = '3D esquematico (C5 azimut, C6 elevacion)'
    ch.style = 13
    ch.height, ch.width = 13, 17
    ch.x_axis.title, ch.y_axis.title = ('horizontal', 'vertical')
    ch.x_axis.delete = False; ch.y_axis.delete = False

    def ci(nombre):
        return _CI(col[nombre])

    def ref_nombre(nombre, r):
        return f"'CALCULO_3D'!${col[nombre]}${r}"

    def etiqueta(idx):
        return DataLabelList(
            dLbl=[DataLabel(idx=idx, showSerName=True, showVal=False, showCatName=False,
                            showLegendKey=False, showPercent=False, showBubbleSize=False, dLblPos='t')],
            showSerName=False, showVal=False, showCatName=False, showLegendKey=False,
            showPercent=False, showBubbleSize=False)

    for r in range(2, FIN_B + 1):
        s = Series(Reference(ws3, min_col=ci('by1'), max_col=ci('byt'), min_row=r, max_row=r),
                   Reference(ws3, min_col=ci('bx1'), max_col=ci('bxt'), min_row=r, max_row=r))
        s.tx = SeriesLabel(strRef=StrRef(ref_nombre('lblB', r)))
        s.marker.symbol = 'none'
        s.graphicalProperties.line.solidFill = '7F7F7F'
        s.graphicalProperties.line.width = 28000
        s.smooth = False
        s.smooth = False
        s.dPt = [DataPoint(idx=4, spPr=GraphicalProperties(ln=LineProperties(solidFill='000000', w=15000)))]
        s.dLbls = etiqueta(1)
        ch.series.append(s)
    for nombre_x, nombre_y in [('bx1', 'rotI'), ('bx2', 'rotJ')]:
        s = Series(Reference(ws3, min_col=ci(nombre_y), min_row=2, max_row=FIN_B),
                   Reference(ws3, min_col=ci(nombre_x), min_row=2, max_row=FIN_B), title='Extremo rotulado')
        s.marker.symbol = 'circle'; s.marker.size = 8
        s.marker.graphicalProperties.solidFill = 'FFFFFF'
        s.marker.graphicalProperties.line.solidFill = '000000'
        s.graphicalProperties.line.noFill = True
        ch.series.append(s)
    for r in range(2, FIN_N + 1):
        n = Series(Reference(ws3, min_col=ci('nsy'), min_row=r, max_row=r),
                   Reference(ws3, min_col=ci('nsx'), min_row=r, max_row=r))
        n.tx = SeriesLabel(strRef=StrRef(ref_nombre('lblN', r)))
        n.marker.symbol = 'circle'; n.marker.size = 4
        n.marker.graphicalProperties.solidFill = '000000'
        n.graphicalProperties.line.noFill = True
        n.smooth = False
        n.dLbls = etiqueta(0)
        ch.series.append(n)
    for nombre_y, simbolo, etiq in [('apE', 'square', 'Apoyo empotrado'), ('apR', 'diamond', 'Apoyo rotulado')]:
        a = Series(Reference(ws3, min_col=ci(nombre_y), min_row=2, max_row=FIN_N),
                   Reference(ws3, min_col=ci('nsx'), min_row=2, max_row=FIN_N), title=etiq)
        a.marker.symbol = simbolo; a.marker.size = 9
        a.marker.graphicalProperties.solidFill = 'E67E22'
        a.graphicalProperties.line.noFill = True
        ch.series.append(a)
    # series de leyenda: no dibujan nada (y = #N/A); solo muestran el simbolo de cada tipo
    x_leyenda = f"{col['_VC']}7"
    y_leyenda = f"{col['_VC']}8"
    leyenda = [('Barra', 'linea', '7F7F7F'), ('Eje fuerte (flecha)', 'linea', '000000'),
               ('Extremo rotulado (circulo blanco)', 'circulo', 'FFFFFF'), ('Nodo (N)', 'circulo', '000000'),
               ('Apoyo empotrado (cuadrado)', 'square', 'E67E22'), ('Apoyo rotulado (rombo)', 'diamond', 'E67E22')]
    primera_leyenda = len(ch.series)
    for etiq, tipo, color in leyenda:
        s = Series(Reference(ws3, min_col=_CI(col['_VC']), min_row=8, max_row=8),
                   Reference(ws3, min_col=_CI(col['_VC']), min_row=7, max_row=7), title=etiq)
        if tipo == 'linea':
            s.marker.symbol = 'none'
            s.graphicalProperties.line.solidFill = color
            s.graphicalProperties.line.width = 28000 if color == '7F7F7F' else 15000
        else:
            s.marker.symbol = {'circulo': 'circle', 'square': 'square', 'diamond': 'diamond'}[tipo]
            s.marker.size = 8 if tipo != 'circulo' or color == 'FFFFFF' else 5
            s.marker.graphicalProperties.solidFill = color
            s.marker.graphicalProperties.line.solidFill = '000000'
            s.graphicalProperties.line.noFill = True
        ch.series.append(s)
    for serie in ch.series:
        serie.smooth = False          # lineas rectas: sin suavizado las flechas no se curvan
    assert len(ch.series) <= 255, f'grafico 3D con {len(ch.series)} series (limite de Excel: 255)'
    ch.legend = Legend()
    ch.legend.position = 'b'
    ch.legend.legendEntry = [LegendEntry(idx=i, delete=True) for i in range(primera_leyenda)]
    ws_v.add_chart(ch, 'A31')


def _grafico_3d_rotulas(ws_v, ws3, col):
    """3D con rotulas de los elementos (sin IDs): barras normales (gris), barras con extremo rotulado (morada
    discontinua) y circulo blanco en cada extremo rotulado. Usa la misma proyeccion que la 3D principal."""
    from openpyxl.chart.legend import Legend, LegendEntry
    ch = ScatterChart()
    ch.title = '3D con rotulas de los elementos'
    ch.style = 13
    ch.height, ch.width = 13, 17
    ch.x_axis.title, ch.y_axis.title = ('horizontal', 'vertical')
    ch.x_axis.delete = False; ch.y_axis.delete = False

    def ci(nombre):
        return _CI(col[nombre])

    for r in range(2, FIN_B + 1):
        s = Series(Reference(ws3, min_col=ci('nA'), max_col=ci('nB'), min_row=r, max_row=r),
                   Reference(ws3, min_col=ci('bx1'), max_col=ci('bx2'), min_row=r, max_row=r), title='Barra')
        s.marker.symbol = 'none'
        s.graphicalProperties.line.solidFill = '7F7F7F'
        s.graphicalProperties.line.width = 28000
        s.smooth = False
        ch.series.append(s)
    for r in range(2, FIN_B + 1):
        s = Series(Reference(ws3, min_col=ci('rA'), max_col=ci('rB'), min_row=r, max_row=r),
                   Reference(ws3, min_col=ci('bx1'), max_col=ci('bx2'), min_row=r, max_row=r),
                   title='Barra con extremo rotulado')
        s.marker.symbol = 'none'
        s.graphicalProperties.line.solidFill = '6A1B9A'
        s.graphicalProperties.line.width = 28000
        s.graphicalProperties.line.prstDash = 'dash'
        s.smooth = False
        ch.series.append(s)
    for nombre_x, nombre_y in [('bx1', 'rotI'), ('bx2', 'rotJ')]:
        s = Series(Reference(ws3, min_col=ci(nombre_y), min_row=2, max_row=FIN_B),
                   Reference(ws3, min_col=ci(nombre_x), min_row=2, max_row=FIN_B), title='Extremo rotulado')
        s.marker.symbol = 'circle'; s.marker.size = 8
        s.marker.graphicalProperties.solidFill = '6A1B9A'
        s.marker.graphicalProperties.line.solidFill = '6A1B9A'
        s.graphicalProperties.line.noFill = True
        s.smooth = False
        ch.series.append(s)
    n = Series(Reference(ws3, min_col=ci('nsy'), min_row=2, max_row=FIN_N),
               Reference(ws3, min_col=ci('nsx'), min_row=2, max_row=FIN_N), title='Nodo')
    n.marker.symbol = 'circle'; n.marker.size = 4
    n.marker.graphicalProperties.solidFill = '000000'
    n.graphicalProperties.line.noFill = True
    n.smooth = False
    ch.series.append(n)
    for nombre_y, simbolo, etiq in [('apE', 'square', 'Apoyo empotrado (cuadrado)'),
                                    ('apR', 'diamond', 'Apoyo rotulado (rombo)')]:
        a = Series(Reference(ws3, min_col=ci(nombre_y), min_row=2, max_row=FIN_N),
                   Reference(ws3, min_col=ci('nsx'), min_row=2, max_row=FIN_N), title=etiq)
        a.marker.symbol = simbolo; a.marker.size = 9
        a.marker.graphicalProperties.solidFill = 'E67E22'
        a.graphicalProperties.line.noFill = True
        a.smooth = False
        ch.series.append(a)
    primera_leyenda = len(ch.series)
    for etiq, tipo, color in [('Barra', 'linea', '7F7F7F'), ('Barra con extremo rotulado', 'linea', '6A1B9A'),
                              ('Extremo rotulado (circulo morado)', 'circulo', '6A1B9A'),
                              ('Nodo', 'circulo', '000000'), ('Apoyo empotrado (cuadrado)', 'square', 'E67E22'),
                              ('Apoyo rotulado (rombo)', 'diamond', 'E67E22')]:
        s = Series(Reference(ws3, min_col=_CI(col['_VC']), min_row=8, max_row=8),
                   Reference(ws3, min_col=_CI(col['_VC']), min_row=7, max_row=7), title=etiq)
        if tipo == 'linea':
            s.marker.symbol = 'none'
            s.graphicalProperties.line.solidFill = color
            s.graphicalProperties.line.width = 28000
        else:
            s.marker.symbol = {'circulo': 'circle', 'square': 'square', 'diamond': 'diamond'}[tipo]
            s.marker.size = 7
            s.marker.graphicalProperties.solidFill = color
            s.marker.graphicalProperties.line.solidFill = '000000'
            s.graphicalProperties.line.noFill = True
        ch.series.append(s)
    for serie in ch.series:
        serie.smooth = False
    assert len(ch.series) <= 255, f'grafico 3D con rotulas: {len(ch.series)} series'
    ch.legend = Legend()
    ch.legend.position = 'b'
    ch.legend.legendEntry = [LegendEntry(idx=i, delete=True) for i in range(primera_leyenda)]
    ws_v.add_chart(ch, 'A60')


def _grafico_lateral(ws_v, ws_c):
    """Alzado lateral Y-Z (plano X = cota X de C8): barras (gris), nodos, apoyos y extremos rotulados."""
    ch = ScatterChart()
    ch.title = 'Alzado Y-Z (cota X de C8)'
    ch.style = 13
    ch.legend = None
    ch.height, ch.width = 10, 16
    ch.x_axis.title, ch.y_axis.title = ('Y (m)', 'Z (m)')
    ch.x_axis.delete = False; ch.y_axis.delete = False
    for r in range(2, FIN_B + 1):
        s_ = Series(Reference(ws_c, min_col=_CI('AF'), max_col=_CI('AG'), min_row=r, max_row=r),
                    Reference(ws_c, min_col=_CI('F'), max_col=_CI('G'), min_row=r, max_row=r))
        s_.marker.symbol = 'none'
        s_.graphicalProperties.line.solidFill = '000000'
        s_.graphicalProperties.line.width = 22000
        s_.smooth = False
        ch.series.append(s_)
    n = Series(Reference(ws_c, min_col=_CI('AI'), min_row=2, max_row=FIN_N),
               Reference(ws_c, min_col=_CI('AH'), min_row=2, max_row=FIN_N), title='Nodos')
    n.marker.symbol = 'circle'; n.marker.size = 5
    n.marker.graphicalProperties.solidFill = '000000'
    n.graphicalProperties.line.noFill = True
    n.smooth = False
    ch.series.append(n)
    a = Series(Reference(ws_c, min_col=_CI('AJ'), min_row=2, max_row=FIN_N),
               Reference(ws_c, min_col=_CI('AH'), min_row=2, max_row=FIN_N), title='Apoyos')
    a.marker.symbol = 'square'; a.marker.size = 9
    a.marker.graphicalProperties.solidFill = 'E67E22'
    a.graphicalProperties.line.noFill = True
    a.smooth = False
    ch.series.append(a)
    for xcol, ycol in [('F', 'AK'), ('G', 'AL')]:
        s_ = Series(Reference(ws_c, min_col=_CI(ycol), min_row=2, max_row=FIN_B),
                    Reference(ws_c, min_col=_CI(xcol), min_row=2, max_row=FIN_B), title='Rotula')
        s_.marker.symbol = 'circle'; s_.marker.size = 8
        s_.marker.graphicalProperties.solidFill = '6A1B9A'
        s_.marker.graphicalProperties.line.solidFill = '6A1B9A'
        s_.graphicalProperties.line.noFill = True
        s_.smooth = False
        ch.series.append(s_)
    assert len(ch.series) <= 255
    ws_v.add_chart(ch, 'K31')


def _graficos(ws_v, ws_c):
    """Planta (X-Y) y alzado (X-Z) en VISTA_VIVA: barras, nodos y apoyos vinculados a las celdas."""
    def grafico(titulo, ejes, x_nodo, y_nodo, x_apoyo, y_apoyo, rango_barras, etiquetas):
        ch = ScatterChart()
        ch.title = titulo
        ch.style = 13
        ch.legend = None
        ch.height, ch.width = 10, 16
        ch.x_axis.title, ch.y_axis.title = etiquetas
        ch.x_axis.delete = False; ch.y_axis.delete = False
        for r in range(2, FIN_B + 1):
            s = Series(Reference(ws_c, min_col=rango_barras[1], max_col=rango_barras[1] + 1, min_row=r, max_row=r),
                       Reference(ws_c, min_col=rango_barras[0], max_col=rango_barras[0] + 1, min_row=r, max_row=r))
            s.marker.symbol = 'none'
            s.graphicalProperties.line.solidFill = '555555'
            s.graphicalProperties.line.width = 22000
            s.smooth = False
            ch.series.append(s)
        n = Series(Reference(ws_c, min_col=y_nodo, min_row=2, max_row=FIN_N),
                   Reference(ws_c, min_col=x_nodo, min_row=2, max_row=FIN_N), title='Nodos')
        n.marker.symbol = 'circle'; n.marker.size = 5
        n.marker.graphicalProperties.solidFill = '000000'
        n.graphicalProperties.line.noFill = True
        ch.series.append(n)
        a = Series(Reference(ws_c, min_col=y_apoyo, min_row=2, max_row=FIN_N),
                   Reference(ws_c, min_col=x_apoyo, min_row=2, max_row=FIN_N), title='Apoyos')
        a.marker.symbol = 'square'; a.marker.size = 9
        a.marker.graphicalProperties.solidFill = 'E67E22'
        a.graphicalProperties.line.noFill = True
        ch.series.append(a)
        return ch

    # planta: barras X1:X2 (J:K) y Y1:Y2 (L:M); nodos S (x) y T (y); apoyos W, X
    p = grafico('Planta (nivel Z de C3)', None, 19, 20, 23, 24, (10, 12),
                ('X (m)', 'Y (m)'))
    # alzado: barras X1:X2 (N:O) y Z1:Z2 (P:Q); nodos U (x) y V (z); apoyos Y, Z
    z = grafico('Alzado X-Z (cota Y de C4)', None, 21, 22, 25, 26, (14, 16),
                ('X (m)', 'Z (m)'))
    for ch_obj, ycols in [(p, ('AB', 'AC')), (z, ('AD', 'AE'))]:
        for xcol, ycol in [('D', ycols[0]), ('E', ycols[1])]:
            s_ = Series(Reference(ws_c, min_col=_CI(ycol), min_row=2, max_row=FIN_B),
                        Reference(ws_c, min_col=_CI(xcol), min_row=2, max_row=FIN_B), title='Rotula')
            s_.marker.symbol = 'circle'; s_.marker.size = 8
            s_.marker.graphicalProperties.solidFill = '6A1B9A'
            s_.marker.graphicalProperties.line.solidFill = '6A1B9A'
            s_.graphicalProperties.line.noFill = True
            s_.smooth = False
            ch_obj.series.append(s_)
    ws_v.add_chart(p, 'A10')
    ws_v.add_chart(z, 'J10')


# ---------------- CARGAS EN NODOS ----------------
CARGAS_COLS = ['ID NODO', 'ESTADO', 'FX (kgf)', 'FY (kgf)', 'FZ (kgf)', 'MX (kgf·m)', 'MY (kgf·m)', 'MZ (kgf·m)', 'NOTA']
CARGA_FILA0 = 9                       # primera fila de datos de la hoja CARGAS
CARGA_MAX = 300
CARGA_FIN = CARGA_FILA0 + CARGA_MAX - 1
ESTADOS_MAX = 30                      # filas 2..31 de la hoja ESTADOS
ESTADOS_FIN = ESTADOS_MAX + 1


def ejemplo_estados():
    """Estados de carga de ejemplo (el usuario los nombra y agrega en la hoja ESTADOS)."""
    return [['Peso propio y muerta', 'D', 'Peso propio, tabiqueria y cubierta', 'SI'],
            ['Sobrecarga', 'L', 'Sobrecarga de uso en el nivel superior', 'NO'],
            ['Viento X', 'W', 'Viento en direccion X sobre fachada izquierda', 'NO']]


def ejemplo_cargas():
    """Ejemplo: peso propio sobre los 6 nudos del nivel superior y viento X sobre 2 de ellos."""
    filas = [[id_, 'Peso propio y muerta', 0, 0, -1500, 0, 0, 0, None] for id_ in (3, 6, 9, 12, 15, 18)]
    filas += [[id_, 'Viento X', 800, 0, 0, 0, 0, 0, None] for id_ in (3, 6)]
    return filas


def _hoja_estados(wb, estados):
    """Hoja ESTADOS: lista de estados de carga que define el usuario (nombre, tipo y descripcion)."""
    ws = wb.create_sheet('ESTADOS')
    _encabezado(ws, ['NOMBRE DEL ESTADO', 'TIPO (D, L, W, E u otro)', 'DESCRIPCION', 'PESO PROPIO (SI/NO)'],
                [34, 22, 60, 20])
    for f in estados:
        ws.append(list(f) + [None] * (4 - len(f)))
    for _ in range(ESTADOS_MAX - len(estados)):
        ws.append([None] * 4)
    dv_pp = DataValidation(type='list', formula1='"SI,NO"', allow_blank=True)
    ws.add_data_validation(dv_pp); dv_pp.add(f'D2:D{ESTADOS_FIN}')
    return ws


def _hoja_calc_cargas(wb, col3d):
    """Calculo de la vista 3D de cargas: suma de cargas por nodo para el estado elegido en CARGAS!C3, y
    posicion en pantalla (misma proyeccion que CALCULO_3D) de cada nodo y de la punta de su flecha."""
    ws = wb.create_sheet('CALCULO_CARGAS')
    cols = ['id', 'fx', 'fy', 'fz', 'mx', 'my', 'mz', 'any', 'mag', 'tx3', 'ty3', 'tz3',
            'ax1', 'ax2', 'ay1', 'ay2', 'lbl']
    col = {nombre: _L(k) for k, nombre in enumerate(cols, start=1)}
    constantes = ['fmax', 'escala', 'dx', 'dy']
    KC = _L(len(cols) + 2)
    VC = _L(len(cols) + 3)
    for k, nombre in enumerate(constantes, start=2):
        col[nombre] = f'${VC}${k}'
    _encabezado(ws, [n for n in cols] + [''] + ['constante', 'valor'] + [''] * 0,
                [7] * 6 + [9] * 11 + [3, 14, 10], relleno=CABECERA_CALC)
    cA = f"CALCULO_3D!${col3d['_VC']}$2"; sA = f"CALCULO_3D!${col3d['_VC']}$3"
    cE = f"CALCULO_3D!${col3d['_VC']}$4"; sE = f"CALCULO_3D!${col3d['_VC']}$5"
    rango = lambda c: f"CARGAS!${c}${CARGA_FILA0}:${c}${CARGA_FIN}"
    ws[f'{KC}2'] = 'fuerza maxima (tf)'; ws[f'{VC}2'] = f'=MAX({col["mag"]}2:{col["mag"]}{FIN_N})'
    ws[f'{KC}3'] = 'escala flecha (m/tf)'; ws[f'{VC}3'] = f'=IF({col["fmax"]}>0,CARGAS!$C$4/{col["fmax"]},0)'
    ws[f'{KC}4'] = 'x de leyenda'; ws[f'{VC}4'] = 0
    ws[f'{KC}5'] = 'y de leyenda'; ws[f'{VC}5'] = '=NA()'
    for r in range(2, FIN_N + 1):
        c = lambda n: f'{col[n]}{r}'
        ws[c('id')] = f'=IF(NODOS!A{r}="","",NODOS!A{r})'
        for nombre, letra in [('fx', 'C'), ('fy', 'D'), ('fz', 'E'), ('mx', 'F'), ('my', 'G'), ('mz', 'H')]:
            ws[c(nombre)] = (f'=IF({c("id")}="",0,SUMIFS({rango(letra)},{rango("A")},{c("id")},'
                             f'{rango("B")},CARGAS!$C$3))')
        ws[c('any')] = (f'=IF(OR({c("fx")}<>0,{c("fy")}<>0,{c("fz")}<>0,{c("mx")}<>0,{c("my")}<>0,'
                        f'{c("mz")}<>0),1,0)')
        ws[c('mag')] = f'=SQRT({c("fx")}^2+{c("fy")}^2+{c("fz")}^2)'
        ws[c('tx3')] = f'=NODOS!B{r}+{col["escala"]}*{c("fx")}'
        ws[c('ty3')] = f'=NODOS!C{r}+{col["escala"]}*{c("fy")}'
        ws[c('tz3')] = f'=NODOS!D{r}+{col["escala"]}*{c("fz")}'
        ws[c('ax1')] = f'=CALCULO_3D!{col3d["nsx"]}{r}'
        ws[c('ax2')] = f'={c("tx3")}*{cA}-{c("ty3")}*{sA}'
        ws[c('ay1')] = f'=IF({c("any")}=1,CALCULO_3D!{col3d["nsy"]}{r},NA())'
        ws[c('ay2')] = (f'=IF(AND({c("any")}=1,{c("mag")}>0),{c("tz3")}*{cE}+({c("tx3")}*{sA}+{c("ty3")}*{cA})*{sE},'
                        f'NA())')
        texto = '&'.join(f'IF({c(n)}<>0,"{e} "&ROUND({c(n)},2)&" ","")'
                        for n, e in [('fx', 'Fx'), ('fy', 'Fy'), ('fz', 'Fz'), ('mx', 'Mx'), ('my', 'My'), ('mz', 'Mz')])
        ws[c('lbl')] = f'=IF({c("any")}=1,"N"&{c("id")}&": "&{texto},"")'
    return ws, col


# ---------------- LISTAS DESPLEGABLES POR GRUPO DE ELEMENTO (perfiles que cumplen el diseno) ----------------
GRUPOS_LISTA = ['COLUMNA', 'VIGA', 'ARRIOSTRE', 'DIAGONAL']


def _hoja_listas_grupo(wb, ws_l, listas=None):
    """Columnas F..I de LISTAS: perfiles por grupo de elemento, con nombres definidos LISTA_<GRUPO>. Sin diseno
    ejecutado (listas None) se listan todos los perfiles; si ninguno cumple, se indica."""
    from openpyxl.workbook.defined_name import DefinedName
    from openpyxl.utils import get_column_letter
    for j, g in enumerate(GRUPOS_LISTA):
        col = 6 + j
        letra = get_column_letter(col)
        if listas is None or g not in listas:
            nombres = [n for _, n in PERFILES_ORDEN]
        elif listas[g] is None:
            nombres = ['(sin barras de este grupo)']
        else:
            nombres = listas[g] or ['(ningun perfil cumple: revise el diseno)']
        cab = ws_l.cell(row=1, column=col, value=f'PERFILES {g}')
        cab.font = NEGRITA
        cab.fill = ENCABEZADO
        for k, n in enumerate(nombres):
            ws_l.cell(row=k + 2, column=col, value=n)
        ws_l.column_dimensions[letra].width = 24
        wb.defined_names[f'LISTA_{g}'] = DefinedName(f'LISTA_{g}',
                                                     attr_text=f"LISTAS!${letra}$2:${letra}${len(nombres) + 1}")


# ---------------- LONGITUDES POR BARRA (K y longitudes no arriostradas, como en RAM Element) ----------------
LONG_COLS = ['ID', 'LX (m)', 'LY (m)', 'KX', 'KY', 'LB (m)', 'CB',
             'E5 UNA PATA', 'E5 UNION SOLDADA O 2 PERNOS', 'E5 SIN CARGA INTERMEDIA',
             'E5 INDIVIDUAL O ALMA DE ARMADURA', 'LI CONEXION', 'LI LONGITUD CONEXION (m)', 'NOTA']
LONG_FIN = BARRAS_MAX + 1          # filas 2..107, alineadas fila a fila con BARRAS


def ejemplo_longitudes():
    """Ejemplo: LX, LY y LB = longitud de cada barra (m) desde la geometria del marco; KX = KY = 1.0 y CB = 1.0.
    Son datos obligatorios para el diseno: cambielos por los de su modelo (LX, LY y LB no se suponen)."""
    ej = DibujoModelo(ruta='ejemplo')
    ej.marco_grilla([0, 5, 10], [0, 4], [0, 3.5, 7], 'IR 10 × 49', 'IR 12 × 16', 'IR 12 × 16')
    filas = []
    for b in ej.barras:
        p1, p2 = ej.nodos[b['n1']], ej.nodos[b['n2']]
        L = round(sum((q - p) ** 2 for p, q in zip(p1, p2)) ** 0.5, 4)
        filas.append([L, L, 1.0, 1.0, L, 1.0] + [None] * 7)     # LX, LY, KX, KY, LB, CB, E5 x4, LI x2, NOTA
    return filas


def _hoja_longitudes(wb, filas=None):
    """Hoja LONGITUDES: por barra, longitud no arriostrada en X (LX) y en Y (LY), factores K, LB (pandeo lateral
    torsional) y CB. El ID sale de BARRAS. Vacio = valor supuesto por el diseño (se marca en la salida)."""
    ws = wb.create_sheet('LONGITUDES')
    _encabezado(ws, LONG_COLS, [8, 11, 11, 9, 9, 11, 9, 13, 14, 14, 14, 12, 14, 44])
    filas = filas or []
    for k in range(BARRAS_MAX):
        r = k + 2
        fila = filas[k] if k < len(filas) else [None] * (len(LONG_COLS) - 1)
        ws.cell(row=r, column=1, value=f'=IF(BARRAS!$A{r}="","",BARRAS!$A{r})')
        for c, v in enumerate(fila[:len(LONG_COLS) - 1], start=2):
            ws.cell(row=r, column=c, value=v)
    dv = DataValidation(type='decimal', operator='greaterThan', formula1='0', allow_blank=True)
    ws.add_data_validation(dv); dv.add(f'B2:G{LONG_FIN}'); dv.add(f'M2:M{LONG_FIN}')
    dv_si = DataValidation(type='list', formula1='"SI,NO"', allow_blank=True)
    ws.add_data_validation(dv_si); dv_si.add(f'H2:K{LONG_FIN}')
    dv_con = DataValidation(type='list', formula1='"UNA PATA,DOS PATAS"', allow_blank=True)
    ws.add_data_validation(dv_con); dv_con.add(f'L2:L{LONG_FIN}')
    return ws


def _hoja_cargas(wb, filas_cargas, estado_inicial=''):
    """Hoja CARGAS: estado de carga a mostrar (C3), largo de la flecha (C4) y la tabla de cargas por nodo."""
    ws = wb.create_sheet('CARGAS')
    ws['A1'] = 'Cargas aplicadas en los nodos (kgf, kgf·m)'
    ws['A1'].font = Font(bold=True, size=12)
    ws['A3'] = 'Estado de carga a mostrar en el 3D'
    ws['C3'] = estado_inicial
    ws['A4'] = 'Largo maximo de la flecha de carga (m)'
    ws['C4'] = 1.5
    ws['A5'] = 'Azimut y elevacion de la vista: se cambian en VISTA_VIVA (C5 y C6).'
    ws['A6'] = 'Unidades: fuerzas en kgf y momentos en kgf·m. Cada fila es un nodo con un estado de carga (hoja ESTADOS).'
    for celda in ('C3', 'C4'):
        ws[celda].fill = ENTRADA
    for k, nombre in enumerate(CARGAS_COLS, start=1):
        celda = ws.cell(row=CARGA_FILA0 - 1, column=k, value=nombre)
        celda.font = NEGRITA; celda.fill = ENCABEZADO
        celda.alignment = Alignment(horizontal='center', wrap_text=True)
    for k, ancho in enumerate([10, 28, 11, 11, 11, 12, 12, 12, 30], start=1):
        ws.column_dimensions[_L(k)].width = ancho
    for i, f in enumerate(filas_cargas):
        for k, v in enumerate(f, start=1):
            ws.cell(row=CARGA_FILA0 + i, column=k, value=v)
    dv_nodo = DataValidation(type='list', formula1=f'NODOS!$A$2:$A${FIN_N}', allow_blank=True)
    dv_estado = DataValidation(type='list', formula1=f'ESTADOS!$A$2:$A${ESTADOS_FIN}', allow_blank=True)
    dv_num = DataValidation(type='decimal', operator='between', formula1='-1000000', formula2='1000000',
                            allow_blank=True)
    for dv, rango_ in [(dv_nodo, f'A{CARGA_FILA0}:A{CARGA_FIN}'), (dv_estado, f'B{CARGA_FILA0}:B{CARGA_FIN}'),
                       (dv_num, f'C{CARGA_FILA0}:H{CARGA_FIN}')]:
        ws.add_data_validation(dv); dv.add(rango_)
    dv_caso = DataValidation(type='list', formula1=f'ESTADOS!$A$2:$A${ESTADOS_FIN}', allow_blank=True)
    ws.add_data_validation(dv_caso); dv_caso.add('C3')
    ws.freeze_panes = f'A{CARGA_FILA0}'
    return ws


def _grafico_cargas(ws_car, ws_cc, col_cc, ws3, col3d):
    """3D de cargas: barras (gris), nodos (negro), cada nodo con su etiqueta (N y carga) y su flecha de carga
    (roja, punta triangular). Apoyos: cuadrado (empotrado) y rombo (rotulado). Sin IDs de barras."""
    from openpyxl.chart.legend import Legend, LegendEntry
    from openpyxl.chart.series import SeriesLabel
    from openpyxl.chart.data_source import StrRef
    from openpyxl.chart.label import DataLabel, DataLabelList
    from openpyxl.chart.marker import DataPoint, Marker
    from openpyxl.chart.shapes import GraphicalProperties
    from openpyxl.drawing.line import LineProperties

    ch = ScatterChart()
    ch.title = '3D de cargas por nodo (estado en CARGAS!C3)'
    ch.style = 13
    ch.height, ch.width = 14, 18
    ch.x_axis.title, ch.y_axis.title = ('horizontal', 'vertical')
    ch.x_axis.delete = False; ch.y_axis.delete = False

    def ci3(n):
        return _CI(col3d[n])

    def cci(n):
        return _CI(col_cc[n])

    def etiqueta(idx):
        return DataLabelList(
            dLbl=[DataLabel(idx=idx, showSerName=True, showVal=False, showCatName=False, showLegendKey=False,
                            showPercent=False, showBubbleSize=False, dLblPos='t')],
            showSerName=False, showVal=False, showCatName=False, showLegendKey=False,
            showPercent=False, showBubbleSize=False)

    for r in range(2, FIN_B + 1):                     # barras: 3 puntos (inicio, medio, fin), sin etiqueta
        s = Series(Reference(ws3, min_col=ci3('by1'), max_col=ci3('by2'), min_row=r, max_row=r),
                   Reference(ws3, min_col=ci3('bx1'), max_col=ci3('bx2'), min_row=r, max_row=r))
        s.marker.symbol = 'none'
        s.graphicalProperties.line.solidFill = '7F7F7F'
        s.graphicalProperties.line.width = 28000
        s.smooth = False
        ch.series.append(s)
    for r in range(2, FIN_N + 1):                     # una serie por nodo: su nombre es la etiqueta N + carga
        s = Series(Reference(ws_cc, min_col=cci('ay1'), max_col=cci('ay2'), min_row=r, max_row=r),
                   Reference(ws_cc, min_col=cci('ax1'), max_col=cci('ax2'), min_row=r, max_row=r))
        s.tx = SeriesLabel(strRef=StrRef(f"'CALCULO_CARGAS'!${col_cc['lbl']}${r}"))
        s.marker.symbol = 'none'
        s.graphicalProperties.line.solidFill = 'C62828'
        s.graphicalProperties.line.width = 28000
        s.smooth = False
        s.dPt = [DataPoint(idx=1, marker=Marker(symbol='triangle', size=8),
                           spPr=GraphicalProperties(solidFill='C62828', ln=LineProperties(solidFill='C62828')))]
        s.dLbls = etiqueta(0)
        ch.series.append(s)
    n = Series(Reference(ws3, min_col=ci3('nsy'), min_row=2, max_row=FIN_N),
               Reference(ws3, min_col=ci3('nsx'), min_row=2, max_row=FIN_N), title='Nodo (N)')
    n.marker.symbol = 'circle'; n.marker.size = 4
    n.marker.graphicalProperties.solidFill = '000000'
    n.graphicalProperties.line.noFill = True
    n.smooth = False
    ch.series.append(n)
    for nombre_y, simbolo, etiq in [('apE', 'square', 'Apoyo empotrado (cuadrado)'),
                                    ('apR', 'diamond', 'Apoyo rotulado (rombo)')]:
        a = Series(Reference(ws3, min_col=ci3(nombre_y), min_row=2, max_row=FIN_N),
                   Reference(ws3, min_col=ci3('nsx'), min_row=2, max_row=FIN_N), title=etiq)
        a.marker.symbol = simbolo; a.marker.size = 9
        a.marker.graphicalProperties.solidFill = 'E67E22'
        a.graphicalProperties.line.noFill = True
        a.smooth = False
        ch.series.append(a)
    primera_leyenda = len(ch.series)
    x_leg = Reference(ws_cc, min_col=_CI(col_cc['dx'].split('$')[1]), min_row=4, max_row=4)
    y_leg = Reference(ws_cc, min_col=_CI(col_cc['dy'].split('$')[1]), min_row=5, max_row=5)
    for etiq, tipo, color in [('Barra', 'linea', '7F7F7F'), ('Carga aplicada (flecha roja)', 'linea', 'C62828'),
                              ('Nodo (N)', 'circulo', '000000'), ('Apoyo empotrado (cuadrado)', 'square', 'E67E22'),
                              ('Apoyo rotulado (rombo)', 'diamond', 'E67E22')]:
        s = Series(y_leg, x_leg, title=etiq)
        if tipo == 'linea':
            s.marker.symbol = 'none'
            s.graphicalProperties.line.solidFill = color
            s.graphicalProperties.line.width = 28000
        else:
            s.marker.symbol = {'circulo': 'circle', 'square': 'square', 'diamond': 'diamond'}[tipo]
            s.marker.size = 7
            s.marker.graphicalProperties.solidFill = color
            s.graphicalProperties.line.noFill = True
        ch.series.append(s)
    for serie in ch.series:
        serie.smooth = False
    assert len(ch.series) <= 255, f'grafico de cargas con {len(ch.series)} series'
    ch.legend = Legend()
    ch.legend.position = 'b'
    ch.legend.legendEntry = [LegendEntry(idx=i, delete=True) for i in range(primera_leyenda)]
    ws_car.add_chart(ch, 'K3')


def _hoja_materiales(wb, materiales):
    """Hoja MATERIALES: aceros del proyecto (nombre, tipo, Fy y Fu en kgf/cm2, fuente)."""
    ws = wb.create_sheet('MATERIALES')
    _encabezado(ws, ['NOMBRE', 'TIPO', 'FY (kgf/cm2)', 'FU (kgf/cm2)', 'E (kgf/cm2)', 'NU (Poisson)', 'FUENTE'],
                [14, 12, 14, 14, 16, 13, 80])
    for f in materiales:
        ws.append(list(f) + [None] * (7 - len(f)))
    for _ in range(MAT_MAX - len(materiales)):
        ws.append([None] * 7)
    return ws


# ---------------- COMBINACIONES DE CARGA ----------------
COMB_FILA0 = 3                       # primera fila de combinaciones
COMB_MAX = 40
COMB_FIN = COMB_FILA0 + COMB_MAX - 1
COMBINACIONES_DEFAULT = [
    [1] + [None] * (ESTADOS_MAX - 1),
    [1, 1] + [None] * (ESTADOS_MAX - 2),
    [1, 0.75, 0.75] + [None] * (ESTADOS_MAX - 3),
    [1, None, 1] + [None] * (ESTADOS_MAX - 3),
    [0.6, None, 1] + [None] * (ESTADOS_MAX - 3),
]


def _hoja_combinaciones(wb, combinaciones):
    """Hoja COMBINACIONES: columnas = estados (de la hoja ESTADOS), filas = combinaciones. Los factores son
    entradas del usuario (vacio = 0). La columna LC se arma sola: 'ASDn = f1·estado1 + f2·estado2 ...'."""
    ws = wb.create_sheet('COMBINACIONES')
    ws['A1'] = 'Combinaciones de carga: escriba los factores en las celdas amarillas (vacio = 0).'
    ws['A1'].font = NEGRITA
    cols = [_L(2 + j) for j in range(ESTADOS_MAX)]
    ws.cell(row=2, column=1, value='LC (calculada)').font = NEGRITA
    ws.cell(row=2, column=1).fill = ENCABEZADO
    ws.column_dimensions['A'].width = 70
    for j, col in enumerate(cols):
        ws[f'{col}2'] = f'=IF(ESTADOS!A{2 + j}="","",ESTADOS!A{2 + j})'
        ws[f'{col}2'].font = NEGRITA
        ws[f'{col}2'].fill = ENCABEZADO
        ws[f'{col}2'].alignment = Alignment(horizontal='center', wrap_text=True)
        ws.column_dimensions[col].width = 14
    ws.row_dimensions[2].height = 45
    for k in range(COMB_MAX):
        r = COMB_FILA0 + k
        terminos = '&'.join(
            f'IF(AND(ISNUMBER({c}{r}),{c}{r}<>0,{c}$2<>""),"+ "&ROUND({c}{r},2)&"·"&{c}$2&" ","")' for c in cols)
        ws[f'A{r}'] = f'=IF(LEN({terminos})=0,"","ASD{k + 1} = "&TRIM(MID({terminos},3,999)))'
    filas = list(combinaciones) if combinaciones else []
    for k in range(COMB_MAX):
        fila = filas[k] if k < len(filas) else [None] * ESTADOS_MAX
        for j, col in enumerate(cols):
            v = fila[j] if j < len(fila) else None
            celda = ws[f'{col}{COMB_FILA0 + k}']
            celda.value = None if v is None or (isinstance(v, str) and v.strip() == '') else v
            celda.fill = ENTRADA
            celda.number_format = '0.00'
    dv = DataValidation(type='decimal', operator='between', formula1='-100', formula2='100', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f'B{COMB_FILA0}:{cols[-1]}{COMB_FIN}')
    ws.freeze_panes = f'B{COMB_FILA0}'
    return ws



# ---------------------------------------------------------------- PARAMETROS y NORMA (hojas de la planilla)
# PARAMETROS: lo que usted elige o ingresa (listas desplegables). NORMA: valores de la norma con su referencia
# (solo lectura). El notebook lee ambas hojas: no hay valores de norma ni supuestos dentro del codigo.
PARAM_CATALOGO = [
    # CLAVE, concepto, valor (ejemplo), unidad, opciones, referencia, explicacion
    ('SISTEMA_SISMICO', 'Sistema estructural sismico', 'Marcos de acero de ductilidad media', '',
     'lista (hoja NORMA, tabla 4.3.2)', 'NTC Diseno por Sismo 2023, tabla 4.3.2, pag. 53',
     'Define Q, gamma SV, gamma OI y R0 del sistema.'),
    ('CRUJIAS_AMBAS', 'Tres o mas crujias resistentes en las dos direcciones', 'SÍ', '', 'SÍ / NO',
     'NTC Diseno por Sismo 2023, §3.3.1, pag. 42-43',
     'SÍ: k1 = 1.0. NO: k1 = 0.8 (menos de tres crujias en alguna direccion).'),
    ('ZONA_SISMICA', 'Zona sismica del sitio', 'B', '', 'A / B / C',
     'NTC Diseno por Sismo 2023, §3.1 (eq. 3.1.1)', 'Se usa si KS_METODO = SEGUN ZONA. Dato obligatorio.'),
    ('TS', 'Ts del sitio (SASID)', 0.5, 's', 'numero > 0', 'NTC Diseno por Sismo 2023, eq. 3.1.1 y SASID',
     'Periodo caracteristico del sitio. Dato del SASID. Obligatorio.'),
    ('TA', 'Ta del sitio (SASID)', 0.2, 's', 'numero > 0', 'NTC Diseno por Sismo 2023, §3.3.1b y SASID',
     'Limite de la meseta. k2 = 0 si T >= Ta (T de §6.4.1). Obligatorio.'),
    ('TB', 'Tb del sitio (SASID)', 1.0, 's', 'numero > Ta', 'NTC Diseno por Sismo 2023, §3.2 y SASID',
     'Limite superior de la meseta. Obligatorio.'),
    ('K_SASID', 'Factor k del SASID', 1.0, '', 'numero > 0', 'NTC Diseno por Sismo 2023, §3.2, eq. 3.2.1',
     "Q' = 1 + (Q-1)/k. Con k = 1, Q' = Q. Dato del SASID. Obligatorio."),
    ('C_SASID', 'Coeficiente sismico c (SASID)', 0.25, '', 'numero > 0',
     'NTC Diseno por Sismo 2023, §6.3, eq. 6.3.1', "Base de la fuerza de diseno V0 = c W0/(Q' R'). Obligatorio."),
    ('KS_METODO', 'Factor Ks para la distorsion LDNE', 'CONSERVADOR (Ks=1)', '',
     'CONSERVADOR (Ks=1) / SEGUN ZONA (ec. 3.1.1)', 'NTC Diseno por Sismo 2023, tabla 3.1.1, nota [3]; eq. 3.1.1',
     'CONSERVADOR: Ks = 1. SEGUN ZONA: Ks de la zona y de Ts.'),
    ('DEFORMABLES', 'Elementos no estructurales capaces de deformarse o separados', 'SÍ', '', 'SÍ / NO',
     'NTC Diseno por Sismo 2023, §1.7, pag. 26', 'SÍ: limite LDNE 0.004. NO: 0.002.'),
    ('FRAGILES', 'Elementos no estructurales fragiles unidos', 'NO', '', 'SÍ / NO',
     'NTC Criterios y Acciones, §4.1.1 b), pag. 8', 'SÍ: distorsion h/500. NO: h/250.'),
    ('VIENTO', 'Viento considerado en el diseno', 'NO', '', 'NO',
     'Criterio del proyecto (version actual)',
     'Esta version no considera viento. Los estados y combinaciones con W se omiten.'),
    ('KZ_TORSION', 'Factor Kz de pandeo torsional (extremos)', 1.0, '', '1.0 / 0.5',
     'AISC 360-22, E4 (Kz, factor de longitud efectiva para pandeo torsional)',
     '1.0: extremos sin restriccion al alabeo. 0.5: extremos con restriccion al alabeo y a la rotacion. Confirme segun sus conexiones.'),
    ('METODO', 'Metodo de analisis sismico', 'ESTÁTICO', '', 'ESTÁTICO',
     'NTC Diseno por Sismo 2023, §6.1-6.2',
     'Solo analisis estatico. El modal espectral no se usa en esta aplicacion.'),
]

# DECISION D15 (abierta): solo marcos de acero (tabla 4.3.2). Alternativa: agregar contraventeos y sistemas duales.
NORMA_SISTEMAS = [
    # NOMBRE, Q, gamma SV, gamma OI, R0, referencia
    ('Marcos de acero de ductilidad alta', 4.0, 0.030, 0.0075, 2.0,
     'NTC Diseno por Sismo 2023, tabla 4.3.2, i) Marcos, pag. 53; R0 de §3.3.1a'),
    ('Marcos de acero de ductilidad media', 3.0, 0.020, 0.0075, 2.0,
     'NTC Diseno por Sismo 2023, tabla 4.3.2, i) Marcos, pag. 53; R0 de §3.3.1a'),
    ('Marcos de acero de ductilidad baja', 2.0, 0.015, 0.0075, 1.75,
     'NTC Diseno por Sismo 2023, tabla 4.3.2, i) Marcos, pag. 53; R0 de §3.3.1a (Q < 3)'),
]

NORMA_VALORES = [
    # CLAVE, valor, unidad, referencia, explicacion
    ('LDNE_DEFORMABLES', 0.004, '', 'NTC Diseno por Sismo 2023, §1.7, pag. 26',
     'Limite de distorsion LDNE si los elementos no estructurales son deformables o estan separados.'),
    ('LDNE_NO', 0.002, '', 'NTC Diseno por Sismo 2023, §1.7, pag. 26', 'Limite LDNE en los demas casos.'),
    ('NTC_CA_H_FRAGILES', 500, '', 'NTC Criterios y Acciones, §4.1.1 b), pag. 8',
     'Distorsion horizontal h/500 con elementos no estructurales fragiles unidos.'),
    ('NTC_CA_H_OTROS', 250, '', 'NTC Criterios y Acciones, §4.1.1 b), pag. 8', 'Distorsion h/250 en otros casos.'),
    ('SEG2_FACTOR', 0.08, '', 'NTC Diseno por Sismo 2023, §2.4, eq. 2.4.1, pag. 32',
     'Efectos de segundo orden despreciables si la distorsion no excede 0.08 V/W.'),
    ('FLECHA_DIVISOR', 300, '', 'AISC 360-22, Comentario L2, pag. 16.1-543',
     'Flecha vertical maxima L/300 en vigas. El comentario indica que 1/300 del claro es visible y puede causar dano arquitectonico. La NTC-Acero no fija un numero (§11.4 remite a la NTC-CA).'),
    ('K1_SI', 1.0, '', 'NTC Diseno por Sismo 2023, §3.3.1a, pag. 42-43', 'k1 con tres o mas crujias en ambas direcciones.'),
    ('K1_NO', 0.8, '', 'NTC Diseno por Sismo 2023, §3.3.1a, pag. 42-43', 'k1 con menos de tres crujias en alguna direccion.'),
    ('K2_COEF', 0.5, '', 'NTC Diseno por Sismo 2023, §3.3.1b, pag. 43', 'k2 = 0.5 (1 - (T/Ta)^2) si T < Ta.'),
    ('K2_EXP', 2, '', 'NTC Diseno por Sismo 2023, §3.3.1b, pag. 43', 'Exponente de T/Ta en k2.'),
    ('RP_SV', 1.0, '', 'NTC Diseno por Sismo 2023, §3.3.2a', 'R-prima para Seguridad de Vida = R.'),
    ('RP_OI', 0.75, '', 'NTC Diseno por Sismo 2023, §3.3.2b', 'R-prima para Ocupacion Inmediata = 0.75 R.'),
    ('KS_A_DEN', 6, '', 'NTC Diseno por Sismo 2023, eq. 3.1.1 (zona A)', 'Ks = 1/6 en zona A.'),
    ('KS_C_DEN', 4, '', 'NTC Diseno por Sismo 2023, eq. 3.1.1 (zona C)', 'Ks = 1/4 en zona C.'),
    ('KS_B_A', 6, '', 'NTC Diseno por Sismo 2023, eq. 3.1.1 (zona B)', 'Zona B: Ks = 1/[6 - 4(Ts - 0.5)].'),
    ('KS_B_B', 4, '', 'NTC Diseno por Sismo 2023, eq. 3.1.1 (zona B)', 'Coeficiente de Ts en la zona B.'),
    ('KS_B_C', 0.5, 's', 'NTC Diseno por Sismo 2023, eq. 3.1.1 (zona B)', 'Valor de Ts en la zona B.'),
    ('G', 9.81, 'm/s2', 'NTC Diseno por Sismo 2023, §6.4.1', 'Aceleracion de la gravedad para el periodo T.'),
    ('NTC_LR_PATIN', 0.56, 'sqrt(E/Fy)', 'NTC-Acero 2020, tabla 3.2.1, pag. 57', 'lambda_r de patin (I y canal) en compresion.'),
    ('NTC_LR_ALMA', 1.49, 'sqrt(E/Fy)', 'NTC-Acero 2020, tabla 3.2.1, pag. 57', 'lambda_r de alma en compresion.'),
    ('NTC_LR_PATA', 0.45, 'sqrt(E/Fy)', 'NTC-Acero 2020, tabla 3.2.1, pag. 57', 'lambda_r de ala de angulo en compresion.'),
    ('NTC_LIM_PATIN_PL', 0.30, 'sqrt(E/Fy)', 'NTC-Acero 2020, tabla 3.2.2, pag. 58', 'Patin tipo 1 (flexion).'),
    ('NTC_LIM_PATIN_P', 0.38, 'sqrt(E/Fy)', 'NTC-Acero 2020, tabla 3.2.2, pag. 58', 'Patin tipo 2 (flexion) y limite media de Tabla 12.1.2.'),
    ('NTC_LIM_PATIN_R', 1.00, 'sqrt(E/Fy)', 'NTC-Acero 2020, tabla 3.2.2, pag. 58', 'Patin tipo 3 (flexion).'),
    ('NTC_LIM_ALMA_PL', 2.45, 'sqrt(E/Fy)', 'NTC-Acero 2020, tabla 3.2.2, pag. 58', 'Alma tipo 1 (flexion).'),
    ('NTC_LIM_ALMA_P', 3.76, 'sqrt(E/Fy)', 'NTC-Acero 2020, tabla 3.2.2, pag. 58', 'Alma tipo 2 (flexion).'),
    ('NTC_LIM_ALMA_R', 5.70, 'sqrt(E/Fy)', 'NTC-Acero 2020, tabla 3.2.2, pag. 58', 'Alma tipo 3 (flexion).'),
    ('NTC_LIM_PATA_P', 0.54, 'sqrt(E/Fy)', 'NTC-Acero 2020, tabla 3.2.2, pag. 58', 'Ala de angulo tipo 2 (flexion).'),
    ('NTC_LIM_PATA_R', 0.91, 'sqrt(E/Fy)', 'NTC-Acero 2020, tabla 3.2.2, pag. 58', 'Ala de angulo tipo 3 (flexion).'),
    ('NTC_KLR_COMP', 200, '', 'NTC-Acero 2020, §2.3.2, pag. 41', 'KL/r maximo en compresion (obligatorio).'),
    ('NTC_KLR_REF_PRINC', 240, '', 'NTC-Acero 2020, §2.3.2 (comentario)', 'L/r de referencia en tension, miembros principales.'),
    ('NTC_KLR_REF_CONTR', 300, '', 'NTC-Acero 2020, §2.3.2 (comentario)', 'L/r de referencia en tension, contraventeos.'),
    ('NTC_KLR_DUCTIL', 60, '', 'NTC-Acero 2020, §12.1.3.1, pag. 207', 'KL/r maximo en columnas ductiles.'),
    ('AISC_OMEGA_TFLU', 1.67, '', 'AISC 360-22, D2 (fluencia en traccion)', 'Factor de seguridad ASD, traccion por fluencia.'),
    ('AISC_OMEGA_TFRA', 2.00, '', 'AISC 360-22, D2 (fractura en traccion)', 'Factor de seguridad ASD, traccion por fractura.'),
    ('AISC_OMEGA_C', 1.67, '', 'AISC 360-22, E1 (compresion)', 'Factor de seguridad ASD en compresion.'),
    ('AISC_OMEGA_B', 1.67, '', 'AISC 360-22, F1 (flexion)', 'Factor de seguridad ASD en flexion.'),
    ('AISC_OMEGA_V', 1.67, '', 'AISC 360-22, G1 (cortante)', 'Factor de seguridad ASD en cortante.'),
    ('AISC_OMEGA_V_LAM', 1.50, '', 'AISC 360-22, G2.1(a)', 'Cortante en alma de I laminada con h/tw <= 2.24 sqrt(E/Fy).'),
    ('AISC_KV_I', 5.34, '', 'AISC 360-22, G2.2', 'kv de alma sin atiesadores.'),
    ('AISC_KV_ANG', 1.2, '', 'AISC 360-22, G3', 'kv de la pata de angulo.'),
    ('AISC_CB_MAX_ANG', 1.5, '', 'AISC 360-22, F10-4', 'Cb maximo para angulos.'),
    ('AISC_LP_PATIN', 0.38, 'sqrt(E/Fy)', 'AISC 360-22, Tabla B4.1b', 'lambda_p de ala (flexion, I y canal).'),
    ('AISC_LR_PATIN', 1.00, 'sqrt(E/Fy)', 'AISC 360-22, Tabla B4.1b', 'lambda_r de ala (flexion, I y canal).'),
    ('AISC_CV_LIM', 1.10, '', 'AISC 360-22, G2.2', 'Limite de h/tw para Cv = 1 (factor 1.10 sqrt(kv E/Fy)).'),
    ('AISC_HTW_LAM', 2.24, '', 'AISC 360-22, G2.1(a)', 'Limite h/tw de I laminada con Ωv = 1.50.'),
    ('AISC_LIM_ANG_E4', 0.71, '', 'AISC 360-22, E4 y F10.3 (angulos)', 'b/t de angulo sin pandeo flexotorsional.'),
    ('AISC_E5_RAT_LIM', 80, '', 'AISC 360-22, E5', 'L/ra de corte entre E5-1 y E5-2.'),
    ('AISC_B41A_C1_ALMA', 0.18, '', 'AISC 360-22, Tabla B4.1a', 'Coeficiente c1 de alma (E7).'),
    ('AISC_B41A_C2_ALMA', 1.31, '', 'AISC 360-22, Tabla B4.1a', 'Coeficiente c2 de alma (E7).'),
    ('AISC_B41A_C1_PATA', 0.22, '', 'AISC 360-22, Tabla B4.1a', 'Coeficiente c1 de pata (E7).'),
    ('AISC_B41A_C2_PATA', 1.49, '', 'AISC 360-22, Tabla B4.1a', 'Coeficiente c2 de pata (E7).'),
    ('AISC_LR_PATA_B41A', 0.45, 'sqrt(E/Fy)', 'AISC 360-22, Tabla B4.1a', 'lambda_r de pata de angulo (E7).'),
]


def _cabecera_en(ws, fila, columnas, anchos):
    """Cabecera de tabla en la fila indicada (la cabecera de _encabezado va siempre en la fila 1)."""
    for c, nombre in enumerate(columnas, start=1):
        celda = ws.cell(row=fila, column=c, value=nombre)
        celda.font = NEGRITA
        celda.fill = ENCABEZADO
        celda.alignment = Alignment(horizontal='center', wrap_text=True)
        ws.column_dimensions[celda.column_letter].width = anchos[c - 1]


def _hoja_normas_y_parametros(wb):
    """Crea las hojas NORMA (solo lectura) y PARAMETROS (listas desplegables y datos a ingresar)."""
    from openpyxl.worksheet.datavalidation import DataValidation as DV
    ws_n = wb.create_sheet('NORMA')
    ws_n['A1'] = 'NORMA: valores de la norma usados por el calculo (solo lectura). Cada valor tiene su referencia.'
    ws_n['A1'].font = NEGRITA
    ws_n['A3'] = 'SISTEMAS ESTRUCTURALES (NTC Diseno por Sismo 2023, tabla 4.3.2)'
    ws_n['A3'].font = NEGRITA
    _cabecera_en(ws_n, 4, ['NOMBRE DEL SISTEMA', 'Q', 'gamma SV', 'gamma OI', 'R0', 'REFERENCIA'],
                 [44, 8, 11, 11, 8, 70])
    for k, (nombre, q, gsv, goi, r0, ref) in enumerate(NORMA_SISTEMAS):
        fila = 5 + k
        for col, valor in zip('ABCDEF', [nombre, q, gsv, goi, r0, ref]):
            ws_n[f'{col}{fila}'] = valor
    fila_v = 5 + len(NORMA_SISTEMAS) + 2
    ws_n[f'A{fila_v}'] = 'VALORES DE NORMA (usados por el calculo)'
    ws_n[f'A{fila_v}'].font = NEGRITA
    _cabecera_en(ws_n, fila_v + 1, ['CLAVE', 'VALOR', 'UNIDAD', 'REFERENCIA', 'EXPLICACION'], [44, 12, 12, 60, 90])
    for k, (clave, valor, unidad, ref, expl) in enumerate(NORMA_VALORES):
        fila = fila_v + 2 + k
        for col, dato in zip('ABCDE', [clave, valor, unidad, ref, expl]):
            ws_n[f'{col}{fila}'] = dato
    ws_n.protection.sheet = True
    ws_n.freeze_panes = 'A4'

    ws_p = wb.create_sheet('PARAMETROS')
    ws_p['A1'] = 'PARAMETROS DE DISENO: elija en las listas (columna C, amarilla). Sin estos datos no se hace el diseno.'
    ws_p['A1'].font = NEGRITA
    ws_p['A2'] = ('Los datos del SASID (Ts, Ta, Tb, k, c) y la zona vienen de su estudio de sitio. Los valores de '
                  'ejemplo son para probar: reemplacelos por los suyos.')
    _cabecera_en(ws_p, 4, ['CLAVE', 'CONCEPTO', 'VALOR', 'UNIDAD', 'OPCIONES', 'REFERENCIA NORMATIVA', 'EXPLICACION'],
                 [22, 44, 40, 8, 40, 52, 70])
    dv_lista = {
        'CRUJIAS_AMBAS': DV(type='list', formula1='"SÍ,NO"', allow_blank=False),
        'ZONA_SISMICA': DV(type='list', formula1='"A,B,C"', allow_blank=False),
        'KS_METODO': DV(type='list', formula1='"CONSERVADOR (Ks=1),SEGUN ZONA (ec. 3.1.1)"', allow_blank=False),
        'DEFORMABLES': DV(type='list', formula1='"SÍ,NO"', allow_blank=False),
        'FRAGILES': DV(type='list', formula1='"SÍ,NO"', allow_blank=False),
        'VIENTO': DV(type='list', formula1='"NO"', allow_blank=False),
        'METODO': DV(type='list', formula1='"ESTÁTICO"', allow_blank=False),
        'KZ_TORSION': DV(type='list', formula1='"1.0,0.5"', allow_blank=False),
        'SISTEMA_SISMICO': DV(type='list', formula1=f'NORMA!$A$5:$A${4 + len(NORMA_SISTEMAS)}', allow_blank=False),
    }
    for dv in dv_lista.values():
        ws_p.add_data_validation(dv)
    dv_num = DV(type='decimal', operator='greaterThan', formula1='0', allow_blank=False)
    ws_p.add_data_validation(dv_num)
    for k, (clave, concepto, valor, unidad, opciones, ref, expl) in enumerate(PARAM_CATALOGO):
        fila = 5 + k
        ws_p[f'A{fila}'] = clave
        ws_p[f'B{fila}'] = concepto
        ws_p[f'C{fila}'] = valor
        ws_p[f'C{fila}'].fill = ENTRADA
        ws_p[f'D{fila}'] = unidad
        ws_p[f'E{fila}'] = opciones
        ws_p[f'F{fila}'] = ref
        ws_p[f'G{fila}'] = expl
        if clave in dv_lista:
            dv_lista[clave].add(f'C{fila}')
        if clave in ('TS', 'TA', 'TB', 'K_SASID', 'C_SASID'):
            dv_num.add(f'C{fila}')
    ws_p.freeze_panes = 'A5'
    return ws_p, ws_n


def escribir_planilla(ruta, filas_nodos, filas_barras, imagen=None, filas_cargas=None, estados=None,
                      materiales=None, combinaciones=None, longitudes=None, listas=None,
                      grupos_perfil=None, fu_matriz=None):
    """Escribe el libro completo con los datos dados. Cada fila de NODOS: NODOS_COLS; de BARRAS: BARRAS_COLS."""
    wb = openpyxl.Workbook()
    ws_i = wb.active; ws_i.title = 'INSTRUCCIONES'
    texto = [
        'PLANTILLA DE SOPORTES: como llenarla',
        '',
        'PARAMETROS: elija en las listas desplegables (columna C, amarilla) e ingrese Ts, Ta, Tb, k y c del SASID.',
        'NORMA: valores de la norma con su referencia. Solo lectura: el calculo los toma de aqui.',
        'LONGITUDES: LX, LY, LB, KX, KY y CB son obligatorios en cada barra. No se suponen valores.',
        'BARRAS: DUCTILIDAD (ALTA o MEDIA) es obligatoria en COLUMNA y VIGA.',
        'VIENTO: esta version no considera viento; no se usan los estados ni las combinaciones con W.',
        '',
        'NODOS: una fila por nodo. X, Y, Z en metros. Capacidad: 98 nodos.',
        'UX, UY, UZ, RX, RY, RZ: SI = ese grado de libertad queda restringido en el nodo. Vacio o NO = libre.',
        '   Empotrado = los 6 en SI. Rotulado = UX, UY, UZ en SI (giros libres). Rodillo = solo UZ, etc.',
        'BARRAS: una fila por barra. NODO_I y NODO_J son IDs de la hoja NODOS. Capacidad: 106 barras.',
        'ELEMENTO: COLUMNA, VIGA, ARRIOSTRE o DIAGONAL (lista).',
        'DUCTILIDAD: ALTA o MEDIA (lista). Vacio = no se verifica la Tabla 12.1.2 de la NTC para esta barra.',
        'PERFIL: nombre Gerdau rev04 (lista ordenada por familia y seccion).',
        'MATERIAL: elija la calidad de la lista (base de datos de la hoja MATERIALES). Es obligatorio: vacio da error.',
        'EJE_FUERTE_X, _Y, _Z: vector libre del eje fuerte (direccion del peralte) en coordenadas globales.',
        '   Vacio = direccion por defecto del motor. Basta una componente (las vacias valen 0). No puede ser paralelo a la barra.',
        'CONEXION_I y CONEXION_J: empotrado o rotulado en cada extremo de la barra. Vacio = empotrado.',
        'Ver la hoja CONEXIONES para el significado de cada tipo.',
        'REPORTAR (NODOS y BARRAS): SI = el resultado de ese nodo o barra sale en el Excel de resultados. Vacio = no sale.',
        'MATERIALES: E (modulo de elasticidad, kgf/cm2) y NU (Poisson) de cada calidad. Son datos suyos: el analisis los lee de aqui.',
        'ESTADOS: PESO PROPIO = SI en el estado donde OpenSees aplica el peso de la seccion (masa Gerdau, kgf/m).',
        'LONGITUDES: por barra, LX y LY (m) longitud no arriostrada en X e Y, KX y KY (factor K), LB (m) para pandeo lateral, CB. Vacio = supuesto.',
        'E5 (angulos LI): SI en las cuatro columnas solo si la pata cumple: (1) carga en los extremos por una pata; (2) union soldada o con 2 pernos o mas; '
        '(3) sin cargas transversales intermedias; (4) miembro individual o alma de armadura plana. Vacio o NO = K L/rz y H2.',
        'LI CONEXION: UNA PATA o DOS PATAS (ambas patas conectadas). LI LONGITUD CONEXION (m): longitud de la conexion; vacio = longitud de la barra.',
        'VISTA_VIVA: planta, alzado y 3D esquematico que se actualizan al cambiar NODOS y BARRAS.',
        '   Cambie el nivel Z (C3), la cota Y (C4), el azimut (C5), la elevacion (C6) y el largo de la flecha (C7).',
        '',
        'No cambiar los nombres de las hojas ni de las columnas. Las filas vacias se ignoran.',
    ]
    for linea in texto:
        ws_i.append([linea])
    ws_i['A1'].font = Font(bold=True, size=13)
    ws_i.column_dimensions['A'].width = 115

    ws_n = wb.create_sheet('NODOS')
    _encabezado(ws_n, NODOS_COLS, [8, 12, 12, 12, 7, 7, 7, 7, 7, 7, 36, 12])
    for f in filas_nodos:
        ws_n.append(f)
    for _ in range(FIN_N - 1 - len(filas_nodos)):
        ws_n.append([None] * len(NODOS_COLS))
    dv_grados = DataValidation(type='list', formula1='"SI,NO"', allow_blank=True)
    ws_n.add_data_validation(dv_grados); dv_grados.add(f'E2:J{FIN_N}')
    dv_rep_n = DataValidation(type='list', formula1='"SI,NO"', allow_blank=True)
    ws_n.add_data_validation(dv_rep_n); dv_rep_n.add(f'L2:L{FIN_N}')

    ws_b = wb.create_sheet('BARRAS')
    _encabezado(ws_b, BARRAS_COLS, [8, 10, 10, 14, 18, 13, 13, 13, 14, 14, 12, 30, 12, 14])
    for f in filas_barras:
        ws_b.append(f)
    for _ in range(FIN_B - 1 - len(filas_barras)):
        ws_b.append([None] * len(BARRAS_COLS))
    dv_elem = DataValidation(type='list', formula1='"' + ','.join(ELEMENTOS) + '"', allow_blank=True)
    # PERFIL: lista que depende del ELEMENTO de la fila (LISTA_COLUMNA, LISTA_VIGA, ...). Sin diseno, todos los perfiles.
    dv_perf = DataValidation(type='list', formula1='INDIRECT("LISTA_"&$D2)', allow_blank=True)
    dv_vec = DataValidation(type='decimal', operator='between', formula1='-1000000', formula2='1000000',
                            allow_blank=True)
    dv_ci = DataValidation(type='list', formula1='"' + ','.join(TIPOS_CONEXION) + '"', allow_blank=True)
    dv_cj = DataValidation(type='list', formula1='"' + ','.join(TIPOS_CONEXION) + '"', allow_blank=True)
    dv_mat = DataValidation(type='list', formula1=f'MATERIALES!$A$2:$A${MAT_FIN}', allow_blank=True)
    dv_rep_b = DataValidation(type='list', formula1='"SI,NO"', allow_blank=True)
    dv_duc_b = DataValidation(type='list', formula1='"ALTA,MEDIA"', allow_blank=True)
    lista_dv = [(dv_elem, f'D2:D{FIN_B}'), (dv_vec, f'F2:H{FIN_B}'),
                (dv_ci, f'I2:I{FIN_B}'), (dv_cj, f'J2:J{FIN_B}'), (dv_mat, f'K2:K{FIN_B}'),
                (dv_rep_b, f'M2:M{FIN_B}'), (dv_duc_b, f'N2:N{FIN_B}')]
    if grupos_perfil is None:
        lista_dv.insert(1, (dv_perf, f'E2:E{FIN_B}'))      # sin diseno: perfil por barra
    else:
        for r in range(2, FIN_B + 1):                       # con diseno: el perfil lo da su grupo (PERFIL_GRUPO)
            ws_b.cell(row=r, column=5, value=f'=IFERROR(INDEX(PERFIL_GRUPO!$B$2:$B$5,MATCH(D{r},PERFIL_GRUPO!$A$2:$A$5,0)),"")')
    for dv, rango in lista_dv:
        ws_b.add_data_validation(dv); dv.add(rango)

    _hoja_longitudes(wb, longitudes)
    ws_c = wb.create_sheet('CONEXIONES')
    _encabezado(ws_c, ['TIPO', 'EN NODOS (UX a RZ = SI)', 'EN EXTREMOS DE BARRA (CONEXION_I / CONEXION_J)',
                       'USO TIPICO'], [14, 44, 50, 46])
    ws_c.append(['empotrado', 'SI en UX, UY, UZ, RX, RY y RZ (base de columna empotrada).',
                 'El extremo transmite momento: la barra sigue el giro del nodo (union rigida).',
                 'Base de columna, nudo rigido de marco.'])
    ws_c.append(['rotulado', 'SI en UX, UY y UZ; RX, RY y RZ en NO (giros libres).',
                 'El momento en el extremo es cero (articulado).',
                 'Apoyo articulado, viga simple, extremo de arriostre.'])
    ws_c.append(['(vacio)', 'En NODOS: NO o vacio en los 6 grados: nodo libre.', 'En BARRAS: se toma empotrado.', '-'])
    for fila in ws_c.iter_rows(min_row=2):
        for celda in fila:
            celda.alignment = Alignment(wrap_text=True, vertical='top')

    ws_l = wb.create_sheet('LISTAS')
    _encabezado(ws_l, ['PERFIL', 'ESTADO', 'MASA (kg/m)', 'ELEMENTO'], [18, 20, 14, 14])
    for k, (_, nombre) in enumerate(PERFILES_ORDEN):
        p = G.PERFILES[nombre]
        ws_l.cell(row=k + 2, column=1, value=nombre)
        ws_l.cell(row=k + 2, column=2, value=p['estado'])
        ws_l.cell(row=k + 2, column=3, value=p['masa_kg_m'])
    for k, e in enumerate(ELEMENTOS):
        ws_l.cell(row=k + 2, column=4, value=e)
    _hoja_listas_grupo(wb, ws_l, listas)
    if grupos_perfil is not None and fu_matriz is not None:
        _hojas_diseno_vivo(wb, grupos_perfil, fu_matriz)

    ws_calc = _hoja_calculo(wb)
    ws_3d, col_3d = _hoja_3d(wb)
    _hoja_estados(wb, estados or [])
    _hoja_materiales(wb, materiales if materiales is not None else MATERIALES_DEFAULT)
    _hoja_combinaciones(wb, combinaciones if combinaciones is not None else COMBINACIONES_DEFAULT)
    _hoja_normas_y_parametros(wb)
    ws_cc, col_cc = _hoja_calc_cargas(wb, col_3d)
    primer_estado = estados[0][0] if estados else ''
    ws_car = _hoja_cargas(wb, filas_cargas or [], primer_estado)
    _grafico_cargas(ws_car, ws_cc, col_cc, ws_3d, col_3d)

    ws_v = wb.create_sheet('VISTA_VIVA')
    ws_v['A1'] = 'Vista en vivo de la planilla: se actualiza al cambiar NODOS o BARRAS.'
    ws_v['A1'].font = Font(bold=True, size=12)
    ws_v['A3'] = 'Nivel Z para planta (m)'
    ws_v['C3'] = 3.5
    ws_v['A4'] = 'Cota Y para alzado (m)'
    ws_v['C4'] = 0
    for celda in ('C3', 'C4'):
        ws_v[celda].fill = ENTRADA
    ws_v['A5'] = 'Azimut (grados)'
    ws_v['C5'] = 30
    ws_v['A6'] = 'Elevacion (grados)'
    ws_v['C6'] = 20
    ws_v['A7'] = 'Largo flecha eje fuerte (m)'
    ws_v['C7'] = 0.8
    for celda in ('C5', 'C6', 'C7'):
        ws_v[celda].fill = ENTRADA
    ws_v['A8'] = 'Cota X para alzado lateral Y-Z (m)'
    ws_v['C8'] = 0
    ws_v['C8'].fill = ENTRADA
    ws_v['A9'] = 'Cambie los angulos para girar la vista 3D esquematica (abajo).'
    ws_v.column_dimensions['A'].width = 26
    _graficos(ws_v, ws_calc)
    _grafico_lateral(ws_v, ws_calc)
    _grafico_3d(ws_v, ws_3d, col_3d)
    _grafico_3d_rotulas(ws_v, ws_3d, col_3d)

    wb.calculation = CalcProperties(fullCalcOnLoad=True)
    wb.save(ruta)
    return ruta


def _sin_suavizado(ruta_xlsx):
    """LibreOffice guarda las series con suavizado (smooth=1): las flechas del eje fuerte se verian curvas.
    Se reescriben los graficos con smooth=0 (lineas rectas)."""
    import zipfile
    tmp = ruta_xlsx + '.tmp'
    with zipfile.ZipFile(ruta_xlsx) as origen, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as destino:
        for item in origen.infolist():
            datos = origen.read(item.filename)
            if item.filename.startswith('xl/charts/chart') and item.filename.endswith('.xml'):
                datos = datos.replace(b'<c:smooth val="1"/>', b'<c:smooth val="0"/>')
            destino.writestr(item, datos)
    os.replace(tmp, ruta_xlsx)


def guardar_con_valores(ruta):
    """Recalcula el libro con LibreOffice (si esta instalado) para que las formulas y graficos tengan valores
    guardados: asi se ven tambien en visores que no calculan. Sin LibreOffice, Excel calcula al abrir."""
    import shutil, subprocess, tempfile
    soffice = shutil.which('soffice') or shutil.which('libreoffice')
    if not soffice:
        print('LibreOffice no disponible: Excel calcula la hoja al abrirla.')
        return
    tmp = tempfile.mkdtemp()
    subprocess.run([soffice, '--headless', '--calc', '--convert-to', 'xlsx', '--outdir', tmp, ruta],
                   capture_output=True, timeout=300)
    salida = os.path.join(tmp, os.path.basename(ruta))
    if os.path.exists(salida):
        _sin_suavizado(salida)
        shutil.move(salida, ruta)
        print('Valores calculados guardados en', ruta)
    else:
        print('No se pudo recalcular con LibreOffice; Excel calcula la hoja al abrirla.')


def crear_plantilla(ruta=None, sobrescribir=False):
    ruta = ruta or os.path.join(os.getcwd(), 'plantilla_soportes.xlsx')
    if os.path.exists(ruta) and not sobrescribir:
        print('Ya existe', ruta, '- no se sobrescribe la planilla llenada.')
        return ruta
    nodos, barras = ejemplo_filas()
    escribir_planilla(ruta, nodos, barras, filas_cargas=ejemplo_cargas(), estados=ejemplo_estados(),
                      materiales=MATERIALES_DEFAULT, combinaciones=COMBINACIONES_DEFAULT,
                      longitudes=ejemplo_longitudes())
    guardar_con_valores(ruta)
    print('Plantilla creada:', ruta)
    return ruta


def cargar_plantilla(ruta=None):
    ruta = ruta or os.path.join(os.getcwd(), 'plantilla_soportes.xlsx')
    if os.path.exists(ruta):
        print('Ya existe, se usa tal cual:', ruta)
    else:
        with open(ruta, 'wb') as f:
            f.write(base64.b64decode(PLANTILLA_B64))
        print('Plantilla escrita en:', ruta)
    return ruta


# Plantilla incrustada en el notebook (mismo archivo que plantilla_soportes.xlsx del repositorio)
PLANTILLA_B64 = '<plantilla omitida: ver plantilla/>'
RUTA_PLANTILLA = cargar_plantilla() if PLANTILLA_B64 else crear_plantilla()
_hojas = pd.read_excel(RUTA_PLANTILLA, sheet_name=None, dtype=object)
print('Hojas cargadas:', list(_hojas))
display(_hojas['NODOS'].head(8))
display(_hojas['BARRAS'].head(8))


# ---------------- DISENO POR GRUPO EN EXCEL: el perfil se elige por grupo y el FU se recalcula ----------------
def _hojas_diseno_vivo(wb, grupos_perfil, fu_matriz):
    """PERFIL_GRUPO: un perfil por grupo (desplegable), con FU y esbeltez maximos de sus barras.
    FU_BARRAS: FU y esbeltez de cada barra con su perfil (formulas). FU_MATRIZ: FU de cada barra con cada perfil
    del catalogo, calculado al ejecutar el bloque 10. Al cambiar el perfil de un grupo, Excel recalcula todo."""
    from openpyxl.formatting.rule import FormulaRule
    from openpyxl.styles import PatternFill as _PF
    rojo, verde = _PF('solid', fgColor='F8CBAD'), _PF('solid', fgColor='C6EFCE')

    ws_g = wb.create_sheet('PERFIL_GRUPO')
    _encabezado(ws_g, ['GRUPO', 'PERFIL ELEGIDO', 'FU MAXIMO', 'FU ESBELTEZ LOCAL', 'FU ESBELTEZ GLOBAL',
                       'ESTADO', 'BARRAS'], [14, 26, 14, 18, 20, 14, 10])
    for k, g in enumerate(GRUPOS_LISTA):
        r = k + 2
        ws_g.cell(row=r, column=1, value=g)
        ws_g.cell(row=r, column=2, value=grupos_perfil.get(g))
        ws_g.cell(row=r, column=7, value=f'=COUNTIF(FU_BARRAS!$B$2:$B${FIN_B},A{r})')
        for col, letra in ((3, 'E'), (4, 'F'), (5, 'G')):
            rango = f'FU_BARRAS!${letra}$2:${letra}${FIN_B}'
            ws_g.cell(row=r, column=col, value=(
                f'=IF(G{r}=0,"sin barras",IF(COUNTIFS(FU_BARRAS!$B$2:$B${FIN_B},A{r},{rango},">=0")=0,"no aplica",'
                f'_xlfn.MAXIFS({rango},FU_BARRAS!$B$2:$B${FIN_B},A{r})))'))
        ws_g.cell(row=r, column=6, value=f'=IF(ISNUMBER(C{r}),IF(C{r}<=1,"CUMPLE","NO CUMPLE"),C{r})')
        dv = DataValidation(type='list', formula1=f'LISTA_{g}', allow_blank=True, errorStyle='warning',
                            showErrorMessage=True, errorTitle='Perfil fuera de la lista',
                            error='Este perfil no cumple para el grupo. Se usara igual: revise el FU.')
        ws_g.add_data_validation(dv); dv.add(f'B{r}')
    ws_g.cell(row=7, column=1, value='Elija el perfil de cada grupo: se aplica a todas sus barras y el FU se recalcula. '
                                     'Verde = FU <= 1 (cumple), rojo = FU > 1.')
    ws_g.conditional_formatting.add('C2:E5', FormulaRule(formula=['AND(ISNUMBER(C2),C2>1)'], fill=rojo))
    ws_g.conditional_formatting.add('C2:E5', FormulaRule(formula=['AND(ISNUMBER(C2),C2<=1)'], fill=verde))

    ws_f = wb.create_sheet('FU_BARRAS')
    _encabezado(ws_f, ['ID', 'ELEMENTO', 'PERFIL', 'FILA (auxiliar)', 'FU MAXIMO', 'FU ESBELTEZ LOCAL',
                       'FU ESBELTEZ GLOBAL', 'FU DUCTILIDAD', 'CASO QUE GOBIERNA', 'ESTADO', 'AVISO'],
                [8, 13, 22, 12, 12, 16, 16, 15, 26, 16, 36])
    for r in range(2, FIN_B + 1):
        ws_f.cell(row=r, column=1, value=f'=IF(BARRAS!A{r}="","",BARRAS!A{r})')
        ws_f.cell(row=r, column=2, value=f'=IF(A{r}="","",BARRAS!D{r})')
        ws_f.cell(row=r, column=3, value=f'=IF(A{r}="","",BARRAS!E{r})')
        ws_f.cell(row=r, column=4, value=f'=IF(A{r}="","",IFERROR(MATCH(A{r}&"|"&C{r},FU_MATRIZ!$A:$A,0),""))')
        for col, letra in ((5, 'E'), (6, 'G'), (7, 'H'), (8, 'I'), (9, 'J')):
            ws_f.cell(row=r, column=col, value=f'=IF(D{r}="","",INDEX(FU_MATRIZ!${letra}:${letra},D{r}))')
        ws_f.cell(row=r, column=10, value=(f'=IF(A{r}="","",IF(D{r}="","SIN DATO: perfil fuera del diseno",'
                                           f'INDEX(FU_MATRIZ!$K:$K,D{r})))'))
        ws_f.cell(row=r, column=11, value=(f'=IF(D{r}="","",IF(B{r}<>INDEX(FU_MATRIZ!$D:$D,D{r}),'
                                           f'"ELEMENTO cambio: ejecute el bloque 10",""))'))
    ws_f.conditional_formatting.add(f'E2:G{FIN_B}', FormulaRule(formula=['AND(ISNUMBER(E2),E2>1)'], fill=rojo))
    ws_f.conditional_formatting.add(f'E2:G{FIN_B}', FormulaRule(formula=['AND(ISNUMBER(E2),E2<=1)'], fill=verde))
    ws_f.freeze_panes = 'A2'

    ws_m = wb.create_sheet('FU_MATRIZ')
    _encabezado(ws_m, COLS_MATRIZ_XL, [26, 6, 22, 14, 12, 12, 16, 18, 20, 24, 14])
    for fila in fu_matriz.itertuples(index=False):
        ws_m.append([None if (isinstance(v, float) and v != v) else (v.item() if hasattr(v, 'item') else v)
                     for v in fila])
    ws_m.freeze_panes = 'A2'
