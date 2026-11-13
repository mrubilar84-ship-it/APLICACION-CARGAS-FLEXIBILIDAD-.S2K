"""
DISEÑO DE ELEMENTOS DE ACERO CON LAS NTC PARA DISEÑO Y CONSTRUCCION DE ESTRUCTURAS DE ACERO
(Gaceta Oficial CDMX, 7 de julio de 2020). Unidades internas: cm, kgf, kgf·cm.

ALCANCE DE ESTA VERSION
  - Perfiles I de doble simetria (familia IR): tension, compresion, flexion en ambos ejes, cortante en ambos
    ejes, flexocompresion, flexotension y flexion con cortante.
  - Otras familias: solo tension (si tienen area). El resto aparece como NO REVISADO.
  - Acciones: las COMBINACIONES del analisis (bloque 9). Deben venir ya factoradas segun la norma.
  - Analisis de primer orden: no incluye efectos P-Delta ni P-delta (la norma los pide en el diseño).

DATOS DE ENTRADA (hoja BARRAS, columnas por barra):
  K EJE FUERTE, K EJE DEBIL: factor de longitud efectiva para pandeo alrededor de cada eje. Vacio = 1.0 (se marca).
  LB (m): longitud no soportada lateralmente. Vacio = longitud de la barra (se marca).

CRITERIOS CONSERVADORES (se marcan en la salida):
  Cb = 1.0 (6.2.1 permite un valor mayor); area neta Ae = A (sin agujeros; las conexiones no se modelan).
  Patin no compacto (tipo 3): Mn = My (6.4); el valor interpolado de 6.4.3a no se usa.
"""
import math
import numpy as np
import pandas as pd
import perfiles_gerdau as G

FR_FLUENCIA_T = 0.9        # 4.2.1
FR_FRACTURA_T = 0.75       # 4.2.2
FR = 0.9                   # capitulos 5, 6 y 8
FR_CORTANTE_LAMINADA = 1.0  # 7.2.2 (vigas I laminadas, h/tw <= 2.24 sqrt(E/Fy))
FR_CORTANTE_OTRAS = 0.9    # 7.1 y 7.7
CB_CONSERVADOR = 1.0
K_SUPUESTO = 1.0


class ErrorDiseno(Exception):
    pass


# ---------------------------------------------------------------- tablas y clasificacion
def n_compresion(fy):
    """Tabla 5.2.1 (perfiles I laminados estandar, tp <= 51 mm): (n eje mayor, n eje menor) segun Fy (kgf/cm2)."""
    if fy < 3513:               # <= 2530 kgf/cm2 (A-36) y 2535-3510 kgf/cm2
        return 1.4, 1.4
    if fy <= 3517:              # 3515 kgf/cm2 (Gr. 50)
        return 2.0, 1.4
    return 2.0, 2.0             # 3520-6325 kgf/cm2


def clasificar_i(p, fy, E):
    """Clasificacion de la seccion I: patines (b = bf/2) y alma (h = d - 2 tf). Tablas 3.2.1 y 3.2.2."""
    r = math.sqrt(E / fy)
    b = p['B'] / 2.0
    tf = p['t']
    tw = p['e']
    h = p['H'] - 2.0 * tf
    lf, lw = b / tf, h / tw
    lpf, lrf = 0.38 * r, 1.00 * r
    lpw, lrw = 3.76 * r, 5.70 * r
    f = 'C' if lf <= lpf else ('NC' if lf <= lrf else 'E')
    w = 'C' if lw <= lpw else ('NC' if lw <= lrw else 'E')
    if f == 'C' and w == 'C':
        tipo = 'tipo 2'
    elif f != 'E' and w != 'E':
        tipo = 'tipo 3'
    else:
        tipo = 'tipo 4'
    comp_ok = (lf <= 0.56 * r) and (lw <= 1.49 * r)          # tabla 3.2.1, compresion axial
    return dict(r=r, b=b, h=h, lf=lf, lw=lw, lpf=lpf, lrf=lrf, lpw=lpw, lrw=lrw,
                f=f, w=w, tipo=tipo, comp_ok=comp_ok)


# ---------------------------------------------------------------- tension (capitulo 4)
def resistencia_traccion(p, fy, fu):
    """Rt = min(FR Fy A, FR Fu Ae) con Ae = A. Si no hay Fu, solo fluencia (se marca)."""
    rt_f = FR_FLUENCIA_T * fy * p['A']
    if fu is None:
        return rt_f, 'fractura NO REVISADA: falta Fu del material'
    return min(rt_f, FR_FRACTURA_T * fu * p['A']), ''


# ---------------------------------------------------------------- compresion (capitulo 5)
def resistencia_compresion(p, fy, E, Kx, Ky, Lx, Ly, c):
    """Rc = FR chi Fy A con n por eje (tabla 5.2.1). Devuelve (Rc, detalle por eje)."""
    nx, ny = n_compresion(fy)
    out = {}
    for eje, n, K, L, rr in [('X', nx, Kx, Lx, p['rx']), ('Y', ny, Ky, Ly, p['ry'])]:
        kl_r = K * L / rr
        fe = math.pi ** 2 * E / kl_r ** 2                             # 5.2.4
        lam = math.sqrt(fy / fe)                                      # 5.2.3
        chi = (1.0 + (fy / fe) ** n) ** (-1.0 / n)                    # 5.2.2
        out[eje] = dict(n=n, K=K, L=L, KL_r=kl_r, Fe=fe, lam=lam, chi=chi, Rc=FR * chi * fy * p['A'])
    rc = min(out['X']['Rc'], out['Y']['Rc'])
    return rc, out


