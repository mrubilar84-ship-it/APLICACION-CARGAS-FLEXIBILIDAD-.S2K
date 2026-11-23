"""Placas base ASD (bloque 10b). Verifica cada nodo de la hoja BASES con las combinaciones de servicio de REACCIONES.

Chequeos (los valores vienen de la hoja NORMA; el codigo no supone ninguno):
  1. Aplastamiento sobre el dado: P_p = min(0.85 f'c A1 sqrt(A2/A1), 1.7 f'c A1), admisible P_p / Omega_c (IMCA cap. J,
     J8-1 y J8-2; Omega_c = 2.31 en DRP). Con excentricidad fuera del tercio medio: distribucion triangular (NO REVISADO).
  2. Espesor de la placa: voladizo de AISC Design Guide 1 (2.a ed.) en ASD: l = max(m, n, lambda n'),
     t_req = l sqrt(2 Omega f / Fy), Omega = 1.5 / 0.90 (flexion). FU = (t_req / t)^2.
  3. Pernos a traccion: Rn = 0.7 Fu At (DG1 §3.2.1 y p. 19, segun el texto de DG1), Omega = 1.5 / 0.75.
  4. Cono de concreto: N_b = k lambda sqrt(f'c) h_ef^1.5 (ACI 318-02 Ap. D, SI, k = 10), phi = 0.70, Omega = 1.5 / 0.70.
  5. Pernos a cortante con roscas: Rn = 0.4 Fu Ab (DG1 p. 42), phi = 0.75, Omega = 1.5 / 0.75.
  6. Soldadura de filete: 0.6 F_EXX (0.707 w) (DG1 p. 42), phi = 0.75, Omega = 1.5 / 0.75.

Unidades: cm, kgf, kgf/cm2. Los momentos de REACCIONES (kgf·m) se pasan a kgf·cm antes de llegar aqui.
Lo que no se verifico en imagen se marca NO REVISADO en la memoria.
"""
import math
import perfiles_gerdau as G

# Campos de la hoja BASES, en el mismo orden que sus columnas (BASES_COLS de la plantilla).
CAMPOS = ['id', 'fc', 'dado_n', 'dado_b', 'pl_n', 'pl_b', 'pl_t', 'fy', 'n', 'c_t', 'diam', 'hilos', 'fu', 'hef',
          'sold_w', 'sold_l', 'mu', 'nota']
OBLIGATORIOS = [c for c in CAMPOS if c not in ('id', 'nota', 'mu')]   # sin friccion: mu no es dato del calculo
ETIQUETA = {'fc': "f'c (kgf/cm2)", 'dado_n': 'dado N (cm)', 'dado_b': 'dado B (cm)', 'pl_n': 'placa N (cm)',
            'pl_b': 'placa B (cm)', 'pl_t': 'placa t (cm)', 'fy': 'Fy placa (kgf/cm2)', 'n': 'anclas totales n',
            'c_t': 'c anclas (cm)', 'diam': 'diametro ancla (pulg)', 'hilos': 'hilos por pulg', 'fu': 'Fu ancla (kgf/cm2)',
            'hef': 'h_ef ancla (cm)', 'sold_w': 'soldadura w (cm)', 'sold_l': 'longitud soldadura (cm)',
            'mu': 'coef. de friccion'}
NORMA_BASE = ['BASE_J8_085', 'BASE_J8_LIM', 'BASE_OMEGA_C', 'BASE_FACTOR_ASD', 'BASE_PHI_PL', 'BASE_PHI_ANCLA_T',
              'BASE_FNT', 'BASE_PHI_ANCLA_V', 'BASE_FV', 'BASE_PHI_CONO', 'BASE_KC_CONO', 'BASE_LAMBDA',
              'BASE_PHI_SOLD', 'BASE_SOLD_FRAC', 'BASE_FEXX_KSI']
