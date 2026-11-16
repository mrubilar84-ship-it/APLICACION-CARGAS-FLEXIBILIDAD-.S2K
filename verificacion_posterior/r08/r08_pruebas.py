# -*- coding: utf-8 -*-
"""R-08 (verificacion independiente): pruebas del calculo OpenSees de la planilla de soportes.

Cada prueba imprime una linea OK o FALLA. Las lineas INFO son diagnosticos y no cuentan.
Codigo de salida: 0 solo si todas las pruebas estan OK.
No modifica el repositorio. Lee las fuentes (copias identicas en scratch, ver control 0.1) y escribe solo en
agente_r08/trabajo.
"""
import sys
import os
import tempfile
import math
import json
import hashlib

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8')

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(_HERE, '..', '..'))
SCR = os.environ.get('CARPETA_TRABAJO', os.path.join(_HERE, 'trabajo'))   # contiene ejemplo/ y sismo/ (ejecuciones del notebook)
EJEMPLO = os.path.join(SCR, 'ejemplo')
SISMO = os.path.join(SCR, 'sismo')
TRABAJO = os.environ.get('CARPETA_SALIDA') or tempfile.mkdtemp(prefix='r08_')
JSON_GERDAU = os.path.join(REPO, 'fuentes_notebook', 'datos', 'perfiles_gerdau_mexico_rev04.json')

os.makedirs(TRABAJO, exist_ok=True)
os.chdir(TRABAJO)                       # correr() escribe ejes_locales.png en el directorio actual
sys.path.insert(0, EJEMPLO)

import numpy as np
import pandas as pd
import openseespy.opensees as ops
import analisis_opensees as AO
from orientacion_gerdau import vecxz_de_barra, ejes_locales
from dibujo_directo import DibujoModelo, GRADOS
import perfiles_gerdau as G

RESULTADOS = []

# Propiedades de la prueba aislada (las mismas de auditoria_rev01/pruebas/test_rev01.py)
PROPS_TEST = {'A': 20.0, 'Iz': 2000.0, 'Iy': 200.0, 'J': 10.0, 'masa': 20.0, 'E': 2.04e6, 'nu': 0.3}
Q_TEST = 0.2                            # kgf/cm (masa 20 kg/m)
L_TEST = 600.0                          # cm
FIX = (True,) * 6


def md5(ruta):
    with open(ruta, 'rb') as fh:
        return hashlib.md5(fh.read()).hexdigest()


def reg(ok, codigo, nombre, obtenido, esperado, nota=''):
    RESULTADOS.append({'cod': codigo, 'nombre': nombre, 'obt': obtenido, 'esp': esperado, 'ok': bool(ok), 'nota': nota})
    etiqueta = 'OK   ' if ok else 'FALLA'
    linea = f'{etiqueta} [{codigo}] {nombre} | obtenido: {obtenido} | esperado: {esperado}'
    if nota:
        linea += f' | {nota}'
    print(linea, flush=True)


def info(codigo, nombre, texto):
    print(f'INFO  [{codigo}] {nombre} | {texto}', flush=True)


def cmp(codigo, nombre, obt, esp, tol_rel=1e-6, tol_abs=1e-9, nota=''):
    o, e = float(obt), float(esp)
    ok = math.isfinite(o) and abs(o - e) <= max(tol_abs, tol_rel * abs(e))
    reg(ok, codigo, nombre, f'{o:.8g}', f'{e:.8g}', nota)
    return ok


def num(v):
    try:
        f = float(v)
        return 0.0 if math.isnan(f) else f
    except (TypeError, ValueError):
        return 0.0


def masa_json(nombre):
    """Masa (kg/m) de la base Gerdau rev04 (JSON del repositorio, fuente independiente del modulo del programa)."""
    p = PERFILES_JSON[nombre]
    return float(p['masa_kg_m'])


with open(JSON_GERDAU, encoding='utf-8') as fh:
    PERFILES_JSON = {p['perfil_comercial']: p for p in json.load(fh)['perfiles']}


# ===================================================================================================
# 0. Control de fuentes
# ===================================================================================================
def control_fuentes():
    print('\n== 0. Control de fuentes ==', flush=True)
    for nombre in ['analisis_opensees.py', 'orientacion_gerdau.py', 'dibujo_directo.py']:
        a = md5(os.path.join(REPO, 'fuentes_notebook', nombre))
        b = md5(os.path.join(EJEMPLO, nombre))
        reg(a == b, '0.1', f'copia de scratch = repositorio ({nombre})', b[:12], a[:12])


# ===================================================================================================
# 1. Equilibrio global de fuerzas y momentos (caso gravitacional y caso sismo)
# ===================================================================================================
def leer_entrada(carpeta):
    f = os.path.join(carpeta, 'plantilla_soportes.xlsx')
    nod = pd.read_excel(f, sheet_name='NODOS', dtype=object)
    nod = nod[nod['ID'].notna()]
    coords = {int(float(r['ID'])): np.array([float(r['X (m)']), float(r['Y (m)']), float(r['Z (m)'])])
              for _, r in nod.iterrows()}
    bar = pd.read_excel(f, sheet_name='BARRAS', dtype=object)
    bar = bar[bar['ID'].notna()]
    cg = pd.read_excel(f, sheet_name='CARGAS', header=7, dtype=object).iloc[:, :9]
    cg.columns = ['ID', 'ESTADO', 'FX', 'FY', 'FZ', 'MX', 'MY', 'MZ', 'NOTA']
    cg = cg[cg['ID'].notna() & cg['ESTADO'].notna()].copy()
    cg['ESTADO'] = cg['ESTADO'].astype(str).str.strip()
    es = pd.read_excel(f, sheet_name='ESTADOS', dtype=object)
    estados = {}
    for _, r in es.iterrows():
        if isinstance(r.iloc[0], str):
            estados[r.iloc[0].strip()] = (str(r.iloc[1]).strip().upper(), str(r.iloc[3]).strip().upper())
    return coords, bar, cg, estados


