# Verifica _deflexion_viga (flecha de viga por giros de extremo + peso propio) contra un modelo subdividido.
import sys
import numpy as np
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'codigo', 'modulos'))
import analisis_opensees as AO

class Modelo:
    pass

def modelo(xs):
    d = Modelo()
    d.nodos = [(x, 0.0, 0.0) for x in xs]                       # metros, viga a lo largo de X
    d.barras = [{'n1': k, 'n2': k + 1, 'perfil': 'X', 'material': 'M', 'elemento': 'VIGA', 'eje_fuerte': None}
                for k in range(len(xs) - 1)]
    n = len(xs)
    d.apoyos = {0: (True, True, True, True, False, False), n - 1: (False, True, True, True, False, False)}
    return d

PROPS = {'A': 20.0, 'Iz': 2000.0, 'Iy': 200.0, 'J': 10.0, 'masa': 20.0, 'E': 2.04e6, 'nu': 0.3}

def correr(xs, cargas, pp):
    d = modelo(xs)
    props = [dict(PROPS) for _ in d.barras]
    res = AO._resolver(d, props, cargas, pp)
    return d, props, res

xi = np.linspace(0.0, 1.0, 401)
L = 600.0
ok = True
for nombre, cargas_fn, pp, fpp in [
        ('peso propio', lambda n: {}, True, 1.0),
        ('momento en extremo', lambda n: {n - 1: (0, 0, 0, 0, 3.0e5, 0)}, False, 0.0),
        ('peso propio + momento', lambda n: {n - 1: (0, 0, 0, 0, 3.0e5, 0)}, True, 1.0)]:
    d1, p1, r1 = correr([0.0, 6.0], cargas_fn(2), pp)
    d4, p4, r4 = correr([0.0, 1.5, 3.0, 4.5, 6.0], cargas_fn(5), pp)
    dz1 = AO._deflexion_viga(d1, p1, 0, r1, fpp, xi)
    # puntos intermedios del modelo de 4 elementos: nodos en xi = 0.25, 0.5, 0.75
    ref = {0.25: r4['nodos'][1][2], 0.5: r4['nodos'][2][2], 0.75: r4['nodos'][3][2]}
    err = max(abs(dz1[int(round(k * 400))] - v) for k, v in ref.items())
    print(f'{nombre:24s} z(0.5) 1 elem = {dz1[200]:+.6f} cm | 4 elem = {ref[0.5]:+.6f} cm | max dif = {err:.2e} cm')
    ok &= err < 1e-6 * max(1.0, np.max(np.abs(dz1)))
    if nombre == 'peso propio':
        q = PROPS['masa'] / 100.0
        _, yl, zl = AO.ejes_locales(d1, 0)
        I_z_global = PROPS['Iz'] if abs(yl[2]) > 0.99 else PROPS['Iy']   # eje local y vertical -> Iz gobierna
        exacta = -5 * q * L ** 4 / (384 * PROPS['E'] * I_z_global) * np.sign(dz1[200])
        print(f'   yl={np.round(yl,3)} zl={np.round(zl,3)}; analitica 5qL4/384EI = {exacta:+.6f} cm; formula xi=0.5 = {dz1[200]:+.6f} cm')
        ok &= abs(abs(dz1[200]) - abs(exacta)) < 1e-9 * abs(exacta) * 1e3
print('RESULTADO:', 'OK' if ok else 'REVISAR')
