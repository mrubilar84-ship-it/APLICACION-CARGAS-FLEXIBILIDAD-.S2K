"""Pruebas de la revision 01: momento maximo en el tramo (H-01) y flecha relativa a la cuerda (H-02).
Sale con codigo distinto de cero si alguna comprobacion no se cumple."""
import os, sys
import numpy as np
from types import SimpleNamespace
import openseespy.opensees as ops

DIB = os.environ.get('DIBUJO', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'codigo', 'modulos'))
sys.path.insert(0, DIB)
import analisis_opensees as AO
import diseno_asd as DA
from orientacion_gerdau import ejes_locales, vecxz_de_barra

fallos = []
def check(nombre, obtenido, esperado, tol_rel=1e-6, tol_abs=1e-9):
    ok = abs(obtenido - esperado) <= max(tol_abs, tol_rel * abs(esperado))
    print(f"{'OK  ' if ok else 'FALLA'} {nombre}: obtenido={obtenido:.10g} esperado={esperado:.10g}")
    if not ok:
        fallos.append(nombre)

PROPS = {'A': 20.0, 'Iz': 2000.0, 'Iy': 200.0, 'J': 10.0, 'masa': 20.0, 'E': 2.04e6, 'nu': 0.3}
Q = 0.2                      # kgf/cm (peso propio: masa 20 kg/m -> 0.2 kgf/cm)
L = 600.0                    # cm

def dib_viga(xs, apoyos):
    d = SimpleNamespace()
    d.nodos = [(x / 100.0, 0.0, 0.0) for x in xs]           # m
    d.barras = [{'n1': k, 'n2': k + 1, 'elemento': 'VIGA', 'eje_fuerte': None, 'perfil': 'X', 'material': 'M'}
                for k in range(len(xs) - 1)]
    d.apoyos = apoyos
    return d

def resolver(xs, apoyos, pp=True):
    d = dib_viga(xs, apoyos)
    props = [dict(PROPS) for _ in d.barras]
    return d, props, AO._resolver(d, props, {}, pp)

def modelo_con_asentamiento(xs, delta_cm):
    """Viga simplemente apoyada con el apoyo derecho desplazado delta_cm hacia abajo (OpenSees, sp)."""
    ops.wipe(); ops.model('basic', '-ndm', 3, '-ndf', 6)
    d = dib_viga(xs, {0: (True, True, True, True, False, False), len(xs) - 1: (False, True, False, True, False, False)})
    for i, (x, y, z) in enumerate(d.nodos):
        ops.node(i + 1, x * 100, y * 100, z * 100)
    ops.fix(1, 1, 1, 1, 1, 0, 0)
    ops.fix(len(xs), 0, 1, 0, 1, 0, 0)
    for k, b in enumerate(d.barras):
        ops.geomTransf('Linear', k + 1, *vecxz_de_barra(d.nodos, b))
        ops.element('elasticBeamColumn', k + 1, k + 1, k + 2, PROPS['A'], PROPS['E'], PROPS['E'] / (2 * (1 + PROPS['nu'])),
                    PROPS['J'], PROPS['Iy'], PROPS['Iz'], k + 1)
    ops.timeSeries('Constant', 1)
    ops.pattern('Plain', 1, 1)
    for k, b in enumerate(d.barras):
        x_loc, y_loc, z_loc = ejes_locales(d, k)
        w = np.array([0.0, 0.0, -1.0]) * PROPS['masa'] / 100.0
        ops.eleLoad('-ele', k + 1, '-type', '-beamUniform', float(w @ y_loc), float(w @ z_loc), float(w @ x_loc))
    ops.pattern('Plain', 2, 1)
    ops.sp(len(xs), 3, delta_cm)
    ops.system('BandGeneral'); ops.numberer('RCM'); ops.constraints('Transformation')
    ops.integrator('LoadControl', 1.0); ops.algorithm('Linear'); ops.analysis('Static')
    ops.analyze(1)
    nodos = {i: np.array(ops.nodeDisp(i + 1), float) for i in range(len(xs))}
    res = {'nodos': nodos, 'extremos': {}, 'barras': {}}
    for k in range(len(xs) - 1):
        res['extremos'][k] = (np.array(ops.nodeDisp(k + 1), float), np.array(ops.nodeDisp(k + 2), float))
    ops.wipe()
    return d, [dict(PROPS) for _ in d.barras], res

xi = np.array([0.25, 0.5, 0.75])

