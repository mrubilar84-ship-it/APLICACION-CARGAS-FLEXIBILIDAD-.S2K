"""
DISENO ASD SEGUN ANSI/AISC 360-22 (Specification for Structural Steel Buildings, 2022).
Familias: IR (perfil I doblemente simetrico), CE (canal, eje x de simetria), LI (angulo de lados iguales).
Fuera del diseno: CS (barras macizas) y LM (no se consideran por instruccion del usuario).
Unidades: cm, kgf (fuerzas), kgf·cm (momentos). Demandas: ASD (combinaciones de servicio de COMBINACIONES).

Referencias (capitulo y ecuacion del texto de AISC 360-22):
  D2   Traccion: Pn = Fy Ag (Ωt = 1.67); Pn = Fu Ae (Ωt = 2.00)
  E3   Pandeo por flexion: Fe = pi^2 E/(KL/r)^2; Fn = 0.658^(Fy/Fe) Fy si Fy/Fe <= 2.25; 0.877 Fe si no. (E3-1..4)
  E4   Torsional y flexotorsional: E4-2 (doblemente simetrico); E4-3 con Fex si el eje x es de simetria (canales).
  E5   Angulos sencillos: Lc/rz = 72 + 0.75 L/ra (E5-1) o 32 + 1.25 L/ra (E5-2) si se cumplen las condiciones de
       E5(a) (patas de ARRIOSTRE y DIAGONAL). En otros casos se usa K L/rz y el caso debe ir por H2.
       Flexotorsional no requerido si b/t <= 0.71 sqrt(E/Fy); si no, no implementado (se marca NO REVISADO).
  E7   Elementos esbeltos: Ae = Ag - sum (b - be) t; be = b si lambda <= lambda_r; si no E7-3 con Fel = (c2 lambda_r/lambda)^2 Fy.
       Angulos: E3 solamente (E7); patas no atiesadas: lambda_r = 0.45 sqrt(E/Fy), c1 = 0.22, c2 = 1.49 (B4.1a, E7.1c).
  F2   Flexion eje mayor, compacta: Mn = min(Mp, LTB). Mp = Fy Zx; Lp, Lr, Fcr (F2-4..8).
  F3   Patin no compacto/esbelto (I doblemente simetrico): F3-1 y F3-2.
  F6   Flexion eje menor (I y canales): Mn = min(Mp, 1.6 Fy Sy) con F6-2 (no compacto) y F6-3 (esbelto).
  F10  Angulos sencillos, flexion sobre ejes principales: F10-1 (1.5 My); F10-2/3 (LTB con Mcr); F10-4 (Mcr eje
       principal mayor, beta_w = 0 en lados iguales); F10.3 pandeo local de pata: F10-6, F10-7, F10-8 (lambda_p =
       0.54 sqrt(E/Fy), lambda_r = 0.91 sqrt(E/Fy); Table B4.1b caso 12).
  G2   Cortante de almas (I y canales): Vn = 0.6 Fy Aw Cv1 (G2-1); Ωv = 1.50 para I laminada (G2.1a), 1.67 si no.
  G3   Angulo sencillo: Vn = 0.6 Fy b t Cv2 (G3-1), con h/tw = b/t y kv = 1.2 (una pata, conservador).
  H1   Flexocompresion H1-1a/b (Pr/Pc >= 0.2: 8/9); flexotraccion H1-1a/b con Pc = Pn/Ωt.
  H2   Angulos (no cubiertos por H1): H2-1 con momento resultante sobre cada eje principal (conservador).

Supuestos de estimacion (se listan en SUPUESTOS de cada barra):
  IR faltantes: Zx = B t (H - t) + e h^2/4, Zy = B^2 t/2 + h e^2/4 (h = H - 2t); Cw = Iy ho^2/4 (E4, nota de usuario).
  LI: area, Ix e rx de catalogo; centroide, producto de inercia y ejes principales por geometria rectangular (sin acuerdos).
"""
import math
import re
import numpy as np
import pandas as pd
import perfiles_gerdau as G
# DECISION D18 (abierta): resistencia por AISC 360-22 ASD; la NTC-Acero se usa para esbelteces y ductilidad (requisito del proyecto).

# Valores de norma (AISC 360-22 y NTC-Acero CDMX): se leen de la hoja NORMA de la planilla con cargar_norma().
# Este modulo no trae valores de norma ni supuestos: si falta un valor, el calculo se detiene.
OMEGA_T_FLU = OMEGA_T_FRA = OMEGA_C = OMEGA_B = OMEGA_V = OMEGA_V_LAMINADA = None
KV_I = KV_ANGULO = CB_MAX_ANGULO = None
AISC_LP_PATIN = AISC_LR_PATIN = AISC_CV_LIM = AISC_HTW_LAM = AISC_LIM_ANG_E4 = AISC_E5_RAT_LIM = None
AISC_B41A = NTC_LR_COMPRESION = NTC_LIMITES_FLEXION = None
NTC_KLR_COMPRESION = NTC_KLR_TENSION_REF = LIMITE_KLR = None
KZ_TORSION = None


def _req(valor, campo_nombre, barra=''):
    """Dato obligatorio de LONGITUDES (KX, KY, CB, LX, LY, LB): sin valor no se supone nada, se detiene el diseno."""
    if valor is None:
        raise ErrorAsd(f'{barra}falta {campo_nombre} en LONGITUDES (dato obligatorio para el diseno)')
    return valor


def cargar_norma(v, kz):
    """Carga los valores de norma desde la hoja NORMA ({CLAVE: valor}) y el Kz elegido en PARAMETROS."""
    global KZ_TORSION
    KZ_TORSION = kz
    global OMEGA_T_FLU, OMEGA_T_FRA, OMEGA_C, OMEGA_B, OMEGA_V, OMEGA_V_LAMINADA, KV_I, KV_ANGULO, CB_MAX_ANGULO
    global AISC_LP_PATIN, AISC_LR_PATIN, AISC_CV_LIM, AISC_HTW_LAM, AISC_LIM_ANG_E4, AISC_E5_RAT_LIM, AISC_B41A
    global NTC_LR_COMPRESION, NTC_LIMITES_FLEXION, NTC_KLR_COMPRESION, NTC_KLR_TENSION_REF, LIMITE_KLR
    try:
        OMEGA_T_FLU, OMEGA_T_FRA = v['AISC_OMEGA_TFLU'], v['AISC_OMEGA_TFRA']
        OMEGA_C, OMEGA_B, OMEGA_V = v['AISC_OMEGA_C'], v['AISC_OMEGA_B'], v['AISC_OMEGA_V']
        OMEGA_V_LAMINADA, KV_I, KV_ANGULO = v['AISC_OMEGA_V_LAM'], v['AISC_KV_I'], v['AISC_KV_ANG']
        CB_MAX_ANGULO = v['AISC_CB_MAX_ANG']
        AISC_LP_PATIN, AISC_LR_PATIN = v['AISC_LP_PATIN'], v['AISC_LR_PATIN']
        AISC_CV_LIM, AISC_HTW_LAM = v['AISC_CV_LIM'], v['AISC_HTW_LAM']
        AISC_LIM_ANG_E4, AISC_E5_RAT_LIM = v['AISC_LIM_ANG_E4'], v['AISC_E5_RAT_LIM']
        AISC_B41A = {'alma': (v['AISC_B41A_C1_ALMA'], v['AISC_B41A_C2_ALMA']),
                     'patin': (v['AISC_B41A_C1_PATA'], v['AISC_B41A_C2_PATA']),
                     'lr_pata': v['AISC_LR_PATA_B41A']}
        NTC_LR_COMPRESION = {'patin': v['NTC_LR_PATIN'], 'alma': v['NTC_LR_ALMA'], 'pata': v['NTC_LR_PATA']}
        NTC_LIMITES_FLEXION = {'patin': (v['NTC_LIM_PATIN_PL'], v['NTC_LIM_PATIN_P'], v['NTC_LIM_PATIN_R']),
                               'alma': (v['NTC_LIM_ALMA_PL'], v['NTC_LIM_ALMA_P'], v['NTC_LIM_ALMA_R']),
                               'pata': (None, v['NTC_LIM_PATA_P'], v['NTC_LIM_PATA_R'])}
        NTC_KLR_COMPRESION = v['NTC_KLR_COMP']
        NTC_KLR_TENSION_REF = {'principal': v['NTC_KLR_REF_PRINC'], 'contraventeo': v['NTC_KLR_REF_CONTR']}
        LIMITE_KLR = v['NTC_KLR_COMP']
    except KeyError as falta:
        raise ErrorAsd(f'falta el valor de norma {falta} en la hoja NORMA de la planilla')




class ErrorAsd(Exception):
    pass


def _forma(familia):
    return {'IR': 'I', 'CE': 'canal', 'LI': 'angulo'}.get(familia)