# ---------------------------------------------------------------- flexion (capitulo 6)
def _Lu_Lr(Z, fy, Cb, G_, J, Cw, Iy, E):
    """Longitudes Lu y Lr (6.3.5 a 6.3.8). Z = Zx (compacta) o Sx (no compacta, 6.4)."""
    xu = 4.293 * (Z * fy) / (Cb * G_ * J) * math.sqrt(Cw / Iy)
    xr = (4.0 / 3.0) * (Z * fy) / (Cb * G_ * J) * math.sqrt(Cw / Iy)
    k = math.sqrt(E * Cw / (G_ * J))
    lu = math.sqrt(2) * math.pi / xu * k * math.sqrt(1 + math.sqrt(1 + xu ** 2))
    lr = math.sqrt(2) * math.pi / xr * k * math.sqrt(1 + math.sqrt(1 + xr ** 2))
    return lu, lr


def _Me(Cb, Lb, E, G_, Iy, J, Cw):
    """Momento elastico de pandeo lateral (6.3.4)."""
    return (Cb * math.pi / Lb) * math.sqrt(E * Iy * G_ * J + (math.pi * E / Lb) ** 2 * Iy * Cw)


def mn_fuerte(p, fy, E, G_, Lb, Cb, c):
    """Mn alrededor del eje fuerte. Patin compacto: 6.3 (ref. Mp). Patin no compacto: 6.4 (ref. My, sin
    interpolar). Patin esbelto: no revisado. Devuelve (Mn, detalle)."""
    Mp = p['Zx'] * fy
    My = p['Sx'] * fy
    if c['f'] == 'E':
        return None, {'nota': 'patin esbelto (tipo 4): no revisado en esta version'}
    if c['f'] == 'C':
        ref, Z_lim = Mp, p['Zx']
    else:
        ref, Z_lim = My, p['Sx']
    lu, lr = _Lu_Lr(Z_lim, fy, Cb, G_, p['J'], p['Cw'], p['Iy'], E)
    me = _Me(Cb, Lb, E, G_, p['Iy'], p['J'], p['Cw'])
    if Lb <= lu:
        mn = ref                                                     # 6.3.1 / 6.4.1
    elif me > (2.0 / 3.0) * ref:
        mn = min(1.15 * ref * (1.0 - 0.28 * ref / me), ref)          # 6.3.2 / 6.4.2
    else:
        mn = me                                                      # 6.3.3 / 6.4.3
    return mn, dict(Lu=lu, Lr=lr, Me=me, Mp=Mp, My=My)


def mn_debil(p, fy, c):
    """Mn alrededor del eje debil (6.6). Patin compacto: min(Zy Fy, 1.6 Sy Fy). Patin no compacto: Sy Fy
    (conservador; 6.6.2b permite interpolar). Patin esbelto: no revisado."""
    if c['f'] == 'E':
        return None, 'patin esbelto (tipo 4): no revisado en esta version'
    if c['f'] == 'NC':
        return p['Sy'] * fy, 'patin no compacto: Mn = Sy Fy (conservador)'
    return min(p['Zy'] * fy, 1.6 * p['Sy'] * fy), ''


# ---------------------------------------------------------------- cortante (capitulo 7)
def _cv(ht, kv, E, fy):
    """Coeficiente Cv (7.2.3 a 7.2.5)."""
    lim1 = 1.10 * math.sqrt(kv * E / fy)
    lim2 = 1.37 * math.sqrt(kv * E / fy)
    if ht <= lim1:
        return 1.0
    if ht <= lim2:
        return lim1 / ht
    return 1.51 * kv * E / (ht ** 2 * fy)


def vn_fuerte(p, fy, E, c, forma='I'):
    """Cortante en el plano del alma (7.2.1): Aa = h tw. Vigas I laminadas (h/tw <= 2.24 sqrt(E/Fy)): Cv = 1, FR = 1."""
    aa = c['h'] * p['e']
    ht = c['h'] / p['e']
    if forma == 'I' and ht <= 2.24 * math.sqrt(E / fy):
        cv, fr = 1.0, FR_CORTANTE_LAMINADA
    else:
        cv, fr = _cv(ht, 5.0, E, fy), FR_CORTANTE_OTRAS
    vn = 0.6 * fy * aa * cv
    return fr * vn, dict(Aa=aa, ht=ht, Cv=cv, FR=fr)


def vn_debil(p, fy, E, c):
    """Cortante normal al alma (7.7): Aa = bf tf, b/tp con b = bf/2, kv = 1.2, FR = 0.9."""
    aa = p['B'] * p['t']
    ht = c['b'] / p['t']
    cv = _cv(ht, 1.2, E, fy)
    vn = 0.6 * fy * aa * cv
    return FR_CORTANTE_OTRAS * vn, dict(Aa=aa, ht=ht, Cv=cv, FR=FR_CORTANTE_OTRAS)


# ---------------------------------------------------------------- tabla 12.1.2 (ductilidad, NTC 12.1.7)
def ductilidad_12_1_2(p, fy, E, forma, elemento, nivel):
    """Tabla 12.1.2: limites de ancho/grueso de elementos en compresion de miembros de ductilidad alta (lambda_da)
    y media (lambda_dm). Patin de I o canal (no atiesado): b/t <= 0.30 (alta) o 0.38 (media) sqrt(E/Fy).
    Alma de I de contraventeo (ARRIOSTRE o DIAGONAL): h/t <= 1.49 sqrt(E/Fy). nivel = 'ALTA', 'MEDIA' o None
    (None = solo informativo). U <= 1 cumple. Devuelve None para secciones macizas."""
    if p is None or forma not in ('I', 'canal'):
        return None
    r = math.sqrt(E / fy)
    b = p['B'] / 2.0 if forma == 'I' else p['B']
    lf = b / p['t']
    lda_f, ldm_f = 0.30 * r, 0.38 * r
    out = {'lf': lf, 'lda_f': lda_f, 'ldm_f': ldm_f}
    u = None
    if nivel == 'ALTA':
        u = lf / lda_f
    elif nivel == 'MEDIA':
        u = lf / ldm_f
    if forma == 'I' and elemento in ('ARRIOSTRE', 'DIAGONAL'):
        h = p['H'] - 2.0 * p['t']
        lw = h / p['e']
        lim_w = 1.49 * r
        out.update({'lw': lw, 'lda_w': lim_w})
        if nivel is not None:
            uw = lw / lim_w
            u = max(u, uw) if u is not None else uw
    out['U'] = u
    return out