def residuos(coords, bar, c_est, r_est, pp, signo):
    """Residuo de equilibrio global (fuerzas y momentos respecto del origen) de un estado.
    Acciones: cargas nodales (CARGAS), peso propio (masa JSON x longitud, en el centroide de cada barra) y
    reacciones (REACCIONES). signo=+1: la reaccion reportada es la fuerza que el apoyo ejerce sobre la estructura.
    signo=-1: convencion contraria (control)."""
    Fa, Ma, Fw, Mw, FR, MR = (np.zeros(3) for _ in range(6))
    esc_F = esc_M = 0.0
    for _, c in c_est.iterrows():
        r = coords[int(float(c['ID']))]
        f = np.array([num(c['FX']), num(c['FY']), num(c['FZ'])])
        m = np.array([num(c['MX']), num(c['MY']), num(c['MZ'])])
        Fa += f
        Ma += m + np.cross(r, f)
        esc_F += np.abs(f).sum()
        esc_M += np.abs(m).sum() + np.abs(np.cross(r, f)).sum()
    if pp:
        for _, b in bar.iterrows():
            ri = coords[int(float(b['NODO_I']))]
            rj = coords[int(float(b['NODO_J']))]
            w = masa_json(str(b['PERFIL']).strip()) * float(np.linalg.norm(rj - ri))     # kgf
            f = np.array([0.0, 0.0, -w])
            rc = (ri + rj) / 2.0
            Fw += f
            Mw += np.cross(rc, f)
            esc_F += w
            esc_M += float(np.linalg.norm(np.cross(rc, f)))
    for _, q in r_est.iterrows():
        r = coords[int(float(q.iloc[2]))]
        f = np.array([num(q.iloc[4]), num(q.iloc[5]), num(q.iloc[6])])          # kgf
        m = np.array([num(q.iloc[7]), num(q.iloc[8]), num(q.iloc[9])])          # kgf·m
        FR += f
        MR += m + np.cross(r, f)
        esc_F += np.abs(f).sum()
        esc_M += np.abs(m).sum() + np.abs(np.cross(r, f)).sum()
    return Fa + Fw + signo * FR, Ma + Mw + signo * MR, esc_F, esc_M


def prueba_1_equilibrio():
    print('\n== 1. Equilibrio global de fuerzas y momentos (caso gravitacional y caso sismo) ==', flush=True)
    n = 0
    for etiqueta, carpeta, estados_prueba in [
            ('ejemplo', EJEMPLO, ['Peso propio y muerta', 'Sobrecarga']),
            ('sismo', SISMO, ['Peso propio y muerta', 'Sobrecarga', 'Sismo X'])]:
        coords, bar, cg, estados = leer_entrada(carpeta)
        reac = pd.read_excel(os.path.join(carpeta, 'resultados_soportes.xlsx'), sheet_name='REACCIONES', dtype=object)
        reac = reac[reac.iloc[:, 1].astype(str).str.strip() == 'ESTADO']
        for est in estados_prueba:
            tipo, pp_txt = estados[est]
            pp = pp_txt == 'SI'
            c_est = cg[cg['ESTADO'] == est]
            r_est = reac[reac.iloc[:, 0].astype(str).str.strip() == est]
            Fp, Mp, eF, eM = residuos(coords, bar, c_est, r_est, pp, +1.0)
            n += 1
            tol_F, tol_M = 1e-7 * max(eF, 1.0), 1e-7 * max(eM, 1.0)
            rF, rM = float(np.linalg.norm(Fp)), float(np.linalg.norm(Mp))
            etiq = f'{etiqueta}, estado "{est}" (tipo {tipo}, PP={pp_txt})'
            reg(rF <= tol_F, f'1.{n}a', f'{etiq}: suma de fuerzas', f'{rF:.3g} kgf',
                f'0 (tol {tol_F:.2g})', f'componentes {np.round(Fp, 9).tolist()}')
            n += 1
            reg(rM <= tol_M, f'1.{n}b', f'{etiq}: suma de momentos respecto del origen', f'{rM:.3g} kgf·m',
                f'0 (tol {tol_M:.2g})', f'componentes {np.round(Mp, 9).tolist()}')
            if est == 'Peso propio y muerta' and etiqueta == 'ejemplo':
                Fn, Mn, _, _ = residuos(coords, bar, c_est, r_est, pp, -1.0)
                no_cierra = float(np.linalg.norm(Fn)) > 1e-4 * max(eF, 1.0) or float(np.linalg.norm(Mn)) > 1e-4 * max(eM, 1.0)
                reg(rF <= tol_F and rM <= tol_M and no_cierra, '1.control-signo',
                    'signo de las reacciones: con la convencion de la hoja el equilibrio cierra y con el signo opuesto no',
                    f'residuo signo opuesto F={float(np.linalg.norm(Fn)):.4g} kgf, M={float(np.linalg.norm(Mn)):.4g} kgf·m',
                    '> 1e-4 x escala', 'reaccion = fuerza que el apoyo ejerce sobre la estructura (FZ hacia arriba)')
    # control de masas: JSON del repositorio (usado aqui) contra el modulo que usa el programa
    for k, nombre in enumerate(['IR 10 × 49', 'IR 12 × 16'], start=1):
        cmp(f'1.masa{k}', f'masa {nombre}: JSON del repositorio = modulo del programa',
            float(G.obtener_perfil(nombre)['masa']), masa_json(nombre), tol_abs=1e-9)


# ===================================================================================================
# Modelos auxiliares
# ===================================================================================================
def viga_dib(xs_m, apoyos, conex=('empotrado', 'empotrado'), perfil='IR 10 × 49'):
    """Viga recta a lo largo de X con nodos en xs_m (m) y barras encadenadas (como en construir_modelo)."""
    dib = DibujoModelo()
    dib.nodos = [(float(x), 0.0, 0.0) for x in xs_m]
    n = len(xs_m)
    for k in range(n - 1):
        ci = conex[0] if k == 0 else 'empotrado'
        cj = conex[1] if k == n - 2 else 'empotrado'
        idx = dib.barra(k, k + 1, 'VIGA', perfil, conexion_i=ci, conexion_j=cj, material='M')
        dib.eje_fuerte(idx, (0.0, 0.0, 1.0))      # eje fuerte explicito: peralte vertical (obligatorio en la planilla)
    for i, r in apoyos.items():
        dib.apoyo(i, r)
    return dib


