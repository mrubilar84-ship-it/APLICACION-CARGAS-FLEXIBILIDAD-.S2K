"""Pruebas de AISC 360-22 B4.2 (espesor de diseno de HSS) y de la exclusion de KL/r para vigas.

Uso:  DIBUJO=<carpeta con los modulos del notebook (diseno_asd.py, perfiles_gerdau.py, gerdau_datos.py)>
      [PLANTILLA=<plantilla_soportes.xlsx>] python3 test_b42_hss.py
Los valores de norma se leen de la hoja NORMA de la plantilla, igual que cargar_norma en el notebook.
Sale con codigo 1 si alguna comprobacion falla.
"""
import math
import os
import sys

import openpyxl

DIB = os.environ.get('DIBUJO')
if not DIB:
    sys.exit('Defina DIBUJO=<carpeta con los modulos del notebook>')
sys.path.insert(0, DIB)
import diseno_asd as D            # noqa: E402
import perfiles_gerdau as G       # noqa: E402

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PLANTILLA = os.environ.get('PLANTILLA', os.path.join(RAIZ, 'plantilla_soportes.xlsx'))
NOMBRE = 'HSS 4 × 4 × 3/16'
FALLOS = []


def cargar_valores(ruta):
    ws = openpyxl.load_workbook(ruta, data_only=True)['NORMA']
    valores, leyendo = {}, False
    for fila in ws.iter_rows(values_only=True):
        if not fila or fila[0] is None:
            continue
        if str(fila[0]).strip() == 'CLAVE':
            leyendo = True
            continue
        if leyendo and isinstance(fila[1], (int, float)):
            valores[str(fila[0]).strip()] = float(fila[1])
    return valores


def chequeo(nombre, ok, detalle=''):
    print(('OK    ' if ok else 'FALLA ') + nombre + (f'  [{detalle}]' if detalle else ''))
    if not ok:
        FALLOS.append(nombre)


def esquina_viva(B, H, t):
    bi, hi = B - 2 * t, H - 2 * t
    return {'A': B * H - bi * hi, 'Ix': (B * H ** 3 - bi * hi ** 3) / 12, 'Iy': (H * B ** 3 - hi * bi ** 3) / 12,
            'Zx': (B * H ** 2 - bi * hi ** 2) / 4, 'Zy': (H * B ** 2 - hi * bi ** 2) / 4,
            'J': 2 * t * (B - t) ** 2 * (H - t) ** 2 / (B + H - 2 * t)}


valores = cargar_valores(PLANTILLA)
chequeo('la plantilla trae AISC_B42_HSS = 0.93', valores.get('AISC_B42_HSS') == 0.93, str(valores.get('AISC_B42_HSS')))

# 1) Factor 1.0: el catalogo se conserva exacto (la razon de espesores es 1)
v1 = dict(valores, AISC_B42_HSS=1.0)
D.cargar_norma(v1, 1.0)
p0 = G.obtener_perfil(NOMBRE)
q1 = D._hss_diseno(p0)
for k in ('A', 'Ix', 'Iy', 'Sx', 'Sy', 'Zx', 'Zy', 'J', 'rx', 'ry'):
    chequeo(f'factor 1.0 conserva {k} del catalogo', abs(q1[k] - p0[k]) <= 1e-9 * max(1.0, abs(p0[k])))

# 2) Factor 0.93: propiedades de diseno = catalogo x razon de la seccion de esquina viva
D.cargar_norma(valores, 1.0)
p = G.obtener_perfil(NOMBRE)
q = D._props_asd(NOMBRE, 'HSS')[0]
B, H, tn = p['B'], p['H'], p['t']
td = 0.93 * tn
n, d = esquina_viva(B, H, tn), esquina_viva(B, H, td)
chequeo('t de diseno = 0.93 t nominal', abs(q['t'] - td) < 1e-12, f"{q['t']:.5f} cm")
chequeo('t nominal se conserva', abs(q['t_nominal'] - tn) < 1e-12)
for k in ('A', 'Ix', 'Iy', 'Zx', 'Zy', 'J'):
    ref = p[k] * d[k] / n[k]
    chequeo(f'{k} de diseno = catalogo x razon', abs(q[k] - ref) <= 1e-9 * max(1.0, abs(ref)),
            f'{q[k]:.4f} vs {ref:.4f}')
chequeo('Sx escala como Ix', abs(q['Sx'] / p['Sx'] - q['Ix'] / p['Ix']) < 1e-12)
rx_ref = p['rx'] * math.sqrt((d['Ix'] / n['Ix']) / (d['A'] / n['A']))
chequeo('rx de diseno = rx catalogo x sqrt(razon I / razon A)', abs(q['rx'] - rx_ref) < 1e-9)
chequeo('masa por metro sin cambio', q['masa'] == p['masa'])
chequeo('A de diseno menor que la del catalogo', q['A'] < p['A'])

# 3) Clave faltante en NORMA: error claro (no un cero)
try:
    D.cargar_norma({k: v for k, v in valores.items() if k != 'AISC_B42_HSS'}, 1.0)
    chequeo('clave AISC_B42_HSS faltante da ErrorAsd', False)
except D.ErrorAsd as error:
    chequeo('clave AISC_B42_HSS faltante da ErrorAsd', 'AISC_B42_HSS' in str(error), str(error))
D.cargar_norma(valores, 1.0)

# 4) KL/r: solo miembros comprimidos (vigas exentas)
chequeo('VIGA exenta de KL/r aunque tenga compresion', D.aplica_klr('VIGA', [{'Pr_c': 500.0}]) is False)
chequeo('COLUMNA con compresion: KL/r aplica', D.aplica_klr('COLUMNA', [{'Pr_c': 500.0}]) is True)
chequeo('ARRIOSTRE: KL/r aplica (grupo de miembros comprimidos)', D.aplica_klr('ARRIOSTRE', [{'Pr_c': 0.0}]) is True)

print(f'FALLOS: {len(FALLOS)}')
sys.exit(1 if FALLOS else 0)