# ---------------------------------------------------------------- canales CE (un eje de simetria)
def clasificar_canal(p, fy, E):
    """Canal: patin de ancho total B (tabla 3.2.2, canales) y alma h = d - 2 tf."""
    r = math.sqrt(E / fy)
    b = p['B']
    tf = p['t']
    tw = p['e']
    h = p['H'] - 2.0 * tf
    lf, lw = b / tf, h / tw
    lpf, lrf = 0.38 * r, 1.00 * r
    lpw, lrw = 3.76 * r, 5.70 * r
    f = 'C' if lf <= lpf else ('NC' if lf <= lrf else 'E')
    w = 'C' if lw <= lpw else ('NC' if lw <= lrw else 'E')
    if f == 'C' and w == 'C':
        tipo = 'tipo 2'
    elif f != 'E' and w != 'E':
        tipo = 'tipo 3'
    else:
        tipo = 'tipo 4'
    comp_ok = (lf <= 0.56 * r) and (lw <= 1.49 * r)
    return dict(r=r, b=b, h=h, lf=lf, lw=lw, lpf=lpf, lrf=lrf, lpw=lpw, lrw=lrw,
                f=f, w=w, tipo=tipo, comp_ok=comp_ok)


def resistencia_compresion_canal(p, fy, E, G_, Kx, Ky, Lx, Ly, Lz, Kz=K_SUPUESTO):
    """Canal (5.2.2.2): Fe = min(Fex, Fe acoplada), Fe acoplada = flexion alrededor del eje debil (no simetrico) con
    torsion (5.2.6). xo = sqrt(ro^2 - (Ix+Iy)/A) (centro de cortante), yo = 0. n = 1.4 y FR = 0.9 (5.2.2).
    Interpretacion: la nota de 5.2.6 dice 'eje de simetria X'; la flexion acoplada se toma alrededor de Y (conservador)."""
    A = p['A']
    ro = p['ro']
    xo = math.sqrt(max(ro ** 2 - (p['Ix'] + p['Iy']) / A, 0.0))
    H = 1.0 - xo ** 2 / ro ** 2
    fex = math.pi ** 2 * E / (Kx * Lx / p['rx']) ** 2
    fey = math.pi ** 2 * E / (Ky * Ly / p['ry']) ** 2
    fez = (G_ * p['J'] + math.pi ** 2 * E * p['Cw'] / (Kz * Lz) ** 2) / (A * ro ** 2)
    fe_c = (fey + fez) / (2.0 * H) * (1.0 - math.sqrt(max(1.0 - 4.0 * fey * fez * H / (fey + fez) ** 2, 0.0)))
    fe = min(fex, fe_c)
    n = 1.4
    lam = math.sqrt(fy / fe)
    chi = (1.0 + (fy / fe) ** n) ** (-1.0 / n)
    rc = FR * chi * fy * A
    det = {'X': dict(n=n, K=Kx, L=Lx, KL_r=Kx * Lx / p['rx'], Fe=fex, lam=None, chi=None, Rc=None),
           'Y': dict(n=n, K=Ky, L=Ly, KL_r=Ky * Ly / p['ry'], Fe=fey, lam=None, chi=None, Rc=None),
           'flexotorsion': dict(n=n, xo=xo, H=H, Fe=fe_c, Fez=fez, Fe_min=fe, lam=lam, chi=chi, Rc=rc)}
    return rc, det


# ---------------------------------------------------------------- por barra
def _props(perfil):
    p = G.obtener_perfil(perfil)
    if p is None:
        return None, f'perfil {perfil} no existe en la base Gerdau'
    faltan = [k for k in ('H', 'B', 'e', 't', 'A', 'Ix', 'Iy', 'Sx', 'Sy', 'rx', 'ry', 'J', 'Cw', 'Zx', 'Zy')
              if p.get(k) is None]
    return p, faltan


def _diseno_cuadrada(out, p, fy, fu, E, nu, Lx, Ly, Lb, Kx, Ky, Cb):
    """Barra maciza cuadrada (CS): compresion 5.2.1(b) con n = 1.4; flexion 6.11 con d = t = lado;
    cortante no cubierto por la NTC (NO REVISADO)."""
    req = ['H', 'A', 'Ix', 'Iy', 'Sx', 'Sy', 'rx', 'ry', 'J', 'Zx', 'Zy']
    falta = [k for k in req if p.get(k) is None]
    if falta:
        out['notas'].append('faltan datos de seccion: ' + ', '.join(falta))
        return out
    G_ = E / (2.0 * (1.0 + nu))
    a = p['H']
    A = p['A']
    out.update({'tipo': 'tipo 2', 'f': 'C', 'w': 'C', 'comp_ok': True, 'forma': 'maciza'})
    res = {}
    for eje, K, L, rr in [('X', Kx, Lx, p['rx']), ('Y', Ky, Ly, p['ry'])]:
        kl_r = K * L / rr
        fe = math.pi ** 2 * E / kl_r ** 2
        chi = (1.0 + (fy / fe) ** 1.4) ** (-1.0 / 1.4)
        res[eje] = dict(n=1.4, K=K, L=L, KL_r=kl_r, Fe=fe, chi=chi, Rc=FR * chi * fy * A)
    out['Rc'] = min(res['X']['Rc'], res['Y']['Rc'])
    out['pandeo'] = res
    mp = p['Zx'] * fy
    my = p['Sx'] * fy
    rel = Lb * a / (a * a)                       # L d / t^2 con d = t = a
    lim1, lim2 = 0.08 * E / fy, 1.9 * E / fy
    if rel <= lim1:
        mn = min(mp, 1.6 * fy * p['Sx'])                                  # 6.11.1
    elif rel <= lim2:
        mn = min(Cb * (1.52 - 0.274 * rel * fy / E) * my, mp)             # 6.11.2
    else:
        mn = min((1.9 * E * Cb / rel) * p['Sx'], mp)                      # 6.11.3 y 6.11.4
    out['MRx'] = FR * mn
    out['MRy'] = FR * min(p['Zy'] * fy, 1.6 * fy * p['Sy'])               # 6.11.1 eje debil
    out['VRy'], out['VRz'] = None, None
    out['notas'].append('NO REVISADO: cortante de barra maciza (la NTC no da regla para esta seccion)')
    out['det_x'] = dict(rel=rel, Mp=mp, My=my)
    out['Mpx'] = p['Zx'] * fy
    out['Mpy'] = p['Zy'] * fy
    out['Py'] = A * fy
    out['Lb'] = Lb
    return out


