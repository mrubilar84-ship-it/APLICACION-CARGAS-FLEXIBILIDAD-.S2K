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
          'sold_w', 'sold_l', 'nx', 'nota', 'ny']
OBLIGATORIOS = [c for c in CAMPOS if c not in ('id', 'nota')]   # nx, ny: disposicion de pernos (dato de entrada)
ETIQUETA = {'fc': "f'c (kgf/cm2)", 'dado_n': 'dado N (cm)', 'dado_b': 'dado B (cm)', 'pl_n': 'placa N (cm)',
            'pl_b': 'placa B (cm)', 'pl_t': 'placa t (cm)', 'fy': 'Fy placa (kgf/cm2)', 'n': 'anclas totales n',
            'c_t': 'c anclas (cm)', 'diam': 'diametro ancla (pulg)', 'hilos': 'hilos por pulg', 'fu': 'Fu ancla (kgf/cm2)',
            'hef': 'h_ef ancla (cm)', 'sold_w': 'soldadura w (cm)', 'sold_l': 'longitud soldadura (cm)',
            'nx': 'pernos en X, Nx (por fila)', 'ny': 'pernos en Y, Ny (por fila)'}
NORMA_BASE = ['BASE_J8_085', 'BASE_J8_LIM', 'BASE_OMEGA_C', 'BASE_FACTOR_ASD', 'BASE_PHI_PL', 'BASE_PHI_ANCLA_T',
              'BASE_FNT', 'BASE_PHI_ANCLA_V', 'BASE_FV', 'BASE_PHI_CONO', 'BASE_KC_CONO', 'BASE_LAMBDA',
              'BASE_PHI_SOLD', 'BASE_SOLD_FRAC', 'BASE_FEXX_KSI']
