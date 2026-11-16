#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprobacion manual independiente (no importa modulos de la aplicacion).

A) Barra 1 (IR 10 x 49, columna): FU por AISC 360-22 ASD (D2, E3/E4/E7, F2, F6, G2, G6,
   H1-1) y verificaciones NTC (esbeltez local, KL/r, ancho/grueso Tabla 12.1.2).
   Control: barra 13 (IR 12 x 16, viga, pandeo lateral-torsional elastico F2-3).
B) Flecha de la barra 15 (IR 12 x 16, L = 500 cm) con la solucion exacta de
   Euler-Bernoulli entre extremos (funciones de Hermite + termino del peso propio),
   usando UZ y giros de la hoja DEFORMADA. Control de signos: momentos de extremo
   de la misma solucion contra MZ de la hoja BARRAS.

Solo lectura de:
  fuentes_notebook/datos/perfiles_gerdau_mexico_rev04.json
  auditoria_rev02/ejemplo/diseno_asd.xlsx        (CAPACIDADES, RESULTADOS: solo comparacion)
  auditoria_rev02/ejemplo/resultados_soportes.xlsx (BARRAS, DEFORMADA: entradas)
Los valores de la memoria se transcriben con su seccion (memoria_calculo.html).
"""
import json
import math
import os

import openpyxl

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))  # raiz del repositorio
JSON_PATH = os.path.join(REPO, 'fuentes_notebook', 'datos', 'perfiles_gerdau_mexico_rev04.json')
DISENO_XLSX = os.path.join(REPO, 'auditoria_rev02', 'ejemplo', 'diseno_asd.xlsx')
ESF_XLSX = os.path.join(REPO, 'auditoria_rev02', 'ejemplo', 'resultados_soportes.xlsx')
OUT_TXT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'comprobacion_manual_salida.txt')

SALIDA = []


def P(texto=''):
    SALIDA.append(texto)
    print(texto)


# ---------------------------------------------------------------------------
# Material y factores. Fuente: memoria sec. 3.1 (tabla Materiales y tabla NORMA).
# ---------------------------------------------------------------------------
FY = 3515.0          # kgf/cm2, A-572 G 50 (memoria, Materiales)
FU = 4570.0          # kgf/cm2, A-572 G 50 (memoria, Materiales)
E = 2038900.0        # kgf/cm2 (memoria, Materiales)
NU = 0.30
G = E / (2.0 * (1.0 + NU))
OM_T_FLU = 1.67      # D2 fluencia (tabla NORMA)
OM_T_FRA = 2.00      # D2 fractura (tabla NORMA)
OM_C = 1.67          # E1 (tabla NORMA). La instruccion decia 2.00; AISC 360-22 ASD usa 1.67.
OM_B = 1.67          # F1
OM_V = 1.67          # G1, cortante general
OM_V_I = 1.50        # G2.1(a), I laminada con h/tw <= 2.24 sqrt(E/Fy) (tabla NORMA: AISC_OMEGA_V_LAM)
KZ = 1.0             # PARAMETROS KZ_TORSION (memoria sec. 3.1)
SQ = math.sqrt(E / FY)   # sqrt(E/Fy)


def leer_perfil(nombre):
    """Geometria del perfil desde la base JSON Gerdau rev04 (campos *_cm / *_cm3 / *_cm4 / *_cm6)."""
    with open(JSON_PATH, encoding='utf-8') as f:
        datos = json.load(f)
    clave = nombre.replace(' ', '')
    for p in datos['perfiles']:
        if p['perfil_comercial'].replace(' ', '') == clave:
            return p
    raise KeyError(nombre)


def capacidades(p, KLx, KLy, Lb, Lz, Cb):
    """Capacidades admisibles ASD (kgf, kgf·cm). KLx, KLy, Lb, Lz en cm."""
    d, bf, tw, tf = p['d_ala_diametro_cm'], p['bf_b_cm'], p['tw_cm'], p['tf_t_cm']
    A, Ix, Iy = p['area_cm2'], p['ix_cm4'], p['iy_cm4']
    Sx, Sy, Zx, Zy = p['sx_cm3'], p['sy_cm3'], p['zx_cm3'], p['zy_cm3']
    rx, ry, J, Cw = p['rx_cm'], p['ry_cm'], p['j_cm4'], p['cw_cm6']
    r = {'d': d, 'bf': bf, 'tw': tw, 'tf': tf, 'A': A, 'Ix': Ix, 'Iy': Iy, 'Sx': Sx,
         'Sy': Sy, 'Zx': Zx, 'Zy': Zy, 'rx': rx, 'ry': ry, 'J': J, 'Cw': Cw}

    # --- D2 Traccion (Ae = Ag, U = 1: sin conexiones modeladas, supuesto de la memoria)
    r['Pn_flu'] = FY * A
    r['Pn_fra'] = FU * A
    r['Pt'] = min(r['Pn_flu'] / OM_T_FLU, r['Pn_fra'] / OM_T_FRA)

    # --- E3 / E4 Compresion (doble simetria, Q = 1 verificado en 'esbeltez local')
    r['KLr_x'] = KLx / rx
    r['KLr_y'] = KLy / ry
    r['KLr_max'] = max(r['KLr_x'], r['KLr_y'])
    r['Fex'] = math.pi ** 2 * E / r['KLr_x'] ** 2
    r['Fey'] = math.pi ** 2 * E / r['KLr_y'] ** 2
    r0sq = rx ** 2 + ry ** 2                       # x0 = y0 = 0 (doble simetria)
    r['Fez'] = (G * J + math.pi ** 2 * E * Cw / (KZ * Lz) ** 2) / (A * r0sq)   # E4-5
    r['Fe'] = min(r['Fex'], r['Fey'], r['Fez'])
    if FY / r['Fe'] <= 2.25:                      # E3-2 (inelastico)
        r['Fcr'] = 0.658 ** (FY / r['Fe']) * FY
    else:                                         # E3-3 (elastico)
        r['Fcr'] = 0.877 * r['Fe']
    r['Pn_comp'] = r['Fcr'] * A
    r['Pc'] = r['Pn_comp'] / OM_C

    # --- F2 Flexion eje fuerte (Lb, Cb). Compacidad: F2 aplica solo si alas y alma compactas.
    r['lam_f'] = (bf / 2.0) / tf
    r['lam_w'] = (d - 2.0 * tf) / tw
    assert r['lam_f'] <= 0.38 * SQ, 'ala no compacta: F2 no aplica'
    assert r['lam_w'] <= 3.76 * SQ, 'alma no compacta: F2 no aplica'
    ho = d - tf
    c = 1.0
    jc = J * c / (Sx * ho)
    rts = math.sqrt(math.sqrt(Iy * Cw) / Sx)
    Lp = 1.76 * ry * SQ
    Lr = 1.95 * rts * (E / (0.7 * FY)) * math.sqrt(jc + math.sqrt(jc ** 2 + 6.76 * (0.7 * FY / E) ** 2))
    Mp = FY * Zx
    if Lb <= Lp:
        Mn, zona = Mp, 'Lb <= Lp: F2-1'
    elif Lb <= Lr:
        Mn = Cb * (Mp - (Mp - 0.7 * FY * Sx) * (Lb - Lp) / (Lr - Lp))
        zona = 'Lp < Lb <= Lr: F2-2'
    else:
        Fcr_ltb = Cb * math.pi ** 2 * E / (Lb / rts) ** 2 * math.sqrt(1.0 + 0.078 * jc * (Lb / rts) ** 2)
        Mn = Fcr_ltb * Sx
        zona = 'Lb > Lr: F2-3'
    Mn = min(Mn, Mp)
    r.update({'Lp': Lp, 'Lr': Lr, 'rts': rts, 'ho': ho, 'jc': jc, 'Mp': Mp, 'Mn_ltb': Mn,
              'zona_ltb': zona, 'Mcx': Mn / OM_B})

    # --- F6 Flexion eje debil (ala compacta: Mn = Mp)
    Mp_y = min(FY * Zy, 1.6 * FY * Sy)
    assert r['lam_f'] <= 0.38 * SQ
    r['Mp_y'] = Mp_y
    r['Mcy'] = Mp_y / OM_B

    # --- G2 Cortante eje fuerte (alma). Cv1 = 1 si h/tw <= 2.24 sqrt(E/Fy).
    r['Aw'] = d * tw
    assert r['lam_w'] <= 2.24 * SQ, 'Cv1 < 1: no implementado aqui'
    r['Vn_x'] = 0.6 * FY * r['Aw'] * 1.0
    r['Vcx'] = r['Vn_x'] / OM_V_I

    # --- G6 Cortante eje debil (dos patines, Cv2 = 1.0, segun memoria)
    r['Vn_y'] = 2.0 * 0.6 * FY * bf * tf * 1.0
    r['Vcy'] = r['Vn_y'] / OM_V
    return r


def h1(Pr, Pc, Mrx, Mcx, Mry, Mcy):
    """H1-1 (AISC 360-22 H1.1). Pc = Pc de compresion o Pt de traccion (AISC H1)."""
    ratio = Pr / Pc
    mom = Mrx / Mcx + Mry / Mcy
    if ratio >= 0.2:
        return ratio + 8.0 / 9.0 * mom, 'H1-1a'
    return ratio / 2.0 + mom, 'H1-1b'


def demandas_barra(r):
    """Demandas ASD1 de BARRAS. Convencion RESUMEN: N_I>0 compresion; N_J<0 compresion.
    MZ = momento fuerte (eje x de la seccion), MY = debil. Vy = cortante fuerte, Vz = debil."""
    NI, NJ = r[7], r[13]
    dem = {}
    dem['Pc'] = max(NI, -NJ, 0.0)
    dem['Pt'] = max(-NI, NJ, 0.0)
    dem['Mrx'] = max(abs(r[12]), abs(r[18])) * 100.0     # kgf·m -> kgf·cm (extremos)
    dem['Mry'] = max(abs(r[11]), abs(r[17])) * 100.0
    dem['Vrx'] = max(abs(r[8]), abs(r[14]))
    dem['Vry'] = max(abs(r[9]), abs(r[15]))
    dem['MZmax_hoja'] = r[19] * 100.0
    dem['MYmax_hoja'] = r[20] * 100.0
    return dem


def fila_barras(wb_e, caso, barra):
    for r in wb_e['BARRAS'].iter_rows(min_row=2, values_only=True):
        if r[0] == caso and r[2] == barra:
            return r
    raise KeyError((caso, barra))


def tabla_xlsx(ws):
    filas = list(ws.iter_rows(values_only=True))
    return filas[0], filas[1:]


def indice(enc, prefijo):
    for i, h in enumerate(enc):
        if isinstance(h, str) and h.startswith(prefijo):
            return i
    raise KeyError(prefijo)


def xlsx_valor(ws, idb, prefijo):
    enc, filas = tabla_xlsx(ws)
    for f in filas:
        if f[0] == idb:
            return f[indice(enc, prefijo)]
    raise KeyError(idb)


def cmp_linea(nombre, mio, memo=None, xlsx=None, tol_memo=0.0, dec=4):
    estado = 'OK'
    if memo is not None and abs(mio - memo) > tol_memo:
        estado = 'DIF vs memoria'
    if xlsx is not None and abs(mio - xlsx) > 1e-3 * abs(xlsx) + 1e-9:
        estado = 'DIF vs xlsx' if estado == 'OK' else estado + ' y xlsx'
    m_s = '-' if memo is None else f'{memo:,.{dec}f}'
    x_s = '-' if xlsx is None else f'{xlsx:,.{dec}f}'
    P(f'  {nombre:<28}{mio:>14,.{dec}f}{m_s:>14}{x_s:>14}   {estado}')


def revisar(titulo, idb, perfil, KLx, KLy, Lb, Lz, Cb, modo, memo, dem_memo):
    wb_d = openpyxl.load_workbook(DISENO_XLSX, data_only=True)
    wb_e = openpyxl.load_workbook(ESF_XLSX, data_only=True)
    p = leer_perfil(perfil)
    c = capacidades(p, KLx, KLy, Lb, Lz, Cb)
    r_b = fila_barras(wb_e, 'ASD1', idb)
    dem = demandas_barra(r_b)

    P('=' * 110)
    P(f'{titulo}  |  ID {idb}  |  {p["perfil_comercial"]}  |  {p["masa_kg_m"]} kg/m')
    P(f'Geometria (JSON, {p["referencia_excel"]}): d={c["d"]} bf={c["bf"]} tw={c["tw"]} tf={c["tf"]} '
      f'A={c["A"]} Ix={c["Ix"]} Iy={c["Iy"]} Sx={c["Sx"]:.3f} Sy={c["Sy"]:.3f} Zx={c["Zx"]} Zy={c["Zy"]} '
      f'rx={c["rx"]} ry={c["ry"]} J={c["J"]} Cw={c["Cw"]:.2f}')
    P(f'Longitudes (memoria sec.7): KLx={KLx} KLy={KLy} Lb={Lb} Lz={Lz} cm  Cb={Cb}  '
      f'(ductilidad MEDIA)')
    P('')
    P('-- Capacidades y demandas: mio | memoria | xlsx')
    P(f'  {"":<28}{"mio":>14}{"memoria":>14}{"xlsx":>14}')
    xc = wb_d['CAPACIDADES']
    xr = wb_d['RESULTADOS']
    # xlsx CAPACIDADES (fila del ID)
    x_Pt = xlsx_valor(xc, idb, 'Pa traccion')
    x_Pc = xlsx_valor(xc, idb, 'Pa compresion')
    x_Mcx = xlsx_valor(xc, idb, 'Ma eje mayor')
    x_Mcy = xlsx_valor(xc, idb, 'Ma eje menor')
    x_Vcx = xlsx_valor(xc, idb, 'Va eje mayor')
    x_Vcy = xlsx_valor(xc, idb, 'Va eje menor')
    x_Fn = xlsx_valor(xc, idb, 'Fn (')
    x_KLx = xlsx_valor(xc, idb, 'KL/r eje fuerte')
    x_KLy = xlsx_valor(xc, idb, 'KL/r eje debil')

    P('  Traccion D2')
    cmp_linea('Pn fluencia Fy Ag', c['Pn_flu'])
    cmp_linea('Pn fractura Fu Ae', c['Pn_fra'])
    cmp_linea('Pt admisible', c['Pt'], memo.get('Pt'), x_Pt, 0.5)
    P('  Compresion E3/E4/E7')
    cmp_linea('KL/rx', c['KLr_x'], memo.get('KLr_x'), x_KLx, 0.05, 2)
    cmp_linea('KL/ry', c['KLr_y'], memo.get('KLr_y'), x_KLy, 0.05, 2)
    cmp_linea('Fex (kgf/cm2)', c['Fex'])
    cmp_linea('Fey (kgf/cm2)', c['Fey'], memo.get('Fe'), None, 1.0, 2)
    cmp_linea('Fez (kgf/cm2)', c['Fez'])
    cmp_linea('Fe = min (kgf/cm2)', c['Fe'], memo.get('Fe'), None, 1.0, 2)
    cmp_linea('Fcr = Fn (kgf/cm2)', c['Fcr'], memo.get('Fn'), x_Fn, 0.5, 2)
    cmp_linea('Pn = Fn Ae (kgf)', c['Pn_comp'], memo.get('Pn_comp'), None, 0.5, 2)
    cmp_linea('Pc = Pn/Omega_c (kgf)', c['Pc'], memo.get('Pc'), x_Pc, 0.5, 2)
    P('  Flexion eje fuerte F2 (Lb=%g cm, Cb=%g)' % (Lb, Cb))
    cmp_linea('Lp (cm)', c['Lp'], None, None, dec=2)
    cmp_linea('Lr (cm)', c['Lr'], None, None, dec=2)
    cmp_linea('rts (cm)', c['rts'], None, None, dec=3)
    cmp_linea('Mp = Fy Zx (kgf·cm)', c['Mp'], memo.get('Mp_x'), None, 0.5, 1)
    cmp_linea('Mn LTB (kgf·cm)', c['Mn_ltb'], memo.get('Mn_ltb'), None, 1.0, 1)
    cmp_linea('Mcx = Mn/Omega_b (kgf·cm)', c['Mcx'], memo.get('Mcx'), x_Mcx, 0.5, 1)
    P(f'    zona LTB: {c["zona_ltb"]}')
    P('  Flexion eje debil F6')
    cmp_linea('Mp_y = min(Fy Zy,1.6FySy)', c['Mp_y'], memo.get('Mp_y'), None, 0.5, 1)
    cmp_linea('Mcy = Mp_y/Omega_b (kgf·cm)', c['Mcy'], memo.get('Mcy'), x_Mcy, 0.5, 1)
    P('  Cortante G2 (eje fuerte) y G6 (eje debil)')
    cmp_linea('Vn_x = 0.6 Fy Aw Cv1', c['Vn_x'], None, None, dec=1)
    cmp_linea('Vcx = Vn/1.50 (kgf)', c['Vcx'], memo.get('Vcx'), x_Vcx, 0.5, 1)
    cmp_linea('Vcy = Vn/1.67 (kgf)', c['Vcy'], memo.get('Vcy'), x_Vcy, 0.5, 1)

    # Demandas (combinacion ASD1 = ASD2 en esta corrida: sobrecarga sin cargas)
    P('  Demandas ASD1 (BARRAS) | memoria')
    P(f'  {"Pc (kgf)":<28}{dem["Pc"]:>14,.3f}{memo.get("Pr_c", "-"):>14}')
    P(f'  {"Pt (kgf)":<28}{dem["Pt"]:>14,.3f}{memo.get("Pr_t", "-"):>14}')
    P(f'  {"Mrx = MZ (kgf·cm)":<28}{dem["Mrx"]:>14,.3f}{memo.get("Mrx", "-"):>14}  '
      f'(MZ MAX hoja {dem["MZmax_hoja"]:,.3f})')
    P(f'  {"Mry = MY (kgf·cm)":<28}{dem["Mry"]:>14,.3f}{memo.get("Mry", "-"):>14}  '
      f'(MY MAX hoja {dem["MYmax_hoja"]:,.3f})')
    P(f'  {"Vrx = Vy (kgf)":<28}{dem["Vrx"]:>14,.3f}{memo.get("Vrx", "-"):>14}')
    P(f'  {"Vry = Vz (kgf)":<28}{dem["Vry"]:>14,.3f}{memo.get("Vry", "-"):>14}')

    # ----- FU AISC -----
    FU = {}
    FU['traccion'] = dem['Pt'] / c['Pt']
    FU['compresion'] = dem['Pc'] / c['Pc']
    FU['flex_mayor'] = dem['Mrx'] / c['Mcx']
    FU['flex_menor'] = dem['Mry'] / c['Mcy']
    FU['cort_mayor'] = dem['Vrx'] / c['Vcx']
    FU['cort_menor'] = dem['Vry'] / c['Vcy']
    if dem['Pc'] > 0:
        Pr, Pcap = dem['Pc'], c['Pc']
    else:
        Pr, Pcap = dem['Pt'], c['Pt']
    FU['H1'], ec_h1 = h1(Pr, Pcap, dem['Mrx'], c['Mcx'], dem['Mry'], c['Mcy'])
    FU_AISC = max(FU.values())

    # ----- Verificaciones NTC -----
    lamr_f = (0.56 if modo == 'comp' else 1.00) * SQ
    lamr_w = (1.49 if modo == 'comp' else 5.70) * SQ
    NTC = {}
    NTC['esb_local'] = max(c['lam_f'] / lamr_f, c['lam_w'] / lamr_w)
    NTC['esb_global'] = c['KLr_max'] / 200.0 if modo == 'comp' else None
    bt = (c['bf'] / 2.0) / c['tf']
    NTC['ductil_bt'] = bt / (0.38 * SQ)
    NTC['ductil_KLr60'] = c['KLr_max'] / 60.0 if modo == 'comp' else None
    NTC_vals = [v for v in NTC.values() if v is not None]
    FU_NTC = max(NTC_vals)
    FU_TOTAL = max(FU_AISC, FU_NTC)

    P('')
    P('-- FU (mio) | memoria | xlsx RESULTADOS')
    P(f'  {"":<28}{"mio":>14}{"memoria":>14}{"xlsx":>14}')
    cmp_linea('FU traccion', FU['traccion'], memo.get('FU_T'), xlsx_valor(xr, idb, 'FU TRACCION'), 5e-4, 5)
    cmp_linea('FU compresion', FU['compresion'], memo.get('FU_C'), xlsx_valor(xr, idb, 'FU COMPRESION'), 5e-4, 5)
    cmp_linea('FU flexion eje mayor', FU['flex_mayor'], memo.get('FU_Mx'), xlsx_valor(xr, idb, 'FU FLEXION EJE MAYOR'), 5e-4, 5)
    cmp_linea('FU flexion eje menor', FU['flex_menor'], memo.get('FU_My'), xlsx_valor(xr, idb, 'FU FLEXION EJE MENOR'), 5e-4, 5)
    cmp_linea('FU cortante eje mayor', FU['cort_mayor'], memo.get('FU_Vx'), xlsx_valor(xr, idb, 'FU CORTANTE EJE MAYOR'), 5e-4, 5)
    cmp_linea('FU cortante eje menor', FU['cort_menor'], memo.get('FU_Vy'), xlsx_valor(xr, idb, 'FU CORTANTE EJE MENOR'), 5e-4, 5)
    cmp_linea('FU interaccion ' + ec_h1, FU['H1'], memo.get('FU_H1'), xlsx_valor(xr, idb, 'FU INTERACCION'), 5e-4, 5)
    cmp_linea('FU esbeltez local', NTC['esb_local'], None, xlsx_valor(xr, idb, 'FU ESBELTEZ LOCAL'), dec=5)
    if NTC['esb_global'] is not None:
        cmp_linea('FU esbeltez global KL/r/200', NTC['esb_global'], None, xlsx_valor(xr, idb, 'FU ESBELTEZ GLOBAL'), dec=5)
    cmp_linea('FU ductilidad b/t', NTC['ductil_bt'], memo.get('FU_duct_bt'), xlsx_valor(xr, idb, 'FU DUCTILIDAD'), 5e-4, 5)
    if NTC['ductil_KLr60'] is not None:
        cmp_linea('FU ductilidad KL/r/60', NTC['ductil_KLr60'], None, None, dec=5)
    P('')
    P(f'  FU maximo AISC (fuerzas)          mio = {FU_AISC:.5f}')
    P(f'  FU maximo NTC (esbeltez/ductil.)  mio = {FU_NTC:.5f}')
    P(f'  FU MAXIMO total                   mio = {FU_TOTAL:.5f}  | memoria cabecera = {memo.get("FU_max_bar", "-")}'
      f'  | xlsx FU MAXIMO = {xlsx_valor(xr, idb, "FU MAXIMO"):.5f}')
    P('  Detalle esbeltez local (%s): lam_f = %.4f (lim %.4f), lam_w = %.4f (lim %.4f)' % (
        'compresion NTC 3.2.1' if modo == 'comp' else 'flexion NTC 3.2.2',
        c['lam_f'], lamr_f, c['lam_w'], lamr_w))
    P('  Ductilidad MEDIA: b/t = %.4f, limite 0.38 sqrt(E/Fy) = %.4f' % (bt, 0.38 * SQ))
    return {'c': c, 'dem': dem, 'FU': FU, 'FU_AISC': FU_AISC, 'FU_NTC': FU_NTC,
            'FU_TOTAL': FU_TOTAL, 'NTC': NTC}


# ---------------------------------------------------------------------------
# B) Flecha por Euler-Bernoulli entre extremos (Hermite + peso propio)
# ---------------------------------------------------------------------------
def nodos_asd1(wb_e):
    """Coordenadas (cm), UZ (cm) y giros (rad) de DEFORMADA para la combinacion ASD1."""
    nodos = {}
    for r in wb_e['DEFORMADA'].iter_rows(min_row=2, values_only=True):
        if r[0] == 'ASD1' and r[1] == 'COMBINACION':
            nodos[r[2]] = {'X': r[3] * 100.0, 'Y': r[4] * 100.0, 'Z': r[5] * 100.0,
                           'UZ': r[8] / 10.0,          # mm -> cm
                           'RX': r[9], 'RY': r[10], 'RZ': r[11]}
    return nodos


def hermite(EI, L, w1, w2, t1, t2, q, n=4001):
    """Flecha relativa a la cuerda: max |w(x) - cuerda(x)|. w en cm, t = dw/ds en rad, q kgf/cm."""
    mejor_x, mejor_d = 0.0, 0.0
    for i in range(n):
        x = L * i / (n - 1)
        xi = x / L
        H1 = 1 - 3 * xi ** 2 + 2 * xi ** 3
        H2 = L * (xi - 2 * xi ** 2 + xi ** 3)
        H3 = 3 * xi ** 2 - 2 * xi ** 3
        H4 = L * (-xi ** 2 + xi ** 3)
        pp = q * x ** 2 * (L - x) ** 2 / (24.0 * EI)
        w = H1 * w1 + H2 * t1 + H3 * w2 + H4 * t2 + pp
        cuerda = w1 + (w2 - w1) * xi
        dev = w - cuerda
        if abs(dev) > abs(mejor_d):
            mejor_x, mejor_d = x, dev
    return mejor_x / L, mejor_d


def momentos_extremo(EI, L, w1, w2, t1, t2, q):
    """EI w''(0) y EI w''(L): momentos de extremo de la misma solucion."""
    m0 = EI * (-6 * w1 - 4 * L * t1 + 6 * w2 - 2 * L * t2) / L ** 2 + q * L ** 2 / 12.0
    mL = EI * (6 * w1 + 2 * L * t1 - 6 * w2 + 4 * L * t2) / L ** 2 + q * L ** 2 / 12.0
    return m0, mL


def datos_viga(wb_e, nodos, barra):
    r = fila_barras(wb_e, 'ASD1', barra)
    I, J = nodos[r[3]], nodos[r[4]]
    dx, dy, dz = J['X'] - I['X'], J['Y'] - I['Y'], J['Z'] - I['Z']
    L = math.sqrt(dx * dx + dy * dy + dz * dz)
    ux, uy, uz = dx / L, dy / L, dz / L
    assert abs(uz) < 1e-9, 'viga no horizontal'
    # Giro de la tangente en la direccion de la barra: dw/ds = (theta x u)_z = RX*uy - RY*ux
    t1 = I['RX'] * uy - I['RY'] * ux
    t2 = J['RX'] * uy - J['RY'] * ux
    return {'barra': barra, 'I': r[3], 'J': r[4], 'L': L, 'ux': ux, 'uy': uy,
            'w1': I['UZ'], 'w2': J['UZ'], 't1': t1, 't2': t2, 'row': r,
            'RYI': I['RY'], 'RYJ': J['RY']}


def main():
    wb_d = openpyxl.load_workbook(DISENO_XLSX, data_only=True)
    wb_e = openpyxl.load_workbook(ESF_XLSX, data_only=True)

    P('COMPROBACION MANUAL INDEPENDIENTE (AISC 360-22 ASD / NTC) - salida')
    P('Unidades: kgf, kgf·cm, cm. Las columnas "memoria" y "xlsx" son comparacion, no entrada.')
    P('')

    # ------------------------------------------------------------------ A
    P('#' * 110)
    P('A. FACTOR DE USO: BARRA 1 (columna) Y CONTROL BARRA 13 (viga)')
    P('#' * 110)

    memo_b1 = {
        'Pt': 195535, 'KLr_x': 31.8, 'KLr_y': 53.8, 'Fe': 6940, 'Fn': 2844,
        'Pn_comp': 264168, 'Pc': 158185, 'Mp_x': 3479850, 'Mn_ltb': 3341528, 'Mcx': 2000915,
        'Mp_y': 1630960, 'Mcy': 976623, 'Vcx': 30592, 'Vcy': 91099,
        'Pr_c': 2217, 'Pr_t': 0.0, 'Mrx': 974.8, 'Mry': 1413, 'Vrx': 4.2, 'Vry': 6.1,
        'FU_T': 0.000, 'FU_C': 0.014, 'FU_Mx': 0.000, 'FU_My': 0.001, 'FU_Vx': 0.000,
        'FU_Vy': 0.000, 'FU_H1': 0.009, 'FU_duct_bt': 0.977, 'FU_max_bar': 0.977,
    }
    b1 = revisar('BARRA 1', 1, 'IR 10 × 49', KLx=350.0, KLy=350.0, Lb=350.0, Lz=350.0, Cb=1.0,
                 modo='comp', memo=memo_b1, dem_memo=None)
    P('')
    # Sensibilidad: Omega_c = 2.00 (la instruccion) en lugar de 1.67
    P('  Nota interpretacion: si Omega_c = 2.00 (instruccion), FU compresion = %.5f '
      '(en vez de %.5f); no cambia el FU maximo total.' % (
          b1['FU']['compresion'] * OM_C / 2.00, b1['FU']['compresion']))
    P('')

    memo_b13 = {
        'Pt': 63986, 'Pc': 5140, 'Fe': 322.0, 'Fn': 282.4, 'Pn_comp': 8584,
        'Mp_x': 1156435, 'Mn_ltb': 225327, 'Mcx': 134926, 'Mp_y': 130055, 'Mcy': 77877,
        'Vcx': 24014, 'Vcy': 17092,
        'Pr_c': 0.0, 'Pr_t': 10.1, 'Mrx': 5456, 'Mry': 0.0, 'Vrx': 62.7, 'Vry': 0.0,
        'FU_T': 0.000, 'FU_C': 0.000, 'FU_Mx': 0.040, 'FU_My': 0.000, 'FU_Vx': 0.003,
        'FU_Vy': 0.000, 'FU_H1': 0.041, 'FU_duct_bt': 0.824, 'FU_max_bar': 0.824,
    }
    b13 = revisar('CONTROL BARRA 13 (viga)', 13, 'IR 12 × 16', KLx=500.0, KLy=500.0, Lb=500.0,
                  Lz=500.0, Cb=1.0, modo='flex', memo=memo_b13, dem_memo=None)
    P('')

    # ------------------------------------------------------------------ B
    P('#' * 110)
    P('B. FLECHA RELATIVA A LA CUERDA: BARRA 15 (IR 12 x 16, L = 500 cm), ASD1')
    P('#' * 110)
    nodos = nodos_asd1(wb_e)
    v = datos_viga(wb_e, nodos, 15)
    p12 = leer_perfil('IR 12 × 16')
    EIx = E * p12['ix_cm4']      # eje fuerte (Mz) en el plano vertical
    EIy = E * p12['iy_cm4']      # eje debil, solo para contraste
    q = -p12['masa_kg_m'] / 100.0  # peso propio (masa Gerdau x g = 1 kgf/kg), kgf/cm, hacia abajo
    L = v['L']
    P(f'Barra 15: nodos I={v["I"]} J={v["J"]}, L = {L:.3f} cm (memoria: 500.0). Direccion u = ({v["ux"]:.1f}, {v["uy"]:.1f}, 0)')
    P(f'Traslaciones UZ (DEFORMADA, mm): I = {v["w1"]*10:.6f}   J = {v["w2"]*10:.6f}')
    P(f'Giros (DEFORMADA, RY rad): I = {v["RYI"]:.6e}   J = {v["RYJ"]:.6e}')
    P(f'Pendiente dw/ds (rad) = RX*uy - RY*ux: I = {v["t1"]:.6e}   J = {v["t2"]:.6e}')
    P(f'EI (fuerte) = E Ix = {EIx:.4e} kgf·cm2;  EI (debil) = E Iy = {EIy:.4e}')
    qb = v['row']
    carga_hoja = (qb[8] + qb[14]) / L  # VyI + VyJ entre L: kgf/cm (magnitud)
    P(f'q peso propio: masa 23.9 kg/m -> q = {q:.6f} kgf/cm;  control BARRAS (VyI+VyJ)/L = {carga_hoja:.6f}')
    P('')

    P('Control de signos y eje: momentos de extremo de la solucion vs BARRAS (ASD1 = PP aqui)')
    P(f'  {"":<22}{"EI fuerte":>16}{"EI debil":>16}{"BARRAS kgf·cm":>18}')
    for nom, EI in (('fuerte Ix', EIx), ('debil Iy', EIy)):
        m0, mL = momentos_extremo(EI, L, v['w1'], v['w2'], v['t1'], v['t2'], q)
        P(f'  EI w(0) [{nom}]  = {m0:>14,.2f}   -> M_I = -EI w(0) = {-m0:>12,.2f}   BARRAS MZ_I = {v["row"][12]*100:>12,.2f}')
        P(f'  EI w(L) [{nom}]  = {mL:>14,.2f}   ->  M_J = +EI w(L)= {mL:>12,.2f}   BARRAS MZ_J = {v["row"][18]*100:>12,.2f}')
    P('  (Se toma la eleccion de signo que reproduce ambos extremos: M_I = -EI w(0), M_J = +EI w(L).)')
    P('')

    dev_x, dev = hermite(EIx, L, v['w1'], v['w2'], v['t1'], v['t2'], q)
    flecha_mm = abs(dev) * 10.0
    P(f'FLECHA (solucion exacta EB con giros de DEFORMADA): {flecha_mm:.5f} mm  en x/L = {dev_x:.4f}')
    P(f'  signo: {"hacia abajo" if dev < 0 else "hacia arriba"} respecto a la cuerda; memoria: 0.06 mm, x/L = 0.46')
    P(f'  mismo calculo con el eje debil (solo contraste): {abs(hermite(EIy, L, v["w1"], v["w2"], v["t1"], v["t2"], q)[1])*10:.4f} mm')
    P('')

    # Sensibilidad a los giros (no hace falta: la hoja trae RY; esto mide el peso de omitirlos)
    _, dev_sin = hermite(EIx, L, v['w1'], v['w2'], 0.0, 0.0, q)
    t_cuerda = (v['w2'] - v['w1']) / L
    _, dev_cuerda = hermite(EIx, L, v['w1'], v['w2'], t_cuerda, t_cuerda, q)
    P('Sensibilidad (si los giros no existieran):')
    P(f'  giros nulos (t1 = t2 = 0):          {abs(dev_sin)*10:.5f} mm  ({(abs(dev_sin)/abs(dev)-1)*100:+.1f} %)')
    P(f'  giros = pendiente de la cuerda:     {abs(dev_cuerda)*10:.5f} mm  ({(abs(dev_cuerda)/abs(dev)-1)*100:+.1f} %)')
    P(f'  peso del termino de carga (qL^4/384EI, extremos empotrados): {abs(q)*L**4/(384*EIx)*10:.5f} mm')
    P('')

    # Limite
    L_cm = 500.0
    P('Limite L/300 (memoria, FLECHA_DIVISOR 300):')
    P(f'  L/300 = {L_cm*10:.1f} mm / 300 = {L_cm*10/300:.4f} mm  (memoria: 16.67) -> aritmetica correcta')
    P(f'  Referencias: L/360 = {L_cm*10/360:.2f} mm;  L/240 = {L_cm*10/240:.2f} mm;  '
      f'flecha/L/300 = {flecha_mm/(L_cm*10/300)*100:.2f} %')
    P('')

    # Tabla de todas las vigas 13-26 (control de sec. 6.4 de la memoria)
    memo_6_4 = {13: (500, 0.05, 0.48), 14: (500, 0.05, 0.52), 15: (500, 0.06, 0.46), 16: (500, 0.06, 0.54),
                17: (500, 0.05, 0.48), 18: (500, 0.05, 0.52), 19: (500, 0.06, 0.46), 20: (500, 0.06, 0.54),
                21: (400, 0.02, 0.50), 22: (400, 0.03, 0.50), 23: (400, 0.02, 0.50), 24: (400, 0.03, 0.50),
                25: (400, 0.02, 0.50), 26: (400, 0.03, 0.50)}
    P('Todas las vigas (sec. 6.4 de la memoria): mio | memoria')
    P(f'  {"barra":>5}{"L cm":>8}{"mio mm":>12}{"memo mm":>10}{"mio x/L":>10}{"memo x/L":>10}{"L/300":>9}')
    for b in sorted(memo_6_4):
        vb = datos_viga(wb_e, nodos, b)
        xl, dv = hermite(E * p12['ix_cm4'], vb['L'], vb['w1'], vb['w2'], vb['t1'], vb['t2'], q)
        Lb_cm = vb['L']
        P(f'  {b:>5}{Lb_cm:>8.1f}{abs(dv)*10:>12.4f}{memo_6_4[b][1]:>10.2f}{xl:>10.3f}{memo_6_4[b][2]:>10.2f}'
          f'{Lb_cm*10/300:>9.2f}')
    P('')

    # ------------------------------------------------------------------ Extra
    P('#' * 110)
    P('C. CONSISTENCIA DE ENTRADAS (BARRAS, RESUMEN)')
    P('#' * 110)
    r1 = fila_barras(wb_e, 'Peso propio y muerta', 1)
    masa_col = leer_perfil('IR 10 × 49')['masa_kg_m']
    P(f'Columna barra 1, PP: N_I + N_J = {r1[7] + r1[13]:.4f} kgf vs masa x L = {masa_col} kg/m * 3.5 m = {masa_col * 3.5:.4f} kgf')
    so = 0.0
    n_so = 0
    for r in wb_e['BARRAS'].iter_rows(min_row=2, values_only=True):
        if r[0] == 'Sobrecarga':
            n_so += 1
            so += sum(abs(x) for x in r[7:21] if isinstance(x, (int, float)))
    P(f'Estado Sobrecarga en BARRAS: {n_so} filas, suma de |esfuerzos| = {so:.6e} (cero: la sobrecarga no carga la estructura)')
    P('')

    P('FIN.')
    with open(OUT_TXT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(SALIDA) + '\n')
    print('\nSalida escrita en: ' + OUT_TXT)


if __name__ == '__main__':
    main()