def _elementos_E7(p, forma, fy, E, fn):
    """Elementos esbeltos en compresion de I y canales (B4.1a / E7). Devuelve Ae y detalle."""
    Ag = p['A']
    sq = math.sqrt(E / fy)
    if forma == 'I':
        b_alma = p['H'] - 2.0 * p['t']
        b_pat = p['B'] / 2.0
        elems = [(b_alma, p['e'], NTC_LR_COMPRESION['alma'] * sq, AISC_B41A['alma'][0], AISC_B41A['alma'][1], 'alma'),
                 (b_pat, p['t'], NTC_LR_COMPRESION['patin'] * sq, AISC_B41A['patin'][0], AISC_B41A['patin'][1], 'patin'),
                 (b_pat, p['t'], NTC_LR_COMPRESION['patin'] * sq, AISC_B41A['patin'][0], AISC_B41A['patin'][1], 'patin')]
    else:
        b_alma = p['H'] - 2.0 * p['t']
        elems = [(b_alma, p['e'], NTC_LR_COMPRESION['alma'] * sq, AISC_B41A['alma'][0], AISC_B41A['alma'][1], 'alma'),
                 (p['B'], p['t'], NTC_LR_COMPRESION['patin'] * sq, AISC_B41A['patin'][0], AISC_B41A['patin'][1], 'patin'),
                 (p['B'], p['t'], NTC_LR_COMPRESION['patin'] * sq, AISC_B41A['patin'][0], AISC_B41A['patin'][1], 'patin')]
    Ae = Ag
    det = []
    for b, t, lr, c1, c2, nombre in elems:
        lam = b / t
        if lam <= lr:
            be = b
        else:
            fel = (c2 * lr / lam) ** 2 * fy                     # E7-5
            if fel >= fn:
                be = b
            else:
                r = math.sqrt(fel / fn)
                be = min(b * (1.0 - c1 * r) * r, b)            # E7-3
        Ae -= (b - be) * t
        det.append((nombre, round(lam, 2), round(lr, 2), round(be, 3)))
    return Ae, {'elementos': det}


def pn_compresion(p, familia, fy, E, G_, Kx, Ky, Lx, Ly, Lz, Kz=None):
    """Resistencia nominal a compresion de I y canales (E3, E4, E7). Devuelve (Pn, detalle)."""
    forma = _forma(familia)
    A = p['A']
    fex = math.pi ** 2 * E / (Kx * Lx / p['rx']) ** 2
    fey = math.pi ** 2 * E / (Ky * Ly / p['ry']) ** 2
    fes = {'Fex (E3)': fex, 'Fey (E3)': fey}
    if forma == 'I':
        fe_t = (math.pi ** 2 * E * p['Cw'] / (Kz * Lz) ** 2 + G_ * p['J']) / (p['Ix'] + p['Iy'])     # E4-2
        fes['Fe torsional (E4-2)'] = fe_t
    elif forma == 'canal':
        ro = p['ro']
        xo = math.sqrt(max(ro ** 2 - (p['Ix'] + p['Iy']) / A, 0.0))
        H = 1.0 - xo ** 2 / ro ** 2
        fez = (math.pi ** 2 * E * p['Cw'] / (Kz * Lz) ** 2 + G_ * p['J']) / (A * ro ** 2)              # E4-7
        fe_c = (fex + fez) / (2.0 * H) * (1.0 - math.sqrt(max(1.0 - 4.0 * fex * fez * H / (fex + fez) ** 2, 0.0)))  # E4-3 con Fex
        fes['Fe flexotorsional (E4-3, Fex)'] = fe_c
        fes['Fez (E4-7)'] = fez
    fe_min_nombre = min(fes, key=fes.get)
    fe = fes[fe_min_nombre]
    fn = (0.658 ** (fy / fe)) * fy if fy / fe <= 2.25 else 0.877 * fe            # E3-2 / E3-3
    Ae, det_e7 = _elementos_E7(p, forma, fy, E, fn)
    return fn * Ae, dict(Fe=fe, gobierna=fe_min_nombre, Fn=fn, Ae=Ae, E7=det_e7,
                         KLr_x=Kx * Lx / p['rx'], KLr_y=Ky * Ly / p['ry'])


def _ltb_I(p, fy, E, G_, Lb, Cb, canal=False):
    """Pandeo lateral torsional (F2.2 y F2-4..F2-8) con Mp = Fy Zx."""
    Sx, Zx = p['Sx'], p['Zx']
    Mp = fy * Zx
    ho = p['H'] - p['t']
    if canal:
        c = (ho / 2.0) * math.sqrt(p['Iy'] / p['Cw'])               # F2-8b
    else:
        c = 1.0                                                     # F2-8a
    rts = math.sqrt(math.sqrt(p['Iy'] * p['Cw']) / Sx)              # F2-7
    jc = p['J'] * c / (Sx * ho)
    lp = 1.76 * p['ry'] * math.sqrt(E / fy)                          # F2-5
    lr = 1.95 * rts * (E / (0.7 * fy)) * math.sqrt(jc + math.sqrt(jc ** 2 + 6.76 * (0.7 * fy / E) ** 2))  # F2-6
    if Lb <= lp:
        mn = Mp
    elif Lb <= lr:
        mn = min(Cb * (Mp - (Mp - 0.7 * fy * Sx) * (Lb - lp) / (lr - lp)), Mp)    # F2-2
    else:
        fcr = Cb * math.pi ** 2 * E / (Lb / rts) ** 2 * math.sqrt(1.0 + 0.078 * jc * (Lb / rts) ** 2)  # F2-4
        mn = min(fcr * Sx, Mp)                                                                       # F2-3
    return mn, dict(Lp=lp, Lr=lr, rts=rts, Mp=Mp)


def mn_fuerte(p, familia, fy, E, G_, Lb, Cb=None):
    """Momento nominal eje mayor de I y canales (F2, F3). Devuelve (Mn, detalle)."""
    canal = _forma(familia) == 'canal'
    ltb, det = _ltb_I(p, fy, E, G_, Lb, Cb, canal=canal)
    b = p['B'] if canal else p['B'] / 2.0
    lam_f = b / p['t']
    lpf, lrf = AISC_LP_PATIN * math.sqrt(E / fy), AISC_LR_PATIN * math.sqrt(E / fy)
    Mp = det['Mp']
    if lam_f <= lpf:
        lfb = Mp
    elif lam_f <= lrf:
        lfb = Mp - (Mp - 0.7 * fy * p['Sx']) * (lam_f - lpf) / (lrf - lpf)       # F3-1
    else:
        h = p['H'] - 2.0 * p['t']
        kc = min(max(4.0 / math.sqrt(h / p['e']), 0.35), 0.76)
        lfb = 0.9 * E * kc * p['Sx'] / lam_f ** 2                                  # F3-2
    det.update({'lam_f': lam_f, 'lpf': lpf, 'lrf': lrf, 'LTB': ltb, 'LFB': lfb})
    return min(ltb, lfb), det


def mn_debil(p, familia, fy, E):
    """Momento nominal eje menor de I y canales (F6)."""
    forma = _forma(familia)
    Mp = min(fy * p['Zy'], 1.6 * fy * p['Sy'])                                    # F6-1
    b = p['B'] / 2.0 if forma == 'I' else p['B']
    lam = b / p['t']
    lpf, lrf = AISC_LP_PATIN * math.sqrt(E / fy), AISC_LR_PATIN * math.sqrt(E / fy)
    My = fy * p['Sy']
    if lam <= lpf:
        mn = Mp
    elif lam <= lrf:
        mn = Mp - (Mp - 0.70 * fy * p['Sy']) * (lam - lpf) / (lrf - lpf)         # F6-2
    else:
        mn = min(0.70 * E / lam ** 2 * p['Sy'], Mp)                              # F6-3/4
    return mn, dict(lam_f=lam, Mp=Mp, My=My)


def _cv(ht, kv, E, fy):
    lim1 = AISC_CV_LIM * math.sqrt(kv * E / fy)
    if ht <= lim1:
        return 1.0
    return lim1 / ht


def vn_fuerte(p, familia, fy, E):
    """Cortante en el alma eje mayor de I y canales (G2)."""
    h = p['H'] - 2.0 * p['t']
    ht = h / p['e']
    aw = p['H'] * p['e']                                       # Aw = d tw
    if _forma(familia) == 'I' and ht <= AISC_HTW_LAM * math.sqrt(E / fy):
        cv, omega = 1.0, OMEGA_V_LAMINADA                      # G2-2
    else:
        cv, omega = _cv(ht, KV_I, E, fy), OMEGA_V              # G2-3/4
    return 0.6 * fy * aw * cv, omega, dict(h_tw=ht, Cv1=cv)


def vn_debil(p, familia, fy, E):
    """Cortante en el eje menor (G6): dos patines, Cv2 con kv = 1.2 (nota de usuario de G6)."""
    ratio = (p['B'] / (2.0 * p['t'])) if _forma(familia) == 'I' else (p['B'] / p['t'])
    cv2 = _cv(ratio, KV_ANGULO, E, fy)
    vn = 2.0 * 0.6 * fy * p['B'] * p['t'] * cv2
    return vn, OMEGA_V, dict(Cv2=cv2, ratio=ratio)