def diseno_barra(perfil, familia, fy, fu, E, nu, Lx, Ly, Lb, Kx, Ky, Cb=CB_CONSERVADOR):
    """Capacidades de una barra (cm, kgf). IR (perfil I) y CE (canal). Otras familias: solo tension (ver notas)."""
    out = {'perfil': perfil, 'notas': []}
    p, falta = _props(perfil)
    if p is None:
        out['notas'].append(falta)
        return out
    if p.get('A') is None:
        out['notas'].append('falta el area A de la base Gerdau')
        return out
    G_ = E / (2.0 * (1.0 + nu))
    out['Rt'], nota_t = resistencia_traccion(p, fy, fu)
    if nota_t:
        out['notas'].append(nota_t)
    if familia == 'CS':
        return _diseno_cuadrada(out, p, fy, fu, E, nu, Lx, Ly, Lb, Kx, Ky, Cb)
    if familia not in ('IR', 'CE'):
        out['notas'].append(f'NO REVISADO: familia {familia} (en esta version solo tension)')
        return out
    if falta:
        out['notas'].append('faltan datos de seccion: ' + ', '.join(falta))
        return out
    if familia == 'IR':
        c = clasificar_i(p, fy, E)
        forma = 'I'
    else:
        c = clasificar_canal(p, fy, E)
        forma = 'canal'
    out.update({k: c[k] for k in ('tipo', 'f', 'w', 'lf', 'lpf', 'lrf', 'lw', 'lpw', 'lrw', 'comp_ok')})
    out['forma'] = forma
    if forma == 'I':
        out['Rc'], out['pandeo'] = resistencia_compresion(p, fy, E, Kx, Ky, Lx, Ly, c)
    else:
        if p.get('ro') is None:
            out['notas'].append('falta ro (centro de cortante) de la base: compresion NO REVISADA')
            out['Rc'], out['pandeo'] = None, None
        else:
            out['Rc'], out['pandeo'] = resistencia_compresion_canal(p, fy, E, G_, Kx, Ky, Lx, Ly, max(Lx, Ly))
            out['notas'].append('canal: Kz = 1.0 y Lz = mayor longitud no arriostrada (conservador)')
    if not c['comp_ok']:
        out['notas'].append('elemento esbelto en compresion (tabla 3.2.1): compresion NO REVISADA')
    out['MRx'], det_x = mn_fuerte(p, fy, E, G_, Lb, Cb, c)
    if out['MRx'] is not None:
        out['MRx'] = FR * out['MRx']
    else:
        out['notas'].append(det_x['nota'])
    out['det_x'] = det_x
    mn_y, nota_y = mn_debil(p, fy, c)
    out['MRy'] = None if mn_y is None else FR * mn_y
    if nota_y:
        out['notas'].append(nota_y)
    out['VRy'], out['det_vy'] = vn_fuerte(p, fy, E, c, forma)
    out['VRz'], out['det_vz'] = vn_debil(p, fy, E, c)
    out['Mpx'] = p['Zx'] * fy
    out['Mpy'] = p['Zy'] * fy
    out['Py'] = p['A'] * fy
    out['Lb'] = Lb
    return out


def _mx(valores):
    v = [abs(x) for x in valores if x is not None and not (isinstance(x, float) and math.isnan(x))]
    return max(v) if v else 0.0


