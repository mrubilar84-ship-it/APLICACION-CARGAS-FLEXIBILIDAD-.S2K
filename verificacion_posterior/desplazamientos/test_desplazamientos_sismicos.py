"""Pruebas de las derivas de entrepiso de la estructura bajo sismo (memoria, seccion 6.3) y de la hoja DESPLAZAMIENTOS.
Modelo sintetico: no requiere OpenSees.

Uso:  python3 test_desplazamientos_sismicos.py
      (DIBUJO=<carpeta con perfiles_gerdau.py y dibujo_directo.py> si no esta en auditoria_rev05/codigo/generados)
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
import memoria_asd as MA                # noqa: E402

FALLOS = []


def chequeo(nombre, ok, detalle=''):
    print(('OK    ' if ok else 'FALLA ') + nombre + (f'  [{detalle}]' if detalle else ''))
    if not ok:
        FALLOS.append(nombre)


def _cargar_celda6():
    """Extrae del bloque 6 las definiciones (funciones de hoja) sin ejecutar su parte de ejemplo."""
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


def _funcion_celda7(nombre):
    """Extrae del bloque 7 una sola funcion (el bloque entero lee la planilla al importarse)."""
    ruta = os.path.join(FUENTES, 'celda7_validar.py')
    arbol = ast.parse(open(ruta, encoding='utf-8').read(), ruta)
    cuerpo = [n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name == nombre]
    espacio = {}
    exec(compile(ast.Module(body=cuerpo, type_ignores=[]), ruta, 'exec'), espacio)
    return espacio[nombre]


LEER = _funcion_celda7('leer_desplazamientos')


class Dib:
    """Modelo sintetico: base (Z=0) y dos niveles (Z=3 m y Z=6 m), dos nudos por nivel. Coordenadas en metros."""
    def __init__(self):
        self.nodos = [(0.0, 0.0, 0.0), (0.0, 0.0, 3.0), (6.0, 0.0, 3.0), (0.0, 0.0, 6.0), (6.0, 0.0, 6.0)]
        self.clase_combinacion = {'SIS_X': 'sismo', 'GRAV': 'gravitacional'}
        self.estados_tipo = {'E_X': 'E', 'W_X': 'W'}


class DibUnNivel(Dib):
    def __init__(self):
        super().__init__()
        self.nodos = [(0.0, 0.0, 0.0), (6.0, 0.0, 0.0)]


def res(ux_cm, uy_cm):
    return {'nodos': [[ux, uy, 0.0, 0.0, 0.0, 0.0] for ux, uy in zip(ux_cm, uy_cm)]}


IDS = {0: 101, 1: 102, 2: 103, 3: 104, 4: 105}
DIB = Dib()
CASOS = [
    ('SIS_X', 'COMBINACION', res([0.0, 1.0, 0.8, 2.5, 2.0], [0.0, 0.0, 0.0, 0.5, 0.0])),
    ('GRAV', 'COMBINACION', res([0.0, 9.0, 9.0, 9.0, 9.0], [0.0] * 5)),      # gravitacional: no debe entrar
    ('E_X', 'ESTADO', res([0.0, 0.5, 0.5, 0.5, 0.5], [0.0] * 5)),           # caso sismico puro: entra (sin combinar)
    ('W_X', 'ESTADO', res([0.0, 9.0, 9.0, 9.0, 9.0], [0.0] * 5)),           # viento: no entra
]
DESP = {'limite': None, 'convencion': 'ELASTICO'}

# 1) Agrupacion por cota: tolerancia de 1 mm, tres niveles
z = np.array([6000.0, 0.0, 3000.0, 3000.4, 6000.2])
niv = MA._nivel_nodos(z, np.zeros(5), np.zeros(5))
chequeo('nudos agrupados en 3 niveles (tolerancia 1 mm)', len(niv) == 3, str([round(n['z'], 1) for n in niv]))

# 2) Derivas: Δ = δ_i − δ_(i−1), deriva = max(|ΔX|, |ΔY|) / h
niveles = MA._nivel_nodos(np.array(DIB.nodos)[:, 2] * 1000.0,
                          np.array([0.0, 10.0, 10.0, 25.0, 20.0]), np.array([0.0, 0.0, 0.0, 5.0, 0.0]))
filas = MA._derivas_niveles(niveles, None)
chequeo('entrepiso 1: deriva = 10 mm / 3000 mm', abs(filas[0]['deriva'] - 10.0 / 3000.0) < 1e-12,
        f"{filas[0]['deriva']:.6f}")
chequeo('entrepiso 2: deriva = max(15/3000, 5/3000) = 0.005', abs(filas[1]['deriva'] - 0.005) < 1e-12,
        f"{filas[1]['deriva']:.6f}")
chequeo('sin limite: estado PENDIENTE (nunca OK)', all(f['estado'] == 'PENDIENTE' for f in filas))
f4 = MA._derivas_niveles(niveles, 0.004)
chequeo('limite 0.004: entrepiso 2 NO CUMPLE, entrepiso 1 CUMPLE',
        f4[1]['estado'] == 'NO CUMPLE' and f4[0]['estado'] == 'CUMPLE')

# 3) Seccion 6.3 con el modelo sintetico (solo combinaciones de sismo)
sec = MA._seccion_desplazamientos_sismicos(DIB, CASOS, DESP)
chequeo('deriva maxima 0.00500 en la combinacion SIS_X', 'Deriva máxima</b>: 0.00500' in sec and 'SIS_X' in sec)
chequeo('caso sismico puro E_X incluido con su encabezado', 'Caso sísmico E_X' in sec)
chequeo('gravedad y viento excluidos', 'GRAV' not in sec and 'W_X' not in sec)
chequeo('sin limite se muestra PENDIENTE', 'PENDIENTE' in sec and 'class="cumple"' not in sec)
chequeo('la seccion no trae tuberias (Δp, lineas)', 'Δp' not in sec and 'Línea' not in sec)
sec_lim = MA._seccion_desplazamientos_sismicos(DIB, CASOS, dict(DESP, limite=0.004))
chequeo('limite 0.004: deriva maxima NO CUMPLE', 'Estado: <span class="nocumple">NO CUMPLE' in sec_lim)
sec_ok = MA._seccion_desplazamientos_sismicos(DIB, CASOS, dict(DESP, limite=0.006))
chequeo('limite 0.006: deriva maxima CUMPLE', 'Estado: <span class="cumple">CUMPLE' in sec_ok)
chequeo('sin casos sismicos: se indica', 'No hay casos sísmicos' in
        MA._seccion_desplazamientos_sismicos(DIB, [('GRAV', 'COMBINACION', CASOS[1][2])], DESP))
chequeo('un solo nivel: se indica que no hay entrepisos',
        'un solo nivel' in MA._seccion_desplazamientos_sismicos(DibUnNivel(), CASOS[:1], DESP))

# 4) Errores y avisos de la planilla
chequeo('sin hoja DESPLAZAMIENTOS: aviso para copiar la hoja',
        'copie esa hoja' in MA._seccion_desplazamientos_sismicos(DIB, CASOS, None))
try:
    MA._seccion_desplazamientos_sismicos(DIB, CASOS, dict(DESP, limite='abc'))
    chequeo('LIMITE_DERIVA no numerico da error', False)
except MA.DA.ErrorAsd as error:
    chequeo('LIMITE_DERIVA no numerico da error', 'LIMITE_DERIVA' in str(error))

# 5) Ida y vuelta por la hoja: se escribe y se lee LIMITE_DERIVA y CONVENCION
with tempfile.TemporaryDirectory() as tmp:
    ruta = os.path.join(tmp, 'prueba.xlsx')
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    PL['_hoja_desplazamientos'](wb, {'limite': 0.005, 'convencion': 'AMPLIFICADO'})
    wb.save(ruta)
    leido = LEER(ruta)
    chequeo('lee LIMITE_DERIVA = 0.005', leido['limite'] == 0.005, str(leido['limite']))
    chequeo('lee CONVENCION = AMPLIFICADO', leido['convencion'] == 'AMPLIFICADO')
    hoja = openpyxl.load_workbook(ruta)['DESPLAZAMIENTOS']
    textos = [str(c.value) for fila in hoja.iter_rows() for c in fila if c.value is not None]
    chequeo('la hoja no trae tabla de tuberias ni COEF_DP',
            not any('LINEA' in t or 'COEF_DP' in t or 'NODO' in t for t in textos))
    ruta2 = os.path.join(tmp, 'vacia.xlsx')
    wb2 = openpyxl.Workbook()
    wb2.remove(wb2.active)
    PL['_hoja_desplazamientos'](wb2, None)
    wb2.save(ruta2)
    vacia = LEER(ruta2)
    chequeo('hoja vacia: LIMITE_DERIVA None (pendiente)', vacia['limite'] is None)
    ruta3 = os.path.join(tmp, 'sin_hoja.xlsx')
    wb3 = openpyxl.Workbook()
    wb3.active.title = 'NODOS'
    wb3.save(ruta3)
    chequeo('planilla sin la hoja: lector devuelve None', LEER(ruta3) is None)

print(f'FALLOS: {len(FALLOS)}')
sys.exit(1 if FALLOS else 0)