# ---- H-02 a: solido rigido infinitesimal (la flecha relativa a la cuerda debe ser cero)
dib_r = SimpleNamespace(nodos=[(0., 0., 0.), (6., 0., 0.)],
                        barras=[{'n1': 0, 'n2': 1, 'elemento': 'VIGA', 'eje_fuerte': None}])
props_r = [{'masa': 20., 'E': 2.04e6, 'Iy': 200., 'Iz': 2000.}]
ui = np.array([0., 0., 0., 0., 1 / 600, 0.])
uj = np.array([0., 0., -1., 0., 1 / 600, 0.])
y_r = AO._deflexion_viga(dib_r, props_r, 0, {'extremos': {0: (ui, uj)}}, 0.0, xi)
for k, v in zip([0.25, 0.5, 0.75], y_r):
    check(f'H-02 solido rigido x/L={k}', float(v), 0.0, tol_abs=1e-9)

# ---- H-02 b: asentamiento de apoyo en viga simplemente apoyada (determinada): la flecha relativa a la cuerda
#      debe coincidir con un modelo subdividido (4 elementos) en los TRES puntos x/L = 0.25, 0.5, 0.75.
#      (en x/L = 0.5 el termino corregido vale cero: por eso se comprueban los tres puntos)
xs_grid = np.array([0.25, 0.5, 0.75])
d2, p2, r2 = modelo_con_asentamiento([0.0, 600.0], -1.0)
con = AO._deflexion_viga(d2, p2, 0, r2, 1.0, xs_grid)
d4, p4, r4 = modelo_con_asentamiento([0.0, 150.0, 300.0, 450.0, 600.0], -1.0)
ref = []
for k, xk in zip([1, 2, 3], xs_grid):
    cuerda = (1 - xk) * r4['nodos'][0][2] + xk * r4['nodos'][4][2]
    ref.append(r4['nodos'][k][2] - cuerda)
for xk, c_, r_ in zip(xs_grid, con, ref):
    check(f'H-02 asentamiento 1 cm, subdividido, x/L={xk}: flecha relativa a la cuerda (cm)', float(c_), float(r_),
          tol_rel=1e-4, tol_abs=1e-7)

# ---- H-01: momento maximo en el tramo
# a) viga simplemente apoyada con peso propio: M = qL^2/8 en el centro (no aparece en los extremos)
d, p, r = resolver([0.0, 600.0], {0: (True, True, True, True, False, False), 1: (False, True, True, True, False, False)})
mz, my = AO.momentos_maximos_viga(d, p, 0, r, 1.0)
check('H-01 SS con peso propio: momento maximo en el tramo (kgf cm)', mz, Q * L ** 2 / 8, tol_rel=1e-6)
f = r['barras'][0]
check('H-01 SS: momento de extremo Mz I (kgf cm) = 0', float(f[5] * 100.0), 0.0, tol_abs=1e-6)
# b) la demanda que recibe el diseno (tabla de barras -> _demanda_fila)
tab, _, _ = AO._tablas(d, [('PP', 'ESTADO', r)], {0}, set(), {0: 1}, {0: 1, 1: 2}, p, {'PP': 1.0})
dem = DA._demanda_fila(tab.iloc[0].to_dict())
check('H-01 demanda Mr_x que recibe el diseno (kgf cm)', dem['Mr_x'], Q * L ** 2 / 8, tol_rel=1e-6)

# c) doblemente empotrada con peso propio (dos elementos, nudo central libre = viga continua):
#    M de apoyo = qL^2/12 (maximo en el extremo del elemento 1)
d, p, r = resolver([0.0, 300.0, 600.0], {0: (True,) * 6, 2: (True,) * 6})
mz, _ = AO.momentos_maximos_viga(d, p, 0, r, 1.0)
check('H-01 doblemente empotrada: momento maximo en el apoyo (kgf cm) = qL^2/12', mz, Q * L ** 2 / 12, tol_rel=1e-6)

# d) voladizo con peso propio: M en el empotramiento = qL^2/2
d, p, r = resolver([0.0, 600.0], {0: (True,) * 6})
mz, _ = AO.momentos_maximos_viga(d, p, 0, r, 1.0)
check('H-01 voladizo: momento maximo (kgf cm) = qL^2/2', mz, Q * L ** 2 / 2, tol_rel=1e-6)

print('RESULTADO:', 'OK' if not fallos else 'FALLAN: ' + ', '.join(fallos))
sys.exit(1 if fallos else 0)