def chequeos_caso(r, b):
    """Revisa un caso (fila de demandas) contra las capacidades de la barra. r: dict con N, V, M por extremo.
    Devuelve dict con C1..C10 (None = no revisado)."""
    fy_ok = b.get('Rt') is not None
    pc_I, pc_J = max(r['N_I'], 0.0), max(-r['N_J'], 0.0)
    pt_I, pt_J = max(-r['N_I'], 0.0), max(r['N_J'], 0.0)
    pc, pt = max(pc_I, pc_J), max(pt_I, pt_J)
    mx_I, mx_J = abs(r['Mz_I']) * 100.0, abs(r['Mz_J']) * 100.0      # kgf·m -> kgf·cm (eje fuerte)
    my_I, my_J = abs(r['My_I']) * 100.0, abs(r['My_J']) * 100.0     # eje debil
    mx, my = max(mx_I, mx_J), max(my_I, my_J)
    vy, vz = max(abs(r['Vy_I']), abs(r['Vy_J'])), max(abs(r['Vz_I']), abs(r['Vz_J']))
    res = {}
    res['C1 tension'] = (pt / b['Rt']) if (fy_ok and pt > 0) else (0.0 if pt == 0 else None)
    if pc > 0:
        res['C2 compresion'] = (pc / b['Rc']) if (b.get('Rc') and b.get('comp_ok')) else None
    else:
        res['C2 compresion'] = 0.0
    if b.get('MRx') is not None:
        res['C3 flexion eje fuerte'] = mx / b['MRx']
    else:
        res['C3 flexion eje fuerte'] = None
    res['C4 flexion eje debil'] = (my / b['MRy']) if b.get('MRy') else None
    res['C5 cortante eje fuerte'] = (vy / b['VRy']) if b.get('VRy') else None
    res['C6 cortante eje debil'] = (vz / b['VRz']) if b.get('VRz') else None
    # C7: flexocompresion en extremos (8.1.1 y 8.1.3 si tipo 2; 8.1.5 si tipo 3)
    c7 = None
    if pc > 0 and b.get('tipo') in ('tipo 2', 'tipo 3') and b.get('MRx') is not None and b.get('MRy') is not None:
        vals = []
        for pe, mxe, mye in [(pc_I, mx_I, my_I), (pc_J, mx_J, my_J)]:
            if pe <= 0:
                continue
            if b.get('forma') in ('canal', 'maciza') and b['tipo'] == 'tipo 2':
                if not b.get('Mpy'):
                    continue
                vals.append(pe / (FR * b['Py']) + mxe / (FR * b['Mpx']) + mye / (FR * b['Mpy']))   # 8.1.4
                continue
            if b['tipo'] == 'tipo 2':
                if not b.get('Mpy'):
                    continue
                u1 = pe / (FR * b['Py']) + 0.85 * mxe / (FR * b['Mpx']) + 0.60 * mye / (FR * b['Mpy'])
                u2 = mxe / (FR * b['Mpx']) + mye / (FR * b['Mpy'])
                vals.append(max(u1, u2))
            else:
                vals.append(pe / (FR * b['Py']) + mxe / b['MRx'] + mye / b['MRy'])
        c7 = max(vals) if vals else 0.0
    res['C7 flexocompresion extremos'] = c7 if pc > 0 else 0.0
    # C8: columna completa (8.1.6 o 8.1.7)
    if pc > 0 and b.get('Rc') is not None and b.get('MRx') is not None and b.get('MRy') is not None and b.get('comp_ok'):
        if b['tipo'] == 'tipo 2' and b.get('Mpy'):
            res['C8 flexocompresion columna'] = pc / b['Rc'] + mx / b['MRx'] + my / (FR * b['Mpy'])
        elif b['tipo'] == 'tipo 3':
            res['C8 flexocompresion columna'] = pc / b['Rc'] + mx / b['MRx'] + my / b['MRy']
        else:
            res['C8 flexocompresion columna'] = None
    else:
        res['C8 flexocompresion columna'] = None if pc > 0 else 0.0
    # C9: flexotension (8.2.1)
    if pt > 0 and (mx > 0 or my > 0):
        if fy_ok and b.get('MRx') is not None and b.get('MRy') is not None:
            res['C9 flexotension'] = pt / b['Rt'] + mx / b['MRx'] + my / b['MRy']
        else:
            res['C9 flexotension'] = None
    else:
        res['C9 flexotension'] = 0.0
    # C10: flexion y cortante (8.3.1), eje fuerte
    if b.get('MRx') and b.get('VRy'):
        res['C10 flexion y cortante'] = (mx / b['MRx']) ** 2 + (vy / b['VRy']) ** 2
    else:
        res['C10 flexion y cortante'] = None
    res['C11 ductilidad 12.1.2'] = b.get('C11')
    res['C12 esbeltez global KL/r<=200'] = b.get('C12')
    res['C13 columna ductil KL/r<=60'] = b.get('C13')
    return res


def _columnas_caso():
    return ['C1 tension', 'C2 compresion', 'C3 flexion eje fuerte', 'C4 flexion eje debil',
            'C5 cortante eje fuerte', 'C6 cortante eje debil', 'C7 flexocompresion extremos',
            'C8 flexocompresion columna', 'C9 flexotension', 'C10 flexion y cortante',
            'C11 ductilidad 12.1.2', 'C12 esbeltez global KL/r<=200', 'C13 columna ductil KL/r<=60']


# ---------------------------------------------------------------- planilla -> diseño
def _num(v, defecto=None):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return defecto
    try:
        return float(v)
    except (TypeError, ValueError):
        return defecto