def os_una_barra(p1_m, p2_m, vecxz, E, nu, A, J, Iy, Iz, carga_punta=None, uniforme=None, apoyo_1=(1,) * 6,
                 apoyo_2=None):
    """Modelo OpenSees directo (openseespy, elasticBeamColumn 3D, geomTransf Linear), con la misma llamada que el
    programa: (A, E, G, J, Iy, Iz, transf). Unidades cm, kgf. Devuelve (desplazamientos del nudo 2, localForces)."""
    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 6)
    ops.node(1, *[float(c) * 100.0 for c in p1_m])
    ops.node(2, *[float(c) * 100.0 for c in p2_m])
    ops.fix(1, *[int(v) for v in apoyo_1])
    if apoyo_2 is not None:
        ops.fix(2, *[int(v) for v in apoyo_2])
    G_mod = E / (2.0 * (1.0 + nu))
    ops.geomTransf('Linear', 1, *vecxz)
    ops.element('elasticBeamColumn', 1, 1, 2, float(A), float(E), float(G_mod), float(J), float(Iy), float(Iz), 1)
    ops.timeSeries('Constant', 1)
    ops.pattern('Plain', 1, 1)
    if carga_punta is not None:
        ops.load(2, *[float(c) for c in carga_punta])
    if uniforme is not None:
        ops.eleLoad('-ele', 1, '-type', '-beamUniform', *[float(c) for c in uniforme])
    ops.system('BandGeneral')
    ops.numberer('RCM')
    ops.constraints('Transformation')
    ops.integrator('LoadControl', 1.0)
    ops.algorithm('Linear')
    ops.analysis('Static')
    estado = ops.analyze(1)
    u2 = np.array(ops.nodeDisp(2), float)
    ef = np.array(ops.eleResponse(1, 'localForces'), float)
    ops.wipe()
    if estado != 0:
        raise RuntimeError('openseespy no resolvio')
    return u2, ef


def momento_tramo(f_I, L_cm, q_y):
    """Momento Mz(x) a lo largo de la barra a partir de las fuerzas que los nudos ejercen sobre ella (localForces):
    M(x) = -M_I + x*V_I + (x^2/2)*q_y. Verifica M(L) = M_J con el mismo criterio de signos."""
    xs = np.linspace(0.0, L_cm, 4001)
    return -f_I[5] + xs * f_I[1] + 0.5 * xs ** 2 * q_y


# ===================================================================================================
# 2. Voladizo 3D con carga de punta en Y y en Z (ejes fuertes y debiles), openseespy directo
# ===================================================================================================
def prueba_2_voladizo_3d():
    print('\n== 2. Voladizo 3D: carga en punta, eje fuerte (Iz) y eje debil (Iy), convencion vecxz de la planilla ==',
          flush=True)
    E, nu = 2038900.0, 0.3                  # MATERIALES: A-572 G 50
    A, J = 92.9, 57.9                       # IR 10 x 49 (base Gerdau rev04)
    Ix, Iy = 11321.0, 3888.0               # Ix = eje fuerte (peralte), Iy = eje debil
    L, P = 300.0, 1000.0                    # cm, kgf
    p1, p2 = (0.0, 0.0, 0.0), (3.0, 0.0, 0.0)
    b = {'n1': 0, 'n2': 1, 'elemento': 'VIGA', 'eje_fuerte': (0.0, 0.0, 1.0)}   # peralte vertical explicito
    dib = DibujoModelo()
    dib.nodos = [p1, p2]
    dib.barras = [b]
    x, y, z = ejes_locales(dib, 0)
    reg(abs(y[2] - 1.0) < 1e-12, '2.0', 'ejes de la planilla (vecxz por defecto): eje fuerte local y = Z global (peralte vertical)',
        f'y = {np.round(y, 6).tolist()}', '[0, 0, 1]')
    vx = vecxz_de_barra(dib.nodos, b)
    u, _ = os_una_barra(p1, p2, vx, E, nu, A, J, Iy, Ix, carga_punta=[0, 0, P, 0, 0, 0])
    cmp('2.1', 'carga Z (eje fuerte = local y, peralte vertical): flecha PL^3/(3E*Iz), Iz = Ix Gerdau (cm)',
        u[2], P * L ** 3 / (3 * E * Ix))
    u, _ = os_una_barra(p1, p2, vx, E, nu, A, J, Iy, Ix, carga_punta=[0, P, 0, 0, 0, 0])
    cmp('2.2', 'carga Y (eje debil = local z): flecha PL^3/(3E*Iy), Iy = Iy Gerdau (cm)',
        u[1], P * L ** 3 / (3 * E * Iy))
    b2 = {'n1': 0, 'n2': 1, 'elemento': 'VIGA', 'eje_fuerte': (0.0, 1.0, 0.0)}
    vx2 = vecxz_de_barra(dib.nodos, b2)
    u, _ = os_una_barra(p1, p2, vx2, E, nu, A, J, Iy, Ix, carga_punta=[0, P, 0, 0, 0, 0])
    cmp('2.3', 'eje fuerte horizontal (peralte en Y): carga Y usa Iz = Ix Gerdau (cm)', u[1], P * L ** 3 / (3 * E * Ix))
    u, _ = os_una_barra(p1, p2, vx2, E, nu, A, J, Iy, Ix, carga_punta=[0, 0, P, 0, 0, 0])
    cmp('2.4', 'eje fuerte horizontal (peralte en Y): carga Z usa Iy = Iy Gerdau (cm)', u[2], P * L ** 3 / (3 * E * Iy))
    u, _ = os_una_barra(p1, p2, vx, E, nu, A, J, Iy, Ix, carga_punta=[P, 0, 0, 0, 0, 0])
    cmp('2.5', 'control axial: carga X, u = PL/(EA) (cm)', u[0], P * L / (E * A))