# ---------------------------------------------------------------- angulos de lados iguales (LI)
def propiedades_angulo(p):
    """Propiedades de un angulo de lados iguales: b = pata (H = B), t = espesor.
    Centroide, producto de inercia y ejes principales por geometria rectangular (sin acuerdos).
    Ix de catalogo (incluye acuerdos). Devuelve dict con ejes principales u (mayor) y v (menor)."""
    b, t, A = p['H'], p['t'], p['A']
    Ag = (2.0 * b - t) * t
    xc = (b * b * t / 2.0 + t * t * (b - t) / 2.0) / Ag                 # centroide desde el talon (x = y)
    Ixy = t * t * (2.0 * b * b - t * t) / 4.0 - Ag * xc * xc           # producto de inercia centroidal (< 0)
    I0 = p['Ix']                                                       # Ix = Iy
    Iu = I0 + abs(Ixy)                                                 # eje mayor principal (bisectriz del talon)
    Iv = I0 - abs(Ixy)                                                 # eje menor principal (rz)
    if Iv <= 0:
        raise ErrorAsd('angulo con inercia principal menor no positiva: revisar la base')
    c_u = b / math.sqrt(2.0)                                           # dedo a eje u (ambos lados)
    c_talon = math.sqrt(2.0) * xc                                      # talon a eje v
    c_dedo = (b + t - 2.0 * xc) / math.sqrt(2.0)                       # dedo a eje v
    return dict(b=b, t=t, rz=math.sqrt(Iv / A), ru=math.sqrt(Iu / A), Iu=Iu, Iv=Iv, Ixy=Ixy, xc=xc,
                Su=Iu / c_u, Sc_u=Iu / c_u, Sv=Iv / max(c_talon, c_dedo), Sc_v=Iv / c_dedo)


def _fn_E3(fy, E, lam):
    fe = math.pi ** 2 * E / lam ** 2
    fn = (0.658 ** (fy / fe)) * fy if fy / fe <= 2.25 else 0.877 * fe
    return fn, fe


def _slend_angulo(p, Lx, Ly, Kx, Ky, e5):
    """Esbeltez efectiva: z (menor, rz) por E5 o KL/rz, y u (mayor principal) por KL/ru."""
    Lmax = max(Lx, Ly)
    KL = max(Kx * Lx, Ky * Ly)
    if e5:
        rat = Lmax / p['rx']                                           # L/ra, ra = radio eje paralelo a la pata
        lam_z = (72.0 + 0.75 * rat) if rat <= AISC_E5_RAT_LIM else (32.0 + 1.25 * rat)     # E5-1 / E5-2
    else:
        lam_z = KL / p['rz']
    lam_u = KL / p['ru']
    return lam_z, lam_u


def _resistencias_angulo(p, fy, E, Lx, Ly, Lb, Kx, Ky, Cb, e5):
    sq = math.sqrt(E / fy)
    b, t, A = p['b'], p['t'], p['A']
    lam_z, lam_u = _slend_angulo(p, Lx, Ly, Kx, Ky, e5)
    fn_z, _ = _fn_E3(fy, E, lam_z)
    fn_u, _ = _fn_E3(fy, E, lam_u)
    fn = min(fn_z, fn_u)
    gob = 'Fe eje z (menor, E5)' if (fn_z <= fn_u and e5) else ('Fe eje z (menor, K L/rz)' if fn_z <= fn_u else 'Fe eje u (mayor)')
    # E7 patas esbeltas en compresion (B4.1a: 0.45 sqrt(E/Fy); c1 = 0.22, c2 = 1.49), ambas patas
    lam_leg = b / t
    lr_leg = AISC_B41A['lr_pata'] * sq
    if lam_leg <= lr_leg:
        be = b
    else:
        fel = (AISC_B41A['patin'][1] * lr_leg / lam_leg) ** 2 * fy                       # E7-5
        if fel >= fn:
            be = b
        else:
            r = math.sqrt(fel / fn)
            be = min(b * (1.0 - 0.22 * r) * r, b)                       # E7-3
    Ae = A - 2.0 * (b - be) * t
    pn_c = fn * Ae
    motivo = None
    if lam_leg > AISC_LIM_ANG_E4 * sq:
        # DECISION D14 (abierta): E4 flexotorsional de angulos no implementado; la barra queda NO REVISADO. Alternativa: implementarlo.
        motivo = 'b/t > 0.71 sqrt(E/Fy): requiere pandeo flexotorsional E4 (no implementado)'
    # F10 flexion sobre ejes principales
    Cb_u = min(Cb, CB_MAX_ANGULO)
    My_u, My_v = fy * p['Su'], fy * p['Sv']
    lp, lr = 0.54 * sq, 0.91 * sq

    def llb(Sc):
        if lam_leg <= lp:
            return None                                                  # compacta: no aplica
        if lam_leg <= lr:
            return fy * Sc * (2.43 - 1.72 * lam_leg / sq)                # F10-6 ((b/t) sqrt(Fy/E) = lam/sq)
        return AISC_LIM_ANG_E4 * E / lam_leg ** 2 * Sc                              # F10-7 / F10-8
    Mcr = 9.0 * E * A * p['rz'] * t * Cb_u / (8.0 * Lb)                  # F10-4 con beta_w = 0
    ratio = My_u / Mcr
    if ratio <= 1.0:
        mn_ltb = min((1.92 - 1.17 * ratio) * My_u, 1.5 * My_u)           # F10-2
    else:
        mn_ltb = (0.92 - 0.17 / ratio) * Mcr                             # F10-3
    lista_u = [1.5 * My_u, mn_ltb]
    lu = llb(p['Sc_u'])
    if lu is not None:
        lista_u.append(lu)
    lista_v = [1.5 * My_v]
    lv = llb(p['Sc_v'])
    if lv is not None:
        lista_v.append(lv)
    Mn_u, Mn_v = min(lista_u), min(lista_v)
    # G3 cortante de una pata
    cv2 = _cv(lam_leg, KV_ANGULO, E, fy)
    Va = 0.6 * fy * b * t * cv2 / OMEGA_V
    return dict(Pa_c=None if motivo else pn_c / OMEGA_C, Ma_x=Mn_u / OMEGA_B, Ma_y=Mn_v / OMEGA_B,
                Va_x=Va, Va_y=Va, klr=max(lam_z, lam_u), motivo=motivo,
                KLr_fuerte=lam_u, KLr_debil=lam_z,
                detalle_c=dict(gobierna=gob, Fn=fn, Ae=Ae, lam_z=lam_z, lam_u=lam_u, be=be),
                detalle_x=dict(Mn=Mn_u, Mcr=Mcr, LTB=mn_ltb, My=My_u, lam_leg=lam_leg, lp=lp, lr=lr),
                detalle_y=dict(Mn=Mn_v, My=My_v),
                detalle_vx=dict(Cv2=cv2), detalle_vy=dict(Cv2=cv2))


def _utilizacion_angulo(res, Pr_t, Pr_c, Mr_x, Mr_y, Vr_x, Vr_y):
    """LI: H2-1 con el momento resultante sobre cada eje principal (cubre cualquier orientacion)."""
    u = {}
    mres = math.hypot(Mr_x, Mr_y)
    u['T traccion'] = Pr_t / res['Pa_t'] if Pr_t > 0 else 0.0
    u['C compresion'] = Pr_c / res['Pa_c'] if Pr_c > 0 else 0.0
    u['F flexion eje mayor'] = mres / res['Ma_x'] if mres > 0 else 0.0      # eje principal u
    u['F flexion eje menor'] = mres / res['Ma_y'] if mres > 0 else 0.0      # eje principal v
    u['V cortante eje mayor'] = Vr_x / res['Va_x'] if Vr_x > 0 else 0.0
    u['V cortante eje menor'] = Vr_y / res['Va_y'] if Vr_y > 0 else 0.0
    if Pr_c > 0:
        pr = Pr_c / res['Pa_c']
    elif Pr_t > 0:
        pr = Pr_t / res['Pa_t']
    else:
        pr = 0.0
    if pr > 0 or mres > 0:
        u['H2 angulo (H2-1)'] = pr + mres / res['Ma_x'] + mres / res['Ma_y']
    return u


def resistencias_asd(p, familia, fy, fu, E, nu, Lx, Ly, Lb, Kx, Ky, Lz, Cb=None, e5=False, U=1.0):
    """Capacidades ASD (admisibles) de la barra: Pa tension, Pa compresion, Ma eje mayor y menor, Va."""
    G_ = E / (2.0 * (1.0 + nu))
    out = {'angulo': familia == 'LI', 'motivo': None}
    pa_flu = fy * p['A'] / OMEGA_T_FLU
    out['Pa_t_fluencia'] = pa_flu
    out['U'] = U                                                                     # D3: Ae = U Ag (sin agujeros)
    out['Pa_t_fractura'] = None if fu is None else fu * p['A'] * U / OMEGA_T_FRA
    out['Pa_t'] = pa_flu if fu is None else min(pa_flu, fu * p['A'] * U / OMEGA_T_FRA)
    if familia == 'LI':
        out.update(_resistencias_angulo(p, fy, E, Lx, Ly, Lb, Kx, Ky, Cb, e5))
        return out
    # DECISION D4 (abierta): Kz elegido en PARAMETROS (1.0 o 0.5).
    pn_c, det_c = pn_compresion(p, familia, fy, E, G_, Kx, Ky, Lx, Ly, Lz, Kz=KZ_TORSION)
    out['Pa_c'] = pn_c / OMEGA_C
    out['detalle_c'] = det_c
    mn_x, det_x = mn_fuerte(p, familia, fy, E, G_, Lb, Cb)
    out['Ma_x'] = mn_x / OMEGA_B
    out['detalle_x'] = det_x
    mn_y, det_y = mn_debil(p, familia, fy, E)
    out['Ma_y'] = mn_y / OMEGA_B
    out['detalle_y'] = det_y
    vn_x, om_x, det_vx = vn_fuerte(p, familia, fy, E)
    out['Va_x'] = vn_x / om_x
    out['detalle_vx'] = det_vx
    vn_y, om_y, det_vy = vn_debil(p, familia, fy, E)
    out['Va_y'] = vn_y / om_y
    out['detalle_vy'] = det_vy
    out['KLr_fuerte'] = Kx * Lx / p['rx']
    out['KLr_debil'] = Ky * Ly / p['ry']
    out['klr'] = max(out['KLr_fuerte'], out['KLr_debil'])
    return out