def diseno_desde_planilla(dib, materiales_filas, longitudes_df, demandas, id_barra, ruta_salida):
    raise NotImplementedError('Sin uso en la version actual: sus demandas leen solo momentos de extremo (auditoria H-01). No usar.')
    """Diseña todas las barras con las combinaciones del analisis. Las longitudes y factores K vienen de la hoja
    LONGITUDES; lo vacio se toma como supuesto y se marca en la salida. demandas: tabla BARRAS del analisis
    (todas las barras y casos). Devuelve (capacidades, resultados, detalle) y escribe el Excel."""
    if materiales_filas is None:
        raise ErrorDiseno('la planilla no tiene la hoja MATERIALES: no hay fy, fu, E ni nu.')
    mat = {}
    for f in materiales_filas:
        mat[str(f[0]).strip()] = dict(fy=_num(f[2]), fu=_num(f[3]), E=_num(f[4]), nu=_num(f[5]))
    lon = {}
    for _, r in longitudes_df.iterrows():
        id_ = _num(r.get('ID'))
        if id_ is not None:
            lon[int(id_)] = r
    combinaciones = demandas[demandas['TIPO'] == 'COMBINACION']
    if combinaciones.empty:
        raise ErrorDiseno('no hay combinaciones de carga: defina COMBINACIONES (acciones factoradas).')

    caps, res_filas, det_filas = [], [], []
    for i, b in enumerate(dib.barras):
        id_ = id_barra.get(i, i)
        perfil = b['perfil']
        m = mat.get(str(b.get('material') or '').strip())
        p0, _ = _props(perfil)
        familia = p0['familia'] if p0 else '?'
        L = float(np.linalg.norm(np.array(dib.nodos[b['n2']]) - np.array(dib.nodos[b['n1']]))) * 100.0
        r = lon.get(id_)
        supuestos = []

        def campo(nombre):
            return _num(r.get(nombre)) if r is not None else None

        lx, ly, lb = campo('LX (m)'), campo('LY (m)'), campo('LB (m)')
        kx, ky, cb = campo('KX'), campo('KY'), campo('CB')
        if lx is None:
            lx = L / 100.0; supuestos.append('LX = longitud de la barra (supuesto)')
        if ly is None:
            ly = L / 100.0; supuestos.append('LY = longitud de la barra (supuesto)')
        if lb is None:
            lb = L / 100.0; supuestos.append('LB = longitud de la barra (supuesto)')
        if kx is None:
            kx = K_SUPUESTO; supuestos.append('KX = 1.0 (supuesto)')
        if ky is None:
            ky = K_SUPUESTO; supuestos.append('KY = 1.0 (supuesto)')
        if cb is None:
            cb = CB_CONSERVADOR; supuestos.append('CB = 1.0 (conservador)')
        if m is None or m['fy'] is None or m['E'] is None or m['nu'] is None:
            caps.append({'ID': id_, 'PERFIL': perfil, 'NOTA': 'material sin fy, E o nu en MATERIALES'})
            res_filas.append([id_, perfil, b.get('material'), None, None, None, 'DATOS INCOMPLETOS',
                              'material sin fy, E o nu en MATERIALES'])
            continue
        cap = diseno_barra(perfil, familia, m['fy'], m['fu'], m['E'], m['nu'],
                           lx * 100.0, ly * 100.0, lb * 100.0, kx, ky, cb)
        duct_raw = r.get('DUCTILIDAD') if r is not None else None
        nivel = None
        if duct_raw is not None and not (isinstance(duct_raw, float) and math.isnan(duct_raw)) \
                and str(duct_raw).strip() != '':
            nivel = str(duct_raw).strip().upper()
        dd = ductilidad_12_1_2(p0, m['fy'], m['E'], cap.get('forma'), dib.barras[i]['elemento'], nivel)
        elem = dib.barras[i]['elemento']
        es_comp = elem in COMPRESION_GRUPOS
        pdl = cap.get('pandeo') or {}
        kl_max = max(pdl['X']['KL_r'], pdl['Y']['KL_r']) if pdl else None
        cap['C12'] = (kl_max / 200.0 if kl_max is not None else None) if es_comp else 0.0
        cap['C13'] = ((kl_max / 60.0 if kl_max is not None else None)
                      if (elem == 'COLUMNA' and nivel in ('ALTA', 'MEDIA')) else 0.0)
        if kl_max is not None and es_comp and kl_max > 200.0:
            cap['notas'].append('NO CUMPLE KL/r <= 200 (2.3.2)')
        if 'lw' in cap:
            cap.update({'LIM ALMA compresion (3.2.1)': 1.49 * math.sqrt(m['E'] / m['fy']),
                        'LIM ALMA flexion compacta (3.2.2)': cap.get('lpw'),
                        'LIM ALMA flexion no compacta (3.2.2)': cap.get('lrw')})
        if dd is not None:
            cap.update({'DUCTILIDAD': nivel or '(informativo)', 'LAMBDA ALA': dd['lf'],
                        'LIM ALA ALTA': dd['lda_f'], 'LIM ALA MEDIA': dd['ldm_f'],
                        'LAMBDA ALMA': dd.get('lw'), 'LIM ALMA': dd.get('lda_w'), 'C11': dd['U']})
            if nivel is None:
                cap['notas'].append('tabla 12.1.2: sin ductilidad asignada (informativo)')
            elif dd['U'] is not None and dd['U'] > 1.0:
                cap['notas'].append(f'NO CUMPLE tabla 12.1.2 (ductilidad {nivel})')
        cap.update({'ID': id_, 'MATERIAL': b.get('material'), 'LX (m)': lx, 'LY (m)': ly, 'LB (m)': lb,
                    'KX': kx, 'KY': ky, 'CB': cb, 'SUPUESTOS': '; '.join(supuestos)})
        caps.append(cap)
        mejor, peor_caso = None, None
        for _, fila in combinaciones[combinaciones['BARRA'] == id_].iterrows():
            d = dict(N_I=_num(fila['N I (kgf)'], 0.0), N_J=_num(fila['N J (kgf)'], 0.0),
                     Vy_I=_num(fila['Vy I (kgf)'], 0.0), Vy_J=_num(fila['Vy J (kgf)'], 0.0),
                     Vz_I=_num(fila['Vz I (kgf)'], 0.0), Vz_J=_num(fila['Vz J (kgf)'], 0.0),
                     Mz_I=_num(fila['Mz I (kgf·m)'], 0.0), Mz_J=_num(fila['Mz J (kgf·m)'], 0.0),
                     My_I=_num(fila['My I (kgf·m)'], 0.0), My_J=_num(fila['My J (kgf·m)'], 0.0))
            ch = chequeos_caso(d, cap)
            util = [v for v in ch.values() if v is not None]
            maximo = max(util) if util else None
            det_filas.append([id_, perfil, fila['CASO']] + [ch[c] for c in _columnas_caso()] + [maximo])
            if maximo is not None and (mejor is None or maximo > mejor):
                mejor, peor_caso = maximo, fila['CASO']
        notas = cap.get('notas', []) + ([cap['SUPUESTOS']] if cap.get('SUPUESTOS') else [])
        res_filas.append([id_, perfil, b.get('material'), cap.get('tipo'), peor_caso, mejor,
                          _estado(mejor, cap), '; '.join(notas)])
    cols_res = ['ID', 'PERFIL', 'MATERIAL', 'TIPO SECCION', 'CASO QUE GOBIERNA', 'UTILIZACION MAXIMA', 'ESTADO',
                'NOTAS']
    resultados = pd.DataFrame(res_filas, columns=cols_res)
    detalle = pd.DataFrame(det_filas, columns=['ID', 'PERFIL', 'CASO'] + _columnas_caso() + ['MAXIMO'])
    capacidades = pd.DataFrame([_fila_capacidad(c) for c in caps])
    _escribir(ruta_salida, capacidades, resultados, detalle)
    return capacidades, resultados, detalle