CHEQUEOS = [
    # clave, nombre, referencia (clave de REF en memoria_asd), unidad de demanda
    ('ap', 'Aplastamiento sobre el dado (IMCA cap. J, J8)', 'BASE_J8', 'kgf/cm2'),
    ('pl', 'Espesor de la placa (AISC DG1, voladizo)', 'BASE_DG1_PL', 'cm'),
    ('T', 'Pernos a tracción (AISC DG1 §3.2.1)', 'BASE_DG1_T', 'kgf por perno'),
    ('cono', 'Cono de concreto de los pernos (ACI 318-02 Ap. D)', 'BASE_CONO', 'kgf (grupo de un lado)'),
    ('V', 'Pernos a cortante (AISC DG1 p. 42)', 'BASE_DG1_V', 'kgf por perno'),
    ('w', 'Soldadura columna–placa (AISC DG1 p. 42)', 'BASE_SOLD', 'kgf/cm'),
]
KGF_POR_KSI = 70.307
MPA_POR_KGCM2 = 0.0980665
KGF_POR_N = 1.0 / 9.80665
TOL_MOMENTO = 1e-3                    # kgf·cm: ruido numerico
LIMITACIONES = [
    'pernos: n/2 por lado en la direccion N (X); no se modelan pernos en la direccion Y (NO REVISADO)',
    'pernos: solo predimensionamiento: no se verifican arrancamiento lateral, rotura lateral, pryout, espesor del '
    'elemento ni el efecto de grupo (NO REVISADO)',
    'pernos: cono de concreto con A_Nc = A_Nco (un cono por lado); no se verifican separacion ni distancia al borde '
    '>= 1.5 h_ef (ACI 318-02 Ap. D, NO REVISADO)',
    'soldadura: modelo simplificado (cortante y tension); no es un modelo de grupo de soldadura ni verifica el momento '
    '(NO REVISADO)',
    'transferencia de compresion por contacto (columna a placa) no verificada (NO REVISADO)',
    'cortante: se resiste con pernos y soldadura; no se considera friccion entre placa y concreto (practica chilena)',
    'valores de NORMA marcados NO REVISADO en la hoja NORMA: ver referencia',
]


def _falta(v):
    return v is None or (isinstance(v, float) and math.isnan(v)) or (isinstance(v, str) and not v.strip())


def _num(v):
    if _falta(v):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def envolvente(perfil, eje):
    """Caja de la seccion en planta, en ejes globales X y Y. H = peralte, B = ancho, eje = direccion del peralte."""
    ux, uy = float(eje[0]), float(eje[1])
    m = math.hypot(ux, uy)
    if m < 1e-9:
        raise ValueError('el eje fuerte es vertical: no se puede proyectar la seccion en planta')
    ux, uy = ux / m, uy / m
    return perfil['H'] * abs(ux) + perfil['B'] * abs(uy), perfil['H'] * abs(uy) + perfil['B'] * abs(ux)


def _traccion_lado(P, e, L, W, x_T, f_adm, pernos=True):
    """Compresion P con excentricidad e en la direccion de longitud L, pernos a x_T del borde comprimido.
    Distribucion triangular: C = f B Y / 2 a Y/3 del borde. Si la carga cae dentro del tercio medio, la presion es
    triangular sin pernos. Si queda fuera del tercio medio, el equilibrio (C = P + T; momentos en torno a los pernos)
    da Y y T con f = f_adm. Si la carga queda fuera de la placa (x_P <= 0), solo hay equilibrio con pernos en
    tension (pernos=True); sin pernos en esa direccion no hay apoyo. NO REVISADO contra DG1 §3.2."""
    x_P = L / 2.0 - e
    if x_P > 0:
        Y0 = 3.0 * x_P
        f0 = 2.0 * P / (W * Y0)
        if f0 <= f_adm:
            return {'f': f0, 'f0': f0, 'T': 0.0, 'Y': Y0, 'ok': True, 'tension': False}
        a = Y0
    else:
        if not pernos:
            return {'f': math.inf, 'f0': math.inf, 'T': None, 'Y': None, 'ok': False, 'tension': False}
        f0 = math.inf
        a = 0.0
    k = f_adm * W / 2.0
    g = lambda Y: k * Y * (x_T - Y / 3.0) - P * (x_T - x_P)
    if x_T - x_P <= 0 or g(L) < 0:
        return {'f': f_adm, 'f0': f0, 'T': None, 'Y': None, 'ok': False, 'tension': True}
    b = L
    for _ in range(100):
        m = (a + b) / 2.0
        if g(m) < 0:
            a = m
        else:
            b = m
    Y = (a + b) / 2.0
    return {'f': f_adm, 'f0': f0, 'T': k * Y - P, 'Y': Y, 'ok': True, 'tension': True}