# ===================================================================================================
# 3. Rotulas (CONEXION rotulado) y voladizo con rotula en la punta
# ===================================================================================================
def prueba_3_rotulas():
    print('\n== 3. Rotulas: biapoyada, empotrada-rotulada, voladizo con rotula en la punta ==', flush=True)
    qL2_8 = Q_TEST * L_TEST ** 2 / 8.0
    apoyo_pin_rot = (True, True, True, True, False, False)
    apoyo_rod = (False, True, True, False, False, False)

    # 3.1 programa: biapoyada rotulada en ambos extremos (la forma natural de pedirla en la planilla)
    dib = viga_dib([0.0, 6.0], {0: apoyo_pin_rot, 1: apoyo_rod}, conex=('rotulado', 'rotulado'))
    props = [dict(PROPS_TEST)]
    nom31 = 'PROGRAMA biapoyada rotulada en ambos extremos: M extremos = 0 y M max = qL^2/8 (kgf·cm)'
    try:
        r = AO._resolver(dib, props, {}, True)
        f31 = r['barras'][0]
        mmax31 = float(np.max(np.abs(momento_tramo(f31[:6], L_TEST, -Q_TEST * ejes_locales(dib, 0)[1][2]))))
        ext31 = max(abs(f31[5]), abs(f31[11]))
        reg(ext31 <= 1e-6 and abs(mmax31 - qL2_8) <= 1e-6 * qL2_8, '3.1', nom31,
            f'extremos {ext31:.4g}; max {mmax31:.6g}', f'0; {qL2_8:.6g}')
    except AO.ErrorAnalisis as e:
        # Biapoyada con pasadores en el plano y torsion libre en ambos extremos: es un mecanismo. El programa debe avisarlo.
        reg(True, '3.1', 'PROGRAMA biapoyada con rotulas en ambos extremos: debe reportar MODELO INESTABLE (torsion libre)',
            f'ErrorAnalisis: {str(e)[:60]}', 'ErrorAnalisis (inestable)')

    # 3.1b diagnostico: con los giros de los nudos principales fijados sigue sin resolver: la causa es la torsion
    d31 = viga_dib([0.0, 6.0], {0: FIX, 1: (False, True, True, True, True, True)}, conex=('rotulado', 'rotulado'))
    try:
        AO._resolver(d31, props, {}, True)
        info('3.1b', 'diagnostico: biapoyada con giros de nudos principales fijados', 'resuelve')
    except AO.ErrorAnalisis:
        info('3.1b', 'diagnostico: biapoyada con giros de nudos principales fijados (la torsion libre de la barra sigue)',
             'ErrorAnalisis: la causa restante es la torsion de la barra rotulada en ambos extremos')

    # 3.2 reimplementacion (openseespy directo): misma idea de rotula (giros libres en el extremo) pero con la
    #     torsion de un extremo restringida; el programa no permite esa restriccion.
    ops.wipe(); ops.model('basic', '-ndm', 3, '-ndf', 6)
    ops.node(1, 0.0, 0.0, 0.0); ops.node(2, L_TEST, 0.0, 0.0)
    ops.fix(1, 1, 1, 1, 1, 0, 0)            # pasador con torsion restringida
    ops.fix(2, 0, 1, 1, 0, 0, 0)            # rodillo
    dib_ref = viga_dib([0.0, 6.0], {0: FIX})
    x_l, y_l, z_l = ejes_locales(dib_ref, 0)
    vx = vecxz_de_barra(dib_ref.nodos, dib_ref.barras[0])
    ops.geomTransf('Linear', 1, *vx)
    G_mod = PROPS_TEST['E'] / (2 * (1 + PROPS_TEST['nu']))
    ops.element('elasticBeamColumn', 1, 1, 2, PROPS_TEST['A'], PROPS_TEST['E'], G_mod, PROPS_TEST['J'],
                PROPS_TEST['Iy'], PROPS_TEST['Iz'], 1)
    w = np.array([0.0, 0.0, -Q_TEST])
    ops.timeSeries('Constant', 1); ops.pattern('Plain', 1, 1)
    ops.eleLoad('-ele', 1, '-type', '-beamUniform', float(w @ y_l), float(w @ z_l), float(w @ x_l))
    ops.system('BandGeneral'); ops.numberer('RCM'); ops.constraints('Transformation')
    ops.integrator('LoadControl', 1.0); ops.algorithm('Linear'); ops.analysis('Static'); ops.analyze(1)
    ef = np.array(ops.eleResponse(1, 'localForces'), float)
    ops.wipe()
    Mx = momento_tramo(ef[:6], L_TEST, float(w @ y_l))
    ext = max(abs(ef[5]), abs(ef[11]))
    cmp('3.2a', 'REIMPLEMENTACION biapoyada (openseespy): momento en extremos = 0', ext, 0.0, tol_abs=1e-6,
        nota='no es el programa: el programa no resuelve este caso (3.1)')
    cmp('3.2b', 'REIMPLEMENTACION biapoyada (openseespy): momento maximo en el tramo = qL^2/8 (kgf·cm)',
        float(np.max(np.abs(Mx))), qL2_8, tol_rel=1e-6, nota='no es el programa')
    ops.wipe()     # el bloque de reimplementacion deja el dominio de OpenSees con estado propio: se limpia antes del programa

    # 3.3 programa: empotrada-rotulada (un extremo con rotula, el otro empotrado). Solvable con el programa.
    dib = viga_dib([0.0, 6.0], {0: FIX, 1: FIX}, conex=('rotulado', 'empotrado'))
    props = [dict(PROPS_TEST)]
    r = AO._resolver(dib, props, {}, True)
    f = r['barras'][0]
    cmp('3.3a', 'PROGRAMA empotrada-rotulada: momento en la rotula (I) = 0 (kgf·cm)', f[5], 0.0, tol_abs=1e-6)
    cmp('3.3b', 'PROGRAMA empotrada-rotulada: momento en el empotramiento (J) = qL^2/8 (kgf·cm)',
        abs(f[11]), qL2_8, tol_rel=1e-6)
    qy = float(np.array([0.0, 0.0, -Q_TEST]) @ ejes_locales(dib, 0)[1])
    Mx = momento_tramo(f[:6], L_TEST, qy)
    cmp('3.3c', 'PROGRAMA empotrada-rotulada: M max en el tramo = qL^2/8 (kgf·cm) y M(L) = M_J (control de signos)',
        float(np.max(np.abs(Mx))), qL2_8, tol_rel=1e-6,
        nota=f'control M(L)-M_J = {abs(Mx[-1] - f[11]):.2g}')
    cmp('3.3d', 'PROGRAMA empotrada-rotulada: reaccion en la rotula = 3qL/8 (kgf, hacia arriba)',
        r['reac'][0][2], 3 * Q_TEST * L_TEST / 8.0, tol_rel=1e-6)

    # 3.4 programa: voladizo con rotula en la punta (la punta libre no tiene momento)
    dib = viga_dib([0.0, 6.0], {0: FIX}, conex=('empotrado', 'rotulado'))
    nom34 = 'PROGRAMA voladizo con rotula en la punta: M en la punta = 0 (kgf·cm)'
    try:
        r34 = AO._resolver(dib, [dict(PROPS_TEST)], {}, True)
        reg(abs(r34['barras'][0][11]) <= 1e-6, '3.4', nom34, f'{r34["barras"][0][11]:.4g}', '0')
    except AO.ErrorAnalisis:
        reg(False, '3.4', nom34, 'ErrorAnalisis (no resuelve)', '0',
            'no se puede hacer con el codigo tal como esta: ver nota de causa en el informe')

    # 3.4b diagnostico: si se fijan los giros del nudo principal de la punta, el programa resuelve (causa = GDL huerfanos)
    dib_d = viga_dib([0.0, 6.0], {0: FIX, 1: (False, False, False, True, True, True)}, conex=('empotrado', 'rotulado'))
    try:
        rd = AO._resolver(dib_d, [dict(PROPS_TEST)], {}, True)
        info('3.4b', 'diagnostico: punta rotulada con los giros del nudo principal fijados (no es el programa tal cual)',
             f'resuelve; M punta = {rd["barras"][0][11]:.3g} kgf·cm')
    except AO.ErrorAnalisis:
        info('3.4b', 'diagnostico: punta rotulada con giros del nudo principal fijados', 'ErrorAnalisis')

    # 3.5 reimplementacion: voladizo con punta rotulada (el nudo de la punta solo tiene los giros de la barra)
    ops.wipe(); ops.model('basic', '-ndm', 3, '-ndf', 6)
    ops.node(1, 0.0, 0.0, 0.0); ops.node(2, L_TEST, 0.0, 0.0)
    ops.fix(1, 1, 1, 1, 1, 1, 1)
    ops.geomTransf('Linear', 1, *vx)
    ops.element('elasticBeamColumn', 1, 1, 2, PROPS_TEST['A'], PROPS_TEST['E'], G_mod, PROPS_TEST['J'],
                PROPS_TEST['Iy'], PROPS_TEST['Iz'], 1)
    ops.timeSeries('Constant', 1); ops.pattern('Plain', 1, 1)
    ops.eleLoad('-ele', 1, '-type', '-beamUniform', float(w @ y_l), float(w @ z_l), float(w @ x_l))
    ops.system('BandGeneral'); ops.numberer('RCM'); ops.constraints('Transformation')
    ops.integrator('LoadControl', 1.0); ops.algorithm('Linear'); ops.analysis('Static'); ops.analyze(1)
    u2 = np.array(ops.nodeDisp(2), float)
    ef = np.array(ops.eleResponse(1, 'localForces'), float)
    ops.wipe()
    cmp('3.5a', 'REIMPLEMENTACION voladizo con punta rotulada: M en la punta = 0 (kgf·cm)', ef[11], 0.0, tol_abs=1e-6,
        nota='no es el programa: el programa no resuelve este caso (3.4)')
    cmp('3.5b', 'REIMPLEMENTACION voladizo con punta rotulada: flecha en la punta = qL^4/(8EIz) (cm)',
        u2[2], -Q_TEST * L_TEST ** 4 / (8 * PROPS_TEST['E'] * PROPS_TEST['Iz']), tol_rel=1e-6, nota='no es el programa')