CHEQUEOS = [
    # clave, nombre, referencia (clave de REF en memoria_asd), unidad de demanda
    ('ap', 'Aplastamiento sobre el dado (DG1 pag. 14, J8)', 'BASE_J8', 'kgf/cm2'),
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
    'pernos: disposicion Nx x Ny es dato de entrada; cada direccion se verifica por separado; interaccion traccion-corte con la ecuacion AISC 360-22 J3-3b y coeficientes de DG1 (NO REVISADO contra DG1 en imagen)',
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


def _direccion(P, e, L, W, c, fp, cant, bf, Fy):
    """Una direccion de la placa, segun la hoja SMath 'CALCULO PLACA BASE MOMENTOS GRANDES' (DG1 §3.2; NO REVISADO
    contra DG1 en imagen). P (kgf); e, L, W, c (cm); fp = fpmax admisible (kgf/cm2); cant = voladizo DG1 (m o n);
    bf = ancho de patin (cm); Fy (kgf/cm2).
    Momento pequeno (e <= ecrit): compresion, lineal (e <= L/6) o triangular, sin pernos en tension.
    Momento grande (e > ecrit): bloque rectangular fp·W sobre Y desde el borde comprimido; pernos en tension a
    x_T = L − c del borde comprimido; Ta = fp·W·Y − P (total de la fila de pernos); espesor por DG1."""
    q = fp * W
    ecrit = L / 2.0 - P / (2.0 * q)
    if e <= ecrit:
        f = P / (L * W) * (1.0 + 6.0 * e / L) if e <= L / 6.0 else 2.0 * P / (W * 3.0 * (L / 2.0 - e))
        return {'grande': False, 'ok': True, 'ecrit': ecrit, 'e': e, 'f': f}
    f_b = L / 2.0 - c                        # f = Sxx/2: distancia del perno al eje de la placa
    xT = L / 2.0 + f_b                       # distancia del borde comprimido al perno en tension
    disc = xT * xT - 2.0 * P * (e + f_b) / q
    if disc < 0:
        return {'grande': True, 'ok': False, 'ecrit': ecrit, 'e': e, 'f': fp, 'Y': None, 'Ta': None, 'xT': xT,
                'f_b': f_b, 'q': q}
    Y = xT - math.sqrt(disc)
    if Y > L:
        return {'grande': True, 'ok': False, 'ecrit': ecrit, 'e': e, 'f': fp, 'Y': Y, 'Ta': None, 'xT': xT,
                'f_b': f_b, 'q': q}
    Ta = max(q * Y - P, 0.0)
    t_comp = 2.58 * math.sqrt(fp * Y * (cant - Y / 2.0) / Fy)
    x = f_b - bf / 2.0
    t_anc = 2.58 * math.sqrt(Ta * x / (W * Fy)) if (Ta > 0 and x > 0) else 0.0
    return {'grande': True, 'ok': True, 'ecrit': ecrit, 'e': e, 'f': fp, 'Y': Y, 'Ta': Ta, 'xT': xT, 'f_b': f_b,
            'x': x, 'q': q, 't_comp': t_comp, 't_anc': t_anc, 'treq': max(t_comp, t_anc)}


def _apoyo(P, mx, my, d, ctx, cant):
    """Verificacion en las dos direcciones, cada una con sus pernos (n/2 por fila; n es dato de entrada):
    ex = |MY|/P a lo largo de N (X) y ey = |MX|/P a lo largo de B (Y). Ta = tension de la fila mas cargada."""
    N, B, c_t = d['pl_n'], d['pl_b'], d['c_t']
    fp, Wx, Wy = ctx['f_adm'], ctx['Wx'], ctx['Wy']
    bf = min(Wx, Wy)
    ex, ey = abs(my) / P, abs(mx) / P
    dx = _direccion(P, ex, N, B, c_t, fp, cant, bf, d['fy'])
    dy = _direccion(P, ey, B, N, c_t, fp, cant, bf, d['fy'])
    ok = dx['ok'] and dy['ok']
    Ta = max(dx.get('Ta') or 0.0, dy.get('Ta') or 0.0) if ok else None
    fu_ap = max([x['f'] / fp for x in (dx, dy) if not x['grande']] or [0.0])
    if not ok:
        fu_ap = math.inf
    return {'ok': ok, 'ex': ex, 'ey': ey, 'dx': dx, 'dy': dy, 'Ta': Ta, 'fu_ap': fu_ap}


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
        # Voladizo de DG1 para el espesor: l = max(m ; n ; lambda·n'), el mismo en las dos direcciones
        X0 = 4 * ctx['Wx'] * ctx['Wy'] / (ctx['Wx'] + ctx['Wy']) ** 2 * ctx['Oc'] * Pc / ctx['Pp']
        lam0 = 1.0 if X0 >= 1.0 else 2 * math.sqrt(X0) / (1 + math.sqrt(1 - X0))
        m0 = (N - 0.95 * ctx['Wx']) / 2.0
        n0 = (B - 0.8 * ctx['Wy']) / 2.0
        np0 = math.sqrt(ctx['Wx'] * ctx['Wy']) / 4.0
        l0 = max(m0, n0, lam0 * np0)
        ap = _apoyo(Pc, mx, my, d, ctx, l0)
        dx, dy = ap['dx'], ap['dy']
        c.update(ex=ap['ex'], ey=ap['ey'], ap_ok=ap['ok'], Ta_x=dx.get('Ta'), Ta_y=dy.get('Ta'), dx=dx, dy=dy,
                 f=max(dx['f'], dy['f']), fuera=dx['grande'] or dy['grande'], Y=dx.get('Y'), T_ap=ap['Ta'],
                 modo_x='grande' if dx['grande'] else 'pequeno', modo_y='grande' if dy['grande'] else 'pequeno',
                 f_x=dx['f'], f_y=dy['f'])
        c['fu']['ap'] = ap['fu_ap']
        if dx['grande'] or dy['grande']:
            c['notas'].append('excentricidad fuera del tercio medio: bloque rectangular fpmax con pernos en tension '
                              '(hoja SMath; DG1 §3.2, NO REVISADO contra DG1 en imagen)')
        if ap['ex'] > 0 and ap['ey'] > 0 and (6 * ap['ex'] / N + 6 * ap['ey'] / B) > 1.0:
            c['pendientes'].append('contacto biaxial fuera del nucleo: cada direccion se verifica por separado, sin '
                                   'solucion de contacto simultanea (NO REVISADO)')
        if not ap['ok']:
            c['notas'].append('no hay solucion con la presion admisible en alguna direccion: aumentar la placa '
                              '(NO CUMPLE)')
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
        # Espesor: el maximo de todos los casos (combinaciones y direcciones)
        casos_t = []
        f_peq = [x['f'] for x in (dx, dy) if not x['grande']]
        if f_peq:
            casos_t.append(l_ * math.sqrt(2.0 * ctx['Opl'] * max(f_peq) / d['fy']))
        for x in (dx, dy):
            if x['grande']:
                casos_t.append(x['treq'] if x['ok'] else math.inf)
        treq = max(casos_t)
        c.update(X=X, lam=lam, m=m_, n=n_, np=np_, l=l_, treq=treq)
        c['fu']['pl'] = (treq / d['pl_t']) ** 2
    # Traccion en pernos: compresion con excentricidad fuera del tercio medio, o levantamiento (anclas al lado X)
    if Pc > 0:
        Tside = (max(c.get('Ta_x') or 0.0, c.get('Ta_y') or 0.0) if c.get('ap_ok') else None)
    else:
        Tside = Pt / 2.0 + abs(my) / (N - 2 * c_t) if (Pt > 0 or abs(my) > 0) else 0.0
        c.update(Ta_x=Tside, Ta_y=0.0)
        if Pt > 0:
            c['pendientes'].append('levantamiento: flexion de la placa por los pernos no verificada (NO REVISADO)')
        if Pt > 0 and abs(mx) > 0:
            c['pendientes'].append('levantamiento con momento en X: pernos solo en la direccion N (NO REVISADO)')
    # Cortante en pernos (reparto igual entre todos los pernos)
    Va = V / n
    c.update(Va=Va)
    c['fu']['V'] = Va / ctx['allow_V'] if V > 0 else 0.0
    if Tside is None:
        c['notas'].append('placa insuficiente: no hay equilibrio con la presion admisible (NO REVISADO)')
        c['fu'].update(T=math.inf, cono=math.inf)
    else:
        # Fila X (en el borde X) tiene Ny pernos; fila Y tiene Nx pernos (datos de entrada)
        nx, ny = int(d['nx']), int(d['ny'])
        Tp_x = (c.get('Ta_x') or 0.0) / ny
        Tp_y = (c.get('Ta_y') or 0.0) / nx
        Tp = max(Tp_x, Tp_y)
        Fu = d['fu']
        Fnt = ctx['Fnt'] * Fu
        Fnv = ctx['Fv'] * Fu
        OT = ctx['OT']
        fv = Va / ctx['Ab']
        # AISC 360-22 J3-3b (ASD): F'nt = 1.3·Fnt − (Ω·Fnt/Fnv)·f_rv ≤ Fnt ; capacidad admisible = F'nt/Ω
        Fnt_p = max(0.0, min(1.3 * Fnt / OT - Fnt * fv / Fnv, Fnt / OT))
        T_all = Fnt_p * ctx['At']
        c.update(Tside=Tside, Ta=Tp, Tp_x=Tp_x, Tp_y=Tp_y, fv=fv, Fnt_p=Fnt_p, T_all=T_all)
        if Tp <= 0:
            c['fu']['T'] = 0.0
        elif T_all <= 0:
            c['fu']['T'] = math.inf
        else:
            c['fu']['T'] = Tp / T_all
        c['fu']['cono'] = Tside / ctx['allow_cono'] if Tside > 0 else 0.0
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
    if math.isfinite(d['n']) and (not float(d['n']).is_integer() or d['n'] < 2):
        invalidos.append('anclas totales n debe ser un entero de al menos 2')
    if all(math.isfinite(d[k]) for k in ('nx', 'ny', 'n')):
        if (not float(d['nx']).is_integer() or not float(d['ny']).is_integer() or d['nx'] < 1 or d['ny'] < 1
                or d['nx'] * d['ny'] != d['n']):
            invalidos.append('pernos: Nx y Ny deben ser enteros >= 1 con Nx · Ny = n (anclas totales)')
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
