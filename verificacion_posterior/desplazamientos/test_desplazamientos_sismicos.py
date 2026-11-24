"""Pruebas de la deformacion lateral sismica de la memoria (criterio W40428-000-DD20-DSC-001 Rev. 0, 11.10 y 11.11):
derivas de entrepiso (solo combinaciones de sismo), lineas de tuberia (Δp = coef · Δh) y lectura de la hoja
DESPLAZAMIENTOS. Modelo sintetico: no requiere OpenSees.

Uso:  python3 test_desplazamientos_sismicos.py
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
# perfiles_gerdau.py (lo importa la planilla) no esta en fuentes_notebook: DIBUJO = carpeta de esos modulos
sys.path.insert(0, os.environ.get('DIBUJO', os.path.join(RAIZ, 'auditoria_rev05', 'codigo', 'generados')))
import memoria_asd as MA                # noqa: E402

FALLOS = []


def chequeo(nombre, ok, detalle=''):
    print(('OK    ' if ok else 'FALLA ') + nombre + (f'  [{detalle}]' if detalle else ''))
    if not ok:
        FALLOS.append(nombre)


def _cargar_celda6():
    """Extrae del bloque 6 las definiciones (constantes, funciones de hoja) sin ejecutar su parte de ejemplo."""
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
    espacio = {}
    exec(compile(ast.Module(body=cuerpo, type_ignores=[]), ruta, 'exec'), espacio)
    return espacio


PL = _cargar_celda6()


def _funciones_celda7(nombres):
    """Extrae del bloque 7 solo las funciones pedidas (el bloque entero lee la planilla al importarse)."""
    ruta = os.path.join(FUENTES, 'celda7_validar.py')
    arbol = ast.parse(open(ruta, encoding='utf-8').read(), ruta)
    cuerpo = [n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name in nombres]
    espacio = {'DESP_FIL_INI': PL['DESP_FIL_INI'], 'DESP_MAX': PL['DESP_MAX'], 'DESP_COLS': PL['DESP_COLS'], 'np': np}
    exec(compile(ast.Module(body=cuerpo, type_ignores=[]), ruta, 'exec'), espacio)
    return espacio


E7 = _funciones_celda7({'_vacio', 'leer_desplazamientos'})


class Dib:
    """Modelo sintetico: base (Z=0) y dos niveles (Z=3 m y Z=6 m), dos nudos por nivel. Coordenadas en metros."""
    def __init__(self):
        self.nodos = [(0.0, 0.0, 0.0), (0.0, 0.0, 3.0), (6.0, 0.0, 3.0), (0.0, 0.0, 6.0), (6.0, 0.0, 6.0)]
        self.clase_combinacion = {'SIS_X': 'sismo', 'GRAV': 'gravitacional'}


def res(ux_cm, uy_cm):
    return {'nodos': [[ux, uy, 0.0, 0.0, 0.0, 0.0] for ux, uy in zip(ux_cm, uy_cm)]}


IDS = {0: 101, 1: 102, 2: 103, 3: 104, 4: 105}
DIB = Dib()
CASOS = [
    ('SIS_X', 'COMBINACION', res([0.0, 1.0, 0.8, 2.5, 2.0], [0.0, 0.0, 0.0, 0.5, 0.0])),
    ('GRAV', 'COMBINACION', res([0.0, 9.0, 9.0, 9.0, 9.0], [0.0] * 5)),      # gravitacional: no debe entrar
    ('E_X', 'ESTADO', res([0.0, 5.0, 5.0, 5.0, 5.0], [0.0] * 5)),           # estado: no debe entrar
]
DESP = {'limite': None, 'convencion': 'ELASTICO', 'lineas': [], 'coef_dp': 0.0085}

# 1) Agrupacion por cota: tolerancia de 1 mm, tres niveles
z = np.array([6000.0, 0.0, 3000.0, 3000.4, 6000.2])
niv = MA._nivel_nodos(z, np.zeros(5), np.zeros(5))
chequeo('nudos agrupados en 3 niveles (tolerancia 1 mm)', len(niv) == 3, str([round(n['z'], 1) for n in niv]))

# 2) Derivas: Δ = δ_i − δ_(i−1), deriva = |Δ| / h
niveles = MA._nivel_nodos(np.array(DIB.nodos)[:, 2] * 1000.0,
                          np.array([0.0, 10.0, 10.0, 25.0, 20.0]), np.array([0.0, 0.0, 0.0, 5.0, 0.0]))
filas = MA._derivas_niveles(niveles, None)
chequeo('entrepiso 1: deriva = 10 mm / 3000 mm', abs(filas[0]['deriva'] - 10.0 / 3000.0) < 1e-12,
        f"{filas[0]['deriva']:.6f}")
chequeo('entrepiso 2: deriva = max(15/3000, 5/3000) = 0.005', abs(filas[1]['deriva'] - 0.005) < 1e-12,
        f"{filas[1]['deriva']:.6f}")
chequeo('sin limite: estado PENDIENTE (nunca OK)', all(f['estado'] == 'PENDIENTE' for f in filas))
chequeo('limite 0.004: entrepiso 2 NO CUMPLE, entrepiso 1 CUMPLE',
        MA._derivas_niveles(niveles, 0.004)[1]['estado'] == 'NO CUMPLE'
        and MA._derivas_niveles(niveles, 0.004)[0]['estado'] == 'CUMPLE')

# 3) Seccion 6.3 con el modelo sintetico (solo combinaciones de sismo)
sec = MA._seccion_desplazamientos_sismicos(DIB, CASOS, IDS, DESP)
chequeo('deriva maxima 0.00500 en la combinacion SIS_X', 'Deriva máxima</b>: 0.00500' in sec and 'SIS_X' in sec)
chequeo('combinacion de gravedad y estado E excluidos', 'GRAV' not in sec and 'E_X' not in sec)
chequeo('sin limite se muestra PENDIENTE', 'PENDIENTE' in sec and 'class="cumple"' not in sec.split('Líneas de tubería')[0])
sec_lim = MA._seccion_desplazamientos_sismicos(DIB, CASOS, IDS, dict(DESP, limite=0.004))
chequeo('limite 0.004: deriva maxima NO CUMPLE', 'Estado: <span class="nocumple">NO CUMPLE' in sec_lim)
sec_ok = MA._seccion_desplazamientos_sismicos(DIB, CASOS, IDS, dict(DESP, limite=0.006))
chequeo('limite 0.006: deriva maxima CUMPLE', 'Estado: <span class="cumple">CUMPLE' in sec_ok)
chequeo('sin combinaciones de sismo: se indica', 'No hay combinaciones de sismo' in
        MA._seccion_desplazamientos_sismicos(DIB, [('GRAV', 'COMBINACION', CASOS[1][2])], IDS, DESP))

class DibUnNivel(Dib):
    def __init__(self):
        super().__init__()
        self.nodos = [(0.0, 0.0, 0.0), (6.0, 0.0, 0.0)]
chequeo('un solo nivel: se indica que no hay entrepisos',
        'un solo nivel' in MA._seccion_desplazamientos_sismicos(DibUnNivel(), CASOS[:1], {0: 101, 1: 102}, DESP))

# 4) Lineas de tuberia: Δh por cotas Z de nudos, Δp = 0.0085 · Δh
lineas = [('L1', 101, 102, 'RIGIDO', 30.0, ''),        # Δh 3000 -> Δp 25.5 <= 30
          ('L2', 101, 104, 'FLEXIBLE', 20.0, ''),      # Δh 6000 -> Δp 51 > 20
          ('L3', 102, 104, None, 30.0, ''),            # sin tipo de apoyo -> PENDIENTE
          ('L4', 101, 104, 'RIGIDO', None, ''),        # sin holgura -> PENDIENTE
          ('L5', 101, 102, 'rigido', 25.6, '')]        # minusculas aceptadas; 25.5 <= 25.6
t = MA._tuberias(DIB, IDS, lineas, 0.0085)
chequeo('L1 Δh = 3000 mm y Δp = 25.5 mm: CUMPLE', abs(t[0]['dh'] - 3000) < 1e-9 and abs(t[0]['dp'] - 25.5) < 1e-9
        and t[0]['estado'] == 'CUMPLE')
chequeo('L2 apoyo flexible: Δp = 51 mm > capacidad 20: NO CUMPLE', t[1]['estado'] == 'NO CUMPLE'
        and abs(t[1]['dh'] - 6000) < 1e-9)
chequeo('L3 sin tipo de apoyo: PENDIENTE', t[2]['estado'] == 'PENDIENTE')
chequeo('L4 sin holgura: PENDIENTE', t[3]['estado'] == 'PENDIENTE')
chequeo('L5 apoyo en minusculas acepta RIGIDO', t[4]['apoyo'] == 'RIGIDO' and t[4]['estado'] == 'CUMPLE')
try:
    MA._tuberias(DIB, IDS, [('L6', 101, 999, 'RIGIDO', 30.0, '')], 0.0085)
    chequeo('nudo inexistente da error claro', False)
except MA.DA.ErrorAsd as error:
    chequeo('nudo inexistente da error claro', '999' in str(error), str(error))

# 5) Errores de la planilla
chequeo('sin hoja DESPLAZAMIENTOS: aviso de plantilla nueva',
        'use la plantilla nueva' in MA._seccion_desplazamientos_sismicos(DIB, CASOS, IDS, None))
try:
    MA._seccion_desplazamientos_sismicos(DIB, CASOS, IDS, dict(DESP, coef_dp=None))
    chequeo('falta COEF_DP da error', False)
except MA.DA.ErrorAsd as error:
    chequeo('falta COEF_DP da error', 'COEF_DP' in str(error))
try:
    MA._seccion_desplazamientos_sismicos(DIB, CASOS, IDS, dict(DESP, limite='abc'))
    chequeo('LIMITE_DERIVA no numerico da error', False)
except MA.DA.ErrorAsd as error:
    chequeo('LIMITE_DERIVA no numerico da error', 'LIMITE_DERIVA' in str(error))

# 6) Ida y vuelta por la planilla: hoja DESPLAZAMIENTOS + NORMA W40428_DELTA_P
with tempfile.TemporaryDirectory() as tmp:
    ruta = os.path.join(tmp, 'prueba.xlsx')
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    PL['_hoja_normas_y_parametros'](wb)
    PL['_hoja_desplazamientos'](wb, {'limite': 0.005, 'convencion': 'AMPLIFICADO',
                                 'lineas': [['L1', 101, 104, 'RIGIDO', 30.0, 'nota']]})
    wb.save(ruta)
    leido = E7['leer_desplazamientos'](ruta)
    chequeo('lee LIMITE_DERIVA = 0.005', leido['limite'] == 0.005, str(leido['limite']))
    chequeo('lee CONVENCION', leido['convencion'] == 'AMPLIFICADO')
    chequeo('lee una linea de tuberia', len(leido['lineas']) == 1 and leido['lineas'][0][0] == 'L1')
    chequeo('lee COEF_DP = 0.0085 de la hoja', leido['coef_dp'] == 0.0085, str(leido['coef_dp']))
    wb2 = openpyxl.Workbook()
    wb2.remove(wb2.active)
    PL['_hoja_normas_y_parametros'](wb2)
    PL['_hoja_desplazamientos'](wb2, None)
    ruta2 = os.path.join(tmp, 'vacia.xlsx')
    wb2.save(ruta2)
    vacia = E7['leer_desplazamientos'](ruta2)
    chequeo('hoja vacia: LIMITE_DERIVA None (pendiente)', vacia['limite'] is None and vacia['lineas'] == [])

print(f'FALLOS: {len(FALLOS)}')
sys.exit(1 if FALLOS else 0)