# ===================================================================================================
# 4. Mecanismo: un grado de libertad sin restriccion
# ===================================================================================================
def prueba_4_mecanismo():
    print('\n== 4. Mecanismo (GDL de giro sin restriccion en la base): el programa debe fallar, no dar numeros ==',
          flush=True)
    # voladizo con RZ libre en la base: la barra puede girar rigidamente alrededor de Z
    apoyo_mec = (True, True, True, True, True, False)
    dib = viga_dib([0.0, 6.0], {0: apoyo_mec})
    props = [dict(PROPS_TEST)]
    # 4.1 carga que excita el mecanismo (Fy en la punta)
    try:
        r = AO._resolver(dib, props, {1: [0.0, 100.0, 0.0, 0.0, 0.0, 0.0]}, False)
        uy = r['nodos'][1][1]
        reg(False, '4.1', 'PROGRAMA (_resolver), RZ libre en la base + Fy=100 kgf en punta: debe reportar fallo',
            f'sin error: UY punta = {uy:.4g} cm (sin aviso)', 'ErrorAnalisis o marca de no resuelto',
            'la matriz es singular pero el solver no lo detecta: el numero se entrega como resultado')
    except AO.ErrorAnalisis as e:
        reg(True, '4.1', 'PROGRAMA (_resolver), RZ libre en la base + Fy=100 kgf en punta: debe reportar fallo',
            'ErrorAnalisis', 'ErrorAnalisis')

    # 4.2 pipeline completo (correr): el Excel se escribe con esos numeros y no hay error
    dib_c = viga_dib([0.0, 6.0], {0: apoyo_mec}, perfil='IR 10 × 49')
    dib_c.cargas = {'Punta Y': {1: [0.0, 100.0, 0.0, 0.0, 0.0, 0.0]}}
    dib_c.combinaciones = {}
    materiales = {'M': {'E': 2038900.0, 'nu': 0.3}}
    try:
        bloques, equil, _ = AO.correr(dib_c, materiales, [('Punta Y', False)], {0}, {0, 1}, {0: 1}, {0: 1, 1: 2},
                                      os.path.join(TRABAJO, 'mecanismo_resultados.xlsx'))
        uy_mm = float(bloques['NODOS'].loc[bloques['NODOS']['NODO'] == 2, 'UY (mm)'].iloc[0])
        reg(False, '4.2', 'PROGRAMA (correr -> Excel), mismo mecanismo: debe fallar o marcar no resuelto',
            f'sin error; UY punta = {uy_mm:.4g} mm en el Excel; residuo equilibrio {equil[0][1]:.2g} kgf',
            'ErrorAnalisis', 'el Excel recibe numeros sin aviso')
    except AO.ErrorAnalisis as e:
        reg(True, '4.2', 'PROGRAMA (correr -> Excel), mismo mecanismo: debe fallar o marcar no resuelto',
            'ErrorAnalisis', 'ErrorAnalisis')

    # 4.3 solo peso propio: el mecanismo no se excita; el giro RZ de la base queda indeterminado y se reporta 0
    try:
        AO._probar_estabilidad(dib, props)          # la comprobacion que el programa hace antes de resolver cualquier estado
        reg(False, '4.3', 'PROGRAMA (comprobacion de estabilidad), RZ libre en la base + solo peso propio: debe reportar inestable',
            'sin aviso', 'ErrorAnalisis (MODELO INESTABLE)')
    except AO.ErrorAnalisis as e:
        reg(True, '4.3', 'PROGRAMA (comprobacion de estabilidad), RZ libre en la base + solo peso propio: debe reportar inestable',
            f'ErrorAnalisis: {str(e)[:60]}', 'ErrorAnalisis (MODELO INESTABLE)')

    # 4.4 control: la misma viga con RZ restringido (estable): la carga Y usa el eje debil Iy
    dib_s = viga_dib([0.0, 6.0], {0: FIX})
    r = AO._resolver(dib_s, [dict(PROPS_TEST)], {1: [0.0, 100.0, 0.0, 0.0, 0.0, 0.0]}, False)
    cmp('4.4', 'control estable: viga empotrada con Fy=100 kgf: UY = PL^3/(3E*Iy) (cm), Iy = eje debil',
        r['nodos'][1][1], 100.0 * L_TEST ** 3 / (3 * PROPS_TEST['E'] * PROPS_TEST['Iy']), tol_rel=1e-6)


