"""Prueba de la flecha de vigas (revision 01). Corrige H-04: el signo esperado sale de la fisica (carga hacia abajo
da flecha negativa), no del propio resultado; cualquier incumplimiento termina con codigo de salida distinto de cero.
Compara con un modelo subdividido (4 elementos) en OpenSees y con la formula analitica 5 q L^4 / (384 E I)."""
import os, sys
import numpy as np

DIB = os.environ.get('DIBUJO', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'codigo', 'modulos'))
sys.path.insert(0, DIB)
import analisis_opensees as AO
from types import SimpleNamespace

PROPS = {'A': 20.0, 'Iz': 2000.0, 'Iy': 200.0, 'J': 10.0, 'masa': 20.0, 'E': 2.04e6, 'nu': 0.3}
L = 600.0                       # cm
Q = PROPS['masa'] / 100.0       # kgf/cm (peso propio)
fallos = []

def modelo(xs, cargas, pp):
    d = SimpleNamespace()
    d.nodos = [(x / 100.0, 0.0, 0.0) for x in xs]
    d.barras = [{'n1': k, 'n2': k + 1, 'elemento': 'VIGA', 'eje_fuerte': None} for k in range(len(xs) - 1)]
    n = len(xs)
    d.apoyos = {0: (True, True, True, True, False, False), n - 1: (False, True, True, True, False, False)}
    props = [dict(PROPS) for _ in d.barras]
    return d, props, AO._resolver(d, props, cargas, pp)

def check(nombre, ok, detalle):
    print(('OK   ' if ok else 'FALLA ') + nombre + ': ' + detalle)
    if not ok:
        fallos.append(nombre)

xi = np.array([0.5])
# 1) peso propio, viga simplemente apoyada: flecha negativa (hacia abajo) y valor analitico
d1, p1, r1 = modelo([0.0, 600.0], {}, True)
f1 = AO._deflexion_viga(d1, p1, 0, r1, 1.0, xi)[0]
esperado1 = -5.0 * Q * L ** 4 / (384.0 * PROPS['E'] * PROPS['Iz'])
check('peso propio: signo y magnitud analitica', f1 < 0 and abs(f1 - esperado1) <= 1e-9 * abs(esperado1),
      f'obtenido={f1:.10g} cm, esperado={esperado1:.10g} cm (-5qL^4/384EI)')
# 2) peso propio, subdividido en 4 elementos: la misma flecha relativa a la cuerda
d4, p4, r4 = modelo([0.0, 150.0, 300.0, 450.0, 600.0], {}, True)
ref4 = r4['nodos'][2][2] - 0.5 * (r4['nodos'][0][2] + r4['nodos'][4][2])
check('peso propio: 1 elemento contra 4 elementos', abs(f1 - ref4) <= 1e-9 * abs(ref4),
      f'1 elem={f1:.10g}, 4 elem={ref4:.10g} cm')
# 3) momento en el extremo (sin peso propio): 1 elemento contra 4 elementos
cargas = {4: (0, 0, 0, 0, 3.0e5, 0)}
d5, p5, r5 = modelo([0.0, 600.0], {1: (0, 0, 0, 0, 3.0e5, 0)}, False)
f5 = AO._deflexion_viga(d5, p5, 0, r5, 0.0, xi)[0]
d6, p6, r6 = modelo([0.0, 150.0, 300.0, 450.0, 600.0], {4: (0, 0, 0, 0, 3.0e5, 0)}, False)
ref6 = r6['nodos'][2][2] - 0.5 * (r6['nodos'][0][2] + r6['nodos'][4][2])
check('momento en extremo: 1 elemento contra 4 elementos', abs(f5 - ref6) <= 1e-6 * max(abs(ref6), 1e-9),
      f'1 elem={f5:.10g}, 4 elem={ref6:.10g} cm')
# 4) peso propio mas momento en el extremo
d7, p7, r7 = modelo([0.0, 600.0], {1: (0, 0, 0, 0, 3.0e5, 0)}, True)
f7 = AO._deflexion_viga(d7, p7, 0, r7, 1.0, xi)[0]
d8, p8, r8 = modelo([0.0, 150.0, 300.0, 450.0, 600.0], {4: (0, 0, 0, 0, 3.0e5, 0)}, True)
ref8 = r8['nodos'][2][2] - 0.5 * (r8['nodos'][0][2] + r8['nodos'][4][2])
check('peso propio y momento: 1 elemento contra 4 elementos', abs(f7 - ref8) <= 1e-6 * max(abs(ref8), 1e-9),
      f'1 elem={f7:.10g}, 4 elem={ref8:.10g} cm')

print('RESULTADO:', 'OK' if not fallos else 'FALLAN: ' + ', '.join(fallos))
sys.exit(1 if fallos else 0)