def _apoyo(P, mx, my, N, B, f_adm, c_t):
    """Presion de apoyo y traccion en los pernos del lado X, para compresion P (kgf) y momentos mx, my (kgf·cm).
    Dentro del nucleo (6e_x/N + 6e_y/B <= 1): presion lineal. Fuera: cada direccion se evalua por separado: lineal si
    su excentricidad esta dentro de su tercio medio; triangular si queda fuera (Y = 3(L/2 − e)). La presion de diseno
    es la mayor de las dos direcciones (aproximacion, NO REVISADA para biaxial fuera del nucleo)."""
    ex, ey = abs(my) / P, abs(mx) / P
    if 6 * ex / N + 6 * ey / B <= 1.0:
        f = P / (N * B) * (1 + 6 * ex / N + 6 * ey / B)
        return {'f': f, 'T': 0.0, 'ok': True, 'ex': ex, 'ey': ey, 'fuera': False, 'Y': None,
                'modo_x': 'lineal', 'modo_y': 'lineal', 'f_x': f, 'f_y': f, 'tension_x': False, 'tension_y': False,
                'biaxial_fuera': False}
    if 6 * ex / N <= 1.0:
        rx = {'f': P / (N * B) * (1 + 6 * ex / N), 'T': 0.0, 'Y': None, 'ok': True, 'tension': False}
        modo_x = 'lineal'
    else:
        rx = _traccion_lado(P, ex, N, B, N - c_t, f_adm)
        modo_x = 'pernos' if rx['tension'] else 'triangular'
    if 6 * ey / B <= 1.0:
        f_y = P / (N * B) * (1 + 6 * ey / B)
        ry_tension = False
        modo_y = 'lineal'
    else:
        ry = _traccion_lado(P, ey, B, N, B, f_adm, pernos=False)     # sin pernos en Y: no hay apoyo fuera del tercio
        ry_tension = ry['tension']
        f_y = ry['f0'] if ry['tension'] else ry['f']
        modo_y = 'triangular'
    f_x = rx['f']
    return {'f': max(f_x, f_y), 'T': rx['T'], 'ok': rx['ok'] and math.isfinite(f_y), 'ex': ex, 'ey': ey,
            'fuera': True, 'Y': rx['Y'] if modo_x == 'pernos' else None, 'modo_x': modo_x, 'modo_y': modo_y,
            'f_x': f_x, 'f_y': f_y, 'tension_x': rx['tension'], 'tension_y': ry_tension,
            'biaxial_fuera': ex > 0 and ey > 0 and (6 * ex / N + 6 * ey / B) > 1.0}


