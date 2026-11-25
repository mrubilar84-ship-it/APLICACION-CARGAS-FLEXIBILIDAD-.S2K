"""Pruebas de la familia GEN (hoja SECCIONES): hoja y lista FORMA, registro en la base de perfiles, avisos y errores.
Una seccion GEN copiada de un perfil del catalogo debe dar los mismos valores que el catalogo.

Uso:  python3 test_secciones_gen.py   (DIBUJO=<carpeta con perfiles_gerdau.py> si no esta en auditoria_rev05/codigo/generados)
Sale con codigo 1 si alguna comprobacion falla.
"""
import ast
import os
import sys
import tempfile

import numpy as np
import openpyxl

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FUENTES = os.path.join(RAIZ, 'fuentes_notebook')
sys.path.insert(0, FUENTES)
sys.path.insert(0, os.environ.get('DIBUJO', os.path.join(RAIZ, 'auditoria_rev05', 'codigo', 'generados')))
import perfiles_gerdau as G            # noqa: E402

FALLOS = []


def chequeo(nombre, ok, detalle=''):
    print(('OK    ' if ok else 'FALLA ') + nombre + (f'  [{detalle}]' if detalle else ''))
    if not ok:
        FALLOS.append(nombre)


def _cargar_celda6():
    ruta = os.path.join(FUENTES, 'celda6_plantilla.py')
    arbol = ast.parse(open(ruta, encoding='utf-8').read(), ruta)
    seguras = ('PatternFill', 'Font', 'Alignment', 'Border', 'Side')
    cuerpo = []
    for n in arbol.body:
        if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
            cuerpo.append(n)
        elif isinstance(n, ast.Assign):
            llamadas = [c for c in ast.walk(n.value) if isinstance(c, ast.Call)]
            if all(isinstance(c.func, ast.Name) and c.func.id in seguras for c in llamadas):
                cuerpo.append(n)
    espacio = {'PERFILES_ORDEN': [(0, 'IR 6 × 8.5')]}
    exec(compile(ast.Module(body=cuerpo, type_ignores=[]), ruta, 'exec'), espacio)
    return espacio


PL = _cargar_celda6()


def _cargar_celda7():
    ruta = os.path.join(FUENTES, 'celda7_validar.py')
    arbol = ast.parse(open(ruta, encoding='utf-8').read(), ruta)
    nombres = {'_vacio', 'leer_secciones', 'registrar_secciones'}
    cuerpo = [n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name in nombres]
    asign = [n for n in arbol.body if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id.startswith('SECC_CLAVE') or isinstance(t, ast.Name) and t.id.startswith('_DISENO')
        or isinstance(t, ast.Name) and t.id.startswith('SECC_REQ') for t in n.targets)]
    espacio = {'np': np, 'G': G, 'SECC_COLS': PL['SECC_COLS'], 'SECC_FORMAS': PL['SECC_FORMAS'],
               'SECC_FIL_INI': PL['SECC_FIL_INI'], 'SECC_MAX': PL['SECC_MAX']}
    exec(compile(ast.Module(body=asign + cuerpo, type_ignores=[]), ruta, 'exec'), espacio)
    return espacio


C7 = _cargar_celda7()
REF = 'IR 6 × 8.5'
p = G.obtener_perfil(REF)


def fila_gen(nombre, forma, sin=()):
    """Fila de SECCIONES (SECC_COLS) con los valores del catalogo REF; 'sin' deja vacias esas columnas."""
    datos = {'NOMBRE': nombre, 'FORMA': forma, 'MASA (kg/m)': p['masa'], 'H (cm)': p['H'], 'B (cm)': p['B'],
             'E alma (cm)': p['e'], 'T ala (cm)': p['t'], 'A (cm2)': p['A'], 'IX (cm4)': p['Ix'],
             'IY (cm4)': p['Iy'], 'SX (cm3)': p['Sx'], 'SY (cm3)': p['Sy'], 'ZX (cm3)': p['Zx'],
             'ZY (cm3)': p['Zy'], 'RX (cm)': p['rx'], 'RY (cm)': p['ry'], 'J (cm4)': p['J'],
             'CW (cm6)': p['Cw'], 'RO (cm)': p.get('ro')}
    return [None if c in sin else datos[c] for c in PL['SECC_COLS']]