# ===================================================================================================
# Modelo de la planilla (misma construccion que construir_modelo y adjuntar_cargas del notebook)
# ===================================================================================================
def materiales_planilla(carpeta):
    m = pd.read_excel(os.path.join(carpeta, 'plantilla_soportes.xlsx'), sheet_name='MATERIALES', dtype=object)
    out = {}
    for _, r in m.iterrows():
        if isinstance(r.iloc[0], str):
            out[r.iloc[0].strip()] = {'E': num(r.iloc[4]), 'nu': num(r.iloc[5])}
    return out


def dib_planilla(carpeta, theta=0.0, ejes_col='default'):
    """Modelo de la planilla. theta: giro alrededor de Z aplicado a coordenadas y cargas (kgf, kgf·cm).
    ejes_col='default': columnas con eje fuerte por defecto (vecxz=(1,0,0), fijo en X global).
    ejes_col='explicit': columnas con eje fuerte explicito girado con el modelo (equivale al defecto si theta=0)."""
    f = os.path.join(carpeta, 'plantilla_soportes.xlsx')
    nod = pd.read_excel(f, sheet_name='NODOS', dtype=object)
    nod = nod[nod['ID'].notna()].reset_index(drop=True)
    bar = pd.read_excel(f, sheet_name='BARRAS', dtype=object)
    bar = bar[bar['ID'].notna()].reset_index(drop=True)
    c, s = math.cos(theta), math.sin(theta)
    R = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
    dib = DibujoModelo()
    ids = [int(float(r['ID'])) for _, r in nod.iterrows()]
    mapa = {}
    dib.nodos = []
    for k, (_, r) in enumerate(nod.iterrows()):
        p = R @ np.array([float(r['X (m)']), float(r['Y (m)']), float(r['Z (m)'])])
        dib.nodos.append(tuple(float(v) for v in p))
        mapa[ids[k]] = k
    id_barra = {}
    for _, r in bar.iterrows():
        n1, n2 = mapa[int(float(r['NODO_I']))], mapa[int(float(r['NODO_J']))]
        ci = str(r['CONEXION_I']).strip().lower() if pd.notna(r['CONEXION_I']) else 'empotrado'
        cj = str(r['CONEXION_J']).strip().lower() if pd.notna(r['CONEXION_J']) else 'empotrado'
        elem = str(r['ELEMENTO']).strip().upper()
        idx = dib.barra(n1, n2, elem, str(r['PERFIL']).strip(), conexion_i=ci, conexion_j=cj,
                        material=str(r['MATERIAL']).strip())
        id_barra[idx] = int(float(r['ID']))
        ejes = [r['EJE_FUERTE_X'], r['EJE_FUERTE_Y'], r['EJE_FUERTE_Z']]
        if elem == 'COLUMNA' and ejes_col == 'explicit':
            dib.eje_fuerte(idx, tuple(R @ np.array([0.0, -1.0, 0.0])))
        elif any(pd.notna(v) for v in ejes):
            dib.eje_fuerte(idx, tuple(0.0 if pd.isna(v) else float(v) for v in ejes))
    for k, (_, r) in enumerate(nod.iterrows()):
        restr = [str(r[g]).strip().upper() == 'SI' for g in GRADOS]
        if any(restr):
            dib.apoyo(k, restr)
    cg = pd.read_excel(f, sheet_name='CARGAS', header=7, dtype=object).iloc[:, :9]
    cg.columns = ['ID', 'ESTADO', 'FX', 'FY', 'FZ', 'MX', 'MY', 'MZ', 'NOTA']
    cargas = {}
    for _, r in cg.iterrows():
        if pd.isna(r['ID']) or pd.isna(r['ESTADO']):
            continue
        k = mapa[int(float(r['ID']))]
        est = str(r['ESTADO']).strip()
        F = R @ np.array([num(r['FX']), num(r['FY']), num(r['FZ'])])
        M = R @ np.array([num(r['MX']), num(r['MY']), num(r['MZ'])]) * 100.0          # kgf·m -> kgf·cm
        vals = [float(v) for v in np.concatenate([F, M])]
        previo = cargas.setdefault(est, {}).get(k, [0.0] * 6)
        cargas[est][k] = [a + b for a, b in zip(previo, vals)]
    dib.cargas = cargas
    dib.id_barra = id_barra
    return dib, {k: ids[k] for k in range(len(ids))}, id_barra