def _combinacion(caso, v, d, ctx):
    """Demandas y FU de una combinacion. v = [FX, FY, FZ (kgf), MX, MY, MZ (kgf·cm)]; FZ > 0 = compresion."""
    fx, fy, fz, mx, my, mz = v
    N, B, c_t, n = d['pl_n'], d['pl_b'], d['c_t'], d['n']
    Pc, Pt = max(fz, 0.0), max(-fz, 0.0)
    V = math.hypot(fx, fy)
    c = {'caso': caso, 'Pc': Pc, 'Pt': Pt, 'V': V, 'mx': mx, 'my': my, 'fx': fx, 'fy': fy, 'fz': fz,
         'fu': {}, 'notas': [], 'pendientes': []}
    # R04-03: momento de torsion MZ y momentos sin compresion: no se verifican (no se representan como cero)
    if abs(mz) > TOL_MOMENTO:
        c['pendientes'].append('torsion MZ en la base: no verificada (NO REVISADO)')
    if Pc <= 0 and (abs(mx) > TOL_MOMENTO or abs(my) > TOL_MOMENTO):
        c['pendientes'].append('momento sin compresion en la base: transferencia al dado y anclajes no verificada '
                               '(NO REVISADO)')
    if Pc > 0:
        ap = _apoyo(Pc, mx, my, N, B, ctx['f_adm'], c_t)
        c.update(f=ap['f'], ex=ap['ex'], ey=ap['ey'], fuera=ap['fuera'], Y=ap['Y'], T_ap=ap['T'], ap_ok=ap['ok'],
                 modo_x=ap['modo_x'], modo_y=ap['modo_y'], f_x=ap['f_x'], f_y=ap['f_y'])
        c['fu']['ap'] = ap['f'] / ctx['f_adm'] if ap['ok'] else math.inf
        if ap['fuera']:
            c['notas'].append('excentricidad fuera del tercio medio: distribucion triangular (NO REVISADO)')
        if ap.get('tension_y'):
            c['notas'].append('excentricidad en Y fuera del tercio medio: sin pernos modelados en Y (NO REVISADO)')
        if ap.get('biaxial_fuera'):
            c['pendientes'].append('contacto biaxial fuera del nucleo: presion por direccion, sin solucion de contacto '
                                   '(NO REVISADO)')
        if not math.isfinite(ap['f']):
            c['notas'].append('la resultante queda fuera de la placa (e > mitad de la placa en una direccion): no hay '
                              'apoyo. NO CUMPLE: aumentar la placa o revisar pernos en esa direccion')
        X = 4 * ctx['Wx'] * ctx['Wy'] / (ctx['Wx'] + ctx['Wy']) ** 2 * ctx['Oc'] * Pc / ctx['Pp']
        if X >= 1.0:
            c['notas'].append('parametro X >= 1: la carga excede el aplastamiento (lambda = 1)')
            lam = 1.0
        else:
            lam = 2 * math.sqrt(X) / (1 + math.sqrt(1 - X))
        m_ = (N - 0.95 * ctx['Wx']) / 2.0
        n_ = (B - 0.8 * ctx['Wy']) / 2.0
        np_ = math.sqrt(ctx['Wx'] * ctx['Wy']) / 4.0
        l_ = max(m_, n_, lam * np_)
        treq = l_ * math.sqrt(2.0 * ctx['Opl'] * ap['f'] / d['fy'])
        c.update(X=X, lam=lam, m=m_, n=n_, np=np_, l=l_, treq=treq)
        c['fu']['pl'] = (treq / d['pl_t']) ** 2
    # Traccion en pernos: compresion con excentricidad fuera del tercio medio, o levantamiento (anclas al lado X)
    if Pc > 0:
        Tside = c.get('T_ap')
    else:
        Tside = Pt / 2.0 + abs(my) / (N - 2 * c_t) if (Pt > 0 or abs(my) > 0) else 0.0
        if Pt > 0:
            c['pendientes'].append('levantamiento: flexion de la placa por los pernos no verificada (NO REVISADO)')
        if Pt > 0 and abs(mx) > 0:
            c['pendientes'].append('levantamiento con momento en X: pernos solo en la direccion N (NO REVISADO)')
    if Tside is None:
        c['notas'].append('placa insuficiente: no hay equilibrio con la presion admisible (NO REVISADO)')
        c['fu'].update(T=math.inf, cono=math.inf)
    else:
        Ta = Tside / (n / 2.0)
        c.update(Tside=Tside, Ta=Ta)
        c['fu']['T'] = Ta / ctx['allow_T'] if Tside > 0 else 0.0
        c['fu']['cono'] = Tside / ctx['allow_cono'] if Tside > 0 else 0.0
    # Cortante en pernos (reparto igual entre todos los pernos)
    Va = V / n
    c.update(Va=Va)
    c['fu']['V'] = Va / ctx['allow_V'] if V > 0 else 0.0
    # Soldadura: cortante + tension (levantamiento + momento de ala, conservador)
    Tw = Pt + max(abs(mx) / ctx['Wy'], abs(my) / ctx['Wx'])
    Rw = math.hypot(Tw, V)
    c.update(Tw=Tw, Rw=Rw, Rw_L=Rw / d['sold_l'])
    c['fu']['w'] = (Rw / d['sold_l']) / ctx['allow_w'] if Rw > 0 else 0.0
    return c


