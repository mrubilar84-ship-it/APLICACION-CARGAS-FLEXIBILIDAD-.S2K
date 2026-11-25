"""Prueba del aviso por formulas sin valor calculado en las hojas de entrada (bloque 7 del notebook).
Una formula de una hoja de entrada sin valor guardado se leeria como vacia: debe salir como ERROR.
Uso:  python3 test_formulas_sin_valor.py   Sale con codigo 1 si alguna comprobacion falla.
"""
import ast
import os
import sys
import tempfile

import openpyxl

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FUENTES = os.path.join(RAIZ, 'fuentes_notebook')
FALLOS = []


def chequeo(nombre, ok, detalle=''):
    print(('OK    ' if ok else 'FALLA ') + nombre + (f'  [{detalle}]' if detalle else ''))
    if not ok:
        FALLOS.append(nombre)


def _cargar():
    ruta = os.path.join(FUENTES, 'celda7_validar.py')
    arbol = ast.parse(open(ruta, encoding='utf-8').read(), ruta)
    nombres = {'formulas_sin_valor', 'mensajes_formulas'}
    cuerpo = [n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name in nombres]
    asign = [n for n in arbol.body if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == 'HOJAS_ENTRADA_FORMULAS' for t in n.targets)]
    espacio = {}
    exec(compile(ast.Module(body=asign + cuerpo, type_ignores=[]), ruta, 'exec'), espacio)
    return espacio


M = _cargar()
with tempfile.TemporaryDirectory() as tmp:
    ruta = os.path.join(tmp, 'prueba.xlsx')
    wb = openpyxl.Workbook()
    wb.active.title = 'CARGAS'
    hoja = wb.active
    hoja['A1'] = 1
    hoja['B2'] = '=A1*2'                       # formula de entrada sin valor guardado (openpyxl no calcula)
    wb.create_sheet('CALCULO')['B2'] = '=A1*3'   # hoja de calculo: no es de entrada
    wb.create_sheet('NODOS')['A1'] = 5
    wb.save(ruta)
    h = M['formulas_sin_valor'](ruta)
    chequeo('formula sin valor en CARGAS se detecta', h.get('CARGAS') == ['B2'], str(h))
    chequeo('formula de hoja de calculo no se revisa', 'CALCULO' not in h)
    msgs = M['mensajes_formulas'](ruta)
    chequeo('el aviso es ERROR y nombra la celda', any(m[2] == 'ERROR' and 'B2' in m[3] for m in msgs), str(msgs))
    ruta2 = os.path.join(tmp, 'valor.xlsx')
    wb2 = openpyxl.Workbook()
    wb2.active['A1'] = 2
    wb2.active['B1'] = 7
    wb2.save(ruta2)
    chequeo('sin formulas: sin mensajes', M['mensajes_formulas'](ruta2) == [])

# Caso a mano (XML): A1 con valor; A2 resultado texto vacio (Excel: t="str"); A3 formula sin valor (openpyxl: <v></v>)
with tempfile.TemporaryDirectory() as tmp:
    import zipfile
    ruta3 = os.path.join(tmp, 'xml.xlsx')
    hoja = ('<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetData><row r="1">'
            '<c r="A1"><f>1+1</f><v>2</v></c>'
            '<c r="A2" t="str"><f>IF(1=0,1,"")</f><v/></c>'
            '<c r="A3"><f>3+3</f><v></v></c>'
            '<c r="A4"><v>5</v></c>'
            '</row></sheetData></worksheet>')
    with zipfile.ZipFile(ruta3, 'w') as z:
        z.writestr('xl/workbook.xml', '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="CARGAS" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="x" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr('xl/worksheets/sheet1.xml', hoja)
    h3 = M['formulas_sin_valor'](ruta3)
    chequeo('valor, texto vacio y valor numerico no se marcan; solo A3 sin valor', h3 == {'CARGAS': ['A3']}, str(h3))

print(f'FALLOS: {len(FALLOS)}')
sys.exit(1 if FALLOS else 0)