def utilizacion_asd(res, Pr_t, Pr_c, Mr_x, Mr_y, Vr_x, Vr_y):
    """Utilizaciones ASD (<= 1 cumple): tension, compresion, flexion eje mayor y menor, cortante, H1 o H2."""
    if res.get('angulo'):
        return _utilizacion_angulo(res, Pr_t, Pr_c, Mr_x, Mr_y, Vr_x, Vr_y)
    u = {}
    u['T traccion'] = Pr_t / res['Pa_t'] if Pr_t > 0 else 0.0
    u['C compresion'] = Pr_c / res['Pa_c'] if Pr_c > 0 else 0.0
    u['F flexion eje mayor'] = Mr_x / res['Ma_x'] if Mr_x > 0 else 0.0
    u['F flexion eje menor'] = Mr_y / res['Ma_y'] if Mr_y > 0 else 0.0
    u['V cortante eje mayor'] = Vr_x / res['Va_x'] if Vr_x > 0 else 0.0
    u['V cortante eje menor'] = Vr_y / res['Va_y'] if Vr_y > 0 else 0.0
    mx = Mr_x / res['Ma_x']
    my = Mr_y / res['Ma_y']
    if Pr_c > 0:                                                              # H1-1a/b, compresion
        pc = res['Pa_c']
        ratio = Pr_c / pc
        u['H1 flexocompresion'] = (ratio + 8.0 / 9.0 * (mx + my)) if ratio >= 0.2 else (ratio / 2.0 + (mx + my))
    elif Pr_t > 0 and (mx > 0 or my > 0):                                     # H1-1a/b con Pc = Pt admisible
        pc = res['Pa_t']
        ratio = Pr_t / pc
        u['H1 flexotension'] = (ratio + 8.0 / 9.0 * (mx + my)) if ratio >= 0.2 else (ratio / 2.0 + (mx + my))
    return u


# NTC-Acero CDMX (Gaceta Oficial 7-jul-2020). El diseno de resistencia es AISC 360-22 (ASD); las esbelteces local
# y global se verifican con la NTC (requisito del proyecto en Mexico).
# (los limites NTC-Acero se cargan con cargar_norma(): tablas 3.2.1, 3.2.2 y 2.3.2)


def esbeltez_local(p, familia, fy, E, compresion):
    """Esbeltez local por elemento segun NTC: lambda / lambda_r (<= 1 cumple). Compresion: Tabla 3.2.1;
    flexion: Tabla 3.2.2 (lambda_r = limite de seccion tipo 3). Devuelve (FU, {elemento: (lambda, lambda_r)})."""
    sq = math.sqrt(E / fy)
    if familia == 'LI':
        lams = {'pata': p['H'] / p['t']}
    else:
        b_pat = p['B'] / 2.0 if familia == 'IR' else p['B']
        lams = {'patin': b_pat / p['t'], 'alma': (p['H'] - 2.0 * p['t']) / p['e']}
    elementos = {}
    for n, lam in lams.items():
        lr_norm = NTC_LR_COMPRESION[n] if compresion else NTC_LIMITES_FLEXION[n][2]
        elementos[n] = (lam, lr_norm * sq)
    fu = {n: lam / lr for n, (lam, lr) in elementos.items()}
    return fu, elementos


def tipo_seccion_flexion(p, familia, fy, E):
    """Tipo de seccion (NTC 3.2.1.2, Tabla 3.2.2): 1, 2, 3 o 4 segun el elemento mas esbelto."""
    sq = math.sqrt(E / fy)
    _, det = esbeltez_local(p, familia, fy, E, compresion=False)
    tipo = 1
    for n, (lam, _) in det.items():
        lpl, lp, lr = NTC_LIMITES_FLEXION[n]
        if lpl is not None and lam <= lpl * sq:
            t = 1
        elif lam <= lp * sq:
            t = 2
        elif lam <= lr * sq:
            t = 3
        else:
            t = 4
        tipo = max(tipo, t)
    return tipo


def clasificacion_compresion(p, familia, fy, E):
    """NTC 3.2.1.1 (Tabla 3.2.1): seccion no-esbelta si todos sus elementos cumplen lambda <= lambda_r."""
    fu, _ = esbeltez_local(p, familia, fy, E, compresion=True)
    return 'no-esbelta' if max(fu.values()) <= 1.0 else 'esbelta'


def _num(v, defecto=None):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return defecto
    try:
        return float(v)
    except (TypeError, ValueError):
        return defecto


E5_COLS = ['E5 UNA PATA', 'E5 UNION SOLDADA O 2 PERNOS', 'E5 SIN CARGA INTERMEDIA', 'E5 INDIVIDUAL O ALMA DE ARMADURA']