def _estado(maximo, cap):
    """CUMPLE / NO CUMPLE segun la utilizacion maxima; REVISAR si alguna parte no se pudo revisar."""
    if cap.get('NOTA'):
        return 'DATOS INCOMPLETOS'
    if maximo is None:
        return 'NO REVISADO'
    notas = ' '.join(cap.get('notas', [])).upper()
    incompleto = 'NO REVISAD' in notas or 'FALTAN DATOS' in notas
    if maximo > 1.0:
        return 'NO CUMPLE'
    return 'REVISAR (partes no revisadas)' if incompleto else 'CUMPLE'


def _fila_capacidad(c):
    """Una fila de la hoja CAPACIDADES: capacidades y longitudes usadas de una barra."""
    rc = c.get('Rc')
    return {'ID': c.get('ID'), 'PERFIL': c.get('perfil') or c.get('PERFIL'), 'MATERIAL': c.get('MATERIAL'),
            'LX (m)': c.get('LX (m)'), 'LY (m)': c.get('LY (m)'), 'LB (m)': c.get('LB (m)'),
            'KX': c.get('KX'), 'KY': c.get('KY'), 'CB': c.get('CB'),
            'TIPO SECCION': c.get('tipo'), 'CLASE ALA': c.get('f'), 'CLASE ALMA': c.get('w'),
            'Rt (kgf)': c.get('Rt'), 'Rc (kgf)': rc, 'MRx (kgf·cm)': c.get('MRx'), 'MRy (kgf·cm)': c.get('MRy'),
            'VRy (kgf)': c.get('VRy'), 'VRz (kgf)': c.get('VRz'),
            'DUCTILIDAD': c.get('DUCTILIDAD'), 'LAMBDA ALA': c.get('LAMBDA ALA'),
            'LIM ALA ALTA': c.get('LIM ALA ALTA'), 'LIM ALA MEDIA': c.get('LIM ALA MEDIA'),
            'LAMBDA ALMA (contraventeo)': c.get('LAMBDA ALMA'), 'LIM ALMA (contraventeo)': c.get('LIM ALMA'),
            'LAMBDA ALMA h/tw': c.get('lw'), 'LIM ALMA compresion (3.2.1)': c.get('LIM ALMA compresion (3.2.1)'),
            'LIM ALMA flexion compacta (3.2.2)': c.get('LIM ALMA flexion compacta (3.2.2)'),
            'LIM ALMA flexion no compacta (3.2.2)': c.get('LIM ALMA flexion no compacta (3.2.2)'),
            'SUPUESTOS': c.get('SUPUESTOS'),
            'NOTAS': '; '.join(c.get('notas') or []) or c.get('NOTA')}


GRUPOS_ELEMENTO = ['COLUMNA', 'VIGA', 'ARRIOSTRE', 'DIAGONAL']
COMPRESION_GRUPOS = ('COLUMNA', 'ARRIOSTRE', 'DIAGONAL')
FAMILIAS_CATALOGO = ('IR', 'CE', 'CS')


def _evaluar_perfil_grupo(nombre, fam, grupo, m, lx, ly, lb, kx, ky, nivel, filas_sint):
    """True si el perfil cumple todas las revisiones de la NTC para la envolvente del grupo (resistencia a tension
    con fractura y Fu, esbeltez local y global, flexion, cortante, interaccion y ductilidad).
    Devuelve (cumple, utilizacion_maxima, motivo)."""
    if m['fu'] is None:
        return False, None, 'no revisado: falta Fu del material (fractura en tension)'
    cap = diseno_barra(nombre, fam, m['fy'], m['fu'], m['E'], m['nu'], lx * 100.0, ly * 100.0, lb * 100.0,
                       kx, ky, CB_CONSERVADOR)
    if 'forma' not in cap or cap.get('NOTA'):
        return False, None, 'no revisable'
    p0, _ = _props(nombre)
    dd = ductilidad_12_1_2(p0, m['fy'], m['E'], cap.get('forma'), grupo, nivel)
    if dd is not None:
        cap['C11'] = dd['U']
    pdl = cap.get('pandeo') or {}
    kl_max = max(pdl['X']['KL_r'], pdl['Y']['KL_r']) if pdl else None
    cap['C12'] = (kl_max / 200.0 if kl_max is not None else None) if grupo in COMPRESION_GRUPOS else 0.0
    cap['C13'] = ((kl_max / 60.0 if kl_max is not None else None)
                  if (grupo == 'COLUMNA' and nivel in ('ALTA', 'MEDIA')) else 0.0)
    maciza = cap.get('forma') == 'maciza'
    util, faltan = [], []
    for d in filas_sint:
        for k, v in chequeos_caso(d, cap).items():
            if v is None:
                permitido = (maciza and k in ('C5 cortante eje fuerte', 'C6 cortante eje debil',
                                              'C10 flexion y cortante')) or (k == 'C11 ductilidad 12.1.2' and nivel is None)
                if not permitido:
                    faltan.append(k)
            else:
                util.append(v)
    if faltan:
        return False, None, 'no revisado: ' + ', '.join(sorted(set(faltan)))
    umax = max(util) if util else 0.0
    return umax <= 1.0, umax, 'cumple' if umax <= 1.0 else 'no cumple'