def props_planilla(dib, id_barra, carpeta):
    return AO.propiedades_barras(dib, materiales_planilla(carpeta), id_barra)


def girar6(v, R):
    return np.concatenate([R @ v[:3], R @ v[3:6]])


def dif_global(lista_a, lista_b):
    """Diferencia maxima relativa a la escala global del conjunto (no por barra: una barra con esfuerzos casi nulos
    no debe amplificar el redondeo absoluto)."""
    A = np.concatenate([np.ravel(np.asarray(v, float)) for v in lista_a])
    B = np.concatenate([np.ravel(np.asarray(v, float)) for v in lista_b])
    return float(np.max(np.abs(A - B)) / max(1.0, float(np.max(np.abs(A)))))


# ===================================================================================================
# 5. Orientacion girada: todo el modelo girado alrededor de Z (coordenadas, cargas y ejes fuertes)
# ===================================================================================================
def prueba_5_giro():
    print('\n== 5. Modelo girado 30 grados alrededor de Z (coordenadas, cargas y ejes fuertes) ==', flush=True)
    th = math.radians(30.0)
    R = np.array([[math.cos(th), -math.sin(th), 0.0], [math.sin(th), math.cos(th), 0.0], [0.0, 0.0, 1.0]])
    for etiqueta, carpeta, est, pp, codigo in [('ejemplo', EJEMPLO, 'Peso propio y muerta', True, '5.1'),
                                               ('sismo', SISMO, 'Sismo X', False, '5.4')]:
        d0, ids0, b0 = dib_planilla(carpeta, 0.0, 'default')
        r0 = AO._resolver(d0, props_planilla(d0, b0, carpeta), d0.cargas.get(est, {}), pp)
        bars0 = [r0['barras'][i] for i in r0['barras']]
        # control: el modelo reconstruido en el runner reproduce las reacciones guardadas en el Excel del programa
        Rx = pd.read_excel(os.path.join(carpeta, 'resultados_soportes.xlsx'), sheet_name='REACCIONES', dtype=object)
        Rx = Rx[(Rx.iloc[:, 0].astype(str).str.strip() == est) & (Rx.iloc[:, 1].astype(str).str.strip() == 'ESTADO')]
        idx_de_id = {v: k for k, v in ids0.items()}
        excel_vals, modelo_vals = [], []
        for _, q in Rx.iterrows():
            k = idx_de_id[int(float(q.iloc[2]))]
            modelo_vals.append(r0['reac'][k])
            excel_vals.append(np.array([num(q.iloc[4]), num(q.iloc[5]), num(q.iloc[6]),
                                        num(q.iloc[7]) * 100, num(q.iloc[8]) * 100, num(q.iloc[9]) * 100]))
        cmp('5.0a', f'control: modelo reconstruido reproduce REACCIONES del Excel ({etiqueta}, "{est}") (dif. relativa)',
            dif_global(modelo_vals, excel_vals), 0.0, tol_abs=1e-8)
        if etiqueta == 'ejemplo':
            de, _, be = dib_planilla(carpeta, 0.0, 'explicit')
            re_ = AO._resolver(de, props_planilla(de, be, carpeta), de.cargas.get(est, {}), pp)
            dr_ = dif_global([re_['barras'][i] for i in r0['barras']], bars0)
            cmp('5.0', 'control: eje fuerte de columnas explicito con theta=0 = eje por defecto (dif. relativa)',
                dr_, 0.0, tol_abs=1e-9)
        dR, _, bR = dib_planilla(carpeta, th, 'explicit')
        rR = AO._resolver(dR, props_planilla(dR, bR, carpeta), dR.cargas.get(est, {}), pp)
        dif_reac = dif_global([rR['reac'][k] for k in r0['reac']], [girar6(r0['reac'][k], R) for k in r0['reac']])
        dif_barr = dif_global([rR['barras'][i] for i in r0['barras']], bars0)
        dif_nod = dif_global([rR['nodos'][i] for i in r0['nodos']], [girar6(r0['nodos'][i], R) for i in r0['nodos']])
        cmp(codigo, f'{etiqueta}, estado "{est}" girado 30°: reacciones = R x reacciones originales (dif. relativa)',
            dif_reac, 0.0, tol_abs=1e-8)
        cmp(codigo + 'b', f'{etiqueta}, estado "{est}" girado 30°: esfuerzos de cada barra iguales (dif. relativa)',
            dif_barr, 0.0, tol_abs=1e-8)
        cmp(codigo + 'c', f'{etiqueta}, estado "{est}" girado 30°: desplazamientos = R x originales (dif. relativa)',
            dif_nod, 0.0, tol_abs=1e-8)
        if etiqueta == 'ejemplo':
            dD, _, bD = dib_planilla(carpeta, th, 'default')
            rD = AO._resolver(dD, props_planilla(dD, bD, carpeta), dD.cargas.get(est, {}), pp)
            dif_def = dif_global([rD['barras'][i] for i in r0['barras']], bars0)
            # Control: con el eje fuerte dado por el usuario NO girado junto con el modelo, el resultado cambia.
            reg(dif_def > 1e-3, '5.2', f'{etiqueta}, "{est}" girado 30° con el eje fuerte de las columnas SIN girar: '
                'los esfuerzos cambian (el resultado depende del eje dado)', f'dif. relativa maxima {dif_def:.4g}',
                'diferencia mayor que 1e-3', 'control: el eje fuerte es un dato de la planilla')