def verificar_nodo(datos, perfil, eje, reacciones, nrm):
    """Verifica un nodo de placa base. datos: dict con CAMPOS (float o None); perfil: nombre Gerdau de la columna;
    eje: vector del eje fuerte; reacciones: [(caso, [FX, FY, FZ, MX, MY, MZ])] de las combinaciones (kgf, kgf·cm);
    nrm: valores de la hoja NORMA. Devuelve un dict con estado, verificaciones que gobiernan y notas."""
    res = {'id': datos['id'], 'perfil': perfil, 'datos': datos, 'estado': '', 'fu_max': None, 'verif': [],
           'combos': [], 'notas': [], 'pendientes': [], 'faltan': [], 'norma': [], 'ctx': {}}
    res['faltan'] = [ETIQUETA.get(c, c) for c in OBLIGATORIOS if datos.get(c) is None]
    res['norma'] = [k for k in NORMA_BASE if nrm.get(k) is None]
    if res['norma']:
        res['estado'] = 'FALTA NORMA'
        return res
    if res['faltan']:
        res['estado'] = 'SIN DATOS'
        return res
    d = datos
    N, B = d['pl_n'], d['pl_b']
    invalidos = []
    # R04-07: datos fisicamente validos antes de calcular: finitos, positivos, enteros donde corresponde
    for k in OBLIGATORIOS:
        if not math.isfinite(d[k]):
            invalidos.append(f'{ETIQUETA.get(k, k)}: valor no finito')
    for k in ('fc', 'dado_n', 'dado_b', 'pl_n', 'pl_b', 'pl_t', 'fy', 'c_t', 'diam', 'hilos', 'fu', 'hef',
              'sold_w', 'sold_l'):
        if math.isfinite(d[k]) and d[k] <= 0:
            invalidos.append(f'{ETIQUETA.get(k, k)} debe ser mayor que cero')
    if math.isfinite(d['n']) and (not float(d['n']).is_integer() or d['n'] < 2 or int(d['n']) % 2):
        invalidos.append('anclas totales n debe ser un entero par y al menos 2 (dos lados)')
    if math.isfinite(d['c_t']) and math.isfinite(N) and d['c_t'] >= N / 2.0:
        invalidos.append('c anclas debe ser menor que la mitad de la placa')
    if math.isfinite(N * B) and math.isfinite(d['dado_n'] * d['dado_b']) and d['dado_n'] * d['dado_b'] < N * B:
        invalidos.append('el dado es menor que la placa (A2 < A1)')
    if invalidos:
        res['estado'] = 'DATO INVALIDO'
        res['notas'] += invalidos
        return res
    p = G.obtener_perfil(perfil)
    if p is None or p.get('H') is None or p.get('B') is None:
        res['estado'] = 'SIN DATOS'
        res['faltan'].append('dimensiones H y B del perfil en la base Gerdau')
        return res
    Wx, Wy = envolvente(p, eje)
    if N < Wx or B < Wy:
        res['estado'] = 'DATO INVALIDO'
        res['notas'].append(f'la placa ({N:g} x {B:g} cm) no cubre la envolvente de la seccion ({Wx:.1f} x {Wy:.1f} cm)')
        return res
    Oc = nrm['BASE_OMEGA_C']
    fac = nrm['BASE_FACTOR_ASD']
    Opl = fac / nrm['BASE_PHI_PL']
    OT = fac / nrm['BASE_PHI_ANCLA_T']
    OV = fac / nrm['BASE_PHI_ANCLA_V']
    Ocono = fac / nrm['BASE_PHI_CONO']
    Osol = fac / nrm['BASE_PHI_SOLD']
    A1, A2 = N * B, d['dado_n'] * d['dado_b']
    Pp = min(nrm['BASE_J8_085'] * d['fc'] * A1 * math.sqrt(A2 / A1), nrm['BASE_J8_LIM'] * d['fc'] * A1)
    f_adm = Pp / (Oc * A1)
    # Pernos: area bruta Ab y de tension At (roscada, ASME B1.1), en cm2
    Ab = math.pi / 4.0 * d['diam'] ** 2 * 2.54 ** 2
    At = math.pi / 4.0 * (d['diam'] - 0.9743 / d['hilos']) ** 2 * 2.54 ** 2
    Fu = d['fu']
    allow_T = nrm['BASE_FNT'] * Fu * At / OT
    allow_V = nrm['BASE_FV'] * Fu * Ab / OV
    hef_mm = d['hef'] * 10.0
    Nb = nrm['BASE_KC_CONO'] * nrm['BASE_LAMBDA'] * math.sqrt(d['fc'] * MPA_POR_KGCM2) * hef_mm ** 1.5 * KGF_POR_N
    allow_cono = Nb / Ocono
    fexx = nrm['BASE_FEXX_KSI'] * KGF_POR_KSI
    allow_w = nrm['BASE_SOLD_FRAC'] * fexx * 0.707 * d['sold_w'] / Osol
    ctx = {'Wx': Wx, 'Wy': Wy, 'Oc': Oc, 'Opl': Opl, 'f_adm': f_adm, 'Pp': Pp, 'A1': A1, 'A2': A2,
           'allow_T': allow_T, 'allow_V': allow_V, 'allow_cono': allow_cono, 'allow_w': allow_w, 'Ab': Ab,
           'At': At, 'Nb': Nb, 'fexx': fexx, 'OT': OT, 'OV': OV, 'Ocono': Ocono, 'Osol': Osol, 'Oc_pl': Opl,
           'Kc': nrm['BASE_KC_CONO'], 'Lam': nrm['BASE_LAMBDA'], 'Fnt': nrm['BASE_FNT'], 'Fv': nrm['BASE_FV'],
           'nrm': nrm, 'p': p, 'perfil': perfil, 'eje': tuple(eje)}
    res['ctx'] = ctx
    if not reacciones:
        res['estado'] = 'SIN REACCIONES'
        res['notas'].append('no hay reacciones de combinaciones en este nodo (¿es apoyo del modelo?)')
        return res
    res['combos'] = [_combinacion(caso, v, d, ctx) for caso, v in reacciones]
    for clave, nombre, ref, unidad in CHEQUEOS:
        mejor = max(res['combos'], key=lambda c: c['fu'].get(clave, 0.0))
        fu = mejor['fu'].get(clave, 0.0)
        res['verif'].append({'clave': clave, 'nombre': nombre, 'ref': ref, 'unidad': unidad, 'caso': mejor['caso'],
                             'fu': fu, 'combo': mejor})
    res['fu_max'] = max(v['fu'] for v in res['verif'])
    if any(c['notas'] for c in res['combos']):
        res['notas'] += sorted({n for c in res['combos'] for n in c['notas']})
    # Pendientes: verificaciones no hechas. El estado global no puede ser CUMPLE mientras existan (R04-04).
    res['pendientes'] = sorted({p for c in res['combos'] for p in c['pendientes']}) + LIMITACIONES
    res['notas'] += [p for p in res['pendientes'] if p not in res['notas']]
    if res['fu_max'] > 1.0:
        res['estado'] = 'NO CUMPLE'
    elif res['pendientes']:
        res['estado'] = 'NO REVISADO'
    else:
        res['estado'] = 'CUMPLE'
    return res