def listas_por_grupo(dib, materiales_filas, longitudes_df, demandas, id_barra, familias=FAMILIAS_CATALOGO):
    raise NotImplementedError('Sin uso en la version actual: sus demandas leen solo momentos de extremo (auditoria H-01). No usar.')
    """Perfiles del catalogo que cumplen (resistencia, Fu, esbeltez local y global) para cada grupo de elementos.
    Usa la envolvente de las combinaciones de las barras del grupo y la longitud, K y ductilidad mas exigentes.
    Devuelve (listas {grupo: [perfil,...] ordenados por masa}, tabla DataFrame)."""
    import collections
    import perfiles_gerdau as GG
    mat = {}
    for f in materiales_filas:
        mat[str(f[0]).strip()] = dict(fy=_num(f[2]), fu=_num(f[3]), E=_num(f[4]), nu=_num(f[5]))
    lon = {}
    for _, r in longitudes_df.iterrows():
        id_ = _num(r.get('ID'))
        if id_ is not None:
            lon[int(id_)] = r
    comb = demandas[demandas['TIPO'] == 'COMBINACION']
    catalogo = [(n, d['familia'], d['masa_kg_m']) for n, d in GG.PERFILES.items() if d['familia'] in familias]
    listas, filas_tabla = {}, []
    for g in GRUPOS_ELEMENTO:
        idx = [i for i, b in enumerate(dib.barras) if b['elemento'] == g]
        listas[g] = None                       # None = sin barras de este grupo
        if not idx:
            continue
        ids = [id_barra.get(i, i) for i in idx]
        f = comb[comb['BARRA'].isin(ids)]
        if f.empty:
            continue
        num = lambda c: f[c].astype(float).fillna(0.0)
        pc = max(num('N I (kgf)').clip(lower=0).max(), (-num('N J (kgf)')).clip(lower=0).max())
        pt = max((-num('N I (kgf)')).clip(lower=0).max(), num('N J (kgf)').clip(lower=0).max())
        mz = max(num('Mz I (kgf·m)').abs().max(), num('Mz J (kgf·m)').abs().max())
        my = max(num('My I (kgf·m)').abs().max(), num('My J (kgf·m)').abs().max())
        vy = max(num('Vy I (kgf)').abs().max(), num('Vy J (kgf)').abs().max())
        vz = max(num('Vz I (kgf)').abs().max(), num('Vz J (kgf)').abs().max())
        base = dict(Vy_I=vy, Vy_J=vy, Vz_I=vz, Vz_J=vz, Mz_I=mz, Mz_J=mz, My_I=my, My_J=my)
        filas_sint = [dict(base, N_I=pc, N_J=-pc), dict(base, N_I=-pt, N_J=pt)]
        lx = ly = lb = kx = ky = 0.0
        niveles, materiales = set(), collections.Counter()
        for i in idx:
            r = lon.get(id_barra.get(i, i))
            L = float(np.linalg.norm(np.array(dib.nodos[dib.barras[i]['n2']]) - np.array(dib.nodos[dib.barras[i]['n1']])))
            def campo(nombre):
                return _num(r.get(nombre)) if r is not None else None
            v_lx, v_ly, v_lb = campo('LX (m)'), campo('LY (m)'), campo('LB (m)')
            v_kx, v_ky = campo('KX'), campo('KY')
            lx = max(lx, v_lx if v_lx is not None else L)
            ly = max(ly, v_ly if v_ly is not None else L)
            lb = max(lb, v_lb if v_lb is not None else L)
            kx = max(kx, v_kx if v_kx is not None else K_SUPUESTO)
            ky = max(ky, v_ky if v_ky is not None else K_SUPUESTO)
            duct = r.get('DUCTILIDAD') if r is not None else None
            if duct is not None and not (isinstance(duct, float) and math.isnan(duct)) and str(duct).strip():
                niveles.add(str(duct).strip().upper())
            materiales[str(dib.barras[i].get('material') or '').strip()] += 1
        nivel = 'ALTA' if 'ALTA' in niveles else ('MEDIA' if 'MEDIA' in niveles else None)
        material = materiales.most_common(1)[0][0]
        m = mat.get(material)
        if m is None or m['fy'] is None or m['E'] is None or m['nu'] is None:
            continue
        cumplen = []
        listas[g] = []
        for nombre, fam, masa in catalogo:
            ok, umax, motivo = _evaluar_perfil_grupo(nombre, fam, g, m, lx, ly, lb, kx, ky, nivel, filas_sint)
            if ok and fam == 'CS':
                motivo = 'cumple (cortante no cubierto por la NTC para barra maciza)'
            filas_tabla.append([g, nombre, fam, masa, material, umax, motivo])
            if ok:
                cumplen.append((masa if masa is not None else 1e9, nombre, umax))
        cumplen.sort()
        listas[g] = [n for _, n, _ in cumplen]
    tabla = pd.DataFrame(filas_tabla, columns=['GRUPO', 'PERFIL', 'FAMILIA', 'MASA (kg/m)', 'MATERIAL',
                                                'UTILIZACION MAXIMA', 'RESULTADO'])
    return listas, tabla


def _escribir(ruta, capacidades, resultados, detalle):
    with pd.ExcelWriter(ruta, engine='openpyxl') as w:
        resumen = pd.DataFrame([
            ['Norma', 'NTC para Diseño y Construcción de Estructuras de Acero, CDMX (Gaceta 7-jul-2020)'],
            ['Alcance', 'Perfiles I (IR) completos. Otras familias: solo tension. El resto: NO REVISADO.'],
            ['Acciones', 'Combinaciones de COMBINACIONES del analisis; deben venir factoradas.'],
            ['Analisis', 'Primer orden: no incluye P-Delta ni P-delta.'],
            ['Criterios', 'Cb = 1.0; Ae = A (sin agujeros); patin no compacto: Mn = My; eje debil no compacto: Sy Fy.'],
            ['Unidades', 'fuerzas kgf; momentos kgf·cm en capacidades y kgf·m en acciones; longitudes cm'],
        ], columns=['DATO', 'VALOR'])
        resumen.to_excel(w, sheet_name='RESUMEN', index=False)
        capacidades.to_excel(w, sheet_name='CAPACIDADES', index=False)
        resultados.to_excel(w, sheet_name='RESULTADOS', index=False)
        detalle.to_excel(w, sheet_name='DETALLE', index=False)
        for hoja in w.book.worksheets:
            for col in hoja.columns:
                largo = max(len(str(c.value)) if c.value is not None else 0 for c in col)
                hoja.column_dimensions[col[0].column_letter].width = min(max(10, largo + 2), 40)
            hoja.freeze_panes = 'A2'