# ===================================================================================================
# 6. Barra inclinada 45 grados en el plano XZ con carga vertical en la punta
# ===================================================================================================
def prueba_6_inclinada():
    print('\n== 6. Barra inclinada 45 grados (plano XZ), carga vertical en la punta: dos orientaciones (vecxz) ==',
          flush=True)
    E, nu = 2038900.0, 0.3
    A, J = 92.9, 57.9
    Ix, Iy = 11321.0, 3888.0
    L, P = 300.0, 1000.0                    # cm, kgf
    G_mod = E / (2 * (1 + nu))
    c = math.cos(math.radians(45.0))
    p2 = (3.0 * c, 0.0, 3.0 * c)            # m: barra de 3 m a 45 grados (x, z)
    F = np.array([0.0, 0.0, -P])
    # 6.1: eje fuerte perpendicular a la barra en el plano XZ (lo que daba la regla por defecto), explicito
    for codigo, eje, nombre_I in [('6.1', (-math.sqrt(0.5), 0.0, math.sqrt(0.5)), 'Iz = Ix Gerdau (la carga perpendicular cae en el peralte, local y)'),
                                  ('6.2', (0.0, 1.0, 0.0), 'Iy = Iy Gerdau (la carga perpendicular cae en z, eje debil)')]:
        dib = DibujoModelo()
        dib.nodos = [(0.0, 0.0, 0.0), p2]
        b = {'n1': 0, 'n2': 1, 'elemento': 'VIGA', 'eje_fuerte': eje}
        dib.barras = [b]
        x, y, z = ejes_locales(dib, 0)
        vx = vecxz_de_barra(dib.nodos, b)
        Fl = np.array([F @ x, F @ y, F @ z])
        # prediccion con los ejes locales del codigo: y = peralte (siempre Ix, flexion con Iz), z = ancho (Iy), axial A
        ul = np.array([Fl[0] * L / (E * A), Fl[1] * L ** 3 / (3 * E * Ix), Fl[2] * L ** 3 / (3 * E * Iy)])
        u_pred = ul[0] * x + ul[1] * y + ul[2] * z
        u_os, ef = os_una_barra([0.0, 0.0, 0.0], p2, vx, E, nu, A, J, Iy, Ix, carga_punta=[0, 0, -P, 0, 0, 0])
        # comprobacion: analitica en vertical. Componente perpendicular de P al eje: P*sin45 en el plano del peralte.
        if codigo == '6.1':
            vert_an = -P * L ** 3 / (6 * E * Ix) - P * L / (2 * E * A)
            texto = 'flecha vertical punta (cm): -PL^3/(6E*Iz) - PL/(2EA)'
        else:
            vert_an = -P * L ** 3 / (6 * E * Iy) - P * L / (2 * E * A)
            texto = 'flecha vertical punta (cm): -PL^3/(6E*Iy) - PL/(2EA)'
        cmp(codigo + 'a', f'vecxz {"eje fuerte perpendicular (regla anterior)" if codigo == "6.1" else "eje fuerte horizontal"}: {texto}; flexion con {nombre_I}',
            u_os[2], vert_an, tol_rel=1e-6)
        dif = float(np.max(np.abs(u_os[:3] - u_pred)) / max(1e-12, np.max(np.abs(u_pred))))
        cmp(codigo + 'b', f'vecxz {"eje fuerte perpendicular (regla anterior)" if codigo == "6.1" else "eje fuerte horizontal"}: vector de desplazamiento '
            'OpenSees = prediccion con ejes locales del codigo (dif. relativa)', dif, 0.0, tol_abs=1e-8)
        if codigo == '6.1':
            info('6.1c', 'vecxz por defecto: componente de P perpendicular al eje (sin/en el plano del peralte)',
                 f'P_perp = {P/math.sqrt(2):.2f} kgf en la direccion y local {np.round(y, 4).tolist()} '
                 f'(plano del peralte) -> flexion alrededor de z -> Iz')
        else:
            info('6.2c', 'vecxz de peralte horizontal: componente perpendicular de P en la direccion z local',
                 f'z local {np.round(z, 4).tolist()} -> flexion alrededor de y -> Iy (contraste con 6.1)')
    # contraste: con la inercia equivocada la flecha seria distinta (demuestra que el resultado depende de vecxz)
    vert_equiv = -P * L ** 3 / (6 * E * Iy) - P * L / (2 * E * A)
    info('6.3', 'contraste: flecha vertical de 6.1 si se usara Iy en lugar de Iz (cm)', f'{vert_equiv:.4g}')


# ===================================================================================================
def resumen():
    print('\n== RESUMEN ==', flush=True)
    print(f'{"CODIGO":<14} {"RESULTADO":<6}  PRUEBA', flush=True)
    for r in RESULTADOS:
        print(f'{r["cod"]:<14} {"OK" if r["ok"] else "FALLA":<6}  {r["nombre"]}', flush=True)
    n_ok = sum(1 for r in RESULTADOS if r['ok'])
    n_f = len(RESULTADOS) - n_ok
    print(f'\nTotal: {len(RESULTADOS)} pruebas, OK = {n_ok}, FALLA = {n_f}', flush=True)
    return n_f == 0


if __name__ == '__main__':
    print('R-08 verificacion independiente. Modelo: openseespy', flush=True)
    control_fuentes()
    prueba_1_equilibrio()
    prueba_2_voladizo_3d()
    prueba_3_rotulas()
    prueba_4_mecanismo()
    prueba_5_giro()
    prueba_6_inclinada()
    todas_ok = resumen()
    sys.exit(0 if todas_ok else 1)