def _texto(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ''
    return str(v).strip().upper()


def e5_cumple(r):
    """E5(a): el angulo se trata con E5 solo si LONGITUDES marca SI en las cuatro condiciones de E5 (1 a 4).
    Sin marcar (vacio o NO) se usa K L/rz y H2, como exige AISC E5 cuando no se cumplen."""
    return r is not None and all(_texto(r.get(c)) == 'SI' for c in E5_COLS)


def factor_u_angulo(xc, l_cm, conexion):
    """Factor de rezago U para tension (AISC D3, Tabla D3.1). Ambas patas conectadas: U = 1.0 (caso 1).
    Una pata: U = 1 - xc/l (caso 2; en el caso 8 la tabla permite usar el valor mayor, que es este)."""
    if 'DOS' in (conexion or '').upper():
        return 1.0
    return max(0.0, min(1.0, 1.0 - xc / l_cm))


def _props_asd(nombre, familia):
    """Propiedades para ASD desde la base Gerdau. No se estima ninguna propiedad: lo que falta queda NO REVISADO."""
    p = G.obtener_perfil(nombre)
    if p is None:
        return None, 'perfil no existe en la base Gerdau'
    estimados = []
    if familia == 'LI':
        req = ['H', 't', 'A', 'Ix', 'rx']
    else:
        req = ['H', 'B', 'e', 't', 'A', 'Ix', 'Iy', 'Sx', 'Sy', 'rx', 'ry', 'J', 'Zx', 'Zy']
        if familia in ('IR', 'CE'):
            req.append('Cw')
        if familia == 'CE':
            req.append('ro')
    # DECISION D16 (abierta): sin estimaciones; si la base Gerdau no trae una propiedad, la barra queda NO REVISADO (alternativa: error).
    # Sin estimaciones: si la base Gerdau no trae una propiedad, la barra queda NO REVISADO (se reporta).
    falta = [k for k in req if p.get(k) is None]
    if falta:
        return None, 'NO REVISADO: faltan datos ' + ', '.join(falta)
    if familia == 'LI':
        p.update(propiedades_angulo(p))
    p['_estimados'] = estimados
    return p, ''


def _demanda_fila(fila):
    """Demandas ASD de una fila de BARRAS (kgf, kgf·cm)."""
    N_I, N_J = _num(fila['N I (kgf)'], 0.0), _num(fila['N J (kgf)'], 0.0)
    return dict(Pr_c=max(N_I, -N_J, 0.0), Pr_t=max(-N_I, N_J, 0.0),
                # H-01: el momento de diseno incluye el maximo en el tramo (no solo los extremos)
                Mr_x=max(abs(_num(fila['Mz I (kgf·m)'], 0.0)), abs(_num(fila['Mz J (kgf·m)'], 0.0)),
                         abs(fila['MZ MAX EN EL TRAMO (kgf·m)'])) * 100.0,
                Mr_y=max(abs(_num(fila['My I (kgf·m)'], 0.0)), abs(_num(fila['My J (kgf·m)'], 0.0)),
                         abs(fila['MY MAX EN EL TRAMO (kgf·m)'])) * 100.0,
                Vr_x=max(abs(_num(fila['Vy I (kgf)'], 0.0)), abs(_num(fila['Vy J (kgf)'], 0.0))),
                Vr_y=max(abs(_num(fila['Vz I (kgf)'], 0.0)), abs(_num(fila['Vz J (kgf)'], 0.0))))


# ---------------------------------------------------------------- planilla -> diseno ASD (IR, CE, LI)
GRUPOS_ELEMENTO = ['COLUMNA', 'VIGA', 'ARRIOSTRE', 'DIAGONAL']
COMPRESION_GRUPOS = ('COLUMNA', 'ARRIOSTRE', 'DIAGONAL')
FAMILIAS_ASD = ('IR', 'CE', 'LI')
FAMILIA_ORDEN = ['IR', 'CE', 'LI']
CHEQUEOS_DEMANDA = ['T traccion', 'C compresion', 'F flexion eje mayor', 'F flexion eje menor',
                    'V cortante eje mayor', 'V cortante eje menor', 'H1 flexocompresion', 'H1 flexotension',
                    'H2 angulo (H2-1)']
INTERACCION = ('H1 flexocompresion', 'H1 flexotension', 'H2 angulo (H2-1)')
CHEQUEO_EL = 'EL esbeltez local (B4.1)'
CHEQUEO_EG = 'EG KL/r <= 200 (2.3.2)'
CHEQUEO_D60 = 'D columna ductil KL/r <= 60 (12.1.3.1)'
CHEQUEO_D12 = 'D tabla 12.1.2 ancho/grueso'
CHEQUEOS_ESBELTEZ = [CHEQUEO_EL, CHEQUEO_EG, CHEQUEO_D60, CHEQUEO_D12]
CHEQUEOS_ASD = CHEQUEOS_DEMANDA + CHEQUEOS_ESBELTEZ
COLS_RESULTADOS = ['ID', 'PERFIL', 'MATERIAL', 'GRUPO', 'CASO QUE GOBIERNA', 'FU TRACCION', 'FU COMPRESION',
                   'FU FLEXION EJE MAYOR', 'FU FLEXION EJE MENOR', 'FU CORTANTE EJE MAYOR', 'FU CORTANTE EJE MENOR',
                   'FU INTERACCION (H1/H2)', 'FU ESBELTEZ LOCAL (B4.1)', 'FU ESBELTEZ GLOBAL (KL/r<=200)',
                   'FU DUCTILIDAD (12.1.2, 12.1.3.1)', 'FU MAXIMO', 'KL/r EJE FUERTE', 'KL/r EJE DEBIL',
                   'ESTADO', 'NOTAS']


def _valores_designacion(nombre):
    """Numeros de la designacion comercial: 'IR 6 × 12' -> [6, 12]; 'LI 3 1/2 × 3/8' -> [3.5, 0.375]."""
    partes = [x.strip() for x in seccion_de(nombre).replace('x', '×').split('×')]
    vals = []
    for parte in partes:
        m = re.fullmatch(r'(\d+)\s+(\d+)/(\d+)', parte)
        if m:
            vals.append(int(m[1]) + int(m[2]) / int(m[3]))
            continue
        m = re.fullmatch(r'(\d+)/(\d+)', parte)
        if m:
            vals.append(int(m[1]) / int(m[2]))
            continue
        try:
            vals.append(float(parte))
        except ValueError:
            vals.append(math.inf)
    return vals + [math.inf] * (2 - len(vals))


def clave_orden(nombre):
    """Orden de las listas: tipo (IR, CE, LI), luego la designacion comercial (peralte o ala, luego peso o espesor)
    y la masa como desempate."""
    p = G.PERFILES[nombre]
    a, b = _valores_designacion(nombre)[:2]
    masa = p['masa_kg_m'] if p['masa_kg_m'] is not None else math.inf
    return (FAMILIA_ORDEN.index(p['familia']), a, b, masa, nombre)


def seccion_de(nombre):
    """Seccion sin el tipo: 'IR 10 × 30' -> '10 × 30'."""
    import re
    return re.sub(r'^(IR|CE|LI)\s*ᴬ?\s*', '', nombre).strip()


def _ductilidad(p, familia, fy, E, grupo, nivel):
    """Tabla 12.1.2 (NTC): I y canales (DN); angulos sencillos: alas (no atiesadas), lambda = b/t <= 0.30 (alta) o
    0.38 (media) sqrt(E/Fy)."""
    import diseno_ntc as DN
    if familia == 'LI':
        if nivel not in ('ALTA', 'MEDIA'):
            return None
        lim = (0.30 if nivel == 'ALTA' else 0.38) * math.sqrt(E / fy)
        return {'U': (p['H'] / p['t']) / lim, 'lambda': p['H'] / p['t'], 'limite': lim}
    forma = {'IR': 'I', 'CE': 'canal'}.get(familia)
    return DN.ductilidad_12_1_2(p, fy, E, forma, grupo, nivel) if forma else None


def _chequear(p, familia, fy, fu, E, nu, Lx, Ly, Lb, kx, ky, grupo, nivel, demandas_list, cb=None,
              e5=False, u_t=1.0):
    """Utilizaciones ASD por demanda (una fila por combinacion) y verificaciones de esbeltez de la barra.
    Devuelve dict: res, klr, dd, el (FU local por elemento), el_det, const (FU que no dependen de la demanda),
    filas (una por demanda) y motivo (si no se puede verificar)."""
    res = resistencias_asd(p, familia, fy, fu, E, nu, Lx, Ly, Lb, kx, ky, max(Lx, Ly), Cb=cb, e5=e5, U=u_t)
    klr = res['klr']
    compr = grupo in COMPRESION_GRUPOS
    fu_el, el_det = esbeltez_local(p, familia, fy, E, compresion=compr)
    const = {CHEQUEO_EL: max(fu_el.values())}
    if compr:
        const[CHEQUEO_EG] = klr / LIMITE_KLR
    dd = _ductilidad(p, familia, fy, E, grupo, nivel)
    if grupo == 'COLUMNA' and nivel in ('ALTA', 'MEDIA'):
        const[CHEQUEO_D60] = klr / 60.0
    if dd is not None and dd.get('U') is not None:
        const[CHEQUEO_D12] = dd['U']
    out = dict(res=res, klr=klr, dd=dd, el=fu_el, el_det=el_det, const=const, filas=[], motivo=res.get('motivo'))
    if res.get('motivo') and any(d['Pr_c'] > 0 for d in demandas_list):
        return out
    for d in demandas_list:
        u = utilizacion_asd(res, d['Pr_t'], d['Pr_c'], d['Mr_x'], d['Mr_y'], d['Vr_x'], d['Vr_y'])
        u.update(const)
        out['filas'].append(u)
    return out


def _resumen_fu(ev, pares):
    """FU por verificacion (maximo sobre combinaciones) y caso que gobierna. pares = [(fila, caso)]."""
    mx = {}
    for c in CHEQUEOS_DEMANDA:
        vals = [(u[c], caso) for u, caso in pares if u.get(c) is not None]
        if vals:
            mx[c] = max(vals, key=lambda t: t[0])

    def val(c):
        return mx[c][0] if c in mx else None
    inter = [mx[c] for c in INTERACCION if c in mx]
    cands = [mx[c] for c in CHEQUEOS_DEMANDA if c in mx]
    for c, v in ev['const'].items():
        nombre = '(esbeltez local)' if c == CHEQUEO_EL else ('(esbeltez global)' if c == CHEQUEO_EG else '(ductilidad)')
        cands.append((v, nombre))
    fu_max, caso_gob = max(cands, key=lambda t: t[0]) if cands else (None, '')
    duct = [ev['const'][c] for c in (CHEQUEO_D60, CHEQUEO_D12) if c in ev['const']]
    return {'CASO QUE GOBIERNA': caso_gob,
            'FU TRACCION': val('T traccion'), 'FU COMPRESION': val('C compresion'),
            'FU FLEXION EJE MAYOR': val('F flexion eje mayor'), 'FU FLEXION EJE MENOR': val('F flexion eje menor'),
            'FU CORTANTE EJE MAYOR': val('V cortante eje mayor'), 'FU CORTANTE EJE MENOR': val('V cortante eje menor'),
            'FU INTERACCION (H1/H2)': max(inter, key=lambda t: t[0])[0] if inter else None,
            'FU ESBELTEZ LOCAL (B4.1)': ev['const'].get(CHEQUEO_EL),
            'FU ESBELTEZ GLOBAL (KL/r<=200)': ev['const'].get(CHEQUEO_EG),
            'FU DUCTILIDAD (12.1.2, 12.1.3.1)': max(duct) if duct else None,
            'FU MAXIMO': fu_max}


def _preparar_entradas(materiales_filas, longitudes_df, demandas):
    """Materiales por nombre, longitudes por ID de barra y combinaciones de servicio."""
    mat = {str(f[0]).strip(): dict(fy=_num(f[2]), fu=_num(f[3]), E=_num(f[4]), nu=_num(f[5])) for f in materiales_filas}
    lon = {}
    for _, r in longitudes_df.iterrows():
        id_ = _num(r.get('ID'))
        if id_ is not None:
            lon[int(id_)] = r
    comb = demandas[demandas['TIPO'] == 'COMBINACION']
    return mat, lon, comb


def _entrada_barra(dib, i, id_barra, lon, mat):
    """Datos de entrada ASD de la barra i: longitud, K, Cb, ductilidad y material. Lo no dado se supone y se anota."""
    b = dib.barras[i]
    id_ = id_barra.get(i, i)
    L = float(np.linalg.norm(np.array(dib.nodos[b['n2']]) - np.array(dib.nodos[b['n1']]))) * 100.0
    m = mat.get(str(b.get('material') or '').strip())
    r = lon.get(id_)
    supuestos = []

    def campo(nombre):
        return _num(r.get(nombre)) if r is not None else None
    lx, ly, lb = campo('LX (m)'), campo('LY (m)'), campo('LB (m)')
    kx, ky = campo('KX'), campo('KY')
    cb = _num(r.get('CB')) if r is not None else None
    barra = f'barra {id_}: '
    lx = _req(lx, 'LX (m)', barra)
    ly = _req(ly, 'LY (m)', barra)
    lb = _req(lb, 'LB (m)', barra)
    kx = _req(kx, 'KX', barra)
    ky = _req(ky, 'KY', barra)
    cb = _req(cb, 'CB', barra)
    duct_raw = r.get('DUCTILIDAD') if r is not None else None
    nivel = None
    if duct_raw is not None and not (isinstance(duct_raw, float) and math.isnan(duct_raw)) and str(duct_raw).strip():
        nivel = str(duct_raw).strip().upper()
    lcon = campo('LI LONGITUD CONEXION (m)')
    conexion_raw = _texto(r.get('LI CONEXION')) if r is not None else ''
    sup_li = []
    familia_b = (G.obtener_perfil(b['perfil']) or {}).get('familia')
    if familia_b == 'LI':
        if not conexion_raw:
            raise ErrorAsd(f'{barra}falta LI CONEXION en LONGITUDES (angulo: UNA PATA, DOS PATAS o SOLDADA)')
        if lcon is None:
            raise ErrorAsd(f'{barra}falta LI LONGITUD CONEXION (m) en LONGITUDES (angulo)')
    return dict(m=m, L=L, lx=lx, ly=ly, lb=lb, kx=kx, ky=ky, cb=cb, nivel=nivel, supuestos=supuestos,
                e5=e5_cumple(r), conexion=conexion_raw or None,
                l_li=lcon * 100.0 if lcon is not None else None, sup_li=sup_li)


def perfil_por_grupo(dib):
    """Perfil de cada grupo. Cada grupo usa una sola seccion: si sus barras tienen perfiles distintos, ErrorAsd
    (no se elige uno en silencio). Devuelve {grupo: perfil} para los grupos con barras."""
    import collections
    perfiles, problemas = {}, []
    for g in GRUPOS_ELEMENTO:
        c = collections.Counter(b['perfil'] for b in dib.barras if b['elemento'] == g)
        if len(c) == 1:
            perfiles[g] = next(iter(c))
        elif len(c) > 1:
            detalle = ', '.join(f'{n} ({k} barras)' for n, k in c.most_common())
            problemas.append(f'{g}: {detalle}')
    if problemas:
        raise ErrorAsd('Cada grupo debe tener una sola seccion. Corrija la columna PERFIL de BARRAS en: '
                       + '; '.join(problemas))
    return perfiles


COLS_MATRIZ = ['CLAVE', 'ID', 'PERFIL', 'ELEMENTO DISENO', 'FU MAXIMO', 'FU DEMANDA', 'FU ESBELTEZ LOCAL (B4.1)',
               'FU ESBELTEZ GLOBAL (KL/r<=200)', 'FU DUCTILIDAD (12.1.2, 12.1.3.1)', 'CASO QUE GOBIERNA', 'ESTADO']
FU_DEMANDA_CLAVES = ['FU TRACCION', 'FU COMPRESION', 'FU FLEXION EJE MAYOR', 'FU FLEXION EJE MENOR',
                     'FU CORTANTE EJE MAYOR', 'FU CORTANTE EJE MENOR', 'FU INTERACCION (H1/H2)']


def matriz_fu_por_perfil(dib, materiales_filas, longitudes_df, demandas, id_barra, familias=FAMILIAS_ASD):
    """FU ASD de cada barra con cada perfil del catalogo (IR, CE, LI), con sus combinaciones, longitudes, K y el
    grupo de la barra. Alimenta la hoja FU_MATRIZ: al cambiar el perfil de un grupo, Excel busca estos valores."""
    mat, lon, comb = _preparar_entradas(materiales_filas, longitudes_df, demandas)
    catalogo = sorted([n for n, d in G.PERFILES.items() if d['familia'] in familias], key=clave_orden)
    props = {n: _props_asd(n, G.PERFILES[n]['familia']) for n in catalogo}
    filas = []
    for i, b in enumerate(dib.barras):
        id_ = id_barra.get(i, i)
        e = _entrada_barra(dib, i, id_barra, lon, mat)
        m = e['m']
        f = comb[comb['BARRA'] == id_]
        demandas_list = [_demanda_fila(x) for _, x in f.iterrows()]
        casos = [x['CASO'] for _, x in f.iterrows()]
        pares_base = list(zip(demandas_list, casos))
        for nombre in catalogo:
            p, falta = props[nombre]
            fam = G.PERFILES[nombre]['familia']
            base = [f'{int(id_)}|{nombre}', int(id_), nombre, b['elemento']]
            if p is None or m is None or m['fy'] is None or m['E'] is None or m['nu'] is None:
                motivo = falta if p is None else 'material sin fy, E o nu'
                filas.append(base + [motivo] + ['NO REVISADO'] * 6)
                continue
            if fam == 'LI' and (e['l_li'] is None or e['conexion'] is None):
                # DECISION D20 (abierta): candidatos LI sin datos de conexion quedan NO REVISADO (alternativa: error).
                # candidato angulo: sin LI CONEXION y LI LONGITUD CONEXION en LONGITUDES no se evalua (no se supone)
                filas.append(base + ['falta LI CONEXION o LI LONGITUD CONEXION en LONGITUDES'] + ['NO REVISADO'] * 6)
                continue
            ev = _chequear(p, fam, m['fy'], m['fu'], m['E'], m['nu'], e['lx'] * 100.0, e['ly'] * 100.0,
                           e['lb'] * 100.0, e['kx'], e['ky'], b['elemento'], e['nivel'], demandas_list, cb=e['cb'],
                           e5=(fam == 'LI' and e['e5']),
                           u_t=(factor_u_angulo(p['xc'], e['l_li'], e['conexion']) if fam == 'LI' else 1.0))
            if ev['motivo'] and any(d['Pr_c'] > 0 for d in demandas_list):
                filas.append(base + ['NO REVISADO'] * 6 + ['NO REVISADO'])
                continue
            if not demandas_list:
                el, eg = ev['const'][CHEQUEO_EL], ev['const'].get(CHEQUEO_EG)
                filas.append(base + ['SIN COMBINACIONES', '—', round(el, 3),
                                     round(eg, 3) if eg is not None else '—', '—', '—', 'SIN COMBINACIONES'])
                continue
            fu = _resumen_fu(ev, list(zip(ev['filas'], casos)))
            dem = [fu[c] for c in FU_DEMANDA_CLAVES if fu.get(c) is not None]
            eg = fu['FU ESBELTEZ GLOBAL (KL/r<=200)']
            duct = fu['FU DUCTILIDAD (12.1.2, 12.1.3.1)']
            filas.append(base + [round(fu['FU MAXIMO'], 4), round(max(dem), 4) if dem else '—',
                                 round(fu['FU ESBELTEZ LOCAL (B4.1)'], 4),
                                 round(eg, 4) if eg is not None else '—',
                                 round(duct, 4) if duct is not None else '—',
                                 fu['CASO QUE GOBIERNA'],
                                 'CUMPLE' if fu['FU MAXIMO'] <= 1.0 else 'NO CUMPLE'])
    return pd.DataFrame(filas, columns=COLS_MATRIZ)


def diseno_asd_desde_planilla(dib, materiales_filas, longitudes_df, demandas, id_barra, ruta_salida):
    """Diseno ASD (AISC 360-22) de las barras IR, CE y LI con las combinaciones de servicio (COMBINACIONES).
    RESULTADOS: FU por verificacion (demanda/capacidad, <= 1 cumple), esbeltez local (B4.1) y global (KL/r <= 200).
    Las barras CS (macizas) y otras familias quedan FUERA DE ALCANCE. Devuelve (capacidades, resultados, detalle)."""
    if materiales_filas is None:
        raise ErrorAsd('la planilla no tiene la hoja MATERIALES.')
    mat = {str(f[0]).strip(): dict(fy=_num(f[2]), fu=_num(f[3]), E=_num(f[4]), nu=_num(f[5])) for f in materiales_filas}
    lon = {}
    for _, r in longitudes_df.iterrows():
        id_ = _num(r.get('ID'))
        if id_ is not None:
            lon[int(id_)] = r
    comb = demandas[demandas['TIPO'] == 'COMBINACION']
    if comb.empty:
        raise ErrorAsd('no hay combinaciones de carga: defina COMBINACIONES (cargas de servicio, ASD).')
    caps, res_filas, det_filas = [], [], []
    for i, b in enumerate(dib.barras):
        id_ = id_barra.get(i, i)
        perfil, grupo = b['perfil'], b['elemento']
        fam = G.obtener_perfil(perfil)
        if fam is None:
            motivo = 'perfil no existe en la base Gerdau'
            caps.append({'ID': id_, 'PERFIL': perfil, 'NOTA': motivo})
            res_filas.append(dict(ID=id_, PERFIL=perfil, MATERIAL=b.get('material'), GRUPO=grupo,
                                  ESTADO='NO REVISADO', NOTAS=motivo))
            continue
        familia = fam['familia']
        if familia not in FAMILIAS_ASD:
            motivo = f'fuera del alcance del diseno ({familia}): solo IR, CE y LI'
            caps.append({'ID': id_, 'PERFIL': perfil, 'FAMILIA': familia, 'NOTA': motivo})
            res_filas.append(dict(ID=id_, PERFIL=perfil, MATERIAL=b.get('material'), GRUPO=grupo,
                                  ESTADO='FUERA DE ALCANCE', NOTAS=motivo))
            continue
        e = _entrada_barra(dib, i, id_barra, lon, mat)
        m, L, lx, ly, lb, kx, ky, cb, nivel, supuestos = (e['m'], e['L'], e['lx'], e['ly'], e['lb'], e['kx'],
                                                          e['ky'], e['cb'], e['nivel'], e['supuestos'])
        p, falta = _props_asd(perfil, familia)
        if p is None or m is None or m['fy'] is None or m['E'] is None or m['nu'] is None:
            motivo = falta if p is None else 'material sin fy, E o nu en MATERIALES'
            caps.append({'ID': id_, 'PERFIL': perfil, 'NOTA': motivo})
            res_filas.append(dict(ID=id_, PERFIL=perfil, MATERIAL=b.get('material'), GRUPO=grupo,
                                  ESTADO='NO REVISADO', NOTAS=motivo))
            continue
        estimados = p.get('_estimados', [])
        es_li = familia == 'LI'
        e5_b = es_li and e['e5']
        u_b = factor_u_angulo(p['xc'], e['l_li'], e['conexion']) if es_li else 1.0
        if es_li:
            supuestos = supuestos + e['sup_li']
        filas_comb = comb[comb['BARRA'] == id_]
        demandas_list = [_demanda_fila(f) for _, f in filas_comb.iterrows()]
        casos = [f['CASO'] for _, f in filas_comb.iterrows()]
        ev = _chequear(p, familia, m['fy'], m['fu'], m['E'], m['nu'], lx * 100.0, ly * 100.0, lb * 100.0,
                       kx, ky, grupo, nivel, demandas_list, cb=cb, e5=e5_b, u_t=u_b)
        res = ev['res']
        if ev['motivo'] and any(d['Pr_c'] > 0 for d in demandas_list):
            motivo = 'NO REVISADO: ' + res['motivo']
            caps.append({'ID': id_, 'PERFIL': perfil, 'FAMILIA': familia, 'NOTA': motivo})
            res_filas.append(dict(ID=id_, PERFIL=perfil, MATERIAL=b.get('material'), GRUPO=grupo,
                                  ESTADO='NO REVISADO', NOTAS=motivo))
            continue
        notas = []
        if familia == 'LI':
            notas.append('LI: ejes principales (u mayor, v menor); H2 con momento resultante; cortante de una pata (G3)')
            notas.append('E5(a) verificado en LONGITUDES: se usa Lc/rz de E5' if e5_b
                         else 'E5 no verificado (LONGITUDES): K L/rz y H2')
            notas.append(f'tension: U = {u_b:.3f} (D3)' if not e['conexion'] == 'DOS PATAS' else 'tension: U = 1.0 (ambas patas)')
        if grupo not in COMPRESION_GRUPOS:
            notas.append('sin verificacion KL/r (elemento sin compresion)')
        cap = {'ID': id_, 'PERFIL': perfil, 'FAMILIA': familia, 'MATERIAL': b.get('material'), 'GRUPO': grupo,
               'L (m)': L / 100.0, 'LX (m)': lx, 'LY (m)': ly, 'LB (m)': lb, 'KX': kx, 'KY': ky, 'CB': cb,
               'DUCTILIDAD': nivel or '(informativo)',
               'Pa traccion (kgf)': res['Pa_t'], 'Pa compresion (kgf)': res['Pa_c'],
               'Ma eje mayor (kgf·cm)': res['Ma_x'], 'Ma eje menor (kgf·cm)': res['Ma_y'],
               'Va eje mayor (kgf)': res['Va_x'], 'Va eje menor (kgf)': res['Va_y'],
               'KL/r eje fuerte': res['KLr_fuerte'], 'KL/r eje debil': res['KLr_debil'],
               'KL/r maximo': ev['klr'], 'Fe gobierna': res['detalle_c'].get('gobierna'),
               'Fn (kgf/cm2)': res['detalle_c'].get('Fn'), 'Ae (cm2)': res['detalle_c'].get('Ae'),
               'EL lambda/lambda_r': '; '.join(f'{n} {lam:.1f}/{lr:.1f}' for n, (lam, lr) in ev['el_det'].items()),
               'FU esbeltez local': max(ev['el'].values()),
               'FU esbeltez global': ev['const'].get(CHEQUEO_EG)}
        cap['E5 aplicado'] = ('SI' if e5_b else 'NO') if es_li else ''
        cap['U tension (LI)'] = round(u_b, 3) if es_li else None
        cap['SUPUESTOS'] = '; '.join(supuestos + ['estimado: ' + s for s in estimados])
        cap['NOTAS'] = '; '.join(notas + ([cap['SUPUESTOS']] if cap['SUPUESTOS'] else []))
        caps.append(cap)
        pares = list(zip(ev['filas'], casos))
        for u, caso in pares:
            det_filas.append([id_, perfil, caso] + [u.get(c) for c in CHEQUEOS_ASD]
                             + [max(v for v in u.values() if v is not None)])
        if not pares:
            fu = {c: None for c in COLS_RESULTADOS if c.startswith('FU')}
            fu.update({'CASO QUE GOBIERNA': None, 'FU ESBELTEZ LOCAL (B4.1)': ev['const'][CHEQUEO_EL],
                       'FU ESBELTEZ GLOBAL (KL/r<=200)': ev['const'].get(CHEQUEO_EG)})
            estado = 'SIN COMBINACIONES'
        else:
            fu = _resumen_fu(ev, pares)
            estado = 'CUMPLE' if fu['FU MAXIMO'] <= 1.0 else 'NO CUMPLE'
        res_filas.append(dict(ID=id_, PERFIL=perfil, MATERIAL=b.get('material'), GRUPO=grupo, **fu,
                              **{'KL/r EJE FUERTE': res['KLr_fuerte'], 'KL/r EJE DEBIL': res['KLr_debil']},
                              ESTADO=estado, NOTAS=cap['NOTAS']))
    resultados = pd.DataFrame(res_filas, columns=COLS_RESULTADOS)
    detalle = pd.DataFrame(det_filas, columns=['ID', 'PERFIL', 'CASO'] + CHEQUEOS_ASD + ['MAXIMO'])
    capacidades = pd.DataFrame(caps)
    with pd.ExcelWriter(ruta_salida, engine='openpyxl') as w:
        pd.DataFrame([['Metodo', 'ASD con ANSI/AISC 360-22 (Omega: traccion 1.67/2.00, compresion y flexion 1.67, cortante 1.50 o 1.67)'],
                      ['Demandas', 'combinaciones de servicio de COMBINACIONES (ASD); sin factores de carga'],
                      ['FU', 'factor de utilizacion = demanda / capacidad ASD; cumple si FU <= 1.0'],
                      ['FU esbeltez local', 'lambda / lambda_r por elemento (B4.1a en compresion, B4.1b en flexion; angulo: pata)'],
                      ['FU esbeltez global', 'KL/r / 200 en elementos a compresion (2.3.2); vigas sin verificacion de KL/r'],
                      ['Alcance', 'IR, CE y LI (angulos de lados iguales). CS (barras macizas) fuera del diseno; LM no incluido. '
                                  'Ductilidad: 12.1.2 (IR y CE) y 12.1.3.1 (columnas)'],
                      ['Unidades', 'fuerzas kgf; momentos kgf·cm; longitudes cm']],
                     columns=['DATO', 'VALOR']).to_excel(w, sheet_name='RESUMEN', index=False)
        capacidades.to_excel(w, sheet_name='CAPACIDADES', index=False)
        resultados.to_excel(w, sheet_name='RESULTADOS', index=False)
        detalle.to_excel(w, sheet_name='DETALLE', index=False)
    return capacidades, resultados, detalle


def fu_grupo_por_perfil(fu_matriz, grupo):
    """Por perfil: el FU maximo de las barras del grupo, cada una con su propia demanda. None si alguna barra del
    grupo no se puede revisar (sin Fu, perfil sin datos, sin combinaciones): entonces el perfil no se puede aceptar."""
    fm = fu_matriz[fu_matriz['ELEMENTO DISENO'] == grupo]
    out = {}
    for perfil, sub in fm.groupby('PERFIL'):
        x = pd.to_numeric(sub['FU MAXIMO'], errors='coerce')
        out[perfil] = None if x.isna().any() else float(x.max())
    return out


def listas_desde_matriz(fu_matriz, dib, familias=FAMILIAS_ASD):
    """Perfiles que cumplen por grupo: cada barra del grupo cumple con su propia demanda (FU <= 1 en resistencia,
    esbeltez local y global). Mismo criterio que FU_BARRAS y que el desplegable del notebook. Ordenados por tipo y
    seccion. Un grupo sin barras recibe el catalogo completo, sin verificar."""
    catalogo = sorted([n for n, d in G.PERFILES.items() if d['familia'] in familias], key=clave_orden)
    listas, filas = {}, []
    for g in GRUPOS_ELEMENTO:
        barras_g = [b for b in dib.barras if b['elemento'] == g]
        listas[g] = list(catalogo)
        if not barras_g:
            continue
        import collections
        material = collections.Counter(str(b.get('material') or '').strip() for b in barras_g).most_common(1)[0][0]
        fm = fu_matriz[fu_matriz['ELEMENTO DISENO'] == g].copy()
        for c in ('FU MAXIMO', 'FU ESBELTEZ LOCAL (B4.1)', 'FU ESBELTEZ GLOBAL (KL/r<=200)'):
            fm[c + ' N'] = pd.to_numeric(fm[c], errors='coerce')
        peor = fu_grupo_por_perfil(fu_matriz, g)
        cumplen = []
        for n in catalogo:
            fam = G.PERFILES[n]['familia']
            base = [g, fam, n, seccion_de(n), G.PERFILES[n]['masa_kg_m'], material]
            sub = fm[fm['PERFIL'] == n]
            if sub.empty:
                filas.append(base + [None, None, None, 'sin datos para este grupo'])
                continue
            x = peor.get(n)
            el = sub['FU ESBELTEZ LOCAL (B4.1) N'].max()
            eg = sub['FU ESBELTEZ GLOBAL (KL/r<=200) N'].max()
            eg = None if pd.isna(eg) else round(float(eg), 4)
            if x is None:
                filas.append(base + [None, round(float(el), 4) if not pd.isna(el) else None, eg,
                                     'no revisado: alguna barra del grupo no se puede verificar'])
                continue
            ok = x <= 1.0
            filas.append(base + [round(x, 4), round(float(el), 4) if not pd.isna(el) else None, eg,
                                 'cumple' if ok else 'no cumple'])
            if ok:
                cumplen.append(n)
        listas[g] = sorted(cumplen, key=clave_orden)
    tabla = pd.DataFrame(filas, columns=['GRUPO', 'TIPO', 'PERFIL', 'SECCION', 'MASA (kg/m)', 'MATERIAL',
                                         'FU MAXIMO', 'FU ESBELTEZ LOCAL (B4.1)',
                                         'FU ESBELTEZ GLOBAL (KL/r<=200)', 'RESULTADO'])
    return listas, tabla


def listas_por_grupo_asd(dib, materiales_filas, longitudes_df, demandas, id_barra, familias=FAMILIAS_ASD):
    raise NotImplementedError('Sin uso en la version actual: sus demandas leen solo momentos de extremo (auditoria H-01). No usar.')
    """Perfiles de IR, CE y LI que cumplen en ASD para cada grupo de elementos: FU <= 1 por resistencia, esbeltez
    local y esbeltez global, con la envolvente de las combinaciones, la longitud, K y Cb mas exigentes.
    Ordenados por tipo y seccion. Un grupo sin barras (o sin demanda) recibe el catalogo completo sin verificar.
    Devuelve (listas {grupo: [perfiles]}, tabla DataFrame)."""
    import collections
    mat = {str(f[0]).strip(): dict(fy=_num(f[2]), fu=_num(f[3]), E=_num(f[4]), nu=_num(f[5])) for f in materiales_filas}
    lon = {}
    for _, r in longitudes_df.iterrows():
        id_ = _num(r.get('ID'))
        if id_ is not None:
            lon[int(id_)] = r
    comb = demandas[demandas['TIPO'] == 'COMBINACION']
    catalogo = sorted([n for n, d in G.PERFILES.items() if d['familia'] in familias], key=clave_orden)
    listas, filas_tabla = {}, []
    for g in GRUPOS_ELEMENTO:
        idx = [i for i, b in enumerate(dib.barras) if b['elemento'] == g]
        listas[g] = list(catalogo)
        if not idx:
            continue
        ids = [id_barra.get(i, i) for i in idx]
        f = comb[comb['BARRA'].isin(ids)]
        if f.empty:
            continue
        num = lambda c: f[c].astype(float).fillna(0.0)
        pc = max(num('N I (kgf)').clip(lower=0).max(), (-num('N J (kgf)')).clip(lower=0).max())
        pt = max((-num('N I (kgf)')).clip(lower=0).max(), num('N J (kgf)').clip(lower=0).max())
        mx = max(num('Mz I (kgf·m)').abs().max(), num('Mz J (kgf·m)').abs().max()) * 100.0
        my = max(num('My I (kgf·m)').abs().max(), num('My J (kgf·m)').abs().max()) * 100.0
        vy = max(num('Vy I (kgf)').abs().max(), num('Vy J (kgf)').abs().max())
        vz = max(num('Vz I (kgf)').abs().max(), num('Vz J (kgf)').abs().max())
        base = dict(Mr_x=mx, Mr_y=my, Vr_x=vy, Vr_y=vz)
        sint = [dict(base, Pr_c=pc, Pr_t=0.0), dict(base, Pr_c=0.0, Pr_t=pt)]
        lx = ly = lb = kx = ky = 0.0
        e5_todas, lineas_li = [], []
        cb_min = None
        niveles, materiales = set(), collections.Counter()
        for i in idx:
            r = lon.get(id_barra.get(i, i))
            L = float(np.linalg.norm(np.array(dib.nodos[dib.barras[i]['n2']]) - np.array(dib.nodos[dib.barras[i]['n1']])))

            def campo(nombre):
                return _num(r.get(nombre)) if r is not None else None
            v = {k: campo(k) for k in ('LX (m)', 'LY (m)', 'LB (m)', 'KX', 'KY', 'CB')}
            lx = max(lx, _req(v['LX (m)'], 'LX (m)'))
            ly = max(ly, _req(v['LY (m)'], 'LY (m)'))
            lb = max(lb, _req(v['LB (m)'], 'LB (m)'))
            kx = max(kx, _req(v['KX'], 'KX'))
            ky = max(ky, _req(v['KY'], 'KY'))
            cbi = _req(v['CB'], 'CB')
            cb_min = cbi if cb_min is None else min(cb_min, cbi)
            duct = r.get('DUCTILIDAD') if r is not None else None
            if duct is not None and not (isinstance(duct, float) and math.isnan(duct)) and str(duct).strip():
                niveles.add(str(duct).strip().upper())
            materiales[str(dib.barras[i].get('material') or '').strip()] += 1
            ent = _entrada_barra(dib, i, id_barra, lon, mat)
            e5_todas.append(ent['e5'])
            lineas_li.append((ent['l_li'], ent['conexion']))
        nivel = 'ALTA' if 'ALTA' in niveles else ('MEDIA' if 'MEDIA' in niveles else None)
        e5_grupo = bool(e5_todas) and all(e5_todas)
        nombre_mat = materiales.most_common(1)[0][0]
        m = mat.get(nombre_mat)
        if m is None or m['fy'] is None or m['E'] is None or m['nu'] is None:
            continue
        cumplen = []
        for nombre in catalogo:
            fam = G.PERFILES[nombre]['familia']
            masa = G.PERFILES[nombre]['masa_kg_m']
            base_fila = [g, fam, nombre, seccion_de(nombre), masa, nombre_mat]
            p, falta = _props_asd(nombre, fam)
            if p is None:
                filas_tabla.append(base_fila + [None, None, None, 'no revisado: ' + falta])
                continue
            ev = _chequear(p, fam, m['fy'], m['fu'], m['E'], m['nu'], lx * 100.0, ly * 100.0, lb * 100.0,
                           kx, ky, g, nivel, sint, cb=cb_min,
                           e5=(fam == 'LI' and e5_grupo),
                           u_t=(min(factor_u_angulo(p['xc'], l, c) for l, c in lineas_li)
                                if fam == 'LI' and lineas_li else 1.0))
            if ev['motivo'] and any(d['Pr_c'] > 0 for d in sint):
                filas_tabla.append(base_fila + [None, None, None, 'no revisado: ' + ev['motivo']])
                continue
            umax = max(max(u.values()) for u in ev['filas']) if ev['filas'] else None
            fu_el = ev['const'][CHEQUEO_EL]
            fu_eg = ev['const'].get(CHEQUEO_EG)
            if m['fu'] is None:
                umax, motivo = None, 'no revisado: falta Fu del material'
            else:
                motivo = 'cumple' if umax is not None and umax <= 1.0 else 'no cumple'
            filas_tabla.append(base_fila + [umax, fu_el, fu_eg, motivo])
            if umax is not None and umax <= 1.0:
                cumplen.append(nombre)
        listas[g] = sorted(cumplen, key=clave_orden)
    tabla = pd.DataFrame(filas_tabla, columns=['GRUPO', 'TIPO', 'PERFIL', 'SECCION', 'MASA (kg/m)', 'MATERIAL',
                                                'FU MAXIMO', 'FU ESBELTEZ LOCAL (B4.1)',
                                                'FU ESBELTEZ GLOBAL (KL/r<=200)', 'RESULTADO'])
    return listas, tabla