# 1) Hoja: FORMA como lista desplegable por seccion; cabecera de 19 columnas
with tempfile.TemporaryDirectory() as tmp:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    PL['_hoja_secciones'](wb, [fila_gen('GEN IR 6x8.5', 'IR')])
    hoja = wb['SECCIONES']
    dvs = [str(dv.formula1) + ' ' + str(dv.sqref) for dv in hoja.data_validations.dataValidation]
    chequeo('FORMA es lista desplegable IR,CE,LI,HSS en toda la columna B',
            any('"IR,CE,LI,HSS"' in d and f'B{PL["SECC_FIL_INI"]}' in d for d in dvs), str(dvs))
    chequeo('cabecera con las 19 columnas', [hoja.cell(row=4, column=c).value for c in range(1, 20)] == PL['SECC_COLS'])
    ruta = os.path.join(tmp, 'secciones.xlsx')
    wb.save(ruta)

    # 2) Listas de perfiles por grupo: al final, formulas que leen la hoja SECCIONES
    wb2 = openpyxl.Workbook()
    wb2.remove(wb2.active)
    ws_l = wb2.create_sheet('LISTAS')
    PL['_hoja_listas_grupo'](wb2, ws_l, None)
    f_slot = ws_l.cell(row=2 + 1, column=6).value
    chequeo('lista de grupo termina en formulas de SECCIONES',
            isinstance(ws_l.cell(row=2 + 1 + 0, column=6).value, str) and 'SECCIONES!$A$5' in str(f_slot))

    # 3) Registro: copia de IR 6 x 8.5 da los mismos valores que el catalogo
    filas = [(5, fila_gen('GEN IR 6x8.5', 'IR'))]
    msgs = C7['registrar_secciones'](filas)
    g = G.obtener_perfil('GEN IR 6x8.5')
    chequeo('registro sin mensajes', msgs == [], str(msgs))
    iguales = all(abs((g[k] or 0) - (p[k] or 0)) < 1e-9 for k in ['H', 'B', 'e', 't', 'A', 'Ix', 'Iy', 'Sx', 'Sy', 'rx', 'ry', 'J', 'Cw', 'Zx', 'Zy', 'masa'])
    chequeo('valores de la seccion GEN = valores del catalogo', iguales)
    chequeo('familia de diseno = forma (IR)', g['familia'] == 'IR' and G.PERFILES['GEN IR 6x8.5']['origen'] == 'GEN')

    # 4) Avisos y errores
    msgs = C7['registrar_secciones']([(6, fila_gen('GEN IR sin Cw', 'IR', sin=('CW (cm6)',)))])
    chequeo('falta CW en IR: AVISO que nombra la columna', any(m[2] == 'AVISO' and 'CW (cm6)' in m[3] for m in msgs), str(msgs))
    msgs = C7['registrar_secciones']([(7, fila_gen('GEN forma mala', 'XX'))])
    chequeo('forma no reconocida: ERROR', any(m[2] == 'ERROR' and 'FORMA' in m[3] for m in msgs))
    msgs = C7['registrar_secciones']([(8, fila_gen(REF, 'IR'))])
    chequeo('nombre de perfil Gerdau repetido: ERROR', any(m[2] == 'ERROR' and 'Gerdau' in m[3] for m in msgs))
    msgs = C7['registrar_secciones']([(9, fila_gen('GEN doble', 'IR')), (10, fila_gen('GEN doble', 'IR'))])
    chequeo('nombre repetido dentro de SECCIONES: ERROR', any(m[2] == 'ERROR' and 'repetido' in m[3] for m in msgs))

print(f'FALLOS: {len(FALLOS)}')
sys.exit(1 if FALLOS else 0)
