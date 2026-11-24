"""Prueba del periodo del soporte (notebook, bloque 9c): columna en voladizo con su peso propio.
Solucion cerrada: T = 2π·sqrt(m·L³ / (3·E·I)) para cada eje de flexion, con m = W/(2g) en el extremo libre
(el peso de la barra se reparte a sus dos extremos; la base esta empotrada y no aporta masa activa).
Uso:  python3 test_periodo_soporte.py
      (DIBUJO=<carpeta con perfiles_gerdau.py> si no esta en auditoria_rev05/codigo/generados)
Sale con codigo 1 si alguna comprobacion falla.
"""
import math
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FUENTES = os.path.join(RAIZ, 'fuentes_notebook')
sys.path.insert(0, FUENTES)
sys.path.insert(0, os.environ.get('DIBUJO', os.path.join(RAIZ, 'auditoria_rev05', 'codigo', 'generados')))
import analisis_opensees as AO          # noqa: E402
import perfiles_gerdau as G             # noqa: E402

FALLOS = []


def chequeo(nombre, ok, detalle=''):
    print(('OK    ' if ok else 'FALLA ') + nombre + (f'  [{detalle}]' if detalle else ''))
    if not ok:
        FALLOS.append(nombre)


class Modelo:
    pass


L_CM, G_CM, E = 300.0, 981.0, 2.04e6
PERFIL = 'IR 6 × 8.5'
p = G.obtener_perfil(PERFIL)
W = p['masa'] / 100.0 * L_CM                       # peso propio de la barra (kgf)
m_tope = W / (2.0 * G_CM)                          # masa en el extremo libre (kgf·s²/cm)
T_fuerte = 2 * math.pi * math.sqrt(m_tope * L_CM ** 3 / (3 * E * p['Ix']))
T_debil = 2 * math.pi * math.sqrt(m_tope * L_CM ** 3 / (3 * E * p['Iy']))

mod = Modelo()
mod.nodos = [(0.0, 0.0, 0.0), (0.0, 0.0, 3.0)]
mod.barras = [{'n1': 0, 'n2': 1, 'perfil': PERFIL, 'material': 'ACERO', 'eje_fuerte': (1.0, 0.0, 0.0)}]
mod.apoyos = {0: (True,) * 6}
materiales = [['ACERO', 'ACERO', 2530.0, 4080.0, E, 0.3, 'prueba']]

import pandas as pd                    # noqa: E402
ESTADOS_SI = pd.DataFrame([{'NOMBRE': 'Peso propio y muerta', 'PESO PROPIO': 'SI'}])
ESTADOS_NO = pd.DataFrame([{'NOMBRE': 'Sobrecarga', 'PESO PROPIO': 'NO'}])
tabla, peso = AO.periodos(mod, materiales, ESTADOS_SI, {0: 1}, factor_hss=None, n_modos=3)
T = list(tabla['T (s)'])
chequeo('peso propio total = W de la barra', abs(peso - W) < 1e-9, f'{peso:.3f} kgf')
chequeo('los dos periodos de flexion coinciden con la solucion cerrada (0.5 %)',
        all(abs(a - b) / b < 0.005 for a, b in zip(sorted(T[:2], reverse=True), sorted([T_debil, T_fuerte], reverse=True))),
        f'modelo {T[0]:.5f} y {T[1]:.5f} s; cerrada {T_debil:.5f} y {T_fuerte:.5f} s')
chequeo('modos ordenados: T1 >= T2 >= T3', T[0] >= T[1] >= T[2])
ef = [tabla.loc[k, ['Masa efectiva X (%)', 'Masa efectiva Y (%)', 'Masa efectiva Z (%)']].tolist() for k in range(3)]
chequeo('modo 1 moviliza ~100 % de la masa en una direccion', max(ef[0]) > 99.0, f'{[round(v, 2) for v in ef[0]]}')
chequeo('modo 2 moviliza ~100 % en la otra direccion de flexion', max(ef[1]) > 99.0
        and ef[1].index(max(ef[1])) != ef[0].index(max(ef[0])), f'{[round(v, 2) for v in ef[1]]}')
chequeo('ninguna fraccion supera 100 %', all(v <= 100.01 for fila in ef for v in fila))

try:
    AO.periodos(mod, materiales, ESTADOS_NO, {0: 1}, factor_hss=None, n_modos=3)
    chequeo('sin PESO PROPIO = SI en ESTADOS no se calcula el periodo', False)
except AO.ErrorAnalisis as error:
    chequeo('sin PESO PROPIO = SI en ESTADOS no se calcula el periodo', 'PESO PROPIO' in str(error))

print(f'FALLOS: {len(FALLOS)}')
sys.exit(1 if FALLOS else 0)