def _reacciones_nodo(reacciones, id_nodo):
    """Combinaciones de servicio de REACCIONES para un nodo: [(caso, [FX, FY, FZ, MX, MY, MZ] kgf / kgf·cm)]."""
    out = []
    for _, r in reacciones.iterrows():
        if str(r['TIPO']).strip().upper() != 'COMBINACION':
            continue
        try:
            if int(float(r['NODO'])) != id_nodo:
                continue
        except (TypeError, ValueError):
            continue
        out.append((str(r['CASO']), [float(r['FX (kgf)']), float(r['FY (kgf)']), float(r['FZ (kgf)']),
                                     100.0 * float(r['MX (kgf·m)']), 100.0 * float(r['MY (kgf·m)']),
                                     100.0 * float(r['MZ (kgf·m)'])]))
    return out


def _barra_columna(dib, indice):
    """Barra de columna que llega al nodo (la primera COLUMNA; si no hay, cualquier barra)."""
    cand = [b for b in dib.barras if indice in (b['n1'], b['n2'])]
    col = [b for b in cand if b['elemento'] == 'COLUMNA']
    return (col or cand or [None])[0]


def diseno_bases(dib, id_de_indice, filas, reacciones, nrm):
    """filas: filas de la hoja BASES (listas en el orden de CAMPOS). reacciones: DataFrame de REACCIONES.
    nrm: {clave: valor} de la hoja NORMA. Devuelve [resultado por nodo]."""
    inv = {v: k for k, v in id_de_indice.items()}
    out = []
    for fila in filas:
        datos = {c: (None if i >= len(fila) else (fila[i] if c == 'nota' else _num(fila[i])))
                 for i, c in enumerate(CAMPOS)}
        datos['nota'] = fila[CAMPOS.index('nota')] if len(fila) > CAMPOS.index('nota') else None
        if datos.get('id') is None:
            continue
        id_nodo = int(float(datos['id']))
        datos['id'] = id_nodo
        if id_nodo not in inv:
            out.append({'id': id_nodo, 'perfil': None, 'estado': 'NODO NO EXISTE', 'fu_max': None, 'verif': [],
                        'combos': [], 'notas': [f'el nodo {id_nodo} no existe en NODOS'], 'faltan': [],
                        'norma': [], 'ctx': {}, 'datos': datos})
            continue
        barra = _barra_columna(dib, inv[id_nodo])
        if barra is None:
            out.append({'id': id_nodo, 'perfil': None, 'estado': 'SIN BARRA', 'fu_max': None, 'verif': [],
                        'combos': [], 'notas': ['el nodo no tiene barras'], 'faltan': [], 'norma': [], 'ctx': {},
                        'datos': datos})
            continue
        if barra['eje_fuerte'] is None:
            out.append({'id': id_nodo, 'perfil': barra['perfil'], 'estado': 'SIN EJE FUERTE', 'fu_max': None,
                        'verif': [], 'combos': [], 'notas': ['la barra no tiene EJE_FUERTE'], 'faltan': [],
                        'norma': [], 'ctx': {}, 'datos': datos})
            continue
        r = verificar_nodo(datos, barra['perfil'], barra['eje_fuerte'],
                           _reacciones_nodo(reacciones, id_nodo), nrm)
        if barra['elemento'] != 'COLUMNA':
            r['notas'].insert(0, f"AVISO: el nodo no tiene COLUMNA: se usa la barra de {barra['elemento']}")
        out.append(r)
    return out


def tabla_resumen(resultados):
    """Tabla para el notebook: una fila por nodo."""
    import pandas as pd
    filas = []
    for r in resultados:
        gobierna = max(r['verif'], key=lambda v: v['fu']) if r['verif'] else None
        filas.append({'NODO': r['id'], 'PERFIL': r['perfil'] or '',
                      'FU MAXIMO': None if r['fu_max'] is None else round(r['fu_max'], 3),
                      'ESTADO': r['estado'],
                      'VERIFICACION QUE GOBIERNA': gobierna['nombre'] if gobierna else '',
                      'CASO QUE GOBIERNA': gobierna['caso'] if gobierna else '',
                      'FALTAN DATOS': ', '.join(r['faltan'] + r['norma'])})
    return pd.DataFrame(filas)
